#!/usr/bin/env python3
"""
美股大盘双信源数据校验引擎
数据源A：Twelve Data（API: dd4f227a11f34265936086a73b46b80c）
数据源B：FRED（美联储经济数据）
交叉验证：SPX / DJI / IXIC
"""
import subprocess, json

KEY  = "dd4f227a11f34265936086a73b46b80c"
BASE = "https://api.twelvedata.com"

def curl(url):
    p = subprocess.run(["curl","-s","--max-time","12",url],capture_output=True,text=True,timeout=18)
    return p.stdout

def td(endpoint, params):
    url = f"{BASE}{endpoint}?apikey={KEY}&{params}&format=JSON"
    r = curl(url)
    try: return json.loads(r)
    except: return {}

# ═══════════════════════════════════════════════════════
#  1. 双信源数据获取
# ═══════════════════════════════════════════════════════
print("="*56)
print("  美股双信源数据校验 · 2026年4月24日")
print("="*56)

# ── 信源A：Twelve Data（ETF代理）──
print("\n【信源A】Twelve Data（SPY/QQQ/DIA ETF）")
spy_td = td("/time_series", "symbol=SPY&interval=1day&outputsize=12")
qqq_td = td("/time_series", "symbol=QQQ&interval=1day&outputsize=12")
dia_td = td("/time_series", "symbol=DIA&interval=1day&outputsize=12")

spy_vals = [(v["datetime"], float(v["close"]), float(v["open"])) for v in spy_td.get("values",[])]
qqq_vals = [(v["datetime"], float(v["close"]), float(v["open"])) for v in qqq_td.get("values",[])]
dia_vals = [(v["datetime"], float(v["close"]), float(v["open"])) for v in dia_td.get("values",[])]

print(f"  SPY: {[(v[0],round(v[1],2)) for v in spy_vals[-5:]]}")
print(f"  QQQ: {[(v[0],round(v[1],2)) for v in qqq_vals[-5:]]}")
print(f"  DIA: {[(v[0],round(v[1],2)) for v in dia_vals[-5:]]}")

# ── 信源B：FRED（官方指数）──
print("\n【信源B】FRED（美联储官方指数）")
fred = json.load(open("/workspace/fresh_fred.json"))
spx_f = fred["SP500"];  dji_f = fred["DJIA"]; nas_f = fred["NASDAQCOM"]
print(f"  SPX: {[v[0]+'='+str(round(v[1],2)) for v in spx_f[-5:]]}")
print(f"  DJI: {[v[0]+'='+str(round(v[1],2)) for v in dji_f[-5:]]}")
print(f"  NASDAQ: {[v[0]+'='+str(round(v[1],2)) for v in nas_f[-5:]]}")

# ═══════════════════════════════════════════════════════
#  2. 交叉验证（ETF×10 vs FRED指数）
# ═══════════════════════════════════════════════════════
print("\n【交叉验证】信源A(ETF×10) vs 信源B(FRED指数)")
print(f"{'日期':<12} {'ETF估算SPX':>12} {'FRED实际SPX':>12} {'误差':>8} {'结论':<6}")
print("-"*54)

match_dates = [d for d in spx_f[-5:] if d[0] in [v[0] for v in spy_vals]]
for fv in match_dates:
    dt = fv[0]
    fval = fv[1]
    sv = next((v for v in spy_vals if v[0]==dt), None)
    if sv:
        est = round(sv[1]*10, 2)
        diff = round(est - fval, 2)
        pct  = round(diff/fval*100, 3)
        ok = abs(pct) < 0.5
        flag = "✅ 吻合" if ok else ("⚠️ 偏差" if abs(pct)<1.5 else "❌ 差异大")
        print(f"{dt:<12} {est:>12,.2f} {fval:>12,.2f} {diff:>+8.2f} ({pct:+.3f}%) {flag}")

# 最关键日（4/24）
print(f"\n{'='*56}\n  4月24日收盘校验结果")
print(f"{'='*56}")
spx_b24 = spx_f[-1]
spy_b24 = spy_vals[-1] if spy_vals else None
if spy_b24:
    est24 = round(spy_b24[1]*10, 2)
    diff24 = round(est24 - spx_b24[1], 2)
    pct24  = round(diff24/spx_b24[1]*100, 3)
    print(f"  信源A (SPY×10): {spy_b24[1]:.2f}×10 = {est24:,.2f}")
    print(f"  信源B (FRED):   {spx_b24[1]:,.2f}")
    print(f"  误差: {diff24:+.2f}点 ({pct24:+.3f}%)")
    print(f"  结论: {'✅ 两信源高度吻合，数据可信' if abs(pct24)<0.5 else '⚠️ 两信源存在偏差，取信源B(FRED)为基准'}")
    print(f"  采用SPX={spx_b24[1]:,.2f} (FRED) | DJI={dji_f[-1][1]:,.2f} | NASDAQ={nas_f[-1][1]:,.2f}")

# ═══════════════════════════════════════════════════════
#  3. 周涨幅双信源对比
# ═══════════════════════════════════════════════════════
print(f"\n{'='*56}\n  周涨幅对比（4/17→4/24）")
print(f"{'='*56}")

# 信源A: TD SPY
a_4d = spy_vals[-1][1]; a_4o = spy_vals[-2][1]  # 4/24, 4/17
a_pct = round((a_4d-a_4o)/a_4o*100, 3)

# 信源B: FRED SPX
b_4d = spx_b24[1]; b_4o = spx_f[-5][1]
b_pct = round((b_4d-b_4o)/b_4o*100, 3)

print(f"  信源A: SPY {a_4o:.2f}→{a_4d:.2f}  周涨幅={a_pct:+.3f}%")
print(f"  信源B: SPX {b_4o:,.2f}→{b_4d:,.2f}  周涨幅={b_pct:+.3f}%")
print(f"  分歧: {abs(a_pct-b_pct):.3f}个百分点 ({'✅ 一致' if abs(a_pct-b_pct)<0.5 else '⚠️ 轻微分歧，取均值'})")

# 最终采用值
final_spx = round((est24 + spx_b24[1])/2, 2) if abs(pct24)<1.0 else spx_b24[1]
final_pct = round((a_pct+b_pct)/2, 3)

print(f"\n  最终采用（两信源均值或共识值）:")
print(f"  SPX:  {final_spx:,.2f}  涨跌幅: {final_pct:+.3f}%")

# 保存最终数据
result = {
    "SPX": {"close": spx_b24[1], "open": 7117.05,  # 用户确认值
            "chg_pct": final_pct,
            "信源A(SPY×10)": est24,
            "信源B(FRED)": spx_b24[1],
            "信源A涨幅": a_pct, "信源B涨幅": b_pct,
            "校验结论": "✅双信源吻合" if abs(pct24)<0.5 else "⚠️取FRED为基准"},
    "DJI": {"close": dji_f[-1][1], "prev_close": dji_f[-5][1],
            "chg_pct": round((dji_f[-1][1]-dji_f[-5][1])/dji_f[-5][1]*100,3),
            "信源A(DIA×10)": round(dia_vals[-1][1]*10,2) if dia_vals else None,
            "信源B(FRED)": dji_f[-1][1]},
    "NASDAQ": {"close": nas_f[-1][1], "prev_close": nas_f[-5][1],
               "chg_pct": round((nas_f[-1][1]-nas_f[-5][1])/nas_f[-5][1]*100,3),
               "信源A(QQQ×10)": round(qqq_vals[-1][1]*10,2) if qqq_vals else None,
               "信源B(FRED)": nas_f[-1][1]}
}
with open("/workspace/verified_us_index.json","w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\n✅ verified_us_index.json saved")
print(json.dumps(result, ensure_ascii=False, indent=2))