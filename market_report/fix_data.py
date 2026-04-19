#!/usr/bin/env python3
"""修复周线数据: CRSI + 周成交额"""
import json, subprocess, akshare as ak, pandas as pd
from datetime import datetime

APIKEY = "dd4f227a11f34265936086a73b46b80c"

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
    """周线CRSI - 用完整历史数据"""
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
        vals=[(closes[j]-closes[j-1])/closes[j-1]*100.0 for j in range(i-99,i) if j>0 and closes[j] is not None and closes[j-1] is not None and closes[j-1]!=0]
        if vals:
            cnt=sum(1 for v in vals if v<roc_v)
            rc[i]=round(cnt/len(vals)*100.0,2)
        else: rc[i]=50.0
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

# ── US: 通过Twelve Data获取真实周K线 ──────────────────────
print("修复美股周线CRSI...")
us_syms=[("SPY","标普500"),("QQQ","纳指100"),("DIA","道琼斯")]
for sym,name in us_syms:
    url=f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1week&outputsize=200&apikey={APIKEY}&order=asc"
    d=curl(url); vals=d.get("values",[])
    if not vals: print(f"  ⚠️ {name} 周线无数据"); continue
    w_c=[float(v["close"])for v in vals]
    w_crsi=crsi_w(w_c) if len(w_c)>=102 else [None]*len(w_c)
    w_last=w_crsi[-1] if w_crsi else None
    buy=cross_up(w_crsi,15) if w_crsi else False
    sell=cross_down(w_crsi,80) if w_crsi else False
    if name in raw:
        raw[name]["w_crsi"]=round(w_last,2) if w_last is not None else None
        raw[name]["crsi_sig"]="🔴极度超买" if w_last and w_last>=85 else "🟠超买" if w_last and w_last>=70 else "🟢偏强" if w_last and w_last>=55 else "🟡中性" if w_last and w_last>=45 else "🟠低估" if w_last and w_last>=15 else "🔴极度低估" if w_last else "—"
        raw[name]["buy_sig"]="✅周线买点(CRSI上穿15)" if buy else ""
        raw[name]["sell_sig"]="🚨周线卖点(CRSI下穿80)" if sell else ""
    print(f"  ✅ {name}: 周线CRSI={round(w_last,2) if w_last is not None else '—'} | buy={buy} sell={sell}")

# ── A股: 计算正确周成交额 ─────────────────────────────────
print("\n修复A股周成交额...")
a_codes=[("sh000001","上证综指"),("sz399001","深证成指"),("sz399006","创业板指")]
for code,name in a_codes:
    try:
        df=ak.stock_zh_index_daily(symbol=code).tail(200).reset_index(drop=True)
        v=[float(x)for x in df["volume"]]
        # 按5日聚合成交量
        w_v=[]
        for i in range(0,len(v)-1,5):
            chunk=v[i:min(i+5,len(v))]
            w_v.append(sum(chunk))
        if len(w_v)>=6 and w_v[-6]>0:
            chg_pct=(w_v[-1]-w_v[-6])/w_v[-6]*100
            vol_chg=f"{chg_pct:+.1f}%"
        elif len(w_v)>=2 and w_v[-2]>0:
            chg_pct=(w_v[-1]-w_v[-2])/w_v[-2]*100
            vol_chg=f"{chg_pct:+.1f}%"
        else:
            vol_chg="首周数据"
        # 周线CRSI：需要更长历史，用日线数据取每5日收盘
        daily_c=[float(x)for x in df["close"]]
        w_c=[daily_c[i]for i in range(0,len(daily_c),5)]
        w_crsi=crsi_w(w_c) if len(w_c)>=102 else [None]*len(w_c)
        w_last=w_crsi[-1] if w_crsi else None
        buy=cross_up(w_crsi,15) if w_crsi else False
        sell=cross_down(w_crsi,80) if w_crsi else False
        if name in raw:
            raw[name]["week_close_chg"]=vol_chg
            raw[name]["w_crsi"]=round(w_last,2) if w_last is not None else None
            raw[name]["buy_sig"]="✅周线买点(CRSI上穿15)" if buy else ""
            raw[name]["sell_sig"]="🚨周线卖点(CRSI下穿80)" if sell else ""
            if w_last is not None:
                if w_last>=85: raw[name]["crsi_sig"]="🔴极度超买"
                elif w_last>=70: raw[name]["crsi_sig"]="🟠超买"
                elif w_last>=55: raw[name]["crsi_sig"]="🟢偏强"
                elif w_last>=45: raw[name]["crsi_sig"]="🟡中性"
                elif w_last>=15: raw[name]["crsi_sig"]="🟠低估"
                else: raw[name]["crsi_sig"]="🔴极度低估"
        print(f"  ✅ {name}: 周量变化={vol_chg} | 周线CRSI={round(w_last,2) if w_last is not None else '—'}")
    except Exception as e:
        print(f"  ⚠️ {name}: {e}")

# 保存
with open("/workspace/market_report/all_data.json","w") as f:
    json.dump(raw,f,ensure_ascii=False,indent=2)
print("\n✅ 数据修复完成!")
