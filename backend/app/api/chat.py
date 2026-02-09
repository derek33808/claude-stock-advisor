"""
AI 股票问答 API
"""

from fastapi import APIRouter, Query
from app.services import chat_service

router = APIRouter()


@router.post("/stock/{code}/chat")
async def stock_chat(
    code: str,
    body: dict,
):
    """
    AI 股票问答

    - code: 股票代码
    - body.question: 用户问题
    - body.user_id: 用户ID (默认 default_user)
    - body.template: 预设模板 (financial/news/comparison/technical/risk)
    """
    question = body.get("question", "").strip()
    user_id = body.get("user_id", "default_user")
    template = body.get("template")

    if not question and not template:
        return {"error": True, "message": "请输入问题"}

    # 预设模板的默认问题
    template_questions = {
        "financial": "请分析这家公司的财报和基本面情况",
        "news": "请总结这家公司近期的重要新闻和公告",
        "comparison": "请将这只股票与同行业其他公司进行对比分析",
        "technical": "请解读当前的技术指标含义和趋势判断",
        "risk": "请分析当前持有这只股票的主要风险",
    }

    if template and not question:
        question = template_questions.get(template, question)

    # 限制问题长度
    if len(question) > 200:
        question = question[:200]

    result = await chat_service.ask_question(code, user_id, question, template)
    return result


@router.get("/stock/{code}/chat/history")
async def get_chat_history(
    code: str,
    user_id: str = Query(default="default_user"),
    limit: int = Query(default=20, le=50),
):
    """
    获取问答历史

    - code: 股票代码
    - user_id: 用户ID
    - limit: 返回数量
    """
    history = chat_service.get_chat_history(code, user_id, limit)
    remaining = chat_service.get_remaining_quota(user_id)

    return {
        "code": code,
        "count": len(history),
        "remaining_quota": remaining,
        "history": history,
    }
