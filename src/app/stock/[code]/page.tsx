import Link from 'next/link';
import { RecommendationData, StockRecommendation, AIAnalysis } from '@/lib/types';
import Disclaimer from '@/components/Disclaimer';
import { headers } from 'next/headers';

// 强制动态渲染，不使用静态生成
export const dynamic = 'force-dynamic';

// 后端 API 基础 URL
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1';

async function getRecommendations(): Promise<RecommendationData | null> {
  try {
    // 从请求头获取主机名，构建完整 URL
    const headersList = await headers();
    const host = headersList.get('host') || 'localhost:3000';
    const protocol = host.includes('localhost') ? 'http' : 'https';
    const baseUrl = `${protocol}://${host}`;

    const res = await fetch(`${baseUrl}/data/recommendations.json`, {
      cache: 'no-store',
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// 从后端 API 获取股票分析（包含 AI 分析）
async function getStockFromAPI(code: string, includeAI: boolean = true): Promise<StockRecommendation | null> {
  try {
    const url = includeAI
      ? `${API_BASE_URL}/stock/${code}?ai_analysis=true`
      : `${API_BASE_URL}/stock/${code}`;

    const res = await fetch(url, {
      cache: 'no-store',
    });
    if (!res.ok) return null;

    const analysis = await res.json();

    // 将 API 返回格式转换为 StockRecommendation 格式
    const result: StockRecommendation = {
      code: analysis.code,
      name: analysis.name,
      industry: analysis.industry || '未知',
      price: analysis.price,
      change: analysis.change,
      score: analysis.score,
      buyPriceLow: analysis.suggestion.buy_price.low,
      buyPriceHigh: analysis.suggestion.buy_price.high,
      stopLoss: analysis.suggestion.stop_loss,
      takeProfit1: analysis.suggestion.take_profit.target1,
      takeProfit2: analysis.suggestion.take_profit.target2,
      holdingDays: analysis.suggestion.holding_days,
      positionRatio: analysis.suggestion.position_ratio,
      reasons: {
        technical: analysis.reasons.filter((r: string) => r.includes('技术') || r.includes('MACD') || r.includes('RSI') || r.includes('均线')),
        fundamental: analysis.reasons.filter((r: string) => r.includes('基本') || r.includes('业绩') || r.includes('估值')),
        capital: analysis.reasons.filter((r: string) => r.includes('资金') || r.includes('成交') || r.includes('量')),
      },
      riskLevel: analysis.suggestion.risk_level as 'low' | 'medium' | 'high',
      summary: analysis.summary,
    };

    // 添加 AI 分析数据
    if (analysis.ai_analysis) {
      result.aiAnalysis = analysis.ai_analysis;
      result.aiRankingScore = analysis.ai_ranking_score;
    }

    return result;
  } catch {
    return null;
  }
}

export default async function StockDetailPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  // Next.js 15+ 中 params 是 Promise，需要 await
  const { code } = await params;

  // 优先从后端 API 获取（包含 AI 生成的交易指导摘要）
  let stock = (await getStockFromAPI(code)) ?? undefined;

  // 如果 API 失败，从本地 JSON 获取
  if (!stock) {
    const data = await getRecommendations();
    stock = data?.recommendations.find((s) => s.code === code);
    if (!stock && data?.allStocks) {
      stock = data.allStocks.find((s) => s.code === code);
    }
  }

  if (!stock) {
    return (
      <main className="max-w-lg mx-auto px-4 py-6">
        <Link href="/" className="text-blue-500 text-sm">← 返回首页</Link>
        <div className="text-center py-12">
          <h1 className="text-xl font-bold text-gray-800">股票未找到</h1>
          <p className="text-sm text-gray-500 mt-2">请检查股票代码是否正确</p>
        </div>
      </main>
    );
  }

  const isUp = stock.change >= 0;

  return (
    <main className="max-w-lg mx-auto px-4 py-6">
      {/* 返回按钮 */}
      <Link href="/" className="inline-flex items-center text-blue-500 text-sm mb-4">
        ← 返回首页
      </Link>

      {/* 股票基本信息 */}
      <header className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{stock.name}</h1>
            <p className="text-sm text-gray-500">{stock.code} · {stock.industry}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-600">{stock.score}</div>
            <div className="text-xs text-gray-400">综合评分</div>
          </div>
        </div>

        {/* 价格信息 */}
        <div className={`mt-4 p-3 rounded-lg ${isUp ? 'bg-up' : 'bg-down'}`}>
          <div className={`text-3xl font-bold ${isUp ? 'text-up' : 'text-down'}`}>
            ¥{stock.price.toFixed(2)}
          </div>
          <div className={`text-lg ${isUp ? 'text-up' : 'text-down'}`}>
            {isUp ? '+' : ''}{stock.change.toFixed(2)}%
          </div>
        </div>
      </header>

      {/* 交易建议 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">交易建议</h2>

        <div className="space-y-3">
          <TradingItem
            label="建议买入价"
            value={`¥${stock.buyPriceLow.toFixed(2)} - ¥${stock.buyPriceHigh.toFixed(2)}`}
            hint="等待回调至此区间买入"
          />
          <TradingItem
            label="止损价"
            value={`¥${stock.stopLoss.toFixed(2)}`}
            hint={`跌破即止损 (${(((stock.stopLoss - stock.buyPriceLow) / stock.buyPriceLow) * 100).toFixed(1)}%)`}
            danger
          />
          <TradingItem
            label="止盈目标1"
            value={`¥${stock.takeProfit1.toFixed(2)}`}
            hint={`盈利 ${(((stock.takeProfit1 - stock.buyPriceLow) / stock.buyPriceLow) * 100).toFixed(1)}% 可减仓`}
            success
          />
          <TradingItem
            label="止盈目标2"
            value={`¥${stock.takeProfit2.toFixed(2)}`}
            hint={`盈利 ${(((stock.takeProfit2 - stock.buyPriceLow) / stock.buyPriceLow) * 100).toFixed(1)}% 可清仓`}
            success
          />
          <TradingItem
            label="建议仓位"
            value={stock.positionRatio}
            hint="单只股票投入比例"
          />
          <TradingItem
            label="持有周期"
            value={stock.holdingDays}
            hint="建议持有时间"
          />
        </div>
      </section>

      {/* 推荐理由 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">推荐理由</h2>

        {stock.reasons.technical.length > 0 && (
          <ReasonBlock title="技术面" items={stock.reasons.technical} />
        )}
        {stock.reasons.fundamental.length > 0 && (
          <ReasonBlock title="基本面" items={stock.reasons.fundamental} />
        )}
        {stock.reasons.capital.length > 0 && (
          <ReasonBlock title="资金面" items={stock.reasons.capital} />
        )}
      </section>

      {/* 风险等级 */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">风险评估</h2>
        <div className={`text-center p-4 rounded-lg ${
          stock.riskLevel === 'low' ? 'bg-green-50' :
          stock.riskLevel === 'medium' ? 'bg-yellow-50' :
          'bg-red-50'
        }`}>
          <div className={`text-2xl font-bold ${
            stock.riskLevel === 'low' ? 'text-green-600' :
            stock.riskLevel === 'medium' ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {stock.riskLevel === 'low' ? '低风险' :
             stock.riskLevel === 'medium' ? '中风险' : '高风险'}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {stock.riskLevel === 'low' ? '波动较小，适合稳健型投资者' :
             stock.riskLevel === 'medium' ? '波动适中，注意控制仓位' :
             '波动较大，建议小仓位参与'}
          </p>
        </div>
      </section>

      {/* AI 智能分析 */}
      {stock.aiAnalysis && (
        <>
          {/* AI 评分卡片 */}
          <section className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-sm border border-purple-100 p-4 mb-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
              <span className="mr-2">🤖</span>
              AI 智能评分
            </h2>
            <div className="flex items-center justify-between mb-4">
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-600">
                  {stock.aiAnalysis.ai_recommendation.ai_score}
                </div>
                <div className="text-xs text-gray-500">AI 评分</div>
              </div>
              <div className="text-center">
                <div className={`text-xl font-bold ${
                  stock.aiAnalysis.ai_recommendation.ai_rating === '强烈推荐' ? 'text-green-600' :
                  stock.aiAnalysis.ai_recommendation.ai_rating === '推荐' ? 'text-blue-600' :
                  stock.aiAnalysis.ai_recommendation.ai_rating === '中性' ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {stock.aiAnalysis.ai_recommendation.ai_rating}
                </div>
                <div className="text-xs text-gray-500">推荐等级</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-gray-700">
                  {stock.aiAnalysis.ai_recommendation.confidence}
                </div>
                <div className="text-xs text-gray-500">置信度</div>
              </div>
            </div>

            {/* 核心观点 */}
            <div className="bg-white rounded-lg p-3 mb-3">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">💡 核心观点</h3>
              <ul className="space-y-1">
                {stock.aiAnalysis.ai_recommendation.key_points.map((point, i) => (
                  <li key={i} className="text-sm text-gray-600 flex items-start">
                    <span className="text-purple-500 mr-2">•</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>

            {/* AI 总结 */}
            <div className="bg-white rounded-lg p-3">
              <p className="text-sm text-gray-700 leading-relaxed">
                {stock.aiAnalysis.ai_recommendation.ai_summary}
              </p>
            </div>
          </section>

          {/* 公司分析 */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
              <span className="mr-2">🏢</span>
              公司分析
            </h2>

            <div className="space-y-3">
              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-sm font-semibold text-gray-700 mb-1">公司简介</h3>
                <p className="text-sm text-gray-600">{stock.aiAnalysis.company.company_profile}</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-sm font-semibold text-gray-700 mb-1">主营业务</h3>
                <p className="text-sm text-gray-600">{stock.aiAnalysis.company.main_business}</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-3">
                <h3 className="text-sm font-semibold text-gray-700 mb-1">核心竞争优势</h3>
                <p className="text-sm text-gray-600">{stock.aiAnalysis.company.competitive_advantage}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-blue-600">
                    {stock.aiAnalysis.company.industry_position}
                  </div>
                  <div className="text-xs text-gray-500">行业地位</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="text-lg font-bold text-green-600">
                    {stock.aiAnalysis.company.growth_potential}
                  </div>
                  <div className="text-xs text-gray-500">成长潜力</div>
                </div>
              </div>

              {stock.aiAnalysis.company.risk_factors.length > 0 && (
                <div className="bg-red-50 rounded-lg p-3">
                  <h3 className="text-sm font-semibold text-red-700 mb-1">⚠️ 风险因素</h3>
                  <ul className="space-y-1">
                    {stock.aiAnalysis.company.risk_factors.map((risk, i) => (
                      <li key={i} className="text-sm text-red-600">• {risk}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>

          {/* 基本面分析 */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
              <span className="mr-2">📊</span>
              基本面分析
            </h2>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className={`rounded-lg p-3 text-center ${
                stock.aiAnalysis.fundamental.valuation_level === '低估' ? 'bg-green-50' :
                stock.aiAnalysis.fundamental.valuation_level === '高估' ? 'bg-red-50' :
                'bg-yellow-50'
              }`}>
                <div className={`text-lg font-bold ${
                  stock.aiAnalysis.fundamental.valuation_level === '低估' ? 'text-green-600' :
                  stock.aiAnalysis.fundamental.valuation_level === '高估' ? 'text-red-600' :
                  'text-yellow-600'
                }`}>
                  {stock.aiAnalysis.fundamental.valuation_level}
                </div>
                <div className="text-xs text-gray-500">估值水平</div>
              </div>

              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-blue-600">
                  {stock.aiAnalysis.fundamental.profitability}
                </div>
                <div className="text-xs text-gray-500">盈利能力</div>
              </div>

              <div className="bg-purple-50 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-purple-600">
                  {stock.aiAnalysis.fundamental.financial_health}
                </div>
                <div className="text-xs text-gray-500">财务健康</div>
              </div>

              <div className="bg-orange-50 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-orange-600">
                  {stock.aiAnalysis.fundamental.investment_value}/10
                </div>
                <div className="text-xs text-gray-500">投资价值</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-600">{stock.aiAnalysis.fundamental.analysis_summary}</p>
            </div>

            <div className="text-xs text-gray-400 text-right mt-2">
              分析时间: {stock.aiAnalysis.analysis_time}
            </div>
          </section>
        </>
      )}

      {/* 交易指导摘要 */}
      {stock.summary && (
        <section className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-sm border border-blue-100 p-4 mb-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
            <span className="mr-2">📝</span>
            交易指导
          </h2>
          <div className="bg-white rounded-lg p-4 text-sm text-gray-700 whitespace-pre-line leading-relaxed">
            {stock.summary}
          </div>
        </section>
      )}

      {/* 风险提示 */}
      <Disclaimer />
    </main>
  );
}

// 交易建议项组件
function TradingItem({
  label,
  value,
  hint,
  danger,
  success,
}: {
  label: string;
  value: string;
  hint?: string;
  danger?: boolean;
  success?: boolean;
}) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
      <div>
        <div className="text-sm text-gray-600">{label}</div>
        {hint && <div className="text-xs text-gray-400">{hint}</div>}
      </div>
      <div className={`text-lg font-semibold ${
        danger ? 'text-red-500' :
        success ? 'text-green-500' :
        'text-gray-800'
      }`}>
        {value}
      </div>
    </div>
  );
}

// 推荐理由块组件
function ReasonBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mb-4 last:mb-0">
      <h3 className="text-sm font-semibold text-gray-700 mb-2">{title}</h3>
      <ul className="space-y-1">
        {items.map((item, index) => (
          <li key={index} className="text-sm text-gray-600 flex items-start">
            <span className="text-blue-500 mr-2">•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
