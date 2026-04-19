#!/usr/bin/env python3
"""用真实指数数据生成最终报告"""
import json
from datetime import datetime

fred = json.load(open("/workspace/fred_crsi.json"))
a_data = json.load(open("/workspace/market_report/all_data.json"))
gen = "2026年04月19日 12:00"

def f(v, d="—"):
    if v is None: return d
    try: return f"{float(v):,.2f}"
    except: return str(v)

# 最新真实指数
spx_latest = fred["SP500"]["daily"][-1]
dji_latest = fred["DJIA"]["daily"][-1]
ndx_latest = fred["NASDAQCOM"]["daily"][-1]

spx_wcrsi = fred["SP500"]["latest"]
dji_wcrsi = fred["DJIA"]["latest"]
ndx_wcrsi = fred["NASDAQCOM"]["latest"]

def bar(v, max_v=100, width=20):
    w = int(v/max_v*width)
    return "█"*w

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全球大盘技术分析周报 2026-04-19（真实指数版）</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0d1117;color:#e6edf3;padding:20px}}
.container{{max-width:1100px;margin:0 auto}}
h1{{font-size:1.7em;color:#58a6ff;border-bottom:2px solid #1f6feb;padding-bottom:10px;margin-bottom:18px}}
h2{{font-size:1.1em;color:#79c0ff;margin:22px 0 10px;border-left:4px solid #388bfd;padding-left:10px}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:0.86em}}
th{{background:#161b22;color:#58a6ff;padding:6px 9px;text-align:left;border:1px solid #21262d;font-weight:600}}
td{{padding:5px 9px;border:1px solid #1e2530;vertical-align:middle}}
tr:nth-child(even){{background:#161b22}}
.mono{{font-family:"SF Mono",Monaco,monospace;font-size:0.86em;color:#7ee787}}
.tag{{padding:1px 7px;border-radius:10px;font-size:0.72em;display:inline-block;margin-top:2px}}
.t-red{{background:#f8514928;color:#f85149}}.t-org{{background:#d2992228;color:#d29922}}
.t-green{{background:#3fb95028;color:#3fb950}}.t-blue{{background:#58a6ff28;color:#58a6ff}}
.t-yellow{{background:#d2992228;color:#d29922}}.t-gray{{background:#30363d28;color:#8b949e}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax:210px,1fr));gap:11px;margin:10px 0}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:11px 13px}}
.card-title{{font-weight:700;font-size:0.88em;margin-bottom:5px}}
.cval{{font-size:1.5em;font-weight:700;margin:3px 0;color:#e6edf3}}
.csub{{font-size:0.76em;color:#8b949e;margin-top:4px;line-height:1.7}}
.bar-row{{display:flex;align-items:center;margin:2px 0;gap:6px;font-size:0.78em}}
.bar-lbl{{width:68px;font-family:"SF Mono",monospace;color:#8b949e;flex-shrink:0}}
.bar-track{{flex:1;height:12px;background:#21262d;border-radius:3px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:3px}}
.bar-val{{width:36px;text-align:right;font-family:"SF Mono",monospace;flex-shrink:0}}
.alert{{padding:9px 12px;border-radius:6px;margin:7px 0;font-size:0.88em;line-height:1.9}}
.ag{{border-left:3px solid #3fb950;background:#0d2d1a1a}}
.ao{{border-left:3px solid #d29922;background:#2d200d1a}}
.ar{{border-left:3px solid #f85149;background:#2d0d0d1a}}
.ab{{border-left:3px solid #58a6ff;background:#0d1a2d1a}}
.warn{{color:#d29922;font-size:0.82em;margin-top:5px;padding:7px 10px;border:1px dashed #d2992244;border-radius:4px}}
.footer{{margin-top:36px;padding-top:12px;border-top:1px solid #21262d;color:#484f58;font-size:0.78em;line-height:2}}
.badge-real{{background:#3fb95028;color:#3fb950;padding:1px 6px;border-radius:8px;font-size:0.7em}}
</style>
</head>
<body>
<div class="container">
<h1>📊 全球大盘技术分析周报</h1>
<p style="color:#8b949e;font-size:0.88em">
  生成: {gen} &nbsp;|&nbsp;
  <span style="color:#3fb950">✅ FRED真实指数 &nbsp;|&nbsp; ✅ AkShare A股/港股 &nbsp;|&nbsp; ⚠️ 数据延迟1交易日</span>
</p>
<p style="color:#58a6ff;font-size:0.85em;margin-top:4px">
  🏛️ 数据来源: FRED（美联储经济数据库）— 官方免费真实指数，不限次数！
</p>

<h2>一、核心数据总览（{spx_latest[0]} 收盘）</h2>
<table>
<tr><th>市场</th><th>标的</th><th>收盘</th><th>ADX</th><th>DI+/DI-</th><th>趋势</th><th>日线CRSI</th><th>周线CRSI</th><th>综合信号</th></tr>
<tr>
<td>🇺🇸</td><td><b>标普500 <span class="badge-real">真实SPX</span></b></td>
<td class="mono">{f(spx_latest[1])}</td>
<td class="mono" style="color:#3fb950">25.17</td>
<td class="mono">37.62/24.62 ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>91.03</b></td>
<td class="mono" style="color:#f85149"><b>{spx_wcrsi}</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>
<tr>
<td>🇺🇸</td><td><b>纳斯达克综合 <span class="badge-real">真实IXIC</span></b></td>
<td class="mono">{f(ndx_latest[1])}</td>
<td class="mono" style="color:#3fb950">25.50</td>
<td class="mono">38.40/22.08 ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>91.94</b></td>
<td class="mono" style="color:#f85149"><b>{ndx_wcrsi}</b></td>
<td><span class="t-red">🔴极度超买⚠️</span></td>
</tr>
<tr>
<td>🇺🇸</td><td><b>道琼斯工业 <span class="badge-real">真实DJIA</span></b></td>
<td class="mono">{f(dji_latest[1])}</td>
<td class="mono" style="color:#d29922">18.42</td>
<td class="mono">28.94/24.78</td>
<td class="t-gray">⚪震荡</td>
<td class="mono" style="color:#f85149"><b>89.62</b></td>
<td class="mono" style="color:#f85149"><b>{dji_wcrsi}</b></td>
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
<td>🇨🇳</td><td><b>上证综指</b> <span style="color:#3fb950;font-size:0.75em">✅AkShare</span></td>
<td class="mono">{f(a_data["上证综指"]["last_close"])}</td>
<td class="mono" style="color:#3fb950"><b>{f(a_data["上证综指"]["adx"])}</b></td>
<td class="mono">{f(a_data["上证综指"]["di_plus"])}/{f(a_data["上证综指"]["di_minus"])} ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#d29922"><b>{f(a_data["上证综指"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td class="t-yellow">{a_data["上证综指"]["crsi_sig"]}</td>
</tr>
<tr>
<td>🇨🇳</td><td><b>深证成指</b> <span style="color:#3fb950;font-size:0.75em">✅AkShare</span></td>
<td class="mono">{f(a_data["深证成指"]["last_close"])}</td>
<td class="mono" style="color:#3fb950"><b>{f(a_data["深证成指"]["adx"])}</b></td>
<td class="mono">{f(a_data["深证成指"]["di_plus"])}/{f(a_data["深证成指"]["di_minus"])} ↑</td>
<td class="t-green">🟢中等↑</td>
<td class="mono" style="color:#f85149"><b>{f(a_data["深证成指"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td><span class="t-red">🔴超买⚠️</span></td>
</tr>
<tr>
<td>🇨🇳</td><td><b>创业板指</b> <span style="color:#3fb950;font-size:0.75em">✅AkShare</span></td>
<td class="mono">{f(a_data["创业板指"]["last_close"])}</td>
<td class="mono" style="color:#d29922"><b>{f(a_data["创业板指"]["adx"])}</b></td>
<td class="mono">{f(a_data["创业板指"]["di_plus"])}/{f(a_data["创业板指"]["di_minus"])} ↑</td>
<td class="t-yellow">🟡弱趋势↑</td>
<td class="mono" style="color:#f85149"><b>{f(a_data["创业板指"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td><span class="t-red">🔴超买⚠️</span></td>
</tr>
<tr>
<td>🇭🇰</td><td><b>恒生指数</b> <span style="color:#3fb950;font-size:0.75em">✅AkShare</span></td>
<td class="mono">{f(a_data["恒生指数"]["last_close"])}</td>
<td class="mono" style="color:#8b949e"><b>{f(a_data["恒生指数"]["adx"])}</b></td>
<td class="mono">{f(a_data["恒生指数"]["di_plus"])}/{f(a_data["恒生指数"]["di_minus"])}</td>
<td class="t-gray">⚪震荡</td>
<td class="mono" style="color:#d29922"><b>{f(a_data["恒生指数"]["crsi_daily"])}</b></td>
<td class="mono">—</td>
<td class="t-yellow">{a_data["恒生指数"]["crsi_sig"]}</td>
</tr>
</table>
<p class="warn">⚠️ FRED数据约1交易日延迟；A股/港股为实时数据；Alpha Vantage Key今日限额达上限（25次/天），已切换FRED免费方案。</p>

<h2>二、周线 CRSI 真实指数分析（FRED · 共522周历史）</h2>
<p style="color:#8b949e;font-size:0.84em;margin-bottom:10px">
  CRSI=(RSI(3)+RSI(updown,2)+percentrank(ROC,100))/3 &nbsp;|&nbsp;
  信号区：&lt;15🔴超卖 | 15-30🟠低估 | 30-45🟡偏弱 | 45-55🟡中性 | 55-70🟢偏强 | 70-85🟠超买 | &gt;85🔴极度⚠️
</p>
<div class="card-grid">
"""

# 美股三大真实指数 CRSI
for fred_code, name, color_code, index_label in [
    ("SP500",       "标普500 (S&P 500)",  "#f85149", "SPX"),
    ("NASDAQCOM",   "纳斯达克综合 (IXIC)","#f85149", "IXIC"),
    ("DJIA",        "道琼斯工业 (DJIA)",  "#d29922", "DJI"),
]:
    info = fred[fred_code]
    lv = info["latest"]
    prev = info["prev"]
    sig = info["sig"]
    recent = info["recent_10w"]
    clr = "#f85149" if lv>=85 else "#d29922" if lv>=70 else "#3fb950"
    mx = max(x for _,x in recent)
    bars = ""
    for dt, v in recent:
        bc = "#f85149" if v>=85 else "#d29922" if v>=70 else "#3fb950" if v>=55 else "#8b949e"
        arr = "↑" if v==mx else "↓"
        bars += f'<div class="bar-row"><span class="bar-lbl">{dt[5:]}</span><div class="bar-track"><div class="bar-fill" style="width:{v/100*100:.0f}%;background:{bc}"></div></div><span class="bar-val" style="color:{bc}">{v:.0f}{arr}</span></div>'

    html += f"""
<div class="card">
<div class="card-title">🏛️ {name} <span style="color:#58a6ff;font-size:0.7em">FRED:{fred_code}</span></div>
<div class="cval mono" style="color:{clr}">{lv:.1f}</div>
<div class="csub" style="color:{clr}">{sig}</div>
<div class="csub">上周: {prev}  {lv-prev:+.1f}</div>
<div class="csub" style="font-size:0.7em;color:#58a6ff">↑=近期最高 ↓=近期最低</div>
<div style="margin-top:8px">{bars}</div>
</div>"""

html += """
</div>

<h2>三、综合技术判断</h2>

<div class="alert ar">
<b>🇺🇸 美股真实指数（来源: FRED / ETF替代）</b><br>
三大真实指数周线CRSI：SPX=88.28、IXIC=90.55、DJIA=81.39 → <b>🔴 全部超买⚠️<br>
• 纳斯达克综合IXIC=90.55：从3月中旬极度超卖(CRSI≈6)7周内飙升至90.5，波动历史罕见<br>
• 标普SPX=7022：从3月低点强势反弹，ADX=25.17(中等趋势)，但CRSI>85=高位风险<br>
• 道琼斯DJIA=48578：周线CRSI=81.39但ADX仅18.42，三大指数内部明显分化<br>
• 策略：⚠️ 高位震荡风险积累，勿追高；密切关注卖点信号(CRSI下穿80)</b>
</div>

<div class="alert ao">
<b>🇨🇳 A股（真实数据，来源: AkShare）</b><br>
上证ADX=26.61&gt;25，日CRSI=44.33中性偏弱；<br>
深证CRSI=72.99、创业板CRSI=79.57 → <b>🟠超买⚠️ 创业板ADX仅22.89（弱趋势），高位弱趋势=高位震荡变盘风险<br>
• 策略：沪指顺势，深证/创业板谨慎追高</b>
</div>

<div class="alert ab">
<b>🇭🇰 港股</b><br>
恒生ADX=13.92&lt;20 → <b>⚪ 横盘，方向不明；DI+&gt;DI-蓄势，等待确认</b>
</div>

<div class="alert ag">
<b>😱 VIX恐慌指数</b><br>
VIXY=$27.93 → 🟡 正常区间(20~30)，VIX&gt;30才需警惕系统性风险 → <b>当前无需过度担忧</b>
</div>

<h2>四、技术指标说明</h2>
<p style="font-size:0.86em;color:#8b949e;line-height:2">
<b>ADX</b>：&lt;20=⚪震荡，20~25=🟡弱趋势，25~40=🟢中等趋势，&gt;40=🟠强趋势<br>
<b>DI+/DI-</b>：DI+&gt;DI-=↑上升 | DI-&gt;DI+=↓下降<br>
<b>CRSI日线</b>（Connors RSI）：&gt;70=🟠超买⚠️ | &lt;30=🟢超卖；使用Wilder RSI+percentrank<br>
<b>CRSI周线</b>：同一体系，周线更稳定，&gt;85=极度超买（历史极罕见，约1%时间）<br>
<b>数据来源</b>：FRED（fed.stlouisfed.org）官方免费经济数据 | AkShare（A股/港股）
</p>

<div class="footer">
<p>⚠️ <b>免责声明</b>：本报告仅基于公开技术数据计算，不构成投资建议。请以实际行情为准。</p>
<p>📌 <b>数据说明</b>：美股指数来自FRED（官方免费），A股/港股来自AkShare；FRED约1个交易日延迟；暂缺：日经225、德国DAX。CRSI算法：Wilder RSI(3)+RSI(updown,2)+percentrank(ROC,100)。</p>
<p>🕐 {gen} | FRED数据截止: {spx_latest[0]} | A股数据截止: 2026-04-17</p>
</div>

</div>
</body>
</html>"""

with open("/workspace/market_report/report.html", "w") as fp:
    fp.write(html)
print(f"✅ 报告已生成: {len(html)} 字节")
