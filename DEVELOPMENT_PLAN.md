# Stock Advisor v2.0 - 详细开发执行计划

**文档版本**: v1.0
**创建日期**: 2026-02-09
**基于文档**: PRD_v2.0.md (91/100分), ARCHITECTURE.md v1.1 (91/100分)
**开发周期**: 7周
**项目状态**: Phase 0 进行中

---

## 目录

1. [开发概览](#1-开发概览)
2. [Phase 0: 稳定化 (第1周)](#2-phase-0-稳定化-第1周)
3. [Phase 1: 核心v2.0功能 (第2-4周)](#3-phase-1-核心v20功能-第2-4周)
4. [Phase 2: 历史与追踪 (第5-6周)](#4-phase-2-历史与追踪-第5-6周)
5. [Phase 3: 打磨与发布 (第7周)](#5-phase-3-打磨与发布-第7周)
6. [代码变更清单](#6-代码变更清单)
7. [测试要求](#7-测试要求)
8. [部署检查清单](#8-部署检查清单)

---

## 1. 开发概览

### 1.1 项目现状

**已完成**:
- ✅ PRD v2.0（91/100分，QA审核通过）
- ✅ ARCHITECTURE v1.1（91/100分，QA审核通过）
- ✅ 测试策略文档（PRD Section 13）
- ✅ 现有代码基础（v1.0，部分功能已实现）

**现有后端服务**:
- `eastmoney_service.py` - 东方财富数据
- `yahoo_service.py` - Yahoo Finance fallback
- `akshare_service.py` - AKShare数据
- `sina_service.py` - 新浪数据
- `indicator_service.py` - 技术指标计算
- `strategy_service.py` - 选股策略
- `ai_analysis_service.py` - AI分析
- `glm_service.py` - GLM模型调用

**需要新增的服务**:
- `news_service.py` - 新闻数据获取
- `fundamental_service.py` - 财报和基本面
- `industry_service.py` - 行业分析
- `comprehensive_analysis_service.py` - 综合分析orchestrator
- `watchlist_service.py` - 自选股管理
- `prediction_tracking_service.py` - 预测追踪
- `analysis_history_service.py` - 历史记录
- `token_monitor_service.py` - Token监控
- `rate_limiter_service.py` - 限流管理
- `trading_calendar_service.py` - 交易日历

### 1.2 v2.0核心变化

| 维度 | v1.0 | v2.0 |
|------|------|------|
| 分析深度 | 仅技术指标 | 5维分析（技术+基本面+新闻+财报+行业） |
| 新闻整合 | 无 | 实时新闻（7天）+ 财报 + 公告 |
| 行业分析 | 无 | 行业走势 + 政策 + 龙头对比 + 资金流向 |
| 用户投资组合 | 无 | 自选股 + 完整分析 + 一键刷新 |
| 预测追踪 | 基础推荐历史 | 自动5天对比 + 准确率统计 |
| Token控制 | 未考虑 | 实时监控 + 告警 + 限流 |

---

## 2. Phase 0: 稳定化 (第1周)

**目标**: 修复所有关键bug，添加基础测试，准备代码库

### 2.1 P0 Bug修复（必须完成）

#### Task 0.1: 部署搜索路由修复到 Render (10分钟)

**问题**: BUG-001 - 股票搜索返回404（路由冲突）

**文件**: `backend/app/api/stock.py`

**修改**:
```python
# 当前路由（有冲突）
@router.get("/stock/{code}")
@router.get("/stock/search")  # ❌ 冲突

# 修复后路由
@router.get("/stock/{code}")
@router.get("/stocks/search")  # ✅ 修复
```

**验证**:
```bash
curl https://stock-advisor-api-6vtb.onrender.com/api/v1/stocks/search?q=茅台
```

#### Task 0.2: 验证API Key管理 (30分钟)

**检查清单**:
- [x] GLM API key 已通过环境变量管理 ✅
- [ ] Supabase key 未硬编码
- [ ] 所有敏感配置在 `.env`
- [ ] `.env.example` 包含所有必需配置

**验证**:
```bash
grep -r "zhipuai\|sk-\|supabase" --include="*.py" backend/app/ | grep -v "get_settings"
```

#### Task 0.3: 重新生成推荐股（10只）(5分钟)

**问题**: BUG-002 - 推荐只返回5只

**文件**: `backend/app/services/strategy_service.py`

**修改**:
```python
# 找到推荐生成函数
def generate_recommendations():
    # 修改为返回 10 只
    return top_stocks[:10]  # 确保是10只
```

**执行**:
```bash
curl -X POST https://stock-advisor-api-6vtb.onrender.com/api/v1/recommendations/generate
```

#### Task 0.4: 修复 prev_close null 问题 (2小时)

**问题**: BUG-003 - prev_close 字段返回 null

**调查步骤**:
1. 检查 `eastmoney_service.py` 中 `get_stock_realtime()` 函数
2. 检查 API 响应字段mapping
3. 添加日志追踪数据源

**文件**: `backend/app/services/eastmoney_service.py`

**可能的修复**:
```python
def get_stock_realtime(code):
    # 检查字段映射
    prev_close = data.get('pre_close') or data.get('preclose') or data.get('yestclose')
    return {
        'prev_close': prev_close,  # 确保字段正确
        # ...
    }
```

#### Task 0.5: 移除死代码 (15分钟)

**前端文件**: 检查 `src/` 或 Next.js app/ 目录

**删除项**:
- `aiRankingsCache` 未使用的缓存代码
- 任何注释掉的代码
- 未使用的导入

#### Task 0.6: 合并类型定义 (30分钟)

**问题**: CODE-002 - `AIRankingItem` 类型定义重复

**文件**:
- `api.ts`
- `types.ts`

**修复**: 统一到 `types.ts`，删除 `api.ts` 中的重复定义

### 2.2 单元测试（P0）(1天)

#### Task 0.7: 设置测试框架

**新文件**: `backend/tests/`

**目录结构**:
```
backend/tests/
├── __init__.py
├── test_indicator_service.py    # 技术指标测试
├── test_strategy_service.py      # 策略测试
├── test_comprehensive_service.py # 综合分析测试
├── test_trading_calendar.py      # 交易日历测试
├── conftest.py                    # pytest配置
└── fixtures/
    └── sample_stock_data.json    # 测试数据
```

**依赖安装**:
```bash
pip install pytest pytest-cov pytest-asyncio
```

#### Task 0.8: indicator_service 单元测试

**文件**: `backend/tests/test_indicator_service.py`

**测试用例**:
```python
import pytest
from app.services.indicator_service import calculate_indicators

def test_macd_calculation():
    """测试MACD指标计算准确性"""
    # 使用已知数据验证计算结果
    pass

def test_rsi_calculation():
    """测试RSI指标计算"""
    pass

def test_ma_calculation():
    """测试移动平均线计算"""
    pass
```

**目标覆盖率**: > 80%

### 2.3 合规审查（P0）(2小时)

#### Task 0.9: 审查所有UI文本

**检查文件**:
- 所有前端组件
- API响应消息
- 错误提示

**合规要求** (参考 PRD Section 10.4):
| ✅ 使用 | ❌ 不使用 |
|---------|----------|
| "分析结果" | "投资建议" |
| "技术信号" | "买入推荐" |
| "参考信息" | "专家意见" |
| "观察" | "必须买入" |

**执行**:
```bash
# 搜索禁止用语
grep -r "投资建议\|买入推荐\|专家意见\|必须买入\|保证收益\|确定涨" frontend/
```

### 2.4 基础设施（P1）(0.5天)

#### Task 0.10: 添加限流中间件 (2小时)

**文件**: `backend/app/main.py`

**依赖**:
```bash
pip install slowapi
```

**代码**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/stock/{code}")
@limiter.limit("10/minute")  # 每分钟10次
async def get_stock(code: str):
    pass
```

#### Task 0.11: GitHub Actions CI配置 (0.5天)

**新文件**: `.github/workflows/ci.yml`

**内容**:
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=term-missing
      - name: Lint
        run: |
          pip install flake8
          flake8 backend/app --max-line-length=120

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Type check
        run: npm run type-check
      - name: Lint
        run: npm run lint

  compliance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check prohibited language
        run: |
          if grep -r "投资建议\|买入推荐\|保证收益" frontend/ backend/; then
            echo "❌ 发现禁止用语"
            exit 1
          fi
```

### 2.5 Phase 0 验收标准

**Exit Criteria**:
- [ ] 所有P0 bugs修复
- [ ] 单元测试通过，覆盖率 > 80%
- [ ] CI pipeline 运行成功
- [ ] 合规检查通过
- [ ] QA Guardian 审核通过

---

## 3. Phase 1: 核心v2.0功能 (第2-4周)

### 3.1 Sprint 1: 数据源 + 后端服务 (第2周)

#### Task 1.1: news_service.py (2天)

**新文件**: `backend/app/services/news_service.py`

**功能**:
```python
def get_recent_news(code: str, days: int = 7) -> List[Dict]:
    """
    获取最近N天的重要新闻

    Args:
        code: 股票代码
        days: 天数

    Returns:
        新闻列表，每条包含：
        - date: 日期
        - title: 标题
        - type: 类型 (利好/利空/中性)
        - importance: 重要性 (高/中/低)
        - summary: 摘要
    """
    # 调用东方财富新闻API
    url = f"https://np-anotice-stock.eastmoney.com/api/security/ann"
    # 过滤重要新闻（包含关键词：业绩、财报、分红等）
    # 返回结构化数据
    pass

def get_announcements(code: str, days: int = 30) -> List[Dict]:
    """获取重要公告"""
    pass
```

**测试**: `backend/tests/test_news_service.py`

#### Task 1.2: fundamental_service.py (2天)

**新文件**: `backend/app/services/fundamental_service.py`

**功能**:
```python
def get_latest_financial_report(code: str) -> Dict:
    """
    获取最新财报数据

    Returns:
        {
            'report_date': '2024-12-31',
            'report_type': '年报' | '季报',
            'revenue': 营业收入,
            'revenue_yoy': 同比增长率,
            'net_profit': 净利润,
            'profit_yoy': 同比增长率,
            'eps': 每股收益,
            'roe': ROE,
            'highlights': [...],  # 财报亮点
        }
    """
    # 使用 AKShare: stock_financial_analysis_indicator
    pass

def get_fundamental_data(code: str) -> Dict:
    """获取基本面数据（PE、PB、ROE等）"""
    pass
```

#### Task 1.3: industry_service.py (2天)

**新文件**: `backend/app/services/industry_service.py`

**功能**:
```python
def get_industry_analysis(industry_name: str) -> Dict:
    """
    获取行业分析数据

    Returns:
        {
            'index_change': 行业指数变化,
            'trend': '上升' | '下降' | '震荡',
            'leading_stocks': [龙头股列表],
            'fund_flow': {
                'total': 净流入金额,
                'trend': '流入' | '流出',
                'rank': 行业排名
            },
            'hot_news': [行业新闻],
            'policy_impact': 政策影响分析
        }
    """
    pass
```

#### Task 1.4: trading_calendar_service.py (1天)

**新文件**: `backend/app/services/trading_calendar_service.py`

**功能** (参考 ARCHITECTURE Section 2.2.11):
```python
from datetime import date, timedelta
from typing import Set
import json

class TradingCalendarService:
    def __init__(self):
        self.trading_days: Set[date] = set()
        self.load_calendar()

    def load_calendar(self):
        """加载交易日历（AKShare + 静态备份）"""
        try:
            # 从 AKShare 获取
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
            self.trading_days = set(df['trade_date'].apply(pd.to_datetime).dt.date)
        except:
            # 降级到静态备份
            with open('data/trading_calendar_static.json') as f:
                data = json.load(f)
                self.trading_days = set(pd.to_datetime(data).dt.date)

    def is_trading_day(self, day: date) -> bool:
        """判断是否为交易日"""
        return day in self.trading_days

    def next_trading_day(self, day: date) -> date:
        """获取下一个交易日"""
        pass
```

**静态备份文件**: `backend/data/trading_calendar_static.json`

#### Task 1.5: token_monitor_service.py (1天)

**新文件**: `backend/app/services/token_monitor_service.py`

**功能** (参考 ARCHITECTURE Section 2.2.8):
```python
class TokenMonitor:
    DAILY_LIMIT = 500000  # 每日限额
    WARNING_THRESHOLD = 0.8  # 80%警告

    def __init__(self):
        self.today_usage = 0
        self.last_reset_date = date.today()

    async def log_usage(self, tokens_used: int):
        """记录Token使用"""
        self._check_daily_reset()
        self.today_usage += tokens_used

    async def check_limit(self) -> Dict:
        """检查是否接近限额"""
        self._check_daily_reset()
        percentage = self.today_usage / self.DAILY_LIMIT

        return {
            'used': self.today_usage,
            'limit': self.DAILY_LIMIT,
            'percentage': percentage,
            'warning': percentage >= self.WARNING_THRESHOLD,
            'blocked': percentage >= 1.0
        }
```

#### Task 1.6: 数据库表创建 (0.5天)

**文件**: `backend/app/db/migrations/001_create_v2_tables.sql`

**表结构** (参考 PRD Section 7):
```sql
-- 自选股
CREATE TABLE watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(50),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, code)
);

-- 分析历史记录
CREATE TABLE analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,
    analysis_date DATE NOT NULL,
    analysis_time TIME NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    change_percent DECIMAL(5,2),
    prediction_direction VARCHAR(20),
    prediction_text TEXT,
    target_price_low DECIMAL(10,2),
    target_price_high DECIMAL(10,2),
    analysis_content JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(code, analysis_date)
);

-- 预测准确度跟踪
CREATE TABLE prediction_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_history(id),
    evaluation_date DATE NOT NULL,
    actual_price DECIMAL(10,2) NOT NULL,
    price_change_percent DECIMAL(5,2) NOT NULL,
    is_direction_correct BOOLEAN,
    is_target_reached BOOLEAN,
    accuracy_score DECIMAL(5,2),
    evaluation_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(analysis_id)
);

-- Token使用统计
CREATE TABLE token_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    api_name VARCHAR(50),
    tokens_used INTEGER,
    requests_count INTEGER,
    cost_estimate DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 新闻缓存
CREATE TABLE stock_news_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,
    news_date DATE NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    source VARCHAR(50),
    news_type VARCHAR(20),
    importance VARCHAR(20),
    impact VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(code, news_date, title)
);

-- 行业数据缓存
CREATE TABLE industry_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    industry_name VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    index_value DECIMAL(10,2),
    index_change DECIMAL(5,2),
    fund_flow_net DECIMAL(10,2),
    fund_flow_rank INTEGER,
    leading_stocks JSONB,
    hot_news JSONB,
    policy_impact TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(industry_name, date)
);

-- 热门股票池
CREATE TABLE hot_stock_universe (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50),
    industry VARCHAR(50),
    market_cap BIGINT,
    avg_turnover DECIMAL(15,2),
    inclusion_date DATE,
    last_verified_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_watchlist_user ON watchlist(user_id);
CREATE INDEX idx_analysis_history_code_date ON analysis_history(code, analysis_date DESC);
CREATE INDEX idx_prediction_tracking_analysis ON prediction_tracking(analysis_id);
CREATE INDEX idx_token_usage_date ON token_usage_log(date, api_name);
CREATE INDEX idx_news_code_date ON stock_news_cache(code, news_date DESC);
CREATE INDEX idx_industry_date ON industry_data_cache(industry_name, date DESC);
```

**执行**:
```bash
# 在 Supabase Dashboard 的 SQL Editor 中执行
```

### 3.2 Sprint 2: 综合分析 + 自选股 (第3周)

#### Task 2.1: comprehensive_analysis_service.py (2天)

**新文件**: `backend/app/services/comprehensive_analysis_service.py`

**功能**: 5维分析orchestrator

```python
async def generate_comprehensive_analysis(code: str) -> Dict:
    """
    生成完整的5维综合分析

    流程:
    1. 并行获取5个维度的数据
    2. 调用GLM-4生成综合分析
    3. 返回结构化结果

    Returns:
        {
            'code': 股票代码,
            'name': 股票名称,
            'quote': 实时行情,
            'technical_analysis': {
                'indicators': 技术指标,
                'signals': 信号判断,
                'prediction': AI预测,
                'ai_comment': AI技术面解读
            },
            'company_analysis': {
                'industry': 行业,
                'market_cap': 市值,
                'business_overview': 业务描述,
                'competitive_advantage': 竞争优势,
                'ai_comment': AI公司分析
            },
            'fundamental_analysis': {
                'pe_ratio': PE,
                'pb_ratio': PB,
                'roe': ROE,
                'revenue_growth': 营收增长,
                'profit_margin': 利润率,
                'latest_report': 最新财报,
                'ai_comment': AI基本面解读
            },
            'recent_developments': {
                'news': 近期新闻列表,
                'announcements': 重要公告,
                'ai_impact': AI影响分析,
                'sentiment': 'positive' | 'negative' | 'neutral'
            },
            'industry_analysis': {
                'index_change': 行业指数变化,
                'trend': 行业趋势,
                'peer_comparison': 同行对比,
                'fund_flow': 资金流向,
                'ai_comment': AI行业分析
            },
            'comprehensive_summary': {
                'investment_thesis': 投资观点,
                'top_positives': 前3个利好因素,
                'top_risks': 前3个风险因素,
                'action': 'buy' | 'hold' | 'sell',
                'risk_level': 风险等级
            },
            'trading_suggestion': {
                'buy_price_low': 建议买入价下限,
                'buy_price_high': 建议买入价上限,
                'stop_loss': 止损价,
                'take_profit_1': 止盈价1,
                'take_profit_2': 止盈价2,
                'position_size': 仓位建议,
                'holding_period': 持有周期
            }
        }
    """
    # 步骤1: 并行获取数据
    quote = await get_realtime_quote(code)
    hist = await get_historical_data(code, days=60)

    # 并行获取5个维度
    results = await asyncio.gather(
        calculate_technical_indicators(hist),
        get_company_info(code),
        get_fundamental_data(code),
        get_recent_news(code, days=7),
        get_industry_analysis(quote['industry'])
    )

    technical, company, fundamental, news, industry = results

    # 步骤2: 构建GLM-4 Prompt
    prompt = build_comprehensive_prompt(
        code, quote, technical, company, fundamental, news, industry
    )

    # 步骤3: 调用GLM-4
    ai_response = await call_glm_api(system_prompt, prompt)

    # 步骤4: 解析和结构化
    return parse_and_structure(ai_response, ...)
```

**AI Prompt设计**: 参考 PRD Section 6 和之前设计的详细 Prompt

#### Task 2.2: 扩展GLM-4 Prompt (1天)

**文件**: `backend/app/prompts/comprehensive_analysis_prompt.py`

**Prompt模板**: (2800 tokens)
```python
def build_comprehensive_prompt(...) -> str:
    return f"""
你是一位资深的A股分析师，请对股票 {code} - {name} 进行全面分析。

===== 1. 技术面分析 =====
当前价格：{price} 元
涨跌幅：{change}%
MACD: {macd_data}
RSI: {rsi_data}
请分析技术形态，预测未来3-5天走势。

===== 2. 公司基本面 =====
{company_info}
请分析公司竞争力和发展前景。

===== 3. 财务基本面 =====
{fundamental_data}
最新财报：{latest_report}
请分析财务健康度和估值水平。

===== 4. 近期动态 =====
{news_list}
{announcements}
请分析近期利好/利空影响。

===== 5. 行业分析 =====
{industry_data}
请分析行业整体走势和个股位置。

===== 输出要求 =====
请输出以下5个部分的分析：
【技术面分析】（200字）
【公司分析】（150字）
【基本面分析】（200字）
【近期动态】（150字）
【行业分析】（150字）
【综合建议】（100字）
"""
```

#### Task 2.3: watchlist_service.py (1天)

**新文件**: `backend/app/services/watchlist_service.py`

**功能**:
```python
async def add_to_watchlist(user_id: str, code: str, name: str) -> Dict:
    """添加到自选股"""
    # 插入到 watchlist 表
    # 立即保存当前分析到 analysis_history（第一条记录）
    pass

async def remove_from_watchlist(user_id: str, code: str) -> Dict:
    """移除自选股"""
    pass

async def get_watchlist(user_id: str) -> List[Dict]:
    """获取自选股列表"""
    # 返回自选股 + 当前分析 + 准确率统计
    pass

async def refresh_watchlist_stock(user_id: str, code: str) -> Dict:
    """刷新单只自选股分析"""
    pass
```

#### Task 2.4: 新API端点 (1天)

**文件**: `backend/app/api/comprehensive.py` (新建)

**端点**:
```python
@router.get("/stock/{code}/comprehensive")
async def get_comprehensive_analysis(code: str):
    """获取股票完整5维分析"""
    result = await comprehensive_analysis_service.generate_comprehensive_analysis(code)
    return result

@router.get("/stock/{code}/news")
async def get_stock_news(code: str, days: int = 7):
    """获取股票新闻"""
    return await news_service.get_recent_news(code, days)

@router.get("/industry/{name}/analysis")
async def get_industry_analysis(name: str):
    """获取行业分析"""
    return await industry_service.get_industry_analysis(name)
```

**文件**: `backend/app/api/watchlist.py` (新建)

**端点**:
```python
@router.post("/watchlist/add")
async def add_watchlist(data: WatchlistAddRequest):
    """添加自选股"""
    pass

@router.delete("/watchlist/remove")
async def remove_watchlist(data: WatchlistRemoveRequest):
    """移除自选股"""
    pass

@router.get("/watchlist/list")
async def get_watchlist(user_id: str):
    """获取自选股列表"""
    pass

@router.post("/watchlist/refresh/{code}")
async def refresh_single(code: str, user_id: str):
    """刷新单只股票"""
    pass
```

#### Task 2.5: 更新main.py注册路由 (0.5天)

**文件**: `backend/app/main.py`

**修改**:
```python
from app.api import comprehensive, watchlist

app.include_router(comprehensive.router, prefix="/api/v1", tags=["综合分析"])
app.include_router(watchlist.router, prefix="/api/v1", tags=["自选股"])
```

### 3.3 Sprint 3: 前端 + 全局刷新 (第4周)

#### Task 3.1: 重设计股票详情页 (2天)

**文件**: Next.js `app/stock/[code]/page.tsx`

**布局**: 展示5维分析

```tsx
export default async function StockDetailPage({ params }: { params: { code: string } }) {
  const analysis = await fetchComprehensiveAnalysis(params.code);

  return (
    <div className="container">
      {/* 基本信息 */}
      <StockHeader {...analysis.quote} />

      {/* 刷新按钮 + 加入自选 */}
      <ActionButtons code={params.code} />

      {/* 5维分析 */}
      <TechnicalAnalysisSection {...analysis.technical_analysis} />
      <CompanyAnalysisSection {...analysis.company_analysis} />
      <FundamentalAnalysisSection {...analysis.fundamental_analysis} />
      <RecentDevelopmentsSection {...analysis.recent_developments} />
      <IndustryAnalysisSection {...analysis.industry_analysis} />

      {/* 综合建议 */}
      <ComprehensiveSummarySection {...analysis.comprehensive_summary} />
      <TradingSuggestionSection {...analysis.trading_suggestion} />

      {/* 免责声明 */}
      <Disclaimer />
    </div>
  );
}
```

**组件文件**:
- `components/TechnicalAnalysisSection.tsx`
- `components/CompanyAnalysisSection.tsx`
- `components/FundamentalAnalysisSection.tsx`
- `components/RecentDevelopmentsSection.tsx` (新)
- `components/IndustryAnalysisSection.tsx` (新)
- `components/ComprehensiveSummarySection.tsx` (新)

#### Task 3.2: 自选股Tab和卡片 (2天)

**文件**: `app/page.tsx` 或 `components/HomeContent.tsx`

**新增Tab**:
```tsx
<Tabs>
  <Tab label="今日推荐">
    <RecommendationsList />
  </Tab>
  <Tab label="我的自选">
    <WatchlistTab />
  </Tab>
</Tabs>
```

**新组件**: `components/WatchlistTab.tsx`

```tsx
export function WatchlistTab() {
  const { watchlist, refresh } = useWatchlist();

  return (
    <div>
      <RefreshAllButton onClick={refresh} />
      {watchlist.map(stock => (
        <WatchlistStockCard
          key={stock.code}
          {...stock}
          onRemove={() => removeFromWatchlist(stock.code)}
          onViewHistory={() => router.push(`/watchlist/${stock.code}/history`)}
        />
      ))}
    </div>
  );
}
```

#### Task 3.3: 全局刷新 + SSE进度 (1.5天)

**后端**: `backend/app/api/refresh.py` (新建)

**SSE端点**:
```python
from fastapi.responses import StreamingResponse
import asyncio

@router.post("/refresh/all")
async def refresh_all(data: RefreshAllRequest):
    """全局刷新（SSE）"""

    async def generate_progress():
        user_id = data.user_id
        codes = data.codes  # 推荐股 + 自选股代码列表

        total = len(codes)
        completed = 0

        # 检查并发保护
        if user_id in _active_refreshes:
            yield f"data: {json.dumps({'event': 'error', 'message': '刷新进行中'})}\n\n"
            return

        _active_refreshes[user_id] = {'status': 'running', 'progress': 0}

        try:
            for code in codes:
                # 检查客户端是否断线
                if await request.is_disconnected():
                    break

                # 刷新单只股票
                await refresh_stock_analysis(code)
                completed += 1

                # 发送进度
                progress = {
                    'event': 'progress',
                    'progress': int(completed / total * 100),
                    'current': f'正在分析 {code}...',
                    'completed': completed,
                    'total': total
                }
                yield f"data: {json.dumps(progress)}\n\n"

                # Heartbeat (每3只股票)
                if completed % 3 == 0:
                    yield f": heartbeat\n\n"

            # 完成
            token_usage = await token_monitor.check_limit()
            yield f"data: {json.dumps({'event': 'complete', 'token_usage': token_usage})}\n\n"

        finally:
            del _active_refreshes[user_id]

    return StreamingResponse(generate_progress(), media_type="text/event-stream")
```

**前端**: `lib/api.ts`

**SSE客户端**:
```typescript
export async function refreshAllStocks(
  codes: string[],
  onProgress: (progress: number, message: string) => void,
  onComplete: () => void
) {
  const response = await fetch('/api/v1/refresh/all', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: getDeviceId(), codes })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (data.event === 'progress') {
          onProgress(data.progress, data.current);
        } else if (data.event === 'complete') {
          onComplete();
        }
      }
    }
  }
}
```

#### Task 3.4: Token使用显示 (0.5天)

**新组件**: `components/TokenBadge.tsx`

```tsx
export function TokenBadge() {
  const { usage, limit, percentage, warning } = useTokenUsage();

  const color = warning ? 'yellow' : percentage > 0.5 ? 'orange' : 'green';

  return (
    <div className={`token-badge ${color}`}>
      Token: {usage}K / {limit}K ({(percentage * 100).toFixed(0)}%)
    </div>
  );
}
```

**新API**: `backend/app/api/token.py`

```python
@router.get("/token/usage/today")
async def get_token_usage():
    """获取今日Token使用情况"""
    return await token_monitor.check_limit()
```

#### Task 3.5: 更新推荐生成使用综合分析 (1天)

**文件**: `backend/app/services/strategy_service.py` 或新建 `recommendation_service.py`

**修改**: 推荐生成使用 `comprehensive_analysis_service`

```python
async def generate_daily_recommendations():
    """每日推荐生成（使用综合分析）"""

    # 1. 从 hot_stock_universe 获取候选池
    candidates = await get_hot_stock_universe()

    # 2. 技术面初筛（快速过滤）
    filtered = []
    for code in candidates:
        quick_score = await quick_technical_score(code)
        if quick_score > 60:
            filtered.append((code, quick_score))

    # 3. 综合分析Top 10
    top_codes = [code for code, _ in sorted(filtered, key=lambda x: x[1], reverse=True)[:10]]

    recommendations = []
    for code in top_codes:
        analysis = await comprehensive_analysis_service.generate_comprehensive_analysis(code)
        recommendations.append({
            'code': code,
            'name': analysis['name'],
            'price': analysis['quote']['price'],
            'change': analysis['quote']['change'],
            'score': calculate_composite_score(analysis),
            'analysis': analysis  # 完整分析
        })

    # 4. 保存到数据库
    await save_recommendations(recommendations)

    return recommendations
```

### 3.4 Phase 1 验收标准

**Exit Criteria**:
- [ ] 综合分析API返回所有5个维度
- [ ] 自选股功能完整（添加/移除/刷新）
- [ ] 全局刷新进度条正常工作
- [ ] Token监控显示准确
- [ ] 每日推荐使用综合分析生成
- [ ] 单元测试覆盖新增服务
- [ ] QA Guardian代码审核通过

---

## 4. Phase 2: 历史与追踪 (第5-6周)

### 4.1 Sprint 4: 预测追踪系统 (第5周)

#### Task 4.1: prediction_tracking_service.py (2天)

**新文件**: `backend/app/services/prediction_tracking_service.py`

**功能**:
```python
class PredictionTrackingService:

    async def save_daily_snapshot(self, code: str, user_id: str):
        """保存每日分析快照"""
        # 1. 获取当前综合分析
        analysis = await comprehensive_analysis_service.generate_comprehensive_analysis(code)

        # 2. 提取预测信息
        snapshot = {
            'code': code,
            'analysis_date': date.today(),
            'price': analysis['quote']['price'],
            'prediction_direction': analysis['comprehensive_summary']['action'],
            'prediction_text': analysis['technical_analysis']['prediction'],
            'target_price_low': analysis['trading_suggestion']['buy_price_low'],
            'target_price_high': analysis['trading_suggestion']['take_profit_2'],
            'analysis_content': analysis  # 完整JSON
        }

        # 3. 插入 analysis_history 表
        await db.analysis_history.insert(snapshot)

    async def evaluate_prediction(self, analysis_id: str):
        """评估5天前的预测（5个交易日后）"""
        # 1. 获取分析记录
        analysis = await db.analysis_history.get(analysis_id)

        # 2. 获取5个交易日后的实际价格
        evaluation_date = trading_calendar.add_trading_days(analysis.analysis_date, 5)
        actual_price = await get_price_on_date(analysis.code, evaluation_date)

        # 3. 计算准确度
        price_change = (actual_price - analysis.price) / analysis.price

        # 方向准确性
        predicted_direction = analysis.prediction_direction  # 'buy'/'hold'/'sell'
        is_direction_correct = (
            (predicted_direction == 'buy' and price_change > 0) or
            (predicted_direction == 'sell' and price_change < 0) or
            (predicted_direction == 'hold' and abs(price_change) < 0.02)
        )

        # 目标价准确性
        is_target_reached = (
            analysis.target_price_low <= actual_price <= analysis.target_price_high
        )

        # 综合准确度分数 (0-100)
        accuracy_score = calculate_accuracy_score(
            is_direction_correct,
            is_target_reached,
            abs(price_change)
        )

        # 4. 保存评估结果
        evaluation = {
            'analysis_id': analysis_id,
            'evaluation_date': evaluation_date,
            'actual_price': actual_price,
            'price_change_percent': price_change * 100,
            'is_direction_correct': is_direction_correct,
            'is_target_reached': is_target_reached,
            'accuracy_score': accuracy_score,
            'evaluation_note': generate_evaluation_note(...)
        }

        await db.prediction_tracking.insert(evaluation)
```

#### Task 4.2: analysis_history_service.py (1.5天)

**新文件**: `backend/app/services/analysis_history_service.py`

**功能**:
```python
async def get_stock_history(code: str, user_id: str, days: int = 30) -> List[Dict]:
    """获取股票历史分析记录"""
    records = await db.analysis_history.query(
        code=code,
        start_date=date.today() - timedelta(days=days),
        order_by='analysis_date DESC'
    )

    # 关联评估结果
    for record in records:
        evaluation = await db.prediction_tracking.get_by_analysis_id(record.id)
        record['evaluation'] = evaluation

    return records

async def get_accuracy_stats(code: str, user_id: str) -> Dict:
    """获取预测准确率统计"""
    evaluations = await db.prediction_tracking.query_by_code(code)

    total = len(evaluations)
    correct = sum(1 for e in evaluations if e.is_direction_correct)

    return {
        'total_predictions': total,
        'correct_count': correct,
        'accuracy_rate': correct / total if total > 0 else 0,
        'avg_accuracy_score': sum(e.accuracy_score for e in evaluations) / total if total > 0 else 0
    }
```

#### Task 4.3: 每日快照定时任务 (1天)

**文件**: `backend/app/scheduler.py` (新建)

**使用APScheduler**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.trading_calendar_service import trading_calendar

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=17, minute=30)
async def daily_snapshot_job():
    """每日17:30保存所有自选股的分析快照"""

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        return

    # 获取所有用户的自选股
    all_watchlists = await db.watchlist.get_all()

    for item in all_watchlists:
        await prediction_tracking_service.save_daily_snapshot(
            code=item.code,
            user_id=item.user_id
        )

@scheduler.scheduled_job('cron', hour=18, minute=0)
async def evaluation_job():
    """每日18:00评估5个交易日前的预测"""

    if not trading_calendar.is_trading_day(date.today()):
        return

    # 获取5个交易日前的分析记录
    evaluation_date = trading_calendar.add_trading_days(date.today(), -5)
    old_analyses = await db.analysis_history.query(analysis_date=evaluation_date)

    for analysis in old_analyses:
        await prediction_tracking_service.evaluate_prediction(analysis.id)
```

**注册到main.py**:
```python
from app.scheduler import scheduler

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
```

#### Task 4.4: 历史分析API (0.5天)

**文件**: `backend/app/api/history.py` (新建)

```python
@router.get("/analysis/history/{code}")
async def get_analysis_history(code: str, user_id: str, days: int = 30):
    """获取股票历史分析记录"""
    return await analysis_history_service.get_stock_history(code, user_id, days)

@router.get("/analysis/accuracy/{code}")
async def get_accuracy_stats(code: str, user_id: str):
    """获取预测准确率统计"""
    return await analysis_history_service.get_accuracy_stats(code, user_id)
```

### 4.2 Sprint 5: 历史前端 (第6周)

#### Task 5.1: 历史复盘页面 (2天)

**新文件**: `app/watchlist/[code]/history/page.tsx`

**布局**: 时间轴视图

```tsx
export default async function HistoryPage({ params }: { params: { code: string } }) {
  const history = await fetchAnalysisHistory(params.code);
  const stats = await fetchAccuracyStats(params.code);

  return (
    <div>
      {/* 当前分析 */}
      <CurrentAnalysisSection />

      {/* 准确率统计 */}
      <AccuracyStatsSection {...stats} />

      {/* 历史时间轴 */}
      <HistoryTimeline records={history} />

      {/* 持续跟踪建议 */}
      <TrackingInsightsSection />
    </div>
  );
}
```

**新组件**:
- `components/AccuracyStatsSection.tsx`
- `components/HistoryTimeline.tsx`
- `components/TimelineEntry.tsx`
- `components/TrackingInsightsSection.tsx`

#### Task 5.2: 准确率显示组件 (1.5天)

**组件**: `components/AccuracyStatsSection.tsx`

```tsx
export function AccuracyStatsSection({ stats }: { stats: AccuracyStats }) {
  return (
    <div className="accuracy-stats">
      <h3>预测准确率统计</h3>
      <div className="stats-grid">
        <StatCard
          label="总预测次数"
          value={stats.total_predictions}
        />
        <StatCard
          label="准确预测"
          value={stats.correct_count}
        />
        <StatCard
          label="准确率"
          value={`${(stats.accuracy_rate * 100).toFixed(1)}%`}
          highlight={stats.accuracy_rate > 0.6}
        />
        <StatCard
          label="平均准确度分数"
          value={stats.avg_accuracy_score.toFixed(1)}
        />
      </div>
    </div>
  );
}
```

#### Task 5.3: 时间轴组件 (1天)

**组件**: `components/HistoryTimeline.tsx`

```tsx
export function HistoryTimeline({ records }: { records: AnalysisRecord[] }) {
  return (
    <div className="timeline">
      {records.map(record => (
        <TimelineEntry key={record.id} {...record} />
      ))}
    </div>
  );
}

function TimelineEntry({ record }: { record: AnalysisRecord }) {
  const { evaluation } = record;

  return (
    <div className="timeline-entry">
      <div className="timeline-date">
        {record.analysis_date}
        {evaluation && (
          <span className="evaluation-badge">
            {evaluation.is_direction_correct ? '✅ 准确' : '❌ 不准'}
          </span>
        )}
      </div>

      <div className="timeline-content">
        <div className="prediction">
          <strong>预测：</strong>{record.prediction_text}
        </div>
        <div className="price">
          当时价格：¥{record.price}
        </div>

        {evaluation && (
          <div className="evaluation">
            <div>5天后实际：¥{evaluation.actual_price}</div>
            <div>变化：{evaluation.price_change_percent > 0 ? '+' : ''}{evaluation.price_change_percent.toFixed(2)}%</div>
            <div>准确度分数：{evaluation.accuracy_score}/100</div>
          </div>
        )}
      </div>
    </div>
  );
}
```

#### Task 5.4: "查看历史"按钮 (0.5天)

**修改**: `components/WatchlistStockCard.tsx`

```tsx
<button onClick={() => router.push(`/watchlist/${code}/history`)}>
  查看历史
</button>
```

#### Task 5.5: 集成测试 (1天)

**测试文件**: `backend/tests/test_prediction_flow.py`

**测试场景**: 完整的从分析→快照→评估流程

```python
@pytest.mark.asyncio
async def test_full_prediction_flow():
    """测试完整的预测追踪流程"""

    # 1. 生成综合分析
    analysis = await comprehensive_analysis_service.generate_comprehensive_analysis('600519')
    assert analysis is not None

    # 2. 保存快照
    await prediction_tracking_service.save_daily_snapshot('600519', 'test_user')

    # 3. 模拟5天后
    # ... mock 5天后的价格

    # 4. 评估预测
    # ... 验证评估结果正确
```

### 4.3 Phase 2 验收标准

**Exit Criteria**:
- [ ] 分析历史每日自动保存
- [ ] 5天后预测评估自动运行
- [ ] 历史复盘页面功能完整
- [ ] 准确率统计正确计算
- [ ] 时间轴正确展示
- [ ] 集成测试通过
- [ ] QA Guardian审核通过

---

## 5. Phase 3: 打磨与发布 (第7周)

### 5.1 UI打磨（2天）

#### Task 6.1: 统一样式和加载状态

**任务**:
- 所有组件使用一致的 loading skeleton
- 统一错误提示样式
- 统一颜色主题
- 添加动画效果（fade-in, slide-in）

**文件**:
- `components/LoadingSkeleton.tsx`
- `components/ErrorMessage.tsx`
- `tailwind.config.js` - 统一配色

#### Task 6.2: 移动端适配测试

**测试设备**:
- iPhone SE (375px)
- iPhone 14 (390px)
- iPad (768px)

**检查项**:
- 所有页面响应式布局正常
- 触摸交互流畅
- 字体大小合适

### 5.2 性能优化（1天）

#### Task 6.3: 懒加载和代码分割

**优化**:
```tsx
// 懒加载重组件
const HistoryTimeline = lazy(() => import('./components/HistoryTimeline'));
const ComprehensiveAnalysis = lazy(() => import('./components/ComprehensiveAnalysis'));

// 使用 Suspense
<Suspense fallback={<LoadingSkeleton />}>
  <HistoryTimeline />
</Suspense>
```

#### Task 6.4: 缓存验证

**验证**:
- Browser cache headers正确
- API响应缓存时长合理
- 数据库查询使用索引

### 5.3 QA验收（1天）

#### Task 6.5: 启动QA Guardian最终审核

**审核内容**:
- 功能完整性检查
- 性能目标验证
- 合规性检查
- 文档完整性

**生成**: `FINAL_QA_REPORT.md`

### 5.4 合规最终审查（0.5天）

#### Task 6.6: 全站免责声明检查

**检查清单**:
- [ ] 每个页面footer有免责声明
- [ ] 股票详情页有单页免责
- [ ] 历史复盘页有预测追踪免责
- [ ] API响应无禁止用语
- [ ] 所有"建议"改为"参考信息"

### 5.5 文档更新（0.5天）

#### Task 6.7: 更新所有文档

**更新**:
- `DESIGN.md` → 标记为已归档
- `PROGRESS.md` → 更新为"v2.0 开发完成"
- `README.md` → 添加v2.0功能说明
- `API_DOCS.md` → 补充所有新端点

### 5.6 部署验证（0.5天）

#### Task 6.8: 部署到生产环境

**步骤**:
1. 推送代码到 GitHub
2. Netlify 自动部署前端
3. Render 自动部署后端
4. Supabase 执行数据库迁移

**验证**:
```bash
# 验证前端
curl https://my-stock-advisor.netlify.app/

# 验证后端
curl https://stock-advisor-api-6vtb.onrender.com/health

# 验证API
curl https://stock-advisor-api-6vtb.onrender.com/api/v1/stock/600519/comprehensive
```

### 5.7 Phase 3 验收标准

**Launch Readiness Checklist** (参考 PRD Section 12.1):

**P0 - Must Complete**:
- [ ] 综合分析返回所有5个维度
- [ ] 每日推荐生成10只股票
- [ ] 自选股：添加、移除、刷新功能正常
- [ ] 全局刷新在2分钟内完成20只股票
- [ ] Token监控显示警告
- [ ] 历史分析每日自动保存
- [ ] 5天预测评估自动运行
- [ ] 时间轴显示历史分析
- [ ] 准确率统计正确
- [ ] 所有页面有免责声明
- [ ] 移动端响应式正常
- [ ] 所有错误处理完善
- [ ] 无硬编码API key

**Performance**:
- [ ] 综合分析 < 5秒
- [ ] 首页加载 < 2秒
- [ ] API响应 < 500ms (缓存命中)

---

## 6. 代码变更清单

### 6.1 新增后端文件

**Services**:
- `backend/app/services/news_service.py`
- `backend/app/services/fundamental_service.py`
- `backend/app/services/industry_service.py`
- `backend/app/services/comprehensive_analysis_service.py`
- `backend/app/services/watchlist_service.py`
- `backend/app/services/prediction_tracking_service.py`
- `backend/app/services/analysis_history_service.py`
- `backend/app/services/token_monitor_service.py`
- `backend/app/services/rate_limiter_service.py`
- `backend/app/services/trading_calendar_service.py`

**API**:
- `backend/app/api/comprehensive.py`
- `backend/app/api/watchlist.py`
- `backend/app/api/history.py`
- `backend/app/api/refresh.py`
- `backend/app/api/token.py`

**Infrastructure**:
- `backend/app/scheduler.py`
- `backend/app/prompts/comprehensive_analysis_prompt.py`

**Data**:
- `backend/data/trading_calendar_static.json`

**Tests**:
- `backend/tests/test_indicator_service.py`
- `backend/tests/test_news_service.py`
- `backend/tests/test_fundamental_service.py`
- `backend/tests/test_industry_service.py`
- `backend/tests/test_comprehensive_service.py`
- `backend/tests/test_prediction_flow.py`

**Database**:
- `backend/app/db/migrations/001_create_v2_tables.sql`

### 6.2 修改后端文件

- `backend/app/main.py` - 注册新路由、添加限流、启动scheduler
- `backend/app/config.py` - 可能需要添加新配置项
- `backend/app/services/strategy_service.py` - 使用综合分析生成推荐
- `backend/requirements.txt` - 添加依赖

### 6.3 新增前端文件

**Pages** (Next.js App Router):
- `app/watchlist/[code]/history/page.tsx`

**Components**:
- `components/TechnicalAnalysisSection.tsx`
- `components/CompanyAnalysisSection.tsx`
- `components/FundamentalAnalysisSection.tsx`
- `components/RecentDevelopmentsSection.tsx`
- `components/IndustryAnalysisSection.tsx`
- `components/ComprehensiveSummarySection.tsx`
- `components/WatchlistTab.tsx`
- `components/WatchlistStockCard.tsx`
- `components/TokenBadge.tsx`
- `components/RefreshAllButton.tsx`
- `components/ProgressBar.tsx`
- `components/AccuracyStatsSection.tsx`
- `components/HistoryTimeline.tsx`
- `components/TimelineEntry.tsx`
- `components/TrackingInsightsSection.tsx`

### 6.4 修改前端文件

- `app/stock/[code]/page.tsx` - 使用新的5维分析
- `app/page.tsx` 或 `components/HomeContent.tsx` - 添加自选股Tab
- `lib/api.ts` - 添加新API调用函数、SSE客户端
- `lib/types.ts` - 添加新类型定义
- `package.json` - 可能添加依赖

### 6.5 配置文件

- `.github/workflows/ci.yml` (新建)
- `backend/.env.example` - 添加新环境变量
- `backend/render.yaml` - 可能需要调整

---

## 7. 测试要求

### 7.1 单元测试

**覆盖率目标**: > 80%

**关键服务测试**:
- `indicator_service` - 技术指标计算准确性
- `comprehensive_analysis_service` - 数据获取和整合
- `prediction_tracking_service` - 预测评估逻辑
- `trading_calendar_service` - 交易日判断

### 7.2 集成测试

**测试场景**:
- 完整的股票查询流程（API → Service → 数据库）
- 推荐生成流程
- 自选股管理流程
- 预测追踪完整流程

### 7.3 E2E测试

**工具**: Playwright

**测试场景**:
1. 股票查询流程
2. 查看今日推荐
3. 添加/移除自选股
4. 全局刷新
5. 查看历史复盘

**执行**:
```bash
npx playwright test
```

### 7.4 性能测试

**测试**:
- 综合分析响应时间 < 5秒
- 全局刷新20只股票 < 2分钟
- 首页加载 < 2秒
- 并发10个查询测试

---

## 8. 部署检查清单

### 8.1 环境变量配置

**Render (后端)**:
```
SUPABASE_URL=https://...
SUPABASE_KEY=...
GLM_API_KEY=...
DEBUG=false
```

**Netlify (前端)**:
```
NEXT_PUBLIC_API_URL=https://stock-advisor-api-6vtb.onrender.com
```

### 8.2 数据库迁移

**Supabase SQL Editor**:
1. 执行 `001_create_v2_tables.sql`
2. 验证所有表创建成功
3. 验证索引创建成功

### 8.3 静态数据初始化

**交易日历**:
- 上传 `trading_calendar_static.json` 到 Render

**热门股票池**:
- 执行初始化脚本，插入60只热门股票到 `hot_stock_universe` 表

### 8.4 定时任务验证

**测试**:
- 验证17:30推荐生成任务执行
- 验证17:30快照保存任务执行
- 验证18:00预测评估任务执行

### 8.5 监控和告警

**配置**:
- Render 服务健康检查
- Sentry 错误追踪（可选）
- Token使用监控告警

---

## 9. 附录

### 9.1 依赖版本

**Backend** (`requirements.txt`):
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic-settings==2.1.0
python-multipart==0.0.6
supabase==2.3.0
pandas==2.2.0
pandas-ta==0.3.14b
akshare==1.12.0
yfinance==0.2.35
slowapi==0.1.9
apscheduler==3.10.4
psutil==5.9.8
pytest==8.0.0
pytest-cov==4.1.0
pytest-asyncio==0.23.4
```

**Frontend** (`package.json`):
```json
{
  "dependencies": {
    "next": "15.1.0",
    "react": "19.0.0",
    "typescript": "5.3.3",
    "@types/node": "20.11.0",
    "@types/react": "19.0.0"
  }
}
```

### 9.2 关键文档索引

| 文档 | 用途 |
|------|------|
| PRD_v2.0.md | 产品需求（91分，权威） |
| ARCHITECTURE.md | 技术架构（91分，权威） |
| QA_PRD_REVIEW.md | PRD审查报告 |
| QA_ARCHITECTURE_REVIEW.md | 架构审查报告 |
| DEVELOPMENT_PLAN.md | 本文档 - 开发计划 |
| TEST_CASES.md | 测试用例 |
| PROGRESS.md | 开发进度追踪 |

---

**文档结束**

这份开发计划文档提供了从Phase 0到Phase 3的完整实施路径。每个任务都有明确的：
- 文件位置
- 代码示例
- 验收标准
- 测试要求

开发团队可以直接按照此计划执行，所有设计决策都已经过QA Guardian的91分审核。
