#!/usr/bin/env python3
"""补充A股周线CRSI(拉2年数据)，修复周成交额计算"""
import json, subprocess, akshare as ak, pandas as pd
APIKEY="dd4f227a11f34265936086a73b46b80c"

def curl(url):
    p=subprocess.run(["curl","-s","--max-time","15",url],capture_output=True,text=True,timeout=20)
    try: return json.loads(p.stdout)
    except: return {}

def wilder_rsi(prices,period):
    n=len(prices); r=[None]*n
    g,l=[],[]
    for i in range(1,n):
        d=prices[i]-prices[i-1]; g.append(max(d,0)); l.append(abs(min(d,0)))
    if len(g)<period: return r
    ag=sum(g[:period])/period; al=sum(l[:period])/period
    r[period]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    for i in range(period,len(g)):
        ag=(ag*(period-1)+g[i])/period; al=(al*(period-1)+l[i])/period
        r[i+1]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    return r

def crsi_w(closes):
    n=len(closes)
    rp=wilder_rsi(closes,3)
    ud=[0.0]*n; p=0.0
    for i in range(1,n):
        if closes[i]==closes[i-1]: p=0.0
        elif closes[i]>closes[i-1]: p=1.0 if p<=0 else p+1.0
        else: p=-1.0 if p>=0 else p-1.0
        ud[i]=p
    ru=wilder_rsi(ud,2)
    rc=[None]*n
    for i in range(100,n):
        cur=closes[i]; prev=closes[i-1]
        if cur is None or prev is None or prev==0: rc[i]=50.0; continue
        roc_v=(cur-prev)/prev*100.0
        vals=[(closes[j]-closes[j-1])/closes[j-1]*100.0 for j in range(i-99,i)
              if j>0 and closes[j] is not None and closes[j-1] is not None and closes[j-1]!=0]
        cnt=sum(1 for v in vals if v<roc_v) if vals else 0
        rc[i]=round(cnt/len(vals)*100.0,2) if vals else 50.0
    out=[]
    for i in range(n):
        a,b,c=rp[i],ru[i],rc[i]
        out.append(round((a+b+c)/3.0,2) if None not in [a,b,c] else None)
    return out

def cross_up(series,threshold):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1]<threshold<=series[i]: return True
    return False

def cross_down(series,threshold):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1]>threshold>=series[i]: return True
    return False

raw=json.load(open("/workspace/market_report/all_data.json","r"))
a_codes=[("sh000001","上证综指"),("sz399001","深证成指"),("sz399006","创业板指")]

print("获取A股长历史(2年+)...")
for code,name in a_codes:
    try:
        # 拉2年=约500交易日
        df=ak.stock_zh_index_daily(symbol=code).tail(500).reset_index(drop=True)
        closes=[float(x)for x in df["close"]]
        volumes=[float(x)for x in df["volume"]]
        dates=[str(x)[:10]for x in df["date"]]
        print(f"  {name}: {len(dates)}日数据 {dates[0]}~{dates[-1]}")

        # 周线收盘: 每5日取一个
        w_c=[]
        for i in range(0,len(closes)-1,5):
            w_c.append(closes[min(i+4,len(closes)-1)])
        print(f"    周线数据: {len(w_c)}周")

        # CRSI
        w_crsi=crsi_w(w_c) if len(w_c)>=104 else [None]*len(w_c)
        valid=[v for v in w_crsi if v is not None]
        w_last=valid[-1] if valid else None
        buy=cross_up(w_crsi,15) if w_crsi else False
        sell=cross_down(w_crsi,80) if w_crsi else False
        print(f"    CRSI有效值: {len(valid)} | 最新={(round(w_last,2) if w_last is not None else 0))} | buy={buy} sell={sell}")

        # 周成交额(近4周对比)
        w_v=[]
        for i in range(0,len(volumes)-1,5):
            w_v.append(sum(volumes[i:min(i+5,len(volumes)-1)]))
        if len(w_v)>=4 and w_v[-2]>0:
            chg_cur=(w_v[-1]-w_v[-2])/w_v[-2]*100
            chg_prev=(w_v[-2]-w_v[-3])/w_v[-3]*100 if len(w_v)>=3 and w_v[-3]>0 else 0
            vol_info=f"本周{len(w_v)}周: {w_v[-1]/1e8:.1f}亿({chg_cur:+.0f}% vs上周)"
        elif len(w_v)>=2 and w_v[-2]>0:
            chg=(w_v[-1]-w_v[-2])/w_v[-2]*100
            vol_info=f"本周{w_v[-1]/1e8:.1f}亿({chg:+.0f}%vs上周)"
        else:
            vol_info="数据不足"
        print(f"    周成交额: {vol_info}")

        if name in raw:
            raw[name]["w_crsi"]=round(w_last,2) if w_last is not None else None
            raw[name]["week_close_chg"]=vol_info
            raw[name]["buy_sig"]="✅周线买点(CRSI上穿15)" if buy else ""
            raw[name]["sell_sig"]="🚨周线卖点(CRSI下穿80)" if sell else ""
            if w_last is not None:
                if w_last>=85: raw[name]["crsi_sig"]="🔴极度超买"
                elif w_last>=70: raw[name]["crsi_sig"]="🟠超买"
                elif w_last>=55: raw[name]["crsi_sig"]="🟢偏强"
                elif w_last>=45: raw[name]["crsi_sig"]="🟡中性"
                elif w_last>=15: raw[name]["crsi_sig"]="🟠低估"
                else: raw[name]["crsi_sig"]="🔴极度低估"
            else:
                raw[name]["crsi_sig"]="数据不足100周"
    except Exception as e:
        print(f"  ⚠️ {name}: {e}")

with open("/workspace/market_report/all_data.json","w") as f:
    json.dump(raw,f,ensure_ascii=False,indent=2)
print("\n✅ 完成!")
# 打印修正后的值
for name in ["上证综指","深证成指","创业板指"]:
    m=raw.get(name,{})
    print(f"  {name}: w_crsi={m.get('w_crsi')} crsi_sig={m.get('crsi_sig')} buy={m.get('buy_sig')} sell={m.get('sell_sig')}")
