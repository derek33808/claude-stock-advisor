"""
基本面数据获取服务
获取财报、PE/PB/ROE等基本面指标
"""

import urllib.request
import json
from typing import Dict, Optional

REQUEST_TIMEOUT = 15


def get_latest_financial_report(code: str) -> Optional[Dict]:
    """
    获取最新财报数据

    Returns:
        {
            'report_date': '2024-12-31',
            'report_type': '年报' | '季报',
            'revenue': 营业收入,
            'revenue_yoy': 同比增长率,
            'net_profit': 净利润,
            'profit_yoy': 同比增长率,
            'eps': 每股收益,
            'roe': ROE,
            'highlights': [...],  # 财报亮点
        }
    """
    try:
        # 东方财富财务数据API
        url = f"http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type=0&code={code}"

        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            content = response.read().decode('utf-8')

        data = json.loads(content)

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


def get_fundamental_data(code: str) -> Optional[Dict]:
    """
    获取基本面数据（PE、PB、ROE等）

    Returns:
        {
            'pe_ratio': PE市盈率,
            'pb_ratio': PB市净率,
            'roe': ROE净资产收益率,
            'revenue_growth': 营收增长率,
            'profit_margin': 利润率,
        }
    """
    try:
        # 使用财报数据计算基本面指标
        report = get_latest_financial_report(code)

        if not report:
            return None

        return {
            'pe_ratio': 0,  # 需要实时价格计算
            'pb_ratio': 0,  # 需要实时价格计算
            'roe': report.get('roe', 0),
            'revenue_growth': report.get('revenue_yoy', 0),
            'profit_margin': 0,  # 需要计算
        }

    except Exception as e:
        print(f"Error fetching fundamental data for {code}: {e}")

    return None


def _extract_highlights(data: dict) -> list:
    """
    从财报数据中提取亮点
    """
    highlights = []

    # 营收增长
    revenue_yoy = data.get('TOTAL_OPERATE_INCOME_YOY', 0)
    if revenue_yoy > 20:
        highlights.append(f"营收同比增长{revenue_yoy:.1f}%")

    # 净利润增长
    profit_yoy = data.get('PARENT_NETPROFIT_YOY', 0)
    if profit_yoy > 20:
        highlights.append(f"净利润同比增长{profit_yoy:.1f}%")

    # ROE
    roe = data.get('WEIGHTAVG_ROE', 0)
    if roe > 15:
        highlights.append(f"ROE达{roe:.1f}%")

    return highlights
