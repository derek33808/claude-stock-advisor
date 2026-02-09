# 数据库迁移指南

## ⚠️ 重要：必须执行数据库迁移

Stock Advisor v2.0 需要创建 7 个新表。**必须**在 Supabase 中执行以下 SQL 脚本。

## 执行步骤

### 1. 登录 Supabase Dashboard
访问: https://supabase.com/dashboard

### 2. 选择项目
选择项目: `stock-advisor`

### 3. 打开 SQL Editor
左侧菜单 → SQL Editor → New Query

### 4. 粘贴并执行 SQL
复制以下完整SQL脚本并执行:

```sql
-- Stock Advisor v2.0 数据库迁移脚本
-- 创建所有v2.0新增表

-- 1. 自选股表
CREATE TABLE IF NOT EXISTS watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(50),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, code)
);

-- 2. 分析历史记录表
CREATE TABLE IF NOT EXISTS analysis_history (
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

-- 3. 预测准确度跟踪表
CREATE TABLE IF NOT EXISTS prediction_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_history(id) ON DELETE CASCADE,
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

-- 4. Token使用统计表
CREATE TABLE IF NOT EXISTS token_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    api_name VARCHAR(50),
    tokens_used INTEGER,
    requests_count INTEGER,
    cost_estimate DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 新闻缓存表
CREATE TABLE IF NOT EXISTS stock_news_cache (
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

-- 6. 行业数据缓存表
CREATE TABLE IF NOT EXISTS industry_data_cache (
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

-- 7. 热门股票池表
CREATE TABLE IF NOT EXISTS hot_stock_universe (
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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_code_date ON analysis_history(code, analysis_date DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_tracking_analysis ON prediction_tracking(analysis_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_date ON token_usage_log(date, api_name);
CREATE INDEX IF NOT EXISTS idx_news_code_date ON stock_news_cache(code, news_date DESC);
CREATE INDEX IF NOT EXISTS idx_industry_date ON industry_data_cache(industry_name, date DESC);

-- 插入初始热门股票池数据
INSERT INTO hot_stock_universe (code, name, industry, market_cap, is_active, inclusion_date) VALUES
('600519', '贵州茅台', '白酒', 1900000, true, CURRENT_DATE),
('000858', '五粮液', '白酒', 750000, true, CURRENT_DATE),
('000568', '泸州老窖', '白酒', 380000, true, CURRENT_DATE),
('601318', '中国平安', '保险', 1200000, true, CURRENT_DATE),
('600036', '招商银行', '银行', 1100000, true, CURRENT_DATE),
('300750', '宁德时代', '电池', 1150000, true, CURRENT_DATE),
('002594', '比亚迪', '汽车', 950000, true, CURRENT_DATE),
('600276', '恒瑞医药', '医药', 450000, true, CURRENT_DATE),
('000651', '格力电器', '家电', 230000, true, CURRENT_DATE),
('000333', '美的集团', '家电', 430000, true, CURRENT_DATE)
ON CONFLICT (code) DO NOTHING;
```

### 5. 验证迁移成功
执行成功后，在 Table Editor 中应该能看到 7 个新表：
- ✅ watchlist
- ✅ analysis_history
- ✅ prediction_tracking
- ✅ token_usage_log
- ✅ stock_news_cache
- ✅ industry_data_cache
- ✅ hot_stock_universe

## 迁移完成！

数据库迁移完成后，Stock Advisor v2.0 的所有功能即可使用。
