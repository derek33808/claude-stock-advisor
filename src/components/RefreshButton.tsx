'use client';

import { useState } from 'react';
import { generateRecommendations } from '@/lib/api';
import ProgressBar from './ProgressBar';

interface RefreshButtonProps {
  onRefreshComplete?: () => void;
}

export default function RefreshButton({ onRefreshComplete }: RefreshButtonProps) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleRefresh = async () => {
    setLoading(true);
    setStatus('idle');
    setMessage('');

    try {
      const result = await generateRecommendations();
      if (result.success) {
        setStatus('success');
        setMessage(`成功生成 ${result.count || 5} 支推荐`);
        // 延迟刷新页面，让用户看到成功提示
        setTimeout(() => {
          onRefreshComplete?.();
          window.location.reload();
        }, 1500);
      } else {
        setStatus('error');
        setMessage(result.message || '生成失败，请重试');
      }
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
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-50 text-blue-600 hover:bg-blue-100 active:bg-blue-200'
          }
        `}
        title="重新生成今日推荐"
      >
        <span className={`${loading ? 'animate-spin' : ''}`}>
          {loading ? '⟳' : '↻'}
        </span>
        <span>{loading ? '分析中...' : '刷新推荐'}</span>
      </button>

      {/* 加载中显示进度条 */}
      {loading && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-100 p-4 z-20">
          <p className="text-xs text-gray-600 mb-2">正在分析60只股票...</p>
          <ProgressBar
            estimatedSeconds={180}
            showPercent
            color="blue"
          />
          <p className="text-xs text-gray-400 mt-2 text-center">
            预计需要 2-3 分钟
          </p>
        </div>
      )}

      {/* 状态提示 */}
      {status !== 'idle' && !loading && (
        <div
          className={`
            absolute top-full right-0 mt-2 px-3 py-2 rounded-lg text-xs font-medium
            whitespace-nowrap shadow-lg z-20
            ${status === 'success'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
            }
          `}
        >
          {status === 'success' ? '✓' : '✗'} {message}
        </div>
      )}
    </div>
  );
}
