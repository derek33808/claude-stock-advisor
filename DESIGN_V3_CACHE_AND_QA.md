# Stock Advisor v3.0 产品设计方案

# 需求一：智能缓存机制 + 需求二：AI 股票问答

**版本**: v3.0
**日期**: 2026-02-09
**作者**: Product Orchestrator
**状态**: 待评审

---

## 1. 需求分析

### 1.1 用户痛点深度剖析

**痛点1：加载速度极慢**

根据代码审查，当前系统每次请求的数据流程：

```
用户打开详情页 /stock/{code}
  -> 调用 eastmoney_service.get_history(code, days=60)    [1-3秒，含重试]
  -> 调用 eastmoney_service.get_realtime(code)             [1-2秒]
  -> 计算 indicator_service.calculate_indicators(df)        [<0.1秒]
  -> 生成 strategy_service 交易建议                         [<0.1秒]
  -> 调用 GLM-4 generate_summary_with_fallback             [3-8秒]
  -> 调用 GLM-4 get_full_ai_analysis (3次API调用)          [10-20秒]
  -> 总计: 15-30秒
```

推荐列表页：

```
/recommendations API
  -> 从 Supabase 读推荐列表                      [1秒]
  -> 逐个调用 eastmoney.get_realtime(10只)       [10-20秒]
  -> 总计: 11-21秒
```

自选股列表：

```
/refresh/all SSE
  -> 逐个调用 comprehensive_analysis_service     [每只15-30秒]
  -> 5只自选股 = 75-150秒（1-2.5分钟）
  -> 10只自选股 = 150-300秒（2.5-5分钟）
```

**问题根源**:
1. 后端内存缓存 `_stock_analysis_cache` 只有3分钟有效期
2. Render 免费版休眠后内存缓存全部丢失
3. 每次详情页访问都触发3次 GLM-4 API 调用
4. 推荐列表的实时价格逐个串行获取
5. 60天历史K线数据每次从东方财富实时拉取
6. Supabase 的 `stock_cache` 表虽存在，但实际未在核心流程中使用

**痛点2：缺乏针对性的股票问答能力**

用户目前只能获取系统预设的分析内容（技术指标、交易建议、AI摘要），无法进一步提问。例如：
- "这家公司最近有什么重大事件？"
- "它的财报表现怎么样？"
- "跟同行业比有什么优势？"
- "现在适合加仓吗？"

这些问题当前系统无法回答，用户需要离开系统去其他平台查询。

### 1.2 核心诉求提炼

| 诉求 | 优先级 | 衡量指标 |
|------|--------|---------|
| 详情页秒开（非首次访问） | P0 | 缓存命中时 <1秒 |
| 推荐列表快速显示 | P0 | <2秒返回（含实时价格） |
| 自选股列表不用每次全量刷新 | P0 | 列表页 <2秒，按需刷新 |
| 历史K线不重复获取 | P1 | 当日只获取一次 |
| AI分析结果可复用 | P1 | 相同分析4小时内不重复调用 |
| 能问AI任何关于个股的问题 | P1 | 支持自由问答 |
| Token成本可控 | P1 | 问答单次 <1000 token |

---

## 2. 方案设计：需求一 - 智能缓存机制

### 2.1 设计理念

**分层缓存 + 按需刷新**

核心思路：将"数据获取"和"数据展示"解耦。用户大部分时间看到的应该是缓存数据，只有主动要求或定时任务才触发真正的数据刷新。

```
┌──────────────────────────────────────────────────────┐
│                    前端 (Netlify)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ 列表页      │  │ 详情页      │  │ 自选股页    │  │
│  │ 读DB缓存    │  │ 读DB缓存    │  │ 读DB缓存    │  │
│  │ +实时价格   │  │ +按需刷新   │  │ +按需刷新   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└───────────────────────────┬──────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────┐
│                    后端 (Render)                       │
│                                                       │
│  ┌───────────────────────────────────────────────┐   │
│  │              第1层: 内存缓存                    │   │
│  │  实时价格缓存 (30秒TTL, dict)                  │   │
│  │  轻量、快速、Render休眠后丢失无影响            │   │
│  └───────────────────────────────────────────────┘   │
│                         │ miss                        │
│  ┌───────────────────────▼───────────────────────┐   │
│  │              第2层: Supabase 持久缓存           │   │
│  │  stock_analysis_cache (完整分析结果)            │   │
│  │  stock_quote_cache (实时行情快照)               │   │
│  │  stock_kline_cache (日K线数据)                  │   │
│  │  ai_analysis_cache (AI分析结果)                 │   │
│  │  持久化、不怕休眠、跨请求共享                  │   │
│  └───────────────────────────────────────────────┘   │
│                         │ miss or expired             │
│  ┌───────────────────────▼───────────────────────┐   │
│  │              第3层: 数据源 (东方财富/Yahoo)      │   │
│  │  实时行情 API                                   │   │
│  │  历史K线 API                                    │   │
│  │  GLM-4 AI 分析                                  │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 2.2 缓存策略设计

#### 2.2.1 数据分类与过期策略

| 数据类型 | 时效性要求 | 缓存位置 | 过期时间 | 刷新时机 |
|---------|-----------|---------|---------|---------|
| **实时价格** | 高（秒级） | 内存 | 30秒 | 每次请求 |
| **日K线数据** | 低（日级） | Supabase | 当天收盘后有效 | 每日17:00调度 |
| **技术指标** | 低（日级） | Supabase | 随K线一起刷新 | 每日17:00调度 |
| **交易建议** | 中（小时级） | Supabase | 4小时 | 随分析刷新 |
| **AI分析结果** | 低（小时级） | Supabase | 4小时 | 按需或调度 |
| **推荐列表** | 低（日级） | Supabase | 当天有效 | 每日17:00 |
| **新闻资讯** | 中（小时级） | Supabase | 已有表 | 已实现 |

#### 2.2.2 关键判断：何时认为缓存有效？

```python
# 交易时段: 9:30-11:30, 13:00-15:00
# 非交易时段: 其他时间

def is_cache_valid(cache_time: datetime, data_type: str) -> bool:
    now = datetime.now()
    age = now - cache_time

    if data_type == "realtime_quote":
        # 盘中: 30秒过期; 非盘中: 不过期(下个交易日开盘前有效)
        if is_trading_hours(now):
            return age < timedelta(seconds=30)
        else:
            return True  # 收盘后价格不变，永远有效直到次日开盘

    elif data_type == "kline":
        # 当天收盘后生成的缓存，到第二天开盘前都有效
        if cache_time.date() == now.date():
            return True
        elif cache_time.date() == get_last_trading_day(now):
            return not is_trading_hours(now)  # 昨天的缓存，今天开盘前有效
        return False

    elif data_type == "analysis":
        # 4小时过期
        return age < timedelta(hours=4)

    elif data_type == "ai_result":
        # 4小时过期（节省Token）
        return age < timedelta(hours=4)

    return False
```

### 2.3 数据库设计

#### 2.3.1 新增表：stock_analysis_cache（核心缓存表）

替代现有的 `stock_cache` 表，存储完整的分析结果。

```sql
-- 股票完整分析结果缓存
-- 每只股票一行，upsert 更新
CREATE TABLE stock_analysis_cache (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50),
    industry VARCHAR(50),

    -- 实时行情快照（最近一次刷新的价格）
    price DECIMAL(10,3),
    change_percent DECIMAL(5,2),
    open_price DECIMAL(10,3),
    high_price DECIMAL(10,3),
    low_price DECIMAL(10,3),
    prev_close DECIMAL(10,3),
    volume BIGINT,
    amount BIGINT,
    market_cap DECIMAL(12,2),
    quote_updated_at TIMESTAMPTZ,        -- 行情更新时间

    -- 技术指标 (JSON)
    indicators JSONB,                     -- 完整技术指标
    -- 交易建议 (JSON)
    suggestion JSONB,                     -- 交易建议
    -- 推荐理由
    reasons JSONB,                        -- string[]
    -- 综合评分
    score INTEGER,

    -- AI 分析结果 (JSON)
    ai_summary TEXT,                      -- 交易指导摘要
    ai_company JSONB,                     -- 公司分析
    ai_fundamental JSONB,                 -- 基本面分析
    ai_recommendation JSONB,              -- AI评分和建议
    ai_ranking_score INTEGER,
    ai_updated_at TIMESTAMPTZ,           -- AI分析更新时间

    -- 缓存元数据
    full_analysis_updated_at TIMESTAMPTZ, -- 完整分析更新时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sac_updated ON stock_analysis_cache(full_analysis_updated_at);
CREATE INDEX idx_sac_quote_updated ON stock_analysis_cache(quote_updated_at);
```

#### 2.3.2 新增表：stock_kline_cache（K线数据缓存）

```sql
-- K线数据缓存
-- 按股票代码+日期存储，避免重复拉取
CREATE TABLE stock_kline_cache (
    code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(10,3),
    high_price DECIMAL(10,3),
    low_price DECIMAL(10,3),
    close_price DECIMAL(10,3),
    volume BIGINT,
    amount BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (code, trade_date)
);

CREATE INDEX idx_skc_code ON stock_kline_cache(code);
CREATE INDEX idx_skc_date ON stock_kline_cache(trade_date DESC);
```

#### 2.3.3 新增表：stock_chat_history（AI问答历史 -- 需求二使用）

```sql
-- AI 问答历史记录
CREATE TABLE stock_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,            -- 股票代码
    user_id VARCHAR(100) NOT NULL,        -- 用户ID
    question TEXT NOT NULL,               -- 用户问题
    answer TEXT NOT NULL,                 -- AI回答
    context_type VARCHAR(50),             -- 上下文类型: general/financial/news/comparison
    tokens_used INTEGER DEFAULT 0,        -- Token消耗
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sch_code_user ON stock_chat_history(code, user_id);
CREATE INDEX idx_sch_created ON stock_chat_history(created_at DESC);
```

### 2.4 后端 API 设计

#### 2.4.1 改造现有 API：GET /stock/{code} -- 缓存优先

**改造前**（当前）：
```
每次请求 -> 东方财富API(历史) -> 东方财富API(实时) -> 指标计算 -> GLM-4 x3
总耗时: 15-30秒
```

**改造后**:
```
请求参数: GET /stock/{code}?refresh=false

if refresh=false:
    1. 查询 stock_analysis_cache 表
    2. 如果缓存存在且 full_analysis_updated_at 在4小时内:
        a. 只更新实时价格 (内存缓存30秒 -> 东方财富API)
        b. 将缓存中的分析结果 + 最新价格合并返回
        c. 耗时: <1秒(内存命中) 或 1-2秒(调东方财富实时)
    3. 如果缓存不存在或已过期:
        a. 执行完整分析流程（同当前逻辑）
        b. 将结果写入 stock_analysis_cache
        c. 耗时: 15-30秒（同当前）

if refresh=true:
    1. 跳过缓存，执行完整分析
    2. 更新 stock_analysis_cache
    3. 耗时: 15-30秒
```

**新增响应字段**：
```json
{
    "...现有字段...",
    "cache_info": {
        "cached": true,
        "analysis_age_minutes": 45,
        "quote_age_seconds": 15,
        "next_refresh_hint": "数据缓存中，点击刷新获取最新分析"
    }
}
```

#### 2.4.2 改造现有 API：GET /recommendations -- 批量价格优化

**改造前**（当前）：
```python
for rec in recommendations:
    realtime = eastmoney_service.get_realtime(rec["code"])  # 串行，每个1-2秒
```

**改造后**:
```
新增: GET /quotes/batch?codes=600519,000858,300750,...

1. 东方财富 API 支持批量行情查询（多个secid用逗号分隔）
2. 一次请求获取所有股票的实时价格
3. 耗时: 1-2秒（无论多少只，单次HTTP请求）
```

**批量行情API实现**：
```python
def get_batch_realtime(codes: list[str]) -> dict[str, dict]:
    """
    批量获取实时行情
    利用东方财富API支持多secid的特性
    """
    secids = ",".join([f"{_get_market_code(c)}.{c}" for c in codes])
    url = (f"https://push2.eastmoney.com/api/qt/ulist.np/get?"
           f"fltt=2&secids={secids}"
           f"&fields=f2,f3,f12,f14,f15,f16,f17,f18")
    # 单次HTTP请求，返回所有股票的价格
    ...
```

**改造后的 /recommendations 流程**：
```
1. Supabase 读取推荐列表        [<1秒]
2. 批量获取10只股票实时价格      [1-2秒]
3. 合并返回                      [<0.1秒]
总计: <3秒 (原来 11-21秒)
```

#### 2.4.3 新增 API：POST /cache/warm -- 缓存预热

```
POST /cache/warm
Body: { "codes": ["600519", "000858", ...] }

功能：
- 后台批量预热指定股票的缓存
- 不返回数据，只写入缓存
- 由调度器在 17:00 生成推荐后自动调用

返回：
{
    "triggered": true,
    "codes_count": 10,
    "estimated_seconds": 150
}
```

#### 2.4.4 新增 API：GET /stock/{code}/quick -- 轻量快速查询

```
GET /stock/{code}/quick

功能：
- 只返回缓存中的基本信息 + 最新价格
- 不包含 AI 分析、不触发 GLM 调用
- 用于列表页快速显示

返回：
{
    "code": "600519",
    "name": "贵州茅台",
    "industry": "白酒",
    "price": 1720.00,        // 实时
    "change": 2.35,          // 实时
    "score": 75,             // 缓存
    "action": "买入",        // 缓存
    "cache_age_minutes": 30  // 缓存年龄
}

耗时: <1秒
```

### 2.5 调度器改造

#### 2.5.1 新增定时任务：缓存预热（17:10）

```python
@scheduler.scheduled_job('cron', hour=17, minute=10, id='cache_warm')
async def cache_warm_job():
    """
    每日17:10 缓存预热
    在推荐生成（17:00）之后执行
    预热推荐股 + 自选股的完整分析缓存
    """
    # 1. 获取需要预热的股票列表
    #    - 今日推荐的10只
    #    - 所有用户的自选股（去重）
    #    - 热门股票池
    codes = set()

    # 推荐股
    _, recs = await db.get_latest_recommendations()
    for rec in recs:
        codes.add(rec['code'])

    # 自选股
    result = supabase.table('watchlist').select('code').execute()
    for item in result.data:
        codes.add(item['code'])

    # 2. 逐个生成完整分析并写入缓存
    for code in codes:
        try:
            analysis = await generate_and_cache_analysis(code)
        except Exception as e:
            print(f"[CacheWarm] Failed for {code}: {e}")
            continue

    # 3. 批量获取实时价格并更新
    quotes = eastmoney_service.get_batch_realtime(list(codes))
    for code, quote in quotes.items():
        await update_quote_cache(code, quote)
```

#### 2.5.2 现有调度器调整

```
17:00  daily_recommendations  -- 生成推荐 (不变)
17:10  cache_warm             -- 缓存预热 (新增)
17:30  daily_snapshot         -- 保存快照 (不变，但可读缓存加速)
18:00  evaluation_job         -- 评估预测 (不变)
```

### 2.6 前端改造

#### 2.6.1 详情页：缓存优先 + 渐进加载

```
StockDetailClient 改造:

1. 进入页面，立即显示骨架屏
2. 调用 GET /stock/{code} (默认 refresh=false)
   -> 缓存命中: <1秒返回，直接渲染
   -> 缓存未命中: 显示加载状态，等待完整分析
3. 页面底部显示 "数据更新于 X 分钟前"
4. 添加 "刷新分析" 按钮
   -> 点击后调用 GET /stock/{code}?refresh=true
   -> 显示进度条，等待新分析
```

```typescript
// 新的获取逻辑
export async function getStockAnalysis(
  code: string,
  refresh: boolean = false
): Promise<StockAnalysis> {
  // 前端也保留短期缓存（避免频繁返回同一页面重复请求）
  if (!refresh) {
    const cached = stockCache.get(code);
    if (cached && Date.now() - cached.timestamp < STOCK_CACHE_MS) {
      return cached.data;
    }
  }

  const refreshParam = refresh ? '&refresh=true' : '';
  const data = await apiRequest<StockAnalysis>(
    `/stock/${code}?${refreshParam}`
  );

  stockCache.set(code, { data, timestamp: Date.now() });
  return data;
}
```

#### 2.6.2 详情页 UI 调整

```
新增元素:
1. 顶部 badge: "缓存数据 | 45分钟前更新" (灰色)
   或 "实时分析 | 刚刚更新" (绿色)

2. 右上角刷新按钮:
   [刷新分析] -- 触发完整重新分析
   点击后变为 [分析中...] + 进度条

3. 价格区域:
   显示实时价格（即使其他数据是缓存的）
   小字: "行情实时 | 分析缓存"
```

#### 2.6.3 推荐列表页：即时显示

```
HomeContent 改造:

当前: 调用 /recommendations -> 等待 -> 显示
改后: 调用 /recommendations -> 即时显示（后端已优化为批量价格）

预期效果:
- 推荐列表 <2秒显示
- 价格为实时数据
- 分析摘要为缓存数据
```

#### 2.6.4 自选股列表：按需加载

```
当前: 打开自选股列表 -> 逐个获取分析 -> 漫长等待
改后:

1. 打开自选股列表
   -> 调用 GET /quotes/batch 获取所有自选股价格 [<2秒]
   -> 从 stock_analysis_cache 读取缓存的分析数据 [<1秒]
   -> 立即展示列表

2. 每只股票卡片显示:
   - 股票名称、代码
   - 实时价格和涨跌
   - 缓存的评分和建议
   - "分析更新于 X 分钟前"

3. 点击进入详情 -> 读缓存秒开

4. 手动刷新按钮 -> 仅刷新选中的单只股票
```

### 2.7 内存预算分析（Render 512MB）

```
当前内存使用估算:
- Python 进程基础:              ~80MB
- FastAPI + uvicorn:           ~30MB
- pandas + numpy:              ~50MB
- APScheduler:                 ~5MB
- Supabase SDK:                ~10MB
- 代码本身:                    ~15MB
- 临时数据处理:                ~50MB
- 合计:                        ~240MB

新增缓存内存:
- 实时价格缓存 (50只, dict):   ~0.1MB
- 临时DataFrame (60天K线):     ~2MB per stock
- 峰值: 调度器批量处理时:      ~40MB (同时处理20只)

总计: ~280MB / 512MB = 55% 使用率
结论: 内存安全。主要缓存放Supabase，内存只放实时价格。
```

---

## 3. 方案设计：需求二 - AI 股票问答

### 3.1 设计理念

**轻量问答 + 上下文复用**

不做通用聊天机器人，而是做**股票详情页内的轻量问答**。核心原则：
1. 问答发生在已有分析上下文中（用户正在看某只股票）
2. 将缓存的分析结果作为上下文，减少 Token 消耗
3. 预设常见问题模板，降低无效提问
4. 单轮问答为主，不维护长对话历史

### 3.2 功能设计

#### 3.2.1 入口位置

在股票详情页底部（风险提示之前），新增 "AI 问答" 区域：

```
┌─────────────────────────────────────┐
│  交易指导                    [已有]  │
│  ...                                │
├─────────────────────────────────────┤
│  历史分析记录                [已有]  │
│  ...                                │
├─────────────────────────────────────┤
│  AI 股票问答                 [新增]  │
│                                     │
│  常见问题:                          │
│  [财报分析] [近期资讯] [同行对比]   │
│  [技术解读] [风险提示]              │
│                                     │
│  ┌─────────────────────────┐ [发送] │
│  │ 输入你的问题...          │       │
│  └─────────────────────────┘       │
│                                     │
│  (问答历史)                         │
│  Q: 这家公司最近有什么利好？        │
│  A: 根据近期资讯，贵州茅台...       │
│                                     │
│  Q: 财报表现怎么样？                │
│  A: 最新财报显示...                 │
│                                     │
│  今日已提问 2/10 次                 │
└─────────────────────────────────────┘
```

#### 3.2.2 预设问题模板

| 模板 | 对应 Prompt 方向 | 需要的上下文 |
|------|-----------------|-------------|
| 财报分析 | 分析公司最新财报数据 | fundamental_service 数据 |
| 近期资讯 | 总结近期新闻和公告 | news_service 数据 |
| 同行对比 | 与同行业公司对比 | industry_service 数据 |
| 技术解读 | 解读当前技术指标含义 | 缓存的 indicators |
| 风险提示 | 分析当前持有风险 | 综合分析数据 |

#### 3.2.3 自由提问

用户也可以输入任意问题，系统将：
1. 自动注入股票基本上下文（代码、名称、价格、行业）
2. 注入缓存的分析结果摘要
3. 调用 GLM-4 回答

### 3.3 后端 API 设计

#### 3.3.1 新增 API：POST /stock/{code}/chat

```
POST /stock/{code}/chat
Body:
{
    "user_id": "default_user",
    "question": "这家公司最近有什么重要事件？",
    "template": "news"  // 可选，预设模板标识
}

Response:
{
    "code": "600519",
    "question": "这家公司最近有什么重要事件？",
    "answer": "根据近期公开信息，贵州茅台...",
    "context_type": "news",
    "tokens_used": 650,
    "remaining_quota": 8,
    "created_at": "2026-02-09T20:30:00Z"
}
```

#### 3.3.2 新增 API：GET /stock/{code}/chat/history

```
GET /stock/{code}/chat/history?user_id=default_user&limit=20

Response:
{
    "code": "600519",
    "count": 5,
    "history": [
        {
            "id": "uuid",
            "question": "...",
            "answer": "...",
            "context_type": "news",
            "tokens_used": 650,
            "created_at": "2026-02-09T20:30:00Z"
        },
        ...
    ]
}
```

### 3.4 Prompt 工程设计

#### 3.4.1 系统 Prompt（固定）

```python
CHAT_SYSTEM_PROMPT = """你是一位专业的A股分析师助手。用户正在查看一只股票的详细分析页面，
你需要根据提供的股票信息和分析数据，回答用户关于这只股票的问题。

要求：
1. 回答要专业、客观、有数据支撑
2. 使用简洁明了的中文
3. 不要编造不存在的数据，如果某些数据没有提供，请诚实说明
4. 控制回答长度在200字以内
5. 末尾加上简短的风险提示
6. 禁止给出明确的买入/卖出建议，只提供分析参考"""
```

#### 3.4.2 User Prompt 模板

```python
def build_chat_prompt(
    stock_context: dict,
    question: str,
    template: str = None,
    extra_data: dict = None
) -> str:
    """
    构建问答 Prompt

    stock_context: 来自 stock_analysis_cache 的缓存数据
    question: 用户问题
    template: 预设模板类型
    extra_data: 额外获取的数据（如新闻、财报）
    """

    base_context = f"""
## 股票信息
- 名称：{stock_context['name']}（{stock_context['code']}）
- 行业：{stock_context['industry']}
- 当前价格：¥{stock_context['price']}
- 涨跌幅：{stock_context['change']}%
- 市值：{stock_context.get('market_cap', '未知')}亿
- 综合评分：{stock_context.get('score', '未知')}/100
- 操作建议：{stock_context.get('action', '未知')}
"""

    # 根据模板添加额外上下文
    if template == "financial":
        # 注入基本面数据
        fundamental = stock_context.get('ai_fundamental', {})
        base_context += f"""
## 基本面数据
- 估值水平：{fundamental.get('valuation_level', '未知')}
- 盈利能力：{fundamental.get('profitability', '未知')}
- 投资价值评分：{fundamental.get('investment_value', '未知')}/10
"""
        if extra_data and extra_data.get('financial_report'):
            report = extra_data['financial_report']
            base_context += f"""
## 最新财报
- ROE：{report.get('roe', '未知')}%
- 营收同比：{report.get('revenue_yoy', '未知')}%
"""

    elif template == "news":
        if extra_data and extra_data.get('news'):
            news_list = extra_data['news'][:5]
            news_text = "\n".join([f"- [{n['date']}] {n['title']} ({n['type']})" for n in news_list])
            base_context += f"""
## 近期新闻
{news_text}
"""

    elif template == "comparison":
        if extra_data and extra_data.get('industry_data'):
            industry = extra_data['industry_data']
            peers = industry.get('leading_stocks', [])[:5]
            peers_text = "\n".join([f"- {p.get('name', '')}：涨跌{p.get('change', 0)}%" for p in peers])
            base_context += f"""
## 同行业公司
行业趋势：{industry.get('trend', '未知')}
{peers_text}
"""

    elif template == "technical":
        indicators = stock_context.get('indicators', {})
        base_context += f"""
## 技术指标
- MACD趋势：{indicators.get('macd', {}).get('trend', '未知')}
- RSI状态：{indicators.get('rsi', {}).get('level', '未知')}（值：{indicators.get('rsi', {}).get('value', 50)}）
- 均线排列：{indicators.get('ma', {}).get('alignment', '未知')}
- BOLL位置：{indicators.get('boll', {}).get('position', '未知')}
- 量比：{indicators.get('volume_ratio', 1)}
"""

    return f"""{base_context}

## 用户问题
{question}

请根据以上信息回答用户问题。"""
```

### 3.5 Token 成本控制

#### 3.5.1 成本估算

```
GLM-4-flash 价格（智谱AI免费额度内）:
- 输入: 0.1元/千tokens
- 输出: 0.1元/千tokens

单次问答 Token 消耗:
- System Prompt: ~200 tokens
- 股票上下文: ~300 tokens
- 用户问题: ~50 tokens
- AI回答: ~300 tokens
- 合计: ~850 tokens

每日成本估算:
- 假设每天 50 次问答
- 50 * 850 = 42,500 tokens
- 成本: 42,500 / 1000 * 0.2 = 8.5元/天

对比现有 AI 分析消耗:
- 每只股票完整分析: 3次GLM调用 * ~1500 tokens = 4500 tokens
- 每日推荐 10 只: 45,000 tokens
- 问答功能增加的 Token 消耗相对可控
```

#### 3.5.2 控制策略

| 限制项 | 限制值 | 说明 |
|-------|-------|------|
| 每日每用户问答次数 | 10次 | 超过后提示"今日额度已用完" |
| 单次问题长度 | 200字 | 前端输入框限制 |
| 单次回答长度 | max_tokens=400 | Prompt 限制 |
| 重复问题缓存 | 2小时 | 相同股票+相似问题，直接返回缓存 |
| 全局每日Token上限 | 500K tokens | 复用现有 TokenMonitor |

#### 3.5.3 相似问题匹配

```python
def find_similar_answer(code: str, question: str, hours: int = 2) -> Optional[str]:
    """
    查找2小时内相同股票的相似问题

    简单匹配策略（避免引入额外模型）：
    1. 相同模板类型的问题直接命中
    2. 自由提问：关键词重叠率 > 70% 认为相似
    """
    # 查询最近的问答记录
    recent = supabase.table('stock_chat_history') \
        .select('question, answer') \
        .eq('code', code) \
        .gte('created_at', (datetime.now() - timedelta(hours=hours)).isoformat()) \
        .execute()

    for item in recent.data:
        if calculate_keyword_overlap(question, item['question']) > 0.7:
            return item['answer']

    return None
```

### 3.6 前端设计

#### 3.6.1 StockChatPanel 组件

```typescript
// 新增组件：src/components/StockChatPanel.tsx

interface StockChatPanelProps {
  code: string;
  stockContext: {
    name: string;
    industry: string;
    price: number;
    change: number;
    score: number;
    indicators: any;
  };
}

// 预设问题
const QUICK_QUESTIONS = [
  { label: '财报分析', template: 'financial', icon: '📊' },
  { label: '近期资讯', template: 'news', icon: '📰' },
  { label: '同行对比', template: 'comparison', icon: '🏢' },
  { label: '技术解读', template: 'technical', icon: '📈' },
  { label: '风险提示', template: 'risk', icon: '⚠️' },
];
```

#### 3.6.2 交互流程

```
1. 用户点击预设问题或输入自由问题
2. 发送按钮变为加载状态
3. 调用 POST /stock/{code}/chat
4. 流式展示回答（或完整返回后展示）
5. 回答下方显示 "Token消耗: 650 | 今日剩余: 8/10次"
6. 问答记录保存在页面中（刷新后从API加载历史）
```

#### 3.6.3 UI 细节

- 问答区域可折叠，默认展开
- 历史记录最多显示最近5条，"查看更多"链接
- 发送中禁用输入框和按钮
- 回答使用略不同的背景色区分
- 错误时显示"AI暂时无法回答，请稍后重试"
- 额度用尽时隐藏输入框，显示提示

---

## 4. 技术可行性分析

### 4.1 Render 512MB 内存限制

| 方案组件 | 内存影响 | 评估 |
|---------|---------|------|
| 实时价格内存缓存 (dict) | +0.1MB | 可忽略 |
| Supabase 读写 | 无新增（已有SDK） | 无影响 |
| 批量行情 API | 无新增内存 | HTTP请求 |
| 问答 Prompt 构建 | +0.5MB (字符串) | 可忽略 |
| 缓存预热调度任务 | 峰值 +20MB | 串行处理，可控 |
| **总影响** | **+20MB 峰值** | **安全** |

**结论**: 所有缓存放 Supabase（第2层），内存只放实时价格（第1层），完全在512MB限制内。

### 4.2 Supabase 免费额度

```
Supabase 免费版限制:
- 数据库存储: 500MB
- API 请求: 无限（但有带宽限制 2GB/月）
- 行数: 无限

新增存储估算:
- stock_analysis_cache: 50只 * 5KB = 250KB
- stock_kline_cache: 50只 * 60天 * 100B = 300KB
- stock_chat_history: 100条/天 * 1KB = 100KB/天 = 3MB/月

总新增: <5MB/月
现有使用: ~10MB
结论: 远在 500MB 限制内
```

### 4.3 GLM-4 Token 成本

```
现有日均消耗:
- 每日推荐 (10只 * 3次调用): ~45K tokens
- 用户浏览触发分析 (~20次): ~90K tokens
- 调度任务 (快照 ~5只): ~22.5K tokens
- 合计: ~157.5K tokens/天

新增消耗:
- 问答功能 (50次/天): ~42.5K tokens
- 缓存减少的调用（分析结果复用4小时）: 节省约 -40K tokens

净变化: +2.5K tokens/天（几乎持平）
结论: 缓存机制节省的 Token 足以覆盖问答功能的消耗
```

### 4.4 东方财富 API 调用频率

```
现有调用模式:
- 每次详情页: 2次（历史+实时）
- 每次推荐列表: 10次（逐个实时）
- 调度任务: 20-30次

优化后:
- 详情页缓存命中: 0-1次（只取实时价格，30秒缓存）
- 推荐列表批量: 1次（替代10次串行）
- 调度任务不变

结论: 大幅减少 API 调用频率，降低被限流风险
```

---

## 5. 优先级和排期

### 5.1 任务拆解

#### Phase A：智能缓存核心（P0，预计 8-10h）

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|---------|------|
| A1: 创建 stock_analysis_cache 表 | P0 | 0.5h | 无 |
| A2: 创建 stock_kline_cache 表 | P0 | 0.5h | 无 |
| A3: 实现 cache_service.py（缓存读写） | P0 | 2h | A1, A2 |
| A4: 实现批量行情 API (get_batch_realtime) | P0 | 1.5h | 无 |
| A5: 改造 GET /stock/{code} 缓存优先 | P0 | 2h | A3 |
| A6: 改造 GET /recommendations 批量价格 | P0 | 1h | A4 |
| A7: 前端详情页缓存UI（缓存提示+刷新按钮） | P0 | 1.5h | A5 |
| A8: 前端推荐列表响应优化 | P0 | 1h | A6 |

#### Phase B：缓存预热和调度（P1，预计 3-4h）

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|---------|------|
| B1: 实现 cache_warm_job 调度任务 | P1 | 1.5h | A3 |
| B2: 自选股列表读缓存快速展示 | P1 | 1.5h | A3, A4 |
| B3: K线数据缓存实现 | P1 | 1h | A2, A3 |

#### Phase C：AI 问答功能（P1，预计 6-8h）

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|---------|------|
| C1: 创建 stock_chat_history 表 | P1 | 0.5h | 无 |
| C2: 实现问答 Prompt 工程 | P1 | 1.5h | 无 |
| C3: 实现 POST /stock/{code}/chat API | P1 | 2h | C1, C2 |
| C4: 实现 GET /stock/{code}/chat/history | P1 | 0.5h | C1 |
| C5: 实现问答频率控制 | P1 | 1h | C3 |
| C6: 前端 StockChatPanel 组件 | P1 | 2h | C3, C4 |
| C7: 集成到详情页 | P1 | 0.5h | C6, A5 |

#### Phase D：测试和优化（P1，预计 2-3h）

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|---------|------|
| D1: 缓存机制 E2E 测试 | P1 | 1h | A全部 |
| D2: 问答功能 E2E 测试 | P1 | 1h | C全部 |
| D3: 性能基准测试 | P2 | 0.5h | 全部 |
| D4: 文档更新 | P2 | 0.5h | 全部 |

### 5.2 建议实施顺序

```
Sprint 1 (Phase A): 智能缓存核心
  - 先做数据库表 (A1, A2)
  - 再做后端缓存服务 (A3, A4)
  - 然后改造现有API (A5, A6)
  - 最后前端适配 (A7, A8)
  - 预计: 2天

Sprint 2 (Phase B + C1-C5): 缓存预热 + 问答后端
  - 调度任务 (B1)
  - 自选股优化 (B2, B3)
  - 问答后端 (C1-C5)
  - 预计: 2天

Sprint 3 (Phase C6-C7 + D): 问答前端 + 测试
  - 前端问答组件 (C6, C7)
  - 测试 (D1-D4)
  - 预计: 1-2天

总计: 5-6天
```

---

## 6. 风险和约束

### 6.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 东方财富批量API格式变化 | 低 | 高 | 做好兼容解析，保留逐个请求的fallback |
| Supabase 缓存读写延迟 > 2秒 | 低 | 中 | 监控延迟，必要时增加内存缓存层 |
| GLM-4 API 配额不足 | 中 | 中 | 缓存减少消耗；问答限频；模板回复兜底 |
| 缓存数据不一致 | 中 | 低 | 缓存都带时间戳；前端显示缓存年龄；手动刷新 |
| Render 休眠影响调度任务 | 高 | 中 | 调度任务本身能唤醒Render；外部cron触发health |
| 问答被滥用/频率过高 | 低 | 低 | 每日限10次；相似问题缓存；全局Token上限 |

### 6.2 产品约束

| 约束 | 说明 | 应对 |
|------|------|------|
| Render 免费版 512MB | 缓存必须放Supabase | 已规划：内存仅放30秒实时价格 |
| Render 免费版休眠 | 15分钟无请求后休眠 | 缓存持久化在Supabase，休眠无影响 |
| Supabase 免费版 500MB | 需控制缓存数据量 | 估算 <15MB，远在限制内 |
| GLM-4 Token 成本 | 需控制问答消耗 | 问答限频+相似缓存+缓存减少其他消耗 |
| 数据新鲜度 vs 响应速度 | 用户可能看到旧数据 | UI明确标注缓存时间；提供手动刷新 |

### 6.3 用户体验权衡

| 权衡点 | 当前体验 | 优化后体验 | 取舍说明 |
|-------|---------|-----------|---------|
| 详情页首次加载 | 15-30秒实时数据 | <1秒缓存数据 | 牺牲部分新鲜度换取速度 |
| 价格时效性 | 每次都是最新 | 30秒延迟 | 非盘中时无差异；盘中30秒可接受 |
| AI分析时效性 | 每次重新分析 | 4小时缓存 | 日内分析不会频繁变化 |
| 问答能力 | 无 | 有限的问答 | 每日10次限制，非无限问答 |

---

## 7. 成功指标

| 指标 | 当前值 | 目标值 | 衡量方式 |
|------|-------|-------|---------|
| 详情页加载时间(缓存命中) | 15-30秒 | <1秒 | 前端Performance API |
| 推荐列表加载时间 | 11-21秒 | <3秒 | API响应时间 |
| 自选股列表加载时间 | 75-300秒 | <3秒 | API响应时间 |
| 每日GLM-4 Token消耗 | ~157K | ~160K | TokenMonitor |
| 用户问答满意度 | N/A | >70% | 问答后评价 |
| 后端内存使用 | ~240MB | <300MB | psutil 监控 |

---

## 8. 文件变更清单

### 后端新增文件
- `backend/app/services/cache_service.py` -- 缓存服务（读写stock_analysis_cache）
- `backend/app/services/chat_service.py` -- 问答服务（Prompt构建+GLM调用+历史管理）
- `backend/app/api/chat.py` -- 问答API路由
- `backend/app/api/quotes.py` -- 批量行情API路由

### 后端修改文件
- `backend/app/api/stock.py` -- 改造为缓存优先逻辑
- `backend/app/api/recommendations.py` -- 改用批量价格
- `backend/app/services/eastmoney_service.py` -- 新增 get_batch_realtime()
- `backend/app/scheduler.py` -- 新增 cache_warm_job
- `backend/app/main.py` -- 注册新路由

### 前端新增文件
- `src/components/StockChatPanel.tsx` -- AI问答面板组件
- `src/components/CacheIndicator.tsx` -- 缓存状态指示器组件

### 前端修改文件
- `src/lib/api.ts` -- 新增问答API函数、修改缓存逻辑
- `src/components/StockDetailClient.tsx` -- 集成缓存提示+问答面板
- `src/components/HomeContent.tsx` -- 适配批量价格API

### 数据库变更
- 新建表: `stock_analysis_cache`
- 新建表: `stock_kline_cache`
- 新建表: `stock_chat_history`

---

*文档版本: v3.0*
*日期: 2026-02-09*
*下一步: 用户评审确认 -> 进入开发阶段*
