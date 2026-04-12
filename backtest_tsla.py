#!/usr/bin/env python3
"""TSLA M13/M200 策略回测"""
import subprocess, json, math, csv

import sys
APIKEY = sys.argv[1] if len(sys.argv) > 1 else "dd4f227a11f34265936086a73b46b80c"
url = ("https://api.twelvedata.com/time_series"
       "?symbol=TSLA&interval=1day&outputsize=1300"
       f"&apikey={APIKEY}&start_date=2021-04-05&end_date=2026-04-05&order=asc")
proc = subprocess.run(["curl","-s",url], capture_output=True, text=True, timeout=20)
raw  = json.loads(proc.stdout)
quotes = raw["values"]
print(f"[Data] {len(quotes)} candles: {quotes[0]['datetime']} → {quotes[-1]['datetime']}")

close  = [float(q["close"]) for q in quotes]
dates  = [q["datetime"] for q in quotes]

def sma(data, period):
    res = []
    for i in range(len(data)):
        res.append(sum(data[i-period+1:i+1])/period if i>=period-1 else None)
    return res

m13  = sma(close, 13)
m200 = sma(close, 200)

INITIAL=10000.0; cash=INITIAL; position=0.0; entry_price=0.0; entry_shares=0
trades=[]; equity=[]
prev_m13=None; m13_was_rising=None

for i in range(len(close)):
    c=close[i]; d=dates[i]; m13v=m13[i]; m200v=m200[i]
    equity.append((d, cash+position*c))
    if m13v is None or m200v is None:
        prev_m13=m13v; continue
    m13_above = m13v>m200v
    is_rising = (m13v>prev_m13) if prev_m13 is not None else False
    turn_up   = (m13_was_rising is False) and is_rising
    turn_down = (m13_was_rising is True)  and (not is_rising)
    if position==0 and m13_above and turn_up:
        shares=int(10000/c)
        if shares>0:
            position=shares; entry_shares=shares; entry_price=c; cash-=shares*c
            trades.append({"date_in":d,"price_in":c,"shares":shares,"m13_in":m13v,"m200_in":m200v})
    elif position>0 and (turn_down or (not m13_above)):
        cash+=position*c
        pnl=cash-entry_price*entry_shares
        trades[-1].update({"date_out":d,"price_out":c,"pnl":pnl,
            "ret_pct":pnl/(entry_price*entry_shares)*100,"equity":cash,
            "exit_reason":"M13拐头向下" if turn_down else "M13<M200"})
        position=0
    m13_was_rising=is_rising; prev_m13=m13v

if position>0:
    lc=close[-1]; ld=dates[-1]; cash+=position*lc
    pnl=cash-entry_price*entry_shares
    trades[-1].update({"date_out":ld,"price_out":lc,"pnl":pnl,
        "ret_pct":pnl/(entry_price*entry_shares)*100,"equity":cash,"exit_reason":"数据截止日平仓"})
    position=0

completed=[t for t in trades if "pnl" in t]
wins=[t for t in completed if t["pnl"]>0]; losses=[t for t in completed if t["pnl"]<=0]
win_rate=len(wins)/len(completed)*100 if completed else 0
total_pnl=sum(t["pnl"] for t in completed); avg_pnl=total_pnl/len(completed)
gross_profit=sum(t["pnl"] for t in wins); gross_loss=abs(sum(t["pnl"] for t in losses))
profit_factor=gross_loss and gross_profit/gross_loss or float('inf')
peak=-float('inf'); max_dd=0.0
for _,eq in equity:
    if eq>peak: peak=eq
    dd=peak-eq
    if dd>max_dd: max_dd=dd
years=5.0
cagr=(math.pow(cash/INITIAL,1/years)-1)*100
returns=[]; prev_eq=INITIAL
for _,eq in equity:
    ret=(eq-prev_eq)/prev_eq; returns.append(ret); prev_eq=eq
avg_ret=sum(returns)/len(returns); std_ret=math.sqrt(sum((r-avg_ret)**2 for r in returns)/len(returns))
sharpe_a=(avg_ret/std_ret)*math.sqrt(252) if std_ret else 0
neg=[r for r in returns if r<0]
std_neg=math.sqrt(sum(r**2 for r in neg)/len(neg)) if neg else 0
sortino_a=(avg_ret/std_neg)*math.sqrt(252) if std_neg else 0
sw=sl=max_sw=max_sl=0
for t in completed:
    if t["pnl"]>0: sw+=1; sl=0; max_sw=max(max_sw,sw)
    else: sl+=1; sw=0; max_sl=max(max_sl,sl)

print(f"""
═══════════════════════════════════════════════════════
   TSLA  M13/M200  趋势策略回测报告
═══════════════════════════════════════════════════════
  回测区间   {quotes[0]['datetime']} → {quotes[-1]['datetime']}
  数据点数   {len(quotes)} 个交易日

  【收益概览】
  初始资金         ${INITIAL:,.2f}
  最终资金         ${cash:,.2f}
  总收益率         {(cash/INITIAL-1)*100:.2f}%
  年化收益率(CAGR)  {cagr:.2f}%
  最大回撤         -${max_dd:,.2f}

  【风险调整指标】
  夏普比率(年化)    {sharpe_a:.3f}
  索提诺比率(年化)  {sortino_a:.3f}
  盈亏比            {profit_factor:.3f}

  【交易统计】
  总交易次数       {len(completed)}
  盈利次数         {len(wins)}
  亏损次数         {len(losses)}
  胜率             {win_rate:.2f}%
  平均每笔收益      ${avg_pnl:,.2f}
  最大连续盈利      {max_sw} 次
  最大连续亏损      {max_sl} 次

  【交易明细】
  {'日期买入':<12} {'买入价':>8} {'数量':>5} {'日期卖出':<12} {'卖出价':>8} {'持仓理由':<16} {'盈亏($)':>10} {'收益率':>8}
  """ + "-"*90)
for t in completed:
    print(f"  {t['date_in']:<12} ${t['price_in']:>7.2f} {t['shares']:>5} "
          f"{t.get('date_out','N/A'):<12} ${t.get('price_out',0):>7.2f} "
          f"{t['exit_reason']:<14} ${t['pnl']:>+9.2f} {t['ret_pct']:>+7.2f}%")

with open("/workspace/backtest_tsla_results.json","w") as f:
    json.dump({"summary":{"initial":INITIAL,"final":cash,"total_return":(cash/INITIAL-1)*100,
               "cagr":cagr,"max_drawdown":max_dd,"sharpe_annual":sharpe_a,
               "sortino_annual":sortino_a,"profit_factor":profit_factor,
               "total_trades":len(completed),"win_rate":win_rate,"avg_pnl":avg_pnl,
               "max_win_streak":max_sw,"max_loss_streak":max_sl},
               "trades":completed,"equity_curve":[(d,eq) for d,eq in equity]}, f, indent=2)
with open("/workspace/equity_tsla_curve.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["date","equity"]); w.writerows(equity)
print("\n[OK] Saved: backtest_tsla_results.json, equity_tsla_curve.csv")
