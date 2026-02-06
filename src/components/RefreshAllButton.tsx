'use client';

import { useState } from 'react';
import { generateRecommendations } from '@/lib/api';
import ProgressBar from './ProgressBar';

export default function RefreshAllButton() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleRefresh = async () => {
    setLoading(true);
    setStatus('idle');
    setMessage('');

    try {
      // 生成推荐（包含AI基本面分析）
      const result = await generateRecommendations();

      if (!result.success) {
        setStatus('error');
        setMessage(result.message || '生成推荐失败');
        setLoading(false);
        return;
      }

      setStatus('success');
      setMessage(`成功刷新！生成 ${result.count || 5} 支智能推荐`);

      // 延迟刷新页面
      setTimeout(() => {
        window.location.reload();
      }, 1500);

    } catch (err) {
      setStatus('error');
      setMessage(err instanceof Error ? err.message : '网络错误，请检查后端服务');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={handleRefresh}
        disabled={loading}
        className={`
          flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
          transition-all duration-200
          ${loading
            ? 'bg-purple-100 text-purple-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600 shadow-sm'
          }
        `}
        title="一键刷新：推荐 + AI排名 + 市场数据"
      >
        <span className={`${loading ? 'animate-spin' : ''}`}>
          {loading ? '⟳' : '↻'}
        </span>
        <span>{loading ? '刷新中...' : '一键刷新'}</span>
      </button>

      {/* 加载中显示进度 */}
      {loading && (
        <div className="absolute top-full right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-100 p-4 z-20">
          <p className="text-sm text-gray-700 font-medium mb-3">
            正在分析股票并生成智能推荐...
          </p>
          <p className="text-xs text-gray-500 mb-3">
            包含技术面 + AI基本面分析
          </p>

          <ProgressBar
            estimatedSeconds={180}
            showPercent
            color="blue"
          />

          <p className="text-xs text-gray-400 mt-2 text-center">
            预计 2-3 分钟
          </p>
        </div>
      )}

      {/* 状态提示 */}
      {status !== 'idle' && !loading && (
        <div
          className={`
            absolute top-full right-0 mt-2 px-4 py-3 rounded-lg text-sm font-medium
            whitespace-nowrap shadow-lg z-20
            ${status === 'success'
              ? 'bg-green-100 text-green-700 border border-green-200'
              : 'bg-red-100 text-red-700 border border-red-200'
            }
          `}
        >
          {status === 'success' ? '✓' : '✗'} {message}
        </div>
      )}
    </div>
  );
}
