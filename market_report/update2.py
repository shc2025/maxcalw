#!/usr/bin/env python3
"""大盘分析完整数据更新"""
import subprocess, json, time, sys
import akshare as ak

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def curl(url):
    p = subprocess.run(["curl","-s","--max-time","15",url],capture_output=True,text=True,timeout=20)
    try: return json.loads(p.stdout)
    except: return {}

# ─── 指标函数 ────────────────────────────────────────────
def wilder_rsi(prices, period):
    n = len(prices)
    r = [None] * n
    g, l = [], []
    for i in range(1, n):
        d = prices[i] - prices[i-1]
        g.append(max(d, 0.0))
        l.append(abs(min(d, 0.0)))
    if len(g) < period:
        return r
    ag = sum(g[:period]) / period
    al = sum(l[:period]) / period
    r[period] = 100.0 if al == 0 else 100.0 - (100.0 / (1.0 + ag / (al + 1e-10)))
    for i in range(period, len(g)):
        ag = (ag * (period-1) + g[i]) / period
        al = (al * (period-1) + l[i]) / period
        r[i+1] = 100.0 if al == 0 else 100.0 - (100.0 / (1.0 + ag / (al + 1e-10)))
    return r

def streak_updown(closes):
    ud = [0.0] * len(closes)
    p = 0.0
    for i in range(1, len(closes)):
        if closes[i] == closes[i-1]:
            p = 0.0
        elif closes[i] > closes[i-1]:
            p = 1.0 if p <= 0 else p + 1.0
        else:
            p = -1.0 if p >= 0 else p - 1.0
        ud[i] = p
    return ud

def pct_rank(series, lookback):
    n = len(series)
    r = [None] * n
    for i in range(lookback, n):
        if series[i] is None:
            continue
        valid = [series[j] for j in range(i-lookback, i) if series[j] is not None]
        if not valid:
            r[i] = 50.0
        else:
            cnt = sum(1 for v in valid if v < series[i])
            r[i] = round(cnt / len(valid) * 100.0, 2)
    return r

def roc(closes, period=1):
    out = []
    for i in range(len(closes)):
        if i < period:
            out.append(None)
        else:
            prev = closes[i-period]
            out.append((closes[i] - prev) / prev * 100.0 if prev != 0 else 0.0)
    return out

def crsi_daily(closes):
    """日线CRSI - 只需200+天数据"""
    n = len(closes)
    rp = wilder_rsi(closes, 3)
    ud = streak_updown(closes)
    ru = wilder_rsi(ud, 2)
    rc_vals = roc(closes, 1)
    pr = pct_rank(rc_vals, 100)
    out = []
    for i in range(n):
        a, b, c_val = rp[i], ru[i], pr[i]
        out.append(round((a+b+c_val)/3.0, 2) if None not in [a, b, c_val] else None)
    return out

def adx_calc(o, h, l, c, period=14):
    n = len(o)
    trs = [0.0] * n
    dmp = [0.0] * n
    dmm = [0.0] * n
    trs[0] = h[0] - l[0]
    for i in range(1, n):
        trs[i] = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
    for i in range(1, n):
        hd = h[i] - h[i-1]
        ld = l[i-1] - l[i]
        if hd > ld and hd > 0:
            dmp[i] = hd
        if ld > hd and ld > 0:
            dmm[i] = ld
    sv = [None] * n
    sp = [None] * n
    sm = [None] * n
    sv[period] = sum(trs[:period]) / period
    sp[period] = sum(dmp[:period]) / period
    sm[period] = sum(dmm[:period]) / period
    for i in range(period, n-1):
        sv[i+1] = sv[i] - sv[i]/period + trs[i]
        sp[i+1] = sp[i] - sp[i]/period + dmp[i]
        sm[i+1] = sm[i] - sm[i]/period + dmm[i]
    di_p = [None] * n
    di_m = [None] * n
    dx = [None] * n
    for i in range(period, n):
        if sv[i] == 0:
            continue
        dp = sp[i] / sv[i] * 100.0
        dm = sm[i] / sv[i] * 100.0
        di_p[i] = dp
        di_m[i] = dm
        s = dp + dm
        dx[i] = abs(dp - dm) / s * 100.0 if s != 0 else 0.0
    adx_v = [None] * n
    for i in range(period*2-1, n):
        w = [dx[j] for j in range(i-period+1, i+1) if dx[j] is not None]
        if len(w) == period:
            adx_v[i] = sum(w) / period
    return adx_v, di_p, di_m, dx

def cross_up(series, threshold):
    for i in range(1, len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1] < threshold <= series[i]:
                return True
    return False

def cross_down(series, threshold):
    for i in range(1, len(series)):
        if series[i] is not None and series[i-1] is not None:
            if series[i-1] > threshold >= series[i]:
                return True
    return False

def sig_adx(adx_v, dp, dm):
    if adx_v is None:
        return "⚪数据不足"
    direction = "↑" if (dp is not None and dm is not None and dp > dm) else "↓"
    if adx_v < 20:
        return f"⚪震荡(ADX<20){direction}"
    elif adx_v < 25:
        return f"🟡弱趋势(ADX 20~25){direction}"
    elif adx_v < 40:
        return f"🟢中等趋势(ADX 25~40){direction}"
    elif adx_v < 60:
        return f"🟠强趋势(ADX 40~60){direction}"
    else:
        return f"🔴极强趋势(ADX>60){direction}"

def sig_crsi(v):
    if v is None:
        return "—"
    if v >= 85:
        return "🔴极度超买"
    elif v >= 70:
        return "🟠超买"
    elif v >= 55:
        return "🟢偏强"
    elif v >= 45:
        return "🟡中性"
    elif v >= 30:
        return "🟡偏弱"
    elif v >= 15:
        return "🟠低估"
    else:
        return "🔴极度低估"

def calc_idx(symbol, name, o, h, l, c, dates):
    """计算单个指数的技术指标"""
    adv, dpm, dmm, dxv = adx_calc(o, h, l, c, 14)
    idx = -1
    for i in range(len(adv)-1, -1, -1):
        if adv[i] is not None:
            idx = i
            break
    d_crsi = crsi_daily(c)
    latest_crsi = d_crsi[-1] if d_crsi else None
    buy = cross_up(d_crsi, 15)
    sell = cross_down(d_crsi, 80)
    return {
        "last_close": round(c[-1], 2),
        "last_date": dates[-1],
        "adx": round(adv[idx], 2) if idx >= 0 and adv[idx] is not None else None,
        "di_plus": round(dpm[idx], 2) if dpm[idx] is not None else None,
        "di_minus": round(dmm[idx], 2) if dmm[idx] is not None else None,
        "adx_sig": sig_adx(adv[idx] if idx >= 0 else None, dpm[idx] if idx >= 0 else None, dmm[idx] if idx >= 0 else None),
        "crsi_daily": round(latest_crsi, 2) if latest_crsi is not None else None,
        "crsi_sig": sig_crsi(latest_crsi),
        "buy_sig": "✅买点(CRSI上穿15)" if buy else "",
        "sell_sig": "🚨卖点(CRSI下穿80)" if sell else "",
    }

# ─── 主程序 ──────────────────────────────────────────────
all_data = {}

print("=== A股 ===")
a_codes = [("sh000001","上证综指"), ("sz399001","深证成指"), ("sz399006","创业板指")]
for code, name in a_codes:
    try:
        df = ak.stock_zh_index_daily(symbol=code).tail(320).reset_index(drop=True)
        dates = [str(r["date"])[:10] for _, r in df.iterrows()]
        o = [float(r["open"]) for _, r in df.iterrows()]
        h = [float(r["high"]) for _, r in df.iterrows()]
        l = [float(r["low"]) for _, r in df.iterrows()]
        c = [float(r["close"]) for _, r in df.iterrows()]
        print(f"  {name}: {len(dates)}天 {dates[0]}~{dates[-1]}")
        r = calc_idx(code, name, o, h, l, c, dates)
        r["class"] = "A股"
        all_data[name] = r
        print(f"  → ADX={r['adx']} 日CRSI={r['crsi_daily']} {r['crsi_sig']}")
    except Exception as e:
        print(f"  ⚠️ {name}: {e}")

print("\n=== 美股 yfinance ===")
us_yf = [("^SPX","标普500","US"), ("^DJI","道琼斯","US"), ("^IXIC","纳斯达克","US")]
try:
    import yfinance as yf
    for sym, name, cls in us_yf:
        try:
            tk = yf.Ticker(sym)
            h = tk.history(period="3mo")
            if h.empty:
                raise ValueError("empty")
            dates = [str(x)[:10] for x in h.index]
            o = [float(x) for x in h["Open"]]
            h2 = [float(x) for x in h["High"]]
            l = [float(x) for x in h["Low"]]
            c = [float(x) for x in h["Close"]]
            r = calc_idx(sym, name, o, h2, l, c, dates)
            r["class"] = "US"
            r["symbol"] = sym
            all_data[name] = r
            print(f"  ✅ {name}({sym}): ADX={r['adx']} 日CRSI={r['crsi_daily']} 收盘={r['last_close']}")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ {name}({sym}): {e}")
except Exception as e:
    print(f"  yfinance加载失败: {e}")

print("\n=== 恒生指数 ===")
try:
    df_hk = ak.stock_hk_daily(symbol="HSI", adjust="qfq").tail(300).reset_index(drop=True)
    dates = [str(r["date"])[:10] for _, r in df_hk.iterrows()]
    o = [float(r["open"]) for _, r in df_hk.iterrows()]
    h = [float(r["high"]) for _, r in df_hk.iterrows()]
    l = [float(r["low"]) for _, r in df_hk.iterrows()]
    c = [float(r["close"]) for _, r in df_hk.iterrows()]
    r = calc_idx("HSI", "恒生指数", o, h, l, c, dates)
    r["class"] = "HK"
    all_data["恒生指数"] = r
    print(f"  ✅ 恒生指数: ADX={r['adx']} DI+={r['di_plus']} DI-={r['di_minus']} {r['adx_sig']}")
except Exception as e:
    print(f"  ⚠️ 恒生: {e}")

print("\n=== 恐慌指数VIXY ===")
try:
    df_v = ak.stock_us_daily(symbol="VIXY", adjust="qfq").tail(200).reset_index(drop=True)
    c_v = float(df_v["close"].iloc[-1])
    d_v = str(df_v["date"].iloc[-1])[:10]
    all_data["恐慌指数(VIXY)"] = {
        "class": "US", "td": "VIXY",
        "last_close": round(c_v, 2), "last_date": d_v,
    }
    print(f"  ✅ VIXY: {d_v} ${c_v:.2f}")
except Exception as e:
    print(f"  ⚠️ VIXY: {e}")

# 保存
with open("/workspace/market_report/all_data.json", "w") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
print(f"\n✅ 完成! 共{len(all_data)}个标的: {list(all_data.keys())}")
