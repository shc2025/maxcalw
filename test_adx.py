#!/usr/bin/env python3
import subprocess, json

APIKEY = 'dd4f227a11f34265936086a73b46b80c'

tests = [
    ('SPY',     '标普500 ETF (S&P 500)'),
    ('QQQ',     '纳指100 ETF (NASDAQ)'),
    ('DIA',     '道琼斯 ETF (Dow Jones)'),
    ('SPX',     '标普500指数'),
    ('DJI',     '道琼斯指数'),
    ('SHCOMP',  '上证指数'),
    ('000001.SS','上证指数(SS格式)'),
    ('DAX',     '德国DAX指数'),
    ('ASHR',    '中国A50 ETF'),
    ('FXI',     'FXI 中国大盘ETF'),
    ('INI',     'INDIAC50 印度指数'),
]

print("Twelve Data ADX 接口测试")
print("=" * 55)

for sym, name in tests:
    url = ('https://api.twelvedata.com/adx?symbol=%s&interval=1day&outputsize=3&apikey=%s') % (sym, APIKEY)
    p = subprocess.run(['curl', '-s', '--max-time', '12', url], capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
        vals = d.get('values', [])
        meta = d.get('meta', {})
        if vals:
            latest = vals[-1]
            adx = latest.get('adx', 'N/A')
            period = meta.get('indicator', {}).get('time_period', '?')
            status = meta.get('indicator', {}).get('name', 'ADX')
            print('✅ %-12s %-30s ADX=%.2f 周期=%s  最新=%s' % (sym, name, float(adx), period, latest['datetime']))
        else:
            msg = d.get('message', d.get('status', ''))
            print('❌ %-12s %-30s %s' % (sym, name, str(msg)[:50]))
    except Exception as e:
        print('❌ %-12s ERROR: %s' % (sym, str(e)[:40]))
