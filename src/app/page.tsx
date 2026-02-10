import MarketHeader from '@/components/MarketHeader';
import SearchBox from '@/components/SearchBox';
import Disclaimer from '@/components/Disclaimer';
import RefreshAllButton from '@/components/RefreshAllButton';
import HomeContent from '@/components/HomeContent';
import AutoRetryLoader from '@/components/AutoRetryLoader';
import { RecommendationData } from '@/lib/types';

// 后端 API 地址
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getRecommendationsFromAPI(): Promise<RecommendationData | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    const res = await fetch(`${API_BASE}/api/v1/recommendations`, {
      cache: 'no-store',
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) return null;

    const data = await res.json();

    // 转换后端数据格式为前端格式
    return {
      date: data.date,
      updateTime: data.update_time,
      market: {
        shIndex: {
          value: data.market.sh_index,
          change: data.market.sh_change,
        },
        szIndex: {
          value: data.market.sz_index,
          change: data.market.sz_change,
        },
        sentiment: data.market.sentiment,
      },
      recommendations: data.recommendations.map((r: Record<string, unknown>) => ({
        code: r.code,
        name: r.name,
        industry: r.industry || '未知',
        price: r.price,
        change: r.change,
        score: r.score,
        buyPriceLow: (r.buy_price_low as number) || 0,
        buyPriceHigh: (r.buy_price_high as number) || 0,
        stopLoss: (r.stop_loss as number) || 0,
        takeProfit1: (r.take_profit_1 as number) || 0,
        takeProfit2: (r.take_profit_2 as number) || 0,
        holdingDays: (r.holding_days as string) || '5-15个交易日',
        positionRatio: (r.position_ratio as string) || '10-15%',
        reasons: {
          technical: (r.reasons as Record<string, string[]>)?.technical || [],
          fundamental: (r.reasons as Record<string, string[]>)?.fundamental || [],
          capital: (r.reasons as Record<string, string[]>)?.capital || [],
        },
        riskLevel: (r.risk_level as string) || 'medium',
      })),
      allStocks: [], // 后端 API 不返回此字段，使用空数组
    };
  } catch (error) {
    console.error('Failed to fetch from API:', error);
    return null;
  }
}

export default async function HomePage() {
  const data = await getRecommendationsFromAPI();

  // SSR 失败时，渲染完整页面框架 + 客户端自动重试
  if (!data) {
    return <AutoRetryLoader />;
  }

  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 页头 */}
      <header className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Stock Advisor</h1>
          <p className="text-sm text-gray-500">A股交易策略指导系统</p>
        </div>
        <RefreshAllButton />
      </header>

      {/* 市场概览 */}
      <MarketHeader
        market={data.market}
        date={data.date}
        updateTime={data.updateTime}
      />

      {/* 股票查询 */}
      <SearchBox />

      {/* 股票列表（推荐 + 自选 + AI排名） */}
      <HomeContent recommendations={data.recommendations} />

      {/* 风险提示 */}
      <Disclaimer />

      {/* 页脚 */}
      <footer className="mt-8 text-center text-xs text-gray-400">
        <p>数据来源：东方财富 · 仅供学习研究</p>
      </footer>
    </main>
  );
}
