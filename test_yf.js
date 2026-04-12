const yf = require('/tmp/node_modules/yfinance');
yf.getHistorical('AAPL', {period1: '2021-04-05', period2: '2026-04-05'})
  .then(r => {
    console.log('rows:', r.length);
    console.log('first:', JSON.stringify(r[0]));
    console.log('last:', JSON.stringify(r[r.length-1]));
  })
  .catch(e => {
    console.error('Error:', e.message);
    // Try alternative format
    return yf.getHistorical('AAPL', '2021-04-05', '2026-04-05');
  })
  .then(r => {
    if (r) {
      console.log('alt rows:', r.length);
      console.log('alt first:', JSON.stringify(r[0]));
    }
  })
  .catch(e => console.error('Alt error:', e.message));
