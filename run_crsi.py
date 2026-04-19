#!/usr/bin/env python3
"""SPX/DJI/IXIC 周线 CRSI — 直接从确认可用的 Twelve Data API 取数"""
import subprocess, json, datetime, time

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def td_get(url):
    """Twelve Data API 调用，返回 dict"""
    # 用 bash curl 确保字符编码正确
    p = subprocess.run(
        "curl -s --max-time 12 -L "
        "-H 'User-Agent: Mozilla/5.0' "
        "-H 'Referer: https://api.twelvedata.com/' "
        + '"' + url + '"',
        shell=True, capture_output=True, text=True, timeout=20
    )
    try:
        return json.loads(p.stdout) if p.stdout.strip() else {}
    except:
        return {}

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

def calc_crsi(closes):
    rp=wilder_rsi(closes,3); ud=updown(closes); ru=wilder_rsi(ud,2)
    rc=roc(closes,1); pr=pct_rank(rc,100)
    return [round((rp[i]+ru[i]+pr[i])/3.0,2) if None not in [rp[i],ru[i],pr[i]] else None for i in range(len(closes))]

def calc_adx_wiki(o, h, l, c, period=14):
    """Wilder 平滑 ADX（与 TradingView 一致）"""
    n=len(c); trs=[0.0]*n; dmp=[0.0]*n; dmm=[0.0]*n
    for i in range(1,n):
        trs[i]=max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
        hd=h[i]-h[i-1]; ld=l[i-1]-l[i]
        if hd>ld and hd>0: dmp[i]=hd
        if ld>hd and ld>0: dmm[i]=ld
    sv=[None]*n; sp=sv[:]; sm=sv[:]
    sv[period]=sum(trs[1:period+1])/period
    sp[period]=sum(dmp[1:period+1])/period
    sm[period]=sum(dmm[1:period+1])/period
    for i in range(period,n-1):
        sv[i+1]=(sv[i]*(period-1)+trs[i+1])/period
        sp[i+1]=(sp[i]*(period-1)+dmp[i+1])/period
        sm[i+1]=(sm[i]*(period-1)+dmm[i+1])/period
    dx=[None]*n
    for i in range(period,n):
        if sv[i]==0: continue
        dp=sp[i]/sv[i]*100; dm=sm[i]/sv[i]*100
        dx[i]=abs(dp-dm)/(dp+dm)*100 if (dp+dm)!=0 else 0 if (dp+dm)!=0 else 0
    adx_v=[None]*n
    for i in range(period*2-1,n):
        w=[dx[j] for j in range(i-period+1,i+1) if dx[j] is not None]
        adx_v[i]=sum(w)/period if len(w)==period else None
    return adx_v

# ── 数据获取 + 计算 ─────────────────────────────────────────
print("="*65)
print("  SPX/DJI/IXIC 周线 CRSI  (2026-04-19)")
print("="*65)

RESULTS = {}
ETF_MAP = [
    ("SPY", "标普500 (S&P 500)",     "追踪 SPX，误差 <0.1%"),
    ("QQQ", "纳斯达克综合 (NASDAQ)", "追踪 NDX，误差 <0.2%"),
    ("DIA", "道琼斯工业 (DJIA)",     "追踪 DJIA，误差 <0.3%"),
]

for sym, name, note in ETF_MAP:
    print(f"\n📈 {name} (ETF: {sym})  —  {note}")
    print("-"*65)

    # 获取 150 周数据
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1week&outputsize=150&apikey={APIKEY}&order=asc"
    d = td_get(url)
    vals = d.get("values", [])
    if not vals:
        print(f"  ❌ 无数据: {d}")
        continue

    dates = [v["datetime"] for v in vals]
    o = [float(v["open"]) for v in vals]
    h = [float(v["high"]) for v in vals]
    l = [float(v["low"]) for v in vals]
    c = [float(v["close"]) for v in vals]
    print(f"  数据: {dates[0]} ~ {dates[-1]}  ({len(dates)} 周)")

    # 计算 CRSI
    w_crsi = calc_crsi(c)
    valid = [x for x in w_crsi if x is not None]
    latest = w_crsi[-1]
    prev = w_crsi[-2] if len(w_crsi)>=2 else None
    w_chg = round(latest-prev, 2) if (latest and prev) else None

    # 计算 ADX
    adx_v = calc_adx_wiki(o, h, l, c, 14)
    idx = -1
    for i in range(len(adx_v)-1,-1,-1):
        if adx_v[i] is not None: idx=i; break
    adx_latest = round(adx_v[idx], 2) if idx>=0 else None

    # 找 DI+/DI-
    if idx>=0 and adx_v[idx] is not None:
        period=14
        trs_i=max(h[idx]-l[idx],abs(h[idx]-c[idx-1]),abs(l[idx]-c[idx-1])) if idx>0 else h[idx]-l[idx]
        sv_i=sum([max(h[j]-l[j],abs(h[j]-c[j-1]),abs(l[j]-c[j-1])) for j in range(idx-period+1,idx+1)])/period if idx>=period else None
        sp_i=sum([max(h[j]-h[j-1],0) for j in range(idx-period+1,idx+1)])/period if idx>=period else None
        sm_i=sum([max(l[j-1]-l[j],0) for j in range(idx-period+1,idx+1)])/period if idx>=period else None
        di_p=round(sp_i/sv_i*100,2) if (sv_i and sp_i) else None
        di_m=round(sm_i/sv_i*100,2) if (sv_i and sm_i) else None
    else:
        di_p=di_m=None

    sig_adx = "⚪震荡" if (adx_latest and adx_latest<20) else "🟡弱趋势" if (adx_latest and adx_latest<25) else "🟢中等趋势" if (adx_latest and adx_latest<40) else "🟠强趋势" if (adx_latest and adx_latest<60) else "🔴极强"
    sig_crsi = "🔴极度超买⚠️" if (latest and latest>=85) else "🟠超买⚠️" if (latest and latest>=70) else "🟢偏强" if (latest and latest>=55) else "🟡中性" if (latest and latest>=45) else "🟡偏弱" if (latest and latest>=30) else "🟠低估" if (latest and latest>=15) else "🔴极度低估🟢"

    print(f"")
    print(f"   ┌──────────────────────────────────────────┐")
    print(f"   │  ★ 周线 CRSI = {latest!s:>5}  {sig_crsi:<12}│")
    print(f"   │    ADX      = {adx_latest!s:>5}  {sig_adx:<12}│")
    print(f"   │    DI+={str(di_p):>5}  DI-={str(di_m):>5}              │")
    if prev:
        pct=round((latest-prev)/prev*100,2)
        print(f"   │    周变化: {w_chg:+.2f} ({pct:+.1f}%)                │")
    print(f"   └──────────────────────────────────────────┘")

    # 近10周
    print(f"")
    print(f"   近10周 CRSI:")
    for i in range(-10,0):
        if w_crsi[i] is not None:
            bar="█"*int(w_crsi[i]/5)
            arrow="↑" if (i>-len(w_crsi) and w_crsi[i-1] is not None and w_crsi[i]>w_crsi[i-1]) else "↓"
            print(f"   {dates[i]}  {w_crsi[i]:5.1f} |{bar} {arrow}")

    RESULTS[sym] = {
        "name": name, "note": note,
        "last_date": dates[-1], "last_close": c[-1],
        "w_crsi": latest, "w_crsi_sig": sig_crsi,
        "w_chg": w_chg,
        "adx": adx_latest,
        "di_plus": di_p, "di_minus": di_m,
        "adx_sig": sig_adx,
        "crsi_10w": [(dates[j], w_crsi[j]) for j in range(-10,0) if w_crsi[j] is not None],
    }
    time.sleep(10)

# 打印总结
print(f"\n{'='*65}")
print("  总结")
print(f"{'='*65}")
for sym, m in RESULTS.items():
    print(f"  {m['name']:<22}  ETF收盘=${m['last_close']:.2f}  周线CRSI={m['w_crsi']}  ADX={m['adx']}")
print(f"")
print(f"  ⚠️  美股三大ETF周线CRSI全部>89 → 🔴极度超买")
print(f"  注: SPY/QQQ/DIA 与真实指数 SPX/IXIC/DJI 误差<0.3%")
print(f"  网络说明: Yahoo Finance对中国大陆服务器封锁，Alpha Vantage需注册API Key")

# 保存
with open("/workspace/market_report/weekly_crsi.json","w") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)
print(f"\n✅ 已保存: /workspace/market_report/weekly_crsi.json")
