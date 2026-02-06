'use client';

import { useState } from 'react';
import { generateRecommendations, getAIRankings } from '@/lib/api';
import ProgressBar from './ProgressBar';

export default function RefreshAllButton() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [step, setStep] = useState<'recommendations' | 'ai' | 'done'>('recommendations');

  const handleRefresh = async () => {
    setLoading(true);
    setStatus('idle');
    setMessage('');
    setStep('recommendations');

    try {
      // 步骤1: 生成推荐
      setStep('recommendations');
      const result = await generateRecommendations();

      if (!result.success) {
        setStatus('error');
        setMessage(result.message || '生成推荐失败');
        setLoading(false);
        return;
      }

      // 步骤2: 刷新 AI 排名（强制刷新缓存）
      setStep('ai');
      try {
        await getAIRankings(10, true);
      } catch {
        // AI 排名失败不阻止整体刷新
        console.log('AI rankings refresh failed, but continuing...');
      }

      setStep('done');
      setStatus('success');
      setMessage(`成功刷新！生成 ${result.count || 5} 支推荐`);

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

  const getStepText = () => {
    switch (step) {
      case 'recommendations':
        return '正在分析股票生成推荐...';
      case 'ai':
        return '正在刷新 AI 排名...';
      case 'done':
        return '刷新完成！';
      default:
        return '准备中...';
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
          <div className="flex items-center gap-2 mb-2">
            <span className={`w-2 h-2 rounded-full ${step === 'recommendations' ? 'bg-blue-500 animate-pulse' : 'bg-green-500'}`}></span>
            <span className="text-xs text-gray-600">1. 生成推荐 (分析60只股票)</span>
          </div>
          <div className="flex items-center gap-2 mb-3">
            <span className={`w-2 h-2 rounded-full ${step === 'ai' ? 'bg-purple-500 animate-pulse' : step === 'done' ? 'bg-green-500' : 'bg-gray-300'}`}></span>
            <span className="text-xs text-gray-600">2. 刷新 AI 排名 (30只热门股)</span>
          </div>

          <p className="text-xs text-gray-700 font-medium mb-2">{getStepText()}</p>

          <ProgressBar
            estimatedSeconds={step === 'recommendations' ? 180 : 60}
            showPercent
            color={step === 'recommendations' ? 'blue' : 'purple'}
          />

          <p className="text-xs text-gray-400 mt-2 text-center">
            {step === 'recommendations' ? '预计 2-3 分钟' : '预计 30-60 秒'}
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
