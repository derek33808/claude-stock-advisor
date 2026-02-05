import MarketHeader from '@/components/MarketHeader';
import SearchBox from '@/components/SearchBox';
import Disclaimer from '@/components/Disclaimer';
import RefreshButton from '@/components/RefreshButton';
import HomeContent from '@/components/HomeContent';
import { RecommendationData } from '@/lib/types';
import { headers } from 'next/headers';

// 强制动态渲染
export const dynamic = 'force-dynamic';

async function getRecommendations(): Promise<RecommendationData | null> {
  try {
    // 从请求头获取主机名，构建完整 URL
    const headersList = await headers();
    const host = headersList.get('host') || 'localhost:3000';
    const protocol = host.includes('localhost') ? 'http' : 'https';
    const baseUrl = `${protocol}://${host}`;

    const res = await fetch(`${baseUrl}/data/recommendations.json`, {
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const data = await getRecommendations();

  if (!data) {
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <div className="text-center py-12">
          <h1 className="text-xl font-bold text-gray-800 mb-2">数据加载中</h1>
          <p className="text-gray-500">请先运行数据生成脚本</p>
          <code className="block mt-4 bg-gray-100 p-2 rounded text-sm">
            python scripts/generate_recommendations.py
          </code>
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
        <RefreshButton />
      </header>

      {/* 市场概览 */}
      <MarketHeader
        market={data.market}
        date={data.date}
        updateTime={data.updateTime}
      />

      {/* 股票查询 */}
      <SearchBox />

      {/* 股票列表（推荐 + 自选） */}
      <HomeContent recommendations={data.recommendations} />

      {/* 风险提示 */}
      <Disclaimer />

      {/* 页脚 */}
      <footer className="mt-8 text-center text-xs text-gray-400">
        <p>数据来源：AKShare · 仅供学习研究</p>
      </footer>
    </main>
  );
}
