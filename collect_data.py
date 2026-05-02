#!/usr/bin/env python3
"""收集本周大盘数据"""
import json
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta

# 本周：2026-04-28 ~ 2026-04-30（周三），4/25(六)、4/26(日)、4/27(一)~4/30是五一假期周
# 取数据窗口：3月底到4月底
start_date = "2026-04-01"
end_date = "2026-04-30"

results = {"A股": {}, "FRED": {}}

# ============ A股数据 ============
print("=== 收集A股数据 ===")

# 上证综指
df_sh = ak.stock_zh_index_daily(symbol="sh000001")
df_sh['date'] = pd.to_datetime(df_sh['date'])
df_sh = df_sh[(df_sh['date'] >= start_date) & (df_sh['date'] <= end_date)].sort_values('date')
print(f"上证综指: {len(df_sh)} 条, 范围 {df_sh['date'].min().date()} ~ {df_sh['date'].max().date()}")
results["A股"]["上证综指"] = df_sh.tail(10).to_dict('records')

# 深证成指
df_sz = ak.stock_zh_index_daily(symbol="sz399001")
df_sz['date'] = pd.to_datetime(df_sz['date'])
df_sz = df_sz[(df_sz['date'] >= start_date) & (df_sz['date'] <= end_date)].sort_values('date')
print(f"深证成指: {len(df_sz)} 条, 范围 {df_sz['date'].min().date()} ~ {df_sz['date'].max().date()}")
results["A股"]["深证成指"] = df_sz.tail(10).to_dict('records')

# 创业板指
df_cy = ak.stock_zh_index_daily(symbol="sz399006")
df_cy['date'] = pd.to_datetime(df_cy['date'])
df_cy = df_cy[(df_cy['date'] >= start_date) & (df_cy['date'] <= end_date)].sort_values('date')
print(f"创业板指: {len(df_cy)} 条, 范围 {df_cy['date'].min().date()} ~ {df_cy['date'].max().date()}")
results["A股"]["创业板指"] = df_cy.tail(10).to_dict('records')

# 两市成交额（使用上证+深证日成交估算）
# AkShare有个接口：stock_sse_summary（上海市场概况）
try:
    summary = ak.stock_sse_summary()
    print("上交所今日概况:", summary)
except Exception as e:
    print("上交所概况失败:", e)

# 沪深两市总成交额
try:
    trade_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date=start_date.replace("-",""), end_date=end_date.replace("-",""), adjust="")
    print("成交额测试:", trade_df.columns.tolist())
except Exception as e:
    print("成交额获取失败:", e)

print("\n--- 上证最后5条 ---")
print(df_sh[['date','close','volume']].tail(5).to_string(index=False))
print("\n--- 深证最后5条 ---")
print(df_sz[['date','close','volume']].tail(5).to_string(index=False))
print("\n--- 创业板最后5条 ---")
print(df_cy[['date','close','volume']].tail(5).to_string(index=False))

# 保存A股数据
with open('/workspace/weekly_ashare.json', 'w', encoding='utf-8') as f:
    json.dump(results["A股"], f, ensure_ascii=False, indent=2, default=str)
print("\nA股数据已保存到 /workspace/weekly_ashare.json")
