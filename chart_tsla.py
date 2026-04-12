import json
with open('/workspace/backtest_tsla_results.json') as f:
    d = json.load(f)

eq    = d['equity_curve']
sum_  = d['summary']
dates = [r[0] for r in eq]
vals  = [r[1] for r in eq]

html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>TSLA M13/M200 回测</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
body{{font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;margin:40px}}
h2{{text-align:center;color:#58a6ff}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;max-width:960px;margin:0 auto 30px}}
.stat{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;text-align:center}}
.stat .l{{font-size:12px;color:#8b949e;margin-bottom:6px}}
.stat .v{{font-size:20px;font-weight:bold;color:#58a6ff}}
.pos{{color:#3fb950}}.neg{{color:#f85149}}
.tbl{{max-width:960px;margin:0 auto;border-collapse:collapse;font-size:13px}}
th{{background:#161b22;color:#8b949e;padding:8px 6px;text-align:left;border-bottom:1px solid #30363d}}
td{{padding:7px 6px;border-bottom:1px solid #21262d;color:#c9d1d9}}
tr:nth-child(even){{background:#161b22}}
canvas{{max-width:960px;margin:20px auto;display:block}}
</style></head><body>
<h2>📈 TSLA M13/M200 策略回测报告（2021–2026）</h2>

<div class=stats>
  <div class=stat><div class=l>总收益率</div><div class="v pos">{sum_['total_return']:.2f}%</div></div>
  <div class=stat><div class=l>年化收益率</div><div class="v pos">{sum_['cagr']:.2f}%</div></div>
  <div class=stat><div class=l>夏普比率</div><div class=v>{sum_['sharpe_annual']:.3f}</div></div>
  <div class=stat><div class=l>胜率</div><div class="v pos">{sum_['win_rate']:.1f}%</div></div>
  <div class=stat><div class=l>最大回撤</div><div class="v neg">-${sum_['max_drawdown']:,.0f}</div></div>
  <div class=stat><div class=l>盈亏比</div><div class=v>{sum_['profit_factor']:.2f}</div></div>
  <div class=stat><div class=l>索提诺比率</div><div class=v>{sum_['sortino_annual']:.3f}</div></div>
  <div class=stat><div class=l>总交易</div><div class=v>{sum_['total_trades']} 笔</div></div>
</div>

<table class=tbl>
<tr><th>买入日期</th><th>买入价</th><th>数量</th><th>卖出日期</th><th>卖出价</th><th>出场原因</th><th>盈亏</th><th>收益率</th></tr>
"""

for t in d['trades']:
    cls = 'pos' if t['pnl']>0 else 'neg'
    html += f"<tr><td>{t['date_in']}</td><td>${t['price_in']:.2f}</td><td>{t['shares']}</td>"
    html += f"<td>{t.get('date_out','N/A')}</td><td>${t.get('price_out',0):.2f}</td>"
    html += f"<td>{t['exit_reason']}</td>"
    html += f"<td class={cls}>${t['pnl']:+,.2f}</td><td class={cls}>{t['ret_pct']:+.2f}%</td></tr>"

html += "</table><canvas id=eq></canvas><script>"
html += f"new Chart(document.getElementById('eq'),{{type:'line',data:{{labels:{json.dumps(dates)},datasets:[{{label:'组合净值',data:{json.dumps(vals)},borderColor:'#58a6ff',backgroundColor:'rgba(88,166,255,0.1)',borderWidth:1.5,fill:true,tension:0.2,pointRadius:0}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{x:{{ticks:{{color:'#8b949e',maxTicksLimit:12}},grid:{{color:'#21262d'}}}},y:{{ticks:{{color:'#8b949e'}},grid:{{color:'#21262d'}}}}}}}})"
html += "</script></body></html>"

with open('/workspace/report_tsla/index.html','w') as f:
    f.write(html)
print("Chart saved to /workspace/report_tsla/index.html")
