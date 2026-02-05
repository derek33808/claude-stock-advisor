'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { WatchlistItem } from './types';

const STORAGE_KEY = 'stock-advisor-watchlist';

interface WatchlistContextType {
  watchlist: WatchlistItem[];
  addToWatchlist: (code: string, name: string) => void;
  removeFromWatchlist: (code: string) => void;
  isInWatchlist: (code: string) => boolean;
  toggleWatchlist: (code: string, name: string) => void;
}

const WatchlistContext = createContext<WatchlistContextType | undefined>(undefined);

export function WatchlistProvider({ children }: { children: ReactNode }) {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  // 初始化时从 localStorage 读取
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setWatchlist(parsed);
        }
      }
    } catch {
      console.error('Failed to load watchlist from localStorage');
    }
    setIsLoaded(true);
  }, []);

  // 数据变化时保存到 localStorage
  useEffect(() => {
    if (isLoaded) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(watchlist));
      } catch {
        console.error('Failed to save watchlist to localStorage');
      }
    }
  }, [watchlist, isLoaded]);

  const addToWatchlist = (code: string, name: string) => {
    setWatchlist((prev) => {
      if (prev.some((item) => item.code === code)) {
        return prev;
      }
      return [...prev, { code, name, addedAt: Date.now() }];
    });
  };

  const removeFromWatchlist = (code: string) => {
    setWatchlist((prev) => prev.filter((item) => item.code !== code));
  };

  const isInWatchlist = (code: string) => {
    return watchlist.some((item) => item.code === code);
  };

  const toggleWatchlist = (code: string, name: string) => {
    if (isInWatchlist(code)) {
      removeFromWatchlist(code);
    } else {
      addToWatchlist(code, name);
    }
  };

  return (
    <WatchlistContext.Provider
      value={{
        watchlist,
        addToWatchlist,
        removeFromWatchlist,
        isInWatchlist,
        toggleWatchlist,
      }}
    >
      {children}
    </WatchlistContext.Provider>
  );
}

export function useWatchlist() {
  const context = useContext(WatchlistContext);
  if (context === undefined) {
    throw new Error('useWatchlist must be used within a WatchlistProvider');
  }
  return context;
}
