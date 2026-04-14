#!/usr/bin/env python3
"""获取A股主要指数K线数据"""
import akshare as ak, json, sys

indices = [
    ("sh000001", "上证指数"),
    ("sz399001", "深证成指"),
    ("sz399006", "创业板指"),
    ("sh000688", "科创50"),
    ("hkHSI",    "恒生指数"),
]

all_data = {}
for code, name in indices:
    try:
        if code.startswith("hk"):
            df = ak.stock_hk_index_daily(symbol="HSI")
        else:
            df = ak.stock_zh_index_daily(symbol=code)
        df = df.tail(90).copy()
        df["date"] = df["date"].astype(str)
        for col in ["open","high","low","close"]:
            df[col] = df[col].astype(float)
        all_data[code] = {
            "name": name,
            "candles": [
                {"time": r["date"], "open": round(float(r["open"]),2),
                 "high": round(float(r["high"]),2), "low": round(float(r["low"]),2),
                 "close": round(float(r["close"]),2)}
                for _, r in df.iterrows()
            ]
        }
        print(f"OK: {name} {len(df)}根K线", file=sys.stderr)
    except Exception as e:
        print(f"ERR: {code} {e}", file=sys.stderr)

with open("/workspace/index_charts_data.json","w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
print("数据保存完成: /workspace/index_charts_data.json", file=sys.stderr)
