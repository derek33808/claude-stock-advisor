export default function StockDetailLoading() {
  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 返回按钮 */}
      <div className="h-5 w-20 bg-gray-200 rounded animate-pulse mb-4"></div>

      {/* 股票基本信息骨架 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <div className="h-8 w-32 bg-gray-200 rounded animate-pulse mb-2"></div>
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
          </div>
          <div className="text-right">
            <div className="h-10 w-16 bg-gray-200 rounded animate-pulse mb-1"></div>
            <div className="h-3 w-12 bg-gray-200 rounded animate-pulse"></div>
          </div>
        </div>

        {/* 价格骨架 */}
        <div className="mt-4 p-3 rounded-lg bg-gray-100">
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse mb-2"></div>
          <div className="h-6 w-20 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </div>

      {/* 加载提示 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 mb-4">
        <div className="flex flex-col items-center justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-500 text-sm">正在加载股票数据...</p>
          <p className="text-gray-400 text-xs mt-1">首次加载可能需要较长时间</p>
        </div>
      </div>

      {/* 交易建议骨架 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="h-6 w-24 bg-gray-200 rounded animate-pulse mb-3"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex justify-between items-center py-2 border-b border-gray-100">
              <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-5 w-32 bg-gray-200 rounded animate-pulse"></div>
            </div>
          ))}
        </div>
      </div>

      {/* 推荐理由骨架 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="h-6 w-24 bg-gray-200 rounded animate-pulse mb-3"></div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-4 w-full bg-gray-200 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    </main>
  );
}
