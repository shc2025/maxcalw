#!/usr/bin/env python3
from tradingview_ta import TA_Handler as TAHandler, Interval, get_multiple_analysis

print("=== AAPL 日线技术分析 ===")
handler = TAHandler(symbol='AAPL', interval=Interval.INTERVAL_1_DAY)
analysis = handler.get_analysis()
print("推荐:", analysis.summary.get('RECOMMENDATION'))
print("RSI(14):", analysis.indicators.get('RSI'))
print("MACD:", analysis.indicators.get('MACD.macd'), "signal:", analysis.indicators.get('MACD.signal'))
print("EMA20:", analysis.indicators.get('EMA20'))
print("SMA50:", analysis.indicators.get('SMA50'))
print("SMA200:", analysis.indicators.get('SMA200'))
print("支撑1:", analysis.indicators.get('Pivot.S1'))
print("阻力1:", analysis.indicators.get('Pivot.R1'))
print()

# 多标的
print("=== 多标的日线对比 ===")
try:
    result = get_multiple_analysis(
        interval=Interval.INTERVAL_1_DAY,
        symbols=['AAPL', 'TSLA', 'NVDA', 'SPY']
    )
    for sym, ana in result.items():
        rsi = ana.indicators.get('RSI', 'N/A')
        rec = ana.summary.get('RECOMMENDATION', 'N/A')
        print(f"{sym}: {rec} | RSI={rsi}")
except Exception as e:
    print("多标的查询出错:", e)
