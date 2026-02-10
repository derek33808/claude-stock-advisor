"""
基本面数据获取服务
获取财报、PE/PB/ROE等基本面指标
全部使用 httpx 异步调用
"""

from typing import Dict, Optional

from app.http_client import get_client

REQUEST_TIMEOUT = 8


async def get_latest_financial_report(code: str) -> Optional[Dict]:
    """
    获取最新财报数据（异步）

    Returns:
        财报数据字典
    """
    try:
        url = f"http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type=0&code={code}"

        client = get_client()
        resp = await client.get(url, timeout=REQUEST_TIMEOUT)
        data = resp.json()

        if data and isinstance(data, list) and len(data) > 0:
            latest = data[0]

            report_date = latest.get('REPORT_DATE', '')[:10]
            report_type = '年报' if '12-31' in report_date else '季报'

            return {
                'report_date': report_date,
                'report_type': report_type,
                'revenue': latest.get('TOTAL_OPERATE_INCOME', 0),
                'revenue_yoy': latest.get('TOTAL_OPERATE_INCOME_YOY', 0),
                'net_profit': latest.get('PARENT_NETPROFIT', 0),
                'profit_yoy': latest.get('PARENT_NETPROFIT_YOY', 0),
                'eps': latest.get('BASIC_EPS', 0),
                'roe': latest.get('WEIGHTAVG_ROE', 0),
                'highlights': _extract_highlights(latest)
            }

    except Exception as e:
        print(f"Error fetching financial report for {code}: {e}")

    return None


async def get_fundamental_data(code: str) -> Optional[Dict]:
    """
    获取基本面数据（PE、PB、ROE等）（异步）
    """
    try:
        report = await get_latest_financial_report(code)

        if not report:
            return None

        return {
            'pe_ratio': 0,
            'pb_ratio': 0,
            'roe': report.get('roe', 0),
            'revenue_growth': report.get('revenue_yoy', 0),
            'profit_margin': 0,
        }

    except Exception as e:
        print(f"Error fetching fundamental data for {code}: {e}")

    return None


def _extract_highlights(data: dict) -> list:
    """从财报数据中提取亮点"""
    highlights = []

    revenue_yoy = data.get('TOTAL_OPERATE_INCOME_YOY', 0)
    if revenue_yoy > 20:
        highlights.append(f"营收同比增长{revenue_yoy:.1f}%")

    profit_yoy = data.get('PARENT_NETPROFIT_YOY', 0)
    if profit_yoy > 20:
        highlights.append(f"净利润同比增长{profit_yoy:.1f}%")

    roe = data.get('WEIGHTAVG_ROE', 0)
    if roe > 15:
        highlights.append(f"ROE达{roe:.1f}%")

    return highlights
