'use client';

import { useState, useEffect } from 'react';

interface ProgressBarProps {
  /** 预估总时间（秒） */
  estimatedSeconds?: number;
  /** 是否显示百分比 */
  showPercent?: boolean;
  /** 颜色主题 */
  color?: 'blue' | 'purple' | 'green';
}

/**
 * 基于时间的真实进度条
 * 使用渐进式算法，开始快后来慢，永远不会到100%（直到真正完成）
 */
export default function ProgressBar({
  estimatedSeconds = 15,
  showPercent = false,
  color = 'blue',
}: ProgressBarProps) {
  const [progress, setProgress] = useState(0);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;

      // 使用对数函数实现渐进式进度
      // 前期快，后期慢，最高到95%
      const targetProgress = Math.min(95, (1 - Math.exp(-elapsed / (estimatedSeconds * 0.5))) * 100);

      setProgress(targetProgress);
    }, 100);

    return () => clearInterval(interval);
  }, [startTime, estimatedSeconds]);

  const colorClasses = {
    blue: 'from-blue-400 to-blue-600',
    purple: 'from-purple-400 to-purple-600',
    green: 'from-green-400 to-green-600',
  };

  return (
    <div className="w-full">
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`bg-gradient-to-r ${colorClasses[color]} h-2 rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${progress}%` }}
        />
      </div>
      {showPercent && (
        <div className="text-xs text-gray-400 text-center mt-1">
          {Math.round(progress)}%
        </div>
      )}
    </div>
  );
}
