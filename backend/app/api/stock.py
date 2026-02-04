"""
股票查询 API
"""

from fastapi import APIRouter, HTTPException
from app.services import akshare_service, indicator_service, strategy_service
from app.models.schemas import StockAnalysis

router = APIRouter()


@router.get("/stock/{code}")
async def get_stock_analysis(code: str):
    """
    获取股票完整分析

    - code: 股票代码（如 600519, 000001, 512930）

    返回：基本信息、实时行情、技术指标、交易建议
    """
    # 获取历史数据
    df = akshare_service.get_history(code, days=60)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的数据，请检查代码是否正确"
        )

    # 获取实时行情
    realtime = akshare_service.get_realtime(code)
    if realtime is None:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的实时行情"
        )

    # 计算技术指标
    indicators = indicator_service.calculate_indicators(df)

    # 生成交易建议
    suggestion = indicator_service.calculate_trading_suggestion(df, indicators)

    # 生成推荐理由
    reasons = indicator_service.generate_reasons(indicators)

    # 计算综合评分
    score = indicator_service.calculate_score(indicators, suggestion)

    return {
        "code": code,
        "name": realtime["name"],
        "industry": realtime.get("industry", ""),
        "price": realtime["price"],
        "change": realtime["change"],
        "open": realtime["open"],
        "high": realtime["high"],
        "low": realtime["low"],
        "volume": realtime["volume"],
        "amount": realtime["amount"],
        "market_cap": realtime.get("market_cap", 0),
        "indicators": indicators,
        "suggestion": suggestion,
        "reasons": reasons,
        "score": score,
    }


@router.get("/stock/{code}/kline")
async def get_stock_kline(code: str, days: int = 60):
    """
    获取股票 K 线数据

    - code: 股票代码
    - days: 天数（默认 60）
    """
    df = akshare_service.get_history(code, days=days)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的 K 线数据"
        )

    # 转换为列表
    kline_data = []
    for _, row in df.iterrows():
        kline_data.append({
            "date": str(row["date"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]),
        })

    return {
        "code": code,
        "days": len(kline_data),
        "data": kline_data,
    }


@router.get("/stock/search")
async def search_stocks(q: str, limit: int = 20):
    """
    搜索股票

    - q: 搜索关键词（代码或名称）
    - limit: 返回数量限制（默认 20）
    """
    if not q or len(q) < 1:
        raise HTTPException(
            status_code=400,
            detail="请输入搜索关键词"
        )

    results = akshare_service.search_stocks(q, limit=limit)

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
