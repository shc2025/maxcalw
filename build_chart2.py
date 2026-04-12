#!/usr/bin/env python3
"""Build TSLA candlestick chart with buy/sell markers using TradingView lightweight-charts"""
import subprocess, json, math

APIKEY = "dd4f227a11f34265936086a73b46b80c"

# ── 1. Fetch OHLC ────────────────────────────────────────────
print("Fetching TSLA OHLC data...")
proc = subprocess.run([
    "curl","-s","--max-time","30",
    "https://api.twelvedata.com/time_series"
    "?symbol=TSLA&interval=1day&outputsize=1300"
    f"&apikey={APIKEY}&start_date=2021-04-05&end_date=2026-04-05&order=asc"
], capture_output=True, text=True, timeout=35)
raw    = json.loads(proc.stdout)
quotes = raw["values"]

# ── 2. Load trade signals ────────────────────────────────────
with open("/workspace/backtest_tsla_results.json") as f:
    bt = json.load(f)
trades = bt["trades"]

# ── 3. Build arrays ──────────────────────────────────────────
dates = [q["datetime"] for q in quotes]
closes= [float(q["close"]) for q in quotes]

def sma(data, period):
    res = []
    for i in range(len(data)):
        res.append(round(sum(data[i-period+1:i+1])/period, 2) if i>=period-1 else None)
    return res

m13  = sma(closes, 13)
m200 = sma(closes, 200)

# Candlestick data
candles = [
    {"time": q["datetime"], "open": float(q["open"]),
     "high": float(q["high"]), "low": float(q["low"]), "close": float(q["close"])}
    for q in quotes
]

# M13/M200 as line series
m13_line  = [{"time": dates[i], "value": v} for i,v in enumerate(m13)  if v]
m200_line = [{"time": dates[i], "value": v} for i,v in enumerate(m200) if v]

# Buy/sell markers
buy_markers  = [{"time": t["date_in"],         "position": "belowBar", "color": "#3fb950", "shape": "arrowUp",   "text": "B"} for t in trades]
sell_markers = [{"time": t.get("date_out",""),  "position": "aboveBar", "color": "#f85149", "shape": "arrowDown", "text": "S"} for t in trades if t.get("date_out")]

# ── 4. Equity curve data ─────────────────────────────────────
eq_dates = [r[0] for r in bt["equity_curve"]]
eq_vals  = [round(r[1], 2) for r in bt["equity_curve"]]
eq_line   = [{"time": eq_dates[i], "value": v} for i,v in enumerate(eq_vals)]

# ── 5. Generate HTML ─────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>TSLA K线 + 买卖点</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3}}

.header{{background:#161b22;border-bottom:1px solid #30363d;padding:18px 32px;display:flex;align-items:center;gap:28px;flex-wrap:wrap}}
.header h1{{font-size:18px;color:#58a6ff;white-space:nowrap}}
.meta{{display:flex;gap:12px;flex-wrap:wrap}}

.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 16px;min-width:90px}}
.card .l{{font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:.05em}}
.card .v{{font-size:16px;font-weight:700;margin-top:2px}}
.c-green{{color:#3fb950}}.c-red{{color:#f85149}}.c-blue{{color:#58a6ff}}

.wrap{{padding:16px 32px}}
.tabs{{display:flex;gap:0;margin-bottom:12px;border-bottom:1px solid #30363d}}
.tab{{padding:8px 20px;cursor:pointer;font-size:13px;color:#8b949e;border-bottom:2px solid transparent;transition:all .15s}}
.tab.active{{color:#58a6ff;border-bottom-color:#58a6ff}}
.panels{{display:flex;gap:16px;flex-wrap:wrap}}

.panel{{flex:1;min-width:340px;background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden}}
.panel-hdr{{padding:10px 14px;background:#1c2128;border-bottom:1px solid #30363d;font-size:12px;color:#8b949e}}
.panel-hdr span{{margin-right:16px}}
.p-line{{padding:4px 0}}

#chart{{width:100%;height:480px}}
#eqChart{{width:100%;height:200px}}

.legend{{display:flex;gap:20px;flex-wrap:wrap;padding:8px 32px;font-size:12px;color:#8b949e}}
.legend span{{display:flex;align-items:center;gap:5px}}
.dots{{width:10px;height:10px;border-radius:2px;display:inline-block}}

.row{{display:flex;gap:16px;padding:0 32px 16px;flex-wrap:wrap}}

table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#1c2128;color:#8b949e;padding:7px 10px;text-align:left;border-bottom:1px solid #30363d;font-weight:400}}
td{{padding:6px 10px;border-bottom:1px solid #21262d;color:#c9d1d9}}
tr:last-child td{{border-bottom:none}}
tr:nth-child(even) td{{background:#161b22}}
</style>
</head>
<body>

<div class=header>
  <h1>📈 TSLA · M13/M200 策略回测</h1>
  <div class=meta>
    <div class=card><div class=l>总收益</div><div class="v c-green">+{bt['summary']['total_return']:.2f}%</div></div>
    <div class=card><div class=l>夏普比率</div><div class="v">{bt['summary']['sharpe_annual']:.3f}</div></div>
    <div class=card><div class=l>胜率</div><div class="v c-green">{bt['summary']['win_rate']:.1f}%</div></div>
    <div class=card><div class=l>盈亏比</div><div class="v">{bt['summary']['profit_factor']:.2f}</div></div>
    <div class=card><div class=l>最大回撤</div><div class="v c-red">-${bt['summary']['max_drawdown']:,.0f}</div></div>
    <div class=card><div class=l>交易次数</div><div class="v">{bt['summary']['total_trades']} 笔</div></div>
  </div>
</div>

<div class=row>
  <!-- K线图 -->
  <div class=panel style="flex:2;min-width:500px">
    <div class=panel-hdr>◇ K线图（▲ 买入 / ▼ 卖出）&nbsp;&nbsp;—&nbsp;蓝=M13 &nbsp;橙=M200</div>
    <div id="chart"></div>
  </div>
  <!-- 净值曲线 -->
  <div class=panel style="flex:1;min-width:280px">
    <div class=panel-hdr>💰 组合净值曲线</div>
    <div id="eqChart"></div>
  </div>
</div>

<div class=legend>
  <span><span class=dots style="background:#3fb950"></span>买入（M13向上拐头）</span>
  <span><span class=dots style="background:#f85149"></span>卖出（M13向下拐头）</span>
  <span><span style="width:20px;height:2px;background:#58a6ff;display:inline-block"></span>M13 均线</span>
  <span><span style="width:20px;height:2px;background:#f0883e;display:inline-block"></span>M200 均线</span>
</div>

<div class=wrap>
  <table>
  <tr><th>买</th><th>买入价</th><th>数量</th><th>卖</th><th>卖出价</th><th>出场</th><th>盈亏</th><th>收益率</th></tr>
  {''.join(f"<tr><td>{t['date_in']}</td><td>${t['price_in']:.2f}</td><td>{t['shares']}</td><td>{t.get('date_out','—')}</td><td>${t.get('price_out',0):.2f}</td><td>{t['exit_reason']}</td><td class={'c-green' if t['pnl']>0 else 'c-red'}>${t['pnl']:+,.2f}</td><td class={'c-green' if t['ret_pct']>0 else 'c-red'}> {t['ret_pct']:+.2f}%</td></tr>" for t in trades)}
  </table>
</div>

<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
const candles  = {json.dumps(candles, ensure_ascii=False)};
const m13Data  = {json.dumps(m13_line,  ensure_ascii=False)};
const m200Data = {json.dumps(m200_line, ensure_ascii=False)};
const eqData   = {json.dumps(eq_line,   ensure_ascii=False)};
const buyMark  = {json.dumps(buy_markers,  ensure_ascii=False)};
const sellMark = {json.dumps(sell_markers, ensure_ascii=False)};
const trades   = {json.dumps(trades, ensure_ascii=False)};

// ── Main chart ───────────────────────────────────────
const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
  width:  document.getElementById('chart').clientWidth,
  height: 480,
  layout: {{
    background: {{ color: '#161b22' }},
    textColor: '#8b949e',
    fontSize: 11,
  }},
  grid: {{
    vertLines: {{ color: '#21262d' }},
    horzLines: {{ color: '#21262d' }},
  }},
  crosshair: {{
    mode: LightweightCharts.CrosshairMode.Normal,
    vertLine: {{ color: '#30363d', style: LightweightCharts.LineStyle.Dashed }},
    horzLine: {{ color: '#30363d', style: LightweightCharts.LineStyle.Dashed }},
  }},
  rightPriceScale: {{
    borderColor: '#30363d',
    scaleMargins: {{ top: 0.05, bottom: 0.05 }},
  }},
  timeScale: {{
    borderColor: '#30363d',
    timeVisible: true,
    secondsVisible: false,
    tickMarkFormatter: t => {{
      const d = new Date(t * 1000);
      return d.toLocaleDateString('en', {{month:'short',day:'numeric',year:'2-digit'}});
    }},
  }},
}});

// Candlestick series
const candleSeries = chart.addCandlestickSeries({{
  upColor:          '#3fb950',
  downColor:        '#f85149',
  borderVisible:    false,
  wickUpColor:      '#3fb950',
  wickDownColor:    '#f85149',
}});
candleSeries.setData(candles);

// M13 line
const s13 = chart.addLineSeries({{
  color:      '#58a6ff',
  lineWidth:  1.5,
  crosshairMarkerVisible: false,
  lastValueVisible: false,
  priceLineVisible: false,
}});
s13.setData(m13Data);

// M200 line
const s200 = chart.addLineSeries({{
  color:      '#f0883e',
  lineWidth:  1.5,
  crosshairMarkerVisible: false,
  lastValueVisible: false,
  priceLineVisible: false,
}});
s200.setData(m200Data);

// Buy markers
const buySer = chart.addSeriesMarkers(candlestickSeries ?? candleSeries, {{
  markers: buyMark,
}});
const sellSer = chart.addSeriesMarkers(candlestickSeries ?? candleSeries, {{
  markers: sellMark,
}});

// Place markers on candlestick series
candleSeries.setMarkers([...buy_markers, ...sell_markers]);

// Resize
window.addEventListener('resize', () => {{
  document.getElementById('chart')?.resize();
}});

// ── Equity chart ─────────────────────────────────────
const eqChart = LightweightCharts.createChart(document.getElementById('eqChart'), {{
  width:  document.getElementById('eqChart').clientWidth,
  height: 200,
  layout: {{ background: {{ color: '#161b22' }}, textColor: '#8b949e', fontSize: 11 }},
  grid:   {{ vertLines: {{ color: '#21262d' }}, horzLines: {{ color: '#21262d' }} }},
  rightPriceScale: {{ borderColor: '#30363d' }},
  timeScale: {{
    borderColor: '#30363d',
    visible: true,
    tickMarkFormatter: t => {{
      const d = new Date(t * 1000);
      return d.toLocaleDateString('en', {{month:'short',day:'numeric',year:'2-digit'}});
    }},
  }},
}});

const eqSer = eqChart.addAreaSeries({{
  topColor:           'rgba(63,185,80,0.25)',
  bottomColor:        'rgba(63,185,80,0.05)',
  lineColor:          '#3fb950',
  lineWidth:          1.5,
  crosshairMarkerVisible: false,
  lastValueVisible:   true,
  priceLineVisible:  false,
  priceScaleId:      'right',
}});
eqSer.setData(eqData);
eqChart.timeScale().fitContent();

// Sync time scales
chart.timeScale().subscribeVisibleLogicalRangeChange(r => {{
  if (r) eqChart.timeScale().setVisibleLogicalRange(r);
}});
eqChart.timeScale().subscribeVisibleLogicalRangeChange(r => {{
  if (r) chart.timeScale().setVisibleLogicalRange(r);
}});

// Click tooltip on chart
const toolTip = document.createElement('div');
toolTip.style = 'position:absolute;display:none;background:#1c2128;border:1px solid #30363d;border-radius:6px;padding:8px 12px;font-size:12px;color:#c9d1d9;pointer-events:none;z-index:999;white-space:nowrap;';
document.getElementById('chart').style.position = 'relative';
document.getElementById('chart').appendChild(toolTip);

chart.subscribeCrosshairMove(param => {{
  if (!param.time || !param.seriesData) {{ toolTip.style.display = 'none'; return; }}
  const candle = param.seriesData.get(candleSeries);
  if (!candle) {{ toolTip.style.display = 'none'; return; }}
  const time = param.time;
  const idx  = candles.findIndex(c => c.time === time);
  const m13v = idx >= 0 && idx < m13Data.length ? m13Data[idx]?.value : null;
  const m200v= idx >= 0 && idx < m200Data.length ? m200Data[idx]?.value : null;
  toolTip.style.display = 'block';
  toolTip.style.left    = (param.point?.x ?? 0) + 12 + 'px';
  toolTip.style.top     = (param.point?.y ?? 0) - 40 + 'px';
  toolTip.innerHTML = `<b style="color:#e6edf3">${{
    new Date(time * 1000).toLocaleDateString('en',{{month:'short',day:'numeric',year:'numeric'}})
  }}</b><br>O: ${{candle.open?.toFixed(2)}}  H: ${{candle.high?.toFixed(2)}}<br>L: ${{candle.low?.toFixed(2)}}  <b style="color:#c9d1d9">C: ${{candle.close?.toFixed(2)}}</b>${{
    m13v ? `<br>M13: <b style="color:#58a6ff">${{m13v.toFixed(2)}}</b>` : ''
  }}${{
    m200v ? `  M200: <b style="color:#f0883e">${{m200v.toFixed(2)}}</b>` : ''
  }}`;
}});
</script>
</body>
</html>"""

with open("/workspace/report_tsla/index.html","w") as f:
    f.write(html)
print("Written: /workspace/report_tsla/index.html")
print(f"  Candles: {len(candles)}, M13: {len(m13_line)}, M200: {len(m200_line)}, Trades: {len(trades)}")
