from pydantic import BaseModel
from typing import Optional
from datetime import date


# ============================================
# 股票相关
# ============================================

class StockInfo(BaseModel):
    """股票基本信息"""
    code: str
    name: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None  # 市值（亿）


class StockQuote(BaseModel):
    """股票实时行情"""
    code: str
    name: str
    price: float
    change: float  # 涨跌幅 %
    open: float
    high: float
    low: float
    volume: float  # 成交量（手）
    amount: float  # 成交额（万）
    turnover: Optional[float] = None  # 换手率 %


class TechnicalIndicators(BaseModel):
    """技术指标"""
    # MACD
    macd_dif: float
    macd_dea: float
    macd_hist: float
    macd_signal: str  # 金叉/死叉/持有

    # RSI
    rsi6: float
    rsi12: float
    rsi_status: str  # 超买/超卖/健康

    # MA
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    ma_trend: str  # 多头排列/空头排列/震荡

    # KDJ
    kdj_k: float
    kdj_d: float
    kdj_j: float

    # BOLL
    boll_upper: float
    boll_mid: float
    boll_lower: float


class TradingSuggestion(BaseModel):
    """交易建议"""
    action: str  # 买入/观望/卖出
    buy_price_low: float
    buy_price_high: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position: str  # 仓位建议 如 "10-15%"
    holding_days: str  # 持有周期 如 "5-15个交易日"
    risk_level: str  # 低/中/高


class StockReasons(BaseModel):
    """推荐理由"""
    technical: list[str]
    fundamental: list[str]
    capital: list[str]


class StockAnalysis(BaseModel):
    """股票完整分析"""
    info: StockInfo
    quote: StockQuote
    indicators: TechnicalIndicators
    suggestion: TradingSuggestion
    reasons: StockReasons
    score: int  # 综合评分 0-100


# ============================================
# 推荐相关
# ============================================

class RecommendationItem(BaseModel):
    """推荐股票项"""
    code: str
    name: str
    industry: Optional[str] = None
    price: float
    change: float
    score: int
    buy_price_low: float
    buy_price_high: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    holding_days: str
    position_ratio: str
    risk_level: str
    reasons: StockReasons


class MarketOverview(BaseModel):
    """市场概览"""
    sh_index: float
    sh_change: float
    sz_index: float
    sz_change: float
    sentiment: str  # 偏多/中性/偏空


class RecommendationResponse(BaseModel):
    """推荐响应"""
    date: str
    update_time: str
    market: MarketOverview
    recommendations: list[RecommendationItem]


# ============================================
# 统计相关
# ============================================

class PerformanceStats(BaseModel):
    """策略表现统计"""
    total_recommendations: int
    win_count: int  # 止盈数
    loss_count: int  # 止损数
    holding_count: int  # 持仓中
    win_rate: float  # 胜率 %
    avg_return: float  # 平均收益 %
    profit_loss_ratio: float  # 盈亏比
    period_days: int  # 统计周期（天）


class TrackingRecord(BaseModel):
    """跟踪记录"""
    recommendation_date: date
    code: str
    name: str
    rec_price: float  # 推荐价
    current_price: float  # 当前价
    change_pct: float  # 涨跌幅 %
    status: str  # holding/stop_loss/take_profit
    days_held: int  # 持有天数
