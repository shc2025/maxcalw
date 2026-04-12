#!/usr/bin/env python3
"""
AAPL M13/M200 Strategy Backtest
- M13 > M200: 看多市场
- M13 向上拐头: 买入 ($10,000 仓位)
- M13 向下拐头: 卖出
- M13 < M200: 平仓
"""

import json, math, sys, subprocess

# ── 1. 获取数据 (via curl) ────────────────────────────────────
url = ("https://api.twelvedata.com/time_series"
       "?symbol=AAPL&interval=1day&outputsize=5000"
       "&apikey=demo&start_date=2021-04-05&end_date=2026-04-05"
       "&order=asc")

proc = subprocess.run(
    ["curl", "-s", url], capture_output=True, text=True, timeout=20
)
raw = json.loads(proc.stdout)

quotes = raw["values"]  # oldest → newest
print(f"[Data] {len(quotes)} candles: {quotes[0]['datetime']} → {quotes[-1]['datetime']}")

# ── 2. 计算 M13 / M200 ──────────────────────────────────────
close  = [float(q["close"]) for q in quotes]
dates  = [q["datetime"] for q in quotes]

def sma(data, period):
    res = []
    for i in range(len(data)):
        if i < period - 1:
            res.append(None)
        else:
            res.append(sum(data[i - period + 1 : i + 1]) / period)
    return res

m13  = sma(close, 13)
m200 = sma(close, 200)

# ── 3. 策略回测 ──────────────────────────────────────────────
INITIAL       = 10_000.0
cash          = INITIAL
position      = 0.0          # 持股数量
entry_price   = 0.0
entry_shares  = 0

trades   = []    # 完整交易（含出场）
equity   = []    # 时间序列

prev_m13       = None
prev_prev_m13  = None
m13_was_rising  = None

for i in range(len(close)):
    c      = close[i]
    d      = dates[i]
    m13v   = m13[i]
    m200v  = m200[i]
    equity_val = cash + position * c
    equity.append((d, equity_val))

    if m13v is None or m200v is None:
        prev_prev_m13 = prev_m13
        prev_m13      = m13v
        continue

    m13_above   = m13v > m200v
    is_rising   = (m13v > prev_m13) if prev_m13 is not None else False
    turn_up     = (m13_was_rising is False) and is_rising
    turn_down   = (m13_was_rising is True)  and (not is_rising)

    # ── 入场 ──
    if position == 0 and m13_above and turn_up:
        shares     = int(10_000 / c)
        if shares > 0:
            position     = shares
            entry_shares = shares
            entry_price  = c
            cash        -= shares * c
            trades.append({
                "date_in": d, "price_in": c, "shares": shares,
                "m13_in": m13v, "m200_in": m200v
            })

    # ── 出场 ──
    elif position > 0 and (turn_down or (not m13_above)):
        cash      += position * c
        pnl        = cash - entry_price * entry_shares
        ret_pct    = pnl / (entry_price * entry_shares) * 100
        trades[-1].update({
            "date_out":   d,
            "price_out":  c,
            "pnl":        pnl,
            "ret_pct":    ret_pct,
            "equity":     cash,
            "exit_reason": "M13拐头向下" if turn_down else "M13<M200"
        })
        position   = 0

    m13_was_rising = is_rising
    prev_prev_m13  = prev_m13
    prev_m13       = m13v

# 最后仍未平仓 → 以最后收盘价平仓
if position > 0:
    last_c     = close[-1]
    last_d     = dates[-1]
    cash      += position * last_c
    pnl        = cash - entry_price * entry_shares
    ret_pct    = pnl / (entry_price * entry_shares) * 100
    trades[-1].update({
        "date_out":   last_d,
        "price_out":  last_c,
        "pnl":        pnl,
        "ret_pct":    ret_pct,
        "equity":     cash,
        "exit_reason": "数据截止日平仓"
    })
    position = 0

# ── 4. 统计指标 ──────────────────────────────────────────────
completed = [t for t in trades if "pnl" in t]
wins      = [t for t in completed if t["pnl"] > 0]
losses    = [t for t in completed if t["pnl"] <= 0]
win_rate  = len(wins) / len(completed) * 100 if completed else 0

total_pnl = sum(t["pnl"] for t in completed)
avg_pnl   = total_pnl / len(completed) if completed else 0

gross_profit = sum(t["pnl"] for t in wins)
gross_loss   = abs(sum(t["pnl"] for t in losses))
profit_factor = gross_loss and gross_profit / gross_loss or float('inf')

# 最大回撤
peak = -float('inf')
max_dd = 0.0
for _, eq in equity:
    if eq > peak: peak = eq
    dd = peak - eq
    if dd > max_dd: max_dd = dd

# 年化收益率
years = (len(completed) and 5.0) or 5.0   # ~5年
cagr  = (math.pow(cash / INITIAL, 1 / years) - 1) * 100

# ── 5. 夏普比率（日频） ──────────────────────────────────────
returns = []
prev_eq = INITIAL
for _, eq in equity:
    ret = (eq - prev_eq) / prev_eq
    returns.append(ret)
    prev_eq = eq

avg_ret  = sum(returns) / len(returns)
std_ret  = math.sqrt(sum((r - avg_ret)**2 for r in returns) / len(returns))
sharpe_d = std_ret and avg_ret / std_ret or 0
sharpe_a = sharpe_d * math.sqrt(252)

# Sortino
neg = [r for r in returns if r < 0]
std_neg  = math.sqrt(sum(r**2 for r in neg) / len(neg)) if neg else 0
sortino  = std_neg and avg_ret / std_neg or 0
sortino_a = sortino * math.sqrt(252)

# 最大连续赢/输
streak_w = streak_l = max_sw = max_sl = 0
for t in completed:
    if t["pnl"] > 0:
        streak_w += 1; streak_l = 0; max_sw = max(max_sw, streak_w)
    else:
        streak_l += 1; streak_w = 0; max_sl = max(max_sl, streak_l)

# ── 6. 打印报告 ──────────────────────────────────────────────
print("""
═══════════════════════════════════════════════════════
   AAPL  M13/M200  趋势策略回测报告
═══════════════════════════════════════════════════════""")
print(f"  回测区间   {quotes[0]['datetime']} → {quotes[-1]['datetime']}")
print(f"  数据点数   {len(quotes)} 个交易日")
print()
print("  【收益概览】")
print(f"  初始资金         ${INITIAL:,.2f}")
print(f"  最终资金         ${cash:,.2f}")
print(f"  总收益率         {(cash/INITIAL-1)*100:.2f}%")
print(f"  年化收益率(CAGR)  {cagr:.2f}%")
print(f"  最大回撤         -${max_dd:,.2f}")
print()
print("  【风险调整指标】")
print(f"  夏普比率(年化)    {sharpe_a:.3f}")
print(f"  索提诺比率(年化)  {sortino_a:.3f}")
print(f"  盈亏比            {profit_factor:.3f}")
print()
print("  【交易统计】")
print(f"  总交易次数       {len(completed)}")
print(f"  盈利次数         {len(wins)}")
print(f"  亏损次数         {len(losses)}")
print(f"  胜率             {win_rate:.2f}%")
print(f"  平均每笔收益      ${avg_pnl:,.2f}")
print(f"  最大连续盈利      {max_sw} 次")
print(f"  最大连续亏损      {max_sl} 次")
print()
print("  【交易明细】")
print(f"  {'日期买入':<12} {'买入价':>8} {'数量':>6} {'日期卖出':<12} {'卖出价':>8} {'持仓理由':<16} {'盈亏($)':>10} {'收益率':>8}")
print("  " + "-"*90)
for t in completed:
    print(f"  {t['date_in']:<12} ${t['price_in']:>7.2f} {t['shares']:>6} "
          f"{t.get('date_out','N/A'):<12} ${t.get('price_out',0):>7.2f} "
          f"{t['exit_reason']:<14} ${t['pnl']:>+9.2f} {t['ret_pct']:>+7.2f}%")

# ── 7. 保存结果 ──────────────────────────────────────────────
with open("/workspace/backtest_results.json", "w") as f:
    json.dump({
        "summary": {
            "initial": INITIAL, "final": cash,
            "total_return": (cash/INITIAL-1)*100,
            "cagr": cagr, "max_drawdown": max_dd,
            "sharpe_annual": sharpe_a, "sortino_annual": sortino_a,
            "profit_factor": profit_factor,
            "total_trades": len(completed), "win_rate": win_rate,
            "avg_pnl": avg_pnl, "max_win_streak": max_sw, "max_loss_streak": max_sl
        },
        "trades": completed,
        "equity_curve": [(d, eq) for d, eq in equity]
    }, f, indent=2)

import csv
with open("/workspace/equity_curve.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "equity"])
    w.writerows(equity)

print("""
  结果已保存:
  /workspace/backtest_results.json   ← 完整结果(JSON)
  /workspace/equity_curve.csv         ← 每日净值曲线
""")
