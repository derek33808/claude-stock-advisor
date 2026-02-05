// 股票推荐数据类型

// 自选股数据
export interface WatchlistItem {
  code: string;      // 股票代码
  name: string;      // 股票名称
  addedAt: number;   // 添加时间戳
}

export interface StockRecommendation {
  code: string;           // 股票代码
  name: string;           // 股票名称
  industry: string;       // 所属行业
  price: number;          // 当前价格
  change: number;         // 涨跌幅 (%)
  score: number;          // 综合评分 (0-100)

  // 交易建议
  buyPriceLow: number;    // 建议买入价下限
  buyPriceHigh: number;   // 建议买入价上限
  stopLoss: number;       // 止损价
  takeProfit1: number;    // 第一止盈价
  takeProfit2: number;    // 第二止盈价
  holdingDays: string;    // 建议持有周期
  positionRatio: string;  // 建议仓位

  // 推荐理由
  reasons: {
    technical: string[];   // 技术面
    fundamental: string[]; // 基本面
    capital: string[];     // 资金面
  };

  // 风险等级
  riskLevel: 'low' | 'medium' | 'high';

  // 交易指导摘要
  summary?: string;

  // AI 智能分析（可选）
  aiAnalysis?: AIAnalysis;
  aiRankingScore?: number;
}

// AI 公司分析
export interface CompanyAnalysis {
  company_profile: string;       // 公司简介
  main_business: string;         // 主营业务
  competitive_advantage: string; // 核心竞争优势
  industry_position: string;     // 行业地位
  growth_potential: string;      // 成长潜力
  risk_factors: string[];        // 风险因素
}

// AI 基本面分析
export interface FundamentalAnalysis {
  valuation_level: string;       // 估值水平
  valuation_reason: string;      // 估值理由
  profitability: string;         // 盈利能力
  financial_health: string;      // 财务健康度
  dividend_policy: string;       // 分红政策
  investment_value: number;      // 投资价值评分 (1-10)
  analysis_summary: string;      // 基本面总结
}

// AI 推荐建议
export interface AIRecommendation {
  ai_score: number;              // AI 评分 (0-100)
  ai_rating: string;             // 推荐等级
  confidence: string;            // 置信度
  time_horizon: string;          // 建议持有周期
  key_points: string[];          // 核心观点
  ai_summary: string;            // AI 分析总结
}

// 完整 AI 分析
export interface AIAnalysis {
  company: CompanyAnalysis;
  fundamental: FundamentalAnalysis;
  ai_recommendation: AIRecommendation;
  analysis_time: string;
}

// AI 排名项
export interface AIRankingItem {
  rank: number;
  code: string;
  name: string;
  industry: string;
  price: number;
  change: number;
  technical_score: number;
  ai_ranking_score: number;
  macd_signal: string;
  ma_trend: string;
  suggestion: string;
}

export interface MarketOverview {
  shIndex: {
    value: number;
    change: number;
  };
  szIndex: {
    value: number;
    change: number;
  };
  sentiment: string;
}

export interface RecommendationData {
  date: string;           // 数据日期
  updateTime: string;     // 更新时间
  market: MarketOverview;
  recommendations: StockRecommendation[];  // 今日推荐 (前5支)
  allStocks: StockRecommendation[];        // 所有分析过的股票 (前100支)
}
