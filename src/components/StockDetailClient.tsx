'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { getStockAnalysis, StockAnalysis, wakeUpBackend, isBackendPossiblyAsleep } from '@/lib/api';
import Disclaimer from './Disclaimer';
import WatchlistButton from './WatchlistButton';
import ProgressBar from './ProgressBar';
import StockChatPanel from './StockChatPanel';

interface StockDetailClientProps {
  code: string;
}

export default function StockDetailClient({ code }: StockDetailClientProps) {
  const [stock, setStock] = useState<StockAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState('加载股票数据中...');
  const [retryCount, setRetryCount] = useState(0);

  const fetchStock = useCallback(async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // 检查后端是否可能休眠（仅首次加载时）
      if (!forceRefresh && isBackendPossiblyAsleep()) {
        setLoadingMessage('正在唤醒后端服务...');
        await wakeUpBackend();
      }

      setLoadingMessage(forceRefresh ? '正在重新分析...' : '正在获取股票数据...');
      const data = await getStockAnalysis(code, forceRefresh);
      setStock(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [code]);

  useEffect(() => {
    fetchStock();
  }, [fetchStock, retryCount]);

  const handleRetry = () => {
    setRetryCount(c => c + 1);
  };

  const handleRefresh = () => {
    fetchStock(true);
  };

  // 计算缓存年龄提示
  const getCacheHint = () => {
    if (!stock) return null;
    const cacheInfo = (stock as unknown as Record<string, unknown>).cache_info as Record<string, unknown> | undefined;
    if (!cacheInfo?.cached) return null;
    const updatedAt = cacheInfo.analysis_updated_at as string;
    if (!updatedAt) return null;
    const ageMs = Date.now() - new Date(updatedAt).getTime();
    const ageMin = Math.round(ageMs / 60000);
    if (ageMin < 1) return '刚刚更新';
    if (ageMin < 60) return `${ageMin}分钟前更新`;
    return `${Math.round(ageMin / 60)}小时前更新`;
  };

  // 加载中状态
  if (loading) {
    const isColdStart = isBackendPossiblyAsleep();
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <Link href="/" className="inline-flex items-center text-blue-500 text-sm mb-4">
          ← 返回首页
        </Link>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">{loadingMessage}</h2>
          <p className="text-sm text-gray-500">股票代码: {code}</p>
          <p className="text-xs text-gray-400 mt-2">
            {isColdStart
              ? '后端服务冷启动中，可能需要 30-60 秒'
              : '首次加载可能需要 10-30 秒'}
          </p>
          {/* 真实进度条 */}
          <div className="mt-4 w-48 mx-auto">
            <ProgressBar
              estimatedSeconds={isColdStart ? 45 : 15}
              showPercent
              color="blue"
            />
          </div>
        </div>
      </main>
    );
  }

  // 错误状态
  if (error || !stock) {
    const isColdStartError = error?.includes('冷启动') || error?.includes('超时');
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <Link href="/" className="text-blue-500 text-sm">← 返回首页</Link>
        <div className="text-center py-12">
          <div className="text-4xl mb-4">{isColdStartError ? '⏳' : '📊'}</div>
          <h1 className="text-xl font-bold text-gray-800">
            {isColdStartError ? '后端服务正在启动' : '暂时无法获取数据'}
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            {isColdStartError
              ? '免费服务器休眠后需要约60秒启动，请点击重试'
              : '可能的原因：'}
          </p>
          {!isColdStartError && (
            <ul className="text-sm text-gray-500 mt-2 space-y-1">
              <li>• 后端服务正在启动中</li>
              <li>• 股票代码 {code} 可能不正确</li>
              <li>• 网络连接问题</li>
            </ul>
          )}
          {error && (
            <p className="text-xs text-red-500 mt-4 max-w-xs mx-auto">{error}</p>
          )}
          <div className="mt-6 space-x-4">
            <button
              onClick={handleRetry}
              className="inline-block px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
            >
              {isColdStartError ? '重新加载' : '刷新重试'}
            </button>
            <Link
              href="/"
              className="inline-block px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300"
            >
              返回首页
            </Link>
          </div>
        </div>
      </main>
    );
  }

  const isUp = stock.change >= 0;

  // 风险等级映射
  const getRiskDisplay = (risk: string) => {
    const riskMap: Record<string, { text: string; bgClass: string; textClass: string }> = {
      'low': { text: '低风险', bgClass: 'bg-green-50', textClass: 'text-green-600' },
      '低': { text: '低风险', bgClass: 'bg-green-50', textClass: 'text-green-600' },
      'medium': { text: '中风险', bgClass: 'bg-yellow-50', textClass: 'text-yellow-600' },
      '中': { text: '中风险', bgClass: 'bg-yellow-50', textClass: 'text-yellow-600' },
      'high': { text: '高风险', bgClass: 'bg-red-50', textClass: 'text-red-600' },
      '高': { text: '高风险', bgClass: 'bg-red-50', textClass: 'text-red-600' },
    };
    return riskMap[risk] || { text: '中风险', bgClass: 'bg-yellow-50', textClass: 'text-yellow-600' };
  };

  const riskDisplay = getRiskDisplay(stock.suggestion.risk_level);

  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 返回按钮 + 缓存状态 */}
      <div className="flex justify-between items-center mb-4">
        <Link href="/" className="inline-flex items-center text-blue-500 text-sm">
          ← 返回首页
        </Link>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            {refreshing ? (
              <>
                <span className="animate-spin">⟳</span>
                分析中...
              </>
            ) : (
              <>⟳ 刷新分析</>
            )}
          </button>
          <WatchlistButton code={stock.code} name={stock.name} size="md" />
        </div>
      </div>

      {/* 缓存状态提示 */}
      {getCacheHint() && (
        <div className="mb-3 flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg text-xs text-gray-500">
          <span>分析数据 · {getCacheHint()}</span>
          <span className="text-green-500">行情实时</span>
        </div>
      )}

      {/* 股票基本信息 */}
      <header className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
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

        {/* 价格信息 */}
        <div className={`mt-4 p-3 rounded-lg ${isUp ? 'bg-up' : 'bg-down'}`}>
          <div className={`text-3xl font-bold ${isUp ? 'text-up' : 'text-down'}`}>
            ¥{stock.price.toFixed(2)}
          </div>
          <div className={`text-lg ${isUp ? 'text-up' : 'text-down'}`}>
            {isUp ? '+' : ''}{stock.change.toFixed(2)}%
          </div>
        </div>
      </header>

      {/* 交易建议 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">交易建议</h2>

        <div className="space-y-3">
          <TradingItem
            label="建议买入价"
            value={`¥${stock.suggestion.buy_price.low.toFixed(2)} - ¥${stock.suggestion.buy_price.high.toFixed(2)}`}
            hint="等待回调至此区间买入"
          />
          <TradingItem
            label="止损价"
            value={`¥${stock.suggestion.stop_loss.toFixed(2)}`}
            hint={`跌破即止损 (${(((stock.suggestion.stop_loss - stock.suggestion.buy_price.low) / stock.suggestion.buy_price.low) * 100).toFixed(1)}%)`}
            danger
          />
          <TradingItem
            label="止盈目标1"
            value={`¥${stock.suggestion.take_profit.target1.toFixed(2)}`}
            hint={`盈利 ${(((stock.suggestion.take_profit.target1 - stock.suggestion.buy_price.low) / stock.suggestion.buy_price.low) * 100).toFixed(1)}% 可减仓`}
            success
          />
          <TradingItem
            label="止盈目标2"
            value={`¥${stock.suggestion.take_profit.target2.toFixed(2)}`}
            hint={`盈利 ${(((stock.suggestion.take_profit.target2 - stock.suggestion.buy_price.low) / stock.suggestion.buy_price.low) * 100).toFixed(1)}% 可清仓`}
            success
          />
          <TradingItem
            label="建议仓位"
            value={stock.suggestion.position_ratio}
            hint="单只股票投入比例"
          />
          <TradingItem
            label="持有周期"
            value={stock.suggestion.holding_days}
            hint="建议持有时间"
          />
        </div>
      </section>

      {/* 推荐理由 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">推荐理由</h2>
        <ul className="space-y-1">
          {stock.reasons.map((reason, index) => (
            <li key={index} className="text-sm text-gray-600 flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              {reason}
            </li>
          ))}
        </ul>
      </section>

      {/* 风险等级 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">风险评估</h2>
        <div className={`text-center p-4 rounded-lg ${riskDisplay.bgClass}`}>
          <div className={`text-2xl font-bold ${riskDisplay.textClass}`}>
            {riskDisplay.text}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {stock.suggestion.risk_level === 'low' || stock.suggestion.risk_level === '低' ? '波动较小，适合稳健型投资者' :
             stock.suggestion.risk_level === 'medium' || stock.suggestion.risk_level === '中' ? '波动适中，注意控制仓位' :
             '波动较大，建议小仓位参与'}
          </p>
        </div>
      </section>

      {/* 交易指导摘要 */}
      {stock.summary && (
        <section className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-sm border border-blue-100 p-4 mb-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
            <span className="mr-2">📝</span>
            交易指导
          </h2>
          <div className="bg-white rounded-lg p-4 text-sm text-gray-700 whitespace-pre-line leading-relaxed">
            {stock.summary}
          </div>
        </section>
      )}

      {/* 历史分析入口 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">历史分析记录</h2>
            <p className="text-xs text-gray-500 mt-1">查看过去30天的分析和预测准确率</p>
          </div>
          <Link
            href={`/history/${stock.code}`}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors flex items-center gap-1"
          >
            <span>查看历史</span>
            <span>→</span>
          </Link>
        </div>
      </section>

      {/* AI 问答 */}
      <StockChatPanel code={stock.code} stockName={stock.name} />

      {/* 风险提示 */}
      <Disclaimer />
    </main>
  );
}

// 交易建议项组件
function TradingItem({
  label,
  value,
  hint,
  danger,
  success,
}: {
  label: string;
  value: string;
  hint?: string;
  danger?: boolean;
  success?: boolean;
}) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
      <div>
        <div className="text-sm text-gray-600">{label}</div>
        {hint && <div className="text-xs text-gray-400">{hint}</div>}
      </div>
      <div className={`text-lg font-semibold ${
        danger ? 'text-red-500' :
        success ? 'text-green-500' :
        'text-gray-800'
      }`}>
        {value}
      </div>
    </div>
  );
}
