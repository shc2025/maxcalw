#!/usr/bin/env python3
import subprocess, json
APIKEY = 'dd4f227a11f34265936086a73b46b80c'

def get(url):
    try:
        p = subprocess.run(['curl','-s','--max-time','15',url],capture_output=True,text=True,timeout=20)
        return json.loads(p.stdout)
    except:
        return None

def wilder(prices, period):
    n = len(prices)
    result = [None]*n
    gains, losses = [], []
    for i in range(1, n):
        d = (prices[i]-prices[i-1]) if (prices[i] is not None and prices[i-1] is not None) else 0
        gains.append(max(d,0)); losses.append(abs(min(d,0)))
    if period<1 or len(gains)<period: return result
    ag=sum(gains[:period])/period; al=sum(losses[:period])/period
    result[period] = 100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    for i in range(period, len(gains)):
        ag=(ag*(period-1)+gains[i])/period; al=(al*(period-1)+losses[i])/period
        result[i+1] = 100.0 if al==0 else 100.0-(100.0/(1.0+ag/(al+1e-10)))
    return result

def ema_rsi(prices, period):
    n = len(prices)
    if n<period+1: return [None]*n
    k = 2.0/(period+1)
    prev = sum(prices[:period])/period
    result = [None]*(period-1)+[prev]
    for i in range(period, n):
        chg = prices[i]-prices[i-1]
        rsi_v = 50.0 if prev==0 else 100.0-(100.0/(1.0+chg/prev))
        rsi_v = max(0.0, min(100.0, rsi_v))
        ema_val = rsi_v*k + prev*(1-k)
        result.append(ema_val); prev = ema_val
    return result

def streak(closes):
    if len(closes)<2: return [0]*len(closes)
    s=[0]
    for i in range(1,len(closes)):
        if closes[i]>closes[i-1]: s.append(1 if s[-1]<=0 else s[-1]+1)
        elif closes[i]<closes[i-1]: s.append(-1 if s[-1]>=0 else s[-1]-1)
        else: s.append(0)
    return s

def roc(prices, period):
    out=[]
    for i in range(len(prices)):
        if i<period or prices[i-period] is None or prices[i] is None: out.append(None)
        else:
            prev=prices[i-period]
            out.append((prices[i]-prev)/prev*100.0 if prev!=0 else 0.0)
    return out

def rma(vals, period):
    if not vals or period<=0: return [None]*len(vals) if vals else []
    alpha=1.0/period; result=[None]*len(vals)
    i0=next((i for i,v in enumerate(vals) if v is not None),None)
    if i0 is None: return result
    result[i0]=vals[i0]
    for i in range(i0+1,len(vals)):
        result[i]=vals[i]*alpha+result[i-1]*(1-alpha) if vals[i] is not None else result[i-1]
    return result

def calc_ha(opens,highs,lows,closes):
    n=len(opens); ha_c=[(opens[i]+highs[i]+lows[i]+closes[i])/4.0 for i in range(n)]
    ha_o=[None]*n; ha_o[0]=(opens[0]+closes[0])/2.0
    for i in range(1,n): ha_o[i]=(ha_o[i-1]+ha_c[i-1])/2.0
    ha_h=[max(highs[i],ha_o[i],ha_c[i]) for i in range(n)]
    ha_l=[min(lows[i], ha_o[i], ha_c[i]) for i in range(n)]
    return ha_o,ha_h,ha_l,ha_c

def ha_rsi(ha_close):
    r=wilder(ha_close,24); return rma(r,3)

def crsi_calc(closes, price_func, lrsi, lrup, lrroc):
    rp=price_func(closes,lrsi)
    st=streak(closes)
    ru=wilder(st,lrup)
    rc=wilder(roc(closes,lrroc),lrup)
    crsi=[]
    for i in range(len(closes)):
        a,b,c=rp[i],ru[i],rc[i]
        if None not in [a,b,c]: crsi.append(round((a+b+c)/3.0,2))
        else: crsi.append(None)
    return crsi,rp,ru,rc

for SYM,NAME in [('TSLA','TESLA'),('QQQ','QQQ')]:
    url=('https://api.twelvedata.com/time_series?symbol=%s&interval=1day&outputsize=200&apikey=%s&end_date=2026-04-18&order=asc')%(SYM,APIKEY)
    d=get(url)
    if not d or not d.get('values'): print(NAME+' data failed'); continue
    vals=d['values']
    dates=[v['datetime'] for v in vals]
    closes=[float(v['close'])for v in vals]
    try:
        idx=dates.index('2026-04-17')
    except ValueError: print(NAME+' no 2026-04-17'); continue
    c=closes[idx]
    ha_o,ha_h,ha_l,ha_c=calc_ha(closes[:idx+1],[float(v['high'])for v in vals[:idx+1]],[float(v['low'])for v in vals[:idx+1]],closes[:idx+1])
    hrs=ha_rsi(ha_c)
    bull=ha_c[-1]>ha_o[-1]
    print(NAME+' O=%.2f H=%.2f L=%.2f C=%.2f HA_%s HA_RSI=%.2f'%(float(vals[idx]['open']),float(vals[idx]['high']),float(vals[idx]['low']),c,'阳' if bull else '阴',round(hrs[-1],4) if hrs[-1] else 0))
    for label,pf,lrsi in [('EMA(3)',ema_rsi,3),('Wilder(3)',wilder,3)]:
        cr,rp,ru,rc=crsi_calc(closes[:idx+1],pf,lrsi,2,100)
        print('  '+label+' CRSI=%.2f price=%.2f updown=%.2f roc=%.2f'%(cr[-1] or 0,rp[-1] or 0,ru[-1] or 0,rc[-1] or 0))
    print('  lenRSI scan (Wilder):')
    for lrsi in [3,5,8,12,20,24]:
        cr,rp2,_,_=crsi_calc(closes[:idx+1],wilder,lrsi,2,100)
        print('    lenRSI=%2d CRSI=%.2f price=%.2f'%(lrsi,cr[-1] or 0,rp2[-1] or 0))
    print('')
