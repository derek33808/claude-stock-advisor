'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SearchBox() {
  const [code, setCode] = useState('');
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) {
      router.push(`/search?code=${code.trim()}`);
    }
  };

  return (
    <form onSubmit={handleSearch} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        查询股票
      </label>
      <div className="flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="输入股票代码，如 600519"
          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
        >
          查询
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-2">
        支持查询所有 A 股股票的推荐分析
      </p>
    </form>
  );
}
