import StockDetailClient from '@/components/StockDetailClient';

// 强制动态渲染
export const dynamic = 'force-dynamic';

export default async function StockDetailPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  // Next.js 15+ 中 params 是 Promise，需要 await
  const { code } = await params;

  // 使用客户端组件加载数据，避免 Netlify 函数超时
  return <StockDetailClient code={code} />;
}
