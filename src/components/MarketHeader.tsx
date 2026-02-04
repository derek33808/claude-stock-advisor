'use client';

import { MarketOverview } from '@/lib/types';

interface MarketHeaderProps {
  market: MarketOverview;
  date: string;
  updateTime: string;
}

export default function MarketHeader({ market, date, updateTime }: MarketHeaderProps) {
  const shUp = market.shIndex.change >= 0;
  const szUp = market.szIndex.change >= 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-gray-800">市场概览</h2>
        <div className="text-xs text-gray-400">
          {date} · 更新于 {updateTime}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* 上证指数 */}
        <div className={`rounded-lg p-3 ${shUp ? 'bg-up' : 'bg-down'}`}>
          <div className="text-xs text-gray-600">上证指数</div>
          <div className={`text-xl font-bold ${shUp ? 'text-up' : 'text-down'}`}>
            {market.shIndex.value.toFixed(2)}
          </div>
          <div className={`text-sm ${shUp ? 'text-up' : 'text-down'}`}>
            {shUp ? '+' : ''}{market.shIndex.change.toFixed(2)}%
          </div>
        </div>

        {/* 深证成指 */}
        <div className={`rounded-lg p-3 ${szUp ? 'bg-up' : 'bg-down'}`}>
          <div className="text-xs text-gray-600">深证成指</div>
          <div className={`text-xl font-bold ${szUp ? 'text-up' : 'text-down'}`}>
            {market.szIndex.value.toFixed(2)}
          </div>
          <div className={`text-sm ${szUp ? 'text-up' : 'text-down'}`}>
            {szUp ? '+' : ''}{market.szIndex.change.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* 市场情绪 */}
      <div className="mt-3 text-center">
        <span className="text-sm text-gray-600">市场情绪：</span>
        <span className={`text-sm font-semibold ${
          market.sentiment === '偏多' ? 'text-up' :
          market.sentiment === '偏空' ? 'text-down' : 'text-gray-600'
        }`}>
          {market.sentiment}
        </span>
      </div>
    </div>
  );
}
