#!/usr/bin/env python3
"""
完整大盘分析数据更新脚本
1. A股: 用AkShare获取300日历史 → 计算日线CRSI（替代周线CRSI）
2. 美股: 等yfinance限流恢复后抓取^SPX ^DJI ^IXIC真实指数
3. 全球: Twelve Data SPY/QQQ/DIA作为备用
"""
import subprocess, json, time, sys
import akshare as ak

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def curl(url):
    p = subprocess.run(["curl","-s","--max-time","15",url],capture_output=True,text=True,timeout=20)
    try: return json.loads(p.stdout)
    except: return {}

def wilder_rsi(prices, period):
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

def streak_updown(closes):
    ud=[0.0]*len(closes); p=0.0
    for i in range(1,len(closes)):
        if closes[i]==closes[i-1]: p=0.0
        elif closes[i]>closes[i-1]: p=1.0 if p<=0 else p+1.0
        else: p=-1.0 if p>=0 else p-1.0
        ud[i]=p
    return ud

def pct_rank(series, lookback):
    n=len(series); r=[None]*n
    for i in range(lookback,n):
        if series[i] is None: continue
        valid=[series[j] for j in range(i-lookback,i) if series[j] is not None]
        if not valid: r[i]=50.0
        else: r[i]=round(sum(1 for v in valid if v<series[i])/len(valid)*100.0,2)
    return r

def roc(closes, period=1):
    out=[]
    for i in range(len(closes)):
        if i<period: out.append(None)
        else:
            prev=closes[i-period]
            out.append((closes[i]-prev)/prev*100.0 if prev!=0 else 0.0)
    return out

def crsi_daily(closes):
    """日线CRSI（只用200日数据）"""
    n=len(closes)
    rp=wilder_rsi(closes,3)
    ud=streak_updown(closes)
    ru=wilder_rsi(ud,2)
    rc_vals=roc(closes,1)
    pr=pct_rank(rc_vals,100)
    out=[]
    for i in range(n):
        a,b,c=rp[i],ru[i],pr[i]
        out.append(round((a+b+c)/3.0,2) if None not in [a,b,c] else None)
    return out

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

def crsi_sig(v):
    if v is None: return "—"
    if v>=85: return "🔴极度超买"
    elif v>=70: return "🟠超买"
    elif v>=55: return "🟢偏强"
    elif v>=45: return "🟡中性"
    elif v>=30: return "🟡偏弱"
    elif v>=15: return "🟠低估"
    else: return "🔴极度低估"

def adx_sig(adx_v,dp,dm):
    if adx_v is None: return "⚪数据不足"
    direction="↑" if (dp is not None and dm is not None and dp>dm) else "↓"
    if adx_v<20: return f"⚪震荡(ADX<20){direction}"
    elif adx_v<25: return f"🟡弱趋势(ADX 20~25){direction}"
    elif adx_v<40: return f"🟢中等趋势(ADX 25~40){direction}"
    elif adx_v<60: return f"🟠强趋势(ADX 40~60){direction}"
    else: return f"🔴极强趋势(ADX>60){direction}"

print("="*55)
print("  大盘数据更新  " + time.strftime("%Y-%m-%d %H:%M"))
print("="*55)

# ─── 1. A股 日线CRSI (300日) ──────────────────────────────
print("\n📡 A股数据...")
a_data={}
a_codes=[("sh000001","上证综指"),("sz399001","深证成指"),("sz399006","创业板指")]
for code,name in a_codes:
    try:
        df=ak.stock_zh_index_daily(symbol=code).tail(320).reset_index(drop=True)
        dates=[str(r["date"])[:10] for _,r in df.iterrows()]
        o=[float(r["open"])for _,r in df.iterrows()]
        h_=[float(r["high"])for _,r in df.iterrows()]
        l_=[float(r["low"])for _,r in df.iterrows()]
        c=[float(r["close"])for _,r in df.iterrows()]
        v=[float(r.get("volume",1))for _,r in df.iterrows()]
        print(f"  {name}: {len(dates)}日数据 {dates[0]}~{dates[-1]}")
        # ADX
        adv,dpm,dmm,dxv=adx_calc(o,h_,l_,c,14)
        idx=-1
        for i in range(len(adv)-1,-1,-1):
            if adv[i] is not None: idx=i; break
        # 日线CRSI
        daily_crsi=crsi_daily(c)
        d_crsi=daily_crsi[-1] if daily_crsi else None
        buy=cross_up(daily_crsi,15)
        sell=cross_down(daily_crsi,80)
        # 周成交额
        w_v=[sum(v[i:min(i+5,len(v))]) for i in range(0,len(v)-1,5)]
        chg_vol="—"
        if len(w_v)>=3 and w_v[-2]>0:
            chg_vol=f"{(w_v[-1]-w_v[-2])/w_v[-2]*100:+.1f}%"
        a_data[name]={
            "last_close":round(c[-1],2),"last_date":dates[-1],
            "adx":round(adv[idx],2) if idx>=0 and adv[idx] is not None else None,
            "di_plus":round(dpm[idx],2) if dpm[idx] is not None else None,
            "di_minus":round(dmm[idx],2) if dmm[idx] is not None else None,
            "adx_sig":adx_sig(adv[idx] if idx>=0 else None, dpm[idx] if idx>=0 else None, dmm[idx] if idx>=0 else None),
            "crsi_daily":round(d_crsi,2) if d_crsi is not None else None,
            "crsi_sig":crsi_sig(d_crsi),
            "buy_sig":"✅日线买点(CRSI上穿15)" if buy else "",
            "sell_sig":"🚨日线卖点(CRSI下穿80)" if sell else "",
            "vol_chg":chg_vol,
            "recent_high":round(max(h_[-30:]),2),"recent_low":round(min(l_[-30:]),2),
            "class":"A股"
        }
        print(f"  ✅ {name}: ADX={a_data[name]['adx']} | 日CRSI={d_crsi} | {a_data[name]['crsi_sig']}")
    except Exception as e:
        print(f"  ⚠️ {name}: {e}")

# ─── 2. 美股 yfinance ──────────────────────────────────
print("\n📡 美股真实指数 (yfinance)...")
us_data={}
us_tickers=[("^SPX","标普500","SPX"),("^DJI","道琼斯","DJI"),("^IXIC","纳斯达克","IXIC")]
try:
    import yfinance as yf
    for sym,name,td in us_tickers:
        try:
            tk=yf.Ticker(sym)
            h=tk.history(period="3mo")
            if h.empty: raise ValueError("empty")
            o=[float(x) for x in h["Open"]]
            h_=[float(x) for x in h["High"]]
            l_=[float(x) for x in h["Low"]]
            c=[float(x) for x in h["Close"]]
            dates=[str(x)[:10] for x in h.index]
            adv,dpm,dmm,dxv=adx_calc(o,h_,l_,c,14)
            idx=-1
            for i in range(len(adv)-1,-1,-1):
                if adv[i] is not None: idx=i; break
            # yfinance 日线CRSI
            daily_crsi=crsi_daily(c)
            d_crsi=daily_crsi[-1] if daily_crsi else None
            buy=cross_up(daily_crsi,15)
            sell=cross_down(daily_crsi,80)
            us_data[name]={
                "td":td,"symbol":sym,
                "last_close":round(c[-1],2),"last_date":dates[-1],
                "adx":round(adv[idx],2) if idx>=0 and adv[idx] is not None else None,
                "di_plus":round(dpm[idx],2) if dpm[idx] is not None else None,
                "di_minus":round(dmm[idx],2) if dmm[idx] is not None else None,
                "adx_sig":adx_sig(adv[idx] if idx>=0 else None,dpm[idx] if idx>=0 else None,dmm[idx] if idx>=0 else None),
                "crsi_daily":round(d_crsi,2) if d_crsi is not None else None,
                "crsi_sig":crsi_sig(d_crsi),
                "buy_sig":"✅日线买点(CRSI上穿15)" if buy else "",
                "sell_sig":"🚨日线卖点(CRSI下穿80)" if sell else "",
                "class":"US"
            }
            print(f"  ✅ {name}({sym}): ADX={us_data[name]['adx']} | 日CRSI={d_crsi} | {us_data[name]['adx_sig']}")
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️ {name}({sym}): {e}")
except Exception as e:
    print(f"  yfinance加载失败: {e}")

# ─── 3. 备用: Twelve Data SPY/QQQ/DIA ──────────────────
print("\n📡 美股ETF备用 (Twelve Data)...")
td_tickers=[("SPY","标普500ETF","标普500"),("QQQ","纳指100ETF","纳指"),("DIA","道琼斯ETF","道琼斯")]
for sym,name,label in td_tickers:
    if label in us_data: continue  # 已有真实指数
    url=f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=200&apikey={APIKEY}&order=asc"
    d=curl(url); vals=d.get("values",[])
    if not vals: print(f"  ⚠️ {name}: 无数据"); continue
    o=[float(v["open"])for v in vals]; h_=[float(v["high"])for v in vals]
    l_=[float(v["low"])for v in vals]; c=[float(v["close"])for v in vals]
    dates=[v["datetime"]for v in vals]
    adv,dpm,dmm,dxv=adx_calc(o,h_,l_,c,14)
    idx=-1
    for i in range(len(adv)-1,-1,-1):
        if adv[i] is not None: idx=i; break
    us_data[name]={
        "td":sym,"last_close":round(c[-1],2),"last_date":dates[-1],
        "adx":round(adv[idx],2) if idx>=0 and adv[idx] is not None else None,
        "di_plus":round(dpm[idx],2) if dpm[idx] is not None else None,
        "di_minus":round(dmm[idx],2) if dmm[idx] is not None else None,
        "adx_sig":adx_sig(adv[idx] if idx>=0 else None,dpm[idx] if idx>=0 else None,dmm[idx] if idx>=0 else None),
        "crsi_daily":None,"crsi_sig":"—","buy_sig":"","sell_sig":"",
        "class":"US"
    }
    print(f"  ✅ {name}: ADX={us_data[name]['adx']}")

# ─── 4. 恒生指数 ──────────────────────────────────────
print("\n📡 恒生指数...")
try:
    df_hk=ak.stock_hk_daily(symbol="HSI",adjust="qfq").tail(200).reset_index(drop=True)
    dates=[str(r["date"])[:10] for _,r in df_hk.iterrows()]
    o=[float(r["open"])for _,r in df_hk.iterrows()]
    h_=[float(r["high"])for _,r in df_hk.iterrows()]
    l_=[float(r["low"])for _,r in df_hk.iterrows()]
    c=[float(r["close"])for _,r in df_hk.iterrows()]
    v=[float(r.get("volume",1))for _,r in df_hk.iterrows()]
    adv,dpm,dmm,dxv=adx_calc(o,h_,l_,c,14)
    idx=-1
    for i in range(len(adv)-1,-1,-1):
        if adv[i] is not None: idx=i; break
    daily_crsi=crsi_daily(c)
    d_crsi=daily_crsi[-1] if daily_crsi else None
    a_data["恒生指数"]={
        "last_close":round(c[-1],2),"last_date":dates[-1],
        "adx":round(adv[idx],2) if idx>=0 and adv[idx] is not None else None,
        "di_plus":round(dpm[idx],2) if dpm[idx] is not None else None,
        "di_minus":round(dmm[idx],2) if dmm[idx] is not None else None,
        "adx_sig":adx_sig(adv[idx] if idx>=0 else None,dpm[idx] if idx>=0 else None,dmm[idx] if idx>=0 else None),
        "crsi_daily":round(d_crsi,2) if d_crsi is not None else None,
        "crsi_sig":crsi_sig(d_crsi),
        "buy_sig":"","sell_sig":"",
        "class":"HK"
    }
    print(f"  ✅ 恒生指数: ADX={a_data['恒生指数']['adx']} | DI+={a_data['恒生指数']['di_plus']} | DI-={a_data['恒生指数']['di_minus']}")
except Exception as e:
    print(f"  ⚠️ 恒生指数: {e}")

# ─── 5. VIXY (恐慌指数) ───────────────────────────────
print("\n📡 恐慌指数...")
try:
    df_vix=ak.stock_us_daily(symbol="VIXY",adjust="qfq").tail(200).reset_index(drop=True)
    c_v=[float(x)for x in df_vix["close"]]
    d_v=[str(x)[:10]for x in df_vix["date"]]
    a_data["恐慌指数(VIXY)"]={
        "last_close":round(c_v[-1],2),"last_date":d_v[-1],
        "class":"US","td":"VIXY"
    }
    print(f"  ✅ VIXY: {d_v[-1]} ${c_v[-1]:.2f}")
except Exception as e:
    print(f"  ⚠️ VIXY: {e}")

# ─── 保存 ─────────────────────────────────────────────
all_data={**us_data,**a_data}
with open("/workspace/market_report/all_data.json","w") as f:
    json.dump(all_data,f,ensure_ascii=False,indent=2)
print(f"\n✅ 完成! 共{len(all_data)}个标的")
print("标的列表:", list(all_data.keys()))
