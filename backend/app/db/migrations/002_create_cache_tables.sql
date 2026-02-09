-- ============================================
-- Stock Advisor v3.0 - Cache & Chat Tables
-- ============================================

-- 1. 股票完整分析结果缓存
-- 每只股票一行，upsert 更新
CREATE TABLE IF NOT EXISTS stock_analysis_cache (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50),
    industry VARCHAR(50),

    -- 实时行情快照
    price DECIMAL(10,3),
    change_percent DECIMAL(8,4),
    open_price DECIMAL(10,3),
    high_price DECIMAL(10,3),
    low_price DECIMAL(10,3),
    prev_close DECIMAL(10,3),
    volume BIGINT,
    amount BIGINT,
    market_cap DECIMAL(14,2),
    quote_updated_at TIMESTAMPTZ,

    -- 技术指标 + 交易建议 + 理由 (JSON)
    indicators JSONB,
    suggestion JSONB,
    reasons JSONB,
    score INTEGER,

    -- AI 分析结果
    ai_summary TEXT,
    ai_company JSONB,
    ai_fundamental JSONB,
    ai_recommendation JSONB,
    ai_ranking_score INTEGER,
    ai_updated_at TIMESTAMPTZ,

    -- 缓存元数据
    full_analysis_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sac_updated ON stock_analysis_cache(full_analysis_updated_at);
CREATE INDEX IF NOT EXISTS idx_sac_quote_updated ON stock_analysis_cache(quote_updated_at);

-- 2. AI 问答历史记录
CREATE TABLE IF NOT EXISTS stock_chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL,
    user_id VARCHAR(100) NOT NULL DEFAULT 'default_user',
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    template VARCHAR(50),
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sch_code_user ON stock_chat_history(code, user_id);
CREATE INDEX IF NOT EXISTS idx_sch_created ON stock_chat_history(created_at DESC);
