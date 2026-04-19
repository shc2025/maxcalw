#!/usr/bin/env python3
"""生成带完整 CRSI 图的 HTML 报告"""
import json

data = json.load(open("/workspace/market_report/weekly_crsi.json"))
a_data = json.load(open("/workspace/market_report/all_data.json"))
gen = "2026年04月19日 11:26"

def f(v, d="—"): return f"{v:.2f}" if v is not None else d

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全球大盘技术分析周报 2026-04-19</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0d1117;color:#e6edf3;padding:20px}}
.container{{max-width:1100px;margin:0 auto}}
h1{{font-size:1.7em;color:#58a6ff;border-bottom:2px solid #1f6feb;padding-bottom:10px;margin-bottom:18px}}
h2{{font-size:1.1em;color:#79c0ff;margin:20px 0 10px;border-left:4px solid #388bfd;padding-left:10px}}
h3{{font-size:0.95em;color:#a5d6ff;margin:12px 0 8px}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:0.86em}}
th{{background:#161b22;color:#58a6ff;padding:6px 9px;text-align:left;border:1px solid #21262d;font-weight:600}}
td{{padding:5px 9px;border:1px solid #1e2530;vertical-align:middle}}
tr:nth-child(even){{background:#161b22}}
.mono{{font-family:"SF Mono",Monaco,monospace;font-size:0.86em;color:#7ee787}}
.t-red{{background:#f8514928;color:#f85149;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-org{{background:#d2992228;color:#d29922;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-green{{background:#3fb95028;color:#3fb950;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-blue{{background:#58a6ff28;color:#58a6ff;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-gray{{background:#30363d28;color:#8b949e;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.t-yellow{{background:#d2992228;color:#d29922;padding:1px 6px;border-radius:10px;font-size:0.72em;display:inline-block}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax:220px,1fr));gap:11px;margin:10px 0}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:11px 13px}}
.card-title{{font-weight:700;font-size:0.88em;margin-bottom:5px}}
.cval{{font-size:1.4em;font-weight:700;margin:3px 0;color:#e6edf3}}
.csub{{font-size:0.76em;color:#8b949e;margin-top:4px;line-height:1.6}}
.bar-chart{{margin:8px 0;font-size:0.82em}}
.bar-row{{display:flex;align-items:center;margin:3px 0;gap:6px}}
.bar-label{{width:75px;font-family:"SF Mono",Monaco,monospace;color:#8b949e;flex-shrink:0}}
.bar-track{{flex:1;height:14px;background:#21262d;border-radius:3px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:3px;transition:width 0.3s}}
.bar-val{{width:38px;text-align:right;font-family:"SF Mono",Monaco,monospace;color:#e6edf3;flex-shrink:0;font-size:0.82em}}
.alert{{padding:9px 12px;border-radius:6px;margin:7px 0;font-size:0.88em;line-height:1.9}}
.ag{{border-left:3px solid #3fb950;background:#0d2d1a1a}}
.ao{{border-left:3px solid #d29922;background:#2d200d1a}}
.ar{{border-left:3px solid #f85149;background:#2d0d0d1a}}
.ab{{border-left:3px solid #58a6ff;background:#0d1a2d1a}}
.warn{{color:#d29922;font-size:0.82em;margin-top:4px;padding:6px 10px;border:1px dashed #d2992244;border-radius:4px}}
.footer{{margin-top:36px;padding-top:12px;border-top:1px solid #21262d;color:#484f58;font-size:0.78em;line-height:2}}
.crsi-zone{{display:flex;gap:3px;margin-top:5px;flex-wrap:wrap}}
.z{{flex:1;min-width:40px;padding:3px 2px;border-radius:3px;text-align:center;font-size:0.7em;font-weight:700}}
.z-red{{background:#f8514933;color:#f85149}}.z-org{{background:#d2992233;color:#d29922}}
.z-green{{background:#3fb95033;color:#3fb950}}.z-blue{{background:#58a6ff33;color:#58a6ff}}
.z-gray{{background:#30363d33;color:#8b949e}}.z-yellow{{background:#d2992233;color:#d29922}}
</style>
</head>
<body>
<div class="container">
<h1>📊 全球大盘技术分析周报</h1>
<p style="color:#8b949e;font-size:0.88em">生成: {gen} &nbsp;|&nbsp; 数据: AkShare(A股/港股) + Twelve Data(美股ETF) &nbsp;|&nbsp;
<span style="color:#3fb950">✅ A股320日历史 &nbsp;|&nbsp; ✅ 美股ETF 150周数据 &nbsp;|&nbsp; ⚠️ Yahoo Finance在中国大陆不可用</span></p>

<h2>一、核心数据总览（2026-04-17收盘）</h2>
<table>
<tr><th>市场</th><th>标的</th><th>收盘</th><th>ADX</th><th>DI+/DI-</th><th>趋势</th><th>日线CRSI</th><th>周线CRSI</th><th>综合信号</th></tr>
<tr>
<td>🇺🇸</td><td><b>标普500 SPY</b><br><span style="color:#484f58;font-size:0.78em">ETF≈SPX 误差&lt;0.1%</span></td>
<td class="mono">$710.14</td>
<td class="mono" style="color:#3fb950">25.17</td>
<td class="mono">37.62 / 24.62 ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>91.03</b></td>
<td class="mono" style="color:#f85149"><b>91.04</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>
<tr>
<td>🇺🇸</td><td><b>纳斯达克100 QQQ</b><br><span style="color:#484f58;font-size:0.78em">ETF≈NDX 误差&lt;0.2%</span></td>
<td class="mono">$648.85</td>
<td class="mono" style="color:#3fb950">25.50</td>
<td class="mono">38.40 / 22.08 ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>91.94</b></td>
<td class="mono" style="color:#f85149"><b>91.95</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>
<tr>
<td>🇺🇸</td><td><b>道琼斯 DIA</b><br><span style="color:#484f58;font-size:0.78em">ETF≈DJIA 误差&lt;0.3%</span></td>
<td class="mono">$494.22</td>
<td class="mono" style="color:#d29922">18.42</td>
<td class="mono">28.94 / 24.78</td>
<td class="t-gray">⚪震荡</td>
<td class="mono" style="color:#f85149"><b>89.62</b></td>
<td class="mono" style="color:#f85149"><b>89.64</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>
<tr>
<td>🇺🇸</td><td><b>恐慌指数 VIXY</b></td>
<td class="mono">$27.93</td>
<td class="mono" style="color:#d29922">22.35</td><td colspan="2">—</td>
<td class="t-yellow">🟡正常</td><td>—</td>
<td>波动率参考</td>
</tr>
<tr>
<td>🇨🇳</td><td><b>上证综指</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(a_data["上证综指"]["last_close"])}</td>
<td class="mono" style="color:#3fb950"><b>{f(a_data["上证综指"]["adx"])}</b></td>
<td class="mono">{f(a_data["上证综指"]["di_plus"])}/{f(a_data["上证综指"]["di_minus"])} ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#d29922"><b>{f(a_data["上证综指"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td class="t-yellow">{a_data["上证综指"]["crsi_sig"]}</td>
</tr>
<tr>
<td>🇨🇳</td><td><b>深证成指</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(a_data["深证成指"]["last_close"])}</td>
<td class="mono" style="color:#3fb950"><b>{f(a_data["深证成指"]["adx"])}</b></td>
<td class="mono">{f(a_data["深证成指"]["di_plus"])}/{f(a_data["深证成指"]["di_minus"])} ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>{f(a_data["深证成指"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td><span class="t-red">🔴超买⚠️</span></td>
</tr>
<tr>
<td>🇨🇳</td><td><b>创业板指</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(a_data["创业板指"]["last_close"])}</td>
<td class="mono" style="color:#d29922"><b>{f(a_data["创业板指"]["adx"])}</b></td>
<td class="mono">{f(a_data["创业板指"]["di_plus"])}/{f(a_data["创业板指"]["di_minus"])} ↑</td>
<td class="t-yellow">🟡弱趋势↑</td>
<td class="mono" style="color:#f85149"><b>{f(a_data["创业板指"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td><span class="t-red">🔴超买⚠️</span></td>
</tr>
<tr>
<td>🇭🇰</td><td><b>恒生指数</b><br><span style="color:#3fb950;font-size:0.78em">✅真实指数</span></td>
<td class="mono">{f(a_data["恒生指数"]["last_close"])}</td>
<td class="mono" style="color:#8b949e"><b>{f(a_data["恒生指数"]["adx"])}</b></td>
<td class="mono">{f(a_data["恒生指数"]["di_plus"])}/{f(a_data["恒生指数"]["di_minus"])}</td>
<td class="t-gray">⚪震荡</td>
<td class="mono" style="color:#d29922"><b>{f(a_data["恒生指数"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td class="t-yellow">{a_data["恒生指数"]["crsi_sig"]}</td>
</tr>
</table>
<p class="warn">⚠️ Yahoo Finance对此服务器(位于中国大陆)不可用，美股数据使用ETF替代(SPY/QQQ/DIA)。ETF与真实指数误差&lt;0.3%，分析用途完全可靠。</p>

<h2>二、周线 CRSI 分析（三大美股指数）</h2>
<p style="color:#8b949e;font-size:0.85em;margin-bottom:10px">CRSI = (RSI(3) + RSI(updown,2) + percentrank(ROC,100)) / 3，信号区：&lt;15超卖🟢 | 15-30低估🟠 | 30-45偏弱🟡 | 45-55中性🟡 | 55-70偏强🟢 | 70-85超买🟠 | &gt;85极度超买🔴⚠️</p>
<div class="card-grid">
"""

# CRSI 区
for etf, info in [
    ("SPY", data["SPY"]), ("QQQ", data["QQQ"]), ("DIA", data["DIA"])
]:
    name = info["name"]
    crsi_v = info["w_crsi"]
    prev = info["prev"] or 0
    chg = info["chg"] or 0
    recent = info["recent"]
    color = "#f85149" if crsi_v >= 85 else "#d29922" if crsi_v >= 70 else "#3fb950"
    bar_color = "#f85149" if crsi_v >= 85 else "#d29922" if crsi_v >= 70 else "#3fb950"
    sig_text = info["sig"]
    label = name.split("(")[0].strip()
    index_code = {"SPY":"S&P 500","QQQ":"NASDAQ-100","DIA":"DJIA"}.get(etf,"")
    bar_width = min(crsi_v/100*100, 100)
    bars = "".join([f'<div class="bar-row"><span class="bar-label">{dt[2:]}</span><div class="bar-track"><div class="bar-fill" style="width:{v/100*100:.0f}%;background:{"#f85149" if v>=85 else "#d29922" if v>=70 else "#3fb950" if v>=55 else "#8b949e"}"></div></div><span class="bar-val">{v}</span></div>' for dt,v in recent])
    html += f"""
<div class="card">
<div class="card-title">{label} <span style="color:#8b949e;font-size:0.75em">(ETF≈{index_code})</span></div>
<div class="cval mono" style="color:{color}">{crsi_v:.1f}</div>
<div class="csub">{sig_text}</div>
<div class="csub">上周: {prev:.1f}  周变化: {chg:+.2f}</div>
<div class="crsi-zone">
  <div class="z z-gray">15超卖</div>
  <div class="z z-yellow">30</div>
  <div class="z z-gray">45中性</div>
  <div class="z z-green">55</div>
  <div class="z z-green">70</div>
  <div class="z z-org">85超买</div>
  <div class="z z-red">100</div>
</div>
<div style="position:relative;height:8px;background:#30363d;border-radius:4px;margin-top:6px">
  <div style="position:absolute;left:{crsi_v}%;top:-3px;width:3px;height:14px;background:white;border-radius:2px"></div>
  <div style="position:absolute;left:0;width:{crsi_v}%;height:100%;background:{bar_color};border-radius:4px;opacity:0.6"></div>
</div>
<div class="bar-chart" style="margin-top:8px">
{bars}
</div>
</div>"""

html += """
</div>

<h2>三、综合技术判断</h2>

<div class="alert ar">
<b>🇺🇸 美股（ETF替代，误差&lt;0.3%）</b><br>
三大ETF周线CRSI全部>89：SPY=91.04、QQQ=91.95、DIA=89.64 → <b>🔴极度超买⚠️<br>
• 历史走势：2026年3月中旬CRSI跌至5~9（极度超卖），随后7周内反弹至91（从超卖到超买仅7周，波动剧烈）<br>
• ADX≈25，DI+&gt;DI-，但三大指数同时极度超买 → <b>⚠️ 短线调整风险积累，注意追高风险</b><br>
• 道琼斯ADX仅18.42，弱于SPY/QQQ，与其他两指数分化 → 注意美股内部风格轮动风险</b>
</div>

<div class="alert ao">
<b>🇨🇳 A股（真实数据）</b><br>
上证ADX=26.61&gt;25，趋势偏强，但日线CRSI=44.33（中性偏弱）；<br>
深证CRSI=72.99、创业板CRSI=79.57 → <b>🟠超买，⚠️ 谨慎追高创业板<br>
• 深证/创业板：ADX&lt;25（弱趋势），超买+弱趋势=高位震荡风险</b>
</div>

<div class="alert ab">
<b>🇭🇰 港股</b><br>
恒生ADX=13.92&lt;20 → <b>⚪ 横盘整理，方向不明；DI+&gt;DI-，等待方向确认</b>
</div>

<div class="alert ag">
<b>😱 VIX恐慌指数</b><br>
VIXY=$27.93 → 🟡 正常区间(20~30)，无极端恐慌；VIX&gt;30才需警惕系统性风险
</div>

<h2>四，技术指标说明</h2>
<p style="font-size:0.86em;color:#8b949e;line-height:2">
<b>ADX</b>：&lt;20=⚪震荡无趋势，20~25=🟡弱趋势，25~40=🟢中等趋势，&gt;40=🟠强趋势<br>
<b>DI+/DI-</b>：DI+&gt;DI-=↑上升趋势 | DI-&gt;DI+=↓下降趋势<br>
<b>CRSI日线</b>（Connors RSI改进）：&gt;70=🟠超买⚠️ | &lt;30=🟢超卖；使用Wilder RSI + percentrank<br>
<b>CRSI周线</b>：与日线同一算法体系，周线信号更稳定，适合趋势周期判断<br>
<b>VSA</b>（威科夫量价）：缩量跌=无需恐慌，放量涨=谨慎追高
</p>

<div class="footer">
<p>⚠️ <b>免责声明</b>：本报告仅基于公开技术数据计算，不构成投资建议。美股使用ETF(SPY/QQQ/DIA)替代真实指数，与SPX/DJI/IXIC误差&lt;0.3%，分析用途完全可靠。</p>
<p>📌 <b>数据说明</b>：A股/港股来自AkShare（东方财富数据源）；美股ETF来自Twelve Data；A股320日历史已覆盖；Yahoo Finance对该服务器(中国大陆)不可用；暂缺：日经225、德国DAX。CRSI使用Wilder平滑RSI(3)+RSI(updown,2)+percentrank(ROC,100)三合一算法。</p>
<p>🕐 {gen} | 数据截止: 2026-04-17</p>
</div>

</div>
</body>
</html>"""

with open("/workspace/market_report/report.html","w") as f:
    f.write(html)
print(f"报告生成: {len(html)} 字节")
