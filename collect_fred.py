import urllib.request, json, os
from datetime import datetime, timedelta

FRED_KEY = "1acf96d0a7b2c1b3e1d9e9f2a3c8b4e5"
BASE = "https://api.stlouisfed.org/fred"
SERIES = {
    "SP500": "SP500",
    "DJIA": "DJIA", 
    "NASDAQCOM": "NASDAQCOM",
    "VIXCLS": "VIXCLS",
    "DGS10": "DGS10",
    "DGS2": "DGS2",
    "T10Y2Y": "T10Y2Y",
}

end = "2026-05-15"
start = "2026-05-01"
result = {}

for name, sid in SERIES.items():
    url = f"{BASE}/series/observations?series_id={sid}&api_key={FRED_KEY}&file_type=json&observation_start={start}&observation_end={end}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            obs = data.get("seri es", {}).get("observations", [])
            result[name] = obs
    except Exception as e:
        result[name] = {"error": str(e)}

with open("/workspace/fresh_fred.json", "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print("FRED done:", {k: len(v) if isinstance(v, list) else v.get("error", "??") for k,v in result.items()})
