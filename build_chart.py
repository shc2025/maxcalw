#!/usr/bin/env python3
"""Fetch TSLA OHLC + trades, build candlestick chart with buy/sell markers"""
import subprocess, json, math, csv

APIKEY = "dd4f227a11f34265936086a73b46b80c"

# ── 1. Fetch OHLC ────────────────────────────────────────────
print("Fetching TSLA OHLC data...")
proc = subprocess.run([
    "curl","-s","--max-time","30",
    "https://api.twelvedata.com/time_series"
    "?symbol=TSLA&interval=1day&outputsize=1300"
    f"&apikey={APIKEY}&start_date=2021-04-05&end_date=2026-04-05&order=asc"
], capture_output=True, text=True, timeout=35)
raw = json.loads(proc.stdout)
quotes = raw["values"]  # oldest → newest
print(f"  Got {len(quotes)} candles")

# ── 2. Load trade signals ────────────────────────────────────
with open("/workspace/backtest_tsla_results.json") as f:
    bt = json.load(f)
trades = bt["trades"]

# ── 3. Build date-indexed OHLC map ──────────────────────────
ohlc = {}
for q in quotes:
    ohlc[q["datetime"]] = {
        "o": float(q["open"]), "h": float(q["high"]),
        "l": float(q["low"]),  "c": float(q["close"]),
        "v": int(q["volume"])
    }

dates_all = [q["datetime"] for q in quotes]
closes    = [ohlc[d]["c"] for d in dates_all]

# ── 4. SMA ───────────────────────────────────────────────────
def sma(data, period):
    res = []
    for i in range(len(data)):
        res.append(sum(data[i-period+1:i+1])/period if i>=period-1 else None)
    return res

m13  = sma(closes, 13)
m200 = sma(closes, 200)

# ── 5. Build buy/sell point lists ────────────────────────────
buy_x,  buy_y  = [], []
sell_x, sell_y = [], []

# Also track equity curve aligned to dates_all
INITIAL = 10000.0
cash    = INITIAL
position= 0.0
entry_price=0.0; entry_shares=0
trade_idx = 0
prev_m13=None; m13_was_rising=None

# Build equity aligned to dates_all
equity_by_date = {}
for i, d in enumerate(dates_all):
    equity_by_date[d] = cash + position * ohlc[d]["c"]

# Build buy/sell annotations from trades
for t in trades:
    buy_x.append(t["date_in"])
    buy_y.append(t["price_in"])
    sell_x.append(t.get("date_out",""))
    sell_y.append(t.get("price_out", 0))

# ── 6. Compute M13/M200 arrays for overlay ───────────────────
m13_json  = json.dumps([round(v,2) if v is not None else None for v in m13])
m200_json = json.dumps([round(v,2) if v is not None else None for v in m200])

# ── 7. Build OHLC arrays for chart ──────────────────────────
ohlc_o = [round(ohlc[d]["o"],2) for d in dates_all]
ohlc_h = [round(ohlc[d]["h"],2) for d in dates_all]
ohlc_l = [round(ohlc[d]["l"],2) for d in dates_all]
ohlc_c = [round(ohlc[d]["c"],2) for d in dates_all]

# ── 8. Equity curve ─────────────────────────────────────────
eq_dates = [r[0] for r in bt["equity_curve"]]
eq_vals  = [round(r[1],2) for r in bt["equity_curve"]]

# ── 9. Generate HTML ─────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>TSLA K线 + 买卖点</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/luxon@3.4.3/build/global/luxon.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.3.1/dist/chartjs-adapter-luxon.umd.min.js"></script>
<style>
*{{box-sizing:border-box}}
body{{font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;margin:0;padding:0}}
.header{{background:#161b22;border-bottom:1px solid #30363d;padding:20px 40px;display:flex;align-items:center;gap:24px;flex-wrap:wrap}}
.header h1{{margin:0;font-size:20px;color:#58a6ff}}
.header .meta{{display:flex;gap:20px;flex-wrap:wrap}}
.badge{{background:#21262d;border:1px solid #30363d;border-radius:6px;padding:6px 14px;font-size:13px}}
.badge .lb{{color:#8b949e;font-size:11px}}
.badge .val{{font-weight:bold;color:#e6edf3}}
.pos{{color:#3fb950}}.neg{{color:#f85149}}

.chart-section{{padding:20px 40px}}
.section-title{{font-size:14px;color:#8b949e;margin-bottom:12px}}

#mainChart{{background:#161b22;border:1px solid #30363d;border-radius:8px}}

.legend-wrap{{display:flex;gap:20px;flex-wrap:wrap;padding:10px 40px;font-size:13px;color:#8b949e}}
.legend-wrap span{{display:flex;align-items:center;gap:6px}}

canvas{{display:block}}
</style>
</head>
<body>

<div class=header>
  <h1>📈 TSLA M13/M200 策略 K线图</h1>
  <div class=meta>
    <div class=badge><div class=lb>总收益率</div><div class="val pos">+{bt['summary']['total_return']:.2f}%</div></div>
    <div class=badge><div class=lb>夏普比率</div><div class=val>{bt['summary']['sharpe_annual']:.3f}</div></div>
    <div class=badge><div class=lb>胜率</div><div class="val pos">{bt['summary']['win_rate']:.1f}%</div></div>
    <div class=badge><div class=lb>盈亏比</div><div class=val>{bt['summary']['profit_factor']:.2f}</div></div>
    <div class=badge><div class=lb>最大回撤</div><div class="val neg">-${bt['summary']['max_drawdown']:,.0f}</div></div>
    <div class=badge><div class=lb>交易次数</div><div class=val>{bt['summary']['total_trades']} 笔</div></div>
  </div>
</div>

<div class=chart-section>
  <div class=section-title>◇ K线图（红▼=卖出，绿▲=买入）&nbsp;&nbsp;━━ M13 &nbsp;&nbsp;━ M200</div>
  <canvas id="mainChart"></canvas>
</div>

<div class=legend-wrap>
  <span><span style="width:12px;height:12px;background:#3fb950;border-radius:2px"></span>买入点 (M13向上拐头)</span>
  <span><span style="width:12px;height:12px;background:#f85149;border-radius:2px"></span>卖出点 (M13向下拐头)</span>
  <span><span style="width:20px;height:2px;background:#58a6ff"></span>M13 均线</span>
  <span><span style="width:20px;height:2px;background:#f0883e"></span>M200 均线</span>
</div>

<script>
// ── Data ──────────────────────────────────────────
const dates    = {json.dumps(dates_all)};
const open_    = {json.dumps(ohlc_o)};
const high_    = {json.dumps(ohlc_h)};
const low_     = {json.dumps(ohlc_l)};
const close_   = {json.dumps(ohlc_c)};
const m13_arr  = {m13_json};
const m200_arr = {m200_json};

const buyX  = {json.dumps(buy_x)};
const buyY  = {json.dumps(buy_y)};
const sellX = {json.dumps(sell_x)};
const sellY = {json.dumps(sell_y)};

// ── Candlestick colour ─────────────────────────────
function candleColour(idx) {{
  return close_[idx] >= open_[idx] ? '#3fb950' : '#f85149';
}}

// Chart.js 4 custom candlestick element
class CandlestickElement {{
  constructor(props) {{
    this.x       = props.x;
    this.o        = props.o;
    this.h        = props.h;
    this.l        = props.l;
    this.c        = props.c;
    this.colour   = props.colour;
  }}
  draw(ctx) {{
    const x = this.x;
    const o = this.o, h = this.h, l = this.l, c = this.c;
    const cw = 3;
    ctx.strokeStyle = this.colour;
    ctx.fillStyle   = this.colour;
    ctx.lineWidth   = 1;
    // wick
    ctx.beginPath();
    ctx.moveTo(x, h); ctx.lineTo(x, l);
    ctx.stroke();
    // body
    const top = Math.max(o, c), bot = Math.min(o, c);
    ctx.fillRect(x - cw, top, cw*2, bot - top || 1);
  }}
  tooltipPosition() {{ return {{x: this.x, y: this.c}}; }}
  get labelposition() {{ return 'right'; }}
}}

// Build chart
const ctx = document.getElementById('mainChart').getContext('2d');
const labels = dates; // full labels

const chart = new Chart(ctx, {{
  type: 'line',
  data: {{
    labels,
    datasets: [
      // 1. M13
      {{
        label: 'M13',
        data: m13_arr,
        borderColor: '#58a6ff',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0,
        order: 3
      }},
      // 2. M200
      {{
        label: 'M200',
        data: m200_arr,
        borderColor: '#f0883e',
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0,
        order: 3
      }},
      // 3. Buy arrows
      {{
        label: '买入',
        data: buyX.map((x,i) => ({{x, y: buyY[i]}})),
        borderColor: '#3fb950',
        backgroundColor: '#3fb950',
        pointRadius: 8,
        pointStyle: 'triangle',
        showLine: false,
        order: 1
      }},
      // 4. Sell arrows
      {{
        label: '卖出',
        data: sellX.map((x,i) => ({{x, y: sellY[i]}})),
        borderColor: '#f85149',
        backgroundColor: '#f85149',
        pointRadius: 8,
        pointStyle: 'triangle',
        rotation: 180,
        showLine: false,
        order: 1
      }},
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: '#161b22',
        borderColor: '#30363d',
        borderWidth: 1,
        titleColor: '#e6edf3',
        bodyColor: '#8b949e',
        callbacks: {{
          title: items => items[0].label,
          label: ctx2 => {{
            if (ctx2.datasetIndex < 2) {{
              const v = ctx2.raw;
              return v != null ? ` ${{ctx2.dataset.label}}: ${{v.toFixed(2)}}` : '';
            }}
            if (ctx2.datasetIndex === 2) return ` ▲ 买入: ${{ctx2.raw.y.toFixed(2)}}`;
            if (ctx2.datasetIndex === 3) return ` ▼ 卖出: ${{ctx2.raw.y.toFixed(2)}}`;
          }}
        }}
      }},
      // Candlestick overlay via custom dataset
      beforeDatasetsDraw: chart => {{
        const {{ctx: c, chartArea}} = chart;
        if (!chartArea) return;
        c.save();
        c.beginPath();
        c.rect(chartArea.left, chartArea.top, chartArea.right - chartArea.left, chartArea.bottom - chartArea.top);
        c.clip();

        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        const step  = Math.max(1, Math.floor(labels.length / xAxis.ticks.length));

        for (let i = 0; i < labels.length; i++) {{
          const xPix = xAxis.getPixelForValue(labels[i]);
          const oPix = yAxis.getPixelForValue(open_[i]);
          const hPix = yAxis.getPixelForValue(high_[i]);
          const lPix = yAxis.getPixelForValue(low_[i]);
          const cPix = yAxis.getPixelForValue(close_[i]);
          const col  = candleColour(i);
          const cw   = Math.max(2, (xAxis.getPixelForValue(labels[Math.min(i+1,labels.length-1)]) - xAxis.getPixelForValue(labels[i])) / 2 - 1);

          c.strokeStyle = col;
          c.fillStyle   = col;
          c.lineWidth   = 1;

          // wick
          c.beginPath();
          c.moveTo(xPix, hPix);
          c.lineTo(xPix, lPix);
          c.stroke();

          // body
          const top = Math.min(oPix, cPix);
          const bot = Math.max(oPix, cPix);
          c.fillRect(xPix - cw, top, cw*2, Math.max(bot - top, 1));
        }}
        c.restore();
      }}
    }},
    scales: {{
      x: {{
        type: 'category',
        ticks: {{
          color: '#8b949e',
          maxTicksLimit: 16,
          maxRotation: 0
        }},
        grid: {{ color: '#21262d' }}
      }},
      y: {{
        position: 'right',
        ticks: {{ color: '#8b949e', callback: v => '$' + v.toFixed(0) }},
        grid: {{ color: '#21262d' }}
      }}
    }}
  }}
}});
</script>
</body>
</html>"""

with open("/workspace/report_tsla/index.html","w") as f:
    f.write(html)
print("Chart written to /workspace/report_tsla/index.html")
