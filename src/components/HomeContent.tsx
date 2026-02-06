'use client';

import { useState, useEffect, useRef } from 'react';
import { useWatchlist } from '@/lib/watchlist-context';
import { StockRecommendation } from '@/lib/types';
import { getStockAnalysis, prefetchStocks, StockAnalysis } from '@/lib/api';
import StockCard from './StockCard';
import TabSwitcher, { TabType } from './TabSwitcher';
import Link from 'next/link';
import ProgressBar from './ProgressBar';

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

export default function HomeContent({ recommendations }: HomeContentProps) {
  const { watchlist } = useWatchlist();
  const [activeTab, setActiveTab] = useState<TabType>('recommendations');
  const [watchlistStocks, setWatchlistStocks] = useState<StockRecommendation[]>([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);

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

  return (
    <section>
      {/* Tab 切换器 */}
      <TabSwitcher
        activeTab={activeTab}
        onTabChange={setActiveTab}
        recommendationsCount={recommendations.length}
        watchlistCount={watchlist.length}
      />

      {/* 智能推荐列表 */}
      {activeTab === 'recommendations' && (
        <div className="space-y-4">
          {/* 说明 */}
          <div className="bg-blue-50 rounded-lg p-3 mb-4">
            <p className="text-xs text-blue-700">
              🤖 智能推荐：综合技术面 + AI基本面分析，为您精选高潜力股票
            </p>
          </div>

          {recommendations.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
              <div className="text-4xl mb-3">📊</div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">暂无推荐</h3>
              <p className="text-sm text-gray-500">
                点击右上角"一键刷新"生成智能推荐
              </p>
            </div>
          ) : (
            recommendations.map((stock, index) => (
              <StockCard key={stock.code} stock={stock} rank={index + 1} />
            ))
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
              <div className="mt-3 w-48 mx-auto">
                <ProgressBar estimatedSeconds={10} color="blue" />
              </div>
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
