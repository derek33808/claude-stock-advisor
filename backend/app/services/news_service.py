"""
新闻数据获取服务
获取股票的最近新闻、公告等信息
"""

import urllib.request
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3


def get_recent_news(code: str, days: int = 7) -> List[Dict]:
    """
    获取最近N天的重要新闻

    Args:
        code: 股票代码
        days: 天数

    Returns:
        新闻列表，每条包含：
        - date: 日期
        - title: 标题
        - type: 类型 (利好/利空/中性)
        - importance: 重要性 (高/中/低)
        - summary: 摘要
    """
    # 东方财富新闻API
    url = f"http://np-anotice-stock.eastmoney.com/api/security/ann?cb=&page_size=10&page_index=1&ann_type=A&client_source=web&sr=-1&stock_list={code}"

    news_list = []

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            content = response.read().decode('utf-8')

        # 解析响应
        data = json.loads(content)

        if data.get('data') and data['data'].get('list'):
            for item in data['data']['list'][:10]:
                news_date = item.get('notice_date', '')[:10]

                # 只返回最近N天的新闻
                if news_date:
                    news_time = datetime.strptime(news_date, '%Y-%m-%d')
                    if datetime.now() - news_time > timedelta(days=days):
                        continue

                title = item.get('title', '')

                # 判断利好/利空
                news_type = "中性"
                if any(word in title for word in ['业绩预增', '分红', '中标', '合作', '增持', '利好']):
                    news_type = "利好"
                elif any(word in title for word in ['业绩下滑', '亏损', '减持', '风险', '处罚', '利空']):
                    news_type = "利空"

                # 判断重要性
                importance = "中"
                if any(word in title for word in ['重大', '重要', '年报', '半年报', '季报']):
                    importance = "高"

                news_list.append({
                    'date': news_date,
                    'title': title,
                    'type': news_type,
                    'importance': importance,
                    'summary': title[:100]
                })

    except Exception as e:
        print(f"Error fetching news for {code}: {e}")

    return news_list


def get_announcements(code: str, days: int = 30) -> List[Dict]:
    """
    获取重要公告

    Args:
        code: 股票代码
        days: 天数

    Returns:
        公告列表
    """
    # 复用新闻接口，过滤出公告类型
    news = get_recent_news(code, days)

    # 过滤出重要公告
    announcements = [
        item for item in news
        if item['importance'] == '高' or any(
            word in item['title']
            for word in ['公告', '决议', '股东大会', '董事会']
        )
    ]

    return announcements
