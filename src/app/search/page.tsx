'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { getStockAnalysis, StockAnalysis, ApiError } from '@/lib/api';
import Disclaimer from '@/components/Disclaimer';

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const code = searchParams.get('code') || '';
  const [stock, setStock] = useState<StockAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchCode, setSearchCode] = useState(code);

  // 查询股票
  const fetchStock = async (stockCode: string) => {
    if (!stockCode.trim()) return;

    setLoading(true);
    setError(null);
    setStock(null);

    try {
      const data = await getStockAnalysis(stockCode.trim());
      setStock(data);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 404) {
          setError(`未找到股票 "${stockCode}"，请检查代码是否正确`);
        } else {
          setError(err.message);
        }
      } else {
        setError('网络错误，请检查后端服务是否运行');
      }
    } finally {
      setLoading(false);
    }
  };

  // 初始加载或 URL 参数变化时查询
  useEffect(() => {
    if (code) {
      setSearchCode(code);
      fetchStock(code);
    }
  }, [code]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchCode.trim()) {
      router.push(`/search?code=${searchCode.trim()}`);
    }
  };

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
            placeholder="输入股票代码，如 600519"
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors disabled:bg-gray-400"
          >
            {loading ? '查询中...' : '查询'}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          支持查询所有 A 股股票和 ETF，实时计算分析
        </p>
      </form>

      {/* 加载状态 */}
      {loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-3"></div>
          <p className="text-gray-500">正在分析股票数据，请稍候...</p>
          <p className="text-xs text-gray-400 mt-1">首次查询可能需要几秒钟</p>
        </div>
      )}

      {/* 错误状态 */}
      {error && !loading && (
        <div className="bg-white rounded-xl shadow-sm border border-red-100 p-6 text-center">
          <div className="text-red-400 text-4xl mb-3">⚠️</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">查询失败</h2>
          <p className="text-sm text-gray-500">{error}</p>
        </div>
      )}

      {/* 空状态 */}
      {!code && !loading && !error && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <div className="text-gray-400 text-4xl mb-3">📊</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">输入股票代码查询</h2>
          <p className="text-sm text-gray-500">
            输入任意 A 股股票代码（如 600519）或 ETF 代码（如 512930）
            <br />
            系统将实时计算技术指标并生成交易建议
          </p>
        </div>
      )}

      {/* 查询结果 */}
      {stock && !loading && <StockAnalysisResult stock={stock} />}

      <Disclaimer />
    </main>
  );
}

// 股票分析结果组件
function StockAnalysisResult({ stock }: { stock: StockAnalysis }) {
  const isUp = stock.change >= 0;

  return (
    <>
      {/* 股票基本信息 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{stock.name}</h1>
            <p className="text-sm text-gray-500">{stock.code} · {stock.industry || '未知行业'}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-600">{stock.score}</div>
            <div className="text-xs text-gray-400">综合评分</div>
          </div>
        </div>

        <div className={`mt-4 p-3 rounded-lg ${isUp ? 'bg-red-50' : 'bg-green-50'}`}>
          <div className={`text-3xl font-bold ${isUp ? 'text-red-500' : 'text-green-500'}`}>
            ¥{stock.price.toFixed(2)}
          </div>
          <div className={`text-lg ${isUp ? 'text-red-500' : 'text-green-500'}`}>
            {isUp ? '+' : ''}{stock.change.toFixed(2)}%
          </div>
        </div>

        {/* 今日行情 */}
        <div className="mt-3 grid grid-cols-4 gap-2 text-center text-sm">
          <div>
            <div className="text-gray-400">开盘</div>
            <div className="font-medium">{stock.open.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-gray-400">最高</div>
            <div className="font-medium text-red-500">{stock.high.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-gray-400">最低</div>
            <div className="font-medium text-green-500">{stock.low.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-gray-400">成交量</div>
            <div className="font-medium">{formatVolume(stock.volume)}</div>
          </div>
        </div>
      </div>

      {/* 交易建议 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          交易建议
          <span className={`ml-2 text-sm px-2 py-1 rounded ${
            stock.suggestion.action === '买入' ? 'bg-red-100 text-red-600' :
            stock.suggestion.action === '卖出' ? 'bg-green-100 text-green-600' :
            'bg-gray-100 text-gray-600'
          }`}>
            {stock.suggestion.action}
          </span>
        </h2>

        <div className="space-y-3">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">建议买入价</div>
            <div className="text-lg font-semibold text-gray-800">
              ¥{stock.suggestion.buy_price.low.toFixed(2)} - ¥{stock.suggestion.buy_price.high.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">止损价</div>
            <div className="text-lg font-semibold text-red-500">
              ¥{stock.suggestion.stop_loss.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">止盈目标1</div>
            <div className="text-lg font-semibold text-green-500">
              ¥{stock.suggestion.take_profit.target1.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">止盈目标2</div>
            <div className="text-lg font-semibold text-green-500">
              ¥{stock.suggestion.take_profit.target2.toFixed(2)}
            </div>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <div className="text-sm text-gray-600">建议仓位</div>
            <div className="text-lg font-semibold text-gray-800">{stock.suggestion.position_ratio}</div>
          </div>
          <div className="flex justify-between items-center py-2">
            <div className="text-sm text-gray-600">持有周期</div>
            <div className="text-lg font-semibold text-gray-800">{stock.suggestion.holding_days}</div>
          </div>
        </div>
      </div>

      {/* 技术指标 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">技术指标</h2>

        <div className="grid grid-cols-2 gap-3">
          <IndicatorCard
            title="MACD"
            value={stock.indicators.macd.histogram.toFixed(3)}
            label={stock.indicators.macd.trend}
            color={stock.indicators.macd.histogram > 0 ? 'red' : 'green'}
          />
          <IndicatorCard
            title="RSI"
            value={stock.indicators.rsi.value.toFixed(1)}
            label={stock.indicators.rsi.level}
            color={stock.indicators.rsi.value > 70 ? 'red' : stock.indicators.rsi.value < 30 ? 'green' : 'gray'}
          />
          <IndicatorCard
            title="KDJ-K"
            value={stock.indicators.kdj.k.toFixed(1)}
            label={stock.indicators.kdj.k > 80 ? '超买' : stock.indicators.kdj.k < 20 ? '超卖' : '中性'}
            color={stock.indicators.kdj.k > 80 ? 'red' : stock.indicators.kdj.k < 20 ? 'green' : 'gray'}
          />
          <IndicatorCard
            title="均线"
            value={stock.indicators.ma.alignment}
            label={`MA5: ${stock.indicators.ma.ma5.toFixed(2)}`}
            color={stock.indicators.ma.alignment === '多头排列' ? 'red' : stock.indicators.ma.alignment === '空头排列' ? 'green' : 'gray'}
          />
          <IndicatorCard
            title="BOLL"
            value={stock.indicators.boll.position}
            label={`中轨: ${stock.indicators.boll.middle.toFixed(2)}`}
            color={stock.indicators.boll.position === '上轨附近' ? 'red' : stock.indicators.boll.position === '下轨附近' ? 'green' : 'gray'}
          />
          <IndicatorCard
            title="量比"
            value={stock.indicators.volume_ratio.toFixed(2)}
            label={stock.indicators.volume_ratio > 2 ? '放量' : stock.indicators.volume_ratio < 0.5 ? '缩量' : '正常'}
            color={stock.indicators.volume_ratio > 2 ? 'red' : 'gray'}
          />
        </div>
      </div>

      {/* 分析报告 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">分析报告</h2>
        <ul className="space-y-2">
          {stock.reasons.map((reason, i) => (
            <li key={i} className="text-sm text-gray-600 flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* 风险等级 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className={`text-center p-4 rounded-lg ${
          stock.suggestion.risk_level === 'low' ? 'bg-green-50' :
          stock.suggestion.risk_level === 'medium' ? 'bg-yellow-50' :
          'bg-red-50'
        }`}>
          <div className={`text-xl font-bold ${
            stock.suggestion.risk_level === 'low' ? 'text-green-600' :
            stock.suggestion.risk_level === 'medium' ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            风险等级：{stock.suggestion.risk_level === 'low' ? '低' :
             stock.suggestion.risk_level === 'medium' ? '中' : '高'}
          </div>
        </div>
      </div>
    </>
  );
}

// 指标卡片组件
function IndicatorCard({
  title,
  value,
  label,
  color,
}: {
  title: string;
  value: string;
  label: string;
  color: 'red' | 'green' | 'gray';
}) {
  const colorClasses = {
    red: 'text-red-500',
    green: 'text-green-500',
    gray: 'text-gray-600',
  };

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="text-xs text-gray-400">{title}</div>
      <div className={`text-lg font-semibold ${colorClasses[color]}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

// 格式化成交量
function formatVolume(volume: number): string {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿';
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(0) + '万';
  }
  return volume.toString();
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="max-w-lg mx-auto px-4 py-6 text-center">加载中...</div>}>
      <SearchContent />
    </Suspense>
  );
}
