'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getAnalysisHistory, getAccuracyStats } from '@/lib/api';
import ProgressBar from './ProgressBar';

interface HistoryClientProps {
  code: string;
}

interface HistoryRecord {
  id: string;
  code: string;
  analysis_date: string;
  analysis_time: string;
  price: number;
  change_percent: number;
  prediction_direction: string;
  prediction_text: string;
  target_price_low: number;
  target_price_high: number;
  evaluation?: {
    evaluation_date: string;
    actual_price: number;
    price_change_percent: number;
    is_direction_correct: boolean;
    is_target_reached: boolean;
    accuracy_score: number;
    evaluation_note: string;
  };
}

interface AccuracyStats {
  total_predictions: number;
  evaluated_predictions: number;
  direction_correct_count: number;
  target_reached_count: number;
  direction_accuracy: number;
  target_accuracy: number;
  average_accuracy_score: number;
}

export default function HistoryClient({ code }: HistoryClientProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [stats, setStats] = useState<AccuracyStats | null>(null);
  const [stockName, setStockName] = useState('');

  useEffect(() => {
    loadData();
  }, [code]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 并行加载历史记录和准确率统计
      const [historyData, statsData] = await Promise.all([
        getAnalysisHistory(code, 'default_user', 30),
        getAccuracyStats(code, 'default_user').catch(() => null)
      ]);

      setHistory(historyData.history || []);
      setStats(statsData);

      // 从历史记录中获取股票名称（如果有的话）
      if (historyData.history && historyData.history.length > 0) {
        const content = historyData.history[0].analysis_content;
        if (content && content.name) {
          setStockName(content.name);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载历史数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <Link href="/" className="text-blue-500 text-sm mb-4 inline-block">
          ← 返回首页
        </Link>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">加载历史记录</h2>
          <p className="text-sm text-gray-500">股票代码: {code}</p>
          <div className="mt-4">
            <ProgressBar estimatedSeconds={5} color="blue" />
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <Link href="/" className="text-blue-500 text-sm mb-4 inline-block">
          ← 返回首页
        </Link>
        <div className="bg-white rounded-xl shadow-sm border border-red-100 p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">加载失败</h2>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600"
          >
            重试
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 返回按钮和标题 */}
      <div className="flex justify-between items-center mb-4">
        <Link href={`/stock/${code}`} className="text-blue-500 text-sm">
          ← 返回详情
        </Link>
        <Link href="/" className="text-blue-500 text-sm">
          首页
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-800 mb-2">
        {stockName || code} 历史分析
      </h1>
      <p className="text-sm text-gray-500 mb-6">
        查看过去30天的分析记录和预测准确率
      </p>

      {/* 准确率统计卡片 */}
      {stats && stats.evaluated_predictions > 0 && (
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 mb-6 border border-blue-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span>📊</span>
            预测准确率统计
          </h2>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-white rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-600">
                {stats.direction_accuracy.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">方向准确率</div>
              <div className="text-xs text-gray-400 mt-1">
                {stats.direction_correct_count}/{stats.evaluated_predictions}
              </div>
            </div>

            <div className="bg-white rounded-lg p-3">
              <div className="text-2xl font-bold text-purple-600">
                {stats.target_accuracy.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">目标达成率</div>
              <div className="text-xs text-gray-400 mt-1">
                {stats.target_reached_count}/{stats.evaluated_predictions}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">综合评分</span>
              <span className="text-lg font-semibold text-green-600">
                {stats.average_accuracy_score.toFixed(1)}
              </span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              已评估 {stats.evaluated_predictions} 次预测，共 {stats.total_predictions} 次分析
            </div>
          </div>
        </div>
      )}

      {/* 历史记录列表 */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <span>📅</span>
          历史记录
        </h2>

        {history.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="text-4xl mb-3">📝</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">暂无历史记录</h3>
            <p className="text-sm text-gray-500 mb-4">
              该股票还没有分析历史记录
            </p>
            <Link
              href={`/stock/${code}`}
              className="text-blue-500 text-sm hover:underline"
            >
              查看当前分析 →
            </Link>
          </div>
        ) : (
          history.map((record) => (
            <div
              key={record.id}
              className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 hover:shadow-md transition-shadow"
            >
              {/* 日期和价格 */}
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-sm font-semibold text-gray-800">
                    {record.analysis_date} {record.analysis_time}
                  </div>
                  <div className="text-xs text-gray-500">分析时间</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-800">
                    ¥{record.price.toFixed(2)}
                  </div>
                  <div className={`text-xs ${record.change_percent >= 0 ? 'text-red-500' : 'text-green-500'}`}>
                    {record.change_percent >= 0 ? '+' : ''}{record.change_percent.toFixed(2)}%
                  </div>
                </div>
              </div>

              {/* 预测信息 */}
              <div className="bg-blue-50 rounded-lg p-3 mb-3">
                <div className="text-sm font-medium text-gray-800 mb-1">
                  预测方向: <span className="text-blue-600">{record.prediction_direction}</span>
                </div>
                <div className="text-xs text-gray-600 mb-2">
                  {record.prediction_text}
                </div>
                <div className="text-xs text-gray-500">
                  目标价: ¥{record.target_price_low?.toFixed(2)} - ¥{record.target_price_high?.toFixed(2)}
                </div>
              </div>

              {/* 评估结果 */}
              {record.evaluation ? (
                <div className={`rounded-lg p-3 ${
                  record.evaluation.is_direction_correct
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-800">
                      评估结果 ({record.evaluation.evaluation_date})
                    </span>
                    <span className={`text-xs font-semibold ${
                      record.evaluation.is_direction_correct ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {record.evaluation.is_direction_correct ? '✓ 预测正确' : '✗ 预测错误'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500">实际价格: </span>
                      <span className="font-medium">¥{record.evaluation.actual_price.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">涨跌幅: </span>
                      <span className={`font-medium ${record.evaluation.price_change_percent >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {record.evaluation.price_change_percent >= 0 ? '+' : ''}{record.evaluation.price_change_percent.toFixed(2)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">目标达成: </span>
                      <span className="font-medium">
                        {record.evaluation.is_target_reached ? '是' : '否'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">准确度: </span>
                      <span className="font-medium">{record.evaluation.accuracy_score.toFixed(1)}</span>
                    </div>
                  </div>
                  {record.evaluation.evaluation_note && (
                    <div className="text-xs text-gray-600 mt-2 italic">
                      {record.evaluation.evaluation_note}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <span className="text-xs text-gray-500">
                    ⏳ 等待评估（5个交易日后）
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* 底部链接 */}
      <div className="mt-8 text-center">
        <Link
          href={`/stock/${code}`}
          className="text-blue-500 text-sm hover:underline"
        >
          查看当前分析 →
        </Link>
      </div>
    </main>
  );
}
