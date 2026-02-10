'use client';

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      <div className="text-center py-12">
        <div className="text-4xl mb-4">⚠️</div>
        <h1 className="text-xl font-bold text-gray-800 mb-2">页面加载出错</h1>
        <p className="text-gray-500 mb-4">后端服务可能正在启动中，请稍后重试</p>
        <button
          onClick={() => reset()}
          className="inline-block px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 mr-2"
        >
          重试
        </button>
        <a
          href="/"
          className="inline-block px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300"
        >
          刷新页面
        </a>
      </div>
    </main>
  );
}
