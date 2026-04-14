#!/usr/bin/env python3
"""Build AA chart HTML"""
import akshare as ak, json

df = ak.stock_us_daily(symbol='AA').tail(60).copy()
df['date'] = df['date'].astype(str)
for col in ['open','high','low','close']:
    df[col] = df[col].astype(float)

candles = [
    {'time': r['date'],
     'open': round(float(r['open']), 2),
     'high': round(float(r['high']), 2),
     'low': round(float(r['low']), 2),
     'close': round(float(r['close']), 2)}
    for _, r in df.iterrows()
]
closes = [c['close'] for c in candles]
c0 = closes[-1]

def sma(d, p):
    r = []
    for i in range(len(d)):
        if i < p - 1:
            r.append(None)
        else:
            r.append(round(sum(d[i-p+1:i+1]) / p, 2))
    return r

m13 = sma(closes, 13)
m20 = sma(closes, 20)
m50 = sma(closes, 50)

d_str = json.dumps(candles)
c_str = json.dumps(closes)

html = f'''<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8"><title>Alcoa AA K线图</title>
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3}}
.hdr{{background:#161b22;border-bottom:1px solid #30363d;padding:14px 24px}}
.hdr h1{{font-size:16px;color:#58a6ff}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:12px 24px;background:#161b22;border-bottom:1px solid #30363d}}
.card{{background:#21262d;border:1px solid #30363d;border-radius:8px;padding:10px 14px}}
.card .l{{font-size:10px;color:#8b949e;text-transform:uppercase}}
.card .v{{font-size:17px;font-weight:700;margin-top:3px}}
.wrap{{padding:14px 24px}}
canvas{{width:100%;height:480px;background:#161b22;border:1px solid #30363d;border-radius:8px;display:block}}
.info{{font-size:12px;color:#8b949e;margin-bottom:8px}}
</style></head>
<body>
<div class=hdr><h1>Alcoa (AA) K线技术分析图</h1></div>
<div class=cards>
  <div class=card><div class=l>最新价</div><div class=v style="color:#3fb950">${c0:.2f}</div></div>
  <div class=card><div class=l>M13均线</div><div class=v style="color:#58a6ff">${m13[-1]:.2f}</div></div>
  <div class=card><div class=l>M20均线</div><div class=v style="color:#f0883e">${m20[-1]:.2f}</div></div>
  <div class=card><div class=l>M50均线</div><div class=v style="color:#ff7eb3">${m50[-1]:.2f}</div></div>
</div>
<div class=wrap>
  <div class=info>阳线绿/阴线红 · 蓝=MA13 橙=MA20 粉=MA50 | 数据来源: AkShare</div>
  <canvas id="main"></canvas>
</div>
<script>
const D={d_str},C={c_str};
function smaArr(d,p){{const r=[];for(let i=0;i<d.length;i++)r.push(i<p-1?null:+(d.slice(i-p+1,i+1).reduce((s,v)=>s+v,0)/p).toFixed(2));return r;}}
const m13=smaArr(C,13),m20=smaArr(C,20),m50=smaArr(C,50);
const ch=LightweightCharts.createChart(document.getElementById('main'),{{
  width:document.getElementById('main').clientWidth,height:480,
  layout:{{background:{{color:'#161b22'}},textColor:'#8b949e',fontSize:11}},
  grid:{{vertLines:{{color:'#21262d'}},horzLines:{{color:'#21262d'}}}},
  rightPriceScale:{{borderColor:'#30363d'}},
  timeScale:{{borderColor:'#30363d',timeVisible:true,
    tickMarkFormatter:t=>new Date(t*1000).toLocaleDateString('zh',{{month:'short',day:'numeric'}})}},
  crosshair:{{mode:LightweightCharts.CrosshairMode.Normal,
    vertLine:{{color:'#30363d',style:LightweightCharts.LineStyle.Dashed}},
    horzLine:{{color:'#30363d',style:LightweightCharts.LineStyle.Dashed}}}},
}});
const cs=ch.addCandlestickSeries({{upColor:'#3fb950',downColor:'#f85149',borderVisible:false,wickUpColor:'#3fb950',wickDownColor:'#f85149'}});
const s13=ch.addLineSeries({{color:'#58a6ff',lineWidth:1.5,pointRadius:0}});
const s20=ch.addLineSeries({{color:'#f0883e',lineWidth:1.5,pointRadius:0}});
const s50=ch.addLineSeries({{color:'#ff7eb3',lineWidth:1.5,pointRadius:0}});
cs.setData(D);
s13.setData(D.map((d,i)=>({{time:d.time,value:m13[i]}})));
s20.setData(D.map((d,i)=>({{time:d.time,value:m20[i]}})));
s50.setData(D.map((d,i)=>({{time:d.time,value:m50[i]}})));
ch.timeScale().fitContent();
window.addEventListener('resize',()=>ch.resize(document.getElementById('main').clientWidth,480));
</script></body></html>'''

with open('/workspace/aa_chart/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('OK, candles:', len(candles))
