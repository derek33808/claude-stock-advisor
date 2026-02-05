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
