//@version=6
indicator('威科夫Spring+JOC V1.0（修复版）', overlay=true, max_bars_back=5000, max_lines_count=500, max_labels_count=500)

// ===== 用户参数 =====
len20 = input.int(20, 'S/R 周期 20', group='支撑/阻力')
len60 = input.int(60, 'S/R 周期 60', group='支撑/阻力')
len120 = input.int(120, 'S/R 周期 120', group='支撑/阻力')
len240 = input.int(240, 'S/R 周期 240', group='支撑/阻力')
len480 = input.int(480, 'S/R 周期 480', group='支撑/阻力')
mergePct = input.float(0.3, '合并容差 %', minval=0.1, maxval=2.0, step=0.1, group='支撑/阻力') / 100
atrPeriod = input.int(14, 'ATR 周期', group='支撑/阻力')
pivotLen = input.int(6, 'Pivot 长度', group='威科夫信号')
volControl = input.bool(false, '成交量控制', group='威科夫信号')
volMulti = input.float(1.0, '成交量倍数', group='威科夫信号')
volRangeLen = input.int(20, '成交量均值周期', group='威科夫信号')
adxControl = input.bool(false, 'ADX 过滤', group='威科夫信号')
adxLen = input.int(14, 'ADX 周期', group='威科夫信号')
adxThreshold = input.float(25.0, 'ADX 阈值', group='威科夫信号')
rangeLookback = input.int(60, '盘整窗口', group='威科夫信号')
showSRZones = input.bool(true, '显示支撑/阻力', group='显示设置')
showSignals = input.bool(true, '显示威科夫信号', group='显示设置')
showRange = input.bool(true, '显示盘整区间', group='显示设置')

// ===== 预计算指标 =====
atr = ta.atr(atrPeriod)
avgVol = ta.sma(volume, volRangeLen)
meetsVolThresh = volume <= avgVol * volMulti

hi20 = ta.highest(high, len20)
lo20 = ta.lowest(low, len20)
hi60 = ta.highest(high, len60)
lo60 = ta.lowest(low, len60)
hi120 = ta.highest(high, len120)
lo120 = ta.lowest(low, len120)
hi240 = ta.highest(high, len240)
lo240 = ta.lowest(low, len240)
hi480 = ta.highest(high, len480)
lo480 = ta.lowest(low, len480)
rangeHigh = ta.highest(high, rangeLookback)
rangeLow = ta.lowest(low, rangeLookback)

// ========== 修复1：ADX 变量初始化 ==========
// 原版 BUG：var float sTR = na → nz(sTR[1]) 第一根 bar 返回 na → TR=NaN → ADX 崩溃
// 修复：用当天 range 初始化 sTR
var float sTR  = high - low
var float sDMP = 0.0
var float sDMM = 0.0

_tr  = math.max(high - low, math.abs(high - nz(close[1])), math.abs(low - nz(close[1])))
_dmp = (high - nz(high[1]) > nz(low[1]) - low) ? math.max(high - nz(high[1]), 0) : 0
_dmm = (nz(low[1]) - low > high - nz(high[1])) ? math.max(nz(low[1]) - low, 0) : 0
sTR  := nz(sTR[1])  - nz(sTR[1])  / adxLen + _tr
sDMP := nz(sDMP[1]) - nz(sDMP[1]) / adxLen + _dmp
sDMM := nz(sDMM[1]) - nz(sDMM[1]) / adxLen + _dmm
diP  = sDMP / sTR * 100
diM  = sDMM / sTR * 100
dx   = math.abs(diP - diM) / (diP + diM) * 100
customADX = ta.sma(dx, adxLen)

// ===== Pivot =====
calcHalf(w) => math.floor(w / 2)
_h20  = calcHalf(len20)
ph20  = ta.pivothigh(_h20, _h20)
pl20  = ta.pivotlow(_h20, _h20)
_h60  = calcHalf(len60)
ph60  = ta.pivothigh(_h60, _h60)
pl60  = ta.pivotlow(_h60, _h60)
_h120 = calcHalf(len120)
ph120 = ta.pivothigh(_h120, _h120)
pl120 = ta.pivotlow(_h120, _h120)
_h240 = calcHalf(len240)
ph240 = ta.pivothigh(_h240, _h240)
pl240 = ta.pivotlow(_h240, _h240)
_h480 = calcHalf(len480)
ph480 = ta.pivothigh(_h480, _h480)
pl480 = ta.pivotlow(_h480, _h480)

// ===== 结构体 =====
type SR
    float   price
    float   weight
    float   strength
    string  source
    string  kind

// ===== processSwingPoint =====
processSwingPoint(float p, int pivotBar, int half, string srcType, string kind, float w, array<SR> target, float ca) =>
    if not (na(p) or p <= 0)
        hiR = 0.0
        loR = 1e10
        for j = 1 to math.max(1, half)
            cb = pivotBar - j
            if cb >= 0 and cb <= bar_index and cb < 5000
                hiR := math.max(hiR, high[cb])
                loR := math.min(loR, low[cb])
        for j = 0 to math.max(1, half)
            cb = pivotBar + j
            if cb <= bar_index and cb < 5000
                hiR := math.max(hiR, high[cb])
                loR := math.min(loR, low[cb])
        if hiR > 0 and loR < 1e9 and hiR - loR > ca * 0.5 and ca > 0
            array.push(target, SR.new(p, w, 0.0, srcType, kind))

// ===== processCluster =====
processCluster(array<SR> cl, float ps, float ws, array<string> srcs, bool isSup, float lp, array<SR> ma) =>
    if ws > 0 and array.size(cl) > 0
        mp = ps / ws
        if mp > 0
            lb = 0.0
            for k = 0 to array.size(cl) - 1
                m = array.get(cl, k)
                lb += (m.weight >= 5.0) ? 5.0 : (m.weight >= 4.0) ? 4.0 : (m.weight >= 3.0) ? 3.0 : (m.weight >= 2.0) ? 2.0 : (m.weight >= 1.0) ? 1.0 : 0.0
            sb = array.size(srcs) >= 3 ? 3.0 : 0.0
            tb = 0.0
            if bar_index >= 60
                touches = 0
                for k = 0 to math.min(60, bar_index) - 1
                    tp = isSup ? low[k] : high[k]
                    if tp > 0 and math.abs(tp - mp) / mp <= 0.01
                        touches += 1
                tb := math.min(touches * 0.5, 5.0)
            fs = array.size(cl) + lb + sb + tb
            ks = isSup ? "support" : "resistance"
            array.push(ma, SR.new(mp, 1.0, fs, array.join(srcs, "+"), ks))

// ===== calcSR =====
calcSR() =>
    s = array.new<SR>()
    r = array.new<SR>()
    periods  = array.from(len20, len60, len120, len240, len480)
    weights = array.from(1.0, 2.0, 3.0, 4.0, 5.0)
    hiVals  = array.from(hi20, hi60, hi120, hi240, hi480)
    loVals  = array.from(lo20, lo60, lo120, lo240, lo480)
    ca = atr
    if ca <= 0
        [s, r]
    for idx = 0 to array.size(periods) - 1
        w      = array.get(periods, idx)
        weight = array.get(weights, idx)
        hiW    = array.get(hiVals, idx)
        loW    = array.get(loVals, idx)
        if bar_index < w or w <= 0
            continue
        half = calcHalf(w)
        if half <= 0
            continue
        midP = (hiW + loW) / 2
        if not (na(hiW) or na(loW) or hiW <= 0 or loW <= 0 or hiW < loW)
            for i = 0 to half * 2
                if i <= bar_index and bar_index - i >= 0
                    if w == len20
                        if not na(ph20[i]) and ph20[i] > 0
                            processSwingPoint(ph20[i], bar_index - i, half, "Swing_High", "resistance", weight, r, ca)
                        if not na(pl20[i]) and pl20[i] > 0
                            processSwingPoint(pl20[i], bar_index - i, half, "Swing_Low",  "support",    weight, s, ca)
                    if w == len60
                        if not na(ph60[i]) and ph60[i] > 0
                            processSwingPoint(ph60[i], bar_index - i, half, "Swing_High", "resistance", weight, r, ca)
                        if not na(pl60[i]) and pl60[i] > 0
                            processSwingPoint(pl60[i], bar_index - i, half, "Swing_Low",  "support",    weight, s, ca)
                    if w == len120
                        if not na(ph120[i]) and ph120[i] > 0
                            processSwingPoint(ph120[i], bar_index - i, half, "Swing_High", "resistance", weight, r, ca)
                        if not na(pl120[i]) and pl120[i] > 0
                            processSwingPoint(pl120[i], bar_index - i, half, "Swing_Low",  "support",    weight, s, ca)
                    if w == len240
                        if not na(ph240[i]) and ph240[i] > 0
                            processSwingPoint(ph240[i], bar_index - i, half, "Swing_High", "resistance", weight, r, ca)
                        if not na(pl240[i]) and pl240[i] > 0
                            processSwingPoint(pl240[i], bar_index - i, half, "Swing_Low",  "support",    weight, s, ca)
                    if w == len480
                        if not na(ph480[i]) and ph480[i] > 0
                            processSwingPoint(ph480[i], bar_index - i, half, "Swing_High", "resistance", weight, r, ca)
                        if not na(pl480[i]) and pl480[i] > 0
                            processSwingPoint(pl480[i], bar_index - i, half, "Swing_Low",  "support",    weight, s, ca)
        // VPOC
        if hiW > loW and hiW - loW > ca * 0.5
            nBins = math.max(10, math.min(30, math.floor(w / 3)))
            if nBins > 0
                bSize = (hiW - loW) / nBins
                if bSize > 0
                    vp = array.new_float(nBins, 0.0)
                    startBar = math.max(0, bar_index - w + 1)
                    for k = startBar to bar_index
                        rng = high[k] - low[k]
                        if rng > 0
                            for b = 0 to nBins - 1
                                bLo = loW + b * bSize
                                bHi = bLo + bSize
                                oL  = math.max(low[k], bLo)
                                oH  = math.min(high[k], bHi)
                                if oH > oL
                                    v = array.get(vp, b)
                                    array.set(vp, b, v + volume[k] * (oH - oL) / rng)
                    maxV = -1.0
                    maxI = 0
                    for b = 0 to nBins - 1
                        v = array.get(vp, b)
                        if v > maxV
                            maxV := v
                            maxI := b
                    if maxV > 0
                        pocLo = loW + maxI * bSize
                        pocHi = pocLo + bSize
                        if pocLo > 0 and pocHi > 0
                            array.push(r, SR.new(pocHi, weight, 0.0, "VPOC", "resistance"))
                            array.push(s, SR.new(pocLo, weight, 0.0, "VPOC", "support"))
        // Range
        if midP > 0 and (hiW - loW) / midP < 0.15
            array.push(r, SR.new(hiW, weight, 0.0, "Range", "resistance"))
            array.push(s, SR.new(loW, weight, 0.0, "Range", "support"))
    [s, r]

// ===== topSR =====
topSR(array<SR> candidates, bool isSup) =>
    if array.size(candidates) > 0
        cc = close
        filtered = array.new<SR>()
        for i = 0 to array.size(candidates) - 1
            c = array.get(candidates, i)
            if not na(c.price) and c.price > 0.0 and math.abs(c.price - cc) / cc <= 0.5
                array.push(filtered, c)
        nf = array.size(filtered)
        if nf > 0
            sorted = array.copy(filtered)
            if nf >= 2
                for i = 0 to nf - 2
                    for j = i + 1 to nf - 1
                        ai = array.get(sorted, i)
                        bj = array.get(sorted, j)
                        cond = isSup ? ai.price > bj.price : ai.price < bj.price
                        if cond
                            tmp = ai
                            array.set(sorted, i, bj)
                            array.set(sorted, j, tmp)
            merged = array.new<SR>()
            cluster = array.new<SR>()
            cPSum = 0.0
            cWSum = 0.0
            cSrcs = array.new_string()
            lastP = 0.0
            for i = 0 to nf - 1
                sr = array.get(sorted, i)
                if na(sr.price) or sr.price <= 0.0
                    continue
                same = (i > 0) and (math.abs(sr.price - lastP) <= mergePct * cc)
                if same
                    array.push(cluster, sr)
                    cPSum += sr.price * sr.weight
                    cWSum += sr.weight
                    if not array.includes(cSrcs, sr.source)
                        array.push(cSrcs, sr.source)
                else
                    if i > 0
                        processCluster(cluster, cPSum, cWSum, cSrcs, isSup, lastP, merged)
                    cluster := array.new<SR>()
                    cPSum := 0.0
                    cWSum := 0.0
                    cSrcs := array.new_string()
                    lastP := sr.price
                    array.push(cSrcs, sr.source)
                    array.push(cluster, sr)
                    cPSum += sr.price * sr.weight
                    cWSum += sr.weight
            if array.size(cluster) > 0 and cWSum > 0.0
                processCluster(cluster, cPSum, cWSum, cSrcs, isSup, lastP, merged)
            mgmtSize = array.size(merged)
            if mgmtSize >= 2
                for i = 0 to mgmtSize - 2
                    for j = i + 1 to mgmtSize - 1
                        ai = array.get(merged, i)
                        bj = array.get(merged, j)
                        if ai.strength < bj.strength
                            tmp = ai
                            array.set(merged, i, bj)
                            array.set(merged, j, tmp)
            limit = math.min(5, mgmtSize)
            result = array.new<SR>()
            for i = 0 to limit - 1
                array.push(result, array.get(merged, i))
            result
        else
            array.new<SR>()
    else
        array.new<SR>()

// ========== 修复2：JOC 一次性触发的全局状态 ==========
// prevJocBar：float 类型，na=从未触发；通过 detectJOC 返回值在主逻辑层更新
var float prevJocBar = na

// ===== 威科夫信号检测 =====

// Spring
// 修复：直接取 bar_index-pivotLen 位置的 low 作为 pp，无需依赖 pivot_lows[bar_index]
detectSpring(array<SR> supp) =>
    springSig  = false
    springConf = 0
    pp = low[pivotLen]
    if not (na(pp) or pp <= 0 or bar_index < pivotLen)
        tCount = 0
        for j = bar_index - pivotLen to bar_index
            if j >= 0 and low[j] < pp and not na(low[j])
                tCount += 1
        if tCount <= 3 and low < pp and close > pp and low <= rangeLow and not na(rangeLow)
            baseConf = 55
            if low < rangeLow and close > pp
                baseConf += 10
            if volControl and meetsVolThresh
                baseConf += 5
            if not adxControl or (not na(customADX) and customADX < adxThreshold)
                baseConf += 5
            srBonus = 0.0
            if array.size(supp) > 0 and close > 0 and not na(close)
                for si = 0 to array.size(supp) - 1
                    lv = array.get(supp, si)
                    if not na(lv.price) and lv.price > 0
                         and math.abs(pp - lv.price) / close <= 0.005
                        srBonus := 5.0
                        break
            springSig  := true
            springConf := math.min(100, baseConf + int(srBonus))
    [springSig, springConf]

// JOC
// 修复3：移除原版 close<=hiPrev 的矛盾
// 修复4：强制放量（不看 volControl）
// 修复5：阳线确认（收盘位置 >= 65%）
// 修复2：prevJocBar 作为 float var，全局更新
detectJOC(array<SR> resi) =>
    jocSig    = false
    jocConf   = 0
    float newJocBar = na   // float 类型才能赋 na

    if bar_index >= rangeLookback and rangeLookback > 0
        hiPrev = rangeHigh[1]

        // 修复3：移除 close<=hiPrev；只检查前收是否在区间内（蓄力）
        bool notValid = na(hiPrev) or hiPrev <= 0
             or na(close[1])
             or close[1] > hiPrev                                    // 前收在区间内 = 蓄力
             or math.abs(close[1] - hiPrev) / hiPrev > 0.05            // 前收偏离不超过 5%

        if not notValid and close > hiPrev
            // 修复4：强制放量
            if avgVol > 0 and volume > avgVol * 1.5
                // 修复5：阳线确认
                float dayRange = high - low
                float closePos  = dayRange > 0 ? (close - low) / dayRange : 0.0
                if closePos >= 0.65
                    // 修复2：一次性触发（同幅度 ±1%，5根内不重复）
                    bool sameZone = not na(prevJocBar)
                         and bar_index - int(prevJocBar) > 0
                         and bar_index - int(prevJocBar) <= 5
                         and hiPrev > 0
                         and math.abs(hiPrev - rangeHigh[int(prevJocBar)]) / hiPrev < 0.01

                    if not sameZone
                        baseConf = 70
                        srBonus = 0.0
                        if array.size(resi) > 0 and close > 0 and not na(close)
                            for ri = 0 to array.size(resi) - 1
                                lv = array.get(resi, ri)
                                if not na(lv.price) and lv.price > 0
                                     and math.abs(hiPrev - lv.price) / close <= 0.01
                                    srBonus := 5.0
                                    break
                        jocSig    := true
                        jocConf   := math.min(100, baseConf + int(srBonus))
                        newJocBar := float(bar_index)

    [jocSig, jocConf, newJocBar]

// ===== 主逻辑 =====
[rawSupp, rawResi] = calcSR()
supports    = topSR(rawSupp, true)
resistances = topSR(rawResi, false)
[springSig, springConf]   = detectSpring(supports)
[jocSig, jocConf, newBar] = detectJOC(resistances)

// 全局 var 在主逻辑层更新（此处是全局作用域，:= 合法）
if not na(newBar) and newBar > 0
    prevJocBar := newBar

// ===== 绘图对象管理 =====
var line[]  hLines     = array.new_line()
var line[]  sLines     = array.new_line()
var label[] springLbls = array.new_label()
var label[] jocLbls    = array.new_label()
var table   infoTable  = table.new(position.top_right, 3, 2)

// ===== 绘图主逻辑 =====
if barstate.islast
    // 清理旧对象
    if array.size(hLines) > 0
        for ln in hLines
            line.delete(ln)
        array.clear(hLines)
    if array.size(sLines) > 0
        for ln in sLines
            line.delete(ln)
        array.clear(sLines)
    if array.size(springLbls) > 0
        for lbl in springLbls
            label.delete(lbl)
        array.clear(springLbls)
    if array.size(jocLbls) > 0
        for lbl in jocLbls
            label.delete(lbl)
        array.clear(jocLbls)

    // 绘制阻力线
    if showSRZones and array.size(resistances) > 0
        for i = 0 to array.size(resistances) - 1
            lv = array.get(resistances, i)
            if not na(lv.price) and lv.price > 0
                // v6：不写类型前缀，直接赋值
                c = lv.strength >= 8 ? color.new(color.red, 0) : color.new(color.red, 50)
                line newLine = line.new(bar_index, lv.price, bar_index + 20, lv.price,
                                        color=c, width=2, extend=extend.right)
                array.push(hLines, newLine)

    // 绘制支撑线
    if showSRZones and array.size(supports) > 0
        for i = 0 to array.size(supports) - 1
            lv = array.get(supports, i)
            if not na(lv.price) and lv.price > 0
                c = lv.strength >= 8 ? color.new(color.green, 0) : color.new(color.green, 50)
                line newLine = line.new(bar_index, lv.price, bar_index + 20, lv.price,
                                        color=c, width=2, extend=extend.right)
                array.push(sLines, newLine)

    // 绘制信号标签
    if showSignals
        if springSig and low > 0
            l = label.new(bar_index, low * 0.998, 'SPRING\n' + str.tostring(springConf) + '%',
                          color=color.new(color.green, 0), textcolor=color.white,
                          style=label.style_label_up)
            array.push(springLbls, l)
        if jocSig and high > 0
            l = label.new(bar_index, high * 1.002, 'JOC\n' + str.tostring(jocConf) + '%',
                          color=color.new(color.blue, 0), textcolor=color.white,
                          style=label.style_label_down)
            array.push(jocLbls, l)

// 盘整区间 Plot & Fill
// fill() 需要 plot 对象，直接赋值（不能写 "plot rlPlot ="，那会报类型错误）
rlPlot = plot(showRange and not na(rangeLow) and rangeLow > 0 ? rangeLow : na,
              '区间低', color=color.new(color.gray, 50), linewidth=2)
rhPlot = plot(showRange and not na(rangeHigh) and rangeHigh > 0 ? rangeHigh : na,
              '区间高', color=color.new(color.gray, 50), linewidth=2)
fill(rlPlot, rhPlot, color=color.new(color.blue, 95))
bgcolor(springSig ? color.new(color.green, 90) : na, title="Spring背景")
bgcolor(jocSig     ? color.new(color.blue, 90)  : na, title="JOC背景")

// 信号面板
if barstate.islast
    table.clear(infoTable, 0, 0)
    table.cell(infoTable, 0, 0, "威科夫分析",    bgcolor=color.new(color.blue, 80),   text_color=color.white)
    table.cell(infoTable, 1, 0, "支撑: " + str.tostring(array.size(supports)),
                                                    bgcolor=color.new(color.green, 80), text_color=color.white)
    table.cell(infoTable, 2, 0, "阻力: " + str.tostring(array.size(resistances)),
                                                    bgcolor=color.new(color.red, 80),   text_color=color.white)
    table.cell(infoTable, 0, 1, "信号状态:",     bgcolor=color.new(color.gray, 80),   text_color=color.white)
    // 三元表达式：v6 支持内联声明
    sigTxt = springSig ? "Spring: " + str.tostring(springConf) + "%"
          : jocSig     ? "JOC: " + str.tostring(jocConf) + "%"
          : "等待信号"
    sigBg  = springSig ? color.new(color.green, 70)
          : jocSig     ? color.new(color.blue, 70)
          : color.new(color.gray, 70)
    table.cell(infoTable, 1, 1, sigTxt, bgcolor=sigBg, text_color=color.white)
    table.cell(infoTable, 2, 1, "Bar: " + str.tostring(bar_index),
                                                    bgcolor=color.new(color.gray, 80), text_color=color.white)

// ===== 警报 =====
alertcondition(springSig, title='威科夫弹簧信号', message="威科夫弹簧信号出现")
alertcondition(jocSig,     title='威科夫JOC信号',  message="威科夫JOC信号出现")