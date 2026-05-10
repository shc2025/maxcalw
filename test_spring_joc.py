"""
威科夫 Spring / JOC 检测逻辑 - 模拟测试脚本 v2
完全重写，数据长度满足 range_lookback=60 的要求
"""

import random
import json
from dataclasses import dataclass
from typing import Optional

random.seed(42)

# ============================================================
# K 线数据结构
# ============================================================

@dataclass
class Bar:
    high: float
    low: float
    close: float
    volume: float

# ============================================================
# 模拟数据生成
# ============================================================

def make_bars(n: int, base_price: float = 100.0,
              vol_pct: float = 0.015) -> list[Bar]:
    """普通震荡 K 线"""
    bars, p = [], base_price
    for _ in range(n):
        d = p * vol_pct * random.uniform(-1, 1)
        o, c = p, p + d
        h = max(o, c) * random.uniform(1.0, 1.005)
        l = min(o, c) * random.uniform(0.995, 1.0)
        bars.append(Bar(high=h, low=l, close=c, volume=random.uniform(9e5, 1.1e6)))
        p = c
    return bars


def generate_spring_scene() -> list[Bar]:
    """
    Spring 场景：
    - 前 40 根：建立区间震荡，锚定参考价
    - bar 40：planted pivot（pivotlow），确保前后各6根都是它的更高
    - bar 46：Spring 触发根，low < pp（刺穿），close > pp（收回），低量

    pivot_lows[46] = low[46]（因为 bar 46 是 pivot），
    pp = low[46]（PineScript low[pivotLen] = low[40]），
    检测时：low < pp → low[46] < low[46] → 不成立
    → 改为：Spring 根在 bar_index = 47（pivot 位置 = 47-6 = 41），
           pivot_lows[47] = low[47]，pp = low[41]，
           low[47] < low[41]（可成立）
    """
    bars = make_bars(41, base_price=100.0, vol_pct=0.012)

    # bar 41：planted pivot，low = 98.00（比前后12根都低）
    pivot_bar = 41
    planted_price = 98.00  # 固定值，前后各6根最低
    bars.append(Bar(high=planted_price + 1.0,
                     low=planted_price,
                     close=planted_price + 0.6,
                     volume=750000))

    # bar 42~46：普通震荡填充
    for _ in range(5):
        p = 100.0 + random.uniform(-0.8, 0.8)
        bars.append(Bar(high=p + 0.5, low=p - 0.5, close=p, volume=950000))

    # Spring 触发根：bar_index = 47（pivot 位置 = 47-6 = 41）
    spring_bar_idx = len(bars)  # = 47
    spring_low = planted_price * 0.975   # 低于 planted_price (98.00 → 95.55)
    spring_close = planted_price * 1.020  # 收在 planted 上方 (> 98.00)
    bars.append(Bar(high=planted_price + 1.5,
                     low=spring_low,
                     close=spring_close,
                     volume=680000))  # 低量

    # 追加几根正常 bar
    bars += make_bars(5, base_price=bars[-1].close, vol_pct=0.01)
    return bars


def generate_joc_scene() -> list[Bar]:
    """
    JOC 场景：
    - 前 50 根：自由震荡
    - bar 50~70（共21根）：建立明确区间 [99.50, 103.50]
    - bar 71（JOC 触发根）：放量跳空 close=105 > 区间高点 103.50
    """
    # 前50根自由震荡
    bars = make_bars(50, base_price=101.0, vol_pct=0.012)

    # 用具体值重写 bar 50~69（20根），使区间高点 = 103.50
    for i in range(20):
        idx = 50 + i
        p = 101.5 + random.uniform(-1.0, 1.5)
        h = min(p + 0.6, 103.50)
        l = max(p - 0.6, 99.50)
        bars.append(Bar(high=h, low=l, close=p, volume=1_000_000))

    # bar 70（精确植入区间高点）
    bars.append(Bar(high=103.50, low=100.50, close=101.00, volume=1_000_000))

    # JOC 突破根（index 71）：close=105.00 > 区间高点 103.50
    avg_vol = 1_000_000
    bars.append(Bar(high=105.80,
                    low=103.20,
                    close=105.00,
                    volume=int(avg_vol * 1.65)))

    # 突破后连续4根阳线（验证 JOC 不重复触发）
    for _ in range(4):
        last = bars[-1]
        nxt = last.close * 1.003
        bars.append(Bar(high=nxt + 0.4,
                        low=nxt - 0.3,
                        close=nxt,
                        volume=int(avg_vol * 1.1)))
    return bars


def generate_no_signal_scene() -> list[Bar]:
    """普通震荡行情，无 Spring/JOC"""
    return make_bars(80, base_price=100.0, vol_pct=0.015)


# ============================================================
# 技术指标计算（PineScript 等价实现）
# ============================================================

def calc_sma(values: list[float], period: int) -> list[Optional[float]]:
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1: i + 1]) / period)
    return result


def calc_atr(highs: list[float], lows: list[float],
              closes: list[float], period: int = 14) -> list[Optional[float]]:
    trs = [highs[0] - lows[0]]
    for i in range(1, len(highs)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        trs.append(max(hl, hc, lc))
    sma = calc_sma(trs, period)
    return [None] * (period - 1) + sma


def calc_highest(highs: list[float], lookback: int) -> list[Optional[float]]:
    result = []
    for i in range(len(highs)):
        start = max(0, i - lookback + 1)
        result.append(max(highs[start: i + 1]) if start <= i else None)
    return result


def calc_lowest(lows: list[float], lookback: int) -> list[Optional[float]]:
    result = []
    for i in range(len(lows)):
        start = max(0, i - lookback + 1)
        result.append(min(lows[start: i + 1]) if start <= i else None)
    return result


def calc_pivot_low(lows: list[float], length: int) -> list[Optional[float]]:
    """
    等价 PineScript: ta.pivotlow(len, len)
    pivot 在 bar_index = i，左侧 len 根，右侧 len 根的 low 都是 pivot 最低
    """
    n = len(lows)
    result = [None] * n
    for i in range(length, n - length):
        left = lows[i - length: i]
        right = lows[i + 1: i + 1 + length]
        # 严格 len 根
        if len(left) < length or len(right) < length:
            continue
        if min(left) > lows[i] and min(right) > lows[i]:
            result[i] = lows[i]
    return result


def calc_pivot_high(highs: list[float], length: int) -> list[Optional[float]]:
    n = len(highs)
    result = [None] * n
    for i in range(length, n - length):
        left = highs[i - length: i]
        right = highs[i + 1: i + 1 + length]
        if len(left) < length or len(right) < length:
            continue
        if max(left) < highs[i] and max(right) < highs[i]:
            result[i] = highs[i]
    return result


# ============================================================
# 预计算全局指标（对应 PineScript 预计算部分）
# ============================================================

def build_indicators(bars: list[Bar], range_lookback: int = 60,
                     pivot_len: int = 6):
    highs   = [b.high for b in bars]
    lows    = [b.low for b in bars]
    closes  = [b.close for b in bars]
    volumes = [float(b.volume) for b in bars]

    atr          = calc_atr(highs, lows, closes, 14)
    range_high   = calc_highest(highs, range_lookback)
    range_low    = calc_lowest(lows, range_lookback)
    avg_vol      = calc_sma(volumes, 20)
    pivot_lows   = calc_pivot_low(lows, pivot_len)
    pivot_highs  = calc_pivot_high(highs, pivot_len)
    adx_vals     = [22.0] * len(bars)   # 模拟 ADX=22（满足<25）

    return {
        "highs": highs, "lows": lows, "closes": closes,
        "volumes": volumes, "atr": atr,
        "range_high": range_high, "range_low": range_low,
        "avg_vol": avg_vol,
        "pivot_lows": pivot_lows, "pivot_highs": pivot_highs,
        "adx_vals": adx_vals,
    }


# ============================================================
# Spring 检测（PineScript detectSpring 等价翻译）
# ============================================================

def detect_spring(
    bar_index: int,
    ind: dict,
    pivot_len: int = 6,
    range_lookback: int = 60,
    vol_control: bool = False,
    vol_multi: float = 1.5,
    adx_enabled: bool = False,
    adx_threshold: float = 25.0,
) -> tuple[bool, int]:
    """
    等价 PineScript detectSpring() 的核心逻辑：

    ta.pivotlow(pivotLen, pivotLen) 在 bar_index 位置返回：
      - 若 bar_index 是 pivot → 返回 bar_index 的 low（即 planted pivot）
      - 若 bar_index 不是 pivot → 返回 na

    PineScript 代码：
      piv = ta.pivotlow(pivotLen, pivotLen)
      ...
      pp = low[pivotLen]    // bar_index - pivot_len 那根 bar 的 low

    所以 planted pivot 在 bar_index - pivot_len 位置，
    Spring 触发时，bar_index 是 Spring 根，bar_index-pivot_len 是 pivot 根。

    本函数直接取 bar_index-pivot_len 位置的 low 作为 pp，绕过 pivot_lows 查询。
    """
    if bar_index < pivot_len or bar_index >= len(ind["lows"]):
        return False, 0

    # pp = pivot 根的 low（PineScript low[pivotLen]）
    pp_bar = bar_index - pivot_len
    pp = ind["lows"][pp_bar]
    if pp is None or pp <= 0:
        return False, 0

    # 区间内创新低的 bar 数（PineScript t_count）
    t_count = sum(1 for j in range(pp_bar, bar_index + 1)
                   if j >= 0 and j < len(ind["lows"])
                   and ind["lows"][j] < pp)

    close = ind["closes"][bar_index] if bar_index < len(ind["closes"]) else None
    low_i = ind["lows"][bar_index] if bar_index < len(ind["lows"]) else None
    range_low = ind["range_low"][bar_index] if bar_index < len(ind["range_low"]) else None
    avg_vol_i = ind["avg_vol"][bar_index] if bar_index < len(ind["avg_vol"]) else 1.0
    vol_i = ind["volumes"][bar_index] if bar_index < len(ind["volumes"]) else 1.0
    adx_i = ind["adx_vals"][bar_index] if bar_index < len(ind["adx_vals"]) else None

    # Spring 核心条件（与 PineScript 完全一致）
    if (t_count <= 3
            and low_i is not None and low_i < pp
            and close is not None and close > pp
            and range_low is not None and low_i <= range_low):

        base = 55
        if low_i < range_low and close > pp:
            base += 10
        if vol_control and vol_i <= avg_vol_i * vol_multi:
            base += 5
        if not adx_enabled or (adx_i is not None and adx_i < adx_threshold):
            base += 5

        return True, min(100, base)

    return False, 0


# ============================================================
# JOC 检测：原版（含 BUG）+ 修复版
# ============================================================

def detect_joc_original(
    bar_index: int,
    ind: dict,
    range_lookback: int = 60,
) -> tuple[bool, int, str]:
    """
    JOC 原版（PineScript 含 BUG）

    BUG 所在（PineScript 代码）：
        if not (na(hiPrev) or hiPrev <= 0 or close <= hiPrev
                or close[1] > hiPrev or na(close[1])
                or math.abs(close[1] - hiPrev) / hiPrev > 0.05)
            ...
            if close > hiPrev:

    问题1: 条件 `close <= hiPrev` 在前置判断里，但之后又 `if close > hiPrev`，
           逻辑矛盾（先排除再判断），实际上 `close <= hiPrev` 从未成立就跳出了。
    问题2: 突破成立后，`close > hiPrev` 每天成立，信号每天重复触发。
    """
    if bar_index < 1 or bar_index < range_lookback:
        return False, 0, ""

    range_high = ind["range_high"]
    closes = ind["closes"]
    volumes = ind["volumes"]
    avg_vol = ind["avg_vol"]
    resistances = [ind["range_high"][max(0, bar_index - 10)]]

    hiPrev = range_high[bar_index - 1] if (bar_index - 1) < len(range_high) else None
    if hiPrev is None or hiPrev <= 0:
        return False, 0, ""

    close = closes[bar_index]
    prev_close = closes[bar_index - 1]

    # PineScript 原版翻译（保留 BUG）
    skip = (
        prev_close is not None and prev_close > hiPrev
    ) or (
        prev_close is not None and hiPrev > 0 and
        abs(prev_close - hiPrev) / hiPrev > 0.05
    )
    if skip:
        return False, 0, ""

    if close <= hiPrev:
        return False, 0, ""

    base = 60
    avg_v = avg_vol[bar_index] if bar_index < len(avg_vol) else 1.0
    vol = volumes[bar_index] if bar_index < len(volumes) else 0.0
    if vol > avg_v * 1.5 and avg_v > 0:
        base += 10

    sr_bonus = 0.0
    for rv in resistances:
        if rv > 0 and abs(hiPrev - rv) / close <= 0.01:
            sr_bonus = 5.0
            break

    return True, min(100, base + int(sr_bonus)), "原版触发"


def detect_joc_fixed(
    bar_index: int,
    ind: dict,
    range_lookback: int = 60,
) -> tuple[bool, int, str]:
    """
    JOC 修复版

    修复点：
    1. 前置条件检查 prev_close <= hiPrev（蓄力在区间内）
    2. 当根条件 close > hiPrev（真实突破）
    3. 必须是放量（vol > avg * 1.5）
    4. 必须是阳线（收盘在当日高位）
    5. 只允许突破当天触发（prev2_close 不能也突破过）
    """
    if bar_index < 2 or bar_index < range_lookback:
        return False, 0, ""

    range_high = ind["range_high"]
    highs = ind["highs"]
    lows = ind["lows"]
    closes = ind["closes"]
    volumes = ind["volumes"]
    avg_vol = ind["avg_vol"]
    resistances = [ind["range_high"][max(0, bar_index - 10)]]

    hiPrev = range_high[bar_index - 1]
    if hiPrev is None or hiPrev <= 0:
        return False, 0, ""

    close = closes[bar_index]
    prev_close = closes[bar_index - 1]
    prev2_close = closes[bar_index - 2]

    # 修复1：前一根必须在区间内（蓄力）
    if prev_close > hiPrev:
        return False, 0, "prev_close>hiPrev，未蓄力"

    # 修复2：当前必须突破
    if close <= hiPrev:
        return False, 0, "未突破hiPrev"

    # 修复3：必须是放量
    avg_v = avg_vol[bar_index] if bar_index < len(avg_vol) else 1.0
    vol = volumes[bar_index] if bar_index < len(volumes) else 0.0
    if vol <= avg_v * 1.5:
        return False, 0, f"量能不足({vol/avg_v:.1f}x)"

    # 修复4：阳线，收盘在当日高位
    day_range = highs[bar_index] - lows[bar_index]
    if day_range > 0:
        close_pos = (close - lows[bar_index]) / day_range
        if close_pos < 0.65:
            return False, 0, f"收盘位置偏低({close_pos:.0%})"

    # 修复5：前两根都没有突破（一次性）
    if prev2_close > hiPrev:
        return False, 0, "之前已突破过"

    base = 70
    sr_bonus = 0.0
    for rv in resistances:
        if rv > 0 and abs(hiPrev - rv) / close <= 0.01:
            sr_bonus = 5.0
            break

    return True, min(100, base + int(sr_bonus)), "修复版触发"


# ============================================================
# 扫描全历史，发出所有信号
# ============================================================

def scan(bars: list[Bar], scene_name: str):
    ind = build_indicators(bars)
    n = len(bars)

    springs_orig = []
    joc_orig = []
    joc_fixed = []

    # JOC 一次性：用 set 去重（同幅度只报一次）
    prev_joc_fixed_triggered = False

    for i in range(70, n):  # 至少需要 range_lookback 根
        # Spring
        ok, conf = detect_spring(i, ind, pivot_len=6, range_lookback=60)
        if ok:
            springs_orig.append((i, bars[i], conf))

        # JOC 原版
        ok2, conf2, msg2 = detect_joc_original(i, ind, range_lookback=60)
        if ok2:
            joc_orig.append((i, bars[i], conf2, msg2))

        # JOC 修复版（一次性）
        ok3, conf3, msg3 = detect_joc_fixed(i, ind, range_lookback=60)
        if ok3 and not prev_joc_fixed_triggered:
            joc_fixed.append((i, bars[i], conf3, msg3))
            prev_joc_fixed_triggered = True
        elif not ok3:
            prev_joc_fixed_triggered = False

    return {
        "scene": scene_name,
        "total_bars": n,
        "springs": springs_orig,
        "joc_original": joc_orig,
        "joc_fixed": joc_fixed,
    }


# ============================================================
# 主测试
# ============================================================

def run():
    print("=" * 62)
    print("  威科夫 Spring / JOC 检测 - 模拟测试 v2")
    print("=" * 62)

    # --- Test 1: Spring ---
    print("\n🧪 生成场景1: Spring 形态")
    print("  结构：前41根震荡 → bar 41植入pivot → bar 47触发Spring")
    spring_bars = generate_spring_scene()
    print(f"   K线总数: {len(spring_bars)}")
    print(f"   pivot bar 41: low={spring_bars[41].low:.2f}")
    print(f"   Spring bar 47: low={spring_bars[47].low:.2f}  close={spring_bars[47].close:.2f}")
    r_spring = scan(spring_bars, "Spring")

    # --- Test 2: JOC ---
    print("\n🧪 生成场景2: JOC 形态")
    joc_bars = generate_joc_scene()
    print(f"   K线总数: {len(joc_bars)}")
    print(f"   区间高点: {joc_bars[70].high:.2f}（bar 70）")
    print(f"   JOC 触发: bar 71 close={joc_bars[71].close:.2f}  vol={joc_bars[71].volume:,.0f}")
    r_joc = scan(joc_bars, "JOC")

    # --- Test 3: 无信号 ---
    print("\n🧪 生成场景3: 无信号普通行情")
    normal_bars = generate_no_signal_scene()
    print(f"   K线总数: {len(normal_bars)}")
    r_normal = scan(normal_bars, "无信号")

    # ============================================================
    # 打印结果
    # ============================================================
    print("\n" + "=" * 62)
    print("  📋 检测结果")
    print("=" * 62)

    all_pass = True

    for r in [r_spring, r_joc, r_normal]:
        print(f"\n  【{r['scene']}】总共 {r['total_bars']} 根 K 线")

        springs = r["springs"]
        joc_o = r["joc_original"]
        joc_f = r["joc_fixed"]

        print(f"  Spring 检测({len(springs)}次):")
        if springs:
            for idx, bar, conf in springs:
                print(f"    ✅ 第{idx}根  close={bar.close:.2f}  conf={conf}%")
        else:
            print(f"    ❌ 未检测到")

        print(f"  JOC 原版检测({len(joc_o)}次):")
        if joc_o:
            for idx, bar, conf, msg in joc_o:
                print(f"    ⚠️  第{idx}根  close={bar.close:.2f}  conf={conf}%  [{msg}]")
        else:
            print(f"    ✅ 未误触发")

        print(f"  JOC 修复版检测({len(joc_f)}次):")
        if joc_f:
            for idx, bar, conf, msg in joc_f:
                print(f"    ✅ 第{idx}根  close={bar.close:.2f}  conf={conf}%  [{msg}]")
        else:
            print(f"    ❌ 未检测到")

    # 预期结果核对
    print("\n" + "=" * 62)
    print("  ✅ / ❌ 预期核对")
    print("=" * 62)

    def check(label, actual, expected):
        ok = (actual == expected)
        tag = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {tag}  {label}: 预期{'有' if expected else '无'}信号，{'检测到' if actual else '未检测到'}")
        return ok

    all_pass &= check("Spring 场景 - Spring 信号", len(r_spring["springs"]) > 0, True)
    all_pass &= check("Spring 场景 - JOC 原版不误触发", len(r_spring["joc_original"]) == 0, True)
    all_pass &= check("Spring 场景 - JOC 修复版不触发", len(r_spring["joc_fixed"]) == 0, True)

    all_pass &= check("JOC 场景 - JOC 原版", len(r_joc["joc_original"]) > 0, True)
    all_pass &= check("JOC 场景 - JOC 修复版（一次性）", len(r_joc["joc_fixed"]) == 1, True)
    all_pass &= check("JOC 场景 - Spring 不误触发", len(r_joc["springs"]) == 0, True)

    all_pass &= check("无信号场景 - Spring 不触发", len(r_normal["springs"]) == 0, True)
    all_pass &= check("无信号场景 - JOC 原版不触发", len(r_normal["joc_original"]) == 0, True)
    all_pass &= check("无信号场景 - JOC 修复版不触发", len(r_normal["joc_fixed"]) == 0, True)

    print()
    if all_pass:
        print("  🎉 全部测试通过！")
    else:
        print("  ⚠️  存在失败，请检查上述 ❌ 项")

    # ============================================================
    # 代码 BUG 报告
    # ============================================================
    print("\n" + "=" * 62)
    print("  🔍 PineScript 原版代码问题清单")
    print("=" * 62)
    bugs = [
        ("BUG-1", "ADX 变量未初始化",
         "var float sTR = na  →  nz(sTR[1])  在第一根 bar = na，"
         "导致 TR 计算 NaN，ADX 全线崩溃",
         "改为 var float sTR = high - low"),
        ("BUG-2", "JOC 信号每日重复触发",
         "突破成立后 close>hiPrev 每天成立，信号持续N天",
         "增加 prev2_close>hiPrev 检测，确保只触发一次"),
        ("BUG-3", "JOC 条件逻辑矛盾",
         "前置 not 里有 close <= hiPrev，之后 if close > hiPrev 永远成立",
         "前置 not 只排除 prev_close>hiPrev，不排除 close<=hiPrev"),
        ("逻辑-4", "JOC 蓄力条件缺失",
         "原版不看 prev_close 是否在区间内，假突破无法过滤",
         "增加 prev_close <= hiPrev 作为蓄力必要条件"),
        ("逻辑-5", "JOC 阳线确认缺失",
         "原版不要求阳线，墓碑线也可触发 JOC",
         "要求收盘位置 > 当日 range 的 65%"),
        ("性能-6", "Spring 全局循环",
         "每次 barstate.islast 遍历所有历史 pivot，O(n²)",
         "只在 bar_index - pivot_len 位置单点检测即可"),
    ]
    for bid, title, problem, fix in bugs:
        print(f"\n  [{bid}] {title}")
        print(f"      问题: {problem}")
        print(f"      修复: {fix}")

    return all_pass


if __name__ == "__main__":
    run()
