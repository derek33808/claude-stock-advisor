"""
Token 使用监控服务
监控 GLM API Token 使用量，实现告警
"""

from datetime import date, datetime
from typing import Dict


class TokenMonitor:
    """Token 监控器"""

    DAILY_LIMIT = 500000  # 每日限额 500K tokens
    WARNING_THRESHOLD = 0.8  # 80%警告

    def __init__(self):
        self.today_usage = 0
        self.last_reset_date = date.today()
        self.usage_log = []

    def _check_daily_reset(self):
        """检查是否需要每日重置"""
        today = date.today()
        if today > self.last_reset_date:
            # 新的一天，重置计数
            self.today_usage = 0
            self.last_reset_date = today
            print(f"[TokenMonitor] Daily reset: {today}")

    async def log_usage(self, tokens_used: int, api_name: str = "GLM-4"):
        """
        记录 Token 使用

        Args:
            tokens_used: 使用的 token 数量
            api_name: API 名称
        """
        self._check_daily_reset()
        self.today_usage += tokens_used

        # 记录日志
        self.usage_log.append({
            'timestamp': datetime.now(),
            'api_name': api_name,
            'tokens': tokens_used,
            'total_today': self.today_usage
        })

        # 检查是否需要告警
        status = await self.check_limit()
        if status['warning']:
            print(f"⚠️ [TokenMonitor] WARNING: {status['percentage']*100:.1f}% used ({self.today_usage}/{self.DAILY_LIMIT})")

    async def check_limit(self) -> Dict:
        """
        检查是否接近限额

        Returns:
            {
                'used': 今日使用量,
                'limit': 每日限额,
                'percentage': 使用百分比,
                'warning': 是否警告,
                'blocked': 是否阻塞
            }
        """
        self._check_daily_reset()
        percentage = self.today_usage / self.DAILY_LIMIT

        return {
            'used': self.today_usage,
            'limit': self.DAILY_LIMIT,
            'percentage': round(percentage, 3),
            'warning': percentage >= self.WARNING_THRESHOLD,
            'blocked': percentage >= 1.0,
            'remaining': max(0, self.DAILY_LIMIT - self.today_usage)
        }

    def get_today_stats(self) -> Dict:
        """获取今日统计"""
        return {
            'date': str(self.last_reset_date),
            'total_usage': self.today_usage,
            'request_count': len(self.usage_log),
            'avg_per_request': self.today_usage / len(self.usage_log) if self.usage_log else 0
        }


# 全局实例
token_monitor = TokenMonitor()
