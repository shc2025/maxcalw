#!/usr/bin/env python3
import subprocess, json, importlib.util

APIKEY = "dd4f227a11f34265936086a73b46b80c"

def get_kline(symbol, days=10):
    url = ("https://api.twelvedata.com/time_series?symbol=%s&interval=1day&outputsize=%d&apikey=%s&order=desc") % (symbol, days, APIKEY)
    p = subprocess.run(["curl","-s","--max-time","15",url],capture_output=True,text=True)
    d = json.loads(p.stdout); vals = d.get("values",[])
    print("  API said:", d.get("status"))
    return vals

print("=== 直接查询 MCD ===")
v = get_kline("MCD", 10)
for x in v: print(" ", x["datetime"], "O=", x["open"], "C=", x["close"])

print("\n=== 用 end_date=2026-04-17 ===")
url2 = ("https://api.twelvedata.com/time_series?symbol=MCD&interval=1day&outputsize=10&apikey=%s&end_date=2026-04-17&order=desc") % APIKEY
p2 = subprocess.run(["curl","-s","--max-time","15",url2],capture_output=True,text=True)
d2 = json.loads(p2.stdout); vals2 = d2.get("values",[])
for x in vals2: print(" ", x["datetime"], "C=", x["close"])

print("\n=== 用 end_date=2026-04-15 ===")
url3 = ("https://api.twelvedata.com/time_series?symbol=MCD&interval=1day&outputsize=10&apikey=%s&end_date=2026-04-15&order=desc") % APIKEY
p3 = subprocess.run(["curl","-s","--max-time","15",url3],capture_output=True,text=True)
d3 = json.loads(p3.stdout); vals3 = d3.get("values",[])
for x in vals3: print(" ", x["datetime"], "C=", x["close"])

print("\n=== crsi_calculator 直接计算 ===")
spec = importlib.util.spec_from_file_location("cc", "/workspace/skills/crsi-calculator/__init__.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
calc = mod.CRSICalculator(api_key=APIKEY)

# 不用date参数，取最新
r = calc.calculate("MCD")
if "error" in r:
    print("Error:", r["error"], "| latest:", r.get("available_latest"))
else:
    print("Date:", r["date"], "Close:", r["close"])
    c = r["components"]; s = r["signal"]
    print("  CRSI = %.2f" % r["crsi"])
    print("  RSI_price=%.2f  RSI_updown=%.2f  pct_rank=%.2f" % (c["rsi_price"], c["rsi_updown"], c["pct_rank_roc"]))
    print("  信号:", s["emoji"], s["zone"])
