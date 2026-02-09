"""
综合分析 API 端点
"""

from fastapi import APIRouter, HTTPException
from app.services import (
    comprehensive_analysis_service,
    news_service,
    industry_service
)

router = APIRouter()


@router.get("/stock/{code}/comprehensive")
async def get_comprehensive_analysis(code: str):
    """
    获取股票完整5维综合分析

    - code: 股票代码

    Returns:
        完整的5维分析结果
    """
    try:
        result = await comprehensive_analysis_service.generate_comprehensive_analysis(code)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/stock/{code}/news")
async def get_stock_news(code: str, days: int = 7):
    """
    获取股票新闻

    - code: 股票代码
    - days: 天数（默认7天）

    Returns:
        新闻列表
    """
    try:
        news = news_service.get_recent_news(code, days)
        return {
            'code': code,
            'days': days,
            'count': len(news),
            'news': news
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@router.get("/industry/{name}/analysis")
async def get_industry_analysis(name: str):
    """
    获取行业分析

    - name: 行业名称

    Returns:
        行业分析数据
    """
    try:
        analysis = industry_service.get_industry_analysis(name)

        if not analysis:
            raise HTTPException(status_code=404, detail="行业数据未找到")

        return {
            'industry': name,
            **analysis
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行业分析失败: {str(e)}")
