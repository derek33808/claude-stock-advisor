"""
AI 股票问答服务
基于缓存的分析数据 + GLM-4 提供单轮问答
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional
from app.db.supabase import get_supabase
from app.services.ai_analysis_service import _get_glm_api_key, _ai_model_status

# GLM 配置
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_MODEL = "glm-4-flash"
GLM_TIMEOUT = 30

# 每日问答额度
DAILY_QUOTA = 10

# 系统提示词
CHAT_SYSTEM_PROMPT = """你是一位专业的A股分析师助手。用户正在查看一只股票的详细分析页面，
你需要根据提供的股票信息和分析数据，回答用户关于这只股票的问题。

要求：
1. 回答要专业、客观、有数据支撑
2. 使用简洁明了的中文
3. 不要编造不存在的数据，如果某些数据没有提供，请诚实说明
4. 控制回答长度在200字以内
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

    suggestion = stock_context.get('suggestion', {})
    if suggestion:
        action = suggestion.get('action', '未知')
        base_context += f"- 操作建议：{action}\n"

    # 根据模板添加额外上下文
    if template == "financial":
        fundamental = stock_context.get('ai_fundamental', {})
        if fundamental:
            base_context += f"""
## 基本面数据
- 估值水平：{fundamental.get('valuation_level', '未知')}
- 盈利能力：{fundamental.get('profitability', '未知')}
- 投资价值评分：{fundamental.get('investment_value', '未知')}/10
"""

    elif template == "technical":
        indicators = stock_context.get('indicators', {})
        if indicators:
            macd = indicators.get('macd', {})
            rsi = indicators.get('rsi', {})
            ma = indicators.get('ma', {})
            boll = indicators.get('boll', {})
            base_context += f"""
## 技术指标
- MACD趋势：{macd.get('trend', '未知')}
- RSI状态：{rsi.get('level', '未知')}（值：{rsi.get('value', 50)}）
- 均线排列：{ma.get('alignment', '未知')}
- BOLL位置：{boll.get('position', '未知')}
- 量比：{indicators.get('volume_ratio', 1)}
"""

    elif template == "risk":
        suggestion = stock_context.get('suggestion', {})
        if suggestion:
            base_context += f"""
## 交易建议
- 止损价：¥{suggestion.get('stop_loss', 0)}
- 风险等级：{suggestion.get('risk_level', '未知')}
- 建议仓位：{suggestion.get('position_ratio', '未知')}
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
        return DAILY_QUOTA  # 出错时允许提问


def find_similar_answer(code: str, question: str, template: Optional[str] = None) -> Optional[dict]:
    """
    查找2小时内相同股票的相似问题
    - 相同模板直接命中
    - 自由提问用关键词匹配
    """
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

        # 模板匹配直接命中
        if template:
            return result.data[0]

        # 自由提问：关键词重叠率
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


def call_glm_chat(system_prompt: str, user_prompt: str) -> Optional[dict]:
    """调用 GLM-4 进行问答"""
    try:
        data = {
            "model": GLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 400,
        }

        req = urllib.request.Request(
            GLM_API_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {_get_glm_api_key()}",
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=GLM_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))

        if result.get("choices") and len(result["choices"]) > 0:
            content = result["choices"][0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            _ai_model_status.clear_error()
            return {"answer": content.strip(), "tokens_used": tokens_used}

        return None

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            pass
        print(f"[Chat] GLM API HTTP error {e.code}: {error_body}")

        if e.code == 429:
            if "quota" in error_body.lower():
                _ai_model_status.set_error("quota_exhausted", "API 配额已用尽")
            else:
                _ai_model_status.set_error("rate_limited", "请求过于频繁")
        return None

    except Exception as e:
        print(f"[Chat] GLM API error: {e}")
        return None


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
) -> dict:
    """
    处理用户问答请求
    1. 检查额度
    2. 查找相似问题缓存
    3. 获取股票上下文
    4. 调用 GLM-4
    5. 保存记录
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
        # 缓存中没有，用基础信息
        from app.services.eastmoney_service import get_realtime
        realtime = get_realtime(code)
        stock_context = {
            "code": code,
            "name": realtime.get("name", code) if realtime else code,
            "industry": realtime.get("industry", "") if realtime else "",
            "price": realtime.get("price", 0) if realtime else 0,
            "change_percent": realtime.get("change", 0) if realtime else 0,
        }

    # 4. 构建 prompt 并调用 GLM
    user_prompt = build_chat_prompt(stock_context, question, template)
    result = call_glm_chat(CHAT_SYSTEM_PROMPT, user_prompt)

    if not result:
        return {
            "error": True,
            "message": "AI 暂时无法回答，请稍后重试",
            "remaining_quota": remaining,
        }

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
