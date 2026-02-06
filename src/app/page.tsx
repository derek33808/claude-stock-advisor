import MarketHeader from '@/components/MarketHeader';
import SearchBox from '@/components/SearchBox';
import Disclaimer from '@/components/Disclaimer';
import RefreshAllButton from '@/components/RefreshAllButton';
import HomeContent from '@/components/HomeContent';
import { RecommendationData } from '@/lib/types';

// 强制动态渲染
export const dynamic = 'force-dynamic';

// 后端 API 地址
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getRecommendationsFromAPI(): Promise<RecommendationData | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recommendations`, {
      cache: 'no-store',
      next: { revalidate: 0 },
    });

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
        buyPriceLow: (r.suggestion as Record<string, unknown>)?.buy_price
          ? ((r.suggestion as Record<string, Record<string, number>>).buy_price.low || 0)
          : 0,
        buyPriceHigh: (r.suggestion as Record<string, unknown>)?.buy_price
          ? ((r.suggestion as Record<string, Record<string, number>>).buy_price.high || 0)
          : 0,
        stopLoss: (r.suggestion as Record<string, number>)?.stop_loss || 0,
        takeProfit1: (r.suggestion as Record<string, unknown>)?.take_profit
          ? ((r.suggestion as Record<string, Record<string, number>>).take_profit.target1 || 0)
          : 0,
        takeProfit2: (r.suggestion as Record<string, unknown>)?.take_profit
          ? ((r.suggestion as Record<string, Record<string, number>>).take_profit.target2 || 0)
          : 0,
        holdingDays: (r.suggestion as Record<string, string>)?.holding_days || '5-15个交易日',
        positionRatio: (r.suggestion as Record<string, string>)?.position_ratio || '10-15%',
        reasons: {
          technical: (r.reasons as string[] || []).filter((reason: string) =>
            reason.includes('技术') || reason.includes('MACD') || reason.includes('RSI') || reason.includes('均线')
          ),
          fundamental: (r.reasons as string[] || []).filter((reason: string) =>
            reason.includes('基本') || reason.includes('业绩') || reason.includes('估值')
          ),
          capital: (r.reasons as string[] || []).filter((reason: string) =>
            reason.includes('资金') || reason.includes('成交') || reason.includes('量')
          ),
        },
        riskLevel: (r.suggestion as Record<string, string>)?.risk_level || 'medium',
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

  if (!data) {
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <div className="text-center py-12">
          <div className="text-4xl mb-4">🔄</div>
          <h1 className="text-xl font-bold text-gray-800 mb-2">正在连接后端服务</h1>
          <p className="text-gray-500 mb-4">后端服务可能正在启动中（约需60秒）</p>
          <a
            href="/"
            className="inline-block px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
          >
            刷新重试
          </a>
        </div>
      </main>
    );
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
