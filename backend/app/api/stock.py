"""
股票查询 API
"""

from fastapi import APIRouter, HTTPException
from app.services import eastmoney_service, indicator_service, strategy_service
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
    df = eastmoney_service.get_history(code, days=60)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的数据，请检查代码是否正确"
        )

    # 获取实时行情
    realtime = eastmoney_service.get_realtime(code)
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
    reasons_raw = indicator_service.generate_reasons(indicators)

    # 计算综合评分
    score = indicator_service.calculate_score(indicators, suggestion)

    # 转换指标格式以匹配前端期望
    macd = indicators.get("macd", {})
    rsi = indicators.get("rsi", {})
    ma = indicators.get("ma", {})
    kdj = indicators.get("kdj", {})
    boll = indicators.get("boll", {})
    vol = indicators.get("volume", {})

    # 计算 BOLL 位置
    close_price = realtime["price"]
    boll_upper = boll.get("upper", 0)
    boll_lower = boll.get("lower", 0)
    boll_mid = boll.get("mid", 0)
    if boll_upper and boll_lower:
        if close_price >= boll_upper * 0.98:
            boll_position = "上轨附近"
        elif close_price <= boll_lower * 1.02:
            boll_position = "下轨附近"
        elif close_price > boll_mid:
            boll_position = "中轨上方"
        else:
            boll_position = "中轨下方"
    else:
        boll_position = "中性"

    formatted_indicators = {
        "macd": {
            "macd": macd.get("dif", 0),
            "signal": macd.get("dea", 0),
            "histogram": macd.get("hist", 0),
            "trend": macd.get("signal", "未知"),
        },
        "rsi": {
            "value": rsi.get("rsi6", 50),
            "level": rsi.get("status", "健康"),
        },
        "ma": {
            "ma5": ma.get("ma5", 0),
            "ma10": ma.get("ma10", 0),
            "ma20": ma.get("ma20", 0),
            "ma60": ma.get("ma60", 0),
            "alignment": ma.get("trend", "震荡"),
        },
        "kdj": {
            "k": kdj.get("k", 50),
            "d": kdj.get("d", 50),
            "j": kdj.get("j", 50),
        },
        "boll": {
            "upper": boll.get("upper", 0),
            "middle": boll.get("mid", 0),
            "lower": boll.get("lower", 0),
            "position": boll_position,
        },
        "atr": indicators.get("atr", 0),
        "volume_ratio": vol.get("ratio", 1),
    }

    # 转换建议格式
    formatted_suggestion = {
        "action": suggestion.get("action", "观望"),
        "buy_price": {
            "low": suggestion.get("buy_price_low", 0),
            "high": suggestion.get("buy_price_high", 0),
        },
        "stop_loss": suggestion.get("stop_loss", 0),
        "take_profit": {
            "target1": suggestion.get("take_profit_1", 0),
            "target2": suggestion.get("take_profit_2", 0),
        },
        "holding_days": suggestion.get("holding_days", "5-15个交易日"),
        "position_ratio": suggestion.get("position", "10-15%"),
        "risk_level": suggestion.get("risk_level", "中"),
    }

    # 合并推荐理由为数组
    reasons = []
    for reason in reasons_raw.get("technical", []):
        reasons.append(f"技术面: {reason}")
    for reason in reasons_raw.get("fundamental", []):
        reasons.append(f"基本面: {reason}")
    for reason in reasons_raw.get("capital", []):
        reasons.append(f"资金面: {reason}")
    if not reasons:
        reasons = ["数据正在分析中"]

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
        "indicators": formatted_indicators,
        "suggestion": formatted_suggestion,
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
    df = eastmoney_service.get_history(code, days=days)
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

    results = eastmoney_service.search_stocks(q, limit=limit)

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
