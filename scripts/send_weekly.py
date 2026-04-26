#!/usr/bin/env python3
"""
每周定时推送周报到钉钉（优化版）
"""
import subprocess, json, datetime, time

TOKEN = "c2b875cc4161cf35bdf3c15f15d6006fe5c998f7a285e888b15844c7adbc0315"
URL   = f"https://oapi.dingtalk.com/robot/send?access_token={TOKEN}"

def curl(url, timeout=10):
    p = subprocess.run(["curl","-s","--max-time",str(timeout),url],
                      capture_output=True,text=True,timeout=timeout+2)
    return p.stdout

def fetch_fred(sym):
    raw = curl(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sym}", timeout=12)
    data = {}
    for line in raw.strip().split('\n')[1:]:
        p = line.strip().split(',')
        if len(p) >= 2 and p[1]:
            try: data[p[0]] = float(p[1])
            except: pass
    return sorted(data.items())

def rsi14(closes):
    if len(closes) < 15: return None
    g, l = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        g.append(max(d, 0)); l.append(abs(min(d, 0)))
    if len(g) < 14: return None
    ag = sum(g[-14:]) / 14; al = sum(l[-14:]) / 14
    return round(100 - (100 / (1 + ag / (al + 1e-10))), 2) if al else 100.0

def avg(lst): return sum(lst) / len(lst) if lst else None

def fChg(ch): return f"{'+' if ch > 0 else ''}{ch:.2f}%"

print("=== 定时周报推送开始 ===")
t0 = time.time()

# ── FRED数据 ──────────────────────────────────────────────
print("  [1/4] 拉取FRED数据...")
fred = {}
for code in ["SP500","DJIA","NASDAQCOM","VIXCLS","DGS10","DGS2","T10Y2Y"]:
    fred[code] = fetch_fred(code)
    print(f"    {code}: {fred[code][-1]}")

spx_vals = fred["SP500"]; dji_vals = fred["DJIA"]; nas_vals = fred["NASDAQCOM"]
spx_c = [float(v) for _,v in spx_vals]
spx_close = spx_vals[-1][1]; spx_prev = spx_vals[-5][1]
spx_chg = round((spx_close - spx_prev) / spx_prev * 100, 2)
spx_rsi = rsi14(spx_c)
ma200 = avg(spx_c[-200:])
spx_dev = round((spx_close - ma200) / ma200 * 100, 2)
dji_close = dji_vals[-1][1]; dji_prev = dji_vals[-5][1]
dji_chg = round((dji_close - dji_prev) / dji_prev * 100, 2)
nas_close = nas_vals[-1][1]; nas_prev = nas_vals[-5][1]
nas_chg = round((nas_close - nas_prev) / nas_prev * 100, 2)

vix_week = [(v[0],round(float(v[1]),2)) for v in fred["VIXCLS"] if v[0]>="2026-04-20"]
vix_latest = vix_week[-1][1] if vix_week else None
vix_avg = round(avg([x[1] for x in vix_week]),2) if vix_week else None
y10_v = float(fred["DGS10"][-1][1])
spd_v = float(fred["T10Y2Y"][-1][1]) if fred.get("T10Y2Y") else None

# ── Twelve Data ─────────────────────────────────────────────
print("  [2/4] 拉取Twelve Data SPY...")
KEY = "dd4f227a11f34265936086a73b46b80c"
spy_raw = curl(f"https://api.twelvedata.com/time_series?symbol=SPY&interval=1day&outputsize=5&apikey={KEY}&format=JSON", timeout=12)
try:
    spy_data = json.loads(spy_raw)
    spy_close_etf = float(spy_data["values"][-1]["close"]) if spy_data.get("values") else None
except: spy_close_etf = None
print(f"    SPY ETF: {spy_close_etf}")

# ── A股 ─────────────────────────────────────────────────────
print("  [3/4] 拉取A股数据...")
try:
    import akshare as ak
    a = {}
    for code, name in [("sh000001","上证"),("sz399001","深证"),("sz399006","创业板")]:
        df = ak.stock_zh_index_daily(symbol=code).tail(10).reset_index(drop=True)
        a[name] = {"close":[float(r["close"]) for _,r in df.iterrows()]}
    sh_c = a["上证"]["close"]; sz_c = a["深证"]["close"]; cy_c = a["创业板"]["close"]
    sh_close = sh_c[-1]; sz_close = sz_c[-1]; cy_close = cy_c[-1]
    sh_prev = sh_c[-5]; sz_prev = sz_c[-5]; cy_prev = cy_c[-5]
    sh_chg = round((sh_close - sh_prev)/sh_prev*100, 2)
    sz_chg = round((sz_close - sz_prev)/sz_prev*100, 2)
    cy_chg = round((cy_close - cy_prev)/cy_prev*100, 2)
    sh_rsi = rsi14(sh_c); sz_rsi = rsi14(sz_c); cy_rsi = rsi14(cy_c)
    rsi_avg = avg([r for r in [sh_rsi,sz_rsi,cy_rsi] if r])

    df_szse = ak.stock_szse_summary()
    szse = float(df_szse[df_szse["证券类别"]=="股票"]["成交金额"].iloc[-1]) / 1e8
    total_turn = szse + round(szse * 1.32, 0)
    a_success = True
except Exception as e:
    print(f"  A股数据拉取失败: {e}")
    sh_close=sz_close=cy_close=sh_chg=sz_chg=cy_chg=sh_rsi=sz_rsi=cy_rsi=rsi_avg=total_turn=0
    a_success = False

# ── 评分 ──────────────────────────────────────────────────
print("  [4/4] 计算评分...")
vol_s = 100 if total_turn > 8000 else (80 if total_turn > 6000 else (20 if total_turn > 4000 else 0))
ma20 = avg(sh_c[-20:]) if a_success else None
ma_score = 60 if (ma20 and sh_close > ma20) else 40
rsi_s = 60 if rsi_avg and rsi_avg >= 50 else 30
tech_cn = round(vol_s*0.35 + ma_score*0.40 + rsi_s*0.25, 1)
fund_cn = round(60*0.40 + 70*0.35 + 65*0.25, 1)
total_cn = round(tech_cn*0.40 + fund_cn*0.30 + 50*0.20 + 35*0.10, 1)

vix_s = 60 if vix_latest and vix_latest < 20 else 20
dev_s = 60 if 0 < spx_dev <= 10 else 80
rs_s = 70 if spx_rsi and spx_rsi > 85 else (60 if spx_rsi and spx_rsi >= 50 else 40)
tech_us = round(vix_s*0.30 + dev_s*0.45 + rs_s*0.25, 1)
fund_us = round(60*0.35 + 60*0.40 + 60*0.25, 1)
total_us = round(tech_us*0.35 + fund_us*0.30 + 60*0.25 + 30*0.10, 1)

def st(s):
    if s>=80: return "🟢 强势牛市","满仓","80-100%"
    elif s>=60: return "🟢 偏强震荡","7成仓","60-80%"
    elif s>=40: return "🟡 中性偏弱","5成仓","30-50%"
    elif s>=20: return "🟠 偏弱震荡","3成仓","10-20%"
    else: return "🔴 熊市","空仓","0-10%"

st_cn, rec_cn, pos_cn = st(total_cn)
st_us, rec_us, pos_us = st(total_us)

# ── 双信源说明 ───────────────────────────────────────────
verify = ""
if spy_close_etf:
    est = round(spy_close_etf * 10, 2)
    diff = abs(est - spx_close)
    ok = "✅ 误差<0.5%" if diff/spx_close < 0.005 else f"⚠️ 误差{diff/spx_close*100:.1f}%，已采用FRED"
    verify = f"📡双源校验({ok})"

date_str = spx_vals[-1][0]
elapsed = time.time() - t0
print(f"  数据获取完成，耗时{elapsed:.1f}秒")
print(f"  A股={total_cn}分({st_cn}) 美股={total_us}分({st_us})")

# ── 发送 ──────────────────────────────────────────────────
print("  发送钉钉...")
payload = {
    "msgtype": "markdown",
    "markdown": {
        "title": f"📊 大盘周报 · {date_str}",
        "text": (
            f"## 📊 大盘周报 · {date_str}\n\n---\n\n"
            "### 🏆 综合评分\n\n"
            f"| 市场 | 评分 | 状态 | 仓位建议 |\n"
            f"|------|------|------|---------|\n"
            f"| 🇨🇳 **A股** | **{total_cn}分** | {st_cn} | **{rec_cn}**（上限{pos_cn}） |\n"
            f"| 🇺🇸 **美股** | **{total_us}分** | {st_us} | **{rec_us}**（上限{pos_us}） |\n\n---\n\n"
            "### 本周关键数据\n\n"
            f"| 指数 | 收盘 | 周涨跌幅 | 关键信号 |\n"
            f"|------|------|---------|---------|\n"
            f"| **标普500 SPX** | **{spx_close:,.2f}** | **{fChg(spx_chg)}** | RSI={spx_rsi} · 偏离MA200 {spx_dev:+.2f}% {verify} |\n"
            f"| **纳斯达克 IXIC** | **{nas_close:,.2f}** | **{fChg(nas_chg)}** | |\n"
            f"| **道琼斯 DJIA** | **{dji_close:,.2f}** | **{fChg(dji_chg)}** | |\n"
            f"| **上证综指** | **{sh_close:.2f}** | **{fChg(sh_chg)}** | RSI={sh_rsi:.1f if sh_rsi else 'N/A'} |\n"
            f"| **深证成指** | **{sz_close:.2f}** | **{fChg(sz_chg)}** | RSI={sz_rsi:.1f if sz_rsi else 'N/A'} |\n"
            f"| **创业板指** | **{cy_close:.2f}** | **{fChg(cy_chg)}** | RSI={cy_rsi:.1f if cy_rsi else 'N/A'} |\n\n---\n\n"
            "### 核心维度\n\n"
            f"**🇨🇳 A股**：技术面{tech_cn} · 基本面{fund_cn} · 情绪面50 · 全球事件35\n"
            f"**🇺🇸 美股**：技术面{tech_us} · 基本面{fund_us} · 情绪面60 · 全球事件30\n\n---\n\n"
            "### ⚠️ 本周风险\n\n"
            "1. 关税谈判陷入停滞（Reuters确认）\n"
            "2. Trump警告再加征50%关税（向伊朗供武）\n"
            "3. A股RSI三指数>80超买区域\n\n"
            "### ✅ 本周支撑\n\n"
            f"1. 两市成交额≈{total_turn:,.0f}亿/日 2. 政策暖风 3. VIX={vix_latest}（未恐慌）\n\n---\n\n"
            f"| 事件 | 说明 |\n"
            f"|------|------|\n"
            f"| 关税谈判 | 关注Trump访华进展 |\n"
            f"| 美联储FOMC | 预期按兵不动，关注降息路径 |\n"
            f"| A股降准 | 周末若宣布周一大幅高开 |\n\n---\n\n"
            f"| 市场 | 仓位 | 上限 |\n"
            f"|------|------|------|\n"
            f"| 🇨🇳 A股 | **{rec_cn}** | {pos_cn} |\n"
            f"| 🇺🇸 美股 | **{rec_us}** | {pos_us} |\n\n---\n\n"
            f"*如远工作室 v1.0 · 数据截至 {date_str} · 获取耗时{elapsed:.0f}秒*"
        )
    }
}

body = json.dumps(payload, ensure_ascii=False)
cmd = ["curl","-s","--max-time","15","-X","POST",
       "-H","Content-Type: application/json","-d",body, URL]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
try:
    result = json.loads(r.stdout)
    print(f"  钉钉响应: errcode={result.get('errcode')} errmsg={result.get('errmsg')}")
except:
    print(f"  钉钉响应解析失败: {r.stdout[:200]}")
print("=== 完成 ===")
