'use client';

import { StockRecommendation } from '@/lib/types';
import Link from 'next/link';

interface StockCardProps {
  stock: StockRecommendation;
  rank: number;
}

export default function StockCard({ stock, rank }: StockCardProps) {
  const isUp = stock.change >= 0;

  return (
    <Link href={`/stock/${stock.code}`}>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow cursor-pointer">
        {/* 头部：排名和评分 */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <span className="bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded">
              #{rank}
            </span>
            <span className={`text-xs px-2 py-1 rounded ${
              stock.riskLevel === 'low' ? 'bg-green-100 text-green-700' :
              stock.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            }`}>
              {stock.riskLevel === 'low' ? '低风险' :
               stock.riskLevel === 'medium' ? '中风险' : '高风险'}
            </span>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">{stock.score}</div>
            <div className="text-xs text-gray-400">评分</div>
          </div>
        </div>

        {/* 股票名称和代码 */}
        <div className="mb-3">
          <h3 className="text-lg font-semibold text-gray-800">{stock.name}</h3>
          <p className="text-sm text-gray-500">{stock.code} · {stock.industry}</p>
        </div>

        {/* 价格和涨跌 */}
        <div className="flex justify-between items-end mb-3">
          <div>
            <div className={`text-2xl font-bold ${isUp ? 'text-up' : 'text-down'}`}>
              ¥{stock.price.toFixed(2)}
            </div>
            <div className={`text-sm ${isUp ? 'text-up' : 'text-down'}`}>
              {isUp ? '+' : ''}{stock.change.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* 交易建议摘要 */}
        <div className={`rounded-lg p-3 ${isUp ? 'bg-up' : 'bg-down'}`}>
          <div className="text-xs text-gray-600 mb-1">建议买入区间</div>
          <div className="text-sm font-semibold">
            ¥{stock.buyPriceLow.toFixed(2)} - ¥{stock.buyPriceHigh.toFixed(2)}
          </div>
        </div>

        {/* 点击提示 */}
        <div className="mt-3 text-center text-xs text-gray-400">
          点击查看详细分析 →
        </div>
      </div>
    </Link>
  );
}
