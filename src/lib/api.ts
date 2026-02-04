/**
 * API 服务层 - 与后端通信
 */

// 后端 API 基础 URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * 股票分析结果
 */
export interface StockAnalysis {
  code: string;
  name: string;
  industry: string;
  price: number;
  change: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
  market_cap: number;
  indicators: {
    macd: { macd: number; signal: number; histogram: number; trend: string };
    rsi: { value: number; level: string };
    ma: { ma5: number; ma10: number; ma20: number; ma60: number; alignment: string };
    kdj: { k: number; d: number; j: number };
    boll: { upper: number; middle: number; lower: number; position: string };
    atr: number;
    volume_ratio: number;
  };
  suggestion: {
    action: string;
    buy_price: { low: number; high: number };
    stop_loss: number;
    take_profit: { target1: number; target2: number };
    holding_days: string;
    position_ratio: string;
    risk_level: string;
  };
  reasons: string[];
  score: number;
}

/**
 * 市场概览
 */
export interface MarketOverview {
  sh_index: number;
  sh_change: number;
  sz_index: number;
  sz_change: number;
  sentiment: string;
}

/**
 * 推荐数据响应
 */
export interface RecommendationsResponse {
  date: string;
  update_time: string;
  market: MarketOverview;
  recommendations: StockAnalysis[];
  message?: string;
}

/**
 * 搜索结果
 */
export interface SearchResult {
  code: string;
  name: string;
  industry?: string;
}

/**
 * API 错误
 */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/**
 * 通用 API 请求函数
 */
async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }));
      throw new ApiError(error.detail || '请求失败', response.status);
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('网络错误，请检查后端服务是否运行', 0);
  }
}

/**
 * 获取今日推荐
 */
export async function getRecommendations(): Promise<RecommendationsResponse> {
  return apiRequest<RecommendationsResponse>('/recommendations');
}

/**
 * 获取指定日期的推荐
 */
export async function getRecommendationsByDate(date: string): Promise<RecommendationsResponse> {
  return apiRequest<RecommendationsResponse>(`/recommendations/${date}`);
}

/**
 * 获取股票分析
 */
export async function getStockAnalysis(code: string): Promise<StockAnalysis> {
  return apiRequest<StockAnalysis>(`/stock/${code}`);
}

/**
 * 搜索股票
 */
export async function searchStocks(query: string, limit: number = 20): Promise<{
  query: string;
  count: number;
  results: SearchResult[];
}> {
  return apiRequest(`/stock/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

/**
 * 获取市场概览
 */
export async function getMarketOverview(): Promise<MarketOverview> {
  return apiRequest<MarketOverview>('/market/overview');
}

/**
 * 手动触发生成推荐
 */
export async function generateRecommendations(): Promise<{
  success: boolean;
  date?: string;
  count?: number;
  recommendations?: StockAnalysis[];
  message?: string;
}> {
  return apiRequest('/recommendations/generate', { method: 'POST' });
}

/**
 * 获取表现统计
 */
export async function getPerformanceStats(days: number = 30): Promise<{
  period_days: number;
  total_recommendations: number;
  win_count: number;
  loss_count: number;
  holding_count: number;
  win_rate: number;
  avg_return: number;
  profit_loss_ratio: number;
}> {
  return apiRequest(`/stats/performance?days=${days}`);
}
