'use client';

import { useWatchlist } from '@/lib/watchlist-context';

interface WatchlistButtonProps {
  code: string;
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function WatchlistButton({
  code,
  name,
  size = 'md',
  className = '',
}: WatchlistButtonProps) {
  const { isInWatchlist, toggleWatchlist } = useWatchlist();
  const isWatched = isInWatchlist(code);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleWatchlist(code, name);
  };

  const sizeClasses = {
    sm: 'text-lg w-7 h-7',
    md: 'text-xl w-8 h-8',
    lg: 'text-2xl w-10 h-10',
  };

  return (
    <button
      onClick={handleClick}
      className={`
        flex items-center justify-center rounded-full
        transition-all duration-200
        ${isWatched
          ? 'text-yellow-500 hover:text-yellow-600 bg-yellow-100 hover:bg-yellow-200'
          : 'text-gray-400 hover:text-yellow-500 bg-gray-100 hover:bg-yellow-100 border border-gray-200'
        }
        ${sizeClasses[size]}
        ${className}
      `}
      title={isWatched ? '移除自选' : '添加自选'}
      aria-label={isWatched ? '移除自选' : '添加自选'}
    >
      {isWatched ? '★' : '☆'}
    </button>
  );
}
