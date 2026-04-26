#!/usr/bin/env python3
"""
大盘周报评分引擎 — 基于"统一大盘牛熊评分日报规则v1.0"
"""
import json, subprocess
from datetime import datetime

# ── 数据加载 ────────────────────────────────────────────────
fred = json.load(open("/workspace/weekly_fred.json"))
a_share = json.load(open("/workspace/weekly_ashare.json"))

# ── 辅助函数 ───────────────────────────────────────────────
def latest(d, n=5):
    """返回最近n个值"""
    vals = d[-n:]
    return [(x[0], x[1]) for x in vals]

def avg(vals): return sum(vals)/len(vals) if vals else None
def last(d): return d[-1] if d else None

def rsi14(closes):
    """计算RSI(14)"""
    if len(closes) < 15: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0)); losses.append(abs(min(d, 0)))
    if len(gains) < 14: return None
    avg_g = avg(gains[-14:]); avg_l = avg(losses[-14:])
    if avg_l == 0: return 100
    rs = avg_g / avg_l
    return 100 - (100 / (1 + rs))

# ── 美股数据 ────────────────────────────────────────────────
spx_d = fred["SP500"]   # (date, value)
dji_d = fred["DJIA"]
nasdaq_d = fred["NASDAQCOM"]
vix_d = fred["VIXCLS"]
us10y_d = fred["DGS10"]
us2y_d = fred["DGS2"]
spread_d = fred.get("T10Y2Y", [(None,None)])

spx_latest = spx_d[-1]
dji_latest = dji_d[-1]
nasdaq_latest = nasdaq_d[-1]
vix_l = vix_d[-1]
us10y_l = us10y_d[-1]
us2y_l = us2y_d[-1]
spread_l = spread_d[-1] if spread_d else (None, None)

# 计算SPX 200日均线
spx_closes = [v for _,v in spx_d]
spx_dates = [k for k,_ in spx_d]
ma200 = avg(spx_closes[-200:]) if len(spx_closes) >= 200 else None
spx_dev = (spx_latest[1] - ma200) / ma200 * 100 if ma200 else None

# SPX 本周涨跌（4个交易日）
week_closes = [v for _,v in spx_d[-5:-1]]  # 上周五~本周三
week_chg = (spx_latest[1] - spx_d[-5][1]) / spx_d[-5][1] * 100 if len(spx_d) >= 5 else None

# 计算RSI(14)
spx_rsi = rsi14(spx_closes[-60:])  # 用60天数据算RSI(14)

# VIX
vix_val = vix_l[1]
us10y_val = us10y_l[1]
us2y_val = us2y_l[1]
spread_val = spread_l[1] if spread_l[1] else None
spread_date = spread_l[0] if spread_l[0] else None

print("=== 本周数据（2026-04-21~2026-04-24 ===\n")
print(f"SPX: {spx_latest[0]} = {spx_latest[1]:,.2f}")
print(f"SPX 200日均线: {ma200:,.2f} (偏离: {spx_dev:+.2f}%)")
print(f"SPX RSI(14): {spx_rsi:.1f}" if spx_rsi else "SPX RSI: N/A")
print(f"SPX 本周涨跌: {week_chg:+.2f}%" if week_chg else "")
print(f"DJI: {dji_latest[0]} = {dji_latest[1]:,.2f}")
print(f"NASDAQ: {nasdaq_latest[0]} = {nasdaq_latest[1]:,.2f}")
print(f"VIX: {vix_l[0]} = {vix_val}")
print(f"US10Y: {us10y_l[0]} = {us10y_val}%")
print(f"US2Y: {us2y_l[0]} = {us2y_val}%")
print(f"10Y-2Y利差: {spread_date} = {spread_val}" if spread_val else "10Y-2Y利差: N/A")

# ── A股数据 ────────────────────────────────────────────────
print()
sh_name = "上证综指"
sz_name = "深证成指"
cy_name = "创业板指"
sh_d = a_share.get(sh_name, {})
sz_d = a_share.get(sz_name, {})
cy_d = a_share.get(cy_name, {})

def ai(name, d, key):
    vals = d.get(key, [])
    return vals[-1] if vals else None

sh_c = sh_d.get("close", []); sh_v = sh_d.get("volume", [])
sz_c = sz_d.get("close", []); sz_v = sz_d.get("volume", [])
cy_c = cy_d.get("close", []); cy_v = cy_d.get("volume", [])

sh_latest_close = sh_c[-1] if sh_c else None
sz_latest_close = sz_c[-1] if sz_c else None
cy_latest_close = cy_c[-1] if cy_c else None
sh_dates = sh_d.get("dates", [])

# 成交量（成交额，单位亿元）
# volume字段是"成交量"（手），1手=100股，成交额≈成交量/100×均价
# 从akshare获取的index daily数据，volume单位通常是"手"
# 成交额(亿元) ≈ (成交量/100000000)*均价/100 = 成交量*均价/100000000*100 = 成交量*均价/1000000
# 更准确：akshare的"成交量"单位是"股"，"成交额"单位是"元"
# 但数据里没有成交额，直接用成交量估算
# 用个股平均价格估算：成交额 ≈ 成交量 × 平均股价
def estimate_turnover(vol, close):
    """估算成交额（亿元）成交量单位是股"""
    if not vol or not close: return None
    # 成交额 = 成交量(股) × 平均价格(元/股) / 1亿
    avg_price = close * 0.5  # 粗估
    return vol * avg_price / 1e8  # 亿元

# 直接用成交量（手）对比历史判断
sh_vol = sh_v[-1] if sh_v else None
sz_vol = sz_v[-1] if sz_v else None
total_vol = (sh_vol or 0) + (sz_vol or 0)
# 换算为亿元（假设A股平均股价5元，均价=5元）
avg_price_est = 5.0  # 人仔
total_turnover_yi = total_vol * avg_price_est / 1e8 if total_vol else None

print(f"上证: {sh_dates[-1] if sh_dates else ''} close={sh_latest_close}")
print(f"深证: close={sz_latest_close}")
print(f"创业板: close={cy_latest_close}")
print(f"两市成交量: {total_vol/1e8:.2f}亿股（估算成交额约{total_turnover_yi:.0f}亿元）" if total_turnover_yi else "")

# 计算A股RSI
sh_rsi = rsi14(sh_c[-60:]) if len(sh_c) >= 15 else None
sz_rsi = rsi14(sz_c[-60:]) if len(sz_c) >= 15 else None
cy_rsi = rsi14(cy_c[-60:]) if len(cy_c) >= 15 else None
print(f"上证RSI(14): {sh_rsi:.1f}" if sh_rsi else "RSI N/A")
print(f"深证RSI(14): {sz_rsi:.1f}" if sz_rsi else "RSI N/A")
print(f"创业板RSI(14): {cy_rsi:.1f}" if cy_rsi else "RSI N/A")
