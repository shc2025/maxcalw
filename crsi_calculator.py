#!/usr/bin/env python3
"""
CRSI (Connors Research RSI) Calculator v2
数据来源: AkShare K线 / Twelve Data K线

CRSI = (RSI_price + RSI_streak + RSI_ROC) / 3

1. RSI_price  : RSI(Close, period=3)
2. RSI_streak : RSI(连续趋势天数, period=2)
3. RSI_ROC    : RSI(ROC(Close,period=2), period=2)
"""

import subprocess, json

APIKEY = "dd4f227a11f34265936086a73b46b80c"

# ─── 基础指标 ───────────────────────────────────────

def _to_float(v):
    try:
        return float(v)
    except:
        return None

def rsi_rolling(prices, period=14):
    """滚动 RSI，返回 [val_or_None] 列表，长度与 prices 一致"""
    out = []
    gains, losses = [], []
    for i, p in enumerate(prices):
        if i == 0:
            out.append(None); continue
        diff = (prices[i] - prices[i-1]) if prices[i-1] else 0
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
        if i < period:
            out.append(None)
        elif i == period:
            ag = sum(gains[-period:]) / period
            al = sum(losses[-period:]) / period
            out.append(100.0 if al == 0 else round(100 - 100/(1 + ag/al), 4))
        else:
            ag = (gains[-1] + (period-1)*((gains[-2]*(period-1) if len(gains)>=period else 0)) / (period-1)) if period > 1 else gains[-1]
            # Wilder 平滑法
            prev_ag = (out[-1] / 100 * (period-1) + gains[-1]) / period * period if out[-1] is not None else sum(gains[-period:])/period
            prev_al = ((100-out[-1]) / 100 * (period-1) + losses[-1]) / period * period if out[-1] is not None else sum(losses[-period:])/period
            # 简化: EMA 方式
            ag_ema = gains[-1] / period + (out[-1] / 100 * (period-1)) * (period-1) / period if out[-1] is not None else sum(gains[-period:])/period
            al_ema = losses[-1] / period + ((100-out[-1]) / 100 * (period-1)) * (period-1) / period if out[-1] is not None else sum(losses[-period:])/period
            out.append(None if ag_ema is None else round(100 - 100*(al_ema/(ag_ema+1e-10)), 4))
    return out

def rsi_wilder(prices, period=3):
    """Wilder RSI (标准 CRSI 算法)"""
    # 过滤 None
    cleaned = [(i, v) for i, v in enumerate(prices) if v is not None]
    if len(cleaned) < period + 1:
        return [None] * len(prices)
    vals = [v for _, v in cleaned]
    idx_map = [i for i, _ in cleaned]

    result = [None] * len(prices)
    avg_gain = 0.0; avg_loss = 0.0
    for k in range(1, period):
        d = vals[k] - vals[k-1]
        avg_gain += max(d, 0); avg_loss += abs(min(d, 0))
    avg_gain /= period; avg_loss /= period
    init_val = 100.0 if avg_loss == 0 else 100 - 100/(1 + avg_gain/(avg_loss+1e-10))
    result[idx_map[period]] = round(init_val, 4)
    for k in range(period+1, len(vals)):
        d = vals[k] - vals[k-1]
        avg_gain = (avg_gain*(period-1) + max(d,0)) / period
        avg_loss = (avg_loss*(period-1) + abs(min(d,0))) / period
        result[idx_map[k]] = round(100.0 if avg_loss == 0 else 100 - 100/(1 + avg_gain/(avg_loss+1e-10)), 4)
    return result

def roc(closes, period=2):
    """Rate of Change"""
    out = []
    for i in range(len(closes)):
        if i < period or closes[i-period] is None or closes[i-period] == 0:
            out.append(None)
        else:
            out.append((closes[i] - closes[i-period]) / closes[i-period] * 100)
    return out

def streak_days(closes):
    """连续趋势天数: 上涨=+N, 下跌=-N"""
    if len(closes) < 2:
        return [0] * len(closes)
    s = [0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            s.append(1 if s[-1] <= 0 else s[-1] + 1)
        elif closes[i] < closes[i-1]:
            s.append(-1 if s[-1] >= 0 else s[-1] - 1)
        else:
            s.append(0)
    return s

def crsi(prices, rsi_p=3, streak_p=2, roc_p=2):
    """计算完整 CRSI 及分解"""
    rsi_price = rsi_wilder(prices, rsi_p)
    streaks    = streak_days(prices)
    rsi_streak = rsi_wilder(streaks, streak_p)
    roc_vals   = roc(prices, roc_p)
    # ROC 值中可能含 None，传入前过滤
    roc_valid = [(i,v) for i,v in enumerate(roc_vals) if v is not None]
    if len(roc_valid) >= 3:
        roc_idx = [i for i,_ in roc_valid]
        roc_v   = [v for _,v in roc_valid]
        rsi_roc_raw = rsi_wilder(roc_v, streak_p)
        rsi_roc = [None]*len(roc_vals)
        for k, v in zip(roc_idx, rsi_roc_raw):
            rsi_roc[k] = v
    else:
        rsi_roc = [None]*len(roc_vals)

    crsi_val = []
    for i in range(len(prices)):
        rp = rsi_price[i]; rs = rsi_streak[i]; rc = rsi_roc[i]
        if None not in [rp, rs, rc]:
            crsi_val.append(round((rp + rs + rc) / 3, 2))
        else:
            crsi_val.append(None)
    return {
        'crsi':      crsi_val,
        'rsi_price': [round(v,2) if v else None for v in rsi_price],
        'rsi_streak': [round(v,2) if v else None for v in rsi_streak],
        'rsi_roc':   [round(v,2) if v else None for v in rsi_roc],
        'streaks':   streaks,
    }

def signal(v):
    if v is None: return "—"
    if v >= 80: return "🔴极度超买"
    if v >= 65: return "🟠超买"
    if v >= 45: return "🟡中性"
    if v >= 35: return "🟢低估"
    return "🔵极度低估"

# ─── 获取 K 线 ────────────────────────────────────────

def get_kline_td(symbol, name, days=60):
    url = (f"https://api.twelvedata.com/time_series?symbol={symbol}"
           f"&interval=1day&outputsize={days}&apikey={APIKEY}"
           f"&start_date=2025-10-01&end_date=2026-04-17&order=asc")
    try:
        out = subprocess.run(["curl","-s","--max-time","12",url],
                            capture_output=True, text=True, timeout=15)
        d = json.loads(out.stdout)
        vals = d.get("values", [])
        if not vals:
            print(f"  [{name}] 无数据: {d.get('status','unknown')}")
            return None, None
        print(f"  [{name}] ✅ {len(vals)}根K线  ({vals[0]['datetime']} → {vals[-1]['datetime']})")
        return [float(v["close"]) for v in vals], [v["datetime"] for v in vals]
    except Exception as e:
        print(f"  [{name}] ❌ {e}")
        return None, None

def get_kline_ak(symbol, name, days=60):
    """AkShare 获取 A股日K"""
    import akshare as ak
    try:
        df = ak.stock_zh_index_daily(symbol=symbol).tail(days)
        df["date"] = df["date"].astype(str)
        closes = df["close"].astype(float).tolist()
        dates  = df["date"].tolist()
        print(f"  [{name}] ✅ {len(closes)}根K线 AkShare")
        return closes, dates
    except Exception as e:
        print(f"  [{name}] ❌ AkShare: {e}")
        return None, None

# ─── 主程序 ──────────────────────────────────────────

print("=" * 65)
print("  CRSI (Connors Research RSI) 计算器  v2")
print("  CRSI = (RSI_close + RSI_streak + RSI_ROC) / 3")
print("=" * 65)

targets = [
    ("AAPL",     "苹果 Apple",       "us"),
    ("TSLA",     "特斯拉 Tesla",    "us"),
    ("NVDA",     "英伟达 Nvidia",   "us"),
    ("SPY",      "标普500 ETF",     "us"),
    ("QQQ",      "纳斯达克100 ETF", "us"),
    ("000001.SH","上证指数",         "ak"),
    ("399006.SZ","创业板指",        "ak"),
]

results = []
for sym, name, src in targets:
    print(f"\n▶ 获取 {name} ({sym}) …")
    if src == "ak":
        closes, dates = get_kline_ak(sym, name)
    else:
        closes, dates = get_kline_td(sym, name)
    if closes is None:
        continue

    d = crsi(closes)
    crsi_vals = d['crsi']
    last = crsi_vals[-1]
    rsi_p = d['rsi_price'][-1]
    rsi_s = d['rsi_streak'][-1]
    rsi_r = d['rsi_roc'][-1]

    # 近10日
    valid10 = [v for v in crsi_vals[-10:] if v is not None]
    avg10 = sum(valid10)/len(valid10) if valid10 else None

    # 近5日趋势
    v5 = [v for v in crsi_vals[-5:] if v is not None]
    up = sum(1 for i in range(1,len(v5)) if v5[i]>v5[i-1]) if len(v5)>=2 else 0
    trend = "↑上升" if up>=3 else "↓下降" if up<=1 else "→震荡"

    print(f"  最新:  CRSI={last}  RSI_price={rsi_p}  RSI_streak={rsi_s}  RSI_ROC={rsi_r}")
    print(f"  信号:  {signal(last)}")
    if avg10:
        print(f"  均值:  近10日CRSI均值={avg10:.2f}  {trend}")

    results.append({
        'name': name, 'symbol': sym,
        'close': closes[-1], 'date': dates[-1],
        'crsi': last, 'rsi_p': rsi_p, 'rsi_s': rsi_s, 'rsi_r': rsi_r,
        'avg10': avg10, 'trend': trend,
    })

print("\n" + "=" * 65)
print("  汇总对比")
print("=" * 65)
hdr = "%-14s  %8s  %5s  %6s  %6s  %6s  %6s  %4s  %s"
print(hdr % ("标的","收盘价","CRSI","RSI(P)","RSI(S)","RSI(R)","10日均","趋势","综合信号"))
print("  " + "-" * 80)
for r in results:
    avg_str = "%.1f" % r['avg10'] if r['avg10'] else "N/A"
    row = "%-14s  %8.2f  %5.1f  %6.1f  %6.1f  %6.1f  %6s  %4s  %s" % (
        r['name'], r['close'], r['crsi'],
        r['rsi_p'], r['rsi_s'], r['rsi_r'],
        avg_str, r['trend'], signal(r['crsi']))
    print(" " + row)

print("\n  数值说明:")
print("  CRSI ≥80: 🔴极度超买(高位风险)   CRSI 65~80: 🟠超买")
print("  CRSI 45~65: 🟡中性               CRSI 35~45: 🟢低估")
print("  CRSI <35: 🔵极度低估(低位机会)")
