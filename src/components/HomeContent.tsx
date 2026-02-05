'use client';

import { useState, useEffect } from 'react';
import { useWatchlist } from '@/lib/watchlist-context';
import { StockRecommendation } from '@/lib/types';
import { getStockAnalysis, getAIRankings, StockAnalysis, AIRankingItem } from '@/lib/api';
import StockCard from './StockCard';
import TabSwitcher, { TabType } from './TabSwitcher';
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

// AI 排名卡片组件
function AIRankingCard({ item }: { item: AIRankingItem }) {
  const isUp = item.change >= 0;

  // 根据 AI 评分确定颜色
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-blue-600 bg-blue-50';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  // 根据建议确定颜色
  const getSuggestionColor = (suggestion: string) => {
    if (suggestion === '买入' || suggestion === '强烈买入') return 'text-red-600 bg-red-50';
    if (suggestion === '观望' || suggestion === '持有') return 'text-blue-600 bg-blue-50';
    if (suggestion === '回避' || suggestion === '卖出') return 'text-green-600 bg-green-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <Link href={`/stock/${item.code}`}>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow">
        {/* 排名和基本信息 */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            {/* 排名 */}
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
              ${item.rank <= 3 ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-white' : 'bg-gray-100 text-gray-600'}
            `}>
              {item.rank}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-800">{item.name}</span>
                <span className="text-xs text-gray-400">{item.code}</span>
              </div>
              <span className="text-xs text-gray-500">{item.industry}</span>
            </div>
          </div>

          {/* AI 评分 */}
          <div className={`px-3 py-1 rounded-full text-sm font-bold ${getScoreColor(item.ai_ranking_score)}`}>
            {item.ai_ranking_score}分
          </div>
        </div>

        {/* 价格和涨跌 */}
        <div className="flex items-center justify-between mb-3">
          <div>
            <span className="text-xl font-bold text-gray-800">¥{item.price.toFixed(2)}</span>
            <span className={`ml-2 text-sm font-medium ${isUp ? 'text-red-500' : 'text-green-500'}`}>
              {isUp ? '+' : ''}{item.change.toFixed(2)}%
            </span>
          </div>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSuggestionColor(item.suggestion)}`}>
            {item.suggestion}
          </span>
        </div>

        {/* 技术指标 */}
        <div className="flex gap-2 text-xs">
          <span className={`px-2 py-1 rounded ${
            item.macd_signal.includes('金叉') ? 'bg-red-50 text-red-600' :
            item.macd_signal.includes('死叉') ? 'bg-green-50 text-green-600' :
            'bg-gray-50 text-gray-600'
          }`}>
            MACD: {item.macd_signal}
          </span>
          <span className={`px-2 py-1 rounded ${
            item.ma_trend === '多头排列' ? 'bg-red-50 text-red-600' :
            item.ma_trend === '空头排列' ? 'bg-green-50 text-green-600' :
            'bg-gray-50 text-gray-600'
          }`}>
            {item.ma_trend}
          </span>
          <span className="px-2 py-1 rounded bg-purple-50 text-purple-600">
            技术分: {item.technical_score}
          </span>
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

    try {
      const response = await getAIRankings(10);
      setAIRankings(response.rankings);
    } catch {
      setRankingsError('加载 AI 排名失败，请检查网络');
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
              <p className="text-xs text-gray-400 mt-1">首次加载可能需要较长时间</p>
            </div>
          ) : rankingsError ? (
            <div className="bg-white rounded-xl shadow-sm border border-red-100 p-6 text-center">
              <div className="text-red-400 text-4xl mb-3">⚠️</div>
              <p className="text-sm text-gray-500">{rankingsError}</p>
              <button
                onClick={loadAIRankings}
                className="mt-3 text-purple-500 text-sm hover:underline"
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
