#!/usr/bin/env python3
"""
Phase 3: 大盘分析周报生成
数据来源: Twelve Data + AkShare (已验证准确)
"""
import json, subprocess, math
import akshare as ak
import pandas as pd
from datetime import datetime

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

def adx_calc(o,h,l,c,period=14):
    n=len(o); trs=[0.0]*n; dmp=[0.0]*n; dmm=[0.0]*n
    trs[0]=h[0]-l[0]
    for i in range(1,n):
        trs[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
    for i in range(1,n):
        hd=h[i]-h[i-1]; ld=l[i-1]-l[i]
        if hd>ld and hd>0: dmp[i]=hd
        if ld>hd and ld>0: dmm[i]=ld
    sv=[None]*n; sp=[None]*n; sm=[None]*n
    sv[period]=sum(trs[:period])/period; sp[period]=sum(dmp[:period])/period; sm[period]=sum(dmm[:period])/period
    for i in range(period,n-1):
        sv[i+1]=sv[i]-sv[i]/period+trs[i]; sp[i+1]=sp[i]-sp[i]/period+dmp[i]; sm[i+1]=sm[i]-sm[i]/period+dmm[i]
    dp_m=[None]*n; dm_m=[None]*n; dx=[None]*n
    for i in range(period,n):
        if sv[i]==0: continue
        dp=sp[i]/sv[i]*100; dm=sm[i]/sv[i]*100; s=dp+dm
        dp_m[i]=dp; dm_m[i]=dm; dx[i]=abs(dp-dm)/s*100 if s else 0
    adx_v=[None]*n
    for i in range(period*2-1,n):
        w=[dx[j] for j in range(i-period+1,i+1) if dx[j] is not None]
        if len(w)==period: adx_v[i]=sum(w)/period
    return adx_v,dp_m,dm_m,dx

def crsi_w(closes):
    if len(closes)<102: return [None]*len(closes)
    rp=wilder_rsi(closes,3)
    ud=[0.0]*len(closes); p=0.0
    for i in range(1,len(closes)):
        if closes[i]==closes[i-1]: p=0.0
        elif closes[i]>closes[i-1]: p=1.0 if p<=0 else p+1.0
        else: p=-1.0 if p>=0 else p-1.0
        ud[i]=p
    ru=wilder_rsi(ud,2)
    rc_out=[None]*len(closes)
    for i in range(100,len(closes)):
        cur=closes[i]; prev=closes[i-1]
        if cur is None or prev is None: continue
        roc_v=(cur-prev)/prev*100 if prev!=0 else 0
        vals=[(closes[j]-closes[j-1])/closes[j-1]*100.0 for j in range(i-99,i) if j>0 and closes[j] is not None and closes[j-1] is not None and closes[j-1]!=0]
        if vals:
            cnt=sum(1 for val in vals if val<roc_v)
            rc_out[i]=round(cnt/len(vals)*100.0,2)
        else:
            rc_out[i]=50.0
    out=[]
    for i in range(len(closes)):
        a,b,c=rp[i],ru[i],rc_out[i]
        out.append(round((a+b+c)/3.0,2) if None not in [a,b,c] else None)
    return out

def adx_signal(adx_v,dp,dm):
    if adx_v is None: return "⚪数据不足"
    direction="↑" if (dp is not None and dm is not None and dp>dm) else "↓"
    if adx_v<20: return f"⚪震荡(ADX<20){direction}"
    elif adx_v<25: return f"🟡弱趋势(ADX25~){direction}"
    elif adx_v<40: return f"🟢中等趋势(ADX40){direction}"
    elif adx_v<60: return f"🟠强趋势(ADX40~60){direction}"
    else: return f"🔴极强趋势(ADX>60){direction}"

def crsi_signal(v):
    if v is None: return "⚪数据不足"
    if v>=85: return "🔴极度超买"
    elif v>=70: return "🟠超买"
    elif v>=55: return "🟢偏强"
    elif v>=45: return "🟡中性"
    elif v>=30: return "🟡偏弱"
    elif v>=15: return "🟠低估"
    else: return "🔴极度低估"

def cross_up(series, threshold):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1]<threshold<=series[i]: return True
    return False

def cross_down(series, threshold):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1]>threshold>=series[i]: return True
    return False

def vsa(vols, highs, lows, closes):
    """威科夫量价分析（返回近5日信号）"""
    n=len(vols)
    if n<10: return []
    avg_vol=sum(vols[-20:])/min(20,n)
    results=[]
    for i in range(-5,0):
        idx=n+i
        if idx<1: continue
        vol=vols[idx]; price=closes[idx]; prev=closes[idx-1]
        pct=(price-prev)/prev*100 if prev!=0 else 0
        ratio=vol/avg_vol if avg_vol>0 else 1
        if ratio<0.8:
            if pct>1: sig="缩量上涨(供应弱)"
            elif pct<-1: sig="缩量下跌(需求弱)"
            else: sig="缩量整理"
        elif ratio>1.3:
            if pct>1: sig="放量上涨🔥"
            elif pct<-1: sig="放量下跌🔥"
            else: sig="放量震荡"
        else:
            sig="量价平稳"
        chg=f"+{pct:.2f}%" if pct>=0 else f"{pct:.2f}%"
        date_lbl=f"{(n-i-1)}日前" if i<-1 else "昨日"
        results.append({"t":date_lbl,"sig":sig,"ratio":round(ratio,1),"chg":chg})
    return results

def support_resistance(c, h, l, n=20):
    """支撑阻力位"""
    recent_h=max(h[-n:]); recent_l=min(l[-n:])
    return recent_h, recent_l

def find_pivots(h, l, c, n=20):
    """识别经典形态"""
    patterns=[]
    if n<5: return patterns
    # 价格创n日新低但未跌破
    if l[-1]<min(l[-n:-1])*1.001: patterns.append("新低破位⚠️")
    # 横盘整理
    range_pct=(max(h[-n:])-min(l[-n:]))/min(l[-n:])*100 if min(l[-n:])>0 else 0
    if range_pct<3: patterns.append(f"横盘整理({range_pct:.1f}%)")
    # 急涨后缩量
    if len(c)>=5:
        chg5=(c[-1]-c[-5])/c[-5]*100 if c[-5]!=0 else 0
        if chg5>5: patterns.append(f"急涨后观察({chg5:+.1f}%)")
    return patterns

# ─── 采集所有数据 ───────────────────────────────────────────
print("开始数据采集...")
all_data={}
report_date=datetime.now().strftime("%Y年%m月%d日")

# ── 1. US (Twelve Data) ─────────────────────────────────
us_syms=[("SPY","标普500","SP500"),("QQQ","纳指100","NASDAQ"),("DIA","道琼斯","DJIA"),("VIXY","恐慌指数VIX","VIX")]
for sym,name,_ in us_syms:
    url=f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=200&apikey={APIKEY}&order=asc"
    url_w=f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1week&outputsize=200&apikey={APIKEY}&order=asc"
    d=curl(url); dw=curl(url_w)
    vals=d.get("values",[]); wvals=dw.get("values",[])
    if not vals: print(f"  ⚠️ {name} 日线无数据"); continue
    dates=[v["datetime"]for v in vals]; o=[float(v["open"])for v in vals]; h=[float(v["high"])for v in vals]
    l_=[float(v["low"])for v in vals]; c=[float(v["close"])for v in vals]
    w_dates=[v["datetime"]for v in wvals]; w_c=[float(v["close"])for v in wvals] if wvals else []
    adx_v,dp_v,dm_v,dx_v=adx_calc(o,h,l_,c,14)
    idx=-1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    w_crsi=crsi_w(w_c) if len(w_c)>=102 else [None]*len(w_c)
    recent_h,recent_l=support_resistance(c,h,l_,20)
    vsa_sig=vsa([1.0]*len(c),h,l_,c)  # TD无vol
    pats=find_pivots(h,l_,c,20)
    w_last=w_crsi[-1] if w_crsi else None
    buy=cross_up(w_crsi,15) if w_crsi else False
    sell=cross_down(w_crsi,80) if w_crsi else False
    all_data[name]={
        "class":"US","td":sym,
        "last_date":dates[-1],"last_close":round(c[-1],2),
        "adx":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
        "di_plus":round(dp_v[idx],2) if idx>=0 and dp_v[idx] is not None else None,
        "di_minus":round(dm_v[idx],2) if idx>=0 and dm_v[idx] is not None else None,
        "adx_sig":adx_signal(adx_v[idx],dp_v[idx],dm_v[idx]) if idx>=0 else "⚪",
        "w_crsi":round(w_last,2) if w_last is not None else None,
        "crsi_sig":crsi_signal(w_last),
        "buy_sig":"✅周线买点(CRSI上穿15)" if buy else "",
        "sell_sig":"🚨周线卖点(CRSI下穿80)" if sell else "",
        "recent_high":round(recent_h,2),"recent_low":round(recent_l,2),
        "vsa":vsa_sig,"patterns":pats,
        "week_close_chg":f"{(c[-1]-c[-6])/c[-6]*100:+.2f}%" if len(c)>=6 else "N/A",
    }
    print(f"  ✅ {name}: ADX={all_data[name]['adx']} | 周线CRSI={all_data[name]['w_crsi']} | {all_data[name]['adx_sig']}")

# ── 2. A股 (AkShare) ────────────────────────────────────
print("采集A股...")
a_shares=[("sh000001","上证综指"),("sz399001","深证成指"),("sz399006","创业板指")]
for code,name in a_shares:
    try:
        df=ak.stock_zh_index_daily(symbol=code).tail(200).reset_index(drop=True)
        dates=[str(r["date"])[:10] for _,r in df.iterrows()]
        o=[float(r["open"])for _,r in df.iterrows()]; h=[float(r["high"])for _,r in df.iterrows()]
        l_=[float(r["low"])for _,r in df.iterrows()]; c=[float(r["close"])for _,r in df.iterrows()]
        v=[float(r.get("volume",1))for _,r in df.iterrows()]
        adx_v,dp_v,dm_v,dx_v=adx_calc(o,h,l_,c,14)
        idx=-1
        for i in range(len(adx_v)-1,-1,-1):
            if adx_v[i] is not None: idx=i; break
        # 周线（以5日为单位）
        w_c_=[c[i*5] if i*5<len(c) else c[-1] for i in range(len(c)//5+1)]
        w_crsi=crsi_w(w_c_) if len(w_c_)>=102 else [None]*len(w_c_)
        w_last=w_crsi[-1] if w_crsi else None
        buy=cross_up(w_crsi,15) if w_crsi else False
        sell=cross_down(w_crsi,80) if w_crsi else False
        recent_h,recent_l=support_resistance(c,h,l_,20)
        vsa_sig=vsa(v,h,l_,c)
        pats=find_pivots(h,l_,c,20)
        # 周成交额变化
        w_v=[sum(v[i*5:min((i+1)*5,len(v))])for i in range(len(v)//5+1)]
        chg5=f"{(w_v[-1]-w_v[-6])/w_v[-6]*100:+.1f}%" if len(w_v)>=6 and w_v[-6]>0 else "首周"
        all_data[name]={
            "class":"A股","ak_code":code,
            "last_date":dates[-1],"last_close":round(c[-1],2),
            "adx":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
            "di_plus":round(dp_v[idx],2) if dp_v[idx] is not None else None,
            "di_minus":round(dm_v[idx],2) if dm_v[idx] is not None else None,
            "adx_sig":adx_signal(adx_v[idx],dp_v[idx],dm_v[idx]) if idx>=0 else "⚪",
            "w_crsi":round(w_last,2) if w_last is not None else None,
            "crsi_sig":crsi_signal(w_last),
            "buy_sig":"✅周线买点(CRSI上穿15)" if buy else "",
            "sell_sig":"🚨周线卖点(CRSI下穿80)" if sell else "",
            "recent_high":round(recent_h,2),"recent_low":round(recent_l,2),
            "vsa":vsa_sig,"patterns":pats,
            "week_close_chg":chg5,
        }
        print(f"  ✅ {name}: ADX={all_data[name]['adx']} | 周线CRSI={all_data[name]['w_crsi']} | 周量变化={chg5}")
    except Exception as e:
        print(f"  ⚠️ {name}: {e}")

# ── 3. 恒生指数 ─────────────────────────────────────────
print("采集恒生指数...")
try:
    df_hk=ak.stock_hk_daily(symbol="HSI",adjust="qfq").tail(200).reset_index(drop=True)
    dates=[str(r["date"])[:10] for _,r in df_hk.iterrows()]
    o=[float(r["open"])for _,r in df_hk.iterrows()]; h=[float(r["high"])for _,r in df_hk.iterrows()]
    l_=[float(r["low"])for _,r in df_hk.iterrows()]; c=[float(r["close"])for _,r in df_hk.iterrows()]
    v=[float(r.get("volume",1))for _,r in df_hk.iterrows()]
    adx_v,dp_v,dm_v,dx_v=adx_calc(o,h,l_,c,14)
    idx=-1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    recent_h,recent_l=support_resistance(c,h,l_,20)
    vsa_sig=vsa(v,h,l_,c)
    pats=find_pivots(h,l_,c,20)
    w_c_=[c[i*5]if i*5<len(c)else c[-1]for i in range(len(c)//5+1)]
    w_crsi=crsi_w(w_c_) if len(w_c_)>=102 else [None]*len(w_c_)
    w_last=w_crsi[-1] if w_crsi else None
    all_data["恒生指数"]={
        "class":"HK",
        "last_date":dates[-1],"last_close":round(c[-1],2),
        "adx":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
        "di_plus":round(dp_v[idx],2) if dp_v[idx] is not None else None,
        "di_minus":round(dm_v[idx],2) if dm_v[idx] is not None else None,
        "adx_sig":adx_signal(adx_v[idx],dp_v[idx],dm_v[idx]) if idx>=0 else "⚪",
        "w_crsi":round(w_last,2) if w_last is not None else None,
        "crsi_sig":crsi_signal(w_last),
        "buy_sig":"","sell_sig":"",
        "recent_high":round(recent_h,2),"recent_low":round(recent_l,2),
        "vsa":vsa_sig,"patterns":pats,
        "week_close_chg":f"{(c[-1]-c[-6])/c[-6]*100:+.2f}%" if len(c)>=6 else "N/A",
    }
    print(f"  ✅ 恒生指数: ADX={all_data['恒生指数']['adx']} | DI+={all_data['恒生指数']['di_plus']} | DI-={all_data['恒生指数']['di_minus']}")
except Exception as e:
    print(f"  ⚠️ 恒生指数: {e}")

# ── 4. VIX恐慌指数(用VIXY替代) ──────────────────────────
try:
    df_vixy=ak.stock_us_daily(symbol="VIXY",adjust="qfq").tail(200).reset_index(drop=True)
    dates_v=[str(r["date"])[:10] for _,r in df_vixy.iterrows()]
    c_v=[float(r["close"])for _,r in df_vixy.iterrows()]
    o_v=[float(r["open"])for _,r in df_vixy.iterrows()]
    h_v=[float(r["high"])for _,r in df_vixy.iterrows()]
    l_v=[float(r["low"])for _,r in df_vixy.iterrows()]
    adx_v,dp_v,dm_v,dx_v=adx_calc(o_v,h_v,l_v,c_v,14)
    idx=-1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    all_data["恐慌指数(VIXY)"]={
        "class":"US","td":"VIXY",
        "last_date":dates_v[-1],"last_close":round(c_v[-1],2),
        "adx":round(adx_v[idx],2) if idx>=0 and adx_v[idx] is not None else None,
        "di_plus":round(dp_v[idx],2) if dp_v[idx] is not None else None,
        "di_minus":round(dm_v[idx],2) if dm_v[idx] is not None else None,
        "adx_sig":"波动率指数(ADX不代表趋势方向)" if adx_v[idx] is not None else "⚪",
        "w_crsi":None,"crsi_sig":"","buy_sig":"","sell_sig":"",
        "recent_high":round(max(h_v[-20:]),2),"recent_low":round(min(l_v[-20:]),2),
        "vsa":[],"patterns":[],
        "week_close_chg":f"{(c_v[-1]-c_v[-6])/c_v[-6]*100:+.2f}%" if len(c_v)>=6 else "N/A",
    }
    print(f"  ✅ 恐慌指数(VIXY): {dates_v[-1]} 收盘={c_v[-1]:.2f}")
except Exception as e:
    print(f"  ⚠️ VIXY: {e}")

# ─── 历史相似场景分析 ─────────────────────────────────────
print("\n历史相似场景分析...")
hist_data={}
try:
    df_sh=ak.stock_zh_index_daily(symbol="sh000001").tail(500).reset_index(drop=True)
    closes_sh=[float(x)for x in df_sh["close"]]; dates_sh=[str(x)[:10]for x in df_sh["date"]]
    n=len(closes_sh)
    recent_chg=(closes_sh[-1]-closes_sh[-2])/closes_sh[-2]*100
    recent_5chg=(closes_sh[-1]-closes_sh[-5])/closes_sh[-5]*100 if n>=5 else 0
    adx_sh,dp_sh,dm_sh,_=adx_calc([float(x)for x in df_sh["open"]],
                                   [float(x)for x in df_sh["high"]],
                                   [float(x)for x in df_sh["low"]],closes_sh,14)
    idx_sh=-1
    for i in range(len(adx_sh)-1,-1,-1):
        if adx_sh[i] is not None: idx_sh=i; break
    # 历史上在相似ADX区间的表现
    similar_adx=[(dates_sh[i],closes_sh[i],adx_sh[i])for i in range(14,len(adx_sh))
                if adx_sh[i] is not None and abs(adx_sh[i]-(adx_sh[idx_sh] or 0))<3]
    # 大跌(>3%)后市场表现
    big_drops=[]
    for i in range(1,n):
        chg=(closes_sh[i]-closes_sh[i-1])/closes_sh[i-1]*100
        if chg<-3 and i<n-1:
            rebound=(closes_sh[i+1]-closes_sh[i])/closes_sh[i]*100 if i+1<n else 0
            next5=(closes_sh[min(i+5,n-1)]-closes_sh[i])/closes_sh[i]*100 if i+5<n else 0
            big_drops.append((dates_sh[i],round(chg,2),round(rebound,2),round(next5,2)))
    hist_data={
        "recent_chg":round(recent_chg,2),
        "recent_5chg":round(recent_5chg,2),
        "recent_adx":round(adx_sh[idx_sh],2) if idx_sh>=0 and adx_sh[idx_sh] is not None else None,
        "similar_scenes":similar_adx[-5:] if similar_adx else [],
        "big_drops":big_drops[-5:] if big_drops else [],
        "avg_rebound":round(sum(x[2]for x in big_drops)/len(big_drops),2) if big_drops else 0,
        "avg_5day_recover":round(sum(x[3]for x in big_drops)/len(big_drops),2) if big_drops else 0,
    }
    print(f"  上证近期: {recent_chg:+.2f}% (5日: {recent_5chg:+.2f}%) ADX≈{hist_data['recent_adx']}")
    print(f"  历史大跌>3%: {len(big_drops)}次 平均次日反弹:{hist_data['avg_rebound']:+.2f}%  5日修复:{hist_data['avg_5day_recover']:+.2f}%")
    if big_drops: print(f"  近期3次: {big_drops[-3:]}")
except Exception as e:
    print(f"  历史分析 ERR: {e}")

# ─── 保存 ─────────────────────────────────────────────────
with open("/workspace/market_report/all_data.json","w") as f:
    json.dump({"markets":all_data,"hist":hist_data,"date":report_date,"gen_time":datetime.now().isoformat()},f,ensure_ascii=False,indent=2)
print(f"\n✅ 数据汇总完成，共{len(all_data)}个指数/ETF")
