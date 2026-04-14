#!/usr/bin/env python3
"""AA技术分析"""
import akshare as ak, json

df = ak.stock_us_daily(symbol='AA').tail(60).copy()
df['date'] = df['date'].astype(str)
for col in ['open','high','low','close']:
    df[col] = df[col].astype(float)

closes = df['close'].tolist()
dates  = df['date'].tolist()
c0     = closes[-1]

def sma(d, p):
    r = []
    for i in range(len(d)):
        r.append(sum(d[i-p+1:i+1])/p if i>=p-1 else None)
    return r

m13=sma(closes,13); m20=sma(closes,20); m50=sma(closes,50)
lo52=min(closes); hi52=max(closes)
ret7=(c0/closes[-8]-1)*100 if len(closes)>=8 else 0
ret30=(c0/closes[-31]-1)*100 if len(closes)>=31 else 0
ret60=(c0/closes[0]-1)*100

peak=c0; maxdd=0
for c in closes:
    if c>peak: peak=c
    dd=(peak-c)/peak*100
    if dd>maxdd: maxdd=dd

monthly={}
for _,r in df.iterrows():
    ym=r['date'][:7]
    if ym not in monthly: monthly[ym]={'o':r['open'],'h':r['high'],'l':r['low'],'c':r['close']}

def rsi(d, n=14):
    gains=[]; losses=[]
    for i in range(1,len(d)):
        diff=d[i]-d[i-1]
        gains.append(max(diff,0)); losses.append(abs(min(diff,0)))
    avgG=sum(gains[-n:])/n; avgL=sum(losses[-n:])/n
    return 100-(100/(1+avgG/avgL)) if avgL else 100

rsi14=rsi(closes)
hi52s=max(closes); lo52s=min(closes)
arr='多头' if c0>m13[-1]>m20[-1]>m50[-1] else '空头' if c0<m13[-1]<m20[-1]<m50[-1] else '混乱'

out = []
out.append('=== AA 技术分析 ===')
out.append('最新价: $%.2f (%s)' % (c0, dates[-1]))
out.append('7日: %+.2f%%  30日: %+.2f%%  60日: %+.2f%%' % (ret7, ret30, ret60))
out.append('M13: $%.2f  M20: $%.2f  M50: $%.2f' % (m13[-1], m20[-1], m50[-1]))
out.append('均线: %s' % arr)
out.append('52W高: $%.2f  52W低: $%.2f  距高点: %+.2f%%' % (hi52s, lo52s, (c0/hi52s-1)*100))
out.append('RSI(14): %.1f' % rsi14)
out.append('最大回撤: %.2f%%' % maxdd)
out.append('')
out.append('月K线:')
for ym in sorted(monthly.keys()):
    v=monthly[ym]; idx=list(monthly.keys()).index(ym)
    prev=monthly[list(monthly.keys())[idx-1]]['c'] if idx>0 else v['o']
    ret=(v['c']/prev-1)*100
    out.append('  %s: O$%.2f H$%.2f L$%.2f C$%.2f  %+.2f%%' % (ym, v['o'], v['h'], v['l'], v['c'], ret))

candles=[{'time':r['date'],'open':round(float(r['open']),2),'high':round(float(r['high']),2),'low':round(float(r['low']),2),'close':round(float(r['close']),2)} for _,r in df.iterrows()]
with open('/workspace/aa_chart_data.json','w') as f:
    json.dump(candles, f)

for line in out:
    print(line)
print('\nK线%d根已保存到 /workspace/aa_chart_data.json' % len(candles))
