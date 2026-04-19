#!/usr/bin/env python3
"""大盘分析报告生成器"""
import json
from datetime import datetime as dt

data = json.load(open("/workspace/market_report/all_data.json"))
gen = dt.now().strftime("%Y年%m月%d日 %H:%M")

def f(v, d="—"):
    if v is None: return d
    try: return f"{float(v):.2f}"
    except: return str(v)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全球大盘技术分析周报 {gen[:10]}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0d1117;color:#e6edf3;padding:24px}}
.container{{max-width:1100px;margin:0 auto}}
h1{{font-size:1.8em;color:#58a6ff;border-bottom:2px solid #1f6feb;padding-bottom:12px;margin-bottom:20px}}
h2{{font-size:1.15em;color:#79c0ff;margin:24px 0 12px;border-left:4px solid #388bfd;padding-left:10px}}
h3{{font-size:0.95em;color:#a5d6ff;margin:14px 0 8px}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:0.87em}}
th{{background:#161b22;color:#58a6ff;padding:7px 9px;text-align:left;border:1px solid #21262d;font-weight:600;white-space:nowrap}}
td{{padding:6px 9px;border:1px solid #1e2530;vertical-align:middle}}
tr:nth-child(even){{background:#161b22}}
.mono{{font-family:"SF Mono",Monaco,monospace;font-size:0.87em;color:#7ee787}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax:230px,1fr));gap:11px;margin:10px 0}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:11px 13px}}
.card-title{{font-weight:700;font-size:0.9em;margin-bottom:5px}}
.cval{{font-size:1.45em;font-weight:700;margin:3px 0;color:#e6edf3}}
.csub{{font-size:0.78em;color:#8b949e;margin-top:4px;line-height:1.6}}
.t-red{{background:#f8514928;color:#f85149;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-org{{background:#d2992228;color:#d29922;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-green{{background:#3fb95028;color:#3fb950;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-blue{{background:#58a6ff28;color:#58a6ff;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-gray{{background:#30363d28;color:#8b949e;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.alert{{padding:10px 13px;border-radius:6px;margin:7px 0;font-size:0.88em;line-height:1.9}}
.ag{{border-left:3px solid #3fb950;background:#0d2d1a1a}}
.ao{{border-left:3px solid #d29922;background:#2d200d1a}}
.ar{{border-left:3px solid #f85149;background:#2d0d0d1a}}
.ab{{border-left:3px solid #58a6ff;background:#0d1a2d1a}}
.warn{{color:#d29922;font-size:0.82em;margin-top:4px;padding:6px 10px;border:1px dashed #d2992244;border-radius:4px}}
.ft{{margin-top:36px;padding-top:12px;border-top:1px solid #21262d;color:#484f58;font-size:0.8em;line-height:2}}
</style>
</head>
<body>
<div class="container">
<h1>📊 全球大盘技术分析周报</h1>
<p style="color:#8b949e;font-size:0.88em">
  生成: {gen} &nbsp;|&nbsp; 数据: AkShare(A股/港股) + Twelve Data(美股ETF)
</p>
<p style="color:#3fb950;font-size:0.87em;margin-top:4px">✅ A股320日历史已覆盖 &nbsp;|&nbsp; ✅ 美股ETF数据(SPY/QQQ/DIA)已覆盖 &nbsp;|&nbsp; ⚠️ yfinance真实指数(SPX/DJI/IXIC)限流中
</p>

<h2>一、核心数据总览（2026-04-17收盘）</h2>
<table>
<tr><th>市场</th><th>标的</th><th>收盘</th><th>ADX</th><th>DI+</th><th>DI-</th><th>趋势</th><th>日线CRSI</th><th>信号</th></tr>

<tr>
<td>🇺🇸</td><td><b>标普500 SPY</b><br><span style="color:#484f58;font-size:0.78em">(ETF替代)</span></td>
<td class="mono">${f(data.get("SPY",{}).get("last_close"))}</td>
<td class="mono" style="color:#3fb950"><b>{f(data.get("SPY",{}).get("adx"))}</b></td>
<td class="mono">{f(data.get("SPY",{}).get("di_plus"))}</td>
<td class="mono">{f(data.get("SPY",{}).get("di_minus"))}</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>{f(data.get("SPY",{}).get("w_crsi") or data.get("SPY",{}).get("crsi_daily"))}</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>

<tr>
<td>🇺🇸</td><td><b>纳斯达克100 QQQ</b><br><span style="color:#484f58;font-size:0.78em">(ETF替代)</span></td>
<td class="mono">${f(data.get("QQQ",{}).get("last_close"))}</td>
<td class="mono" style="color:#3fb950"><b>{f(data.get("QQQ",{}).get("adx"))}</b></td>
<td class="mono">{f(data.get("QQQ",{}).get("di_plus"))}</td>
<td class="mono">{f(data.get("QQQ",{}).get("di_minus"))}</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>{f(data.get("QQQ",{}).get("w_crsi") or data.get("QQQ",{}).get("crsi_daily"))}</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>

<tr>
<td>🇺🇸</td><td><b>道琼斯 DIA</b><br><span style="color:#484f58;font-size:0.78em">(ETF替代)</span></td>
<td class="mono">${f(data.get("DIA",{}).get("last_close"))}</td>
<td class="mono" style="color:#d29922"><b>{f(data.get("DIA",{}).get("adx"))}</b></td>
<td class="mono">{f(data.get("DIA",{}).get("di_plus"))}</td>
<td class="mono">{f(data.get("DIA",{}).get("di_minus"))}</td>
<td class="t-gray">⚪震荡</td>
<td class="mono" style="color:#f85149"><b>{f(data.get("DIA",{}).get("w_crsi") or data.get("DIA",{}).get("crsi_daily"))}</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>

<tr>
<td>🇺🇸</td><td><b>恐慌指数 VIXY</b></td>
<td class="mono">${f(data.get("恐慌指数(VIXY)",{}).get("last_close"))}</td>
<td class="mono" style="color:#d29922">22.35</td>
<td colspan="2">—</td>
<td class="t-org">🟡正常区间</td>
<td>—</td>
<td>波动率参考</td>
</tr>

<tr>
<td>🇨🇳</td><td><b>上证综指</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(data["上证综指"]["last_close"])}</td>
<td class="mono" style="color:#3fb950"><b>{f(data["上证综指"]["adx"])}</b></td>
<td class="mono">{f(data["上证综指"]["di_plus"])}</td>
<td class="mono">{f(data["上证综指"]["di_minus"])}</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#d29922"><b>{f(data["上证综指"]["crsi_daily"])}</b></td>
<td class="t-org">{data["上证综指"]["crsi_sig"]}</td>
</tr>

<tr>
<td>🇨🇳</td><td><b>深证成指</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(data["深证成指"]["last_close"])}</td>
<td class="mono" style="color:#3fb950"><b>{f(data["深证成指"]["adx"])}</b></td>
<td class="mono">{f(data["深证成指"]["di_plus"])}</td>
<td class="mono">{f(data["深证成指"]["di_minus"])}</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>{f(data["深证成指"]["crsi_daily"])}</b></td>
<td><span class="t-red">🔴超买⚠️</span></td>
</tr>

<tr>
<td>🇨🇳</td><td><b>创业板指</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(data["创业板指"]["last_close"])}</td>
<td class="mono" style="color:#d29922"><b>{f(data["创业板指"]["adx"])}</b></td>
<td class="mono">{f(data["创业板指"]["di_plus"])}</td>
<td class="mono">{f(data["创业板指"]["di_minus"])}</td>
<td class="t-org">🟡弱趋势↑</td>
<td class="mono" style="color:#f85149"><b>{f(data["创业板指"]["crsi_daily"])}</b></td>
<td><span class="t-red">🔴超买⚠️</span></td>
</tr>

<tr>
<td>🇭🇰</td><td><b>恒生指数 HSI</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(data["恒生指数"]["last_close"])}</td>
<td class="mono" style="color:#8b949e"><b>{f(data["恒生指数"]["adx"])}</b></td>
<td class="mono">{f(data["恒生指数"]["di_plus"])}</td>
<td class="mono">{f(data["恒生指数"]["di_minus"])}</td>
<td class="t-gray">⚪震荡</td>
<td class="mono" style="color:#d29922"><b>{f(data["恒生指数"]["crsi_daily"])}</b></td>
<td class="t-org">{data["恒生指数"]["crsi_sig"]}</td>
</tr>
</table>
<p class="warn">⚠️ 美股使用ETF替代（SPY≈SPX, QQQ≈纳指, DIA≈DJI），高度相关但存在差异。真实指数(SPX/DJI/IXIC)待yfinance限流恢复后更新。</p>

<h2>二、分市场技术分析</h2>

<h3>🇺🇸 美股（ETF替代数据）</h3>
<div class="card-grid">
<div class="card">
<div class="card-title">标普500 SPY (S&P 500 ETF)</div>
<div class="cval mono">${f(data.get("SPY",{}).get("last_close"))}</div>
<div class="csub">ADX={f(data.get("SPY",{}).get("adx"))} <b class="t-green">🟢 中等上升趋势</b></div>
<div class="csub">DI+={f(data.get("SPY",{}).get("di_plus"))} &gt; DI-={f(data.get("SPY",{}).get("di_minus"))} → 上升动能强</div>
<div class="csub">5日涨跌: <span style="color:#3fb950">+4.52%</span></div>
<div class="csub">近30日: 高=${f(data.get("SPY",{}).get("recent_high"))} 低=${f(data.get("SPY",{}).get("recent_low"))}</div>
<div class="csub"><span class="t-red">⚠️ 日线CRSI={f(data.get("SPY",{}).get("w_crsi") or data.get("SPY",{}).get("crsi_daily"))} 极度超买 注意高位风险</span></div>
</div>
<div class="card">
<div class="card-title">纳斯达克100 QQQ (Nasdaq-100 ETF)</div>
<div class="cval mono">${f(data.get("QQQ",{}).get("last_close"))}</div>
<div class="csub">ADX={f(data.get("QQQ",{}).get("adx"))} <b class="t-green">🟢 中等上升趋势</b></div>
<div class="csub">DI+={f(data.get("QQQ",{}).get("di_plus"))} &gt; DI-={f(data.get("QQQ",{}).get("di_minus"))}</div>
<div class="csub">5日涨跌: <span style="color:#3fb950">+6.18%</span> <span class="t-red">⚡ 急涨后观察</span></div>
<div class="csub">近30日: 高=${f(data.get("QQQ",{}).get("recent_high"))} 低=${f(data.get("QQQ",{}).get("recent_low"))}</div>
<div class="csub"><span class="t-red">⚠️ 日线CRSI={f(data.get("QQQ",{}).get("w_crsi") or data.get("QQQ",{}).get("crsi_daily"))} 极度超买+急涨后</span></div>
</div>
<div class="card">
<div class="card-title">道琼斯 DIA (DJIA ETF)</div>
<div class="cval mono">${f(data.get("DIA",{}).get("last_close"))}</div>
<div class="csub">ADX={f(data.get("DIA",{}).get("adx"))} <b class="t-gray">⚪ 震荡无趋势</b></div>
<div class="csub">DI+&gt;DI- 但ADX&lt;20，方向偏多但趋势不足</div>
<div class="csub">5日涨跌: <span style="color:#3fb950">+3.12%</span></div>
<div class="csub"><span class="t-red">⚠️ 日线CRSI={f(data.get("DIA",{}).get("w_crsi") or data.get("DIA",{}).get("crsi_daily"))} 极度超买</span></div>
</div>
<div class="card">
<div class="card-title">恐慌指数 VIXY</div>
<div class="cval mono" style="color:#d29922">${f(data.get("恐慌指数(VIXY)",{}).get("last_close"))}</div>
<div class="csub"><b class="t-org">🟡 正常区间(20~30)</b></div>
<div class="csub">VIXY收盘{f(data.get("恐慌指数(VIXY)",{}).get("last_close"))} → 市场紧张程度中等</div>
<div class="csub">VIX&gt;30通常对应股市下跌压力</div>
</div>
</div>

<h3>🇨🇳 A股（真实指数，320日历史）</h3>
<div class="card-grid">
<div class="card">
<div class="card-title">上证综指</div>
<div class="cval mono">{f(data["上证综指"]["last_close"])}</div>
<div class="csub">ADX={f(data["上证综指"]["adx"])} <b class="t-green">🟢 中等上升趋势</b></div>
<div class="csub">DI+={f(data["上证综指"]["di_plus"])} &gt; DI-={f(data["上证综指"]["di_minus"])}</div>
<div class="csub">日线CRSI={f(data["上证综指"]["crsi_daily"])} {data["上证综指"]["crsi_sig"]}</div>
<div class="csub">近30日高=4058.6 低=3794.7</div>
</div>
<div class="card">
<div class="card-title">深证成指</div>
<div class="cval mono">{f(data["深证成指"]["last_close"])}</div>
<div class="csub">ADX={f(data["深证成指"]["adx"])} <b class="t-green">🟢 中等上升趋势</b></div>
<div class="csub">DI+={f(data["深证成指"]["di_plus"])} &gt; DI-={f(data["深证成指"]["di_minus"])} → 强上升</div>
<div class="csub"><span class="t-red">⚠️ 日线CRSI={f(data["深证成指"]["crsi_daily"])} {data["深证成指"]["crsi_sig"]}</span></div>
</div>
<div class="card">
<div class="card-title">创业板指</div>
<div class="cval mono">{f(data["创业板指"]["last_close"])}</div>
<div class="csub">ADX={f(data["创业板指"]["adx"])} <b class="t-org">🟡 弱趋势</b></div>
<div class="csub">DI+={f(data["创业板指"]["di_plus"])} &gt; DI-={f(data["创业板指"]["di_minus"])}</div>
<div class="csub"><span class="t-red">⚠️ 日线CRSI={f(data["创业板指"]["crsi_daily"])} {data["创业板指"]["crsi_sig"]}</span></div>
</div>
</div>

<h3>🇭🇰 港股</h3>
<div class="card-grid">
<div class="card">
<div class="card-title">恒生指数 (HSI)</div>
<div class="cval mono">{f(data["恒生指数"]["last_close"])}</div>
<div class="csub">ADX={f(data["恒生指数"]["adx"])} <b class="t-gray">⚪ 无明确趋势</b></div>
<div class="csub">DI+={f(data["恒生指数"]["di_plus"])} &gt; DI-={f(data["恒生指数"]["di_minus"])} → 方向偏上</div>
<div class="csub">⚠️ ADX&lt;20 横盘整理，等待方向确认</div>
<div class="csub">日线CRSI={f(data["恒生指数"]["crsi_daily"])} {data["恒生指数"]["crsi_sig"]}</div>
</div>
</div>

<h2>三，综合技术判断</h2>

<div class="alert ar">
<b>🇺🇸 美股（ETF替代）</b><br>
SPY/QQQ ADX≈25.17/25.50，DI+&gt;DI-，上升趋势；但三大ETF日线CRSI全部&gt;89（SPY=91.03, QQQ=91.94, DIA=89.62），极度超买，DIA的ADX仅18.42（弱势），三大指数分化 → <b>⚠️ 谨慎，高位回调风险显著；纳指+6%急涨后观察</b>
</div>

<div class="alert ao">
<b>🇨🇳 A股（真实数据，320日）</b><br>
上证ADX=26.61&gt;25，DI+&gt;DI-，偏强；深证CRSI=72.99 ⚠️超买；创业板CRSI=79.57 ⚠️接近80超买；创业板ADX=22.89&lt;25，方向积累 → <b>⚠️ 沪指可顺势，深证和创业板谨慎追高</b>
</div>

<div class="alert ab">
<b>🇭🇰 港股</b><br>
恒生ADX=13.92&lt;20，⚪横盘无趋势；DI+&gt;DI-蓄势 → <b>等待方向确认，注意变盘信号</b>
</div>

<div class="alert ag">
<b>😱 VIX恐慌指数</b><br>
VIXY=$27.93 → <b>🟡 正常区间(20~30)</b>，无极端恐慌，VIX&gt;30通常对应股市压力 → <b>当前无需过度担忧</b>
</div>

<h2>四，技术指标说明</h2>
<p style="font-size:0.87em;color:#8b949e;line-height:2">
<b>ADX</b>：&lt;20=⚪震荡无趋势，20~25=🟡弱趋势，25~40=🟢中等趋势，&gt;40=🟠强趋势<br>
<b>DI+/DI-</b>：DI+&gt;DI-=↑上升趋势 | DI-&gt;DI+=↓下降趋势<br>
<b>CRSI日线</b>（Connors RSI改进版）：&gt;70=🟠超买⚠️(谨慎追高)，&lt;30=🟢超卖(关注买入)；使用Wilder RSI+percentrank算法<br>
<b>VSA</b>（威科夫量价）：缩量跌=无需恐慌，放量涨=谨慎追高
</p>

<div class="ft">
<p>⚠️ <b>免责声明</b>：本报告仅基于公开技术数据计算，不构成投资建议。美股ETF(SPY/QQQ/DIA)与真实指数(SPX/DJI/IXIC)高度相关但存在差异，请以实际行情为准。</p>
<p>📌 <b>数据说明</b>：A股/港股来自AkShare（东方财富数据源），320日历史；美股ETF来自Twelve Data；暂缺：日经225、德国DAX、法国CAC40、韩国KOSPI；yfinance真实指数(SPX/DJI/IXIC)限流中待恢复。</p>
<p>🕐 {gen} | 数据截止: 2026-04-17</p>
</div>

</div>
</body>
</html>"""

with open("/workspace/market_report/report.html", "w") as fp:
    fp.write(html)
print(f"报告生成完成! {len(html)} 字节")
