"""
新闻数据获取服务
获取股票的最近新闻、公告等信息
全部使用 httpx 异步调用
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.http_client import get_client

REQUEST_TIMEOUT = 8
MAX_RETRIES = 2


async def get_recent_news(code: str, days: int = 7) -> List[Dict]:
    """
    获取最近N天的重要新闻（异步）

    Args:
        code: 股票代码
        days: 天数

    Returns:
        新闻列表
    """
    url = f"http://np-anotice-stock.eastmoney.com/api/security/ann?cb=&page_size=10&page_index=1&ann_type=A&client_source=web&sr=-1&stock_list={code}"

    news_list = []

    try:
        client = get_client()
        resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        if data.get('data') and data['data'].get('list'):
            for item in data['data']['list'][:10]:
                news_date = item.get('notice_date', '')[:10]

                if news_date:
                    news_time = datetime.strptime(news_date, '%Y-%m-%d')
                    if datetime.now() - news_time > timedelta(days=days):
                        continue

                title = item.get('title', '')

                news_type = "中性"
                if any(word in title for word in ['业绩预增', '分红', '中标', '合作', '增持', '利好']):
                    news_type = "利好"
                elif any(word in title for word in ['业绩下滑', '亏损', '减持', '风险', '处罚', '利空']):
                    news_type = "利空"

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


async def get_announcements(code: str, days: int = 30) -> List[Dict]:
    """
    获取重要公告（异步）

    Args:
        code: 股票代码
        days: 天数

    Returns:
        公告列表
    """
    news = await get_recent_news(code, days)

    announcements = [
        item for item in news
        if item['importance'] == '高' or any(
            word in item['title']
            for word in ['公告', '决议', '股东大会', '董事会']
        )
    ]

    return announcements
