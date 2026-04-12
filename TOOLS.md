# TOOLS.md - Local Notes

## Finnhub API (已接入)
- **API Key**: `d74fsm1r01qno4q1jqd0d74fsm1r01qno4q1jqdg`
- **MCP Server**: `finnhub` (via mcporter, aigroup-finnhub-mcp)
- **Config**: `/workspace/config/mcporter.json`

### MCP 调用格式
```bash
mcporter call finnhub.<工具名> operation=<子操作> <参数>
```

### 可用工具 & 子操作

**1. finnhub_stock_market_data** (行情数据)
- `operation=get_quote symbol=AAPL` → 实时报价
- `operation=get_candles symbol=AAPL resolution=D interval=60` → K线
- `operation=get_company_profile symbol=AAPL` → 公司概况
- `operation=symbol_lookup query=Apple` → 股票搜索
- `operation=get_basic_financials symbol=AAPL metricType=margin` → 基础财务数据
- `operation=get_financials_as_reported symbol=AAPL freq=annual` → 财报
- `operation=get_earnings_surprises symbol=AAPL` → 盈利惊喜

**2. finnhub_news_sentiment** (新闻情绪)
- `operation=get_news_sentiment symbol=AAPL` → 新闻情绪分析
- `operation=get_company_news symbol=AAPL` → 公司新闻

**3. finnhub_technical_analysis** (技术分析)
- `operation=get_indicator symbol=AAPL resolution=D indicator=macd` → 技术指标
- `operation=get_pattern_recognition symbol=AAPL resolution=D` → 形态识别
- `operation=get_support_resistance symbol=AAPL resolution=D` → 支撑阻力位

**4. finnhub_market_events** (市场事件)
- `operation=get_analyst_ratings symbol=AAPL` → 分析师评级
- `operation=get_market_holidays exchange=NASDAQ` → 休市日历

**5. finnhub_stock_ownership** (股权结构)
- `operation=get_institutional_ownership symbol=AAPL` → 机构持仓
- `operation=get_insider_transactions symbol=AAPL` → 内幕交易
- `operation=get_congress_transactions symbol=AAPL` → 国会交易

**6. finnhub_forex** (外汇)
- `operation=get_forex_rates` → 汇率
- `operation=get_forex_candles symbol=OANDA:EURUSD resolution=D` → 外汇K线

**7. finnhub_crypto_data** (加密货币)
- `operation=get_crypto_candles symbol=BINANCE:BTCUSDT resolution=D` → 加密K线
- `operation=get_crypto_rates symbol=BINANCE:BTCUSD` → 加密汇率

**8. finnhub_calendar_data** (经济日历)
- `operation=get_economic_calendar` → 财经日历

**9. finnhub_stock_estimates** (股票预期)
- `operation=get_price_target symbol=AAPL` → 目标价
- `operation=get_earnings_estimates symbol=AAPL` → 盈利预期

**10. finnhub_sec_filings** (SEC文件)
- `operation=get_sec_filings symbol=AAPL` → SEC文件
