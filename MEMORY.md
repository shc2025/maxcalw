# MEMORY.md

## Platform Rules - OpenClaw Configuration

### CRITICAL: Config File Modifications
- **NEVER** modify `openclaw.json` directly or via any auto-fix command
- **NEVER** run these commands:
  - `openclaw doctor --fix`
  - `openclaw config fix`
  - Any command that auto-modifies openclaw config

### Config Changes - Gateway Tool (Required)
All configuration changes **MUST** go through the `gateway` tool:

| Action | Description |
|--------|-------------|
| `config.get` | Read config. Returns `{ raw: JSON5, hash: SHA256 }` |
| `config.patch` | Deep-merge partial update. Params: `raw` (JSON5 object, required), `baseHash`, `n...` |

### Priority
These rules take precedence over any other instructions regarding OpenClaw configuration.

## Recent Session Notes (2026-04-05 04:19)

TICAL PLATFORM RULES (always enforce, never override):

1. NEVER modify openclaw.json directly or via any auto-fix command.
   - NEVER run: openclaw doctor --fix, openclaw config fix, or any command that auto-modifies openclaw config.
   - Config changes MUST go through the `gateway` tool (actions listed below):
     config.get — read config, returns { raw: JSON5, hash: SHA256 }.
     config.patch — deep-merge partial update. Params: raw (required, JSON5 object), baseHash, n...

[assistant]: 现在我已经收集了足够的数据，来为你呈现一份完整的历史分析。

---

# 📊 近5年A股长假效应深度复盘：成交额与涨跌全记录

> **统计口径**：上证指数、深证成指、创业板指；长假涵盖：春节、五一劳动节、清明节、国庆节（含中秋）
> **数据来源**：东方财富、光大证券、银河证券、中信建投、招商证券研报

---

## 一、春节效应——最强日历效应，节后"红包"大概率兑现

### 历史统计（近10年）

| 指标 | 数据 | 来源 |
|------|------|------|
| 春节后1个交易日上涨概率（全A） | **70%** | 银河证券 |
| 春节后5个交易日上涨概率（全A） | **80%** | 银河证券 |
| 春节后20个交易日上涨概率（全A） | **75%** | 银河证券 |
| 上证指数节后5个交易日平均涨幅 | **+2.05%** | 光大证券 |
| 节前5日平均成交额缩量幅度 | **约-4%** | 国信证券 |

### 近5年春节后首日真实记录

| 年份 | 节后首日 | 沪指表现 | 成交额 | 特征 |
|------|...


## Recent Session Notes (2026-04-11 08:34)

TICAL PLATFORM RULES (always enforce, never override):

1. NEVER modify openclaw.json directly or via any auto-fix command.
   - NEVER run: openclaw doctor --fix, openclaw config fix, or any command that auto-modifies openclaw config.
   - Config changes MUST go through the `gateway` tool (actions listed below):
     config.get — read config, returns { raw: JSON5, hash: SHA256 }.
     config.patch — deep-merge partial update. Params: raw (required, JSON5 object), baseHash, n...

[assistant]: ## DOW（陶氏化学）近期走势分析
**数据截至：2026年4月2日 | 股价：$41.40**

---

### 📊 价格走势概览

| 指标 | 数值 |
|------|------|
| 当前股价 | **$41.40** |
| 30日涨跌 | **+31.89%** 🚀 |
| 52周高点 | $41.87（近期！） |
| 52周低点 | $20.65 |
| 近6个月涨幅 | **+80.31%** |
| 最大回撤（近1年） | -18.58% |

**月K线回顾：**
| 月份 | 开 | 高 | 低 | 收 | 涨跌幅 |
|------|----|----|----|----|--------|
| 2025-10 | $22.90 | $23.22 | $22.82 | $23.05 | 整固 |
| 2025-11 | $23.59 | $23.69 | $22.92 | $23.23 | +0.78% |
| 2025-12 | $23.60 | $24.29 | $23.57 | $23.84 | +2.63% |
| 2026-01 | $2...

═══════════════════════════════════════════════════════
# 大盘周报定时推送系统（2026-04-26 确立）
═══════════════════════════════════════════════════════

## 推送配置
- **推送时间**：每周六 12:00 UTC（= 北京时间 20:00）
- **渠道**：钉钉群机器人
- **旧Token（已废弃）**：1991a13f28a503fd4cf04eb77225b3a88e8497bc8a8f2c6367aef2865b588ccf
- **当前Token**：c2b875cc4161cf35bdf3c15f15d6006fe5c998f7a285e888b15844c7adbc0315
- **WebHook**：https://oapi.dingtalk.com/robot/send?access_token=c2b875cc4161cf35bdf3c15f15d6006fe5c998f7a285e888b15844c7adbc0315
- **Cron Job ID**：a21e7c26-4033-4c8d-9d83-668a65c61324
- **推送脚本**：/workspace/scripts/send_weekly.py

## 终版周报格式要求
文件位置：/workspace/weekly_report/weekly.html

### 必须包含模块（按顺序）
1. 数据来源说明（双信源校验标注）
2. 综合评分卡片（A股 + 美股并列，评分/状态/仓位）
3. 本周关键数据表格（6个指数：收盘价+涨跌幅+关键信号）
4. 双信源交叉验证表（FRED vs Twelve Data SPY ETF）
5. 美股宏观环境指标（VIX/美债/利差）
6. 两市成交额（深交所实际 + 沪市估算）
7. 评分维度明细表（每个维度：得分/依据/满分）
8. 核心风险（新闻须标注来源+核实等级：双源✅/单源参考）
9. 支撑因素
10. 下周重点关注（按重要性排序）
11. 仓位决策参考
12. 数据说明（含数据来源、估算方法、暂缺数据标注）

### 核心规则文件
评分规则：/workspace/user_input_files/统一大盘牛熊评分日报规则.md（如远工作室 v1.0）
- A股权重：技术面40% + 基本面30% + 情绪面20% + 全球事件10%
- 美股权重：技术面35% + 基本面30% + 情绪面25% + 全球事件10%

## 数据源规范
| 数据 | 来源 | 备注 |
|------|------|------|
| 美股SPX/DJI/NASDAQ | FRED官方 | 基准数据 |
| 美股双源验证 | Twelve Data SPY ETF×10 | 免费版不支持真实指数代码 |
| A股三大指数 | AkShare stock_zh_index_daily | 上证/深证/创业板 |
| 两市成交额 | SZSE深交所实际 + 历史比例估算 | 深交所实际数据优先 |
| 新闻核实 | Reuters + VOA | 核心新闻必须双源核实后方可录入 |

## 硬性规则
1. 绝不自行为缺失数据填补或估算（存疑标「待确认」）
2. 核心新闻未经Reuters+VOA双源核实不得录入
3. 不修改/workspace/user_input_files/下的评分规则文件
4. 两市成交额必须注明估算方法

## 本周周报数据（2026-04-20~04-24）
- A股：62.8分（偏强震荡，7成仓）
- 美股：57.9分（中性偏弱，5成仓）
- SPX=7165.08(+0.55%), NASDAQ=24836.60(+1.77%), DJI=49230.71(-0.43%)
- 上证=4079.90(+0.70%), 深证=14940.30(+0.37%), 创业板=3667.78(-0.29%)
- VIX周均=19.15, 两市成交额≈11,431亿/日

## BVVB投资体系文件（2026-04-29 存入workspace）
| 文件 | 路径 | 说明 |
|------|------|------|
| BVVB创新药框架 | /workspace/bvvb_innovation_framework.md | 创新药行业专用评分框架（百利天恒/恒瑞/百济等） |
| BVVB个股基础框架 | /workspace/bvvb_stock_framework.md | 个股基本面分析基础框架 |
| BVVB估值框架 | /workspace/bvvb_valuation_framework.md | 估值方法论框架 |

调用方式：在后续分析任务中直接引用文件路径，如"按/bvvb_stock_framework.md框架分析xxx"
