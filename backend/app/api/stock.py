"""
股票查询 API
全面异步化 + 并行化优化
"""

import asyncio
from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Query
from cachetools import TTLCache
from app.services import eastmoney_service, indicator_service, strategy_service
from app.services.glm_service import generate_summary_with_fallback, generate_template_summary
from app.services.ai_analysis_service import get_full_ai_analysis, calculate_ai_ranking_score, get_ai_model_status
from app.services import cache_service
from app.db.supabase import get_supabase
from app.models.schemas import StockAnalysis

router = APIRouter()

# AI 排名缓存（TTLCache，30分钟过期，最多1条）
_ai_rankings_cache: TTLCache = TTLCache(maxsize=1, ttl=1800)
_AI_RANKINGS_KEY = "rankings"

# 单股票分析缓存（TTLCache，交易时段3分钟/非交易时段30分钟，最多200条）
_stock_analysis_cache: TTLCache = TTLCache(maxsize=200, ttl=180)


def _get_stock_cache_ttl() -> int:
    """智能缓存过期：交易时段3分钟，非交易时段30分钟"""
    if cache_service._is_trading_hours():
        return 180  # 3 minutes
    return 1800  # 30 minutes


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

    results = await eastmoney_service.search_stocks(q, limit=limit)

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

    缓存策略：L1 内存(智能TTL) -> L2 Supabase(4小时) -> L3 数据源(实时)
    """
    # ===== 非刷新模式：尝试从缓存读取 =====
    if not refresh:
        # L1: 内存缓存 (TTLCache 自动过期)
        cache_key = f"{code}_{ai_analysis}"
        cached = _stock_analysis_cache.get(cache_key)
        if cached:
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
                realtime = await eastmoney_service.get_realtime(code)
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
    # 60s 总超时保护：超时则降级返回纯技术分析（无AI）
    try:
        return await asyncio.wait_for(_do_full_analysis(code, ai_analysis), timeout=60.0)
    except asyncio.TimeoutError:
        print(f"[Stock] {code} 完整分析超时(60s)，降级到纯技术分析")
        try:
            return await asyncio.wait_for(
                _do_full_analysis(code, ai_analysis=False, skip_ai_summary=True),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=f"股票 {code} 分析超时，请稍后重试")


async def _do_full_analysis(code: str, ai_analysis: bool = True, skip_ai_summary: bool = False) -> dict:
    """执行完整的股票分析流程并写入所有缓存层

    Args:
        code: 股票代码
        ai_analysis: 是否包含 AI 智能分析
        skip_ai_summary: 跳过 GLM AI 摘要生成，使用纯模板（批量接口用）
    """
    # 并行获取历史数据和实时行情
    df, realtime = await asyncio.gather(
        eastmoney_service.get_history(code, days=60),
        eastmoney_service.get_realtime(code),
    )

    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的数据，请检查代码是否正确"
        )

    if realtime is None:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的实时行情"
        )

    # 计算技术指标
    indicators = indicator_service.calculate_indicators(df)
    suggestion = indicator_service.calculate_trading_suggestion(df, indicators, current_price=realtime["price"])
    reasons_raw = indicator_service.generate_reasons(indicators)
    score = indicator_service.calculate_score(indicators, suggestion)

    # 多维度评分 + 价格预测
    score_details = indicator_service.calculate_score_detailed(
        indicators, suggestion, current_price=realtime["price"], df=df)
    price_prediction = indicator_service.calculate_price_prediction(
        indicators, current_price=realtime["price"], df=df)

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

    # 生成摘要和 AI 分析可以并行
    if skip_ai_summary:
        summary = generate_template_summary(
            name=realtime["name"],
            code=code,
            price=realtime["price"],
            change=realtime["change"],
            score=score,
            suggestion=formatted_suggestion,
            indicators=formatted_indicators,
            reasons=reasons,
        )
        ai_result = None
        if ai_analysis:
            ai_result = await get_full_ai_analysis(
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
    elif ai_analysis:
        # 并行执行 AI 摘要 和 AI 全面分析
        summary_task = generate_summary_with_fallback(
            name=realtime["name"],
            code=code,
            price=realtime["price"],
            change=realtime["change"],
            score=score,
            suggestion=formatted_suggestion,
            indicators=formatted_indicators,
            reasons=reasons,
        )
        ai_task = get_full_ai_analysis(
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
        summary, ai_result = await asyncio.gather(summary_task, ai_task)
    else:
        summary = await generate_summary_with_fallback(
            name=realtime["name"],
            code=code,
            price=realtime["price"],
            change=realtime["change"],
            score=score,
            suggestion=formatted_suggestion,
            indicators=formatted_indicators,
            reasons=reasons,
        )
        ai_result = None

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
        "score_details": score_details,
        "price_prediction": price_prediction,
        "summary": summary,
    }

    if ai_result:
        response["ai_analysis"] = ai_result

        ai_ranking_score = calculate_ai_ranking_score(
            technical_score=score,
            ai_score=ai_result.get("ai_recommendation", {}).get("ai_score", score),
            change=realtime["change"],
            volume_status=vol.get("status", "正常"),
            ma_trend=ma.get("trend", "震荡"),
        )
        response["ai_ranking_score"] = ai_ranking_score

        # 合并 AI 维度评分（AI 提供估值/质量/情绪维度）
        ai_rec = ai_result.get("ai_recommendation", {})
        ai_dims = ai_rec.get("dimensions", {})
        if ai_dims:
            response["score_details"]["valuation_score"] = ai_dims.get("valuation_score", 50)
            response["score_details"]["quality_score"] = ai_dims.get("quality_score", 50)
            response["score_details"]["sentiment_score"] = ai_dims.get("sentiment_score", 50)

        # 合并 AI 价格预测（技术 40% + AI 60% 加权）
        ai_pred = ai_rec.get("price_prediction", {})
        if ai_pred and ai_pred.get("5d_target_high"):
            tech_pred = response["price_prediction"]
            merged = {}
            for key in ["5d_target_high", "5d_target_low", "5d_most_likely"]:
                tech_val = tech_pred.get(key, 0)
                ai_val = ai_pred.get(key, 0)
                if tech_val and ai_val:
                    merged[key] = round(tech_val * 0.4 + ai_val * 0.6, 2)
                else:
                    merged[key] = ai_val or tech_val
            for key in ["probability_up", "probability_down", "probability_flat"]:
                tech_val = tech_pred.get(key, 33)
                ai_val = ai_pred.get(key, 33)
                merged[key] = int(tech_val * 0.4 + ai_val * 0.6)
            merged["expected_return_pct"] = round(
                tech_pred.get("expected_return_pct", 0) * 0.4 +
                ai_pred.get("expected_return_pct", 0) * 0.6, 2)
            response["price_prediction"] = merged

        # AI catalysts
        if ai_rec.get("catalysts"):
            response["catalysts"] = ai_rec["catalysts"]

    # ===== 写入所有缓存层 =====

    # L1: 内存缓存 (TTLCache)
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

    # 保存分析历史记录（每只股票每天一条，upsert 避免重复）
    try:
        supabase_client = get_supabase()
        supabase_client.table('analysis_history').upsert({
            'code': code,
            'analysis_date': str(date.today()),
            'analysis_time': datetime.now().strftime('%H:%M:%S'),
            'price': response['price'],
            'change_percent': response['change'],
            'prediction_direction': formatted_suggestion.get('action', '观望'),
            'prediction_text': summary[:500] if summary else '',
            'target_price_low': formatted_suggestion['buy_price']['low'],
            'target_price_high': formatted_suggestion['take_profit']['target2'],
            'analysis_content': response,
            'created_at': datetime.now().isoformat(),
        }, on_conflict='code,analysis_date').execute()
    except Exception as e:
        print(f"[History] Failed to save analysis history for {code}: {e}")

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

    # 2. 批量获取实时价格（单次 HTTP，异步）
    batch_quotes = await eastmoney_service.get_batch_realtime(code_list)
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

    # 3. 未缓存的股票：快速计算技术评分（不调 AI，~100ms/只）
    #    使用 Semaphore 控制并发，保持 batch 在 15s 内
    batch_semaphore = asyncio.Semaphore(3)

    async def _quick_score(stock_code: str) -> dict:
        """快速技术评分（无AI调用）"""
        quote = batch_quotes.get(stock_code)
        if not quote:
            return None

        base_item = {
            "code": stock_code,
            "name": quote.get("name", stock_code),
            "industry": quote.get("industry", ""),
            "price": quote.get("price", 0),
            "change": quote.get("change", 0),
            "open": quote.get("open", 0),
            "high": quote.get("high", 0),
            "low": quote.get("low", 0),
            "prev_close": quote.get("prev_close", 0),
            "volume": quote.get("volume", 0),
            "amount": quote.get("amount", 0),
            "market_cap": quote.get("market_cap", 0),
        }

        async with batch_semaphore:
            try:
                df = await eastmoney_service.get_history(stock_code, days=60)
                if df is not None and not df.empty:
                    indicators = indicator_service.calculate_indicators(df)
                    suggestion = indicator_service.calculate_trading_suggestion(
                        df, indicators, current_price=quote.get("price", 0))
                    score = indicator_service.calculate_score(indicators, suggestion)
                    score_details = indicator_service.calculate_score_detailed(
                        indicators, suggestion, current_price=quote.get("price", 0), df=df)

                    base_item["score"] = score
                    base_item["score_details"] = score_details
                    base_item["indicators"] = {}  # 轻量响应不含完整指标
                    base_item["suggestion"] = {
                        "action": suggestion.get("action", "观望"),
                        "buy_price": {"low": suggestion.get("buy_price_low", 0), "high": suggestion.get("buy_price_high", 0)},
                        "stop_loss": suggestion.get("stop_loss", 0),
                        "take_profit": {"target1": suggestion.get("take_profit_1", 0), "target2": suggestion.get("take_profit_2", 0)},
                        "holding_days": suggestion.get("holding_days", "-"),
                        "position_ratio": suggestion.get("position", "-"),
                        "risk_level": suggestion.get("risk_level", "medium"),
                    }
                    base_item["reasons"] = []
                    return base_item
            except Exception as e:
                print(f"[Batch] Quick score failed for {stock_code}: {e}")

        # 回退：无评分的轻量响应
        base_item["score"] = 0
        base_item["indicators"] = {}
        base_item["suggestion"] = {
            "action": "点击查看详情",
            "buy_price": {"low": 0, "high": 0},
            "stop_loss": 0,
            "take_profit": {"target1": 0, "target2": 0},
            "holding_days": "-",
            "position_ratio": "-",
            "risk_level": "medium",
        }
        base_item["reasons"] = []
        return base_item

    if uncached_codes:
        quick_results = await asyncio.gather(
            *[_quick_score(sc) for sc in uncached_codes],
            return_exceptions=True,
        )
        for qr in quick_results:
            if isinstance(qr, dict):
                results.append(qr)

    return {
        "count": len(results),
        "stocks": results,
    }


@router.post("/stocks/prefetch")
async def prefetch_stocks(codes: List[str]):
    """
    批量预加载股票数据（后台缓存）
    """
    results = {"success": [], "failed": []}

    for code in codes[:20]:
        try:
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
    """
    df = await eastmoney_service.get_history(code, days=days)
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的 K 线数据"
        )

    # 使用 to_dict('records') 替代 iterrows() 提高性能
    kline_data = []
    for row in df.to_dict('records'):
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
    """
    # 并行获取历史数据和实时行情
    df, realtime = await asyncio.gather(
        eastmoney_service.get_history(code, days=60),
        eastmoney_service.get_realtime(code),
    )

    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的数据"
        )

    if realtime is None:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {code} 的实时行情"
        )

    # 计算技术指标
    indicators = indicator_service.calculate_indicators(df)
    suggestion = indicator_service.calculate_trading_suggestion(df, indicators, current_price=realtime["price"])
    score = indicator_service.calculate_score(indicators, suggestion)

    # 获取完整 AI 分析
    ai_result = await get_full_ai_analysis(
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
    使用 asyncio.gather + Semaphore 并行分析 + 批量获取实时价格
    """
    # 检查缓存是否有效
    if not refresh and _AI_RANKINGS_KEY in _ai_rankings_cache:
        cached = _ai_rankings_cache[_AI_RANKINGS_KEY]
        cached_rankings = cached["data"][:limit]
        return {
            "count": len(cached_rankings),
            "rankings": cached_rankings,
            "cached": True,
            "cache_time": cached["updated_at"].strftime("%H:%M:%S"),
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

    # 批量获取实时价格（单次 HTTP 请求）
    batch_quotes = await eastmoney_service.get_batch_realtime(hot_stocks)

    # 并行获取历史数据 + 计算指标（Semaphore 限制并发）
    semaphore = asyncio.Semaphore(5)

    async def _analyze_stock(code: str) -> Optional[dict]:
        async with semaphore:
            try:
                df = await eastmoney_service.get_history(code, days=60)
                if df is None or df.empty:
                    return None

                realtime = batch_quotes.get(code)
                if not realtime:
                    return None

                indicators = indicator_service.calculate_indicators(df)
                suggestion = indicator_service.calculate_trading_suggestion(df, indicators, current_price=realtime["price"])
                score = indicator_service.calculate_score(indicators, suggestion)

                vol = indicators.get("volume", {})
                ma = indicators.get("ma", {})
                macd = indicators.get("macd", {})

                ai_ranking_score = calculate_ai_ranking_score(
                    technical_score=score,
                    ai_score=score,
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
                    "macd_signal": macd.get("signal", "未知"),
                    "ma_trend": ma.get("trend", "震荡"),
                    "action": suggestion.get("action", "观望"),
                    "buy_price_low": suggestion.get("buy_price_low", 0),
                    "buy_price_high": suggestion.get("buy_price_high", 0),
                    "stop_loss": suggestion.get("stop_loss", 0),
                    "take_profit_1": suggestion.get("take_profit_1", 0),
                    "take_profit_2": suggestion.get("take_profit_2", 0),
                    "risk_level": suggestion.get("risk_level", "medium"),
                    "holding_days": suggestion.get("holding_days", "5-15个交易日"),
                    "position_ratio": suggestion.get("position", "10-15%"),
                }

            except Exception as e:
                print(f"Error processing {code}: {e}")
                return None

    # 并行分析所有股票
    analysis_results = await asyncio.gather(
        *[_analyze_stock(code) for code in hot_stocks]
    )

    rankings = [r for r in analysis_results if r is not None]

    # 按 AI 排名分数降序排序
    rankings.sort(key=lambda x: x["ai_ranking_score"], reverse=True)

    # 添加排名
    for i, item in enumerate(rankings):
        item["rank"] = i + 1

    # 更新缓存
    _ai_rankings_cache[_AI_RANKINGS_KEY] = {
        "data": rankings,
        "updated_at": datetime.now(),
    }

    # 获取 AI 模型状态
    ai_status = get_ai_model_status()

    return {
        "count": len(rankings[:limit]),
        "rankings": rankings[:limit],
        "cached": False,
        "cache_time": datetime.now().strftime("%H:%M:%S"),
        "ai_model_status": ai_status,
    }
