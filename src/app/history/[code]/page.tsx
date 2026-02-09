import HistoryClient from '@/components/HistoryClient';

// 强制动态渲染
export const dynamic = 'force-dynamic';

export default async function HistoryPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;

  return <HistoryClient code={code} />;
}
