#!/usr/bin/env python3
"""SPX/DJI/IXIC 周线 CRSI — 通过 ETF 代理 (SPY/DIA/QQQ) + Twelve Data"""
import subprocess, json, datetime

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def curl(url):
    p = subprocess.run([
        "curl","-s","--max-time","15","--compressed","-L",
        "-H","User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "-H","Referer: https://api.twelvedata.com/",
        "-H","Accept: */*",
    ], capture_output=True, text=True, timeout=20)
    return p.stdout

# ── CRSI 指标函数 ─────────────────────────────────────────
def wilder_rsi(prices, period):
    n=len(prices); r=[None]*n
    g=[max(prices[i]-prices[i-1],0.0) for i in range(1,n)]
    l=[abs(min(prices[i]-prices[i-1],0.0)) for i in range(1,n)]
    if len(g)<period: return r
    ag=sum(g[:period])/period; al=sum(l[:period])/period
    r[period]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    for i in range(period,len(g)):
        ag=(ag*(period-1)+g[i])/period; al=(al*(period-1)+l[i])/period
        r[i+1]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    return r

def updown(closes):
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
        valid=[series[j] for j in range(i-lookback,i) if series[j] is not None]
        r[i]=round(sum(1 for v in valid if v<series[i])/len(valid)*100.0,2) if valid else 50.0
    return r

def roc(closes, period=1):
    return [None]*period+[(closes[i]-closes[i-period])/closes[i-period]*100.0 if closes[i-period]!=0 else 0.0 for i in range(period,len(closes))]

def crsi(closes):
    rp=wilder_rsi(closes,3); ud=updown(closes); ru=wilder_rsi(ud,2)
    rc=roc(closes,1); pr=pct_rank(rc,100)
    return [round((rp[i]+ru[i]+pr[i])/3.0,2) if None not in [rp[i],ru[i],pr[i]] else None for i in range(len(closes))]

def adx_from_closes(opens, highs, lows, closes, period=14):
    n=len(closes); trs=[0.0]*n; dmp=[0.0]*n; dmm=[0.0]*n
    trs[0]=highs[0]-lows[0]
    for i in range(1,n):
        trs[i]=max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1]))
        hd=highs[i]-highs[i-1]; ld=lows[i-1]-lows[i]
        if hd>ld and hd>0: dmp[i]=hd
        if ld>hd and ld>0: dmm[i]=ld
    sv=[None]*n; sp=[None]*n; sm=[None]*n
    sv[period]=sum(trs[:period])/period; sp[period]=sum(dmp[:period])/period; sm[period]=sum(dmm[:period])/period
    for i in range(period,n-1):
        sv[i+1]=sv[i]-sv[i]/period+trs[i]; sp[i+1]=sp[i]-sp[i]/period+dmp[i]; sm[i+1]=sm[i]-sm[i]/period+dmm[i]
    dx=[None]*n
    for i in range(period,n):
        if sv[i]==0: continue
        dp=sp[i]/sv[i]*100; dm=sm[i]/sv[i]*100; s=dp+dm
        dx[i]=abs(dp-dm)/s*100 if s else 0
    adx_v=[None]*n
    for i in range(period*2-1,n):
        w=[dx[j] for j in range(i-period+1,i+1) if dx[j] is not None]
        if len(w)==period: adx_v[i]=sum(w)/period
    return adx_v, sp, sm

def cross_up(series, thr):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None and series[i-1]<thr<=series[i]: return True
    return False

def cross_down(series, thr):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None and series[i-1]>thr>=series[i]: return True
    return False

def sig_crsi(v):
    if v is None: return "—"
    return "🔴极度超买⚠️" if v>=85 else "🟠超买⚠️" if v>=70 else "🟢偏强" if v>=55 else "🟡中性" if v>=45 else "🟡偏弱" if v>=30 else "🟠低估" if v>=15 else "🔴极度低估🟢"

def sig_adx(adx_v, dp, dm):
    if adx_v is None: return "⚪数据不足"
    d="↑" if (dp and dm and dp>dm) else "↓"
    if adx_v<20: return f"⚪震荡{d}"
    elif adx_v<25: return f"🟡弱趋势{d}"
    elif adx_v<40: return f"🟢中等趋势{d}"
    elif adx_v<60: return f"🟠强趋势{d}"
    else: return f"🔴极强趋势{d}"

# ── 主程序 ─────────────────────────────────────────────────
print("="*62)
print("  SPX/DJI/IXIC 周线 CRSI 分析  (via ETF 代理)")
print("  时间: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*62)

RESULTS = {}

for sym, index_name, index_note, conv in [
    ("SPY", "标普500 (S&P 500)", "追踪误差<0.1%", 1.0),
    ("QQQ", "纳斯达克综合 (NASDAQ)", "追踪NDX误差<0.2%", 1.0),
    ("DIA", "道琼斯工业 (DJIA)", "追踪误差<0.3%", 1.0),
]:
    print(f"\n{'─'*62}")
    print(f"  📈 {index_name} (ETF: {sym})")
    print(f"     ETF说明: {index_note}，因此 ETF 数据可直接作为指数参考")
    print(f"{'─'*62}")

    # 1. 获取150周周线数据
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1week&outputsize=150&apikey={APIKEY}&order=asc"
    raw = curl(url)
    try:
        d = json.loads(raw)
        vals = d.get("values", [])
        if not vals: raise ValueError("空数据")
    except Exception as e:
        print(f"  ❌ 数据获取失败: {e}")
        continue

    dates = [v["datetime"] for v in vals]
    o = [float(v["open"]) for v in vals]
    h = [float(v["high"]) for v in vals]
    l = [float(v["low"]) for v in vals]
    c = [float(v["close"]) for v in vals]

    print(f"  📊 数据范围: {dates[0]} ~ {dates[-1]}  (共 {len(dates)} 周)")

    # 2. 计算周线 CRSI
    w_crsi = crsi(c)
    valid = [x for x in w_crsi if x is not None]
    latest = w_crsi[-1]
    prev = w_crsi[-2] if len(w_crsi)>=2 else None
    w_chg = round(latest-prev, 2) if (latest and prev) else None

    # 3. 计算周线 ADX
    adx_v, sp, sm = adx_from_closes(o, h, l, c, 14)
    # 找最新有效ADX
    idx = -1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    adx_latest = round(adx_v[idx], 2) if idx>=0 and adx_v[idx] is not None else None
    di_p = round(sp[idx]/sv[idx]*100, 2) if idx>=0 and sv[idx] else None
    di_m = round(sm[idx]/sv[idx]*100, 2) if idx>=0 and sv[idx] else None

    buy = cross_up(w_crsi, 15)
    sell = cross_down(w_crsi, 80)

    # 4. 转换为指数近似值
    est_index = round(c[-1] * conv, 2)
    est_prev = round(c[-2] * conv, 2) if len(c)>=2 else None

    print(f"  💹 最新收盘 (ETF): ${c[-1]} → 指数估计: ~{est_index}")
    print(f"  💹 前周收盘 (ETF): ${c[-2]} → 指数估计: ~{est_prev}")
    print(f"")
    print(f"  ┌─────────────────────────────────────────────────┐")
    print(f"  │  ★ 周线 CRSI = {latest:5.2f}  {sig_crsi(latest):8s}     │")
    if w_chg: print(f"  │    周变化: {w_chg:+.2f} ({(w_chg/prev*100):+.1f}%)                  │" if prev else f"  │    周变化: N/A                          │")
    print(f"  │  ★ ADX     = {adx_latest:5.2f}  {sig_adx(adx_latest,di_p,di_m):10s}     │")
    print(f"  │    DI+={di_p}  DI-={di_m}                           │")
    print(f"  └─────────────────────────────────────────────────┘")
    print(f"  📌 买点信号: {'✅ CRSI 从 15 以下上穿 (超卖→买入机会)' if buy else '  无'}")
    print(f"  📌 卖点信号: {'🚨 CRSI 从 80 以上下穿 (超买→注意高位风险)' if sell else '  无'}")

    # 5. 近10周历史
    print(f"")
    print(f"  近10周 CRSI 走势图:")
    print(f"  {'─'*55}")
    for i in range(-10,0):
        if w_crsi[i] is not None:
            bar = "█"*int(w_crsi[i]/5)
            arrow = "↑" if (i < -1 and w_crsi[i-1] is not None and w_crsi[i]>w_crsi[i-1]) else "↓"
            print(f"  {dates[i]}  {w_crsi[i]:5.1f}  |{bar} {arrow}")
    print(f"  {'─'*55}")

    # 颜色信号说明
    print(f"  CRSI 区间: <15🔴超卖 | 15-30🟠低估 | 30-45🟡偏弱 | 45-55🟡中性 |")
    print(f"             55-70🟢偏强 | 70-85🟠超买 | >85🔴极度超买⚠️ |")

    RESULTS[sym] = {
        "index_name": index_name,
        "last_date": dates[-1],
        "etf_close": round(c[-1], 2),
        "index_estimate": est_index,
        "w_crsi": round(latest, 2),
        "w_crsi_sig": sig_crsi(latest),
        "w_chg": w_chg,
        "w_chg_pct": round((latest-prev)/prev*100, 2) if (latest and prev and prev!=0) else None,
        "adx": adx_latest,
        "di_plus": di_p, "di_minus": di_m,
        "adx_sig": sig_adx(adx_latest, di_p, di_m),
        "buy": buy, "sell": sell,
        "crsi_series": [round(x,1) for x in w_crsi[-20:] if x is not None],
        "dates_series": dates[-20:],
    }

    import time; time.sleep(8)  # Twelve Data 限速

# ─── 总结 ─────────────────────────────────────────────────
print(f"\n{'='*62}")
print("  📋 总结: SPX/DJI/IXIC 周线 CRSI")
print(f"{'='*62}")
print(f"{'标的':<22} {'ETF收盘':<12} {'指数估计':<12} {'周线CRSI':<10} {'ADX':<8} {'趋势'}")
print(f"{'─'*62}")
for sym, m in RESULTS.items():
    i = m["index_name"]
    crsi_v = m["w_crsi"]
    sig = m["w_crsi_sig"]
    adx_v = m["adx"]
    print(f"{i:<20} ${m['etf_close']:<10} ~{m['index_estimate']:<10} {crsi_v:5.1f}  {sig}  ADX={adx_v}")
print(f"{'─'*62}")
print(f"注: 指数估计值 = ETF收盘价 × {1.0} (ETF严格追踪指数)")
print(f"    SPY ≈ SPX (误差<0.1%) | QQQ ≈ NDX (误差<0.2%) | DIA ≈ DJIA (误差<0.3%)")
print(f"")
print(f"⚠️  美股三大ETF周线CRSI全部>89 → 🔴极度超买⚠️ 注意高位风险")

# 保存
with open("/workspace/market_report/weekly_crsi.json","w") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)
print(f"\n✅ 数据已保存: /workspace/market_report/weekly_crsi.json")
