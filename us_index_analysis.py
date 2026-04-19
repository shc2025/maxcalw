#!/usr/bin/env python3
"""
SPX/DJI/IXIC 真实指数 + 周线 CRSI 综合分析
一次性获取所有可用数据
"""
import subprocess, json, time, datetime, sys

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def curl(url, referer="https://api.twelvedata.com/", timeout=15):
    p = subprocess.run([
        "curl", "-s", f"--max-time={timeout}", "--compressed", "-L",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "-H", f"Referer: {referer}",
        "-H", "Accept: */*",
    ], capture_output=True, text=True, timeout=timeout+5)
    return p.stdout

# ─── 技术指标 ───────────────────────────────────────────────
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

def crsi_daily(closes):
    rp=wilder_rsi(closes,3); ud=updown(closes); ru=wilder_rsi(ud,2)
    rc=roc(closes,1); pr=pct_rank(rc,100)
    return [round((rp[i]+ru[i]+pr[i])/3.0,2) if None not in [rp[i],ru[i],pr[i]] else None for i in range(len(closes))]

def crsi_weekly_from_daily(closes_d, n_weeks=104):
    """从日线聚合为周线再算CRS"""
    # 按周聚合
    weekly={}
    for i,c in enumerate(closes_d[-n_weeks*7:]):
        dt=datetime.datetime.utcnow()-datetime.timedelta(days=len(closes_d[-n_weeks*7:])-i)
        wk=dt.strftime("%Y-%W")
        if wk not in weekly: weekly[wk]=c
        else: weekly[wk]=c  # 周末收市价
    wc=list(weekly.values())
    return crsi_daily(wc) if len(wc)>=105 else None

def cross_up(series, thr):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1]<thr<=series[i]: return True
    return False

def cross_down(series, thr):
    for i in range(1,len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1]>thr>=series[i]: return True
    return False

def crsi_sig(v):
    if v is None: return "—"
    return "🔴极度超买⚠️" if v>=85 else "🟠超买⚠️" if v>=70 else "🟢偏强" if v>=55 else "🟡中性" if v>=45 else "🟡偏弱" if v>=30 else "🟠低估" if v>=15 else "🔴极度低估🟢"

# ─── 主程序 ─────────────────────────────────────────────────
print("="*60)
print("  美股真实指数 + 周线 CRSI 分析  " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
print("="*60)

all_data = {}
errors = []

# ══ 1. Twelve Data SPY/QQQ/DIA 周线 CRSI (唯一可用源) ══
print("\n📡 [源A] Twelve Data ETF 周线数据 (≈真实指数)")
for sym, label, index_name, note in [
    ("SPY", "SPY≈标普500", "S&P 500", "追踪误差<0.1%"),
    ("QQQ", "QQQ≈纳斯达克", "NASDAQ-100", "追踪误差<0.2%"),
    ("DIA", "DIA≈道琼斯", "DJIA", "追踪误差<0.3%"),
]:
    print(f"\n  [{sym}] {label}")
    try:
        # 日线数据 (用于周线聚合)
        url_d = f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=730&apikey={APIKEY}&order=asc"
        raw_d = curl(url_d)
        d_daily = json.loads(raw_d)
        vals_d = d_daily.get("values", [])
        if not vals_d: raise ValueError("no daily data")
        closes_d = [float(v["close"]) for v in vals_d]
        dates_d = [v["datetime"] for v in vals_d]
        print(f"    日线: {len(closes_d)}天 ({dates_d[0]}~{dates_d[-1]})")

        # 聚合成周线
        weekly_map = {}
        for i, v in enumerate(vals_d):
            dt = datetime.datetime.strptime(v["datetime"], "%Y-%m-%d")
            wk_key = (dt.year, dt.isocalendar()[1])
            o,h,l,c = float(v["open"]),float(v["high"]),float(v["low"]),float(v["close"])
            if wk_key not in weekly_map:
                weekly_map[wk_key] = {"open":o,"high":h,"low":l,"close":c}
            else:
                weekly_map[wk_key]["high"] = max(weekly_map[wk_key]["high"], h)
                weekly_map[wk_key]["low"] = min(weekly_map[wk_key]["low"], l)
                weekly_map[wk_key]["close"] = c

        w_keys = sorted(weekly_map.keys())
        closes_w = [weekly_map[k]["close"] for k in w_keys]
        print(f"    周线: {len(closes_w)}周 (用于CRSI)")

        # 计算周线 CRSI
        w_crsi = crsi_daily(closes_w)
        valid_w = [x for x in w_crsi if x is not None]
        latest_w = w_crsi[-1] if w_crsi else None
        prev_w = w_crsi[-2] if len(w_crsi)>=2 else None
        last_wk = w_keys[-1]
        last_date_str = f"{last_wk[0]}-W{last_wk[1]:02d}"
        last_close_w = closes_w[-1]

        # ADX (从日线算)
        url_adx = f"https://api.twelvedata.com/adx?symbol={sym}&interval=1day&period=14&outputsize=100&apikey={APIKEY}"
        raw_adx = curl(url_adx)
        d_adx = json.loads(raw_adx)
        adx_vals = d_adx.get("values", [])
        adx_latest = float(adx_vals[-1]["adx"]) if adx_vals else None
        di_plus_latest = float(adx_vals[-1]["di_plus"]) if adx_vals else None
        di_minus_latest = float(adx_vals[-1]["di_minus"]) if adx_vals else None

        buy = cross_up(w_crsi, 15)
        sell = cross_down(w_crsi, 80)

        print(f"    最新周: {last_date_str} 收盘={last_close_w}")
        print(f"    周线ADX: {adx_latest} | DI+: {di_plus_latest} | DI-: {di_minus_latest}")
        print(f"    ★ 周线 CRSI: {latest_w} ({crsi_sig(latest_w)})")
        print(f"      前周: {prev_w} | 周变化: {latest_w-prev_w:+.2f if (latest_w and prev_w) else 'N/A'}")
        print(f"      买点: {'✅ CRSI上穿15' if buy else '无'} | 卖点: {'🚨 CRSI下穿80' if sell else '无'}")

        # 近10周历史
        print(f"    近10周CRSI:")
        for i in range(-10,0):
            if i>=-len(w_crsi) and w_crsi[i] is not None:
                wk=w_keys[i]; bar="█"*int(w_crsi[i]/10)
                print(f"      {wk[0]}-W{wk[1]:02d}: {w_crsi[i]:5.1f} |{bar}")

        all_data[sym] = {
            "index_name": index_name, "etf_label": label, "etf_note": note,
            "last_date": last_date_str, "last_close": round(last_close_w,2),
            "adx": round(adx_latest,2) if adx_latest else None,
            "di_plus": round(di_plus_latest,2) if di_plus_latest else None,
            "di_minus": round(di_minus_latest,2) if di_minus_latest else None,
            "w_crsi": round(latest_w,2) if latest_w else None,
            "prev_w_crsi": round(prev_w,2) if prev_w else None,
            "crsi_sig": crsi_sig(latest_w),
            "buy": buy, "sell": sell,
            "w_crsi_series": [round(x,2) if x else None for x in w_crsi[-20:]],
            "w_dates": [f"{k[0]}-W{k[1]:02d}" for k in w_keys[-20:]],
        }
        time.sleep(6)  # Twelve Data 免费限流
    except Exception as e:
        err = f"  ❌ {sym}: {str(e)}"
        print(err)
        errors.append(err)

# ══ 2. 测试 Alpha Vantage ══
print("\n📡 [源B] Alpha Vantage 测试")
try:
    url = "https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=SP500&apikey=demo"
    raw = curl(url, referer="https://www.alphavantage.co/")
    d = json.loads(raw)
    print(f"  Alpha Vantage demo: {str(d)[:200]}")
    all_data["alpha_vantage"] = {"status": "ok" if d else "empty", "data": str(d)[:200]}
except Exception as e:
    print(f"  Alpha Vantage: ❌ {e}")
    all_data["alpha_vantage"] = {"status": "error", "msg": str(e)}

# ══ 3. 测试 NASDAQ API ══
print("\n📡 [源C] NASDAQ API 测试")
try:
    url = "https://api.nasdaq.com/api/quote/SPY/info?assetclass=etf"
    raw = curl(url, referer="https://www.nasdaq.com/")
    d = json.loads(raw)
    price = d.get("data",{}).get("primaryData",{}).get("lastSalePrice")
    print(f"  NASDAQ API: price={price}")
    all_data["nasdaq"] = {"status": "ok", "price": price}
except Exception as e:
    print(f"  NASDAQ API: ❌ {e}")
    all_data["nasdaq"] = {"status": "error", "msg": str(e)}

# ─── 保存 ─────────────────────────────────────────────────
with open("/workspace/market_report/weekly_crsi.json","w") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"✅ 完成! 成功 {len([k for k in all_data if k not in ['alpha_vantage','nasdaq']])} 个标的")
print(f"错误: {len(errors)} 个")
for e in errors: print(f"  {e}")
print(f"数据已保存: /workspace/market_report/weekly_crsi.json")
print(f"{'='*60}")
