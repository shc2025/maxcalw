#!/usr/bin/env python3
"""
大盘指数技术分析 — Phase 1: 数据采集与技术指标计算
每周收盘后运行，采集所有标的技术数据
"""
import subprocess, json, sys, os
from datetime import datetime, timedelta

APIKEY = "dd4f227a11f34265936086a73b46b80c"

# ─── 0. 工具函数 ───────────────────────────────────────────

def curl(url):
    p = subprocess.run(["curl","-s","--max-time","15",url],capture_output=True,text=True,timeout=20)
    try: return json.loads(p.stdout)
    except: return {}

def wilder_rsi(prices, period):
    n = len(prices); result=[None]*n
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

def streak_updown(closes):
    ud=[0.0]*len(closes); prev=0.0
    for i in range(1,len(closes)):
        if closes[i]==closes[i-1]: prev=0.0
        elif closes[i]>closes[i-1]: prev=1.0 if prev<=0 else prev+1.0
        else: prev=-1.0 if prev>=0 else prev-1.0
        ud[i]=prev
    return ud

def pct_rank(series, lookback):
    n=len(series); result=[None]*n
    for i in range(lookback,n):
        if series[i] is None: continue
        valid=[series[j] for j in range(i-lookback,i) if series[j] is not None]
        result[i]=round(sum(1 for v in valid if v<series[i])/len(valid)*100.0,2) if valid else 50.0
    return result

def roc(closes,period=1):
    out=[None]*len(closes)
    for i in range(period,len(closes)):
        if closes[i-period] is None or closes[i] is None: continue
        prev=closes[i-period]; out[i]=((closes[i]-prev)/prev*100.0) if prev!=0 else 0.0
    return out

def crsi_weekly(closes):
    """计算周线CRSI，返回所有历史值"""
    if len(closes)<102: return [None]*len(closes)
    rp=wilder_rsi(closes,3); ud=streak_updown(closes)
    ru=wilder_rsi(ud,2); rc=pct_rank(roc(closes,1),100)
    out=[]
    for i in range(len(closes)):
        a,b,c=rp[i],ru[i],rc[i]
        out.append(round((a+b+c)/3.0,2) if None not in [a,b,c] else None)
    return out

def adx_daily(opens,highs,lows,closes,period=14):
    """计算日线ADX（Wilder平滑）"""
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

def crsi_signal(v):
    if v is None: return "数据不足"
    if v>=85: return "🔴极度超买"
    elif v>=70: return "🟠超买"
    elif v>=55: return "🟢偏强"
    elif v>=45: return "🟡中性"
    elif v>=30: return "🟡偏弱"
    elif v>=15: return "🟠低估"
    else: return "🔴极度低估"

def adx_signal(adx_v,di_p,di_m):
    if adx_v is None: return "数据不足"
    if adx_v<20: trend="⚪震荡(无趋势)"
    elif adx_v<25: trend="🟡弱趋势"
    elif adx_v<40: trend="🟢中等趋势"
    elif adx_v<60: trend="🟠强趋势"
    else: trend="🔴极强趋势"
    if di_p is not None and di_m is not None:
        if di_p>di_m: direction="↑上升"
        elif di_m>di_p: direction="↓下降"
        else: direction="横"
    else: direction="横"
    return f"{trend}{direction}"

def cross_through(series, threshold, direction):
    """
    检测上穿/下穿信号
    direction: 'up'(上穿15), 'down'(下穿80)
    """
    if len(series)<2: return False
    for i in range(1,len(series)):
        if series[i] is None or series[i-1] is None: continue
        if direction=='up':
            if series[i-1]<threshold<=series[i]: return True
        else:
            if series[i-1]>threshold>=series[i]: return True
    return False

def fetch_td(symbol, interval="1day", weeks=200):
    """从 Twelve Data 获取K线"""
    size = weeks if interval=="1week" else 200
    url = (f"https://api.twelvedata.com/time_series?symbol={symbol}"
           f"&interval={interval}&outputsize={size}&apikey={APIKEY}&order=asc")
    d=curl(url); vals=d.get("values",[])
    if not vals: return [],[],[],[],[]
    dates=[v["datetime"] for v in vals]
    o=[float(v["open"])for v in vals]
    h=[float(v["high"])for v in vals]
    l=[float(v["low"]) for v in vals]
    c=[float(v["close"])for v in vals]
    return dates,o,h,l,c

def vsa_analysis(volumes, highs, lows, closes):
    """
    威科夫量价分析（简化版）
    返回近5日VSA信号列表
    """
    n=len(volumes)
    if n<10: return []
    avg_vol=sum(volumes[-20:])/min(20,n)
    results=[]
    for i in range(-6,0):
        idx=n+i if i<0 else i
        if idx<1 or idx>=n: continue
        vol=volumes[idx]; price=closes[idx]
        prev=closes[idx-1]; pct_change=(price-prev)/prev*100.0 if prev!=0 else 0
        ratio=vol/avg_vol if avg_vol>0 else 1
        # 缩量上涨/下跌判断
        if ratio<0.8:
            if pct_change>1: sig="缩量上涨(供应弱，可能继续)"
            elif pct_change<-1: sig="缩量下跌(需求弱，可能反弹)"
            else: sig="缩量震荡"
        elif ratio>1.3:
            if pct_change>1: sig="🔥放量上涨(需求强，谨慎追高)"
            elif pct_change<-1: sig="🔥放量下跌(抛压重，注意风险)"
            else: sig="放量震荡"
        else:
            if pct_change>0.5: sig="温和放量上涨"
            elif pct_change<-0.5: sig="温和放量下跌"
            else: sig="量价平稳"
        change_str=f"+{pct_change:.2f}%" if pct_change>=0 else f"{pct_change:.2f}%"
        date_str=f"近{i+6}日" if i>=-5 else "今日"
        results.append({"label":date_str,"sig":sig,"vol_ratio":round(ratio,2),"price_chg":change_str})
    return results

def pattern_analysis(dates, closes, highs, lows, volumes):
    """
    形态分析：支撑/阻力位 + 常见形态
    返回关键价位和形态列表
    """
    n=len(closes)
    if n<30: return {},[]
    # 近期高低点
    recent_high=max(highs[-30:]); recent_low=min(lows[-30:]); idx_h=highs.index(recent_high)
    idx_l=lows.index(recent_low)
    levels={
        "近30日高点": (recent_high, dates[idx_h]),
        "近30日低点": (recent_low, dates[idx_l]),
    }
    # 50日高低
    if n>=50:
        m50_high=max(highs[-50:]); m50_low=min(lows[-50:])
        levels["近50日高点"]=(m50_high,dates[highs.index(m50_high)])
        levels["近50日低点"]=(m50_low,dates[lows.index(m50_low)])
    # 形态识别（简化）
    patterns=[]
    # 顶背离检查（价格创30日新高但RSI未创新高）
    if n>=14:
        rsi14=wilder_rsi(closes,14)
        # 双底
        if n>=20:
            l20=[(lows[i],dates[i]) for i in range(n-20,n) if lows[i] is not None]
            if l20:
                min_low=min(v[0] for v in l20)
                if lows[-1]<=min_low*1.01 and lows[-1]>=min_low*0.99: patterns.append("疑似双底(W底)")
                if lows[-1]<min_low: patterns.append("新低破位(注意风险)")
        # 缩量整理判断
        if n>=5:
            recent_vol=sum(volumes[-5:])/5; prev_vol=sum(volumes[-10:-5])/5 if n>=10 else recent_vol
            if recent_vol<prev_vol*0.7: patterns.append("量能萎缩(酝酿变盘)")
    return levels,patterns

# ─── 1. 定义所有大盘指数 ────────────────────────────────────

MARKETS = {
    # US (通过ETF映射)
    "标普500 (SPY)":    {"td":"SPY",  "class":"US",   "vix_td":"VIX"},
    "纳指100 (QQQ)":   {"td":"QQQ",  "class":"US",   "vix_td":"VIX"},
    "道琼斯 (DIA)":    {"td":"DIA",  "class":"US",   "vix_td":"VIX"},
    "恐慌指数 (VIX)":  {"td":"VIX",  "class":"US",   "vix_td":None},
    # A股 (AkShare)
    "上证综指":         {"class":"A"},
    "深证成指":         {"class":"A"},
    "创业板指":         {"class":"A"},
    # HK
    "恒生指数":         {"class":"HK"},
    "恒生科技":         {"class":"HK"},
    # Other
    "日经225":         {"class":"INT"},
    "德国DAX":         {"td":"DAX", "class":"INT"},
    "法国CAC40":       {"class":"INT"},
    "韩国综合":         {"class":"INT"},
}

# ─── 2. 采集数据并计算指标 ─────────────────────────────────

print("="*60)
print("  大盘指数技术分析  " + datetime.now().strftime("%Y-%m-%d"))
print("="*60)

all_results = {}
errors = []

# ── 2a. US市场 (Twelve Data) ──────────────────────────────
print("\n📡 采集美股数据...")
us_symbols = [("SPY","标普500"),("QQQ","纳指100"),("DIA","道琼斯"),("VIX","恐慌指数")]
us_daily   = {}; us_weekly = {}

for sym, name in us_symbols:
    d_dates,d_o,d_h,d_l,d_c = fetch_td(sym,"1day",200)
    w_dates,w_o,w_h,w_l,w_c = fetch_td(sym,"1week",200)
    if not d_c:
        print(f"  ⚠️  {name} 日线数据获取失败"); errors.append(name); continue
    # ADX日线
    adx_v,di_p,di_m,dx = adx_daily(d_o,d_h,d_l,d_c,14)
    idx=-1
    # 找最后一个有效ADX
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    vol_daily=[1.0]*len(d_c)  # Twelve Data免费层无volume，用dummy
    levels,pats = pattern_analysis(d_dates,d_c,d_h,d_l,vol_daily)
    vsa = vsa_analysis(vol_daily,d_h,d_l,d_c) if vol_daily[0] else []
    # 周线CRSI
    w_crsi = crsi_weekly(w_c) if w_c else [None]*len(w_c)
    # 买点/卖点检测
    buy_sig  = False; sell_sig = False
    if len(w_crsi)>=2:
        buy_sig  = cross_through(w_crsi,15,"up")
        sell_sig = cross_through(w_crsi,80,"down")
    us_daily[sym] = {
        "name":name,"dates":d_dates,"closes":d_c,"highs":d_h,"lows":d_l,
        "adx_latest": round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
        "di_plus_latest": round(di_p[idx],2) if idx>=0 and di_p[idx] is not None else None,
        "di_minus_latest": round(di_m[idx],2) if idx>=0 and di_m[idx] is not None else None,
        "adx_sig": adx_signal(adx_v[idx] if idx>=0 else None, di_p[idx] if idx>=0 else None, di_m[idx] if idx>=0 else None),
        "vsa": vsa, "patterns": pats, "levels": levels,
    }
    us_weekly[sym] = {"name":name,"w_dates":w_dates,"w_closes":w_c,"w_crsi":w_crsi,"buy_sig":buy_sig,"sell_sig":sell_sig}
    print(f"  ✅ {name}: ADX={us_daily[sym]['adx_latest']} | 周线CRSI={round(w_crsi[-1] if w_crsi and w_crsi[-1] else 0,2)}")

# ── 2b. A股 (AkShare) ────────────────────────────────────
print("\n📡 采集A股数据...")
try:
    import akshare as ak, pandas as pd
    a_shares = [
        ("sh000001","上证综指"),
        ("sz399001","深证成指"),
        ("sz399006","创业板指"),
    ]
    for code, name in a_shares:
        try:
            df = ak.stock_zh_index_daily(symbol=code).tail(200).reset_index(drop=True)
            d_dates = [str(row["date"])[:10] for _,row in df.iterrows()]
            d_o = [float(row["open"]) for _,row in df.iterrows()]
            d_h = [float(row["high"]) for _,row in df.iterrows()]
            d_l = [float(row["low"])  for _,row in df.iterrows()]
            d_c = [float(row["close"])for _,row in df.iterrows()]
            d_v = [float(row.get("volume",1)) for _,row in df.iterrows()]
            # 日线ADX
            adx_v,di_p,di_m,dx = adx_daily(d_o,d_h,d_l,d_c,14)
            idx=-1
            for i in range(len(adx_v)-1,-1,-1):
                if adx_v[i] is not None: idx=i; break
            # 周线CRSI: 转换周线
            w_dates=[]; w_o=[]; w_h=[]; w_l=[]; w_c=[]
            if len(d_dates)>=7:
                for i in range(0,len(d_dates)-1,5):
                    chunk_c=d_c[i:i+5]; chunk_o=d_o[i:i+5]; chunk_h=d_h[i:i+5]; chunk_l=d_l[i:i+5]
                    w_dates.append(d_dates[min(i+4,len(d_dates)-1)])
                    w_o.append(chunk_o[0]); w_h.append(max(chunk_h)); w_l.append(min(chunk_l)); w_c.append(chunk_c[-1])
            w_crsi = crsi_weekly(w_c) if len(w_c)>=102 else [None]*len(w_c)
            buy_sig = cross_through(w_crsi,15,"up")
            sell_sig= cross_through(w_crsi,80,"down")
            levels,pats = pattern_analysis(d_dates,d_c,d_h,d_l,d_v)
            vsa = vsa_analysis(d_v,d_h,d_l,d_c) if d_v else []
            # 周成交额
            w_vols=[]
            for i in range(0,len(d_v)-1,5):
                w_vols.append(sum(d_v[i:i+5]))
            avg_vol5=sum(w_vols[-5:])/min(5,len(w_vols)) if w_vols else 0
            prev_vol5=sum(w_vols[-10:-5])/min(5,len(w_vols)-5) if len(w_vols)>=10 else avg_vol5
            vol_chg="↑+"+str(round((avg_vol5-prev_vol5)/prev_vol5*100,1))+"%" if prev_vol5>0 else "持平"
            all_results[name]={
                "dates":d_dates,"closes":d_c,
                "adx_latest":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
                "di_plus_latest":round(di_p[idx],2) if idx>=0 and di_p[idx] is not None else None,
                "di_minus_latest":round(di_m[idx],2) if idx>=0 and di_m[idx] is not None else None,
                "adx_sig":adx_signal(adx_v[idx] if idx>=0 else None,di_p[idx] if idx>=0 else None,di_m[idx] if idx>=0 else None),
                "w_dates":w_dates,"w_crsi":w_crsi,"buy_sig":buy_sig,"sell_sig":sell_sig,
                "vsa":vsa,"patterns":pats,"levels":levels,"class":"A",
                "vol_chg":vol_chg,"last_close":round(d_c[-1],2),"last_date":d_dates[-1],
            }
            print(f"  ✅ {name}: ADX={all_results[name]['adx_latest']} | 周CRSI={round(w_crsi[-1] if w_crsi and w_crsi[-1] else 0,2)} | {vol_chg}")
        except Exception as e:
            print(f"  ⚠️  {name}: {e}"); errors.append(name)
except Exception as e:
    print(f"  A股数据加载失败: {e}")

# ── 2c. HK + INT 市场 ───────────────────────────────────
print("\n📡 采集港股及国际市场...")
try:
    import akshare as ak
    # 恒生指数
    try:
        df_hk=ak.stock_hk_index_daily(symbol="HSI").tail(200).reset_index(drop=True)
        hk_dates=[str(row["date"])[:10] for _,row in df_hk.iterrows()]
        hk_o=[float(row["open"])for _,row in df_hk.iterrows()]
        hk_h=[float(row["high"])for _,row in df_hk.iterrows()]
        hk_l=[float(row["low"])for _,row in df_hk.iterrows()]
        hk_c=[float(row["close"])for _,row in df_hk.iterrows()]
        hk_v=[float(row.get("volume",1))for _,row in df_hk.iterrows()]
        adx_v,di_p,di_m,dx=adx_daily(hk_o,hk_h,hk_l,hk_c,14)
        idx=-1
        for i in range(len(adx_v)-1,-1,-1):
            if adx_v[i] is not None: idx=i; break
        w_crsi_hk=[None]*len(hk_c)
        buy_sig=False; sell_sig=False
        all_results["恒生指数"]={
            "dates":hk_dates,"closes":hk_c,
            "adx_latest":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
            "di_plus_latest":round(di_p[idx],2) if idx>=0 and di_p[idx] is not None else None,
            "di_minus_latest":round(di_m[idx],2) if idx>=0 and di_m[idx] is not None else None,
            "adx_sig":adx_signal(adx_v[idx] if idx>=0 else None,di_p[idx] if idx>=0 else None,di_m[idx] if idx>=0 else None),
            "w_crsi":w_crsi_hk,"buy_sig":buy_sig,"sell_sig":sell_sig,
            "vsa":[],"patterns":[],"levels":{},
            "class":"HK","last_close":round(hk_c[-1],2),"last_date":hk_dates[-1],
        }
        print(f"  ✅ 恒生指数: ADX={all_results['恒生指数']['adx_latest']}")
    except Exception as e:
        print(f"  恒生指数失败: {e}"); errors.append("恒生指数")

    # 日经225
    try:
        df_nk=ak.index_hist(symbol="NI225",adjust="0").tail(200).reset_index(drop=True)
        nk_dates=[str(row["日期"])[:10] for _,row in df_nk.iterrows()]
        nk_o=[float(row["开盘"])for _,row in df_nk.iterrows()]
        nk_h=[float(row["最高"])for _,row in df_nk.iterrows()]
        nk_l=[float(row["最低"])for _,row in df_nk.iterrows()]
        nk_c=[float(row["收盘"])for _,row in df_nk.iterrows()]
        nk_v=[float(row.get("成交额",1))for _,row in df_nk.iterrows()]
        adx_v,di_p,di_m,dx=adx_daily(nk_o,nk_h,nk_l,nk_c,14)
        idx=-1
        for i in range(len(adx_v)-1,-1,-1):
            if adx_v[i] is not None: idx=i; break
        all_results["日经225"]={
            "dates":nk_dates,"closes":nk_c,
            "adx_latest":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
            "di_plus_latest":round(di_p[idx],2) if idx>=0 and di_p[idx] is not None else None,
            "di_minus_latest":round(di_m[idx],2) if idx>=0 and di_m[idx] is not None else None,
            "adx_sig":adx_signal(adx_v[idx] if idx>=0 else None,di_p[idx] if idx>=0 else None,di_m[idx] if idx>=0 else None),
            "w_crsi":[None]*len(nk_c),"buy_sig":False,"sell_sig":False,
            "vsa":[],"patterns":[],"levels":{},
            "class":"INT","last_close":round(nk_c[-1],2),"last_date":nk_dates[-1],
        }
        print(f"  ✅ 日经225: ADX={all_results['日经225']['adx_latest']}")
    except Exception as e:
        print(f"  日经225失败: {e}"); errors.append("日经225")

except Exception as e:
    print(f"  国际市场数据加载失败: {e}")

# 合并US结果
for sym,data in us_daily.items():
    name=data["name"].replace("标普500","SPY").replace("纳指100","QQQ").replace("道琼斯","DIA").replace("恐慌指数","VIX")
    all_results[name]=data
    all_results[name]["class"]="US"
    all_results[name]["last_close"]=round(data["closes"][-1],2)
    all_results[name]["last_date"]=data["dates"][-1]
    if sym=="VIX":
        all_results[name]["adx_sig"]="恐慌指数(波动率)→"+("高位震荡(市场紧张)" if data["adx_latest"] and data["adx_latest"]>20 else "低位平稳(市场平静)")
        all_results[name]["w_crsi"]=[None]*len(data["closes"])

# DAX
dax_dates,dax_o,dax_h,dax_l,dax_c=fetch_td("DAX","1day",200)
if dax_c:
    adx_v,di_p,di_m,dx=adx_daily(dax_o,dax_h,dax_l,dax_c,14)
    idx=-1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    all_results["德国DAX"]={
        "dates":dax_dates,"closes":dax_c,
        "adx_latest":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
        "di_plus_latest":round(di_p[idx],2) if idx>=0 and di_p[idx] is not None else None,
        "di_minus_latest":round(di_m[idx],2) if idx>=0 and di_m[idx] is not None else None,
        "adx_sig":adx_signal(adx_v[idx] if idx>=0 else None,di_p[idx] if idx>=0 else None,di_m[idx] if idx>=0 else None),
        "w_crsi":[None]*len(dax_c),"buy_sig":False,"sell_sig":False,
        "vsa":[],"patterns":[],"levels":{},
        "class":"INT","last_close":round(dax_c[-1],2),"last_date":dax_dates[-1],
    }
    print(f"  ✅ 德国DAX: ADX={all_results['德国DAX']['adx_latest']}")
else:
    print("  ⚠️ DAX数据获取失败"); errors.append("DAX")

# ─── 保存中间结果 ────────────────────────────────────────────
with open("/workspace/market_report/raw_data.json","w") as f:
    json.dump({k: {
        "last_close": v.get("last_close"),
        "last_date":  v.get("last_date"),
        "adx_latest": v.get("adx_latest"),
        "di_plus":    v.get("di_plus_latest"),
        "di_minus":   v.get("di_minus_latest"),
        "adx_sig":    v.get("adx_sig"),
        "w_crsi_last":(v.get("w_crsi") or [None])[-1] if v.get("w_crsi") else None,
        "buy_sig":    v.get("buy_sig",False),
        "sell_sig":   v.get("sell_sig",False),
        "vsa":        v.get("vsa",[]),
        "patterns":   v.get("patterns",[]),
        "vol_chg":    v.get("vol_chg",""),
        "class":      v.get("class",""),
    } for k,v in all_results.items()}, f, ensure_ascii=False, indent=2)

print(f"\n✅ 数据采集完成 | 共{len(all_results)}个指数 | 失败: {errors}")
print(f"数据已保存至 /workspace/market_report/raw_data.json")
