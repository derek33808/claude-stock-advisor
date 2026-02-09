"""
股票查询 API
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from app.services import eastmoney_service, indicator_service, strategy_service
from app.services.glm_service import generate_summary_with_fallback
from app.services.ai_analysis_service import get_full_ai_analysis, calculate_ai_ranking_score, get_ai_model_status
from app.services import cache_service
from app.models.schemas import StockAnalysis

router = APIRouter()

# AI 排名缓存（内存缓存，有效期 30 分钟）
_ai_rankings_cache = {
    "data": None,
    "updated_at": None,
    "cache_duration": timedelta(minutes=30)
}

# 单股票分析缓存（内存缓存，有效期 3 分钟 - 盘中数据变化快）
_stock_analysis_cache: dict = {}
_stock_cache_duration = timedelta(minutes=3)


# 搜索路由使用 /stocks/search (复数) 避免与 /stock/{code} 冲突
@router.get("/stocks/search")
async def search_stocks(q: str = Query(..., min_length=1, description="搜索关键词"), limit: int = 20):
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


@router.get("/stock/{code}")
async def get_stock_analysis(
    code: str,
    ai_analysis: bool = Query(default=True, description="是否包含 AI 智能分析（默认开启）"),
    refresh: bool = Query(default=False, description="强制刷新缓存")
):
    """
    获取股票完整分析（三层缓存优先）

    - code: 股票代码（如 600519, 000001, 512930）
    - ai_analysis: 是否包含 AI 智能分析
    - refresh: 强制刷新缓存（跳过所有缓存，重新分析）

    缓存策略：L1 内存(30秒) -> L2 Supabase(4小时) -> L3 数据源(实时)
    """
    global _stock_analysis_cache

    # ===== 非刷新模式：尝试从缓存读取 =====
    if not refresh:
        # L1: 内存缓存 (3分钟)
        cache_key = f"{code}_{ai_analysis}"
        if cache_key in _stock_analysis_cache:
            cached = _stock_analysis_cache[cache_key]
            if datetime.now() - cached["updated_at"] < _stock_cache_duration:
                response = cached["data"].copy()
                response["cached"] = True
                response["cache_time"] = cached["updated_at"].strftime("%H:%M:%S")
                response["cache_info"] = {
                    "cached": True,
                    "level": "L1",
                    "analysis_updated_at": cached["updated_at"].isoformat(),
                    "quote_fresh": True,
                }
                return response

        # L2: Supabase 持久缓存 (4小时)
        db_cached = cache_service.get_cached_analysis(code)
        if db_cached:
            # 获取实时价格（内存缓存30秒）
            realtime = cache_service.get_cached_quote(code)
            if not realtime:
                realtime = eastmoney_service.get_realtime(code)
                if realtime:
                    cache_service.set_cached_quote(code, realtime)

            response = cache_service.build_response_from_cache(db_cached, realtime)

            # 回填 L1 内存缓存
            _stock_analysis_cache[cache_key] = {
                "data": response,
                "updated_at": datetime.now()
            }

            return response

    # ===== L3: 完整分析（缓存未命中或强制刷新） =====
    return await _do_full_analysis(code, ai_analysis)


async def _do_full_analysis(code: str, ai_analysis: bool = True) -> dict:
    """执行完整的股票分析流程并写入所有缓存层"""
    global _stock_analysis_cache

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
    suggestion = indicator_service.calculate_trading_suggestion(df, indicators)
    reasons_raw = indicator_service.generate_reasons(indicators)
    score = indicator_service.calculate_score(indicators, suggestion)

    # 转换指标格式
    macd = indicators.get("macd", {})
    rsi = indicators.get("rsi", {})
    ma = indicators.get("ma", {})
    kdj = indicators.get("kdj", {})
    boll = indicators.get("boll", {})
    vol = indicators.get("volume", {})

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

    reasons = []
    for reason in reasons_raw.get("technical", []):
        reasons.append(f"技术面: {reason}")
    for reason in reasons_raw.get("fundamental", []):
        reasons.append(f"基本面: {reason}")
    for reason in reasons_raw.get("capital", []):
        reasons.append(f"资金面: {reason}")
    if not reasons:
        reasons = ["数据正在分析中"]

    summary = generate_summary_with_fallback(
        name=realtime["name"],
        code=code,
        price=realtime["price"],
        change=realtime["change"],
        score=score,
        suggestion=formatted_suggestion,
        indicators=formatted_indicators,
        reasons=reasons,
    )

    response = {
        "code": code,
        "name": realtime["name"],
        "industry": realtime.get("industry", ""),
        "price": realtime["price"],
        "change": realtime["change"],
        "open": realtime["open"],
        "high": realtime["high"],
        "low": realtime["low"],
        "prev_close": realtime.get("prev_close", 0),
        "volume": realtime["volume"],
        "amount": realtime["amount"],
        "market_cap": realtime.get("market_cap", 0),
        "indicators": formatted_indicators,
        "suggestion": formatted_suggestion,
        "reasons": reasons,
        "score": score,
        "summary": summary,
    }

    if ai_analysis:
        ai_result = get_full_ai_analysis(
            name=realtime["name"],
            code=code,
            industry=realtime.get("industry", "未知"),
            price=realtime["price"],
            change=realtime["change"],
            market_cap=realtime.get("market_cap", 0),
            score=score,
            indicators=indicators,
            suggestion=suggestion,
        )
        response["ai_analysis"] = ai_result

        ai_ranking_score = calculate_ai_ranking_score(
            technical_score=score,
            ai_score=ai_result.get("ai_recommendation", {}).get("ai_score", score),
            change=realtime["change"],
            volume_status=vol.get("status", "正常"),
            ma_trend=ma.get("trend", "震荡"),
        )
        response["ai_ranking_score"] = ai_ranking_score

    # ===== 写入所有缓存层 =====

    # L1: 内存缓存
    cache_key = f"{code}_{ai_analysis}"
    _stock_analysis_cache[cache_key] = {
        "data": response,
        "updated_at": datetime.now()
    }

    # L1: 实时价格内存缓存
    cache_service.set_cached_quote(code, realtime)

    # L2: Supabase 持久缓存
    cache_service.save_analysis_cache(code, response)

    response["cached"] = False
    response["cache_info"] = {
        "cached": False,
        "level": "L3",
        "analysis_updated_at": datetime.now().isoformat(),
        "quote_fresh": True,
    }
    return response


@router.get("/stocks/batch")
async def get_batch_stock_analyses(
    codes: str = Query(..., description="逗号分隔的股票代码列表"),
):
    """
    批量获取股票分析（缓存优先 + 实时价格）
    用于自选股列表快速加载

    - codes: 逗号分隔的股票代码（如 600519,000858,300750）
    - 最多 20 只
    """
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {"count": 0, "stocks": []}

    code_list = code_list[:20]

    # 1. 批量获取 Supabase 缓存
    cached_analyses = cache_service.get_cached_analyses_batch(code_list)

    # 2. 批量获取实时价格（单次 HTTP）
    batch_quotes = eastmoney_service.get_batch_realtime(code_list)
    cache_service.set_cached_quotes_batch(batch_quotes)

    results = []
    uncached_codes = []

    for code in code_list:
        cached = cached_analyses.get(code)
        if cached:
            realtime = batch_quotes.get(code)
            response = cache_service.build_response_from_cache(cached, realtime)
            results.append(response)
        else:
            uncached_codes.append(code)

    # 3. 未缓存的股票执行完整分析
    for code in uncached_codes:
        try:
            analysis = await _do_full_analysis(code, ai_analysis=False)
            results.append(analysis)
        except Exception:
            quote = batch_quotes.get(code)
            if quote:
                results.append({
                    "code": code,
                    "name": quote.get("name", code),
                    "industry": "",
                    "price": quote.get("price", 0),
                    "change": quote.get("change", 0),
                    "score": 0,
                    "indicators": {},
                    "suggestion": {
                        "action": "数据加载中",
                        "buy_price": {"low": 0, "high": 0},
                        "stop_loss": 0,
                        "take_profit": {"target1": 0, "target2": 0},
                        "holding_days": "-",
                        "position_ratio": "-",
                        "risk_level": "medium",
                    },
                    "reasons": ["数据正在加载中"],
                })

    return {
        "count": len(results),
        "stocks": results,
    }


@router.post("/stocks/prefetch")
async def prefetch_stocks(codes: list[str]):
    """
    批量预加载股票数据（后台缓存）

    - codes: 股票代码列表

    预加载后，后续访问单股票 API 会直接返回缓存数据
    """
    results = {"success": [], "failed": []}

    for code in codes[:20]:  # 限制最多 20 只
        try:
            # 调用单股票分析（会自动缓存）
            await get_stock_analysis(code, ai_analysis=False, refresh=False)
            results["success"].append(code)
        except Exception as e:
            results["failed"].append({"code": code, "error": str(e)})

    return {
        "total": len(codes),
        "cached": len(results["success"]),
        "failed": len(results["failed"]),
        "details": results
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


@router.get("/stock/{code}/ai-analysis")
async def get_stock_ai_analysis(code: str):
    """
    获取股票 AI 智能分析（独立接口，更详细的分析）

    - code: 股票代码

    返回：公司分析、基本面分析、AI评分、投资建议
    """
    # 获取历史数据
    df = eastmoney_service.get_history(code, days=60)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的数据"
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
    suggestion = indicator_service.calculate_trading_suggestion(df, indicators)
    score = indicator_service.calculate_score(indicators, suggestion)

    # 获取完整 AI 分析
    ai_result = get_full_ai_analysis(
        name=realtime["name"],
        code=code,
        industry=realtime.get("industry", "未知"),
        price=realtime["price"],
        change=realtime["change"],
        market_cap=realtime.get("market_cap", 0),
        score=score,
        indicators=indicators,
        suggestion=suggestion,
    )

    # 计算 AI 排名分数
    vol = indicators.get("volume", {})
    ma = indicators.get("ma", {})
    ai_ranking_score = calculate_ai_ranking_score(
        technical_score=score,
        ai_score=ai_result.get("ai_recommendation", {}).get("ai_score", score),
        change=realtime["change"],
        volume_status=vol.get("status", "正常"),
        ma_trend=ma.get("trend", "震荡"),
    )

    return {
        "code": code,
        "name": realtime["name"],
        "industry": realtime.get("industry", ""),
        "price": realtime["price"],
        "change": realtime["change"],
        "technical_score": score,
        "ai_ranking_score": ai_ranking_score,
        "company_analysis": ai_result.get("company", {}),
        "fundamental_analysis": ai_result.get("fundamental", {}),
        "ai_recommendation": ai_result.get("ai_recommendation", {}),
        "analysis_time": ai_result.get("analysis_time", ""),
    }


@router.get("/rankings/ai")
async def get_ai_rankings(
    limit: int = Query(default=10, le=20, description="返回数量"),
    refresh: bool = Query(default=False, description="强制刷新缓存")
):
    """
    获取 AI 智能排名榜

    返回根据 AI 综合评分排名的股票列表
    - 数据缓存 30 分钟，避免重复计算
    - 设置 refresh=true 可强制刷新
    """
    global _ai_rankings_cache

    # 检查缓存是否有效
    if not refresh and _ai_rankings_cache["data"] is not None:
        if _ai_rankings_cache["updated_at"] is not None:
            cache_age = datetime.now() - _ai_rankings_cache["updated_at"]
            if cache_age < _ai_rankings_cache["cache_duration"]:
                # 返回缓存数据
                cached_rankings = _ai_rankings_cache["data"][:limit]
                return {
                    "count": len(cached_rankings),
                    "rankings": cached_rankings,
                    "cached": True,
                    "cache_time": _ai_rankings_cache["updated_at"].strftime("%H:%M:%S"),
                }

    # 使用预定义的热门股票进行排名（30只覆盖更多行业）
    hot_stocks = [
        # 白酒消费
        "600519", "000858", "000568", "002304",
        # 新能源/电动车
        "300750", "002594", "601012", "002812",
        # 金融保险
        "601318", "600036", "000001", "601166",
        # 科技互联网
        "002415", "300059", "002230", "000063",
        # 医药健康
        "600276", "000651", "300015", "002007",
        # 家电制造
        "000333", "000725", "600690",
        # 其他龙头
        "603288", "600030", "601888", "000568",
        "600887", "601899", "002352",
    ]
    # 去重
    hot_stocks = list(dict.fromkeys(hot_stocks))

    rankings = []

    for code in hot_stocks:
        try:
            # 获取数据
            df = eastmoney_service.get_history(code, days=60)
            if df is None or df.empty:
                continue

            realtime = eastmoney_service.get_realtime(code)
            if realtime is None:
                continue

            # 计算指标
            indicators = indicator_service.calculate_indicators(df)
            suggestion = indicator_service.calculate_trading_suggestion(df, indicators)
            score = indicator_service.calculate_score(indicators, suggestion)

            # 计算 AI 排名分数
            vol = indicators.get("volume", {})
            ma = indicators.get("ma", {})
            macd = indicators.get("macd", {})

            ai_ranking_score = calculate_ai_ranking_score(
                technical_score=score,
                ai_score=score,  # 简化版本使用技术评分
                change=realtime["change"],
                volume_status=vol.get("status", "正常"),
                ma_trend=ma.get("trend", "震荡"),
            )

            rankings.append({
                "code": code,
                "name": realtime["name"],
                "industry": realtime.get("industry", ""),
                "price": realtime["price"],
                "change": realtime["change"],
                "technical_score": score,
                "ai_ranking_score": ai_ranking_score,
                "macd_signal": macd.get("signal", "未知"),
                "ma_trend": ma.get("trend", "震荡"),
                "action": suggestion.get("action", "观望"),
                # 交易建议详情
                "buy_price_low": suggestion.get("buy_price_low", 0),
                "buy_price_high": suggestion.get("buy_price_high", 0),
                "stop_loss": suggestion.get("stop_loss", 0),
                "take_profit_1": suggestion.get("take_profit_1", 0),
                "take_profit_2": suggestion.get("take_profit_2", 0),
                "risk_level": suggestion.get("risk_level", "medium"),
                "holding_days": suggestion.get("holding_days", "5-15个交易日"),
                "position_ratio": suggestion.get("position", "10-15%"),
            })

        except Exception as e:
            print(f"Error processing {code}: {e}")
            continue

    # 按 AI 排名分数降序排序
    rankings.sort(key=lambda x: x["ai_ranking_score"], reverse=True)

    # 添加排名
    for i, item in enumerate(rankings):
        item["rank"] = i + 1

    # 更新缓存
    _ai_rankings_cache["data"] = rankings
    _ai_rankings_cache["updated_at"] = datetime.now()

    # 获取 AI 模型状态
    ai_status = get_ai_model_status()

    return {
        "count": len(rankings[:limit]),
        "rankings": rankings[:limit],
        "cached": False,
        "cache_time": _ai_rankings_cache["updated_at"].strftime("%H:%M:%S"),
        "ai_model_status": ai_status,
    }
