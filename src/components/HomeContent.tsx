'use client';

import { useState, useEffect, useRef } from 'react';
import { useWatchlist } from '@/lib/watchlist-context';
import { StockRecommendation } from '@/lib/types';
import { getStockAnalysis, getAIRankings, prefetchStocks, StockAnalysis, AIRankingItem, AIModelStatus, AIRankingsResponse, wakeUpBackend, isBackendPossiblyAsleep } from '@/lib/api';
import StockCard from './StockCard';
import TabSwitcher, { TabType } from './TabSwitcher';
import WatchlistButton from './WatchlistButton';
import Link from 'next/link';

interface HomeContentProps {
  recommendations: StockRecommendation[];
}

// 将 API 返回的 StockAnalysis 转换为 StockRecommendation 格式
function convertToRecommendation(analysis: StockAnalysis): StockRecommendation {
  return {
    code: analysis.code,
    name: analysis.name,
    industry: analysis.industry || '未知',
    price: analysis.price,
    change: analysis.change,
    score: analysis.score,
    buyPriceLow: analysis.suggestion.buy_price.low,
    buyPriceHigh: analysis.suggestion.buy_price.high,
    stopLoss: analysis.suggestion.stop_loss,
    takeProfit1: analysis.suggestion.take_profit.target1,
    takeProfit2: analysis.suggestion.take_profit.target2,
    holdingDays: analysis.suggestion.holding_days,
    positionRatio: analysis.suggestion.position_ratio,
    reasons: {
      technical: analysis.reasons.filter(r => r.includes('技术') || r.includes('MACD') || r.includes('RSI') || r.includes('均线')),
      fundamental: analysis.reasons.filter(r => r.includes('基本') || r.includes('业绩') || r.includes('估值')),
      capital: analysis.reasons.filter(r => r.includes('资金') || r.includes('成交') || r.includes('量')),
    },
    riskLevel: analysis.suggestion.risk_level as 'low' | 'medium' | 'high',
  };
}

// AI 排名卡片组件 - 与推荐卡片风格一致
function AIRankingCard({ item }: { item: AIRankingItem }) {
  const isUp = item.change >= 0;

  // 风险等级标签
  const getRiskLabel = (risk: string) => {
    const riskMap: Record<string, { text: string; class: string }> = {
      low: { text: '低风险', class: 'bg-green-100 text-green-700' },
      medium: { text: '中风险', class: 'bg-yellow-100 text-yellow-700' },
      high: { text: '高风险', class: 'bg-red-100 text-red-700' },
    };
    return riskMap[risk] || riskMap.medium;
  };

  const riskInfo = getRiskLabel(item.risk_level);

  return (
    <Link href={`/stock/${item.code}`}>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow cursor-pointer relative">
        {/* 自选按钮 */}
        <div className="absolute top-3 right-3 z-10">
          <WatchlistButton code={item.code} name={item.name} size="sm" />
        </div>

        {/* 排名和风险等级 */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            {/* AI 排名徽章 */}
            <span className={`
              text-white text-xs font-bold px-2 py-1 rounded
              ${item.rank <= 3 ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-purple-500'}
            `}>
              AI #{item.rank}
            </span>
            <span className={`text-xs px-2 py-1 rounded ${riskInfo.class}`}>
              {riskInfo.text}
            </span>
          </div>
          <div className="text-right pr-8">
            <div className="text-2xl font-bold text-purple-600">{item.ai_ranking_score}</div>
            <div className="text-xs text-gray-400">AI评分</div>
          </div>
        </div>

        {/* 股票名称和代码 */}
        <div className="mb-3">
          <h3 className="text-lg font-semibold text-gray-800">{item.name}</h3>
          <p className="text-sm text-gray-500">{item.code} · {item.industry}</p>
        </div>

        {/* 价格和涨跌 */}
        <div className="flex justify-between items-end mb-3">
          <div>
            <div className={`text-2xl font-bold ${isUp ? 'text-up' : 'text-down'}`}>
              ¥{item.price.toFixed(2)}
            </div>
            <div className={`text-sm ${isUp ? 'text-up' : 'text-down'}`}>
              {isUp ? '+' : ''}{item.change.toFixed(2)}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">操作建议</div>
            <div className={`text-sm font-semibold ${
              item.action === '买入' ? 'text-red-600' :
              item.action === '回避' ? 'text-green-600' :
              'text-blue-600'
            }`}>
              {item.action}
            </div>
          </div>
        </div>

        {/* 建议买入区间 */}
        <div className={`rounded-lg p-3 ${isUp ? 'bg-up' : 'bg-down'}`}>
          <div className="text-xs text-gray-600 mb-1">建议买入区间</div>
          <div className="text-sm font-semibold">
            ¥{item.buy_price_low.toFixed(2)} - ¥{item.buy_price_high.toFixed(2)}
          </div>
        </div>

        {/* 技术指标标签 */}
        <div className="flex flex-wrap gap-2 mt-3 text-xs">
          <span className={`px-2 py-1 rounded ${
            item.macd_signal.includes('金叉') ? 'bg-red-50 text-red-600' :
            item.macd_signal.includes('死叉') ? 'bg-green-50 text-green-600' :
            'bg-gray-50 text-gray-600'
          }`}>
            {item.macd_signal}
          </span>
          <span className={`px-2 py-1 rounded ${
            item.ma_trend === '多头排列' ? 'bg-red-50 text-red-600' :
            item.ma_trend === '空头排列' ? 'bg-green-50 text-green-600' :
            'bg-gray-50 text-gray-600'
          }`}>
            {item.ma_trend}
          </span>
          <span className="px-2 py-1 rounded bg-purple-50 text-purple-600">
            技术分 {item.technical_score}
          </span>
        </div>

        {/* 点击提示 */}
        <div className="mt-3 text-center text-xs text-gray-400">
          点击查看详细分析 →
        </div>
      </div>
    </Link>
  );
}

export default function HomeContent({ recommendations }: HomeContentProps) {
  const { watchlist } = useWatchlist();
  const [activeTab, setActiveTab] = useState<TabType>('recommendations');
  const [watchlistStocks, setWatchlistStocks] = useState<StockRecommendation[]>([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);

  // AI 排名状态
  const [aiRankings, setAIRankings] = useState<AIRankingItem[]>([]);
  const [loadingRankings, setLoadingRankings] = useState(false);
  const [rankingsError, setRankingsError] = useState<string | null>(null);
  const [aiModelStatus, setAIModelStatus] = useState<AIModelStatus | null>(null);

  // 预加载状态（避免重复请求）
  const prefetchedRef = useRef(false);

  // 首次加载时预加载推荐股票详情（后台执行，不阻塞UI）
  useEffect(() => {
    if (prefetchedRef.current || recommendations.length === 0) return;
    prefetchedRef.current = true;

    // 后台预加载，不等待结果
    const codes = recommendations.map(r => r.code);
    prefetchStocks(codes).catch(() => {
      // 预加载失败不影响用户体验，静默处理
    });
  }, [recommendations]);

  // 当切换到自选股 tab 或自选列表变化时，加载自选股数据
  useEffect(() => {
    if (activeTab === 'watchlist' && watchlist.length > 0) {
      loadWatchlistStocks();
    }
  }, [activeTab, watchlist]);

  // 当切换到 AI 排名 tab 时，加载排名数据
  useEffect(() => {
    if (activeTab === 'aiRankings' && aiRankings.length === 0) {
      loadAIRankings();
    }
  }, [activeTab]);

  const loadWatchlistStocks = async () => {
    setLoadingWatchlist(true);
    setWatchlistError(null);

    try {
      const stocks: StockRecommendation[] = [];

      for (const item of watchlist) {
        try {
          const analysis = await getStockAnalysis(item.code);
          stocks.push(convertToRecommendation(analysis));
        } catch {
          // 如果单个股票加载失败，使用基本信息
          stocks.push({
            code: item.code,
            name: item.name,
            industry: '加载失败',
            price: 0,
            change: 0,
            score: 0,
            buyPriceLow: 0,
            buyPriceHigh: 0,
            stopLoss: 0,
            takeProfit1: 0,
            takeProfit2: 0,
            holdingDays: '-',
            positionRatio: '-',
            reasons: { technical: [], fundamental: [], capital: [] },
            riskLevel: 'medium',
          });
        }
      }

      setWatchlistStocks(stocks);
    } catch {
      setWatchlistError('加载自选股失败，请检查网络');
    } finally {
      setLoadingWatchlist(false);
    }
  };

  const loadAIRankings = async () => {
    setLoadingRankings(true);
    setRankingsError(null);
    setAIModelStatus(null);

    try {
      // 如果后端可能休眠，先唤醒
      if (isBackendPossiblyAsleep()) {
        await wakeUpBackend();
      }
      const response = await getAIRankings(10);
      setAIRankings(response.rankings);

      // 更新 AI 模型状态
      if (response.ai_model_status) {
        setAIModelStatus(response.ai_model_status);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '加载失败';
      if (errorMsg.includes('冷启动') || errorMsg.includes('超时')) {
        setRankingsError('后端服务正在启动中，请稍后重试');
      } else {
        setRankingsError('加载 AI 排名失败，请检查网络');
      }
    } finally {
      setLoadingRankings(false);
    }
  };

  return (
    <section>
      {/* Tab 切换器 */}
      <TabSwitcher
        activeTab={activeTab}
        onTabChange={setActiveTab}
        recommendationsCount={recommendations.length}
        watchlistCount={watchlist.length}
        aiRankingsCount={aiRankings.length > 0 ? aiRankings.length : undefined}
      />

      {/* 推荐股票列表 */}
      {activeTab === 'recommendations' && (
        <div className="space-y-4">
          {recommendations.map((stock, index) => (
            <StockCard key={stock.code} stock={stock} rank={index + 1} />
          ))}
        </div>
      )}

      {/* AI 智能排名 */}
      {activeTab === 'aiRankings' && (
        <div className="space-y-4">
          {loadingRankings ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-3"></div>
              <p className="text-gray-500">AI 正在分析热门股票...</p>
              <p className="text-xs text-gray-400 mt-1">
                {isBackendPossiblyAsleep()
                  ? '后端服务启动中，可能需要 30-90 秒'
                  : '分析多只股票可能需要 10-30 秒'}
              </p>
              <div className="mt-3 w-48 mx-auto bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div className="bg-purple-500 h-1.5 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
            </div>
          ) : rankingsError ? (
            <div className="bg-white rounded-xl shadow-sm border border-red-100 p-6 text-center">
              <div className="text-4xl mb-3">⏳</div>
              <p className="text-sm font-medium text-gray-700 mb-1">
                {rankingsError.includes('启动') ? '后端服务正在启动' : '加载失败'}
              </p>
              <p className="text-xs text-gray-500 mb-3">{rankingsError}</p>
              <button
                onClick={loadAIRankings}
                className="px-4 py-2 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600"
              >
                重新加载
              </button>
            </div>
          ) : aiRankings.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
              <div className="text-4xl mb-3">🤖</div>
              <p className="text-gray-500">暂无 AI 排名数据</p>
              <button
                onClick={loadAIRankings}
                className="mt-3 text-purple-500 text-sm hover:underline"
              >
                立即加载
              </button>
            </div>
          ) : (
            <>
              {/* 说明 */}
              <div className="bg-purple-50 rounded-lg p-3 mb-4">
                <p className="text-xs text-purple-700">
                  🤖 AI 智能排名：综合技术面、资金面、趋势分析，为您精选高潜力股票
                </p>
              </div>

              {/* AI 模型状态告警 */}
              {aiModelStatus && !aiModelStatus.available && (
                <div className={`rounded-lg p-4 mb-4 ${
                  aiModelStatus.error_code === 'quota_exhausted'
                    ? 'bg-orange-50 border border-orange-200'
                    : aiModelStatus.error_code === 'auth_failed'
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-yellow-50 border border-yellow-200'
                }`}>
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">
                      {aiModelStatus.error_code === 'quota_exhausted' ? '💳' :
                       aiModelStatus.error_code === 'auth_failed' ? '🔐' :
                       aiModelStatus.error_code === 'unavailable' ? '🔌' :
                       aiModelStatus.error_code === 'rate_limited' ? '⏱️' : '⚠️'}
                    </div>
                    <div className="flex-1">
                      <h4 className={`font-semibold text-sm ${
                        aiModelStatus.error_code === 'quota_exhausted'
                          ? 'text-orange-800'
                          : aiModelStatus.error_code === 'auth_failed'
                          ? 'text-red-800'
                          : 'text-yellow-800'
                      }`}>
                        {aiModelStatus.error_code === 'quota_exhausted' ? 'AI 配额已用尽' :
                         aiModelStatus.error_code === 'auth_failed' ? 'AI 认证失败' :
                         aiModelStatus.error_code === 'unavailable' ? 'AI 模型暂时不可用' :
                         aiModelStatus.error_code === 'rate_limited' ? '请求过于频繁' :
                         aiModelStatus.error_code === 'timeout' ? 'AI 模型响应超时' : 'AI 模型异常'}
                      </h4>
                      <p className={`text-xs mt-1 ${
                        aiModelStatus.error_code === 'quota_exhausted'
                          ? 'text-orange-600'
                          : aiModelStatus.error_code === 'auth_failed'
                          ? 'text-red-600'
                          : 'text-yellow-600'
                      }`}>
                        {aiModelStatus.error_message || '当前使用基础技术分析，AI 智能分析暂时不可用'}
                      </p>
                      <p className="text-xs text-gray-500 mt-2">
                        ℹ️ 排名数据基于技术指标计算，AI 增强分析将在服务恢复后自动启用
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* 排名列表 */}
              {aiRankings.map((item) => (
                <AIRankingCard key={item.code} item={item} />
              ))}

              {/* 刷新按钮 */}
              <div className="text-center py-4">
                <button
                  onClick={loadAIRankings}
                  disabled={loadingRankings}
                  className="text-purple-500 text-sm hover:underline disabled:opacity-50"
                >
                  {loadingRankings ? '加载中...' : '刷新排名'}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* 自选股列表 */}
      {activeTab === 'watchlist' && (
        <div className="space-y-4">
          {watchlist.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
              <div className="text-4xl mb-3">☆</div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">暂无自选股</h3>
              <p className="text-sm text-gray-500 mb-4">
                点击股票卡片右上角的 ☆ 添加自选
              </p>
              <button
                onClick={() => setActiveTab('recommendations')}
                className="text-blue-500 text-sm hover:underline"
              >
                去添加 →
              </button>
            </div>
          ) : loadingWatchlist ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
              <p className="text-gray-500">加载自选股数据...</p>
            </div>
          ) : watchlistError ? (
            <div className="bg-white rounded-xl shadow-sm border border-red-100 p-6 text-center">
              <div className="text-red-400 text-4xl mb-3">⚠️</div>
              <p className="text-sm text-gray-500">{watchlistError}</p>
              <button
                onClick={loadWatchlistStocks}
                className="mt-3 text-blue-500 text-sm hover:underline"
              >
                重新加载
              </button>
            </div>
          ) : (
            <>
              {watchlistStocks.map((stock) => (
                <StockCard key={stock.code} stock={stock} />
              ))}
              <div className="text-center py-4">
                <Link
                  href="/search"
                  className="text-blue-500 text-sm hover:underline"
                >
                  搜索更多股票 →
                </Link>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
