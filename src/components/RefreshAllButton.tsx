'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_BASE_URL } from '@/lib/api';
import ProgressBar from './ProgressBar';

export default function RefreshAllButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [currentTask, setCurrentTask] = useState('');

  const handleRefresh = async () => {
    setLoading(true);
    setStatus('idle');
    setMessage('');
    setProgress(0);
    setCurrentTask('准备刷新...');

    // 全局超时控制（5分钟）
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 300000);

    try {
      // 使用 SSE 调用全局刷新 API
      const response = await fetch(`${API_BASE_URL}/refresh/all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'default_user',
          include_recommendations: true,  // 生成推荐
          include_watchlist: true,        // 刷新自选股
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error('刷新请求失败');
      }

      // 处理 SSE 流
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('无法读取响应');
      }

      let recommendationsCount = 0;
      let stocksCount = 0;
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留未完成的行

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            let data;
            try {
              data = JSON.parse(line.slice(6));
            } catch {
              continue; // 跳过无法解析的行
            }

            if (data.event === 'progress') {
              setProgress(data.progress || 0);
              setCurrentTask(data.current || '处理中...');

              // 记录推荐数量
              if (data.phase === 'recommendations_done') {
                const match = data.current.match(/(\d+)支/);
                if (match) recommendationsCount = parseInt(match[1]);
              }
            } else if (data.event === 'complete') {
              setProgress(100);
              stocksCount = data.stocks_refreshed || 0;
              setStatus('success');
              setMessage(
                `刷新完成！生成 ${recommendationsCount} 支推荐${stocksCount > 0 ? `，刷新 ${stocksCount} 只自选股` : ''}`
              );

              // 延迟后使用 router.refresh 代替 window.location.reload
              setTimeout(() => {
                router.refresh();
              }, 1500);
              return;
            } else if (data.event === 'error') {
              throw new Error(data.message || '刷新失败');
            }
          }
        }
      }

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setStatus('error');
        setMessage('刷新超时（超过5分钟），请稍后重试');
      } else {
        setStatus('error');
        setMessage(err instanceof Error ? err.message : '网络错误，请检查后端服务');
      }
    } finally {
      clearTimeout(timeout);
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
        title="全局刷新：推荐 + 自选股 + 市场数据"
      >
        <span className={`${loading ? 'animate-spin' : ''}`}>
          {loading ? '⟳' : '↻'}
        </span>
        <span>{loading ? '刷新中...' : '一键刷新'}</span>
      </button>

      {/* 加载中显示进度 */}
      {loading && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-100 p-4 z-20">
          <p className="text-sm text-gray-700 font-medium mb-2">
            全局刷新进行中...
          </p>
          <p className="text-xs text-gray-500 mb-3">
            {currentTask}
          </p>

          {/* 实时进度条 */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 text-right mb-3">
            {progress}%
          </p>

          <p className="text-xs text-gray-400 text-center">
            正在刷新推荐和自选股，请稍候...
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
