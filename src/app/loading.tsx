export default function Loading() {
  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 页头骨架 */}
      <header className="mb-6 flex justify-between items-start">
        <div>
          <div className="h-8 w-40 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-32 bg-gray-200 rounded animate-pulse mt-1" />
        </div>
        <div className="h-9 w-24 bg-gray-200 rounded-lg animate-pulse" />
      </header>

      {/* 市场概览骨架 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4 animate-pulse">
        <div className="flex justify-between mb-3">
          <div className="h-4 w-24 bg-gray-200 rounded" />
          <div className="h-4 w-32 bg-gray-200 rounded" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="h-16 bg-gray-200 rounded" />
          <div className="h-16 bg-gray-200 rounded" />
        </div>
      </div>

      {/* 搜索框骨架 */}
      <div className="h-10 bg-gray-200 rounded-lg animate-pulse mb-4" />

      {/* Tab 切换骨架 */}
      <div className="flex gap-4 mb-4">
        <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
        <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
      </div>

      {/* 股票卡片骨架 */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4 animate-pulse">
          <div className="flex justify-between items-start mb-3">
            <div>
              <div className="h-5 w-24 bg-gray-200 rounded mb-1" />
              <div className="h-4 w-32 bg-gray-200 rounded" />
            </div>
            <div className="text-right">
              <div className="h-6 w-16 bg-gray-200 rounded mb-1" />
              <div className="h-4 w-12 bg-gray-200 rounded" />
            </div>
          </div>
          <div className="h-4 w-full bg-gray-200 rounded mb-2" />
          <div className="h-4 w-2/3 bg-gray-200 rounded" />
        </div>
      ))}
    </main>
  );
}
