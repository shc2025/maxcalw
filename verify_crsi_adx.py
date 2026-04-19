#!/usr/bin/env python3
"""简单验证: CRSI + ADX"""
import importlib.util
spec = importlib.util.spec_from_file_location("cc", "/workspace/skills/crsi-calculator/__init__.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
C = mod.CRSICalculator
A = mod.ADXCalculator

calc = C(api_key="dd4f227a11f34265936086a73b46b80c")
a = A(api_key="dd4f227a11f34265936086a73b46b80c")

# CRSI 验证
for sym, exp in [("TSLA", 74.01), ("QQQ", 96.16)]:
    r = calc.calculate(sym, date="2026-04-17")
    if "error" not in r:
        ok = "✅" if abs(r["crsi"] - exp) < 0.1 else "❌"
        print(f"CRSI {sym}: {r['crsi']} (预期 {exp}) {ok}  date={r['date']}")
    else:
        print(f"CRSI {sym}: ERR {r['error']}")

# ADX 验证
for sym in ["SPY", "QQQ"]:
    r = a.calculate_from_twelvedata_with_price(sym)
    if "error" not in r:
        print(f"ADX {sym}: ADX={r['adx']} DI+={r['di_plus']} DI-={r['di_minus']} ({r['date']}) {r['signal']['emoji']}")
    else:
        print(f"ADX {sym}: ERR {r['error']}")
