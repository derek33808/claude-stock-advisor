# Stock Advisor v2.0 - 数据库架构说明

## 📊 概述

Stock Advisor v2.0 **已经配置并使用**持久化数据库来记录所有用户数据、分析历史和推荐记录。

---

## 🗄️ 当前数据库配置

### Supabase PostgreSQL

**提供商**: Supabase (PostgreSQL 云数据库)
**项目名称**: stock-advisor
**数据库 URL**: `https://hntogkygloioqyexevac.supabase.co`
**连接方式**: 通过 Supabase Python SDK
**配置位置**: `backend/.env` (SUPABASE_URL, SUPABASE_KEY)
**状态**: ✅ 运行中，已部署

---

## 📁 数据库表结构（7 个表）

### 1. **watchlist** - 自选股管理
```sql
CREATE TABLE watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,           -- 用户ID（当前统一使用 'default_user'）
    code TEXT NOT NULL,               -- 股票代码（如 600519）
    name TEXT,                        -- 股票名称（如 贵州茅台）
    added_at TIMESTAMP DEFAULT NOW(), -- 添加时间
    UNIQUE(user_id, code)             -- 同一用户不能重复添加
);
```

**用途**:
- 记录用户添加的自选股
- 支持添加、查询、删除操作
- 每日 17:30 自动保存所有自选股的分析快照

---

### 2. **analysis_history** - 分析历史快照
```sql
CREATE TABLE analysis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL,                    -- 股票代码
    user_id TEXT NOT NULL,                 -- 用户ID
    analysis_date DATE NOT NULL,           -- 分析日期
    analysis_time TIME DEFAULT NOW(),      -- 分析时间
    price DECIMAL(10, 2),                  -- 当时价格
    change_percent DECIMAL(5, 2),          -- 涨跌幅
    prediction_direction TEXT,             -- 预测方向（看涨/看跌/震荡）
    prediction_text TEXT,                  -- 预测文本
    target_price_low DECIMAL(10, 2),       -- 目标价下限
    target_price_high DECIMAL(10, 2),      -- 目标价上限
    analysis_content JSONB,                -- 完整分析内容（JSON）
    created_at TIMESTAMP DEFAULT NOW()
);
```

**用途**:
- 每日 17:30 自动保存自选股的分析快照
- 记录当时的价格、预测、目标价
- 用于后续预测准确率评估
- 前端展示历史分析时间轴

---

### 3. **prediction_tracking** - 预测评估跟踪
```sql
CREATE TABLE prediction_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES analysis_history(id), -- 关联的分析记录
    evaluation_date DATE NOT NULL,                    -- 评估日期（5个交易日后）
    actual_price DECIMAL(10, 2),                      -- 实际价格
    price_change_percent DECIMAL(5, 2),               -- 实际涨跌幅
    is_direction_correct BOOLEAN,                     -- 方向是否正确
    is_target_reached BOOLEAN,                        -- 是否达到目标价
    accuracy_score DECIMAL(5, 2),                     -- 准确度评分 (0-100)
    evaluation_note TEXT,                             -- 评估备注
    created_at TIMESTAMP DEFAULT NOW()
);
```

**用途**:
- 每日 18:00 自动评估 5 个交易日前的预测
- 计算预测准确率（方向准确率、目标达成率）
- 生成准确率统计报告
- 前端展示绿色/红色标识（正确/错误）

---

### 4. **recommendations** - 推荐记录
```sql
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_date DATE NOT NULL,     -- 推荐日期
    code TEXT NOT NULL,                    -- 股票代码
    name TEXT,                             -- 股票名称
    score DECIMAL(5, 2),                   -- 综合评分
    price DECIMAL(10, 2),                  -- 当前价格
    change_percent DECIMAL(5, 2),          -- 涨跌幅
    reasons TEXT[],                        -- 推荐理由（数组）
    suggestion JSONB,                      -- 交易建议（JSON）
    created_at TIMESTAMP DEFAULT NOW()
);
```

**用途**:
- 每日 17:00 自动生成 10 支推荐股票
- 保存推荐记录到数据库
- 前端首页展示推荐列表
- 支持历史推荐查询

---

### 5. **market_overview** - 市场概览
```sql
CREATE TABLE market_overview (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    overview_date DATE NOT NULL,
    sh_index DECIMAL(10, 2),      -- 上证指数
    sh_change DECIMAL(5, 2),       -- 上证涨跌幅
    sz_index DECIMAL(10, 2),      -- 深证成指
    sz_change DECIMAL(5, 2),       -- 深证涨跌幅
    cy_index DECIMAL(10, 2),      -- 创业板指
    cy_change DECIMAL(5, 2),       -- 创业板涨跌幅
    created_at TIMESTAMP DEFAULT NOW()
);
```

**用途**:
- 记录每日大盘指数
- 前端首页展示市场概览
- 与推荐一起保存

---

### 6. **token_usage_log** - Token 使用日志
```sql
CREATE TABLE token_usage_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    log_date DATE NOT NULL,
    operation_type TEXT,               -- 操作类型（分析/推荐/刷新）
    stock_code TEXT,                   -- 股票代码
    tokens_used INTEGER,               -- 使用的 Token 数
    model_name TEXT,                   -- 模型名称（GLM-4）
    created_at TIMESTAMP DEFAULT NOW()
);
```

**用途**:
- 监控 AI 模型 Token 使用量
- 防止超出限额
- 成本控制和分析

---

### 7. **hot_stock_universe** - 热门股票池
```sql
CREATE TABLE hot_stock_universe (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code TEXT NOT NULL UNIQUE,
    name TEXT,
    industry TEXT,                     -- 行业
    market_cap DECIMAL(15, 2),        -- 市值
    is_active BOOLEAN DEFAULT TRUE,    -- 是否活跃
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**用途**:
- 存储推荐候选股票池
- 初始 10 只热门股票
- 定期更新维护

---

## 🔄 数据持久化流程

### 用户添加自选股
```
1. 用户点击 ☆ 按钮
2. 前端调用 POST /api/v1/watchlist/add
3. 后端保存到 watchlist 表
4. 返回成功，前端显示 ★
```

### 每日自动快照（17:30）
```
1. 调度器触发 daily_snapshot_job
2. 查询 watchlist 表获取所有自选股
3. 为每只股票生成综合分析
4. 保存分析快照到 analysis_history 表
5. 记录当时的价格、预测、目标价
```

### 预测评估（18:00）
```
1. 调度器触发 evaluation_job
2. 计算 5 个交易日前的日期
3. 查询 analysis_history 表获取该日期的分析
4. 获取当前价格，对比预测
5. 计算准确率，保存到 prediction_tracking 表
```

### 查看历史分析
```
1. 用户点击"查看历史"按钮
2. 前端调用 GET /api/v1/analysis/history/{code}
3. 后端查询 analysis_history 和 prediction_tracking 表
4. 返回历史记录（包含评估结果）
5. 前端展示时间轴和准确率统计
```

---

## 🤔 你的疑问解答

### Q1: 我需要建立自己的数据库吗？

**A**: **不需要！** 系统已经配置好了 Supabase 数据库。

- ✅ 数据库已创建并运行
- ✅ 7 个表已建立
- ✅ 后端已连接配置
- ✅ 所有数据已持久化

你唯一需要做的是：
- 确保 `backend/.env` 中有正确的 Supabase 配置
- 这些配置在部署时已经设置好了

### Q2: 如果不记录，你是怎么跟进自选股推荐历史的？

**A**: 系统**一直在记录**所有数据！

**数据流向**:
```
用户操作 → 前端 → 后端 API → Supabase 数据库 → 持久化存储
```

**已记录的数据**:
1. ✅ **自选股列表** (watchlist 表)
   - 用户添加的所有自选股
   - 持久化存储，不会丢失

2. ✅ **每日分析快照** (analysis_history 表)
   - 每天 17:30 自动保存
   - 记录价格、预测、目标价
   - 30 天历史可查

3. ✅ **预测评估结果** (prediction_tracking 表)
   - 每天 18:00 自动评估
   - 5 个交易日后对比实际走势
   - 计算准确率并标识正确/错误

4. ✅ **推荐记录** (recommendations 表)
   - 每天 17:00 自动生成
   - 所有推荐股票保存
   - 可查询历史推荐

**验证方法**:
```bash
# 查看你的自选股
curl https://stock-advisor-api-6vtb.onrender.com/api/v1/watchlist/list?user_id=default_user

# 查看历史分析（以贵州茅台为例）
curl https://stock-advisor-api-6vtb.onrender.com/api/v1/analysis/history/600519?user_id=default_user

# 查看准确率统计
curl https://stock-advisor-api-6vtb.onrender.com/api/v1/analysis/accuracy/600519?user_id=default_user
```

---

## 👤 关于用户 ID

### 当前设计：单用户模式

**当前实现**: 所有用户使用统一 ID `'default_user'`

**原因**:
- v2.0 聚焦核心功能实现
- 简化开发和部署
- 适合个人使用或小团队

### 未来扩展：多用户模式

如果需要支持多用户，只需：

1. **添加用户认证系统**
   ```python
   # 示例：简单的设备指纹认证
   device_id = generate_device_fingerprint()
   user_id = f"user_{device_id}"
   ```

2. **修改 API 调用**
   ```typescript
   // 前端传递真实用户ID
   const userId = getUserId(); // 从 localStorage 或 cookie 获取
   await addToWatchlist(code, userId);
   ```

3. **数据隔离**
   - 数据库查询自动按 user_id 过滤
   - 每个用户只能看到自己的数据
   - 表结构无需修改

---

## 📊 数据示例

### watchlist 表数据示例
```json
{
  "id": "uuid-1",
  "user_id": "default_user",
  "code": "600519",
  "name": "贵州茅台",
  "added_at": "2026-02-09 10:30:00"
}
```

### analysis_history 表数据示例
```json
{
  "id": "uuid-2",
  "code": "600519",
  "user_id": "default_user",
  "analysis_date": "2026-02-09",
  "analysis_time": "17:30:00",
  "price": 1650.00,
  "change_percent": 2.5,
  "prediction_direction": "看涨",
  "prediction_text": "技术面 MACD 金叉，基本面业绩稳健",
  "target_price_low": 1700.00,
  "target_price_high": 1750.00,
  "analysis_content": { /* 完整分析 JSON */ }
}
```

### prediction_tracking 表数据示例
```json
{
  "id": "uuid-3",
  "analysis_id": "uuid-2",
  "evaluation_date": "2026-02-16",
  "actual_price": 1720.00,
  "price_change_percent": 4.24,
  "is_direction_correct": true,
  "is_target_reached": true,
  "accuracy_score": 95.0,
  "evaluation_note": "预测准确，目标价已达成"
}
```

---

## 🔐 数据安全

### Supabase 安全特性

1. **加密传输**: 所有 API 请求通过 HTTPS
2. **访问控制**: 需要 SUPABASE_KEY 才能访问
3. **备份**: Supabase 自动每日备份
4. **可靠性**: 99.9% SLA 保证

### 环境变量配置

```bash
# backend/.env
SUPABASE_URL=https://hntogkygloioqyexevac.supabase.co
SUPABASE_KEY=your_supabase_key_here  # 已配置

# Render 环境变量（已设置）
# Netlify 环境变量（已设置）
```

---

## ✅ 总结

### 你不需要做任何事情！

✅ **数据库已配置好** - Supabase PostgreSQL
✅ **表结构已创建** - 7 个表全部就绪
✅ **数据已持久化** - 自选股、历史、评估全部保存
✅ **自动任务已运行** - 每日快照和评估
✅ **前端已集成** - 历史页面可查看所有数据

### 系统如何跟踪数据

```
┌─────────────────────────────────────────────────────────┐
│  用户操作                                                 │
│  ↓                                                       │
│  前端调用 API                                            │
│  ↓                                                       │
│  后端处理                                                │
│  ↓                                                       │
│  Supabase 数据库持久化 ✅                                │
│  ↓                                                       │
│  调度器自动快照/评估 ✅                                   │
│  ↓                                                       │
│  前端查询展示历史 ✅                                      │
└─────────────────────────────────────────────────────────┘
```

**你的数据都在 Supabase 云数据库中，安全、持久、可靠！**

---

**创建时间**: 2026-02-09
**文档版本**: v1.0
**项目**: Stock Advisor v2.0
