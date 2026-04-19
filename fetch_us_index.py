#!/usr/bin/env python3
"""
综合测试：SPX/DJI/IXIC 真实指数数据获取
同时获取周线历史用于 CRSI 计算
"""
import subprocess, json, time, sys, re

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def curl(url, method="GET", data=None, headers=None, timeout=15):
    h = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    if headers:
        for k, v in headers.items():
            h[k] = v
    args = ["curl", "-s", f"--max-time={timeout}", "--compressed", "-L"]
    for k, v in h.items():
        args += ["-H", f"{k}: {v}"]
    if method == "POST" and data:
        args += ["-X", "POST", "-d", data]
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout + 5)
    return p.stdout

def parse_price(raw):
    """从各种格式中提取价格"""
    patterns = [
        r'"regularMarketPrice"\s*:\s*([0-9.]+)',
        r'"price"\s*:\s*([0-9.]+)',
        r'([0-9]{2,4}\.[0-9]{2})',
    ]
    for pat in patterns:
        m = re.search(pat, str(raw)[:2000])
        if m:
            return float(m.group(1))
    return None

results = {"current": {}, "weekly": {}, "sources": []}

# ════════════════════════════════════════════════════════
# 1. Yahoo Finance v8 (quote) — 测试真实可达性
# ════════════════════════════════════════════════════════
print("=== 测试1: Yahoo Finance v8 ===")
for sym, label in [("^SPX","标普500"),("^DJI","道琼斯"),("^IXIC","纳斯达克")]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5y"
    raw = curl(url, headers={
        "Referer": "https://finance.yahoo.com/",
        "Origin": "https://finance.yahoo.com"
    })
    try:
        d = json.loads(raw)
        meta = d.get("chart",{}).get("result",[{}])[0].get("meta",{})
        price = meta.get("regularMarketPrice")
        print(f"  ✅ {label}({sym}): ${price} (range={meta.get("currentTradingPeriod",{}).get("regular",{}).get("start",{})})")
        results["current"][sym] = {"price": price, "source": "Yahoo Finance v8"}
        # 提取周线历史 (按周聚合)
        timestamps = d["chart"]["result"][0]["timestamp"]
        ohlcv = d["chart"]["result"][0]["indicators"]["quote"][0]
        # 转换为周线
        weekly = aggregate_weekly(timestamps, ohlcv.get("open",[]), ohlcv.get("high",[]),
                                   ohlcv.get("low",[]), ohlcv.get("close",[]), ohlcv.get("volume",[]))
        results["weekly"][sym] = weekly
        print(f"     周线: {len(weekly)} 周 {weekly[-1] if weekly else 'none'}")
        time.sleep(1.5)
    except Exception as e:
        print(f"  ❌ {label}({sym}): {str(e)[:100]}")
        results["sources"].append(f"Yahoo v8: {e}")

# ════════════════════════════════════════════════════════
# 2. Alpha Vantage (无需 key 的 DEMO 模式)
# ════════════════════════════════════════════════════════
print("\n=== 测试2: Alpha Vantage DEMO ===")
# Demo key 有固定限额，但可以直接测
for sym, label, mkt in [("SPX","标普500","INDEX"),("DJI","道琼斯","INDEX"),("IXIC","纳斯达克","INDEX")]:
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={sym}&outputsize=full&apikey=demo&datatype=csv"
    raw = curl(url, timeout=20)
    lines = raw.strip().split('\n')
    if len(lines) > 2:
        last = lines[-1].split(',')
        price = last[4] if len(last) > 4 else None
        print(f"  ✅ {label}({sym}): 现货={price}, 共{len(lines)-1}天")
        results["current"][f"AV_{sym}"] = {"price": float(price) if price else None, "source": "Alpha Vantage Demo"}
        results["sources"].append(f"Alpha Vantage: OK {len(lines)-1} days")
    else:
        print(f"  ❌ {label}({sym}): {raw[:200]}")
        results["sources"].append(f"Alpha Vantage: FAIL")
    time.sleep(1)

# ════════════════════════════════════════════════════════
# 3. Twelve Data ADX 已有数据，直接展示
# ════════════════════════════════════════════════════════
print("\n=== 测试3: Twelve Data (已有ADX数据) ===")
for sym, name in [("SPY","标普500ETF"),("QQQ","纳指ETF"),("DIA","道琼斯ETF")]:
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=200&apikey={APIKEY}&order=asc"
    d = json.loads(curl(url))
    vals = d.get("values", [])
    if vals:
        last = vals[-1]
        print(f"  ✅ {name}({sym}): close={last['close']} date={last['datetime']}")
        results["current"][sym] = {"price": float(last["close"]), "source": "Twelve Data (ETF替代)"}
    time.sleep(2)

# ════════════════════════════════════════════════════════
# 4. 全球指数聚合 (展示已知数据)
# ════════════════════════════════════════════════════════
print("\n=== 已知数据汇总 ===")
known = {
    "^SPX (标普500)": {"price": None, "note": "yfinance限流中，请稍后重试"},
    "^DJI (道琼斯)": {"price": None, "note": "yfinance限流中，请稍后重试"},
    "^IXIC (纳斯达克)": {"price": None, "note": "yfinance限流中，请稍后重试"},
    "SPY (ETF≈SPX)": {"price": 710.14, "source": "Twelve Data"},
    "QQQ (ETF≈纳指)": {"price": 648.85, "source": "Twelve Data"},
    "DIA (ETF≈DJI)": {"price": 494.22, "source": "Twelve Data"},
}
for k, v in known.items():
    print(f"  {k}: {v}")

print("\n=== 数据源可用性 ===")
for s in results["sources"]:
    print(f"  {s}")

# ════════════════════════════════════════════════════════
# 周线 CRSI 计算辅助
# ════════════════════════════════════════════════════════
def aggregate_weekly(timestamps, opens, highs, lows, closes, volumes):
    """将日线数据聚合成周线 (每周最后一个交易日为结算价)"""
    import datetime
    weekly_data = {}
    for i, ts in enumerate(timestamps):
        dt = datetime.datetime.utcfromtimestamp(ts)
        # ISO周: YYYY-Www (周一开始)
        wk = dt.strftime("%Y-W%W")
        if wk not in weekly_data:
            weekly_data[wk] = {
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": closes[i] if i < len(closes) else None,
                "volume": volumes[i] if i < len(volumes) else 0,
            }
        else:
            w = weekly_data[wk]
            w["high"] = max(w["high"] or 0, highs[i] or 0)
            w["low"] = min(w["low"] or 1e10, lows[i] or 1e10)
            w["close"] = closes[i] if closes[i] else w["close"]
            w["volume"] = (w["volume"] or 0) + (volumes[i] or 0)
    out = []
    for wk in sorted(weekly_data.keys()):
        d = weekly_data[wk]
        out.append({
            "week": wk,
            "open": round(d["open"], 2) if d["open"] else None,
            "high": round(d["high"], 2) if d["high"] else None,
            "low": round(d["low"], 2) if d["low"] else None,
            "close": round(d["close"], 2) if d["close"] else None,
            "volume": int(d["volume"] or 0),
        })
    return out

# ════════════════════════════════════════════════════════
# CRSI 周线计算
# ════════════════════════════════════════════════════════
def calc_crsi(closes):
    """Connors RSI 周线版"""
    def wilder_rsi(prices, period):
        n = len(prices); r = [None]*n
        g, l = [], []
        for i in range(1, n):
            g.append(max(prices[i]-prices[i-1], 0.0))
            l.append(abs(min(prices[i]-prices[i-1], 0.0)))
        if len(g) < period: return r
        ag = sum(g[:period])/period; al = sum(l[:period])/period
        r[period] = 100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
        for i in range(period, len(g)):
            ag = (ag*(period-1)+g[i])/period; al = (al*(period-1)+l[i])/period
            r[i+1] = 100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
        return r

    def updown(closes):
        ud = [0.0]*len(closes); p = 0.0
        for i in range(1, len(closes)):
            if closes[i]==closes[i-1]: p=0.0
            elif closes[i]>closes[i-1]: p = 1.0 if p<=0 else p+1.0
            else: p = -1.0 if p>=0 else p-1.0
            ud[i]=p
        return ud

    def pct_rank(series, lookback):
        n = len(series); r = [None]*n
        for i in range(lookback, n):
            valid = [series[j] for j in range(i-lookback,i) if series[j] is not None]
            if not valid: r[i] = 50.0
            else: r[i] = round(sum(1 for v in valid if v<series[i])/len(valid)*100.0, 2)
        return r

    def roc(closes, period=1):
        return [None]*period + [(closes[i]-closes[i-period])/closes[i-period]*100.0 if closes[i-period]!=0 else 0.0 for i in range(period, len(closes))]

    n = len(closes)
    rp = wilder_rsi(closes, 3)
    ud = updown(closes)
    ru = wilder_rsi(ud, 2)
    rc_vals = roc(closes, 1)
    pr = pct_rank(rc_vals, 100)
    out = []
    for i in range(n):
        a,b,c = rp[i], ru[i], pr[i]
        out.append(round((a+b+c)/3.0, 2) if None not in [a,b,c] else None)
    return out

# ════════════════════════════════════════════════════════
# 用 Twelve Data 计算 ETF 周线 CRSI
# ════════════════════════════════════════════════════════
print("\n=== ETF 周线 CRSI 计算 (SPY/QQQ/DIA) ===")
for sym, name, label in [("SPY","标普500ETF","SPX"),("QQQ","纳指100ETF","IXIC"),("DIA","道琼斯ETF","DJI")]:
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1week&outputsize=150&apikey={APIKEY}&order=asc"
    raw = curl(url)
    try:
        d = json.loads(raw)
        vals = d.get("values", [])
        if len(vals) >= 105:
            closes = [float(v["close"]) for v in vals]
            weekly_crsi = calc_crsi(closes)
            last = weekly_crsi[-1]
            print(f"  ✅ {name}({sym}): {len(vals)}周数据, 最新周CRSI={last}")
        else:
            print(f"  ⚠️ {name}({sym}): 仅{len(vals)}周(需要104+周), 使用日线数据补充")
    except Exception as e:
        print(f"  ❌ {name}({sym}): {e}")

# 保存结果
with open("/workspace/fetch_results.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n✅ 结果已保存到 /workspace/fetch_results.json")
