'use client';

import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { WatchlistItem } from './types';
import { getWatchlist, addWatchlistItem, removeWatchlistItem } from './api';

const STORAGE_KEY = 'stock-advisor-watchlist';

interface WatchlistContextType {
  watchlist: WatchlistItem[];
  addToWatchlist: (code: string, name: string) => void;
  removeFromWatchlist: (code: string) => void;
  isInWatchlist: (code: string) => boolean;
  toggleWatchlist: (code: string, name: string) => void;
  syncing: boolean;
}

const WatchlistContext = createContext<WatchlistContextType | undefined>(undefined);

/** localStorage 读取 */
function loadFromLocal(): WatchlistItem[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch { /* ignore */ }
  return [];
}

/** localStorage 写入 */
function saveToLocal(items: WatchlistItem[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch { /* ignore */ }
}

export function WatchlistProvider({ children }: { children: ReactNode }) {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const migratedRef = useRef(false);

  // 初始化：先显示 localStorage 缓存，然后从后端同步
  useEffect(() => {
    const localData = loadFromLocal();
    if (localData.length > 0) {
      setWatchlist(localData);
    }
    setIsLoaded(true);

    // 从后端加载（后端是权威数据源）
    (async () => {
      try {
        setSyncing(true);
        const resp = await getWatchlist();
        const backendItems: WatchlistItem[] = resp.watchlist.map((item) => ({
          code: item.code,
          name: item.name,
          addedAt: new Date(item.added_at).getTime(),
        }));

        // 如果后端有数据，以后端为准
        if (backendItems.length > 0) {
          setWatchlist(backendItems);
          saveToLocal(backendItems);

          // 把 localStorage 中有但后端没有的迁移到后端
          if (localData.length > 0 && !migratedRef.current) {
            migratedRef.current = true;
            const backendCodes = new Set(backendItems.map((i) => i.code));
            const toMigrate = localData.filter((i) => !backendCodes.has(i.code));
            for (const item of toMigrate) {
              try {
                await addWatchlistItem(item.code, item.name);
              } catch { /* best effort */ }
            }
            // 迁移完成后重新加载
            if (toMigrate.length > 0) {
              const fresh = await getWatchlist();
              const merged: WatchlistItem[] = fresh.watchlist.map((i) => ({
                code: i.code,
                name: i.name,
                addedAt: new Date(i.added_at).getTime(),
              }));
              setWatchlist(merged);
              saveToLocal(merged);
            }
          }
        } else if (localData.length > 0 && !migratedRef.current) {
          // 后端为空，把 localStorage 全部迁移到后端
          migratedRef.current = true;
          for (const item of localData) {
            try {
              await addWatchlistItem(item.code, item.name);
            } catch { /* best effort */ }
          }
        }
      } catch {
        // 后端不可用时，继续使用 localStorage 数据
        console.log('[Watchlist] Backend unavailable, using local cache');
      } finally {
        setSyncing(false);
      }
    })();
  }, []);

  // 数据变化时保存到 localStorage（作为缓存）
  useEffect(() => {
    if (isLoaded) {
      saveToLocal(watchlist);
    }
  }, [watchlist, isLoaded]);

  const addToWatchlist = (code: string, name: string) => {
    setWatchlist((prev) => {
      if (prev.some((item) => item.code === code)) return prev;
      return [...prev, { code, name, addedAt: Date.now() }];
    });
    // 异步同步到后端
    addWatchlistItem(code, name).catch(() => {
      console.log(`[Watchlist] Failed to sync add ${code} to backend`);
    });
  };

  const removeFromWatchlist = (code: string) => {
    setWatchlist((prev) => prev.filter((item) => item.code !== code));
    // 异步同步到后端
    removeWatchlistItem(code).catch(() => {
      console.log(`[Watchlist] Failed to sync remove ${code} from backend`);
    });
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
        syncing,
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
