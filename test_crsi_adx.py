#!/usr/bin/env python3
"""测试: ADX Wilder平滑 vs Twelve Data API 结果对比"""
import subprocess, json, sys

APIKEY = 'dd4f227a11f34265936086a73b46b80c'

# ── 加载本地ADX ──────────────────────────────────────────────
sys.path.insert(0, '/workspace')
from skills.crsi_calculator import ADXCalculator, calc_adx_from_ohlcv

adx_api = ADXCalculator(api_key=APIKEY)

# ── 测试1: Twelve Data API ADX ───────────────────────────────
print("=== Twelve Data ADX (API) ===")
for sym in ['SPY', 'QQQ', 'DIA']:
    r = adx_api.calculate(sym, period=14)
    if 'error' not in r:
        print(f"  {sym}: ADX={r['adx']:.2f}  日期={r['date']}")

# ── 测试2: 本地计算 vs API ───────────────────────────────────
print("\n=== 本地 Wilder vs Twelve Data API ===")
print(f"  {'标的':<6} {'来源':<12} {'ADX':>6} {'DI+':>7} {'DI-':>7} {'状态'}")
print("  " + "-" * 55)

for sym in ['SPY', 'QQQ']:
    # API
    r_api = adx_api.calculate(sym, period=14)
    # 本地
    r_loc = adx_api.calculate_from_twelvedata_with_price(sym, period=14)
    if 'error' not in r_api and 'error' not in r_loc:
        diff = abs(r_api['adx'] - r_loc['adx'])
        ok = '✅ 吻合' if diff < 0.5 else f'⚠️ 差{diff:.2f}'
        print(f"  {sym:<6} {'API':<12} {r_api['adx']:>6.2f} {'N/A':>7} {'N/A':>7} {ok}")
        print(f"  {sym:<6} {'本地Wilder':<12} {r_loc['adx']:>6.2f} {r_loc['di_plus']:>7.2f} {r_loc['di_minus']:>7.2f}  {ok}")

# ── 测试3: A股数据测试（用AkShare拉上证指数） ──────────────────
print("\n=== A股指数 ADX 测试 ===")
try:
    import akshare as ak
    import pandas as pd

    df = ak.stock_zh_index_daily(symbol="sh000001")
    df = df.tail(60).reset_index(drop=True)
    print(f"  上证指数: 获取 {len(df)} 根K线  {df['date'].iloc[-1]} 截止")

    ohlcv = [
        {
            "datetime": str(row["date"]),
            "open":  float(row["open"]),
            "high":  float(row["high"]),
            "low":   float(row["low"]),
            "close": float(row["close"]),
        }
        for _, row in df.iterrows()
    ]

    r = adx_api.calculate_from_ohlcv(ohlcv, period=14)
    if 'error' not in r:
        s = r['signal']
        print(f"  上证指数 ADX = {r['adx']}  DI+={r['di_plus']}  DI-={r['di_minus']}")
        print(f"  信号: {s['emoji']} {s['signal']}")
    else:
        print(f"  错误: {r['error']}")

except Exception as e:
    print(f"  A股测试跳过: {e}")

# ── 测试4: CRSI 验证 ──────────────────────────────────────────
print("\n=== CRSI 验证 (TSLA/QQQ) ===")
from skills.crsi_calculator import CRSICalculator
crsi_calc = CRSICalculator(api_key=APIKEY)
for sym, expected in [('TSLA', 74.01), ('QQQ', 96.16)]:
    r = crsi_calc.calculate(sym, date='2026-04-17')
    if 'error' not in r:
        ok = '✅' if abs(r['crsi'] - expected) < 0.1 else '❌'
        print(f"  {sym}: CRSI={r['crsi']} (预期 {expected}) {ok}")
    else:
        print(f"  {sym}: {r['error']}")

print("\n测试完成!")
