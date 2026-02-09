"""
历史分析记录 API 端点
"""

from fastapi import APIRouter, HTTPException, Query
from app.services import analysis_history_service

router = APIRouter()


@router.get("/analysis/history/{code}")
async def get_analysis_history(
    code: str,
    user_id: str = Query(..., description="用户ID"),
    days: int = Query(30, description="查询天数")
):
    """
    获取股票历史分析记录

    Path:
        - code: 股票代码

    Query:
        - user_id: 用户ID
        - days: 查询天数（默认30天）

    Returns:
        历史分析记录列表（包含评估结果）
    """
    try:
        history = await analysis_history_service.get_stock_history(code, user_id, days)

        return {
            'code': code,
            'days': days,
            'count': len(history),
            'history': history
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/analysis/accuracy/{code}")
async def get_accuracy_stats(
    code: str,
    user_id: str = Query(..., description="用户ID")
):
    """
    获取预测准确率统计

    Path:
        - code: 股票代码

    Query:
        - user_id: 用户ID

    Returns:
        准确率统计
    """
    try:
        stats = await analysis_history_service.get_accuracy_stats(code, user_id)

        return {
            'code': code,
            **stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取准确率统计失败: {str(e)}")
