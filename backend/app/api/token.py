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
            'date': 日期,
            'used': 今日使用量,
            'total_tokens': 总使用量（别名）,
            'limit': 每日限额,
            'percentage': 使用百分比,
            'total_cost_yuan': 预估成本（元）,
            'warning': 是否警告,
            'blocked': 是否阻塞,
            'remaining': 剩余量
        }
    """
    from datetime import datetime
    status = await token_monitor.check_limit()

    # 添加测试期望的字段
    status['date'] = datetime.now().strftime('%Y-%m-%d')
    status['total_tokens'] = status['used']  # 别名
    # 假设每1K tokens = ¥0.001（根据实际API定价调整）
    status['total_cost_yuan'] = round(status['used'] / 1000 * 0.001, 4)

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
