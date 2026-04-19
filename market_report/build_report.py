#!/usr/bin/env python3
"""大盘技术分析周报 - 生成器"""
import json
from datetime import datetime

data = json.load(open("/workspace/market_report/all_data.json", "r"))
gen = datetime.now().strftime("%Y年%m月%d日 %H:%M")

def f(v, d="—"): return str(v) if v is not None else d

print("=== 数据概览 ===")
for name, m in data.items():
    print(f"  {name}: 收盘={f(m.get('last_close'))} ADX={f(m.get('adx'))} 日CRSI={f(m.get('crsi_daily'))} {f(m.get('crsi_sig'))}")
