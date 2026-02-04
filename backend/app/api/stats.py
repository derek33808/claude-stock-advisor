"""
统计 API
"""

from fastapi import APIRouter
from app.db import supabase as db

router = APIRouter()


@router.get("/stats/performance")
async def get_performance_stats(days: int = 30):
    """
    获取策略表现统计

    - days: 统计周期（默认 30 天）

    返回：胜率、收益率、盈亏比等
    """
    stats = await db.get_performance_stats(days=days)

    return {
        "period_days": days,
        "total_recommendations": stats.get("total", 0),
        "win_count": stats.get("win_count", 0),
        "loss_count": stats.get("loss_count", 0),
        "holding_count": stats.get("holding_count", 0),
        "win_rate": stats.get("win_rate", 0),
        "avg_return": stats.get("avg_return", 0),
        "profit_loss_ratio": stats.get("profit_loss_ratio", 0),
    }


@router.get("/stats/tracking/{code}")
async def get_stock_tracking(code: str):
    """
    获取单只股票的跟踪记录

    - code: 股票代码
    """
    # TODO: 实现单只股票跟踪查询
    return {
        "code": code,
        "records": [],
        "message": "功能开发中"
    }
