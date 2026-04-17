#!/usr/bin/env python3
"""
CRSI + HA RSI Engine — 参照用户 TradingView Pine Script V1.1
参数:
  lenRSI=3, lenUpDown=2, lenROC=100
  crsi_lower=15, crsi_upper=80
  ha_rsi_length=24, ha_smoothing=3
  ha_rsi_oversold=30, ha_rsi_overbought=70, confirm_window=3
信号:
  买入: CRSI上穿15  卖出: CRSI下穿80
  做多过滤: HA实体低点<=30  做空过滤: HA实体高点>=70
"""

import subprocess, json, math

APIKEY = "dd4f227a11f34265936086a73b46b80c"

# ──────────────────────────────────────────
# 基础指标
# ──────────────────────────────────────────

def ema(vals, period):
    if not vals or period <= 0:
        return [None] * len(vals) if vals else []
    k = 2.0 / (period + 1)
    result = [None] * len(vals)
    i0 = next((i for i, v in enumerate(vals) if v is not None), None)
    if i0 is None:
        return result
    result[i0] = vals[i0]
    for i in range(i0 + 1, len(vals)):
        if vals[i] is None:
            continue
        result[i] = vals[i] * k + result[i - 1] * (1 - k) if result[i - 1] is not None else vals[i]
    return result

def wilder_rsi(prices, period):
    """Wilder RSI — 等同于 Pine Script ta.rma"""
    n = len(prices)
    result = [None] * n
    gains, losses = [], []
    for i in range(1, n):
        d = (prices[i] - prices[i - 1]) if (prices[i] is not None and prices[i - 1] is not None) else 0
        gains.append(max(d, 0))
        losses.append(abs(min(d, 0)))
    if period < 1 or len(gains) < period:
        return result
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    val0 = 100.0 if al == 0 else 100.0 - (100.0 / (1.0 + ag / (al + 1e-10)))
    result[period] = val0
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
        result[i + 1] = 100.0 if al == 0 else 100.0 - (100.0 / (1.0 + ag / (al + 1e-10)))
    return [round(v, 4) if v is not None else None for v in result]

def roc(prices, period):
    out = []
    for i in range(len(prices)):
        if i < period or prices[i - period] is None or prices[i] is None:
            out.append(None)
        else:
            prev = prices[i - period]
            out.append((prices[i] - prev) / prev * 100.0 if prev != 0 else 0.0)
    return out

def streak_days(closes):
    """连续趋势天数: 上涨=+N, 下跌=-N, 平盘=0"""
    if len(closes) < 2:
        return [0] * len(closes)
    s = [0]
    for i in range(1, len(closes)):
        if closes[i] is None or closes[i - 1] is None:
            s.append(0); continue
        if closes[i] > closes[i - 1]:
            s.append(1 if s[-1] <= 0 else s[-1] + 1)
        elif closes[i] < closes[i - 1]:
            s.append(-1 if s[-1] >= 0 else s[-1] - 1)
        else:
            s.append(0)
    return s

def rma(vals, period):
    """Wilder RMA"""
    if not vals or period <= 0:
        return [None] * len(vals) if vals else []
    alpha = 1.0 / period
    result = [None] * len(vals)
    i0 = next((i for i, v in enumerate(vals) if v is not None), None)
    if i0 is None:
        return result
    result[i0] = vals[i0]
    for i in range(i0 + 1, len(vals)):
        if vals[i] is None:
            result[i] = result[i - 1] if result[i - 1] is not None else None
        else:
            result[i] = vals[i] * alpha + result[i - 1] * (1 - alpha) if result[i - 1] is not None else vals[i]
    return result

# ──────────────────────────────────────────
# CRSI
# ──────────────────────────────────────────

def calc_crsi(closes, lenRSI=3, lenUpDown=2, lenROC=100):
    rsi_price  = wilder_rsi(closes, lenRSI)
    streaks    = streak_days(closes)
    rsi_updown = wilder_rsi(streaks, lenUpDown)
    roc_vals  = roc(closes, lenROC)
    rsi_roc   = wilder_rsi(roc_vals, lenUpDown)
    crsi = []
    for i in range(len(closes)):
        rp = rsi_price[i]; ru = rsi_updown[i]; rc = rsi_roc[i]
        if None not in [rp, ru, rc]:
            crsi.append(round((rp + ru + rc) / 3.0, 2))
        else:
            crsi.append(None)
    return crsi, rsi_price, rsi_updown, rsi_roc

# ──────────────────────────────────────────
# Heikin Ashi OHLC
# ──────────────────────────────────────────

def calc_ha_ohlc(opens, highs, lows, closes):
    n = len(opens)
    ha_c = [(opens[i] + highs[i] + lows[i] + closes[i]) / 4.0 for i in range(n)]
    ha_o = [None] * n
    ha_o[0] = (opens[0] + closes[0]) / 2.0
    for i in range(1, n):
        ha_o[i] = (ha_o[i - 1] + ha_c[i - 1]) / 2.0
    ha_h = [max(highs[i], ha_o[i], ha_c[i]) for i in range(n)]
    ha_l = [min(lows[i], ha_o[i], ha_c[i]) for i in range(n)]
    return ha_o, ha_h, ha_l, ha_c

# ──────────────────────────────────────────
# HA RSI
# ──────────────────────────────────────────

def calc_ha_rsi(ha_close, ha_rsi_length=24, ha_smoothing=3):
    rsi_ha = wilder_rsi(ha_close, ha_rsi_length)
    ha_rsi = rsi_ha if ha_smoothing <= 1 else rma(rsi_ha, ha_smoothing)
    return [round(v, 4) if v is not None else None for v in ha_rsi], rsi_ha

# ──────────────────────────────────────────
# 信号生成
# ──────────────────────────────────────────

def generate_signals(crsi_vals, ha_close, ha_open,
                    crsi_lower=15, crsi_upper=80,
                    ha_rsi_oversold=30, ha_rsi_overbought=70,
                    confirm_window=3,
                    direction="做多方向"):

    ha_hp = [max(ha_open[i], ha_close[i]) for i in range(len(ha_close))]
    ha_lp = [min(ha_open[i], ha_close[i]) for i in range(len(ha_close))]

    prev_crsi = None
    prev_hp = None; prev_lp = None
    buy_bar = None; ha_buy_confirmed = False
    sell_bar = None; ha_sell_confirmed = False

    sigs = []
    is_long = (direction == "做多方向")

    for i in range(len(crsi_vals)):
        c = crsi_vals[i]
        hc = ha_close[i]; ho = ha_open[i]
        hp = ha_hp[i]; lp = ha_lp[i]

        buy_raw = (prev_crsi is not None and c is not None and
                   prev_crsi < crsi_lower <= c)
        sell_raw = (prev_crsi is not None and c is not None and
                     prev_crsi > crsi_upper >= c)

        ha_buy_ok = False; ha_sell_ok = False

        if buy_raw:
            buy_bar = i; ha_buy_confirmed = False
        if sell_raw:
            sell_bar = i; ha_sell_confirmed = False

        if buy_bar is not None and (i - buy_bar) <= confirm_window:
            if prev_lp is not None:
                if is_long and lp <= prev_lp:
                    ha_buy_ok = True; buy_bar = None
                elif not is_long and hp >= prev_hp:
                    ha_buy_ok = True; buy_bar = None
            if buy_bar is not None and (i - buy_bar) == confirm_window:
                buy_bar = None

        if sell_bar is not None and (i - sell_bar) <= confirm_window:
            if prev_hp is not None:
                if is_long and hp >= prev_hp:
                    ha_sell_ok = True; sell_bar = None
                elif not is_long and lp <= prev_lp:
                    ha_sell_ok = True; sell_bar = None
            if sell_bar is not None and (i - sell_bar) == confirm_window:
                sell_bar = None

        ha_rsi_ok_buy  = (lp is not None and lp <= ha_rsi_oversold)
        ha_rsi_ok_sell = (hp is not None and hp >= ha_rsi_overbought)

        buy_sig  = ha_buy_ok  and ha_rsi_ok_buy
        sell_sig = ha_sell_ok and ha_rsi_ok_sell

        if is_long:
            pass
        else:
            buy_sig, sell_sig = sell_sig, buy_sig

        sigs.append({
            "crsi": c,
            "ha_hp": hp, "ha_lp": lp,
            "buy_raw": buy_raw, "sell_raw": sell_raw,
            "buy_signal": buy_sig, "sell_signal": sell_sig,
        })

        prev_crsi = c; prev_hp = hp; prev_lp = lp

    return sigs

# ──────────────────────────────────────────
# 信号解读
# ──────────────────────────────────────────

def crsi_zone(v):
    if v is None: return "N/A"
    if v >= 80: return "🔴极度超买"
    if v >= 65: return "🟠超买"
    if v >= 50: return "🟡偏多"
    if v >= 35: return "🟢偏空"
    if v >= 15: return "🔵低估"
    return "🟦极低估"

# ──────────────────────────────────────────
# 数据获取
# ──────────────────────────────────────────

def get_kline(symbol, name, days=150):
    url = ("https://api.twelvedata.com/time_series?symbol=%s"
           "&interval=1day&outputsize=%d&apikey=%s"
           "&start_date=2025-07-01&end_date=2026-04-17&order=asc") % (
           symbol, days, APIKEY)
    try:
        proc = subprocess.run(["curl","-s","--max-time","15",url],
                            capture_output=True, text=True, timeout=20)
        d = json.loads(proc.stdout)
        vals = d.get("values", [])
        if not vals:
            return None
        def f(key): return [float(v[key]) for v in vals]
        return {"name": name, "symbol": symbol,
                "dates": [v["datetime"] for v in vals],
                "opens": f("open"), "highs": f("high"),
                "lows": f("low"),  "closes": f("close")}
    except Exception as e:
        print("ERR:", e)
        return None

# ──────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────

print("=" * 70)
print("  CRSI + HA RSI 分析  (TradingView Pine Script V1.1 规则)")
print("  CRSI = (RSI_c,3 + RSI(updown,2) + RSI(ROC,100),2) / 3")
print("  HA_RSI = EMA( RSI(HA_close,24), 3 )")
print("  买入: CRSI上穿15+HA低点<=30  |  卖出: CRSI下穿80+HA高点>=70")
print("=" * 70)

targets = [
    ("AAPL",  "苹果 Apple",      150),
    ("TSLA",  "特斯拉 Tesla",    150),
    ("NVDA",  "英伟达 Nvidia",   150),
    ("SPY",   "标普500 ETF",   150),
    ("QQQ",   "纳指100 ETF",   150),
    ("BRK.B", "伯克希尔B",      150),
    ("DOW",   "陶氏化学 DOW",  150),
]

RESULTS = []

for sym, name, days in targets:
    print("\n▶ %s (%s) ..." % (name, sym))
    d = get_kline(sym, name, days)
    if d is None:
        print("  ❌ 获取失败"); continue

    ha_o, ha_h, ha_l, ha_c = calc_ha_ohlc(d["opens"], d["highs"], d["lows"], d["closes"])
    crsi_vals, rsi_price, rsi_updown, rsi_roc = calc_crsi(d["closes"], 3, 2, 100)
    ha_rsi_vals, _ = calc_ha_rsi(ha_c, 24, 3)
    sigs = generate_signals(crsi_vals, ha_c, ha_o, 15, 80, 30, 70, 3, "做多方向")

    n = len(crsi_vals)
    lc  = crsi_vals[-1]
    lhr = ha_rsi_vals[-1] if ha_rsi_vals else None
    lhp = max(ha_o[-1], ha_c[-1])
    llp = min(ha_o[-1], ha_c[-1])
    lha_c = ha_c[-1]; lha_o = ha_o[-1]
    bull = lha_c > lha_o
    close = d["closes"][-1]
    date  = d["dates"][-1]

    buy_cnt  = sum(1 for s in sigs[-30:] if s["buy_signal"])
    sell_cnt = sum(1 for s in sigs[-30:] if s["sell_signal"])

    v5 = [v for v in crsi_vals[-5:] if v is not None]
    up = sum(1 for i in range(1, len(v5))) if len(v5) >= 2 else 0
    trend = "↑上升" if up >= 3 else "↓下降" if up <= 1 else "→震荡"

    print("  ✅ %s  收盘 $%.2f  %s" % (date, close, "🟢阳HA" if bull else "🔴阴HA"))
    print("     CRSI = %s  %s" % (lc, crsi_zone(lc)))
    if lhr:
        print("     HA实体: 高=%.2f 低=%.2f  HA_RSI=%.1f" % (lhp, llp, lhr))
    print("     做多信号:%d次  做空信号:%d次  近5日:%s" % (buy_cnt, sell_cnt, trend))
    print("     ── CRSI构成 ──")
    print("       RSI(close,3)   = %s" % ("%.1f" % rsi_price[-1]  if rsi_price[-1]  else "N/A"))
    print("       RSI(updown,2) = %s" % ("%.1f" % rsi_updown[-1] if rsi_updown[-1] else "N/A"))
    print("       RSI(ROC,100)×2 = %s" % ("%.1f" % rsi_roc[-1]   if rsi_roc[-1]   else "N/A"))

    RESULTS.append({
        "name": name, "symbol": sym, "date": date,
        "close": close,
        "crsi": lc,
        "ha_rsi": lhr,
        "ha_high": lhp, "ha_low": llp,
        "rsi_price": rsi_price[-1] if rsi_price else None,
        "rsi_updown": rsi_updown[-1] if rsi_updown else None,
        "rsi_roc": rsi_roc[-1] if rsi_roc else None,
        "bull": bull,
        "buy": buy_cnt, "sell": sell_cnt,
        "trend": trend,
    })

print("\n" + "=" * 70)
print("  汇总 (做多方向)")
print("=" * 70)
print("  %-12s  %7s  %5s  %5s  %5s  %4s  %4s  %4s  %-10s  %s" % (
    "标的","收盘价","CRSI","HA_RSI","RSI(P)","做多","做空","趋势","HA状态","CRSI区"))
print("  " + "-" * 80)
for r in RESULTS:
    hrsi_s = "%.1f" % r["ha_rsi"] if r["ha_rsi"] else "N/A"
    rp_s   = "%.1f" % r["rsi_price"]  if r["rsi_price"]  else "N/A"
    ha_s   = "🟢阳HA" if r["bull"] else "🔴阴HA"
    print("  %-12s  %7.2f  %5.1f  %5s  %5s  %4d  %4d  %4s  %-10s  %s" % (
        r["name"], r["close"], r["crsi"], hrsi_s, rp_s,
        r["buy"], r["sell"], r["trend"], ha_s, crsi_zone(r["crsi"])))

print("\n  CRSI阈值: ≥80🔴极度超买  |  65~80🟠超买  |  50~65🟡偏多  |  35~50🟢偏空  |  15~35🔵低估  |  <15🟦极低估")
print("  HA_RSI阈值: >70超买区域  |  <30超卖区域")
