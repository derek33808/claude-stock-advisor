'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useWatchlist } from '@/lib/watchlist-context';
import { StockRecommendation } from '@/lib/types';
import { getBatchStockAnalyses, prefetchStocks, StockAnalysis } from '@/lib/api';
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

// 从批量接口返回的数据（可能是缓存或轻量数据）
function convertBatchItem(item: Record<string, unknown>): StockRecommendation {
  const suggestion = (item.suggestion || {}) as Record<string, unknown>;
  const buyPrice = (suggestion.buy_price || {}) as Record<string, number>;
  const takeProfit = (suggestion.take_profit || {}) as Record<string, number>;
  return {
    code: item.code as string,
    name: item.name as string,
    industry: (item.industry as string) || '未知',
    price: item.price as number,
    change: item.change as number,
    score: (item.score as number) || 0,
    buyPriceLow: buyPrice.low || 0,
    buyPriceHigh: buyPrice.high || 0,
    stopLoss: (suggestion.stop_loss as number) || 0,
    takeProfit1: takeProfit.target1 || 0,
    takeProfit2: takeProfit.target2 || 0,
    holdingDays: (suggestion.holding_days as string) || '-',
    positionRatio: (suggestion.position_ratio as string) || '-',
    reasons: { technical: [], fundamental: [], capital: [] },
    riskLevel: ((suggestion.risk_level as string) || 'medium') as 'low' | 'medium' | 'high',
  };
}

// 自选股占位符（加载中显示）
function makePlaceholder(code: string, name: string): StockRecommendation {
  return {
    code,
    name,
    industry: '',
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

    const codes = recommendations.map(r => r.code);
    prefetchStocks(codes).catch(() => {});
  }, [recommendations]);

  // 稳定的自选股 key
  const watchlistKey = useMemo(() => watchlist.map(w => w.code).join(','), [watchlist]);

  // 批量加载自选股（一个请求加载全部）
  const loadWatchlistStocks = useCallback(async () => {
    if (watchlist.length === 0) return;

    setLoadingWatchlist(true);
    setWatchlistError(null);

    // 先显示占位符
    setWatchlistStocks(watchlist.map(item => makePlaceholder(item.code, item.name)));

    try {
      const codes = watchlist.map(w => w.code);
      const result = await getBatchStockAnalyses(codes);

      // 按 watchlist 顺序排列结果
      const stockMap = new Map<string, Record<string, unknown>>();
      for (const stock of (result.stocks as unknown as Record<string, unknown>[])) {
        stockMap.set(stock.code as string, stock);
      }

      const ordered: StockRecommendation[] = watchlist.map(item => {
        const data = stockMap.get(item.code);
        if (data) {
          return convertBatchItem(data);
        }
        return { ...makePlaceholder(item.code, item.name), industry: '暂无数据' };
      });

      setWatchlistStocks(ordered);
    } catch {
      setWatchlistError('加载自选股失败，请检查网络后重试');
    } finally {
      setLoadingWatchlist(false);
    }
  }, [watchlist]);

  // 当切换到自选股 tab 或自选列表变化时，加载自选股数据
  useEffect(() => {
    if (activeTab === 'watchlist' && watchlistKey) {
      loadWatchlistStocks();
    }
  }, [activeTab, watchlistKey, loadWatchlistStocks]);

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
              {/* 加载提示 */}
              {loadingWatchlist && (
                <div className="text-center text-xs text-gray-400 py-1">
                  加载中...
                </div>
              )}

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
