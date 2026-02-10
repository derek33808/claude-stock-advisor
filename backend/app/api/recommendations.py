"""
推荐 API
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.services import eastmoney_service, strategy_service
from app.services import cache_service
from app.db import supabase as db

router = APIRouter()


@router.get("/recommendations")
async def get_today_recommendations():
    """
    获取今日推荐

    返回：市场概览 + 推荐股票列表（价格为实时数据）
    """
    # 获取市场概览（带 fallback）
    market = await eastmoney_service.get_market_indices_with_fallback()

    # 获取最新推荐
    date, recommendations = await db.get_latest_recommendations()

    if not recommendations:
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "update_time": datetime.now().strftime("%H:%M"),
            "market": market,
            "recommendations": [],
            "message": "暂无推荐数据，请等待每日更新"
        }

    # 批量获取实时价格（单次HTTP请求，替代逐个串行）
    codes = [rec["code"] for rec in recommendations]
    batch_quotes = await eastmoney_service.get_batch_realtime(codes)
    for rec in recommendations:
        quote = batch_quotes.get(rec["code"])
        if quote:
            rec["price"] = quote["price"]
            rec["change"] = quote["change"]
    # 回填内存缓存
    cache_service.set_cached_quotes_batch(batch_quotes)

    return {
        "date": date,
        "update_time": datetime.now().strftime("%H:%M"),
        "market": market,
        "recommendations": recommendations,
    }


@router.get("/recommendations/{date}")
async def get_recommendations_by_date(date: str):
    """
    获取指定日期的推荐

    - date: 日期（格式 YYYY-MM-DD）
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式错误，请使用 YYYY-MM-DD 格式"
        )

    recommendations = await db.get_recommendations(date)

    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 {date} 的推荐数据"
        )

    # 获取当天的市场数据
    market = await db.get_market_overview(date)
    if market is None:
        market = {
            "sh_index": 0,
            "sh_change": 0,
            "sz_index": 0,
            "sz_change": 0,
            "sentiment": "未知"
        }

    return {
        "date": date,
        "market": market,
        "recommendations": recommendations,
    }


@router.get("/recommendations/history")
async def get_recommendations_history(
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    limit: int = 10
):
    """
    获取历史推荐列表

    - start_date: 开始日期
    - end_date: 结束日期
    - page: 页码
    - limit: 每页数量
    """
    # TODO: 实现分页查询
    # 目前返回最近的推荐
    date, recommendations = await db.get_latest_recommendations()

    return {
        "page": page,
        "limit": limit,
        "total": len(recommendations),
        "data": [{
            "date": date,
            "count": len(recommendations),
            "recommendations": recommendations
        }]
    }


@router.post("/recommendations/generate")
async def generate_recommendations():
    """
    手动触发生成推荐

    注意：这个操作可能需要几分钟
    """
    try:
        # 生成推荐
        recommendations = await strategy_service.generate_daily_recommendations(top_n=10)

        if not recommendations:
            return {
                "success": False,
                "message": "未能生成推荐，请稍后重试"
            }

        # 保存到数据库
        today = datetime.now().strftime("%Y-%m-%d")
        await db.save_recommendations(today, recommendations)

        # 保存市场概览（带 fallback）
        market = await eastmoney_service.get_market_indices_with_fallback()
        await db.save_market_overview(today, market)

        return {
            "success": True,
            "date": today,
            "count": len(recommendations),
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成推荐失败: {str(e)}"
        )


@router.get("/market/overview")
async def get_market_overview():
    """
    获取市场概览（大盘指数）
    自动 fallback 到新浪财经
    """
    market = await eastmoney_service.get_market_indices_with_fallback()
    return market
