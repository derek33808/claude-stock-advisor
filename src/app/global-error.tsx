'use client';

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <main style={{ maxWidth: '32rem', margin: '0 auto', padding: '1.5rem 1rem', textAlign: 'center' }}>
          <div style={{ paddingTop: '3rem' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#1f2937', marginBottom: '0.5rem' }}>
              页面加载出错
            </h1>
            <p style={{ color: '#6b7280', marginBottom: '1rem' }}>
              服务可能正在启动中，请稍后重试
            </p>
            <button
              onClick={() => reset()}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '0.5rem',
                border: 'none',
                cursor: 'pointer',
                marginRight: '0.5rem',
              }}
            >
              重试
            </button>
            <a
              href="/"
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#e5e7eb',
                color: '#374151',
                borderRadius: '0.5rem',
                textDecoration: 'none',
                display: 'inline-block',
              }}
            >
              刷新页面
            </a>
          </div>
        </main>
      </body>
    </html>
  );
}
