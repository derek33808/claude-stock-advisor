'use client';

import { useState, useEffect, useRef } from 'react';
import { askStockQuestion, getChatHistory, ChatResponse, ChatHistoryItem } from '@/lib/api';

interface StockChatPanelProps {
  code: string;
  stockName: string;
}

const QUICK_QUESTIONS = [
  { label: '财报分析', template: 'financial', icon: '📊' },
  { label: '近期资讯', template: 'news', icon: '📰' },
  { label: '同行对比', template: 'comparison', icon: '🏢' },
  { label: '技术解读', template: 'technical', icon: '📈' },
  { label: '风险提示', template: 'risk', icon: '⚠️' },
];

export default function StockChatPanel({ code, stockName }: StockChatPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<ChatHistoryItem[]>([]);
  const [remainingQuota, setRemainingQuota] = useState(10);
  const [latestAnswer, setLatestAnswer] = useState<ChatResponse | null>(null);
  const [showAllHistory, setShowAllHistory] = useState(false);
  const answerRef = useRef<HTMLDivElement>(null);

  // 加载历史记录（展开时或股票切换时）
  useEffect(() => {
    if (expanded) {
      loadHistory();
    }
  }, [expanded, code]);

  const loadHistory = async () => {
    try {
      const data = await getChatHistory(code);
      setHistory(data.history);
      setRemainingQuota(data.remaining_quota);
    } catch {
      // 静默处理
    }
  };

  const handleAsk = async (q: string, template?: string) => {
    if (loading) return;
    if (!q && !template) return;

    setLoading(true);
    setLatestAnswer(null);

    try {
      const result = await askStockQuestion(code, q, template);
      if (result.error) {
        setLatestAnswer(result);
      } else {
        setLatestAnswer(result);
        setRemainingQuota(result.remaining_quota ?? remainingQuota);
        // 刷新历史
        await loadHistory();
      }
      setQuestion('');
    } catch {
      setLatestAnswer({
        error: true,
        message: '网络错误，请稍后重试',
      });
    } finally {
      setLoading(false);
      // 滚动到答案
      setTimeout(() => {
        answerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 100);
    }
  };

  const handleQuickQuestion = (template: string) => {
    handleAsk('', template);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) {
      handleAsk(question.trim());
    }
  };

  const displayHistory = showAllHistory ? history : history.slice(0, 3);

  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-100 mb-4 overflow-hidden">
      {/* 标题栏（可折叠） */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex justify-between items-center p-4 hover:bg-gray-50 transition-colors"
      >
        <h2 className="text-lg font-semibold text-gray-800 flex items-center">
          <span className="mr-2">💬</span>
          AI 股票问答
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            今日剩余 {remainingQuota}/{10} 次
          </span>
          <span className={`transition-transform ${expanded ? 'rotate-180' : ''}`}>
            ▾
          </span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* 预设问题 */}
          <div>
            <p className="text-xs text-gray-500 mb-2">常见问题</p>
            <div className="flex flex-wrap gap-2">
              {QUICK_QUESTIONS.map((q) => (
                <button
                  key={q.template}
                  onClick={() => handleQuickQuestion(q.template)}
                  disabled={loading || remainingQuota <= 0}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <span>{q.icon}</span>
                  <span>{q.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* 自由提问 */}
          {remainingQuota > 0 ? (
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value.slice(0, 200))}
                placeholder={`问问关于${stockName}的问题...`}
                disabled={loading}
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-100"
                maxLength={200}
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="px-4 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
              >
                {loading ? '思考中...' : '发送'}
              </button>
            </form>
          ) : (
            <div className="text-center py-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">今日问答额度已用完（每日10次）</p>
              <p className="text-xs text-gray-400 mt-1">明天再来提问吧</p>
            </div>
          )}

          {/* 加载中 */}
          {loading && (
            <div className="flex items-center gap-2 py-3">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
              <span className="text-sm text-gray-500">AI 正在分析...</span>
            </div>
          )}

          {/* 最新回答 */}
          {latestAnswer && (
            <div ref={answerRef} className={`p-3 rounded-lg ${latestAnswer.error ? 'bg-red-50' : 'bg-blue-50'}`}>
              {latestAnswer.error ? (
                <p className="text-sm text-red-600">{latestAnswer.message}</p>
              ) : (
                <>
                  <p className="text-xs text-blue-500 font-medium mb-1">
                    Q: {latestAnswer.question}
                  </p>
                  <div className="text-sm text-gray-700 whitespace-pre-line leading-relaxed">
                    {latestAnswer.answer}
                  </div>
                  <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
                    <span>
                      {latestAnswer.cached ? '来自缓存' : `Token: ${latestAnswer.tokens_used}`}
                    </span>
                    <span>剩余 {latestAnswer.remaining_quota} 次</span>
                  </div>
                </>
              )}
            </div>
          )}

          {/* 历史记录 */}
          {history.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-gray-500 font-medium">历史问答</p>
              {displayHistory.map((item) => (
                <div key={item.id} className="border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-500 font-medium mb-1">
                    Q: {item.question}
                  </p>
                  <p className="text-sm text-gray-700 whitespace-pre-line leading-relaxed line-clamp-3">
                    {item.answer}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(item.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              ))}
              {history.length > 3 && !showAllHistory && (
                <button
                  onClick={() => setShowAllHistory(true)}
                  className="w-full text-center text-xs text-blue-500 hover:underline py-1"
                >
                  查看更多 ({history.length - 3} 条)
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
