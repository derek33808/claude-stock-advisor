"""
AI 股票问答服务
基于缓存的分析数据 + 多模型 提供单轮问答
支持智谱GLM、DeepSeek等多个模型
"""

import json
from datetime import datetime, timedelta
from typing import Optional
from app.db.supabase import get_supabase
from app.services.ai_analysis_service import _ai_model_status
from app.services.llm_service import call_llm

# 每日问答额度（测试阶段不限制）
DAILY_QUOTA = 9999

# 系统提示词
CHAT_SYSTEM_PROMPT = """你是一位专业的A股分析师助手。用户正在查看一只股票的详细分析页面，
你需要根据提供的股票信息和分析数据，回答用户关于这只股票的问题。

要求：
1. 回答要专业、客观、有数据支撑，结构清晰
2. 使用分点列出关键信息，必要时用小标题组织内容
3. 充分利用提供的所有数据（行业、技术面、基本面、交易参考等）进行综合分析
4. 不要编造不存在的数据，如果某些数据没有提供，请诚实说明
5. 末尾加上简短的风险提示
6. 禁止给出明确的买入/卖出建议，只提供分析参考"""


def build_chat_prompt(
    stock_context: dict,
    question: str,
    template: Optional[str] = None,
) -> str:
    """构建问答 Prompt"""
    base_context = f"""
## 股票信息
- 名称：{stock_context.get('name', '未知')}（{stock_context.get('code', '')}）
- 行业：{stock_context.get('industry', '未知')}
- 当前价格：¥{stock_context.get('price', 0)}
- 涨跌幅：{stock_context.get('change_percent', 0)}%
- 综合评分：{stock_context.get('score', 0)}/100
"""

    # 行情数据（所有模板通用）
    if stock_context.get('open_price') or stock_context.get('high_price'):
        base_context += f"""
## 今日行情
- 开盘价：¥{stock_context.get('open_price', 0)}
- 最高价：¥{stock_context.get('high_price', 0)}
- 最低价：¥{stock_context.get('low_price', 0)}
- 昨收价：¥{stock_context.get('prev_close', 0)}
- 成交量：{stock_context.get('volume', 0)}
- 成交额：{stock_context.get('amount', 0)}
- 总市值：{stock_context.get('market_cap', 0)}
"""

    suggestion = stock_context.get('suggestion', {})
    if suggestion:
        action = suggestion.get('action', '未知')
        base_context += f"- 操作建议：{action}\n"

    if template == "financial":
        # 真实财报数据
        report = stock_context.get('_financial_report')
        if report:
            base_context += f"""
## 最新财报数据（{report.get('report_type', '季报')} {report.get('report_date', '')[:7]}）
- 营业收入：{_format_amount(report.get('revenue', 0))}
- 营收同比增长：{report.get('revenue_yoy', 0):.1f}%
- 归母净利润：{_format_amount(report.get('net_profit', 0))}
- 净利润同比增长：{report.get('profit_yoy', 0):.1f}%
- 每股收益(EPS)：¥{report.get('eps', 0)}
- 加权ROE：{report.get('roe', 0):.2f}%
"""
            highlights = report.get('highlights', [])
            if highlights:
                base_context += "- 财报亮点：" + "；".join(highlights) + "\n"

        # AI 基本面分析（补充）
        fundamental = stock_context.get('ai_fundamental', {})
        if fundamental:
            base_context += f"""
## AI 基本面评估
- 估值水平：{fundamental.get('valuation_level', '未知')}
- 盈利能力：{fundamental.get('profitability', '未知')}
- 财务健康度：{fundamental.get('financial_health', '未知')}
- 投资价值评分：{fundamental.get('investment_value', '未知')}/10
"""

    elif template == "news":
        # 真实新闻和公告数据
        news_list = stock_context.get('_news', [])
        announcements = stock_context.get('_announcements', [])
        if news_list:
            news_text = "\n".join([
                f"- [{n.get('date', '')}] [{n.get('type', '中性')}] {n.get('title', '')}"
                for n in news_list[:8]
            ])
            base_context += f"""
## 近期新闻（最近7天）
{news_text}
"""
        if announcements:
            ann_text = "\n".join([
                f"- [{a.get('date', '')}] {a.get('title', '')}"
                for a in announcements[:5]
            ])
            base_context += f"""
## 重要公告（最近30天）
{ann_text}
"""
        if not news_list and not announcements:
            base_context += "\n## 近期动态\n暂无近期新闻和公告数据\n"

    elif template == "comparison":
        # 公司基本情况
        company = stock_context.get('ai_company', {})
        if company:
            base_context += f"""
## 公司概况
- 公司简介：{company.get('company_profile', '暂无')}
- 主营业务：{company.get('main_business', '暂无')}
- 竞争优势：{company.get('competitive_advantage', '暂无')}
- 行业地位：{company.get('industry_position', '未知')}
- 成长潜力：{company.get('growth_potential', '未知')}
"""

    elif template == "technical":
        indicators = stock_context.get('indicators', {})
        if indicators:
            macd = indicators.get('macd', {})
            rsi = indicators.get('rsi', {})
            ma = indicators.get('ma', {})
            boll = indicators.get('boll', {})
            kdj = indicators.get('kdj', {})
            base_context += f"""
## 技术指标
- MACD趋势：{macd.get('trend', '未知')}，信号：{macd.get('signal', '未知')}
- RSI状态：{rsi.get('level', '未知')}（RSI6={rsi.get('rsi6', '-')}，RSI12={rsi.get('rsi12', '-')}）
- 均线排列：{ma.get('alignment', '未知')}，趋势：{ma.get('trend', '未知')}
- BOLL位置：{boll.get('position', '未知')}
- KDJ：K={kdj.get('k', '-')} D={kdj.get('d', '-')} J={kdj.get('j', '-')}
- 量比：{indicators.get('volume_ratio', 1)}
"""

    elif template == "risk":
        suggestion = stock_context.get('suggestion', {})
        if suggestion:
            buy_price = suggestion.get('buy_price', {})
            take_profit = suggestion.get('take_profit', {})
            base_context += f"""
## 交易建议
- 建议买入区间：¥{buy_price.get('low', 0)} - ¥{buy_price.get('high', 0)}
- 止损价：¥{suggestion.get('stop_loss', 0)}
- 目标价1：¥{take_profit.get('target1', 0)}
- 目标价2：¥{take_profit.get('target2', 0)}
- 风险等级：{suggestion.get('risk_level', '未知')}
- 建议仓位：{suggestion.get('position_ratio', '未知')}
- 持有周期：{suggestion.get('holding_days', '未知')}
"""
        indicators = stock_context.get('indicators', {})
        if indicators:
            rsi = indicators.get('rsi', {})
            boll = indicators.get('boll', {})
            base_context += f"""
## 风险相关指标
- RSI状态：{rsi.get('level', '未知')}（值：{rsi.get('value', 50)}）
- BOLL位置：{boll.get('position', '未知')}
- 量比：{indicators.get('volume_ratio', 1)}
"""

    # 无特定模板时，自动补充所有可用数据，让 LLM 充分分析
    if not template:
        # 补充公司概况
        company = stock_context.get('ai_company', {})
        if company and company.get('main_business'):
            base_context += f"""
## 公司概况
- 主营业务：{company.get('main_business', '暂无')}
- 竞争优势：{company.get('competitive_advantage', '暂无')}
- 行业地位：{company.get('industry_position', '未知')}
- 成长潜力：{company.get('growth_potential', '未知')}
"""
        # 补充 AI 基本面分析
        fundamental = stock_context.get('ai_fundamental', {})
        if fundamental:
            base_context += f"""
## AI 基本面评估
- 估值水平：{fundamental.get('valuation_level', '未知')}
- 盈利能力：{fundamental.get('profitability', '未知')}
- 财务健康度：{fundamental.get('financial_health', '未知')}
- 投资价值评分：{fundamental.get('investment_value', '未知')}/10
"""
        # 补充技术指标
        indicators = stock_context.get('indicators', {})
        if indicators:
            macd = indicators.get('macd', {})
            rsi = indicators.get('rsi', {})
            ma = indicators.get('ma', {})
            boll = indicators.get('boll', {})
            kdj = indicators.get('kdj', {})
            base_context += f"""
## 技术面分析
- MACD趋势：{macd.get('trend', '未知')}，信号：{macd.get('signal', '未知')}
- RSI状态：{rsi.get('level', '未知')}（RSI6={rsi.get('rsi6', '-')}，RSI12={rsi.get('rsi12', '-')}）
- 均线排列：{ma.get('alignment', '未知')}，趋势：{ma.get('trend', '未知')}
- BOLL位置：{boll.get('position', '未知')}
- KDJ：K={kdj.get('k', '-')} D={kdj.get('d', '-')} J={kdj.get('j', '-')}
- 量比：{indicators.get('volume_ratio', 1)}
"""
        # 补充交易建议
        suggestion = stock_context.get('suggestion', {})
        if suggestion:
            buy_price = suggestion.get('buy_price', {})
            take_profit = suggestion.get('take_profit', {})
            base_context += f"""
## 交易参考
- 建议操作：{suggestion.get('action', '未知')}
- 买入区间：¥{buy_price.get('low', 0)} - ¥{buy_price.get('high', 0)}
- 止损价：¥{suggestion.get('stop_loss', 0)}
- 目标价：¥{take_profit.get('target1', 0)} / ¥{take_profit.get('target2', 0)}
- 风险等级：{suggestion.get('risk_level', '未知')}
"""

    reasons = stock_context.get('reasons', [])
    if reasons:
        reasons_text = "\n".join([f"- {r}" for r in reasons[:5]])
        base_context += f"""
## 分析理由
{reasons_text}
"""

    summary = stock_context.get('ai_summary', '')
    if summary:
        base_context += f"""
## AI 分析摘要
{summary[:300]}
"""

    return f"""{base_context}

## 用户问题
{question}

请根据以上信息回答用户问题。"""


def _format_amount(value) -> str:
    """格式化金额（元→亿/万）"""
    try:
        v = float(value)
        if abs(v) >= 1e8:
            return f"{v / 1e8:.2f}亿元"
        elif abs(v) >= 1e4:
            return f"{v / 1e4:.2f}万元"
        else:
            return f"{v:.2f}元"
    except (ValueError, TypeError):
        return str(value)


def get_remaining_quota(user_id: str) -> int:
    """获取用户今日剩余问答次数"""
    try:
        sb = get_supabase()
        today = datetime.now().strftime("%Y-%m-%d")
        result = sb.table('stock_chat_history') \
            .select('id', count='exact') \
            .eq('user_id', user_id) \
            .gte('created_at', f"{today}T00:00:00") \
            .execute()
        used = result.count if result.count is not None else len(result.data)
        return max(0, DAILY_QUOTA - used)
    except Exception as e:
        print(f"[Chat] Error checking quota: {e}")
        return DAILY_QUOTA


def find_similar_answer(code: str, question: str, template: Optional[str] = None) -> Optional[dict]:
    """查找2小时内相同股票的相似问题"""
    try:
        sb = get_supabase()
        cutoff = (datetime.now() - timedelta(hours=2)).isoformat()

        query = sb.table('stock_chat_history') \
            .select('question, answer, tokens_used, created_at') \
            .eq('code', code) \
            .gte('created_at', cutoff)

        if template:
            query = query.eq('template', template)

        result = query.order('created_at', desc=True).limit(5).execute()

        if not result.data:
            return None

        if template:
            return result.data[0]

        q_keywords = set(question)
        for item in result.data:
            existing_keywords = set(item['question'])
            overlap = len(q_keywords & existing_keywords) / max(len(q_keywords | existing_keywords), 1)
            if overlap > 0.7:
                return item

        return None

    except Exception as e:
        print(f"[Chat] Error finding similar answer: {e}")
        return None


async def call_chat_llm(system_prompt: str, user_prompt: str, model_id: Optional[str] = None) -> dict:
    """调用大模型进行问答（统一路由）"""
    content, error_type = await call_llm(
        system_prompt, user_prompt,
        model_id=model_id,
        max_tokens=1500,
    )

    if error_type:
        error_messages = {
            "auth_failed": "API 认证失败，请检查 API Key",
            "rate_limited": "请求过于频繁，请稍后重试",
            "quota_exhausted": "该模型额度已用尽，请切换到 GLM-4-Flash（免费）",
            "no_api_key": "该模型未配置 API Key",
            "timeout": "AI 响应超时，请稍后重试",
            "unavailable": "AI 服务暂时不可用，请稍后重试",
        }
        msg = error_messages.get(error_type, f"AI 错误: {error_type}")
        _ai_model_status.set_error(error_type, msg)
        return {"error": True, "message": msg}

    if content:
        _ai_model_status.clear_error()
        return {"answer": content, "tokens_used": 0}

    return {"error": True, "message": "AI 未返回结果，请重试"}


def save_chat_history(
    code: str,
    user_id: str,
    question: str,
    answer: str,
    template: Optional[str],
    tokens_used: int,
) -> Optional[str]:
    """保存问答记录到数据库"""
    try:
        sb = get_supabase()
        record = {
            "code": code,
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "template": template,
            "tokens_used": tokens_used,
            "created_at": datetime.now().isoformat(),
        }
        result = sb.table('stock_chat_history').insert(record).execute()
        if result.data:
            return result.data[0].get('id')
        return None
    except Exception as e:
        print(f"[Chat] Error saving chat history: {e}")
        return None


def get_chat_history(code: str, user_id: str, limit: int = 20) -> list:
    """获取问答历史"""
    try:
        sb = get_supabase()
        result = sb.table('stock_chat_history') \
            .select('id, question, answer, template, tokens_used, created_at') \
            .eq('code', code) \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        return result.data or []
    except Exception as e:
        print(f"[Chat] Error fetching chat history: {e}")
        return []


async def ask_question(
    code: str,
    user_id: str,
    question: str,
    template: Optional[str] = None,
    model_id: Optional[str] = None,
) -> dict:
    """
    处理用户问答请求（异步）
    """
    # 1. 检查额度
    remaining = get_remaining_quota(user_id)
    if remaining <= 0:
        return {
            "error": True,
            "message": "今日问答额度已用完（每日10次），明天再来吧",
            "remaining_quota": 0,
        }

    # 2. 查找相似问题
    similar = find_similar_answer(code, question, template)
    if similar:
        return {
            "code": code,
            "question": question,
            "answer": similar['answer'],
            "tokens_used": 0,
            "remaining_quota": remaining,
            "cached": True,
            "created_at": similar['created_at'],
        }

    # 3. 获取股票上下文（从缓存）
    from app.services.cache_service import get_cached_analysis
    stock_context = get_cached_analysis(code)
    if not stock_context:
        from app.services.eastmoney_service import get_realtime
        realtime = await get_realtime(code)
        stock_context = {
            "code": code,
            "name": realtime.get("name", code) if realtime else code,
            "industry": realtime.get("industry", "") if realtime else "",
            "price": realtime.get("price", 0) if realtime else 0,
            "change_percent": realtime.get("change", 0) if realtime else 0,
        }

    # 3.5 根据模板类型，实时获取补充数据
    if template == "news":
        from app.services import news_service
        try:
            import asyncio
            news_list, announcements = await asyncio.gather(
                news_service.get_recent_news(code, days=7),
                news_service.get_announcements(code, days=30),
            )
            stock_context['_news'] = news_list
            stock_context['_announcements'] = announcements
        except Exception as e:
            print(f"[Chat] Error fetching news for {code}: {e}")

    elif template == "financial":
        from app.services import fundamental_service
        try:
            report = await fundamental_service.get_latest_financial_report(code)
            if report:
                stock_context['_financial_report'] = report
        except Exception as e:
            print(f"[Chat] Error fetching financial report for {code}: {e}")

    # 4. 构建 prompt 并调用大模型
    user_prompt = build_chat_prompt(stock_context, question, template)
    result = await call_chat_llm(CHAT_SYSTEM_PROMPT, user_prompt, model_id=model_id)

    if result.get("error"):
        result["remaining_quota"] = remaining
        return result

    # 5. 保存记录
    save_chat_history(code, user_id, question, result["answer"], template, result["tokens_used"])

    return {
        "code": code,
        "question": question,
        "answer": result["answer"],
        "tokens_used": result["tokens_used"],
        "remaining_quota": remaining - 1,
        "cached": False,
        "created_at": datetime.now().isoformat(),
    }
