#!/usr/bin/env python3
"""测试 investpy 完整功能"""
import investpy, json

print("版本:", investpy.__version__)

# 1. 搜索
print("\n=== 搜索 AAPL ===")
try:
    r = investpy.search_stocks(by="symbol", value="AAPL")
    print(r.head(3).to_string())
except Exception as e:
    print("搜索出错:", e)

# 2. 历史数据（dd/mm/yyyy格式）
print("\n=== AAPL 历史日K (2025-01-01 ~ 2026-04-15) ===")
try:
    df = investpy.get_stock_historical_data(
        stock="AAPL",
        country="United States",
        from_date="01/01/2025",
        to_date="15/04/2026"
    )
    print(f"✅ 获取成功 {len(df)} 行，最新:")
    print(df.tail(3).to_string())
    df.to_json("/workspace/investpy_aapl.json", orient="records", date_format="iso")
    print("已保存 /workspace/investpy_aapl.json")
except Exception as e:
    print("❌ 失败:", e)

# 3. 技术指标
print("\n=== 技术指标 (AAPL 日线) ===")
try:
    ti = investpy.technical_indicators(
        technical_data=None,
        symbol="AAPL",
        country="United States",
        product_type="stock",
        interval="daily"
    )
    print(type(ti))
    if hasattr(ti, 'read_html'):
        df2 = ti.read_html(index_col=0)
        print(df2.to_string())
    else:
        print(str(ti)[:500])
except Exception as e:
    print("技术指标出错:", e)

# 4. 指数历史
print("\n=== 标普500指数历史 ===")
try:
    idx = investpy.get_index_historical_data(
        index="S&P 500",
        country="United States",
        from_date="01/01/2026",
        to_date="15/04/2026"
    )
    print(f"✅ {len(idx)} 行")
    print(idx.tail(3).to_string())
except Exception as e:
    print("❌ 失败:", e)
