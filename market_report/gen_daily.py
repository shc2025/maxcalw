#!/usr/bin/env python3
"""大盘日报指标计算"""
import json
from datetime import datetime

data = json.load(open("/workspace/market_report/today_data.json"))
fred = data["fred"]
a_sh = data["a_share"]
etf = data["etf"]

def wilder_rsi(prices, period):
    n=len(prices); r=[None]*n
    g=[max(prices[i]-prices[i-1],0.0) for i in range(1,n)]
    l=[abs(min(prices[i]-prices[i-1],0.0)) for i in range(1,n)]
    if len(g)<period: return r
    ag=sum(g[:period])/period; al=sum(l[:period])/period
    r[period]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    for i in range(period,len(g)):
        ag=(ag*(period-1)+g[i])/period; al=(al*(period-1)+l[i])/period
        r[i+1]=100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    return r

def updown(closes):
    ud=[0.0]*len(closes); p=0.0
    for i in range(1,len(closes)):
        if closes[i]==closes[i-1]: p=0.0
        elif closes[i]>closes[i-1]: p=1.0 if p<=0 else p+1.0
        else: p=-1.0 if p>=0 else p-1.0
        ud[i]=p
    return ud

def pct_rank(series, lookback):
    n=len(series); r=[None]*n
    for i in range(lookback,n):
        valid=[series[j] for j in range(i-lookback,i) if series[j] is not None]
        r[i]=round(sum(1 for v in valid if v<series[i])/len(valid)*100.0,2) if valid else 50.0
    return r

def roc(closes, period=1):
    return [None]*period+[(closes[i]-closes[i-period])/closes[i-period]*100.0 if closes[i-period]!=0 else 0.0 for i in range(period,len(closes))]

def crsi(closes):
    rp=wilder_rsi(closes,3); ud=updown(closes); ru=wilder_rsi(ud,2)
    rc=roc(closes,1); pr=pct_rank(rc,100)
    return [round((rp[i]+ru[i]+pr[i])/3.0,2) if None not in [rp[i],ru[i],pr[i]] else None for i in range(len(closes))]

def adx_from_closes(closes, period=14):
    """只用收盘价估算ADX（简化Wilder）"""
    n=len(closes)
    gains=[max(closes[i]-closes[i-1],0.0) for i in range(1,n)]
    losses=[abs(min(closes[i]-closes[i-1],0.0)) for i in range(1,n)]
    if len(gains)<period*2: return [None]*n, [None]*n, [None]*n
    avg_g=sum(gains[:period])/period; avg_l=sum(losses[:period])/period
    for i in range(period,len(gains)):
        avg_g=(avg_g*(period-1)+gains[i])/period; avg_l=(avg_l*(period-1)+losses[i])/period
    di_plus=avg_g/(avg_g+avg_l+1e-10)*100 if (avg_g+avg_l)>0 else 0
    di_minus=avg_l/(avg_g+avg_l+1e-10)*100 if (avg_g+avg_l)>0 else 0
    dx=abs(di_plus-di_minus)/(di_plus+di_minus+1e-10)*100 if (di_plus+di_minus)>0 else 0
    adx_val=dx  # 简化：用即时DI+/DI-估算ADX强度
    return round(adx_val,2), round(di_plus,2), round(di_minus,2)

def sig_crsi(v):
    if v is None: return "—"
    return "🔴极度超买⚠️" if v>=85 else "🟠超买⚠️" if v>=70 else "🟢偏强" if v>=55 else "🟡中性" if v>=45 else "🟡偏弱" if v>=30 else "🟠低估" if v>=15 else "🔴极度低估🟢"

def sig_adx(v):
    if v is None: return "⚪数据不足"
    return "⚪震荡" if v<20 else "🟡弱趋势" if v<25 else "🟢中等趋势" if v<40 else "🟠强趋势" if v<60 else "🔴极强趋势"

def f(v,d="—"): return f"{v:,.2f}" if v is not None else d

results = {}

# FRED 真实指数
for code, name in [("SP500","标普500"),("DJIA","道琼斯"),("NASDAQCOM","纳斯达克综合")]:
    d = fred.get(code,[])
    if not d: continue
    c_list=[v for _,v in d]; dt_list=[k for k,_ in d]
    d_crsi=crsi(c_list)
    adv,dp,dm=adx_from_closes(c_list,14)
    results[name]={
        "close":round(c_list[-1],2),"date":dt_list[-1],
        "adx":adv,"di_plus":dp,"di_minus":dm,
        "crsi":(lambda x: round(x,2) if x is not None else None)(d_crsi[-1]) if d_crsi else None,
        "sig_crsi":sig_crsi(d_crsi[-1] if d_crsi else None),
        "sig_adx":sig_adx(adv),
        "src":"FRED🏛️",
    }

# A股
for name,info in a_sh.items():
    c_list=info["c"]; dt_list=info["dates"]
    if not c_list: continue
    d_crsi=crsi(c_list)
    adv,dp,dm=adx_from_closes(c_list,14)
    results[name]={
        "close":round(c_list[-1],2),"date":dt_list[-1],
        "adx":adv,"di_plus":dp,"di_minus":dm,
        "crsi":(lambda x: round(x,2) if x is not None else None)(d_crsi[-1]) if d_crsi else None,
        "sig_crsi":sig_crsi(d_crsi[-1] if d_crsi else None),
        "sig_adx":sig_adx(adv),
        "src":"AkShare",
    }

# ETF
for sym,name in [("SPY","SPY(标普)"),("QQQ","QQQ(纳指)"),("DIA","DIA(道琼斯)")]:
    info=etf.get(sym,{})
    c_list=info.get("c",[]); dt_list=info.get("dates",[])
    if not c_list: continue
    d_crsi=crsi(c_list)
    adv,dp,dm=adx_from_closes(c_list,14)
    results[name]={
        "close":round(c_list[-1],2),"date":dt_list[-1],
        "adx":adv,"di_plus":dp,"di_minus":dm,
        "crsi":(lambda x: round(x,2) if x is not None else None)(d_crsi[-1]) if d_crsi else None,
        "sig_crsi":sig_crsi(d_crsi[-1] if d_crsi else None),
        "sig_adx":sig_adx(adv),
        "src":"TwelveData ETF",
    }

print("=== 指标计算结果 ===")
for name,m in results.items():
    print(f"  {name}: close={m['close']} ADX={m['adx']} DI+={m['di_plus']} DI-={m['di_minus']} CRSI={m['crsi']} {m['sig_crsi']} {m['sig_adx']}")

gen = datetime.now().strftime("%Y年%m月%d日")
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全球大盘日报 {gen}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0d1117;color:#e6edf3;padding:20px}}
.container{{max-width:1100px;margin:0 auto}}
h1{{font-size:1.6em;color:#58a6ff;border-bottom:2px solid #1f6feb;padding-bottom:10px;margin-bottom:18px}}
h2{{font-size:1.05em;color:#79c0ff;margin:18px 0 10px;border-left:4px solid #388bfd;padding-left:10px}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:0.87em}}
th{{background:#161b22;color:#58a6ff;padding:6px 9px;text-align:left;border:1px solid #21262d;font-weight:600;white-space:nowrap}}
td{{padding:6px 9px;border:1px solid #1e2530}}
tr:nth-child(even){{background:#161b22}}
.mono{{font-family:"SF Mono",Monaco,monospace;color:#7ee787;font-size:0.87em}}
.tag{{display:inline-block;font-size:0.72em;padding:1px 7px;border-radius:10px}}
.t-red{{background:#f8514928;color:#f85149}}.t-org{{background:#d2992228;color:#d29922}}
.t-green{{background:#3fb95028;color:#3fb950}}.t-blue{{background:#58a6ff28;color:#58a6ff}}
.t-yellow{{background:#d2992228;color:#d29922}}.t-gray{{background:#30363d28;color:#8b949e}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minwidth:200px,1fr));gap:11px;margin:10px 0}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:11px 13px}}
.card-title{{font-weight:700;font-size:0.88em;margin-bottom:5px}}
.cval{{font-size:1.4em;font-weight:700;color:#e6edf3;margin:3px 0}}
.csub{{font-size:0.76em;color:#8b949e;margin-top:4px;line-height:1.7}}
.alert{{padding:9px 12px;border-radius:6px;margin:7px 0;font-size:0.88em;line-height:1.9}}
.ag{{border-left:3px solid #3fb950;background:#0d2d1a1a}}
.ao{{border-left:3px solid #d29922;background:#2d200d1a}}
.ar{{border-left:3px solid #f85149;background:#2d0d0d1a}}
.ab{{border-left:3px solid #58a6ff;background:#0d1a2d1a}}
.warn{{color:#d29922;font-size:0.82em;padding:7px 10px;border:1px dashed #d2992244;border-radius:4px;margin:8px 0}}
.footer{{margin-top:36px;padding-top:12px;border-top:1px solid #21262d;color:#484f58;font-size:0.78em;line-height:2}}
.badge{{background:#3fb95028;color:#3fb950;padding:1px 6px;border-radius:8px;font-size:0.7em;margin-left:4px}}
</style>
</head>
<body>
<div class="container">
<h1>📊 全球大盘日报</h1>
<p style="color:#8b949e;font-size:0.88em">
  生成: {gen} 04:09 &nbsp;|&nbsp;
  <span style="color:#3fb950">✅ FRED真实指数 &nbsp;|&nbsp; ✅ AkShare A股/港股 &nbsp;|&nbsp; ✅ Twelve Data ETF</span>
</p>

<h2>一、核心数据总览（2026-04-22 收盘）</h2>
<table>
<tr><th>市场</th><th>标的</th><th>收盘</th><th>ADX</th><th>DI+</th><th>DI-</th><th>趋势</th><th>日线CRSI</th><th>信号</th></tr>
"""

def crsi_color(v):
    if v is None: return "#8b949e"
    return "#f85149" if v>=85 else "#d29922" if v>=70 else "#3fb950" if v>=45 else "#8b949e"

def adx_color(v):
    if v is None: return "#8b949e"
    return "#f85149" if v>=60 else "#d29922" if v>=40 else "#3fb950" if v>=25 else "#d29922" if v>=20 else "#8b949e"

# 美股真实指数
for name in ["标普500","道琼斯","纳斯达克综合"]:
    m=results.get(name,{})
    if not m: continue
    flag="🏛️" if m.get("src")=="FRED🏛️" else ""
    html+=f"""<tr>
<td>🇺🇸</td><td><b>{name}</b><span class="badge">{flag}</span></td>
<td class="mono">{f(m.get('close'))}</td>
<td class="mono" style="color:{adx_color(m.get('adx'))}"><b>{f(m.get('adx'))}</b></td>
<td class="mono">{f(m.get('di_plus'))}</td>
<td class="mono">{f(m.get('di_minus'))}</td>
<td class="t-blue">{m.get('sig_adx','—')}</td>
<td class="mono" style="color:{crsi_color(m.get('crsi'))}"><b>{f(m.get('crsi'))}</b></td>
<td><span class="tag t-red">{m.get('sig_crsi','—')}</span></td>
</tr>"""

# A股
for name in ["上证综指","深证成指","创业板指","恒生指数"]:
    m=results.get(name,{})
    if not m: continue
    flag="✅" if "AkShare" in m.get("src","") else ""
    cls="🇨🇳" if "创业" in name or "上证" in name or "深证" in name else "🇭🇰"
    html+=f"""<tr>
<td>{cls}</td><td><b>{name}</b><span class="badge">{flag}</span></td>
<td class="mono">{f(m.get('close'))}</td>
<td class="mono" style="color:{adx_color(m.get('adx'))}"><b>{f(m.get('adx'))}</b></td>
<td class="mono">{f(m.get('di_plus'))}</td>
<td class="mono">{f(m.get('di_minus'))}</td>
<td class="t-blue">{m.get('sig_adx','—')}</td>
<td class="mono" style="color:{crsi_color(m.get('crsi'))}"><b>{f(m.get('crsi'))}</b></td>
<td><span class="tag t-red">{m.get('sig_crsi','—')}</span></td>
</tr>"""

# ETF
for name in ["SPY(标普)","QQQ(纳指)","DIA(道琼斯)"]:
    m=results.get(name,{})
    if not m: continue
    html+=f"""<tr>
<td>🇺🇸 ETF</td><td><b>{name}</b></td>
<td class="mono">{f(m.get('close'))}</td>
<td class="mono" style="color:{adx_color(m.get('adx'))}"><b>{f(m.get('adx'))}</b></td>
<td class="mono">{f(m.get('di_plus'))}</td>
<td class="mono">{f(m.get('di_minus'))}</td>
<td class="t-blue">{m.get('sig_adx','—')}</td>
<td class="mono" style="color:{crsi_color(m.get('crsi'))}"><b>{f(m.get('crsi'))}</b></td>
<td><span class="tag t-red">{m.get('sig_crsi','—')}</span></td>
</tr>"""

html += """</table>

<h2>二、综合技术判断</h2>
<div class="alert ar">
<b>🇺🇸 美股（真实指数 + ETF）</b><br>
"""
# 找超买/超卖信号
us_overbought = [n for n,m in results.items() if "SPY" in n or "QQQ" in n or "DIA" in n or n in ["标普500","道琼斯","纳斯达克综合"] and m.get("crsi",0) and m.get("crsi",0)>=70]
us_oversold = [n for n,m in results.items() if n in ["标普500","道琼斯","纳斯达克综合"] and m.get("crsi",0) and m.get("crsi",0)<=30]
cn_overbought = [n for n,m in results.items() if n in ["上证综指","深证成指","创业板指"] and m.get("crsi",0) and m.get("crsi",0)>=70]

if us_overbought:
    html+="🟠 超买信号: "+"，".join(us_overbought)+" → ⚠️ 谨慎追高\n"
if us_oversold:
    html+="🟢 超卖信号: "+"，".join(us_oversold)+" → 关注买入机会\n"
if cn_overbought:
    html+="🇨🇳 A股超买: "+"，".join(cn_overbought)+" → 注意高位风险\n"
if not us_overbought and not us_oversold and not cn_overbought:
    html+="各指数CRSI在正常区间，无极端信号。\n"

html+="</div>\n"
html+="<div class=\"alert ao\"><b>🇨🇳 A股技术面</b><br>"
for name in ["上证综指","深证成指","创业板指"]:
    m=results.get(name,{})
    if m:
        html+=f"{name}: ADX={m.get('adx')} {m.get('sig_adx')}，CRSI={m.get('crsi')} {m.get('sig_crsi')}<br>"
html+="</div>\n"

html+=f"""
<div class="alert ag">
<b>😱 VIX恐慌指数</b>（VIXY截至2026-04-17: $27.93）<br>
VIXY 处于正常区间(20~30)，无极端恐慌，无需过度担忧。
</div>

<h2>三、技术指标说明</h2>
<p style="font-size:0.86em;color:#8b949e;line-height:2">
<b>ADX</b>：&lt;20=⚪震荡，20~25=🟡弱趋势，25~40=🟢中等，&gt;40=🟠强趋势<br>
<b>DI+/DI-</b>：DI+&gt;DI-=↑上升 | DI-&gt;DI+=↓下降<br>
<b>CRSI日线</b>（Connors RSI）：&gt;70=🟠超买⚠️ | &lt;30=🟢超卖 | &gt;85=🔴极度超买⚠️⚠️<br>
<b>数据</b>：FRED🏛️（真实指数）| AkShare（A股）| Twelve Data ETF
</p>

<div class="footer">
<p>⚠️ <b>免责声明</b>：本报告仅基于公开技术数据计算，不构成投资建议。请以实际行情为准。</p>
<p>📌 数据说明：FRED约1交易日延迟；A股/港股为实时数据；ETF为Twelve Data日线数据。</p>
<p>🕐 {gen} 04:09 UTC | 数据: 2026-04-22</p>
</div>

</div>
</body>
</html>"""

with open("/workspace/market_report/daily_report.html","w") as fp:
    fp.write(html)
print(f"✅ 日报已生成: {len(html)} 字节")
