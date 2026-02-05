'use client';

interface TabSwitcherProps {
  activeTab: 'recommendations' | 'watchlist';
  onTabChange: (tab: 'recommendations' | 'watchlist') => void;
  recommendationsCount: number;
  watchlistCount: number;
}

export default function TabSwitcher({
  activeTab,
  onTabChange,
  recommendationsCount,
  watchlistCount,
}: TabSwitcherProps) {
  return (
    <div className="flex bg-gray-100 rounded-lg p-1 mb-4">
      <button
        onClick={() => onTabChange('recommendations')}
        className={`
          flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all
          ${activeTab === 'recommendations'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-800'
          }
        `}
      >
        今日推荐 ({recommendationsCount})
      </button>
      <button
        onClick={() => onTabChange('watchlist')}
        className={`
          flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all
          ${activeTab === 'watchlist'
            ? 'bg-white text-yellow-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-800'
          }
        `}
      >
        我的自选 ({watchlistCount})
      </button>
    </div>
  );
}
