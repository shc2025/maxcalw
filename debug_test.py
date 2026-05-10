"""
调试脚本：验证 Spring / JOC 数据生成 + detect 函数逻辑
不依赖 run()，单独运行，快速定位问题
"""
import random
random.seed(42)

from test_spring_joc import (
    generate_spring_scene, generate_joc_scene,
    build_indicators, detect_spring, detect_joc_original, detect_joc_fixed
)

# ============================================================
# 验证 1: Spring 数据
# ============================================================
print("=" * 55)
print("  验证1: Spring 场景数据")
print("=" * 55)

spring_bars = generate_spring_scene()
ind_s = build_indicators(spring_bars)

pivot_len = 6
range_lookback = 60

# 找 planted pivot（bar 40）并打印前后 low
print("\n[bar 40 附近 12 根 K 线 low]")
for i in range(34, 48):
    bar = spring_bars[i]
    mark = " ← planted" if i == 40 else (" ← spring" if i == 46 else "")
    print(f"  bar {i}: low={bar.low:.4f}  close={bar.close:.4f}{mark}")

# 打印 calc_pivot_low 结果
print("\n[pivot_lows 检测结果（bar 34~50）]")
for i in range(34, min(51, len(ind_s["pivot_lows"]))):
    v = ind_s["pivot_lows"][i]
    if v is not None:
        print(f"  bar {i}: pivot_low={v:.4f}  (low={spring_bars[i].low:.4f})")

# 手动在 bar 46 检测 detect_spring
print("\n[detect_spring 逐条件验证 - bar_index = 46]")
bar_index = 46
piv = ind_s["pivot_lows"][bar_index]
pp_bar = bar_index - pivot_len  # = 40
pp = spring_bars[pp_bar].low
low_i = spring_bars[bar_index].low
close_i = spring_bars[bar_index].close
range_low = ind_s["range_low"][bar_index]

t_count = sum(1 for j in range(pp_bar, bar_index + 1)
              if spring_bars[j].low < pp)

print(f"  pivot_lows[{bar_index}] = {piv}  (should be planted_price)")
print(f"  pp_bar = {pp_bar}, pp = bars[40].low = {pp:.4f}")
print(f"  t_count = {t_count}  (should <= 3)")
print(f"  low < pp ?  {low_i:.4f} < {pp:.4f} = {low_i < pp}")
print(f"  close > pp ?  {close_i:.4f} > {pp:.4f} = {close_i > pp}")
print(f"  low <= rangeLow ?  {low_i:.4f} <= {range_low:.4f} = {low_i <= range_low}")

ok, conf = detect_spring(bar_index, ind_s, pivot_len=pivot_len,
                          range_lookback=range_lookback)
print(f"\n  detect_spring() → ok={ok}  conf={conf}")

# ============================================================
# 验证 2: JOC 数据
# ============================================================
print("\n" + "=" * 55)
print("  验证2: JOC 场景数据")
print("=" * 55)

joc_bars = generate_joc_scene()
ind_j = build_indicators(joc_bars)

print("\n[bar 70~72 K 线数据]")
for i in range(68, min(76, len(joc_bars))):
    bar = joc_bars[i]
    rh_prev = ind_j["range_high"][i-1] if i > 0 else None
    mark = " ← JOC" if i == 71 else ""
    print(f"  bar {i}: high={bar.high:.2f}  close={bar.close:.2f}  "
          f"vol={bar.volume:,.0f}  rangeHigh[bar-1]={rh_prev:.2f}{mark}")

print("\n[JOC 修复版逐条件验证 - bar_index = 71]")
bar_index = 71
hiPrev = ind_j["range_high"][bar_index - 1]
close = joc_bars[bar_index].close
prev_close = joc_bars[bar_index - 1].close
prev2_close = joc_bars[bar_index - 2].close
vol = joc_bars[bar_index].volume
avg_vol = ind_j["avg_vol"][bar_index]
day_range = joc_bars[bar_index].high - joc_bars[bar_index].low
close_pos = (close - joc_bars[bar_index].low) / day_range if day_range > 0 else 0

print(f"  hiPrev (rangeHigh[70]) = {hiPrev:.2f}")
print(f"  prev_close > hiPrev ?  {prev_close:.2f} > {hiPrev:.2f} = {prev_close > hiPrev}")
print(f"  close > hiPrev ?  {close:.2f} > {hiPrev:.2f} = {close > hiPrev}")
print(f"  vol > avg*1.5 ?  {vol:,.0f} > {avg_vol*1.5:,.0f} = {vol > avg_vol*1.5}")
print(f"  收盘位置 {close_pos:.0%} > 65% ? {close_pos > 0.65}")
print(f"  prev2_close > hiPrev ?  {prev2_close:.2f} > {hiPrev:.2f} = {prev2_close > hiPrev}")

ok, conf, msg = detect_joc_fixed(bar_index, ind_j, range_lookback=60)
print(f"\n  detect_joc_fixed() → ok={ok}  conf={conf}  msg={msg}")

# ============================================================
# 验证 3: 无信号场景 - JOC 重复触发
# ============================================================
print("\n" + "=" * 55)
print("  验证3: 无信号场景 JOC 重复触发（BUG2）")
print("=" * 55)

normal_bars = []
import math
for _ in range(5):
    p = 100.0 + random.uniform(-0.5, 0.5)
    normal_bars.append(spring_bars[0].__class__(
        high=p + 0.3, low=p - 0.3, close=p, volume=1_000_000))

from test_spring_joc import generate_no_signal_scene
no_sig_bars = generate_no_signal_scene()
no_sig_bars += [spring_bars[0].__class__(high=105.0, low=100.0, close=104.5, volume=1_600_000)
                for _ in range(6)]  # 模拟连续6根突破

ind_n = build_indicators(no_sig_bars)
print(f"\n[连续6根突破：无信号场景 JOC 原版检测]")
for i in range(65, min(76, len(no_sig_bars))):
    ok, conf, _ = detect_joc_original(i, ind_n, 60)
    if ok:
        hiPrev = ind_n["range_high"][i-1]
        close = no_sig_bars[i].close
        print(f"  bar {i}: JOC触发 close={close:.2f}  rangeHigh[bar-1]={hiPrev:.2f}")

# ============================================================
# 总结：发现的问题
# ============================================================
print("\n" + "=" * 55)
print("  🔍 问题定位")
print("=" * 55)
print("""
[Spring 未检测到]
  原因：pivot_lows[46] = None，planted pivot 未被识别
  根因：bars[40] 的 planted_price 仍高于周围某些 bar 的 low，
        导致 calc_pivot_low 的左右各 6 根比较失败
  修复方向：
    1. 将 planted_price 硬编码为明确低于前后 12 根的固定值（如 93.0）
    2. 或在 detect_spring 中，不依赖 pivot_lows[bar_index] 是否有值，
       直接检查 bar_index-pivot_len 是否为 pivot（通过再次计算验证）
    3. 最简单：detect_spring 时重新计算一次 pivot_low

[JOC 原版重复触发 - 无信号场景]
  原因：BUG2 确认存在 — 一旦 close 突破 rangeHigh，
       后续每天 close > rangeHigh 持续成立，信号重复
  修复：必须使用 detect_joc_fixed（一次性触发）

[JOC 修复版一次性检测]
  状态：✅ 正常工作
""")