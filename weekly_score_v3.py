#!/usr/bin/env python3
"""修正版周报评分"""
import json

def rsi14(c):
    if len(c)<15: return None
    g,l=[],[]
    for i in range(1,len(c)):
        d=c[i]-c[i-1]; g.append(max(d,0)); l.append(abs(min(d,0)))
    if len(g)<14: return None
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    return round(100-(100/(1+ag/(al+1e-10))),2) if al else 100.0

def avg(l): return sum(l)/len(l) if l else None

fred   = json.load(open("/workspace/fresh_fred.json"))
ashare = json.load(open("/workspace/fresh_ashare.json"))

spx_d=fred["SP500"]; dji_d=fred["DJIA"]; nas_d=fred["NASDAQCOM"]
vix_d=fred["VIXCLS"]; y10_d=fred["DGS10"]; y2_d=fred["DGS2"]; spd_d=fred["T10Y2Y"]
spx_c=[float(v) for _,v in spx_d]; dji_c=[float(v) for _,v in dji_d]
nas_c=[float(v) for _,v in nas_d]

# 用用户确认的正确数据
spx_prev_close = 7126.06  # 4/17 FRED
spx_open       = 7117.05  # 用户提供
spx_close      = 7165.08  # FRED 4/24
spx_chg        = round((spx_close-spx_prev_close)/spx_prev_close*100, 2)

dji_prev_close = dji_c[dji_d.index(next(d for d in dji_d if d[0]=="2026-04-17"))]
dji_open       = 49451.70  # 参考
dji_close      = 49230.71
dji_chg        = round((dji_close-dji_prev_close)/dji_prev_close*100, 2)

nas_prev_close = nas_c[nas_d.index(next(d for d in nas_d if d[0]=="2026-04-17"))]
nas_open       = 24404.39
nas_close      = 24836.60
nas_chg        = round((nas_close-nas_prev_close)/nas_prev_close*100, 2)

spx_rsi=rsi14(spx_c)
ma200=avg(spx_c[-200:])
spx_dev=round((spx_close-ma200)/ma200*100,2)
vix_v=float(vix_d[-1][1])  # 4/23=19.31
vix_week=[float(v[1]) for v in vix_d if v[0]>="2026-04-20" and v[0]<="2026-04-24"]
vix_avg=round(avg(vix_week),2) if vix_week else vix_v
y10_v=float(y10_d[-1][1])
y2_v=float(y2_d[-1][1])
spd_v=float(spd_d[-1][1]) if spd_d else None

# A股
sh=ashare["上证"]; sz=ashare["深证"]; cy=ashare["创业板"]
sh_c=[float(x) for x in sh["close"]]
sz_c=[float(x) for x in sz["close"]]
cy_c=[float(x) for x in cy["close"]]
sh_dates=sh["dates"]

# 上证4/17收盘=4051.43，4/24收盘=4079.90
sh_prev=4051.43; sh_open=4053.37; sh_close=sh_c[-1]
sh_chg=round((sh_close-sh_prev)/sh_prev*100,2)

sz_prev=sz_c[len(sz_c)-6]  # 4/17
sz_close=sz_c[-1]
sz_chg=round((sz_close-sz_prev)/sz_prev*100,2)

cy_prev=cy_c[len(cy_c)-6]
cy_close=cy_c[-1]
cy_chg=round((cy_close-cy_prev)/cy_prev*100,2)

sh_rsi=rsi14(sh_c); sz_rsi=rsi14(sz_c); cy_rsi=rsi14(cy_c)
ma20_sh=avg(sh_c[-20:])
ma60_sh=avg(sh_c[-60:]) if len(sh_c)>=60 else None

# 两市成交额（不变）
szse_actual=4927.46
sh_est=round(szse_actual*1.32,0)
total_turn=szse_actual+sh_est

print("=== 修正后本周数据 ===")
print(f"SPX: 开{spx_open} 收{spx_close} 涨{spx_chg:+.2f}%  前周收{spx_prev_close}")
print(f"VIX: 4/24收={vix_v}  周均={vix_avg}")
print(f"上证: 开{sh_open} 收{sh_close} 涨{sh_chg:+.2f}%  前周收{sh_prev}")
print(f"深证: 收{sz_close} 涨{sz_chg:+.2f}%  前周收{sz_prev:.2f}")
print(f"创业板: 收{cy_close} 涨{cy_chg:+.2f}%")
print(f"两市成交额≈{total_turn:,.0f}亿")
print(f"VIX周均值: {vix_avg} (4/20~4/24: {vix_week})")

# A股评分
vol_s=100 if total_turn>8000 else(80 if total_turn>6000 else(20 if total_turn>4000 else 0))
ma_score=60 if (ma20_sh and sh_close>ma20_sh) else 40
rsi_a=avg([r for r in [sh_rsi,sz_rsi,cy_rsi] if r])
rsi_s=60 if rsi_a and rsi_a>=50 else(30 if rsi_a and rsi_a>=40 else 10)
tech_cn=round(vol_s*0.35+ma_score*0.40+rsi_s*0.25,1)
fund_cn=round(60*0.40+70*0.35+65*0.25,1)
sent_cn=50
ge_cn=max(0,min(100,50-15+5-5))
total_cn=round(tech_cn*0.40+fund_cn*0.30+sent_cn*0.20+ge_cn*0.10,1)

# 美股评分（VIX用周均19.0）
vix_s=60 if vix_avg<20 else(20 if vix_avg<25 else 0)
dev_s=60 if 0<spx_dev<=10 else(80 if 0<spx_dev<=5 else 20)
rs_s=70 if spx_rsi and spx_rsi>85 else(60 if spx_rsi and spx_rsi>=50 else 40)
tech_us=round(vix_s*0.30+dev_s*0.45+rs_s*0.25,1)
fund_us=round(60*0.35+60*0.40+60*0.25,1)
sent_us=60
ge_us=max(0,min(100,50-10-5-5))
total_us=round(tech_us*0.35+fund_us*0.30+sent_us*0.25+ge_us*0.10,1)

def st(s):
    if s>=80: return "🟢 强势牛市","满仓","80-100%"
    elif s>=60: return "🟢 偏强震荡","7成仓","60-80%"
    elif s>=40: return "🟡 中性偏弱","5成仓","30-50%"
    elif s>=20: return "🟠 偏弱震荡","3成仓","10-20%"
    else: return "🔴 熊市","空仓","0-10%"

s_cn,r_cn,p_cn=st(total_cn)
s_u,r_u,p_u=st(total_us)

print(f"\n=== 评分结果 ===")
print(f"A股: {total_cn}分 {s_cn} → {r_cn}（{p_cn}）")
print(f"  技术={tech_cn}(量价{vol_s}+趋势{ma_score}+RSI均{rsi_s}) 基本={fund_cn} 情绪={sent_cn} 全球={ge_cn}")
print(f"美股: {total_us}分 {s_u} → {r_u}（{p_u}）")
print(f"  技术={tech_us}(VIX均{vix_avg}→{vix_s}+偏离{dev_s}+RSI{rs_s}) 基本={fund_us} 情绪={sent_us} 全球={ge_us}")

scores={
  "A股":{"评分":total_cn,"状态":s_cn,"建议":r_cn,"仓位":p_cn,
         "技术面":tech_cn,"基本面":fund_cn,"情绪面":sent_cn,"全球事件":ge_cn},
  "美股":{"评分":total_us,"状态":s_u,"建议":r_u,"仓位":p_u,
          "技术面":tech_us,"基本面":fund_us,"情绪面":sent_us,"全球事件":ge_us},
  "数据":{
    "SPX":spx_close,"SPX涨跌":spx_chg,"SPX开盘":spx_open,"SPX_RSI":spx_rsi,
    "DJI":dji_close,"DJI涨跌":dji_chg,
    "NASDAQ":nas_close,"NASDAQ涨跌":nas_chg,
    "VIX收盘":vix_v,"VIX周均":vix_avg,"VIX周数据":vix_week,
    "US10Y":y10_v,"US2Y":y2_v,"利差":spd_v,
    "上证收盘":round(sh_close,2),"上证涨跌":sh_chg,"上证开盘":sh_open,
    "深证收盘":round(sz_close,2),"深证涨跌":sz_chg,
    "创业板收盘":round(cy_close,2),"创业板涨跌":cy_chg,
    "两市日均成交额":round(total_turn,0),
  }
}
with open("/workspace/weekly_scores_v3.json","w") as f:
    json.dump(scores,f,ensure_ascii=False,indent=2)
print("\n✅ v3 saved")
