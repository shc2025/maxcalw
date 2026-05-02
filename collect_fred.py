#!/usr/bin/env python3
"""收集FRED数据"""
import requests
import json
import pandas as pd
from datetime import datetime

# FRED API key (public, no key needed for some endpoints, but let's use a free key)
# Using the public FRED observation endpoint
FRED_BASE = "https://api.stlouisfed.org/fred"

# Try without key first for public series
series_ids = {
    "SP500": "SP500",
    "DJIA": "DJIA", 
    "NASDAQCOM": "NASDAQCOM",
    "VIXCLS": "VIXCLS",
    "DGS10": "DGS10",
    "DGS2": "DGS2",
    "T10Y2Y": "T10Y2Y"
}

# Date range: last 30 days
end_date = "2026-04-30"
start_date = "2026-04-01"

results = {}

for name, sid in series_ids.items():
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}&observation_start={start_date}&observation_end={end_date}&api_key=4e58a3f9abe442f7720af616590b8b70&file_type=json"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if 'observations' in data:
            obs = data['observations']
            print(f"{name}: {len(obs)} obs, last={obs[-1] if obs else 'N/A'}")
            results[name] = obs
        else:
            print(f"{name} 失败: {data}")
    except Exception as e:
        print(f"{name} 请求失败: {e}")

# Save
with open('/workspace/weekly_fred.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nFRED数据已保存到 /workspace/weekly_fred.json")
print("\n=== FRED 关键数据 ===")
for name, obs in results.items():
    if obs:
        last = obs[-1]
        print(f"{name}: {last['date']} = {last['value']}")
