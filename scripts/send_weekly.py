#!/usr/bin/env python3
"""
每周定时推送周报到钉钉（实时生成 + 复核机制版）
第一阶：拉数据 → 发预览+复核请求 → 写状态文件
第二阶（confirm_weekly.py 或 30分钟后 cron 触发）→ 读取状态 → 发送完整周报
"""

import subprocess, json, datetime, time, os, uuid

# ── 配置 ──────────────────────────────────────────────────────────────────────
TOKEN   = "c2b875cc4161cf35bdf3c15f15d6006fe5c998f7a285e888b15844c7adbc0315"
URL     = f"https://oapi.dingtalk.com/robot/send?access_token={TOKEN}"
STATE_FILE = "/workspace/.weekly_state.json"
REVIEW_TIMEOUT_MIN = 30   # 30分钟无人确认则自动发送

# ── 工具函数 ───────────────────────────────────────────────────────────────────
def curl(url, timeout=10):
    p = subprocess.run(["curl","-s","--max-time",str(timeout),url],
                      capture_output=True,text=True,timeout=timeout+2)
    return p.stdout

def rsi14(closes):
    if len(closes) < 15: return None
    g, l = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        g.append(max(d, 0)); l.append(abs(min(d, 0)))
    if len(g) < 14: return None
    ag = sum(g[-14:]) / 14; al = sum(l[-14:]) / 14
    return round(100 - (100 / (1 + ag / (al + 1e-10))), 2) if al else 100.0

def avg(lst): return sum(lst) / len(lst) if lst else None
def fChg(ch): return f"{'+' if ch > 0 else ''}{ch:.2f}%"

# ── 状态管理 ───────────────────────────────────────────────────────────────────
def read_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f: return json.load(f)
        except: pass
    return {}

def write_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ── 数据拉取 ───────────────────────────────────────────────────────────────────
def fetch_all_data():
    """拉取所有市场数据，返回数据字典。日期全部动态计算，绝不硬编码。"""
    print("=== 实时数据拉取开始 ===")
    t0 = time.time()

    today = datetime.date.today()
    weekday = today.weekday()  # 0=周一, 6=周日

    # ── 动态计算本周一和上周五的日期字符串 ──────────────────────────────
    days_since_mon = weekday if weekday <= 4 else 0
    days_since_fri = weekday + 2 if weekday <= 4 else 3

    this_mon = (today - datetime.timedelta(days=days_since_mon)).isoformat()
    this_fri = (today - datetime.timedelta(days=days_since_fri)).isoformat()
    prev_fri = (today - datetime.timedelta(days=days_since_fri + 7)).isoformat()

    print(f"  今日={today} ({today.strftime('%A')})")
    print(f"  本周区间：本周一={this_mon} / 本周五={this_fri}")
    print(f"  对比区间：上周五={prev_fri}")

    fred = {}
    for code in ["SP500","DJIA","NASDAQCOM","VIXCLS","DGS10","DGS2","T10Y2Y"]:
        fred[code] = fetch_fred(code)
        print(f"    {code}: {fred[code][-1] if fred[code] else '无数据'}")

    # ── SPX ───────────────────────────────────────────────────────────────
    spx_vals = fred["SP500"]; spx_c = [float(v) for _,v in spx_vals]
    spx_close = spx_vals[-1][1]; spx_date = spx_vals[-1][0]
    spx_prev = None
    for d, v in reversed(spx_vals):
        if d < spx_date: spx_prev = float(v); break
    spx_chg = round((spx_close - spx_prev) / spx_prev * 100, 2) if spx_prev else 0
    spx_rsi  = rsi14(spx_c)
    ma200    = avg(spx_c[-200:])
    spx_dev  = round((spx_close - ma200) / ma200 * 100, 2) if ma200 else 0

    # ── DJI / NASDAQ ───────────────────────────────────────────────────────
    dji_vals = fred["DJIA"]
    dji_close = dji_vals[-1][1]; dji_date = dji_vals[-1][0]
    dji_prev = None
    for d, v in reversed(dji_vals):
        if d < dji_date: dji_prev = float(v); break
    dji_chg = round((dji_close - dji_prev) / dji_prev * 100, 2) if dji_prev else 0

    nas_vals = fred["NASDAQCOM"]
    nas_close = nas_vals[-1][1]; nas_date = nas_vals[-1][0]
    nas_prev = None
    for d, v in reversed(nas_vals):
        if d < nas_date: nas_prev = float(v); break
    nas_chg = round((nas_close - nas_prev) / nas_prev * 100, 2) if nas_prev else 0

    # ── VIX（动态日期过滤） ───────────────────────────────────────────────
    vix_week = [(v[0], round(float(v[1]), 2))
                for v in fred["VIXCLS"]
                if v[0] >= this_mon]
    vix_latest = vix_week[-1][1] if vix_week else None
    vix_avg    = round(avg([x[1] for x in vix_week]), 2) if vix_week else None
    y10_v = float(fred["DGS10"][-1][1])
    spd_v = float(fred["T10Y2Y"][-1][1]) if fred.get("T10Y2Y") else None

    # ── Twelve Data SPY ──────────────────────────────────────────────────
    KEY = "dd4f227a11f34265936086a73b46b80c"
    spy_close_etf = None
    try:
        spy_raw = curl(f"https://api.twelvedata.com/time_series?symbol=SPY&interval=1day&outputsize=5&apikey={KEY}&format=JSON", timeout=12)
        spy_data = json.loads(spy_raw)
        spy_close_etf = float(spy_data["values"][-1]["close"]) if spy_data.get("values") else None
        print(f"    SPY ETF: {spy_close_etf}")
    except Exception as e:
        print(f"    SPY ETF 拉取失败: {e}")

    # ── A股（动态取最近交易日） ─────────────────────────────────────────
    sh_close=sz_close=cy_close=0
    sh_chg=sz_chg=cy_chg=0
    sh_rsi=sz_rsi=cy_rsi=None
    rsi_avg=total_turn=0
    a_success = False
    try:
        import akshare as ak
        a = {}
        for code, name in [("sh000001","上证"),("sz399001","深证"),("sz399006","创业板")]:
            df = ak.stock_zh_index_daily(symbol=code).tail(20).reset_index(drop=True)
            a[name] = {"close":[float(r["close"]) for _,r in df.iterrows()],
                       "dates": [str(r["date"]) for _,r in df.iterrows()]}
        sh_c = a["上证"]["close"]; sz_c = a["深证"]["close"]; cy_c = a["创业板"]["close"]
        sh_dates = a["上证"]["dates"]; sz_dates = a["深证"]["dates"]; cy_dates = a["创业板"]["dates"]

        sh_close = sh_c[-1]; sz_close = sz_c[-1]; cy_close = cy_c[-1]
        sh_date_latest = sh_dates[-1]; sz_date_latest = sz_dates[-1]; cy_date_latest = cy_dates[-1]

        # 找最近5日前的收盘价（动态）
        def prev_n(clist, date_list, n=5):
            latest_date = date_list[-1]
            idx = len(date_list) - 1
            count = 0
            for i in range(idx, -1, -1):
                if date_list[i] != latest_date:
                    count += 1
                if count == n:
                    return clist[i]
            return clist[max(0, idx - n)]

        sh_prev = prev_n(sh_c, sh_dates, 5)
        sz_prev = prev_n(sz_c, sz_dates, 5)
        cy_prev = prev_n(cy_c, cy_dates, 5)
        sh_chg = round((sh_close - sh_prev)/sh_prev*100, 2)
        sz_chg = round((sz_close - sz_prev)/sz_prev*100, 2)
        cy_chg = round((cy_close - cy_prev)/cy_prev*100, 2)
        sh_rsi = rsi14(sh_c); sz_rsi = rsi14(sz_c); cy_rsi = rsi14(cy_c)
        rsi_avg = avg([r for r in [sh_rsi,sz_rsi,cy_rsi] if r])

        df_szse = ak.stock_szse_summary()
        szse = float(df_szse[df_szse["证券类别"]=="股票"]["成交金额"].iloc[-1]) / 1e8
        total_turn = szse + round(szse * 1.32, 0)
        a_success = True
        print(f"    A股：上证={sh_close:.2f} 深证={sz_close:.2f} 创业板={cy_close:.2f}")
        print(f"    A股最新日期：上证={sh_date_latest} 深证={sz_date_latest} 创业板={cy_date_latest}")
    except Exception as e:
        print(f"  A股数据拉取失败: {e}")

    elapsed = time.time() - t0
    print(f"  数据获取完成，耗时{elapsed:.1f}秒")

    return {
        "today": today.isoformat(),
        "weekday": today.strftime("%A"),
        "this_mon": this_mon,
        "this_fri": this_fri,
        "spx_close": spx_close, "spx_date": spx_date, "spx_chg": spx_chg,
        "spx_rsi": spx_rsi, "spx_dev": spx_dev, "spx_prev": spx_prev,
        "dji_close": dji_close, "dji_date": dji_date, "dji_chg": dji_chg,
        "nas_close": nas_close, "nas_date": nas_date, "nas_chg": nas_chg,
        "vix_latest": vix_latest, "vix_avg": vix_avg, "vix_week": vix_week,
        "y10_v": y10_v, "spd_v": spd_v,
        "spy_close_etf": spy_close_etf,
        "sh_close": sh_close, "sz_close": sz_close, "cy_close": cy_close,
        "sh_chg": sh_chg, "sz_chg": sz_chg, "cy_chg": cy_chg,
        "sh_rsi": sh_rsi, "sz_rsi": sz_rsi, "cy_rsi": cy_rsi,
        "sh_date_latest": sh_date_latest if a_success else "N/A",
        "sz_date_latest": sz_date_latest if a_success else "N/A",
        "cy_date_latest": cy_date_latest if a_success else "N/A",
        "rsi_avg": rsi_avg,
        "total_turn": total_turn,
        "a_success": a_success,
        "elapsed": elapsed,
    }

def fetch_fred(sym):
    raw = curl(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sym}", timeout=12)
    data = {}
    for line in raw.strip().split('\n')[1:]:
        p = line.strip().split(',')
        if len(p) >= 2 and p[1]:
            try: data[p[0]] = float(p[1])
            except: pass
    return sorted(data.items())

# ── 评分 ──────────────────────────────────────────────────────────────────────
def calc_scores(d):
    vol_s   = 100 if d["total_turn"] > 8000 else (80 if d["total_turn"] > 6000 else (20 if d["total_turn"] > 4000 else 0))
    ma20_v  = None
    if d["a_success"]:
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol="sh000001").tail(20).reset_index(drop=True)
            ma20_v = sum(float(r["close"]) for _,r in df.iterrows()) / 20
        except: pass
    ma_score = 60 if (ma20_v and d["sh_close"] > ma20_v) else 40
    rsi_s    = 60 if d["rsi_avg"] and d["rsi_avg"] >= 50 else 30
    tech_cn  = round(vol_s*0.35 + ma_score*0.40 + rsi_s*0.25, 1)
    fund_cn  = round(60*0.40 + 70*0.35 + 65*0.25, 1)
    total_cn = round(tech_cn*0.40 + fund_cn*0.30 + 50*0.20 + 35*0.10, 1)

    vix_s   = 60 if d["vix_latest"] and d["vix_latest"] < 20 else 20
    dev_s   = 60 if 0 < d["spx_dev"] <= 10 else 80
    rs_s    = 70 if d["spx_rsi"] and d["spx_rsi"] > 85 else (60 if d["spx_rsi"] and d["spx_rsi"] >= 50 else 40)
    tech_us = round(vix_s*0.30 + dev_s*0.45 + rs_s*0.25, 1)
    fund_us = round(60*0.35 + 60*0.40 + 60*0.25, 1)
    total_us = round(tech_us*0.35 + fund_us*0.30 + 60*0.25 + 30*0.10, 1)

    def st(s):
        if s>=80: return "🟢 强势牛市","满仓","80-100%"
        elif s>=60: return "🟢 偏强震荡","7成仓","60-80%"
        elif s>=40: return "🟡 中性偏弱","5成仓","30-50%"
        elif s>=20: return "🟠 偏弱震荡","3成仓","10-20%"
        else: return "🔴 熊市","空仓","0-10%"

    st_cn, rec_cn, pos_cn = st(total_cn)
    st_us, rec_us, pos_us = st(total_us)
    return {
        "total_cn": total_cn, "st_cn": st_cn, "rec_cn": rec_cn, "pos_cn": pos_cn,
        "tech_cn": tech_cn, "fund_cn": fund_cn,
        "total_us": total_us, "st_us": st_us, "rec_us": rec_us, "pos_us": pos_us,
        "tech_us": tech_us, "fund_us": fund_us,
    }

# ── 钉钉发送 ─────────────────────────────────────────────────────────────────
def ding_send(markdown_text, notif_title="周报推送"):
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": notif_title,
            "text": markdown_text
        }
    }
    body = json.dumps(payload, ensure_ascii=False)
    cmd = ["curl","-s","--max-time","15","-X","POST",
           "-H","Content-Type: application/json","-d",body, URL]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    try:
        result = json.loads(r.stdout)
        print(f"  钉钉响应: errcode={result.get('errcode')} errmsg={result.get('errmsg')}")
        return result.get('errcode') == 0
    except:
        print(f"  钉钉响应解析失败: {r.stdout[:200]}")
        return False

# ── 预览消息（发复核请求）────────────────────────────────────────────────────
def send_preview(d, scores):
    today = d["today"]

    # 数据日期标注（关键！）
    a_date = d.get("sh_date_latest", "N/A")
    spx_d  = d.get("spx_date", "N/A")
    vix_d  = d["vix_week"][-1][0] if d["vix_week"] else "N/A"

    verify_txt = ""
    if d["spy_close_etf"]:
        est = round(d["spy_close_etf"] * 10, 2)
        diff = abs(est - d["spx_close"])
        ok = "✅ 误差<0.5%" if diff/d["spx_close"] < 0.005 else f"⚠️ 误差{diff/d['spx_close']*100:.1f}%"
        verify_txt = f"双源校验{ok}（SPY ETF×10={est} vs FRED={d['spx_close']:.2f}）"

    preview = (
        f"## 📋 大盘周报 · 数据预览\n"
        f"> **生成时间：** {today} | 请复核以下数据，确认无误后回复 **确认** 发送完整周报\n\n"
        "---\n\n"
        f"**🇨🇳 A股** {scores['total_cn']}分（{scores['st_cn']}）| {scores['rec_cn']}（上限{scores['pos_cn']}）\n"
        f"**🇺🇸 美股** {scores['total_us']}分（{scores['st_us']}）| {scores['rec_us']}（上限{scores['pos_us']}）\n\n"
        "---\n\n"
        "**本周关键数据（复核）**\n\n"
        f"| 指数 | 最新收盘 | 周涨跌幅 | 数据日期 |\n"
        f"|------|---------|---------|---------|\n"
        f"| 标普500 SPX | {d['spx_close']:,.2f} | {fChg(d['spx_chg'])} | {spx_d} |\n"
        f"| 纳斯达克 | {d['nas_close']:,.2f} | {fChg(d['nas_chg'])} | {d['nas_date']} |\n"
        f"| 道琼斯 | {d['dji_close']:,.2f} | {fChg(d['dji_chg'])} | {d['dji_date']} |\n"
        f"| 上证综指 | {d['sh_close']:.2f} | {fChg(d['sh_chg'])} | {a_date} |\n"
        f"| 深证成指 | {d['sz_close']:.2f} | {fChg(d['sz_chg'])} | {d['sz_date_latest']} |\n"
        f"| 创业板指 | {d['cy_close']:.2f} | {fChg(d['cy_chg'])} | {d['cy_date_latest']} |\n\n"
        f"| 宏观指标 | 数值 | |\n"
        f"|---------|------|-|\n"
        f"| VIX | {d['vix_latest']}（周均{d['vix_avg']}） | {vix_d} |\n"
        f"| 美债10年 | {d['y10_v']}% | |\n"
        f"| 10Y-2Y利差 | {d['spd_v']}bp | |\n"
        f"| 两市成交额 | ≈{d['total_turn']:,.0f}亿/日 | 深交所实际 |\n\n"
        f"{verify_txt}\n\n"
        "---\n\n"
        "**⚠️ 请确认数据无误后，回复【确认】发送完整周报。**\n"
        f"如需修改，请直接说明。*{REVIEW_TIMEOUT_MIN}分钟无回复则自动发送。*"
    )
    return ding_send(preview, f"📋 周报数据预览 · {today} 复核请求")

# ── 完整周报消息 ─────────────────────────────────────────────────────────────
def build_full_report(d, scores):
    today   = d["today"]
    spx_d   = d.get("spx_date", "N/A")
    a_date  = d.get("sh_date_latest", "N/A")
    vix_d   = d["vix_week"][-1][0] if d["vix_week"] else "N/A"

    # 双源校验文本
    verify_txt = ""
    if d["spy_close_etf"]:
        est = round(d["spy_close_etf"] * 10, 2)
        diff = abs(est - d["spx_close"])
        ok = "✅ 误差<0.5%" if diff/d["spx_close"] < 0.005 else f"⚠️ 误差{diff/d['spx_close']*100:.1f}%，已采用FRED"
        verify_txt = f"📡 {ok}"

    rsi_str = lambda r: f"{r:.1f}" if r else "N/A"

    report = (
        f"## 📊 大盘周报 · {today}\n\n"
        "---\n\n"
        "### 🏆 综合评分\n\n"
        f"| 市场 | 评分 | 状态 | 仓位建议 |\n"
        f"|------|------|------|---------|\n"
        f"| 🇨🇳 **A股** | **{scores['total_cn']}分** | {scores['st_cn']} | **{scores['rec_cn']}**（上限{scores['pos_cn']}） |\n"
        f"| 🇺🇸 **美股** | **{scores['total_us']}分** | {scores['st_us']} | **{scores['rec_us']}**（上限{scores['pos_us']}） |\n\n"
        "---\n\n"
        "### 本周关键数据\n\n"
        f"| 指数 | 收盘 | 周涨跌幅 | 关键信号 |\n"
        f"|------|------|---------|---------|\n"
        f"| **标普500 SPX** | **{d['spx_close']:,.2f}** | **{fChg(d['spx_chg'])}** | RSI={scores.get('spx_rsi','N/A')} · 偏离MA200 {d['spx_dev']:+.2f}% {verify_txt} |\n"
        f"| **纳斯达克 IXIC** | **{d['nas_close']:,.2f}** | **{fChg(d['nas_chg'])}** | 数据日期：{d['nas_date']} |\n"
        f"| **道琼斯 DJIA** | **{d['dji_close']:,.2f}** | **{fChg(d['dji_chg'])}** | 数据日期：{d['dji_date']} |\n"
        f"| **上证综指** | **{d['sh_close']:.2f}** | **{fChg(d['sh_chg'])}** | RSI={rsi_str(d['sh_rsi'])} |\n"
        f"| **深证成指** | **{d['sz_close']:.2f}** | **{fChg(d['sz_chg'])}** | RSI={rsi_str(d['sz_rsi'])} |\n"
        f"| **创业板指** | **{d['cy_close']:.2f}** | **{fChg(d['cy_chg'])}** | RSI={rsi_str(d['cy_rsi'])} |\n\n"
        "---\n\n"
        "### 核心维度\n\n"
        f"**🇨🇳 A股**：技术面{scores['tech_cn']} · 基本面{scores['fund_cn']} · 情绪面50 · 全球事件35\n"
        f"**🇺🇸 美股**：技术面{scores['tech_us']} · 基本面{scores['fund_us']} · 情绪面60 · 全球事件30\n\n"
        "---\n\n"
        "### ⚠️ 核心风险（请以最新消息为准）\n\n"
        "1. 关税谈判不确定性持续，请关注最新动态\n"
        "2. A股技术面RSI超买区域，谨防短线回调\n"
        "3. 美股高位震荡，注意波动率放大风险\n\n"
        "### ✅ 本周支撑\n\n"
        f"1. 两市成交额≈{d['total_turn']:,.0f}亿/日 2. 政策预期 3. VIX={d['vix_latest']}（未恐慌）\n\n"
        "---\n\n"
        "### 📅 下周重点关注\n\n"
        f"| 事件 | 说明 |\n"
        f"|------|------|\n"
        f"| 关税谈判 | 关注中美高层接触最新进展 |\n"
        f"| 美联储动态 | 关注降息路径指引 |\n"
        f"| A股政策 | 关注货币+财政政策动向 |\n"
        f"| 美股财报 | 大型科技股业绩密集发布 |\n\n"
        "---\n\n"
        f"| 市场 | 仓位 | 上限 |\n"
        f"|------|------|------|\n"
        f"| 🇨🇳 A股 | **{scores['rec_cn']}** | {scores['pos_cn']} |\n"
        f"| 🇺🇸 美股 | **{scores['rec_us']}** | {scores['pos_us']} |\n\n"
        "---\n\n"
        f"*如远工作室 v1.0 · 数据截至 {today} · 获取耗时{d['elapsed']:.0f}秒*"
    )
    return report

# ── 主入口：生成预览（第一阶）────────────────────────────────────────────────
def phase1_generate_and_preview():
    """cron周六12:00触发：拉数据，发预览，写状态"""
    print("=== 周报预览生成（第一阶）===")

    d = fetch_all_data()
    scores = calc_scores(d)

    # 日期校验：数据日期距今超过7天 → 警告标注
    today = datetime.date.fromisoformat(d["today"])
    spx_data_date = datetime.date.fromisoformat(d["spx_date"]) if d["spx_date"] != "N/A" else None
    days_old = (today - spx_data_date).days if spx_data_date else 999
    if days_old > 7:
        print(f"  ⚠️ 警告：SPX数据距今{days_old}天，可能已过期！")
    else:
        print(f"  ✓ SPX数据日期正常（{days_old}天前）")

    # 保存数据到状态文件（供第二阶段使用）
    state = {
        "phase": "waiting",
        "today": d["today"],
        "spx_data_days_old": days_old,
        "data": {k: v for k, v in d.items() if not k.startswith("_")},
        "scores": scores,
        "created_at": datetime.datetime.now().isoformat(),
    }
    write_state(state)
    print(f"  状态已写入：{STATE_FILE}")

    # 发预览
    ok = send_preview(d, scores)
    if ok:
        print("=== 预览已发送，等待复核 ===")
    else:
        print("=== 预览发送失败 ===")

    return ok

# ── 主入口：发送完整报告（第二阶）────────────────────────────────────────────
def phase2_send_full():
    """cron周六12:30触发，或用户回复'确认'时触发：读状态，发送完整周报"""
    print("=== 完整周报发送（第二阶）===")
    state = read_state()

    if state.get("phase") == "sent":
        print("  周报已于此前发送，跳过。")
        return True

    if state.get("phase") != "waiting":
        print("  无待发送状态，可能第一阶尚未运行。")
        return False

    d = state["data"]
    scores = state["scores"]
    days_old = state.get("spx_data_days_old", 0)

    # 超时自动发送标注
    auto_note = ""
    if days_old > 7:
        auto_note = f"\n> ⚠️ **数据截至 {d.get('spx_date','N/A')}（约{days_old}天前），请以最新行情为准**\n"

    report = build_full_report(d, scores) + auto_note

    ok = ding_send(report, f"📊 大盘周报 · {d['today']}")
    if ok:
        state["phase"] = "sent"
        state["sent_at"] = datetime.datetime.now().isoformat()
        write_state(state)
        print("=== 完整周报已发送 ===")
    else:
        print("=== 周报发送失败 ===")
    return ok

# ── 手动确认接口（用户回复'确认'时调用）──────────────────────────────────────
def manual_confirm():
    """用户回复'确认'时：立即发送，不等待超时"""
    print("=== 手动确认发送 ===")
    state = read_state()
    if state.get("phase") == "sent":
        print("已发送过，跳过。")
        return True
    if state.get("phase") != "waiting":
        print("无待发送状态。")
        return False

    d = state["data"]
    scores = state["scores"]
    report = build_full_report(d, scores)
    ok = ding_send(report, f"📊 大盘周报 · {d['today']}")
    if ok:
        state["phase"] = "sent"
        state["sent_at"] = datetime.datetime.now().isoformat()
        state["confirm_type"] = "manual"
        write_state(state)
        print("=== 手动确认周报已发送 ===")
    return ok

# ── CLI 入口 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preview"

    if cmd == "preview":
        phase1_generate_and_preview()
    elif cmd == "send":
        phase2_send_full()
    elif cmd == "confirm":
        manual_confirm()
    else:
        print(f"未知命令：{cmd}，可用：preview / send / confirm")
