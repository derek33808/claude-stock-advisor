"""
交易日历服务
判断是否为交易日，计算下一个交易日
"""

from datetime import date, timedelta
from typing import Set, Optional
import json
import os

class TradingCalendarService:
    """交易日历服务"""

    def __init__(self):
        self.trading_days: Set[date] = set()
        self.load_calendar()

    def load_calendar(self):
        """加载交易日历（静态备份）"""
        try:
            # 尝试从静态文件加载
            calendar_file = os.path.join(
                os.path.dirname(__file__),
                '../../../data/trading_calendar_static.json'
            )

            if os.path.exists(calendar_file):
                with open(calendar_file, 'r') as f:
                    dates = json.load(f)
                    self.trading_days = {
                        date.fromisoformat(d) for d in dates
                    }
                print(f"Loaded {len(self.trading_days)} trading days from static file")
            else:
                # 如果文件不存在，使用简单规则
                self._generate_simple_calendar()

        except Exception as e:
            print(f"Error loading trading calendar: {e}")
            self._generate_simple_calendar()

    def _generate_simple_calendar(self):
        """生成简单的交易日历（排除周末）"""
        # 生成近3年的工作日（排除周末）
        start_date = date.today() - timedelta(days=365*2)
        end_date = date.today() + timedelta(days=365)

        current = start_date
        while current <= end_date:
            # 排除周末
            if current.weekday() < 5:
                self.trading_days.add(current)
            current += timedelta(days=1)

        print(f"Generated {len(self.trading_days)} trading days (weekdays only)")

    def is_trading_day(self, day: date) -> bool:
        """判断是否为交易日"""
        return day in self.trading_days

    def next_trading_day(self, day: date) -> Optional[date]:
        """获取下一个交易日"""
        current = day + timedelta(days=1)
        max_tries = 10

        for _ in range(max_tries):
            if current in self.trading_days:
                return current
            current += timedelta(days=1)

        return None

    def add_trading_days(self, start: date, days: int) -> Optional[date]:
        """
        从起始日期加上N个交易日

        Args:
            start: 起始日期
            days: 交易日数量（可以是负数）

        Returns:
            目标日期
        """
        current = start
        remaining = abs(days)
        direction = 1 if days > 0 else -1

        while remaining > 0:
            current += timedelta(days=direction)
            if current in self.trading_days:
                remaining -= 1

        return current


# 全局实例
trading_calendar = TradingCalendarService()
