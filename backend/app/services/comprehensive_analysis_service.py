"""
综合分析服务（5维分析orchestrator）
整合技术面、基本面、新闻、财报、行业分析，生成完整的综合分析
全部使用异步调用
"""

import asyncio
from typing import Dict, Optional
from app.services import (
    eastmoney_service,
    indicator_service,
    news_service,
    fundamental_service,
    industry_service
)


async def generate_comprehensive_analysis(code: str) -> Dict:
    """
    生成完整的5维综合分析
    """
    # 步骤1: 并行获取基础数据
    quote, history = await asyncio.gather(
        eastmoney_service.get_realtime(code),
        eastmoney_service.get_history(code, days=60),
    )

    if not quote:
        raise ValueError(f"无法获取股票 {code} 的数据")

    if history is None or history.empty:
        raise ValueError(f"无法获取股票 {code} 的历史数据")

    # 步骤2: 并行获取5个维度的数据
    technical_task = asyncio.create_task(_get_technical_analysis(history, quote))
    company_task = asyncio.create_task(_get_company_analysis(code, quote))
    fundamental_task = asyncio.create_task(_get_fundamental_analysis(code))
    news_task = asyncio.create_task(_get_recent_developments(code))
    industry_task = asyncio.create_task(_get_industry_analysis(quote.get('industry', '')))

    # 等待所有任务完成
    technical, company, fundamental, news, industry = await asyncio.gather(
        technical_task,
        company_task,
        fundamental_task,
        news_task,
        industry_task
    )

    # 步骤3: 生成 AI 综合分析
    ai_summary = await _generate_ai_summary(
        code, quote, technical, company, fundamental, news, industry
    )

    # 步骤4: 返回完整分析
    return {
        'code': code,
        'name': quote['name'],
        'quote': quote,
        # 5维分析数据（简化字段名）
        'technical': technical,
        'fundamental': fundamental,
        'news_events': news,
        'industry': industry,
        'ai_synthesis': ai_summary.get('summary', {}),
        # 详细数据（保留完整字段名以兼容）
        'technical_analysis': technical,
        'company_analysis': company,
        'fundamental_analysis': fundamental,
        'recent_developments': news,
        'industry_analysis': industry,
        'comprehensive_summary': ai_summary.get('summary', {}),
        'trading_suggestion': ai_summary.get('trading_suggestion', {}),
        'analysis_time': ai_summary.get('analysis_time', '')
    }


async def _get_technical_analysis(history, quote) -> Dict:
    """技术面分析"""
    indicators = indicator_service.calculate_indicators(history)
    suggestion = indicator_service.calculate_trading_suggestion(history, indicators)
    score = indicator_service.calculate_score(indicators, suggestion)

    return {
        'indicators': indicators,
        'signals': {
            'macd': indicators.get('macd', {}).get('signal', '未知'),
            'rsi': indicators.get('rsi', {}).get('status', '健康'),
            'ma_trend': indicators.get('ma', {}).get('trend', '震荡')
        },
        'score': score,
        'prediction': suggestion.get('action', '观望'),
        'ai_comment': ''
    }


async def _get_company_analysis(code: str, quote: Dict) -> Dict:
    """公司分析"""
    return {
        'industry': quote.get('industry', ''),
        'market_cap': quote.get('market_cap', 0),
        'business_overview': '暂无数据',
        'competitive_advantage': [],
        'ai_comment': ''
    }


async def _get_fundamental_analysis(code: str) -> Dict:
    """基本面分析（异步）"""
    report = await fundamental_service.get_latest_financial_report(code)

    if report:
        return {
            'pe_ratio': 0,
            'pb_ratio': 0,
            'roe': report.get('roe', 0),
            'revenue_growth': report.get('revenue_yoy', 0),
            'profit_margin': 0,
            'latest_report': report,
            'ai_comment': ''
        }

    return {
        'pe_ratio': 0,
        'pb_ratio': 0,
        'roe': 0,
        'revenue_growth': 0,
        'profit_margin': 0,
        'latest_report': None,
        'ai_comment': '暂无财报数据'
    }


async def _get_recent_developments(code: str) -> Dict:
    """近期动态（异步）"""
    news_list = await news_service.get_recent_news(code, days=7)
    announcements = await news_service.get_announcements(code, days=30)

    # 计算情绪
    positive_count = len([n for n in news_list if n['type'] == '利好'])
    negative_count = len([n for n in news_list if n['type'] == '利空'])

    if positive_count > negative_count:
        sentiment = 'positive'
    elif negative_count > positive_count:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    return {
        'news': news_list[:5],
        'announcements': announcements[:3],
        'sentiment': sentiment,
        'ai_impact': ''
    }


async def _get_industry_analysis(industry_name: str) -> Dict:
    """行业分析"""
    if not industry_name:
        return {
            'index_change': 0,
            'trend': '震荡',
            'peer_comparison': [],
            'fund_flow': {},
            'ai_comment': '暂无行业数据'
        }

    industry_data = industry_service.get_industry_analysis(industry_name)

    if industry_data:
        return {
            'index_change': industry_data.get('index_change', 0),
            'trend': industry_data.get('trend', '震荡'),
            'peer_comparison': industry_data.get('leading_stocks', []),
            'fund_flow': industry_data.get('fund_flow', {}),
            'ai_comment': ''
        }

    return {
        'index_change': 0,
        'trend': '震荡',
        'peer_comparison': [],
        'fund_flow': {},
        'ai_comment': '暂无行业数据'
    }


async def _generate_ai_summary(
    code: str,
    quote: Dict,
    technical: Dict,
    company: Dict,
    fundamental: Dict,
    news: Dict,
    industry: Dict
) -> Dict:
    """生成综合分析摘要（基于规则的分析）"""
    return {
        'summary': {
            'investment_thesis': f"{quote['name']} 技术评分{technical['score']}分，{technical['prediction']}",
            'top_positives': _extract_positives(technical, fundamental, news),
            'top_risks': _extract_risks(technical, fundamental, news),
            'action': technical['prediction'],
            'risk_level': _calculate_risk_level(technical, fundamental)
        },
        'trading_suggestion': _generate_trading_suggestion(quote, technical),
        'analysis_time': '刚刚'
    }


def _extract_positives(technical: Dict, fundamental: Dict, news: Dict) -> list:
    """提取利好因素"""
    positives = []

    if technical['score'] >= 70:
        positives.append(f"技术面强势（评分{technical['score']}）")
    if technical['signals']['ma_trend'] == '多头':
        positives.append("均线多头排列")
    if fundamental.get('revenue_growth', 0) > 20:
        positives.append(f"营收高增长（{fundamental['revenue_growth']:.1f}%）")
    if fundamental.get('roe', 0) > 15:
        positives.append(f"ROE优秀（{fundamental['roe']:.1f}%）")
    if news['sentiment'] == 'positive':
        positives.append("近期新闻利好")

    return positives[:3] if positives else ["技术指标正常"]


def _extract_risks(technical: Dict, fundamental: Dict, news: Dict) -> list:
    """提取风险因素"""
    risks = []

    if technical['score'] < 40:
        risks.append(f"技术面偏弱（评分{technical['score']}）")
    if technical['signals']['rsi'] == '超买':
        risks.append("RSI超买，注意回调")
    if news['sentiment'] == 'negative':
        risks.append("近期负面新闻较多")
    if fundamental.get('revenue_growth', 0) < 0:
        risks.append("营收同比下降")

    risks.append("市场系统性风险")

    return risks[:3]


def _calculate_risk_level(technical: Dict, fundamental: Dict) -> str:
    """计算风险等级"""
    score = technical['score']

    if score >= 70:
        return '中'
    elif score >= 50:
        return '中'
    else:
        return '高'


def _generate_trading_suggestion(quote: Dict, technical: Dict) -> Dict:
    """生成交易建议"""
    price = quote['price']
    score = technical['score']

    if score >= 70:
        return {
            'buy_price_low': round(price * 0.98, 2),
            'buy_price_high': round(price * 1.02, 2),
            'stop_loss': round(price * 0.93, 2),
            'take_profit_1': round(price * 1.08, 2),
            'take_profit_2': round(price * 1.15, 2),
            'position_size': '15-20%',
            'holding_period': '10-20个交易日'
        }
    elif score >= 50:
        return {
            'buy_price_low': round(price * 0.95, 2),
            'buy_price_high': round(price, 2),
            'stop_loss': round(price * 0.92, 2),
            'take_profit_1': round(price * 1.05, 2),
            'take_profit_2': round(price * 1.10, 2),
            'position_size': '10-15%',
            'holding_period': '5-15个交易日'
        }
    else:
        return {
            'buy_price_low': round(price * 0.92, 2),
            'buy_price_high': round(price * 0.95, 2),
            'stop_loss': round(price * 0.90, 2),
            'take_profit_1': round(price * 1.03, 2),
            'take_profit_2': round(price * 1.05, 2),
            'position_size': '5-10%',
            'holding_period': '3-10个交易日'
        }
