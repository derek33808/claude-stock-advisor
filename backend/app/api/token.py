"""
Token 使用监控 API 端点
"""

from fastapi import APIRouter
from app.services.token_monitor_service import token_monitor

router = APIRouter()


@router.get("/token/usage/today")
async def get_token_usage():
    """
    获取今日 Token 使用情况

    Returns:
        {
            'used': 今日使用量,
            'limit': 每日限额,
            'percentage': 使用百分比,
            'warning': 是否警告,
            'blocked': 是否阻塞,
            'remaining': 剩余量
        }
    """
    status = await token_monitor.check_limit()
    return status


@router.get("/token/stats")
async def get_token_stats():
    """
    获取今日统计

    Returns:
        今日统计信息
    """
    stats = token_monitor.get_today_stats()
    return stats
