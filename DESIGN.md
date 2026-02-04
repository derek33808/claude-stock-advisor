# A股智能交易策略系统 (Stock Advisor)

## 项目概述

### 愿景声明
构建一个智能化的A股交易策略指导系统，通过量化分析和AI技术，帮助个人投资者：
- **实时查询**：输入任意股票代码，获取完整的技术分析和交易建议
- **智能推荐**：每日自动筛选优质标的，提供专业级选股建议
- **跟踪回溯**：记录推荐历史，验证策略有效性
- **AI分析**（Phase 2）：基本面分析、政策面解读

### 核心价值主张
| 特性 | 说明 |
|-----|------|
| 实时查询 | 输入任意股票代码，3-5秒返回完整分析 |
| 技术分析 | MACD、RSI、KDJ、MA等20+技术指标 |
| 交易建议 | 买入价、止损价、止盈价、仓位建议 |
| 推荐跟踪 | 记录每日推荐，追踪后续表现 |
| 策略验证 | 胜率统计、收益回测 |

### 目标用户
| 用户类型 | 特征 | 核心需求 |
|---------|------|---------|
| 个人投资者 | 有一定股票知识，但缺乏系统分析能力 | 快速获取专业分析 |
| 量化入门者 | 对量化交易感兴趣，想学习策略逻辑 | 理解策略原理 |
| 忙碌上班族 | 没时间盯盘和研究，但想参与股市 | 快速获取可执行的交易计划 |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Netlify (前端)                              │
│                 React + TypeScript + Tailwind                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  首页     │  │ 股票查询  │  │ 推荐历史  │  │ 策略统计  │    │
│  │  推荐列表 │  │ 实时分析  │  │ 跟踪回溯  │  │ 胜率展示  │    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │ API 调用
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Render (后端)                               │
│                    FastAPI + Python                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │  数据获取模块  │  │  策略引擎     │  │  AI 分析模块      │   │
│  │  AKShare      │  │  技术指标     │  │  (Phase 2)        │   │
│  │  实时行情     │  │  选股策略     │  │  基本面/政策面    │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│  ┌───────────────┐  ┌───────────────┐                          │
│  │  推荐生成     │  │  定时任务     │                          │
│  │  交易建议     │  │  每日更新     │                          │
│  └───────────────┘  └───────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                              │ 数据存储
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Supabase (数据库)                            │
│                      PostgreSQL                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │ recommendations│  │ stock_cache   │  │ company_fundamental│   │
│  │ 推荐记录      │  │ 股票数据缓存  │  │ 基本面(Phase 2)   │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│  ┌───────────────┐  ┌───────────────┐                          │
│  │ tracking      │  │ ai_analysis   │                          │
│  │ 跟踪记录      │  │ AI分析缓存   │                          │
│  └───────────────┘  └───────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术选择 | 理由 |
|-----|---------|-----|
| **前端** | React + TypeScript + Tailwind | 类型安全、响应式、移动端友好 |
| **后端** | FastAPI (Python) | 异步高性能、与数据分析无缝集成 |
| **数据库** | Supabase (PostgreSQL) | 免费额度大、实时订阅、易用 |
| **数据源** | AKShare | 免费、无需注册、数据全面 |
| **技术指标** | pandas-ta | 专业技术指标计算库 |
| **部署** | Netlify + Render | 免费、自动部署、CDN |

### 部署架构

```
GitHub Repository
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Netlify   │    │   Render    │    │   Render    │
│   前端静态  │    │   Web API   │    │   Cron Job  │
│   自动部署  │    │   FastAPI   │    │  每日17:30  │
└─────────────┘    └─────────────┘    └─────────────┘
                          │                  │
                          └────────┬─────────┘
                                   ▼
                          ┌─────────────┐
                          │  Supabase   │
                          │  数据库     │
                          └─────────────┘
```

---

## 功能需求

### Phase 1: MVP（核心功能）

#### F1: 实时股票查询
**描述**: 用户输入任意股票代码，获取完整的技术分析

**用户流程**:
```
1. 用户输入股票代码 (如 512930)
         ↓
2. 后端调用 AKShare 获取该股票历史数据 (60日)
         ↓
3. 计算技术指标 (MACD/RSI/MA/KDJ/BOLL)
         ↓
4. 生成交易建议 (买入价/止损/止盈)
         ↓
5. 返回前端展示 (3-5秒)
```

**返回数据**:
| 数据类型 | 内容 |
|---------|------|
| 基本信息 | 股票名称、行业、市值 |
| 实时行情 | 当前价、涨跌幅、成交量、成交额 |
| K线数据 | 近60日 OHLC 数据 |
| 技术指标 | MACD、RSI、MA(5/10/20/60)、KDJ、BOLL |
| 信号判断 | 金叉/死叉、超买/超卖、趋势方向 |
| 交易建议 | 买入价区间、止损价、止盈价、仓位建议 |

**验收标准**:
- [ ] 支持查询 A 股所有股票和 ETF
- [ ] 响应时间 < 5 秒
- [ ] 技术指标计算准确

#### F2: 每日智能推荐
**描述**: 系统每日自动筛选推荐股票

**筛选策略**:
```
第一层: 基础过滤
  - 排除 ST/*ST 股票
  - 排除停牌股票
  - 排除上市不足 60 日新股
  - 流通市值 > 10 亿
  - 日均成交额 > 5000 万

第二层: 技术面筛选
  - MACD 金叉或即将金叉
  - RSI 在 30-70 之间
  - 股价站上 MA20
  - 量价配合（放量上涨）

第三层: 综合评分
  - 技术面得分 (40%)
  - 基本面得分 (30%)
  - 资金流向得分 (20%)
  - 市场情绪得分 (10%)
```

**输出**: 每日 Top 5 推荐股票，含完整分析报告

**验收标准**:
- [ ] 每日 17:30 后自动生成推荐
- [ ] 每支股票有完整的筛选依据
- [ ] 推荐逻辑可追溯

#### F3: 推荐跟踪与回溯
**描述**: 记录推荐历史，追踪后续表现

**功能点**:
- 保存每日推荐记录到数据库
- 追踪推荐股票后续涨跌
- 计算策略胜率和收益率
- 展示历史推荐表现

**数据展示**:
```
📊 策略表现（过去30天）

推荐总数: 150 支
触发止盈: 62 支 (41%)
触发止损: 28 支 (19%)
持仓中:   60 支 (40%)

平均收益: +5.2%
胜率: 68%
盈亏比: 2.1:1
```

**验收标准**:
- [ ] 推荐记录完整保存
- [ ] 可查询任意日期的推荐
- [ ] 自动计算策略表现指标

#### F4: Web 交互界面
**描述**: 清晰易用的移动端优先界面

**页面结构**:
```
首页 (/)
  - 市场概览（大盘指数）
  - 股票搜索框
  - 今日推荐列表
  - 风险提示

股票详情页 (/stock/[code])
  - 基本信息
  - 实时行情
  - 技术指标展示
  - 交易建议面板
  - K线图（可选）

推荐历史页 (/history)
  - 历史推荐列表
  - 表现统计
  - 筛选过滤

策略统计页 (/stats)
  - 胜率统计
  - 收益曲线
  - 策略对比
```

**验收标准**:
- [ ] 移动端优先，响应式设计
- [ ] 页面加载时间 < 2 秒
- [ ] 操作流畅，无卡顿

### Phase 2: AI 分析（未来扩展）

#### F5: 基本面 AI 分析
**描述**: 使用 AI 分析公司财务数据

**分析内容**:
- 财务报表解读（营收、利润、现金流）
- 估值分析（PE、PB、PS 对比）
- 盈利能力评估（ROE、ROA、毛利率）
- 成长性判断（同比增长趋势）

#### F6: 政策面 AI 分析
**描述**: 使用 AI 解读政策新闻对个股影响

**分析内容**:
- 行业政策解读
- 宏观经济影响
- 利好/利空判断
- 影响程度评估

#### F7: 综合 AI 报告
**描述**: 整合技术面、基本面、政策面生成投资报告

**输出示例**:
```
📝 AI 投资分析报告 - 贵州茅台 (600519)

【技术面】⭐⭐⭐⭐
MACD金叉确认，RSI健康区间，均线多头排列，短期看涨。

【基本面】⭐⭐⭐⭐⭐
ROE 25%行业领先，净利润连续10年增长，现金流充沛。

【政策面】⭐⭐⭐
消费刺激政策利好白酒行业，但需关注反腐力度。

【综合建议】
评分: 85/100
建议: 逢低建仓
风险: 中低
```

---

## 数据设计

### 数据源

#### 主数据源: AKShare
**官方资源**:
- 文档: https://akshare.akfamily.xyz/
- GitHub: https://github.com/akfamily/akshare

**获取数据**:
| 数据类型 | AKShare 接口 | 说明 |
|---------|-------------|------|
| 股票列表 | `stock_zh_a_spot_em` | 全市场股票实时行情 |
| 历史日线 | `stock_zh_a_hist` | 指定股票历史K线 |
| ETF 数据 | `fund_etf_spot_em` | ETF 实时行情 |
| ETF 历史 | `fund_etf_hist_em` | ETF 历史K线 |
| 财务指标 | `stock_financial_analysis_indicator` | 基本面数据 |
| 资金流向 | `stock_individual_fund_flow` | 主力资金 |

### 数据库设计 (Supabase)

```sql
-- ============================================
-- Phase 1: MVP 表结构
-- ============================================

-- 每日推荐记录
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,                    -- 推荐日期
    code VARCHAR(10) NOT NULL,             -- 股票代码
    name VARCHAR(50),                      -- 股票名称
    industry VARCHAR(50),                  -- 所属行业
    score INTEGER,                         -- 综合评分 (0-100)
    price DECIMAL(10,2),                   -- 推荐时价格
    change DECIMAL(5,2),                   -- 当日涨跌幅
    buy_price_low DECIMAL(10,2),           -- 建议买入价下限
    buy_price_high DECIMAL(10,2),          -- 建议买入价上限
    stop_loss DECIMAL(10,2),               -- 止损价
    take_profit_1 DECIMAL(10,2),           -- 止盈价1
    take_profit_2 DECIMAL(10,2),           -- 止盈价2
    reasons JSONB,                         -- 推荐理由
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(date, code)
);

-- 推荐跟踪记录
CREATE TABLE recommendation_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID REFERENCES recommendations(id),
    track_date DATE NOT NULL,              -- 跟踪日期
    price DECIMAL(10,2),                   -- 当日收盘价
    change_from_rec DECIMAL(5,2),          -- 相对推荐价涨跌幅
    status VARCHAR(20),                    -- 状态: holding/stop_loss/take_profit
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 股票数据缓存（加速查询）
CREATE TABLE stock_cache (
    code VARCHAR(10) PRIMARY KEY,          -- 股票代码
    name VARCHAR(50),                      -- 股票名称
    industry VARCHAR(50),                  -- 所属行业
    market_cap BIGINT,                     -- 总市值
    daily_data JSONB,                      -- 最近60日K线数据
    indicators JSONB,                      -- 技术指标
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 市场概览
CREATE TABLE market_overview (
    date DATE PRIMARY KEY,
    sh_index DECIMAL(10,2),                -- 上证指数
    sh_change DECIMAL(5,2),                -- 上证涨跌幅
    sz_index DECIMAL(10,2),                -- 深证指数
    sz_change DECIMAL(5,2),                -- 深证涨跌幅
    sentiment VARCHAR(20),                 -- 市场情绪
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Phase 2: AI 分析扩展表（预留）
-- ============================================

-- 公司基本面数据
CREATE TABLE company_fundamental (
    code VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,             -- 报告期
    revenue BIGINT,                        -- 营业收入
    net_profit BIGINT,                     -- 净利润
    pe_ttm DECIMAL(10,2),                  -- 市盈率TTM
    pb DECIMAL(10,2),                      -- 市净率
    roe DECIMAL(5,2),                      -- ROE
    debt_ratio DECIMAL(5,2),               -- 资产负债率
    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (code, report_date)
);

-- AI 分析结果缓存
CREATE TABLE ai_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(20),             -- fundamental/policy/comprehensive
    content TEXT,                          -- AI 分析内容
    score INTEGER,                         -- AI 评分
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 政策新闻（未来）
CREATE TABLE policy_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200),
    content TEXT,
    source VARCHAR(100),
    publish_date DATE,
    affected_industries TEXT[],            -- 影响的行业
    sentiment VARCHAR(20),                 -- positive/negative/neutral
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 索引优化
-- ============================================

CREATE INDEX idx_recommendations_date ON recommendations(date);
CREATE INDEX idx_recommendations_code ON recommendations(code);
CREATE INDEX idx_tracking_rec_id ON recommendation_tracking(recommendation_id);
CREATE INDEX idx_stock_cache_updated ON stock_cache(updated_at);
```

---

## API 设计

### 后端 API 接口

```
基础路径: https://stock-advisor-api.onrender.com/api/v1

# ============================================
# 股票查询
# ============================================

GET  /stock/{code}              # 查询单只股票完整分析
     返回: 基本信息 + 行情 + 技术指标 + 交易建议

GET  /stock/{code}/kline        # 获取K线数据
     参数: period=daily|weekly, days=60

GET  /stock/search?q={keyword}  # 搜索股票
     返回: 匹配的股票列表

# ============================================
# 推荐相关
# ============================================

GET  /recommendations           # 获取今日推荐
GET  /recommendations/{date}    # 获取指定日期推荐
GET  /recommendations/history   # 获取历史推荐列表
     参数: start_date, end_date, page, limit

# ============================================
# 统计分析
# ============================================

GET  /stats/performance         # 策略表现统计
     返回: 胜率、收益率、盈亏比等

GET  /stats/tracking/{code}     # 单只股票跟踪记录

# ============================================
# 市场概览
# ============================================

GET  /market/overview           # 市场概览（大盘指数）

# ============================================
# Phase 2: AI 分析
# ============================================

GET  /ai/analysis/{code}        # 获取 AI 综合分析
POST /ai/analyze/{code}         # 触发 AI 分析
```

### API 响应格式

```json
// 股票查询响应示例
{
  "code": "600519",
  "name": "贵州茅台",
  "industry": "白酒",
  "price": 1720.00,
  "change": 2.35,
  "marketCap": 21600,
  "indicators": {
    "macd": { "dif": 15.2, "dea": 12.8, "macd": 4.8, "signal": "金叉" },
    "rsi": { "rsi6": 55, "rsi12": 52, "status": "健康" },
    "ma": { "ma5": 1700, "ma10": 1680, "ma20": 1650, "ma60": 1600 },
    "kdj": { "k": 65, "d": 58, "j": 79 }
  },
  "suggestion": {
    "action": "买入",
    "buyPriceLow": 1680,
    "buyPriceHigh": 1700,
    "stopLoss": 1630,
    "takeProfit1": 1800,
    "takeProfit2": 1880,
    "position": "10-15%",
    "holdingDays": "5-15个交易日",
    "riskLevel": "中等"
  },
  "reasons": {
    "technical": ["MACD金叉", "站上MA20", "RSI健康"],
    "fundamental": ["PE低于行业均值", "ROE优秀"],
    "capital": ["主力资金净流入"]
  }
}
```

---

## 选股策略

### 策略1: MACD 金叉策略

```python
def macd_golden_cross(df):
    """
    MACD金叉买入信号
    条件:
    1. DIF从下向上穿越DEA（金叉）
    2. MACD柱由负转正
    3. 金叉发生在零轴附近更佳
    """
    dif, dea, macd = df['dif'], df['dea'], df['macd']

    # 今日金叉
    golden_cross = (dif.shift(1) < dea.shift(1)) & (dif > dea)
    # MACD柱转正
    macd_positive = (macd.shift(1) < 0) & (macd > 0)

    return golden_cross | macd_positive
```

### 策略2: RSI 超卖反弹策略

```python
def rsi_oversold_bounce(df):
    """
    RSI超卖反弹信号
    条件:
    1. RSI6曾跌破30（超卖区域）
    2. RSI6从超卖区域回升
    3. RSI6突破RSI12
    """
    rsi6, rsi12 = df['rsi6'], df['rsi12']

    was_oversold = rsi6.rolling(5).min() < 30
    recovering = rsi6 > rsi6.shift(1)
    momentum = (rsi6 > rsi12) & (rsi6 < 50)

    return was_oversold & recovering & momentum
```

### 策略3: 均线多头排列策略

```python
def ma_bullish_alignment(df):
    """
    均线多头排列信号
    条件:
    1. MA5 > MA10 > MA20 > MA60
    2. 股价站上MA5
    3. MA5向上倾斜
    """
    close = df['close']
    ma5, ma10, ma20, ma60 = df['ma5'], df['ma10'], df['ma20'], df['ma60']

    bullish = (ma5 > ma10) & (ma10 > ma20) & (ma20 > ma60)
    above_ma5 = close > ma5
    ma5_rising = ma5 > ma5.shift(1)

    return bullish & above_ma5 & ma5_rising
```

### 策略4: 量价配合策略

```python
def volume_price_confirmation(df):
    """
    量价配合信号
    条件:
    1. 价格上涨
    2. 成交量放大（> 5日均量 * 1.5）
    3. 非跳空高开
    """
    close, volume, open_price = df['close'], df['volume'], df['open']

    price_up = close > close.shift(1)
    vol_ma5 = volume.rolling(5).mean()
    volume_increase = volume > vol_ma5 * 1.5
    no_gap = open_price < close.shift(1) * 1.03

    return price_up & volume_increase & no_gap
```

### 综合评分系统

```python
def calculate_score(stock_data):
    """
    综合评分 (0-100分)

    技术面 (40分):
    - MACD状态: 0-10分
    - RSI状态: 0-10分
    - 均线状态: 0-10分
    - 量价配合: 0-10分

    基本面 (30分):
    - 估值水平: 0-10分
    - 盈利能力: 0-10分
    - 成长性: 0-10分

    资金流向 (20分):
    - 主力资金: 0-10分
    - 北向资金: 0-10分

    市场情绪 (10分):
    - 板块热度: 0-5分
    - 市场趋势: 0-5分
    """
    score = 0
    score += evaluate_technical(stock_data) * 0.4
    score += evaluate_fundamental(stock_data) * 0.3
    score += evaluate_fund_flow(stock_data) * 0.2
    score += evaluate_sentiment(stock_data) * 0.1
    return round(score, 1)
```

### 交易建议计算

```python
def calculate_trading_plan(stock_data):
    """计算交易计划"""
    close = stock_data['close'].iloc[-1]
    high_20 = stock_data['high'].tail(20).max()
    low_20 = stock_data['low'].tail(20).min()
    atr = calculate_atr(stock_data, period=14)

    # 支撑位和阻力位
    support = low_20 * 1.02
    resistance = high_20

    # 买入价（当前价下方1-3%）
    buy_price_low = max(close * 0.97, support)
    buy_price_high = close * 0.99

    # 止损价（买入价下方1.5倍ATR）
    stop_loss = min(buy_price_low - atr * 1.5, support * 0.97)

    # 止盈价（盈亏比 2:1 和 3:1）
    risk = buy_price_low - stop_loss
    take_profit_1 = buy_price_low + risk * 2
    take_profit_2 = buy_price_low + risk * 3

    return {
        'buy_price_range': (buy_price_low, buy_price_high),
        'stop_loss': stop_loss,
        'take_profit_1': take_profit_1,
        'take_profit_2': take_profit_2,
        'risk_reward_ratio': '2:1 / 3:1'
    }
```

---

## 项目结构

```
stock-advisor/
├── DESIGN.md                    # 本设计文档
├── PROGRESS.md                  # 开发进度
├── QA_REPORT.md                 # QA审查报告
│
├── frontend/                    # 前端 (Netlify)
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   ├── page.tsx         # 首页
│   │   │   ├── stock/[code]/    # 股票详情
│   │   │   ├── history/         # 推荐历史
│   │   │   └── stats/           # 统计页面
│   │   ├── components/          # 通用组件
│   │   ├── lib/                 # 工具函数
│   │   └── types/               # 类型定义
│   ├── package.json
│   └── netlify.toml
│
├── backend/                     # 后端 (Render)
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── api/                 # API 路由
│   │   │   ├── stock.py         # 股票查询
│   │   │   ├── recommendations.py
│   │   │   └── stats.py
│   │   ├── services/            # 业务服务
│   │   │   ├── akshare_service.py
│   │   │   ├── indicator_service.py
│   │   │   └── strategy_service.py
│   │   ├── models/              # 数据模型
│   │   └── db/                  # 数据库操作
│   ├── requirements.txt
│   └── render.yaml
│
└── docs/                        # 文档
    ├── api.md
    └── strategies.md
```

---

## 开发路线图

### Phase 1: MVP (2周)

| 里程碑 | 交付物 | 时间 |
|-------|-------|------|
| M1.1 | 后端项目搭建 + Supabase 配置 | Day 1-2 |
| M1.2 | 股票查询 API (AKShare + 技术指标) | Day 3-5 |
| M1.3 | 每日推荐 API + 定时任务 | Day 6-7 |
| M1.4 | 推荐跟踪 + 统计 API | Day 8-9 |
| M1.5 | 前端界面重构 | Day 10-12 |
| M1.6 | 部署 + 测试 | Day 13-14 |

### Phase 2: AI 分析 (2周)

| 里程碑 | 交付物 | 时间 |
|-------|-------|------|
| M2.1 | 基本面数据获取 + 存储 | Day 15-17 |
| M2.2 | AI 分析模块 (Claude API) | Day 18-21 |
| M2.3 | 政策面数据获取 | Day 22-24 |
| M2.4 | 综合报告生成 | Day 25-28 |

### Phase 3: 优化扩展 (1周)

| 里程碑 | 交付物 | 时间 |
|-------|-------|------|
| M3.1 | K线图组件 | Day 29-30 |
| M3.2 | 移动端优化 | Day 31-32 |
| M3.3 | 性能优化 + 缓存 | Day 33-35 |

---

## 合规与风险声明

### 必须展示的声明

```
免责声明:

1. 本系统提供的所有信息、分析、建议仅供参考，不构成任何投资建议。

2. 股票市场存在风险，过往业绩不代表未来表现。投资者应根据自身财务
   状况、风险承受能力和投资目标，独立做出投资决策。

3. 本系统的选股策略基于历史数据和技术分析，无法保证未来收益，
   投资者可能面临本金损失的风险。

4. 本系统不提供证券投资咨询服务，不具备证券投资咨询资格。

5. 使用本系统即表示您已阅读、理解并同意以上声明。
```

---

## 验收标准

### 功能验收

| 功能 | 验收标准 | 优先级 |
|-----|---------|-------|
| 股票查询 | 支持查询任意A股/ETF，响应<5秒 | P0 |
| 技术指标 | MACD/RSI/MA/KDJ 计算准确 | P0 |
| 交易建议 | 盈亏比>2:1，建议合理 | P0 |
| 每日推荐 | 17:30后自动生成 Top 5 | P0 |
| 推荐跟踪 | 记录完整，可追溯 | P1 |
| 策略统计 | 胜率、收益率计算正确 | P1 |

### 性能验收

| 指标 | 目标值 |
|-----|-------|
| 股票查询响应 | < 5 秒 |
| 首页加载 | < 2 秒 |
| API 响应 | < 500ms (缓存命中) |

---

*文档版本: v2.0*
*更新日期: 2026-02-04*
*架构: Netlify + Render + Supabase*
