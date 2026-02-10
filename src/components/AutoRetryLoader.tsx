'use client';

import { useState, useEffect } from 'react';
import { getRecommendations } from '@/lib/api';
import { MarketOverview, StockRecommendation } from '@/lib/types';
import MarketHeader from './MarketHeader';
import SearchBox from './SearchBox';
import HomeContent from './HomeContent';
import RefreshAllButton from './RefreshAllButton';
import Disclaimer from './Disclaimer';

/**
 * SSR 失败时的客户端自动重试加载器
 * 渲染完整页面框架，客户端自动获取数据
 */
export default function AutoRetryLoader() {
  const [loading, setLoading] = useState(true);
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [recommendations, setRecommendations] = useState<StockRecommendation[]>([]);
  const [date, setDate] = useState('');
  const [updateTime, setUpdateTime] = useState('');
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        const data = await getRecommendations();
        if (cancelled) return;

        setDate(data.date);
        setUpdateTime(data.update_time);
        setMarket({
          shIndex: { value: data.market.sh_index, change: data.market.sh_change },
          szIndex: { value: data.market.sz_index, change: data.market.sz_change },
          sentiment: data.market.sentiment,
        });
        // /recommendations 返回数据库格式（扁平字段），需要手动映射
        const recs = data.recommendations as unknown as Record<string, unknown>[];
        setRecommendations(
          recs.map((r) => ({
            code: r.code as string,
            name: r.name as string,
            industry: (r.industry as string) || '未知',
            price: r.price as number,
            change: r.change as number,
            score: r.score as number,
            buyPriceLow: (r.buy_price_low as number) || 0,
            buyPriceHigh: (r.buy_price_high as number) || 0,
            stopLoss: (r.stop_loss as number) || 0,
            takeProfit1: (r.take_profit_1 as number) || 0,
            takeProfit2: (r.take_profit_2 as number) || 0,
            holdingDays: (r.holding_days as string) || '5-15个交易日',
            positionRatio: (r.position_ratio as string) || '10-15%',
            reasons: {
              technical: ((r.reasons as Record<string, string[]>)?.technical) || [],
              fundamental: ((r.reasons as Record<string, string[]>)?.fundamental) || [],
              capital: ((r.reasons as Record<string, string[]>)?.capital) || [],
            },
            riskLevel: ((r.risk_level as string) || 'medium') as 'low' | 'medium' | 'high',
          }))
        );
        setLoading(false);
      } catch {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, []);

  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      <header className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Stock Advisor</h1>
          <p className="text-sm text-gray-500">A股交易策略指导系统</p>
        </div>
        <RefreshAllButton />
      </header>

      {/* Market header: show loading or real data */}
      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold text-gray-800">市场概览</h2>
            <div className="text-xs text-gray-400">加载中...</div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg p-3 bg-gray-50 animate-pulse h-20" />
            <div className="rounded-lg p-3 bg-gray-50 animate-pulse h-20" />
          </div>
        </div>
      ) : error ? (
        <div className="bg-white rounded-xl shadow-sm border border-red-100 p-4 mb-4 text-center">
          <p className="text-sm text-gray-500 mb-2">后端服务连接失败</p>
          <button
            onClick={() => window.location.reload()}
            className="text-blue-500 text-sm hover:underline"
          >
            刷新重试
          </button>
        </div>
      ) : market ? (
        <MarketHeader market={market} date={date} updateTime={updateTime} />
      ) : null}

      <SearchBox />

      {loading ? (
        <div className="text-center py-8 text-gray-400 text-sm">
          <div className="text-3xl mb-2">📊</div>
          正在加载推荐数据...
        </div>
      ) : (
        <HomeContent recommendations={recommendations} />
      )}

      <Disclaimer />

      <footer className="mt-8 text-center text-xs text-gray-400">
        <p>数据来源：东方财富 · 仅供学习研究</p>
      </footer>
    </main>
  );
}
