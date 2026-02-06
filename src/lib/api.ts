/**
 * API 服务层 - 与后端通信
 */

// 后端 API 基础 URL (包含 /api/v1 前缀)
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1';
const HEALTH_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/health';

// 后端状态缓存
let backendAwake = false;
let lastWakeTime = 0;
const WAKE_CACHE_MS = 5 * 60 * 1000; // 5分钟内认为后端是醒的

// 股票数据缓存（避免重复请求）
const stockCache = new Map<string, { data: StockAnalysis; timestamp: number }>();
const STOCK_CACHE_MS = 3 * 60 * 1000; // 缓存 3 分钟

// AI 排名缓存
let aiRankingsCache: { data: { count: number; rankings: AIRankingItem[] }; timestamp: number } | null = null;
const AI_RANKINGS_CACHE_MS = 5 * 60 * 1000; // 缓存 5 分钟

/**
 * 唤醒后端服务（Render 免费版会休眠）
 */
export async function wakeUpBackend(): Promise<boolean> {
  // 如果最近唤醒过，跳过
  if (backendAwake && Date.now() - lastWakeTime < WAKE_CACHE_MS) {
    return true;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 90000); // 90秒超时等待冷启动

    const response = await fetch(HEALTH_URL, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      backendAwake = true;
      lastWakeTime = Date.now();
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

/**
 * 检查后端是否可能在休眠
 */
export function isBackendPossiblyAsleep(): boolean {
  return !backendAwake || Date.now() - lastWakeTime > WAKE_CACHE_MS;
}

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
  prev_close: number;  // 昨收
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
  summary?: string;
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
 * AI 模型状态
 */
export interface AIModelStatus {
  available: boolean;
  error_code: 'unavailable' | 'quota_exhausted' | 'auth_failed' | 'rate_limited' | 'timeout' | 'unknown' | null;
  error_message: string | null;
  last_error_time: string | null;
}

/**
 * API 错误
 */
export class ApiError extends Error {
  status: number;
  aiModelStatus?: AIModelStatus;

  constructor(message: string, status: number, aiModelStatus?: AIModelStatus) {
    super(message);
    this.status = status;
    this.aiModelStatus = aiModelStatus;
  }
}

/**
 * 带重试的 API 请求函数
 */
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit,
  timeoutMs: number = 60000,
  maxRetries: number = 2
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    // 首次请求前，如果后端可能休眠，先尝试唤醒
    if (attempt === 0 && isBackendPossiblyAsleep()) {
      await wakeUpBackend();
    }

    // 创建超时控制器
    const controller = new AbortController();
    const currentTimeout = attempt === 0 ? timeoutMs : timeoutMs * 1.5; // 重试时增加超时
    const timeoutId = setTimeout(() => controller.abort(), currentTimeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new ApiError(error.detail || '请求失败', response.status);
      }

      // 请求成功，更新后端状态
      backendAwake = true;
      lastWakeTime = Date.now();

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiError) {
        throw error; // API 错误不重试
      }

      lastError = error as Error;

      // 如果是超时或网络错误，且还有重试次数，继续重试
      if (attempt < maxRetries) {
        // 等待一段时间再重试（指数退避）
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
        continue;
      }
    }
  }

  // 所有重试都失败了
  if (lastError instanceof Error && lastError.name === 'AbortError') {
    throw new ApiError('请求超时，后端服务可能正在冷启动中（约需60秒），请稍后重试', 408);
  }
  throw new ApiError('网络错误，后端服务可能暂时不可用，请稍后重试', 0);
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
 * 获取股票分析（带缓存）
 */
export async function getStockAnalysis(code: string): Promise<StockAnalysis> {
  // 检查缓存
  const cached = stockCache.get(code);
  if (cached && Date.now() - cached.timestamp < STOCK_CACHE_MS) {
    console.log(`[Cache] Using cached data for ${code}`);
    return cached.data;
  }

  // 请求新数据
  const data = await apiRequest<StockAnalysis>(`/stock/${code}`);

  // 存入缓存
  stockCache.set(code, { data, timestamp: Date.now() });

  return data;
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
 * 注意：此操作需要分析多只股票，可能需要3-5分钟
 */
export async function generateRecommendations(): Promise<{
  success: boolean;
  date?: string;
  count?: number;
  recommendations?: StockAnalysis[];
  message?: string;
}> {
  // 使用 5 分钟超时，因为需要分析 60 只股票
  return apiRequest('/recommendations/generate', { method: 'POST' }, 300000);
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

/**
 * AI 排名项
 */
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
  action: string;
  // 交易建议详情
  buy_price_low: number;
  buy_price_high: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  risk_level: string;
  holding_days: string;
  position_ratio: string;
}

/**
 * AI 排名响应（包含模型状态）
 */
export interface AIRankingsResponse {
  count: number;
  rankings: AIRankingItem[];
  ai_model_status?: AIModelStatus;
  cached?: boolean;
  cache_time?: string;
}

/**
 * 获取 AI 智能排名
 * 注意：此操作需要分析多只股票，可能需要较长时间
 * @param limit 返回数量
 * @param refresh 强制刷新缓存
 */
export async function getAIRankings(limit: number = 10, refresh: boolean = false): Promise<AIRankingsResponse> {
  // AI排名需要更长超时（2分钟）和更多重试
  const refreshParam = refresh ? '&refresh=true' : '';
  return apiRequest(`/rankings/ai?limit=${limit}${refreshParam}`, undefined, 120000, 3);
}

/**
 * 获取 AI 模型状态
 */
export async function getAIModelStatus(): Promise<{
  ai_model: AIModelStatus;
  timestamp: string;
}> {
  const healthUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/ai/status';
  const response = await fetch(healthUrl, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error('无法获取 AI 模型状态');
  }
  return response.json();
}

/**
 * 批量预加载股票数据
 * 用于预热缓存，后续访问详情页会更快
 */
export async function prefetchStocks(codes: string[]): Promise<{
  total: number;
  cached: number;
  failed: number;
}> {
  return apiRequest('/stocks/prefetch', {
    method: 'POST',
    body: JSON.stringify(codes),
  });
}
