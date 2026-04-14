import json, math

with open('/workspace/aa_chart_data.json') as f:
    candles = json.load(f)

closes = [c['close'] for c in candles]
dates  = [c['date'] for c in candles]

def sma(d, p):
    r = []
    for i in range(len(d)):
        r.append(round(sum(d[i-p+1:i+1])/p,2) if i>=p-1 else None)
    return r

def rsi(d, n=14):
    gains=[]; losses=[]
    for i in range(1,len(d)):
        diff=d[i]-d[i-1]
        gains.append(max(diff,0)); losses.append(abs(min(diff,0)))
    avgG=sum(gains[-n:])/n; avgL=sum(losses[-n:])/n
    return round(100-(100/(1+avgG/avgL)) if avgL else 100,1)

m13=sma(closes,13); m20=sma(closes,20); m50=sma(closes,50)
c0=closes[-1]; rsi14=rsi(closes)

html = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8"><title>Alcoa AA 技术分析</title>
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3}
.header{background:#161b22;border-bottom:1px solid #30363d;padding:16px 28px}
.header h1{font-size:17px;color:#58a6ff}
.header .sub{font-size:12px;color:#8b949e;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;padding:16px 28px;background:#161b22;border-bottom:1px solid #30363d}
.card{background:#21262d;border:1px solid #30363d;border-radius:8px;padding:12px 14px}
.card .l{font-size:10px;color:#8b949e;text-transform:uppercase;letter-spacing:.05em}
.card .v{font-size:18px;font-weight:700;margin-top:4px}
.cg{color:#3fb950}.cr{color:#f85149}.cb{color:#58a6ff}.co{color:#f0883e}
.wrap{padding:16px 28px}
canvas{width:100%;height:500px;background:#161b22;border:1px solid #30363d;border-radius:8px;display:block;margin-bottom:12px}
.legends{display:flex;gap:18px;font-size:12px;color:#8b949e;flex-wrap:wrap}
.legends span{display:flex;align-items:center;gap:5px}
.line{width:18px;height:2px;display:inline-block}
</style></head>
<body>
<div class=header>
  <h1>Alcoa (AA) · K线技术分析图</h1>
  <div class=sub>数据来源: AkShare | 图表: lightweight-charts | 更新: 2026-04-13</div>
</div>
<div class=grid>
  <div class=card><div class=l>最新价</div><div class="v cg">$%.2f</div></div>
  <div class=card><div class=l>30日涨跌</div><div class="v %s">%+.2f%%</div></div>
  <div class=card><div class=l>RSI(14)</div><div class="v %s">%.1f</div></div>
  <div class=card><div class=l>M13均线</div><div class="v cb">$%.2f</div></div>
  <div class=card><div class=l>M20均线</div><div class="v cb">$%.2f</div></div>
  <div class=card><div class=l>M50均线</div><div class="v cb">$%.2f</div></div>
</div>
<div class=wrap>
  <div class=legends>
    <span><span class=line style="background:#3fb950"></span>阳线</span>
    <span><span class=line style="background:#f85149"></span>阴线</span>
    <span><span class=line style="background:#58a6ff"></span>MA13</span>
    <span><span class=line style="background:#f0883e"></span>MA20</span>
    <span><span class=line style="background:#ff7eb3"></span>MA50</span>
  </div>
  <canvas id="main"></canvas>
</div>
<script>
const DATA=%DATA%;
const CLOSES=%CLOSES%;

function smaArr(d,p){
  const r=[];
  for(let i=0;i<d.length;i++) r.push(i<p-1?null:+(d.slice(i-p+1,i+1).reduce((s,v)=>s+v,0)/p).toFixed(2));
  return r;
}

const m13=smaArr(CLOSES,13), m20=smaArr(CLOSES,20), m50=smaArr(CLOSES,50);

const chart=LightweightCharts.createChart(document.getElementById('main'),{
  width:document.getElementById('main').clientWidth,height:500,
  layout:{background:{color:'#161b22'},textColor:'#8b949e',fontSize:11},
  grid:{vertLines:{color:'#21262d'},horzLines:{color:'#21262d'}},
  rightPriceScale:{borderColor:'#30363d'},
  timeScale:{borderColor:'#30363d',timeVisible:true,secondsVisible:false,
    tickMarkFormatter:t=>new Date(t*1000).toLocaleDateString('zh',{month:'short',day:'numeric'})},
  crosshair:{mode:LightweightCharts.CrosshairMode.Normal,
    vertLine:{color:'#30363d',style:LightweightCharts.LineStyle.Dashed},
    horzLine:{color:'#30363d',style:LightweightCharts.LineStyle.Dashed}},
});

const cs=chart.addCandlestickSeries({upColor:'#3fb950',downColor:'#f85149',borderVisible:false,wickUpColor:'#3fb950',wickDownColor:'#f85149'});
const s13=chart.addLineSeries({color:'#58a6ff',lineWidth:1.5,pointRadius:0,lastValueVisible:false});
const s20=chart.addLineSeries({color:'#f0883e',lineWidth:1.5,pointRadius:0,lastValueVisible:false});
const s50=chart.addLineSeries({color:'#ff7eb3',lineWidth:1.5,pointRadius:0,lastValueVisible:false});

cs.setData(DATA);
s13.setData(DATA.map((d,i)=>({time:d.time,value:m13[i]})));
s20.setData(DATA.map((d,i)=>({time:d.time,value:m20[i]})));
s50.setData(DATA.map((d,i)=>({time:d.time,value:m50[i]})));
chart.timeScale().fitContent();

const tip=document.createElement('div');
tip.style='position:absolute;display:none;background:#1c2128;border:1px solid #30363d;border-radius:6px;padding:8px 12px;font-size:12px;color:#c9d1d9;pointer-events:none;z-index:999;line-height:1.6';
document.getElementById('main').style.position='relative';
document.getElementById('main').appendChild(tip);

chart.subscribeCrosshairMove(p=>{
  if(!p.time){tip.style.display='none';return;}
  const idx=DATA.findIndex(d=>d.time===p.time);
  if(idx<0){tip.style.display='none';return;}
  const d=DATA[idx];
  const m13v=m13[idx],m20v=m20[idx],m50v=m50[idx];
  const rsi=rsi14||0;
  tip.style.display='block';
  tip.style.left=Math.min((p.point&&p.point.x||0)+12,window.innerWidth-220)+'px';
  tip.style.top=(p.point&&p.point.y||0)+'px';
  const arrow=d.close>=d.open?'▲':'▼';
  const col=d.close>=d.open?'#3fb950':'#f85149';
  tip.innerHTML='<b style="color:#e6edf3">'+new Date(p.time*1000).toLocaleDateString('zh',{month:'short',day:'numeric'})+'</b><br>'
    +arrow+' <b style="color:'+col+'">$'+d.close.toFixed(2)+'</b> (O:$'+d.open.toFixed(2)+' H:$'+d.high.toFixed(2)+' L:$'+d.low.toFixed(2)+')<br>'
    +(m13v?'MA13:<b style="color:#58a6ff">$'+m13v.toFixed(2)+'</b> ':'')+(m20v?'MA20:<b style="color:#f0883e">$'+m20v.toFixed(2)+'</b> ':'')+(m50v?'MA50:<b style="color:#ff7eb3">$'+m50v.toFixed(2)+'</b>':'');
});
window.addEventListener('resize',()=>chart.resize(document.getElementById('main').clientWidth,500));
</script></body></html>""" % (c0,
    'cg' if (c0/closes[-31]-1)>=0 else 'cr' if len(closes)>=31 else 'cg',
    (c0/closes[-31]-1)*100 if len(closes)>=31 else 0,
    'cr' if rsi14>70 else 'cg', rsi14,
    m13[-1],m20[-1],m50[-1])

html=html.replace('%DATA%',json.dumps(candles)).replace('%CLOSES%',json.dumps(closes)).replace('rsi14||0','%.1f'%rsi14)

with open('/workspace/aa_chart/index.html','w',encoding='utf-8') as f:
    f.write(html)
print('OK')
