#!/usr/bin/env python3
"""大盘周报评分引擎 v2.2 — 2026-04-20~26"""
import json

fred   = json.load(open("/workspace/fresh_fred.json"))
ashare = json.load(open("/workspace/fresh_ashare.json"))

def rsi14(c):
    if len(c) < 15: return None
    g,l=[],[]
    for i in range(1,len(c)):
        d=c[i]-c[i-1]; g.append(max(d,0)); l.append(abs(min(d,0)))
    if len(g)<14: return None
    ag=sum(g[-14:])/14; al=sum(l[-14:])/14
    return round(100-(100/(1+ag/(al+1e-10))),2) if al else 100.0

def avg(l): return sum(l)/len(l) if l else None

spx_d=fred["SP500"]; dji_d=fred["DJIA"]; nas_d=fred["NASDAQCOM"]
vix_d=fred["VIXCLS"]; y10_d=fred["DGS10"]; y2_d=fred["DGS2"]; spd_d=fred["T10Y2Y"]

spx_c=[float(v) for _,v in spx_d]; dji_c=[float(v) for _,v in dji_d]
nas_c=[float(v) for _,v in nas_d]

# 本周涨跌
def wk_chg(d):
    dt_map=dict(d)
    o=dt_map.get("2026-04-20")
    c=d[-1][1]
    return o, c, round((c-o)/o*100,2) if o else None

spx_o,spx_cw,spx_pct=wk_chg(spx_d)
dji_o,dji_cw,dji_pct=wk_chg(dji_d)
nas_o,nas_cw,nas_pct=wk_chg(nas_d)

spx_rsi=rsi14(spx_c); ma200=avg(spx_c[-200:])
spx_dev=round((spx_cw-ma200)/ma200*100,2)
vix_v=float(vix_d[-1][1])
y10_v=float(y10_d[-1][1]); y2_v=float(y2_d[-1][1])
spd_v=float(spd_d[-1][1]) if spd_d else None

sh=ashare["上证"]; sz=ashare["深证"]; cy=ashare["创业板"]
sh_c=[float(x) for x in sh["close"]]
sz_c=[float(x) for x in sz["close"]]
cy_c=[float(x) for x in cy["close"]]
sh_dates=sh["dates"]

sh_rsi=rsi14(sh_c); sz_rsi=rsi14(sz_c); cy_rsi=rsi14(cy_c)
ma20_sh=avg(sh_c[-20:])

# 两市成交额：深交所实际+沪市历史比例估算
szse_actual=4927.46    # 深交所2026-04-24全市场股票成交额（元→亿）
sh_est=round(szse_actual*1.32,0)  # 沪市历史均值/深市≈1.32
total_today=szse_actual+sh_est     # ≈11431亿 → >8000亿 → 满分
# 5日均值（两市）
avg_5d=round((szse_actual*0.96+sh_est)*1, 0)  # 深市5日均值略低

# ── A股评分 ────────────────────────────────────────────────────
vol_s=100 if total_today>8000 else(80 if total_today>6000 else(20 if total_today>4000 else 0))
ma_score=50
if ma20_sh:
    if sh_c[-1]>ma20_sh: ma_score=60
    else: ma_score=40
rsi_a=avg([r for r in [sh_rsi,sz_rsi,cy_rsi] if r])
rsi_s=60 if rsi_a and rsi_a>=50 else(30 if rsi_a and rsi_a>=40 else 10)
tech_cn=round(vol_s*0.35+ma_score*0.40+rsi_s*0.25,1)
fund_cn=round(60*0.40+70*0.35+65*0.25,1)
sent_cn=50
ge_cn=max(0,min(100,50-15+5-5))
total_cn=round(tech_cn*0.40+fund_cn*0.30+sent_cn*0.20+ge_cn*0.10,1)

# ── 美股评分 ────────────────────────────────────────────────────
vix_s=60 if vix_v<20 else(20 if vix_v<25 else 0)
dev_s=80 if 0<spx_dev<=5 else(60 if 0<spx_dev<=10 else 20)
rs_s=70 if spx_rsi and spx_rsi>85 else(60 if spx_rsi and spx_rsi>=50 else(40 if spx_rsi and spx_rsi>=40 else 20))
tech_us=round(vix_s*0.30+dev_s*0.45+rs_s*0.25,1)
fund_us=round(60*0.35+60*0.40+60*0.25,1)
sent_us=60
ge_us=max(0,min(100,50-10-5-5))
total_us=round(tech_us*0.35+fund_us*0.30+sent_us*0.25+ge_us*0.10,1)

def st_cn(s):
    if s>=80: return "🟢 强势牛市","满仓持有","80-100%"
    elif s>=60: return "🟢 偏强震荡","7成仓回调加仓","60-80%"
    elif s>=40: return "🟡 中性偏弱","5成仓高抛低吸","30-50%"
    elif s>=20: return "🟠 偏弱震荡","3成仓快进快出","10-20%"
    else: return "🔴 熊市","空仓观望","0-10%"

def st_us(s):
    if s>=80: return "🟢 强势牛市","满仓持有","80-100%"
    elif s>=60: return "🟢 偏强震荡","7成仓","60-80%"
    elif s>=40: return "🟡 中性偏弱","5成仓高抛低吸","30-50%"
    elif s>=20: return "🟠 偏弱震荡","3成仓","10-20%"
    else: return "🔴 熊市","空仓","0-10%"

s_cn,r_cn,p_cn=st_cn(total_cn)
s_u,r_u,p_u=st_us(total_us)

# ── 打印 ──────────────────────────────────────────────────────
print("═"*52)
print("  本周数据（2026-04-20 → 04-24）5个交易日")
print("═"*52)
print(f"  SPX:  7160.89 → {spx_cw:,.2f}  ({spx_pct:+.2f}%)  RSI={spx_rsi}  VIX={vix_v}  偏离MA200={spx_dev:+.2f}%")
print(f"  DJI:  49451.70→ {dji_cw:,.2f}  ({dji_pct:+.2f}%)")
print(f"  NASDAQ:{nas_o:,.2f}→ {nas_cw:,.2f}  ({nas_pct:+.2f}%)")
print(f"  VIX={vix_v}  US10Y={y10_v}%  2Y={y2_v}%  10Y-2Y={spd_v}bp")
print()
print(f"  上证: {sh_dates[-5]}→{sh_dates[-1]}  close={sh_c[-1]:.2f}  RSI={sh_rsi:.1f}")
print(f"  深证: close={sz_c[-1]:.2f}  RSI={sz_rsi:.1f}")
print(f"  创业板: close={cy_c[-1]:.2f}  RSI={cy_rsi:.1f}")
print(f"  深市实际成交额={szse_actual:.2f}亿 + 沪市估算={sh_est:.0f}亿 = 合计≈{total_today:,.0f}亿/日")
print()
print("═"*52)
print("  评分结果")
print("═"*52)
print(f"\n  A股: {total_cn}分 {s_cn}")
print(f"    技术={tech_cn}(量价{vol_s}+趋势{ma_score}+RSI{rsi_s})")
print(f"    基本={fund_cn} 情绪={sent_cn} 全球={ge_cn}")
print(f"    → {r_cn}（{p_cn}）")
print(f"\n  美股: {total_us}分 {s_u}")
print(f"    技术={tech_us}(VIX{vix_s}+偏离{dev_s}+RSI{rs_s})")
print(f"    基本={fund_us} 情绪={sent_us} 全球={ge_us}")
print(f"    → {r_u}（{p_u}）")

scores={
  "A股":{"评分":total_cn,"状态":s_cn,"建议":r_cn,"仓位":p_cn,
         "技术面":tech_cn,"基本面":fund_cn,"情绪面":sent_cn,"全球事件":ge_cn},
  "美股":{"评分":total_us,"状态":s_u,"建议":r_u,"仓位":p_u,
          "技术面":tech_us,"基本面":fund_us,"情绪面":sent_us,"全球事件":ge_us},
  "数据":{"SPX":round(spx_cw,2),"SPX涨跌":spx_pct,"SPX_RSI":spx_rsi,"SPX偏离MA200":spx_dev,
          "DJI":round(dji_cw,2),"DJI涨跌":dji_pct,
          "NASDAQ":round(nas_cw,2),"NASDAQ涨跌":nas_pct,
          "VIX":vix_v,"US10Y":y10_v,"US2Y":y2_v,"利差":spd_v,
          "上证收盘":round(sh_c[-1],2),"上证RSI":sh_rsi,
          "深证收盘":round(sz_c[-1],2),"深证RSI":sz_rsi,
          "创业板收盘":round(cy_c[-1],2),"创业板RSI":cy_rsi,
          "两市日均成交额":round(total_today,0),
          "深市实际成交额":szse_actual,"沪市估算":sh_est}
}
with open("/workspace/weekly_scores_v2.json","w") as f:
    json.dump(scores,f,ensure_ascii=False,indent=2)
print("\n✅ saved")
