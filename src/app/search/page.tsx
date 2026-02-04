'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { RecommendationData, StockRecommendation } from '@/lib/types';
import Disclaimer from '@/components/Disclaimer';

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const code = searchParams.get('code') || '';
  const [data, setData] = useState<RecommendationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchCode, setSearchCode] = useState(code);
  const [searchedCode, setSearchedCode] = useState(code);

  // 加载数据
  useEffect(() => {
    fetch('/data/recommendations.json')
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // 同步 URL 参数
  useEffect(() => {
    setSearchCode(code);
    setSearchedCode(code);
  }, [code]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchCode.trim()) {
      setSearchedCode(searchCode.trim());
      router.push(`/search?code=${searchCode.trim()}`);
    }
  };

  // 查找股票 - 支持模糊匹配
  const stock = data?.allStocks?.find(
    (s) =>
      s.code === searchedCode ||
      s.code.includes(searchedCode) ||
      s.name.includes(searchedCode)
  );

  // 是否在推荐列表中
  const isRecommended = data?.recommendations?.some((s) => s.code === stock?.code);

  if (loading) {
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <div className="text-center py-12">
          <div className="text-gray-500">加载中...</div>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 返回按钮 */}
      <Link href="/" className="inline-flex items-center text-blue-500 text-sm mb-4">
        ← 返回首页
      </Link>

      {/* 搜索框 */}
      <form onSubmit={handleSearch} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchCode}
            onChange={(e) => setSearchCode(e.target.value)}
            placeholder="输入股票代码或名称"
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
          >
            查询
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          支持查询分析库中的股票（当前共 {data?.allStocks?.length || 0} 支）
        </p>
      </form>

      {/* 查询结果 */}
      {searchedCode && !stock && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <div className="text-gray-400 text-4xl mb-3">🔍</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">未找到股票</h2>
          <p className="text-sm text-gray-500">
            股票 &quot;{searchedCode}&quot; 不在分析库中。
            <br />
            请检查代码是否正确，或尝试其他关键词。
          </p>
        </div>
      )}

      {!searchedCode && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <div className="text-gray-400 text-4xl mb-3">📊</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">输入股票代码查询</h2>
          <p className="text-sm text-gray-500">
            输入股票代码（如 600519）或名称（如 茅台）进行查询
          </p>
        </div>
      )}

      {stock && <StockAnalysis stock={stock} isRecommended={isRecommended} />}

      <Disclaimer />
    </main>
  );
}

// 股票分析结果组件
function StockAnalysis({
  stock,
  isRecommended,
}: {
  stock: StockRecommendation;
  isRecommended?: boolean;
}) {
  const isUp = stock.change >= 0;

  return (
    <>
      {/* 推荐标签 */}
      {isRecommended && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mb-4 text-center">
          <span className="text-blue-600 font-semibold">⭐ 今日推荐股票</span>
        </div>
      )}

      {/* 股票基本信息 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{stock.name}</h1>
            <p className="text-sm text-gray-500">{stock.code} · {stock.industry}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-600">{stock.score}</div>
            <div className="text-xs text-gray-400">综合评分</div>
          </div>
        </div>

        <div className={`mt-4 p-3 rounded-lg ${isUp ? 'bg-red-50' : 'bg-green-50'}`}>
          <div className={`text-3xl font-bold ${isUp ? 'text-up' : 'text-down'}`}>
            ¥{stock.price.toFixed(2)}
          </div>
          <div className={`text-lg ${isUp ? 'text-up' : 'text-down'}`}>
            {isUp ? '+' : ''}{stock.change.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* 交易建议 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">交易建议</h2>

        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">建议买入价</div>
            <div className="text-lg font-semibold text-gray-800">
              ¥{stock.buyPriceLow.toFixed(2)} - ¥{stock.buyPriceHigh.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">止损价</div>
            <div className="text-lg font-semibold text-red-500">
              ¥{stock.stopLoss.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">止盈目标1</div>
            <div className="text-lg font-semibold text-green-500">
              ¥{stock.takeProfit1.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">止盈目标2</div>
            <div className="text-lg font-semibold text-green-500">
              ¥{stock.takeProfit2.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">建议仓位</div>
            <div className="text-lg font-semibold text-gray-800">{stock.positionRatio}</div>
          </div>
          <div className="flex justify-between items-center py-2">
            <div className="text-sm text-gray-600">持有周期</div>
            <div className="text-lg font-semibold text-gray-800">{stock.holdingDays}</div>
          </div>
        </div>
      </div>

      {/* 推荐理由 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">分析报告</h2>

        {stock.reasons.technical.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">技术面</h3>
            <ul className="space-y-1">
              {stock.reasons.technical.map((item, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {stock.reasons.fundamental.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">基本面</h3>
            <ul className="space-y-1">
              {stock.reasons.fundamental.map((item, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {stock.reasons.capital.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">资金面</h3>
            <ul className="space-y-1">
              {stock.reasons.capital.map((item, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 风险等级 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className={`text-center p-4 rounded-lg ${
          stock.riskLevel === 'low' ? 'bg-green-50' :
          stock.riskLevel === 'medium' ? 'bg-yellow-50' :
          'bg-red-50'
        }`}>
          <div className={`text-xl font-bold ${
            stock.riskLevel === 'low' ? 'text-green-600' :
            stock.riskLevel === 'medium' ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            风险等级：{stock.riskLevel === 'low' ? '低' :
             stock.riskLevel === 'medium' ? '中' : '高'}
          </div>
        </div>
      </div>
    </>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="max-w-lg mx-auto px-4 py-6 text-center">加载中...</div>}>
      <SearchContent />
    </Suspense>
  );
}
