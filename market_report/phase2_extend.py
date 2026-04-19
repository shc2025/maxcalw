#!/usr/bin/env python3
"""Phase 2: 补充采集失败的市场数据 + 历史相似场景分析"""
import subprocess, json, sys
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def curl(url):
    p=subprocess.run(["curl","-s","--max-time","15",url],capture_output=True,text=True,timeout=20)
    try: return json.loads(p.stdout)
    except: return {}

def wilder_rsi(prices, period):
    n=len(prices); result=[None]*n
    gains,losses=[],[]
    for i in range(1,n):
        d=prices[i]-prices[i-1]; gains.append(max(d,0)); losses.append(abs(min(d,0)))
    if len(gains)<period: return result
    ag=sum(gains[:period])/period; al=sum(losses[:period])/period
    result[period]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    for i in range(period,len(gains)):
        ag=(ag*(period-1)+gains[i])/period; al=(al*(period-1)+losses[i])/period
        result[i+1]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    return result

def adx_daily(opens,highs,lows,closes,period=14):
    n=len(opens); trs=[0.0]*n; dmp=[0.0]*n; dmm=[0.0]*n
    trs[0]=highs[0]-lows[0]
    for i in range(1,n):
        hl=highs[i]-lows[i]; h_c=abs(highs[i]-closes[i-1]); l_c=abs(lows[i]-closes[i-1])
        trs[i]=max(hl,h_c,l_c)
    for i in range(1,n):
        h_diff=highs[i]-highs[i-1]; l_diff=lows[i-1]-lows[i]
        if h_diff>l_diff and h_diff>0: dmp[i]=h_diff
        if l_diff>h_diff and l_diff>0: dmm[i]=l_diff
    str_v=[None]*n; sdp=[None]*n; sdm=[None]*n
    str_v[period]=sum(trs[:period])/period; sdp[period]=sum(dmp[:period])/period; sdm[period]=sum(dmm[:period])/period
    for i in range(period,n-1):
        str_v[i+1]=str_v[i]-str_v[i]/period+trs[i]
        sdp[i+1]=sdp[i]-sdp[i]/period+dmp[i]
        sdm[i+1]=sdm[i]-sdm[i]/period+dmm[i]
    di_p=[None]*n; di_m=[None]*n; dx=[None]*n
    for i in range(period,n):
        if str_v[i]==0.0: continue
        dp=sdp[i]/str_v[i]*100.0; dm=sdm[i]/str_v[i]*100.0
        di_p[i]=dp; di_m[i]=dm; s=dp+dm
        dx[i]=abs(dp-dm)/s*100.0 if s!=0 else 0.0
    adx_v=[None]*n
    for i in range(period*2-1,n):
        window=[dx[j] for j in range(i-period+1,i+1) if dx[j] is not None]
        if len(window)==period: adx_v[i]=sum(window)/period
    return adx_v,di_p,di_m,dx

def adx_sig_func(adx_v,di_p,di_m):
    if adx_v is None: return "数据不足"
    if di_p is not None and di_m is not None:
        direction="↑上升" if di_p>di_m else "↓下降"
    else: direction="横"
    if adx_v<20: return f"⚪震荡(ADX<20){direction}"
    elif adx_v<25: return f"🟡弱趋势(ADX25){direction}"
    elif adx_v<40: return f"🟢中等趋势{direction}"
    elif adx_v<60: return f"🟠强趋势{direction}"
    else: return f"🔴极强趋势{direction}"

raw = json.load(open("/workspace/market_report/raw_data.json","r"))
extend_data = {}

# ─── 1. VIX ────────────────────────────────────────────────
print("=== VIX ===")
vix_syms=["VIX","vix","^VIX","VIXY","VIX=X"]
for sym in vix_syms:
    d=curl(f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=30&apikey={APIKEY}")
    vals=d.get("values",[])
    print(f"  {sym}: {len(vals)} records")
    if vals:
        print(f"  → 最新: {vals[-1]}")
        break

# 尝试通过akshare获取VIX
try:
    df_vix=ak.macro_usa_vix()
    print("akshare VIX:", df_vix.tail(5) if hasattr(df_vix,'tail') else df_vix[:5])
except Exception as e:
    print("VIX akshare ERR:", e)

# ─── 2. 恒生指数 (akshare stock_hk_daily) ─────────────────
print("\n=== 恒生指数 ===")
try:
    df_hsi=ak.stock_hk_daily(symbol="HSI",adjust="qfq").tail(200).reset_index(drop=True)
    print(f"  获取 {len(df_hsi)} 条历史数据")
    print(f"  最新: {df_hsi['date'].iloc[-1]} 收盘={df_hsi['close'].iloc[-1]:.2f}")
    hk_o=[float(x) for x in df_hsi['open']]
    hk_h=[float(x) for x in df_hsi['high']]
    hk_l=[float(x) for x in df_hsi['low']]
    hk_c=[float(x) for x in df_hsi['close']]
    hk_dates=[str(x)[:10] for x in df_hsi['date']]
    adx_v,di_p,di_m,dx=adx_daily(hk_o,hk_h,hk_l,hk_c,14)
    idx=-1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    extend_data["恒生指数"]={
        "adx_latest":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
        "di_plus_latest":round(di_p[idx],2) if di_p[idx] is not None else None,
        "di_minus_latest":round(di_m[idx],2) if di_m[idx] is not None else None,
        "adx_sig":adx_sig_func(adx_v[idx],di_p[idx],di_m[idx]),
        "last_close":round(hk_c[-1],2),"last_date":hk_dates[-1],
        "class":"HK","dates":hk_dates,"closes":hk_c,
        "w_crsi_last":None,"buy_sig":False,"sell_sig":False,"vsa":[],"patterns":[],"vol_chg":"",
    }
    print(f"  ✅ 恒生指数: ADX={extend_data['恒生指数']['adx_latest']} | DI+={extend_data['恒生指数']['di_plus_latest']} | DI-={extend_data['恒生指数']['di_minus_latest']}")
except Exception as e:
    print(f"  恒生指数 ERR: {e}")

# ─── 3. 日经225 ────────────────────────────────────────────
print("\n=== 日经225 ===")
nikkei_funcs=[
    ("index_zh_a_hist", "Nikkei"),
    ("stock_jp_index", "Nikkei stock_jp"),
    ("index_hist","Nikkei index_hist"),
]
for func_name, label in nikkei_funcs:
    try:
        func=getattr(ak,func_name,None)
        if func is None: continue
        if func_name=="index_zh_a_hist":
            df=func(symbol="NI225",adjust="qfq").tail(200).reset_index(drop=True)
        elif func_name=="index_hist":
            df=func(symbol="Nikkei 225",adjust="0").tail(200).reset_index(drop=True)
        else:
            df=func(symbol="Nikkei225").tail(200).reset_index(drop=True)
        print(f"  {func_name}: {len(df)} rows, columns: {list(df.columns)}")
        print(f"  最新: {str(df['日期'].iloc[-1]) if '日期' in df.columns else df['date'].iloc[-1] if 'date' in df.columns else 'N/A'}")
        break
    except Exception as e:
        print(f"  {func_name} ERR: {e}")

# ─── 4. DAX ───────────────────────────────────────────────
print("\n=== 德国DAX ===")
dax_syms=[("DAX",30),("DAX.ID",30),("DE40",30),("GER40",30)]
for sym,cid in dax_syms:
    d=curl(f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=30&apikey={APIKEY}")
    vals=d.get("values",[])
    print(f"  {sym}: {len(vals)} records")
    if vals:
        print(f"  最新: {vals[-1]}")
        break

# ─── 5. 法国CAC40 ─────────────────────────────────────────
print("\n=== 法国CAC40 ===")
cac_syms=["CAC40","FRA40","FCHI","FR40"]
for sym in cac_syms:
    d=curl(f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=30&apikey={APIKEY}")
    vals=d.get("values",[])
    print(f"  {sym}: {len(vals)} records")
    if vals:
        print(f"  最新: {vals[-1]}")
        break

# ─── 6. 韩国综合 ──────────────────────────────────────────
print("\n=== 韩国综合 ===")
kospi_syms=["KS11","KOSPI","KRX:KOSPI"]
for sym in kospi_syms:
    d=curl(f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=30&apikey={APIKEY}")
    vals=d.get("values",[])
    print(f"  {sym}: {len(vals)} records")
    if vals:
        print(f"  最新: {vals[-1]}")
        break

# ─── 7. 历史相似场景分析 ─────────────────────────────────
print("\n=== 历史相似场景分析 ===")
# 使用A股数据找相似模式
try:
    df_a=ak.stock_zh_index_daily(symbol="sh000001").tail(500).reset_index(drop=True)
    closes_a=[float(x) for x in df_a['close']]
    dates_a=[str(x)[:10] for x in df_a['date']]
    # 最近1日变化率
    if len(closes_a)>=2:
        recent_chg=(closes_a[-1]-closes_a[-2])/closes_a[-2]*100
        print(f"  上证最近变化: {recent_chg:+.2f}%")
    # 过去历史大跌相似场景（-3%以上）
    drops=[(dates_a[i],closes_a[i],(closes_a[i]-closes_a[i-1])/closes_a[i-1]*100)
           for i in range(1,len(closes_a)) if (closes_a[i]-closes_a[i-1])/closes_a[i-1]*100<-3]
    print(f"  历史上证-3%以上跌幅次数: {len(drops)} 次")
    if drops:
        print(f"  近期相似场景: {drops[-3:]}")
    # 反弹行情（次日涨幅>1%）
    rebounds=[(dates_a[i],closes_a[i+1],(closes_a[i+1]-closes_a[i])/closes_a[i]*100)
              for i in range(len(closes_a)-1) if (closes_a[i]-closes_a[i-1])/closes_a[i-1]*100<-3 and i>0 and i<len(closes_a)-1
              for _ in [((closes_a[i+1]-closes_a[i])/closes_a[i]*100,)]
              if (closes_a[i+1]-closes_a[i])/closes_a[i]*100>1]
    print(f"  大跌后次日反弹>1%次数: {len(rebounds)} 次")
    if rebounds:
        print(f"  最近3次: {rebounds[-3:]}")
except Exception as e:
    print(f"  历史分析 ERR: {e}")

# 保存扩展数据
for k,v in extend_data.items():
    raw[k]=v

with open("/workspace/market_report/raw_data.json","w") as f:
    json.dump(raw,f,ensure_ascii=False,indent=2)
print("\n✅ Phase 2 完成，数据已更新")
print(f"当前已有指数: {list(raw.keys())}")
