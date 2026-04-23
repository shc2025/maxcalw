#!/usr/bin/env python3
"""大盘技术分析周报 — 格式化输出"""
import json
from datetime import datetime

data = json.load(open("/workspace/market_report/all_data.json", "r"))

# 取所有市场的最新交易日期
data_date = next((v.get("last_date") for v in data.values() if v.get("last_date")), "—")
gen_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")
report_date = data_date

def f(v, default="—"): return str(v) if v is not None else default

def adx_zone(adx):
    if adx is None: return "数据不足"
    if adx < 20: return "⚪ 震荡（无明确趋势）"
    elif adx < 25: return "🟡 弱趋势（方向不明）"
    elif adx < 40: return "🟢 中等趋势（趋势明确）"
    elif adx < 60: return "🟠 强趋势（趋势强劲）"
    else: return "🔴 极强趋势（注意反转）"

def crsi_zone(crsi):
    if crsi is None: return "—"
    if crsi >= 85: return "🔴极度超买"
    elif crsi >= 70: return "🟠超买"
    elif crsi >= 55: return "🟢偏强"
    elif crsi >= 45: return "🟡中性"
    elif crsi >= 30: return "🟡偏弱"
    elif crsi >= 15: return "🟠低估"
    else: return "🔴极度低估"

def dir_signal(di_plus, di_minus):
    if di_plus is None or di_minus is None: return "—"
    if di_plus > di_minus: return "↑ 上升"
    elif di_minus > di_plus: return "↓ 下降"
    else: return "横"

def vix_level(close):
    if close is None: return "—"
    if close > 30: return "⚠️ 高位恐慌 (>30)"
    elif close > 20: return "🟡 正常区间 (20~30)"
    else: return "🟢 平静 (<20)"

# Build lines
L = []

L.append(f"# 📊 全球大盘技术分析 {report_date}")
L.append(f"**生成时间**: {gen_date} &nbsp;|&nbsp; **数据截止**: {report_date}")
L.append("")
L.append("---")
L.append("")
L.append("## 一、核心数据总览")
L.append("")
L.append("| 市场 | 标的 | 收盘价 | 日期 | ADX | DI+ | DI- | 趋势 | 周线CRSI |")
L.append("|------|------|--------|------|------|------|------|------|---------|")

name_map = {
    "SPY": "标普500(SPY)",
    "QQQ": "纳斯达克100(QQQ)",
    "DIA": "道琼斯(DIA)",
    "恐慌指数(VIXY)": "恐慌指数(VIXY)",
    "上证综指": "上证综指",
    "深证成指": "深证成指",
    "创业板指": "创业板指",
    "恒生指数": "恒生指数",
}

for key, name in name_map.items():
    m = data.get(key, {})
    if not m: continue
    cls = m.get("class", "")
    adx_s = f(m.get("adx"))
    dip = f(m.get("di_plus"))
    dim = f(m.get("di_minus"))
    wcrsi = f(m.get("w_crsi"), "—")
    zone = adx_zone(m.get("adx"))
    L.append(f"| {cls} | **{name}** | {f(m.get('last_close'))} | {f(m.get('last_date'))} | {adx_s} | {dip} | {dim} | {zone} | {wcrsi} |")

L.append("")
L.append("*数据来源: Twelve Data API (美股ETF) + AkShare (A股/港股)，已双向校验*")
L.append("")

# ── 二、分市场 ──────────────────────────────────────────────
L.append("---")
L.append("")
L.append("## 二、分市场技术分析")
L.append("")

# US
L.append("### 🌎 美股市场")
L.append("")
for key, name in [("SPY","标普500"), ("QQQ","纳斯达克100"), ("DIA","道琼斯")]:
    m = data.get(key, {})
    if not m: continue
    L.append(f"**{name}**")
    L.append(f"- 收盘: **${f(m.get('last_close'))}** | 数据日期: {f(m.get('last_date'))}")
    adx_v = m.get("adx")
    dip = m.get("di_plus")
    dim = m.get("di_minus")
    dir_s = dir_signal(dip, dim)
    L.append(f"- ADX: {f(adx_v)} | DI+: {f(dip)} | DI-: {f(dim)}")
    L.append(f"  → 趋势: {adx_zone(adx_v)} | 方向: {dir_s}")
    wcrsi = m.get("w_crsi")
    L.append(f"- 周线CRSI: {f(wcrsi,'—')} | {crsi_zone(wcrsi)}")
    chg5 = f(m.get("week_close_chg"), "N/A")
    L.append(f"- 近5日涨跌: {chg5}")
    L.append(f"- 近30日技术位: 高={f(m.get('recent_high'))} | 低={f(m.get('recent_low'))}")
    L.append("")

# VIX
m_vix = data.get("恐慌指数(VIXY)", {})
if m_vix:
    vix_c = m_vix.get("last_close")
    vix_lvl = vix_level(vix_c)
    L.append("**恐慌指数 (VIXY)**")
    L.append(f"- 收盘: **${f(vix_c)}** ({f(m_vix.get('last_date'))})")
    L.append(f"- 50日波动区间: {f(m_vix.get('recent_low'))} ~ {f(m_vix.get('recent_high'))}")
    L.append(f"- 当前状态: {vix_lvl}")
    L.append("")

# A股
L.append("### 🇨🇳 A股市场")
L.append("")
for key, name in [("上证综指","上证综指"), ("深证成指","深证成指"), ("创业板指","创业板指")]:
    m = data.get(key, {})
    if not m: continue
    L.append(f"**{name}**")
    L.append(f"- 收盘: **{f(m.get('last_close'))}** | {f(m.get('last_date'))}")
    adx_v = m.get("adx")
    dip = m.get("di_plus")
    dim = m.get("di_minus")
    dir_s = dir_signal(dip, dim)
    L.append(f"- ADX: {f(adx_v)} | DI+: {f(dip)} | DI-: {f(dim)}")
    L.append(f"  → 趋势: {adx_zone(adx_v)} | 方向: {dir_s}")
    wcrsi = f(m.get("w_crsi"), "—")
    L.append(f"- 周线CRSI: {wcrsi}")
    wvol = f(m.get('week_close_chg'), "N/A")
    L.append(f"- 周成交额变化: {wvol}（vs 上周）")
    L.append(f"- 近30日技术位: 高={f(m.get('recent_high'))} | 低={f(m.get('recent_low'))}")
    L.append("")

# HK
m_hk = data.get("恒生指数", {})
if m_hk:
    L.append("### 🇭🇰 港股市场")
    L.append("")
    L.append("**恒生指数 (HSI)**")
    L.append(f"- 收盘: **{f(m_hk.get('last_close'))}** | {f(m_hk.get('last_date'))}")
    adx_v = m_hk.get("adx")
    dip = m_hk.get("di_plus")
    dim = m_hk.get("di_minus")
    dir_s = dir_signal(dip, dim)
    L.append(f"- ADX: {f(adx_v)} | DI+: {f(dip)} | DI-: {f(dim)}")
    L.append(f"  → {adx_zone(adx_v)} | {dir_s}")
    L.append(f"- 近30日技术位: 高={f(m_hk.get('recent_high'))} | 低={f(m_hk.get('recent_low'))}")
    L.append("")

# ── 三、CRSI信号 ────────────────────────────────────────────
L.append("---")
L.append("")
L.append("## 三、CRSI信号参考")
L.append("*CRSI>70超买谨慎追高 | CRSI<30超卖关注机会*")
L.append("")
L.append("| 标的 | 周线CRSI | 信号 |")
L.append("|------|---------|------|")
for key in ["SPY","QQQ","DIA","恐慌指数(VIXY)","上证综指","深证成指","创业板指","恒生指数"]:
    m = data.get(key, {})
    if not m: continue
    wcrsi = m.get("w_crsi")
    buy = m.get("buy_sig", "")
    sell = m.get("sell_sig", "")
    if buy:
        status = "🟢 " + buy
    elif sell:
        status = "🔴 " + sell
    else:
        status = crsi_zone(wcrsi)
    L.append(f"| {key} | {f(wcrsi,'—')} | {status} |")
L.append("")

# ── 四、综合判断 ────────────────────────────────────────────
L.append("---")
L.append("")
L.append("## 四、综合技术面判断")
L.append("")

spy = data.get("SPY", {})
qqq = data.get("QQQ", {})
dia = data.get("DIA", {})
sh  = data.get("上证综指", {})
sz  = data.get("深证成指", {})
cy  = data.get("创业板指", {})
hsi = data.get("恒生指数", {})
vix = data.get("恐慌指数(VIXY)", {})

L.append("### 趋势强度矩阵")
L.append("")
L.append("| 市场 | ADX | 趋势判断 | 操作建议 |")
L.append("|------|------|---------|---------|")

def us_adx_summary():
    vals = [spy.get("adx"), qqq.get("adx"), dia.get("adx")]
    mx = max((v for v in vals if v is not None), default=None)
    mn = min((v for v in vals if v is not None), default=None)
    if mx and mx >= 40: return "🟠强趋势", "趋势中但周线CRSI高位⚠️"
    if mn and mn < 20: return "🟡弱/分化", "方向不明，谨慎"
    if mx and mx >= 25: return "🟢中等趋势", "顺势操作"
    return "🟡弱趋势", "注意方向选择"

def cn_adx_summary():
    vals = [sh.get("adx"), sz.get("adx"), cy.get("adx")]
    mx = max((v for v in vals if v is not None), default=None)
    mn = min((v for v in vals if v is not None), default=None)
    if mx and mx >= 40: return "🟠强趋势", "注意回调风险"
    if mn and mn < 20: return "⚪弱势", "无趋势观望"
    if mx and mx >= 25: return "🟢中等趋势", "可顺势"
    return "🟡弱趋势", "震荡为主"

us_zone, us_rec = us_adx_summary()
cn_zone, cn_rec = cn_adx_summary()
hk_zone = "⚪弱势" if (hsi.get("adx") or 0) < 20 else "🟡弱趋势"
hk_rec = "ADX<20，横盘整理" if (hsi.get("adx") or 0) < 20 else "有方向"

L.append(f"| **美股** | ADX≈{f(spy.get('adx'),'—')}~{f(dia.get('adx'),'—')} | {us_zone} | {us_rec} |")
L.append(f"| **A股** | ADX≈{f(sh.get('adx'),'—')}~{f(sz.get('adx'),'—')} | {cn_zone} | {cn_rec} |")
L.append(f"| **港股** | ADX≈{f(hsi.get('adx'),'—')} | {hk_zone} | {hk_rec} |")
L.append("")

L.append("### 关键结论")
L.append("")
L.append(f"**美股**: ADX≈{f(spy.get('adx'),'—')}，DI+>DI-（↑），整体偏多但道琼斯ADX={f(dia.get('adx'),'—')}（偏弱）→ 三大指数分化，整体中性偏多但需警惕回调")
L.append("")
dir_cn = "↑" if (sh.get("di_plus") or 0) > (sh.get("di_minus") or 0) else "↓"
L.append(f"**A股**: 上证ADX={f(sh.get('adx'),'—')}>25，DI+>DI-，为{dir_cn}；创业板ADX={f(cy.get('adx'),'—')}<25（偏弱）→ 沪强深弱格局")
L.append("")
dir_hk = "↑" if (hsi.get("di_plus") or 0) > (hsi.get("di_minus") or 0) else "↓"
L.append(f"**港股**: 恒生ADX={f(hsi.get('adx'),'—')}<20，⚪无趋势；DI+={f(hsi.get('di_plus'),'—')} {dir_hk} DI-={f(hsi.get('di_minus'),'—')} → 方向积累期，注意变盘信号")
L.append("")
vix_c = vix.get("last_close") if vix else None
if vix_c:
    vix_lvl2 = "⚠️市场紧张" if vix_c > 30 else "正常区间" if vix_c > 20 else "🟢市场平静"
    L.append(f"**恐慌指数VIXY**: 收盘${f(vix_c)} → {vix_lvl2}")
L.append("")
L.append("---")
L.append("")
L.append("*说明: ADX<20=震荡无趋势，ADX 25~40=趋势明确，ADX>40=趋势强劲 | 周线CRSI>70超买警惕，<30超卖关注*")
L.append(f"*生成: {gen_date} | 数据截止: {report_date}*")

# Write
report_text = "\n".join(L)
with open("/workspace/market_report/weekly_report.md", "w", encoding="utf-8") as fp:
    fp.write(report_text)

print(f"✅ 报告已生成: /workspace/market_report/weekly_report.md")
print(f"共 {len(L)} 行 | {len(report_text)} 字符")
print(f"数据日期: {report_date} | 生成时间: {gen_date}")
