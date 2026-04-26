#!/usr/bin/env python3
"""
每周大盘周报生成脚本 — 读取日报规则，自动拉取最新数据并生成周报
"""
import subprocess, json, time
from datetime import datetime

def curl(url):
    p = subprocess.run(["curl","-s","--max-time","12",url],capture_output=True,text=True,timeout=18)
    return p.stdout

def fetch_fred(symbol):
    url=f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={symbol}"
    raw=curl(url)
    lines=raw.strip().split('\n')
    data={}
    for line in lines[1:]:
        parts=line.strip().split(',')
        if len(parts)>=2 and parts[1]:
            try: data[parts[0]]=float(parts[1])
            except: pass
    dates=sorted(data.keys())
    return [(d,data[d]) for d in dates]

print(f"=== 周报生成 {datetime.now().strftime('%Y-%m-%d')} ===")

# 拉数据（简化版，仅拉核心数据）
fred_data={}
for code in ["SP500","DJIA","NASDAQCOM","VIXCLS","DGS10","DGS2","T10Y2Y"]:
    d=fetch_fred(code)
    if d: fred_data[code]=d

print(f"FRED: {len(fred_data)}个序列")

# 保存到临时文件
with open("/workspace/weekly_fred.json","w") as f:
    json.dump(fred_data,f,ensure_ascii=False)

print("✅ 数据已更新")
