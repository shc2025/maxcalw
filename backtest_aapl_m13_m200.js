const { YahooFinance2 } = require('/tmp/node_modules/yahoo-finance2');

async function run() {
  // Fetch 5 years of daily data
  const data = await YahooFinance2.chart('AAPL', {
    period1: '2021-04-05',
    period2: '2026-04-05',
    interval: '1d',
  });

  const quotes = data.quotes;
  console.log(`Fetched ${quotes.length} daily candles`);
  console.log(`Date range: ${quotes[0].date} → ${quotes[quotes.length-1].date}`);

  // Calculate M13 and M200
  const close = quotes.map(q => q.close);
  const dates = quotes.map(q => q.date);

  function sma(data, period) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null);
      } else {
        let sum = 0;
        for (let j = 0; j < period; j++) {
          sum += data[i - j];
        }
        result.push(sum / period);
      }
    }
    return result;
  }

  const m13 = sma(close, 13);
  const m200 = sma(close, 200);

  // ─── Strategy ───────────────────────────────────────────────
  // Condition: M13 > M200 (long-only, no short)
  // Entry: M13 crosses above M200, or M13 turns up from a dip
  // Exit:  M13 turns down, or M13 crosses below M200
  // Position size: ~$10,000 per trade

  let cash = 10000;
  let position = 0;       // shares held
  let entryPrice = 0;
  let equityCurve = [];   // portfolio value over time
  let trades = [];

  let prevM13 = null, prevPrevM13 = null;
  let prevM13Above = false;

  for (let i = 0; i < close.length; i++) {
    const c = close[i];
    const m13v = m13[i];
    const m200v = m200[i];
    const date = dates[i];

    if (m13v === null || m200v === null) {
      equityCurve.push({ date, equity: cash + position * c });
      continue;
    }

    const m13Above = m13v > m200v;

    // Detect M13 turning points
    // "Upward turn": m13 was going down, now goes up
    // "Downward turn": m13 was going up, now goes down
    let m13TurnUp = false, m13TurnDown = false;
    if (prevPrevM13 !== null && prevM13 !== null) {
      const wasRising = prevM13 - prevPrevM13 > 0;
      const nowRising = m13v - prevM13 > 0;
      if (!wasRising && nowRising) m13TurnUp = true;
      if (wasRising && !nowRising) m13TurnDown = true;
    }

    const equity = cash + position * c;
    equityCurve.push({ date, equity });

    // ── Entry logic ──
    if (position === 0 && m13Above) {
      // BUY: M13 > M200 and M13 turns up
      if (m13TurnUp) {
        const shares = Math.floor(10000 / c);
        if (shares > 0) {
          position = shares;
          cash -= shares * c;
          entryPrice = c;
          trades.push({ date, type: 'BUY', price: c, shares, m13: m13v, m200: m200v, equity: cash + position * c });
        }
      }
    }

    // ── Exit logic ──
    if (position > 0) {
      // Sell: M13 turns down OR M13 crosses below M200
      if (m13TurnDown || (!m13Above)) {
        cash += position * c;
        const pnl = cash - (entryPrice * position);
        trades[trades.length - 1].exitPrice = c;
        trades[trades.length - 1].closeDate = date;
        trades[trades.length - 1].pnl = pnl;
        trades[trades.length - 1].returnPct = pnl / (entryPrice * position) * 100;
        trades[trades.length - 1].equity = cash;
        trades[trades.length - 1].exitReason = m13TurnDown ? 'M13_TURN_DOWN' : 'M13_CROSS_BELOW_M200';
        position = 0;
      }
    }

    prevPrevM13 = prevM13;
    prevM13 = m13v;
  }

  // Close any open position at end
  if (position > 0) {
    const lastClose = close[close.length - 1];
    const lastDate = dates[dates.length - 1];
    cash += position * lastClose;
    const pnl = cash - (entryPrice * position);
    trades[trades.length - 1].exitPrice = lastClose;
    trades[trades.length - 1].closeDate = lastDate;
    trades[trades.length - 1].pnl = pnl;
    trades[trades.length - 1].returnPct = pnl / (entryPrice * position) * 100;
    trades[trades.length - 1].equity = cash;
    trades[trades.length - 1].exitReason = 'END_OF_DATA';
    position = 0;
  }

  // ─── Stats ──────────────────────────────────────────────────
  const completedTrades = trades.filter(t => t.exitPrice !== undefined);
  const winningTrades = completedTrades.filter(t => t.pnl > 0);
  const winRate = completedTrades.length > 0 ? winningTrades.length / completedTrades.length * 100 : 0;
  const totalPnl = completedTrades.reduce((s, t) => s + t.pnl, 0);
  const avgPnl = completedTrades.length > 0 ? totalPnl / completedTrades.length : 0;

  // Max drawdown
  let peak = -Infinity, maxDd = 0;
  for (const { equity } of equityCurve) {
    if (equity > peak) peak = equity;
    const dd = peak - equity;
    if (dd > maxDd) maxDd = dd;
  }

  // Sharpe Ratio (daily returns)
  const initial = 10000;
  const returns = [];
  let prevEq = initial;
  for (const { equity } of equityCurve) {
    returns.push((equity - prevEq) / prevEq);
    prevEq = equity;
  }
  const avgRet = returns.reduce((s, r) => s + r, 0) / returns.length;
  const stdRet = Math.sqrt(returns.reduce((s, r) => s + (r - avgRet) ** 2, 0) / returns.length);
  const sharpeDaily = stdRet > 0 ? avgRet / stdRet : 0;
  const sharpeAnnual = sharpeDaily * Math.sqrt(252);

  // Sortino Ratio
  const negRet = returns.filter(r => r < 0);
  const stdNeg = Math.sqrt(negRet.reduce((s, r) => s + r ** 2, 0) / negRet.length);
  const sortinoDaily = stdNeg > 0 ? avgRet / stdNeg : 0;
  const sortinoAnnual = sortinoDaily * Math.sqrt(252);

  // Profit Factor
  const grossProfit = completedTrades.filter(t => t.pnl > 0).reduce((s, t) => s + t.pnl, 0);
  const grossLoss = Math.abs(completedTrades.filter(t => t.pnl < 0).reduce((s, t) => s + t.pnl, 0));
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? Infinity : 0;

  // Max consecutive wins / losses
  let maxWinStreak = 0, maxLossStreak = 0, curW = 0, curL = 0;
  for (const t of completedTrades) {
    if (t.pnl > 0) { curW++; curL=0; maxWinStreak=Math.max(maxWinStreak,curW); }
    else          { curL++; curW=0; maxLossStreak=Math.max(maxLossStreak,curL); }
  }

  // Annualized return
  const years = (new Date(dates[dates.length-1]) - new Date(dates[0])) / (365.25*24*3600000);
  const cagr = (Math.pow(cash / initial, 1/years) - 1) * 100;

  console.log('\n══════════════════════════════════════');
  console.log('   AAPL M13/M200 Strategy Backtest');
  console.log(`   Period: ${dates[0].slice(0,10)} → ${dates[dates.length-1].slice(0,10)} (${years.toFixed(1)} years)`);
  console.log('══════════════════════════════════════');
  console.log(`\n  Portfolio Summary`);
  console.log(`  ─────────────────────────────────────`);
  console.log(`  Initial Capital:        \$${initial.toLocaleString()}`);
  console.log(`  Final Capital:          \$${cash.toLocaleString('en',{minimumFractionDigits:2})}`);
  console.log(`  Total Return:           ${((cash/initial-1)*100).toFixed(2)}%`);
  console.log(`  CAGR:                   ${cagr.toFixed(2)}%`);
  console.log(`  Max Drawdown:          -\$${maxDd.toFixed(2)}`);
  console.log(`  Sharpe Ratio (ann.):    ${sharpeAnnual.toFixed(3)}`);
  console.log(`  Sortino Ratio (ann.):   ${sortinoAnnual.toFixed(3)}`);
  console.log(`  Profit Factor:         ${profitFactor.toFixed(3)}`);

  console.log(`\n  Trade Statistics`);
  console.log(`  ─────────────────────────────────────`);
  console.log(`  Total Trades:          ${completedTrades.length}`);
  console.log(`  Winning Trades:        ${winningTrades.length}`);
  console.log(`  Losing Trades:         ${completedTrades.length - winningTrades.length}`);
  console.log(`  Win Rate:              ${winRate.toFixed(2)}%`);
  console.log(`  Avg P&L per Trade:     \$${avgPnl.toFixed(2)}`);
  console.log(`  Max Consecutive Wins:   ${maxWinStreak}`);
  console.log(`  Max Consecutive Losses: ${maxLossStreak}`);

  console.log(`\n  Trade Log`);
  console.log(`  ─────────────────────────────────────`);
  for (const t of completedTrades) {
    console.log(`  ${t.date.slice(0,10)}  ${t.type}  @ \$${t.price.toFixed(2)}  × ${t.shares}sh  →  exit ${t.exitReason}  PnL: \$${t.pnl.toFixed(2)} (${t.returnPct?.toFixed(2)}%)`);
  }

  // Save equity curve to CSV
  const fs = require('fs');
  const csv = ['date,equity', ...equityCurve.map(e => `${e.date.slice(0,10)},${e.equity.toFixed(2)}`)];
  fs.writeFileSync('/workspace/equity_curve.csv', csv.join('\n'));
  console.log('\n[Equity curve saved to /workspace/equity_curve.csv]');
}

run().catch(e => { console.error(e); process.exit(1); });
