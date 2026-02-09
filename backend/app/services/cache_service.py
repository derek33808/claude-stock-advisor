"""
智能缓存服务
三层缓存架构：内存(30秒) -> Supabase(4小时) -> 数据源(实时)
"""

from datetime import datetime, timedelta
from typing import Optional
from app.db.supabase import get_supabase

# ============================================
# L1: 内存缓存 - 实时价格 (30秒TTL)
# ============================================

_quote_cache: dict[str, dict] = {}
_QUOTE_TTL = timedelta(seconds=30)


def get_cached_quote(code: str) -> Optional[dict]:
    """从内存获取实时价格缓存"""
    cached = _quote_cache.get(code)
    if cached and datetime.now() - cached["_ts"] < _QUOTE_TTL:
        return cached
    return None


def set_cached_quote(code: str, quote: dict):
    """写入实时价格内存缓存"""
    quote["_ts"] = datetime.now()
    _quote_cache[code] = quote


def set_cached_quotes_batch(quotes: dict[str, dict]):
    """批量写入实时价格内存缓存"""
    now = datetime.now()
    for code, quote in quotes.items():
        quote["_ts"] = now
        _quote_cache[code] = quote


# ============================================
# L2: Supabase 持久缓存 - 完整分析结果
# ============================================

_ANALYSIS_TTL = timedelta(hours=4)


def _is_trading_hours(now: Optional[datetime] = None) -> bool:
    """判断当前是否为交易时段"""
    if now is None:
        now = datetime.now()
    weekday = now.weekday()
    if weekday >= 5:  # 周六日
        return False
    hour, minute = now.hour, now.minute
    t = hour * 60 + minute
    # 9:30-11:30 or 13:00-15:00
    return (570 <= t <= 690) or (780 <= t <= 900)


def get_cached_analysis(code: str) -> Optional[dict]:
    """
    从 Supabase 获取缓存的完整分析结果
    返回 None 表示缓存未命中或已过期
    """
    try:
        sb = get_supabase()
        response = sb.table("stock_analysis_cache") \
            .select("*") \
            .eq("code", code) \
            .limit(1) \
            .execute()

        if not response.data:
            return None

        cached = response.data[0]

        # 检查分析缓存是否过期
        updated_at_str = cached.get("full_analysis_updated_at")
        if not updated_at_str:
            return None

        updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
        now = datetime.now(updated_at.tzinfo)

        if now - updated_at > _ANALYSIS_TTL:
            return None  # 超过4小时，缓存过期

        return cached

    except Exception as e:
        print(f"[Cache] Error reading analysis cache for {code}: {e}")
        return None


def save_analysis_cache(code: str, analysis_data: dict):
    """
    将完整分析结果写入 Supabase 缓存
    analysis_data 应包含所有分析字段
    """
    try:
        sb = get_supabase()
        now = datetime.now().isoformat()

        record = {
            "code": code,
            "name": analysis_data.get("name", ""),
            "industry": analysis_data.get("industry", ""),
            # 行情
            "price": analysis_data.get("price", 0),
            "change_percent": analysis_data.get("change", 0),
            "open_price": analysis_data.get("open", 0),
            "high_price": analysis_data.get("high", 0),
            "low_price": analysis_data.get("low", 0),
            "prev_close": analysis_data.get("prev_close", 0),
            "volume": analysis_data.get("volume", 0),
            "amount": analysis_data.get("amount", 0),
            "market_cap": analysis_data.get("market_cap", 0),
            "quote_updated_at": now,
            # 技术分析
            "indicators": analysis_data.get("indicators", {}),
            "suggestion": analysis_data.get("suggestion", {}),
            "reasons": analysis_data.get("reasons", []),
            "score": analysis_data.get("score", 0),
            # AI 分析
            "ai_summary": analysis_data.get("summary", ""),
            "ai_company": analysis_data.get("ai_analysis", {}).get("company", {}),
            "ai_fundamental": analysis_data.get("ai_analysis", {}).get("fundamental", {}),
            "ai_recommendation": analysis_data.get("ai_analysis", {}).get("ai_recommendation", {}),
            "ai_ranking_score": analysis_data.get("ai_ranking_score", 0),
            "ai_updated_at": now,
            # 元数据
            "full_analysis_updated_at": now,
            "updated_at": now,
        }

        sb.table("stock_analysis_cache").upsert(
            record, on_conflict="code"
        ).execute()

        print(f"[Cache] Saved analysis cache for {code}")

    except Exception as e:
        print(f"[Cache] Error saving analysis cache for {code}: {e}")


def update_quote_in_cache(code: str, realtime: dict):
    """只更新缓存中的行情数据（不触发完整分析）"""
    try:
        sb = get_supabase()
        now = datetime.now().isoformat()

        sb.table("stock_analysis_cache").update({
            "price": realtime.get("price", 0),
            "change_percent": realtime.get("change", 0),
            "open_price": realtime.get("open", 0),
            "high_price": realtime.get("high", 0),
            "low_price": realtime.get("low", 0),
            "prev_close": realtime.get("prev_close", 0),
            "volume": realtime.get("volume", 0),
            "amount": realtime.get("amount", 0),
            "market_cap": realtime.get("market_cap", 0),
            "quote_updated_at": now,
            "updated_at": now,
        }).eq("code", code).execute()

    except Exception as e:
        print(f"[Cache] Error updating quote cache for {code}: {e}")


def get_cached_analyses_batch(codes: list[str]) -> dict[str, dict]:
    """批量获取多只股票的缓存分析结果"""
    try:
        sb = get_supabase()
        response = sb.table("stock_analysis_cache") \
            .select("*") \
            .in_("code", codes) \
            .execute()

        result = {}
        now = datetime.now()

        for cached in response.data:
            updated_at_str = cached.get("full_analysis_updated_at")
            if not updated_at_str:
                continue
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            if now.astimezone(updated_at.tzinfo) - updated_at <= _ANALYSIS_TTL:
                result[cached["code"]] = cached

        return result

    except Exception as e:
        print(f"[Cache] Error batch reading analysis cache: {e}")
        return {}


def build_response_from_cache(cached: dict, realtime: Optional[dict] = None) -> dict:
    """
    将 Supabase 缓存记录转换为 API 响应格式
    如果提供了 realtime，用实时价格覆盖缓存价格
    """
    price = realtime["price"] if realtime else cached.get("price", 0)
    change = realtime["change"] if realtime else cached.get("change_percent", 0)

    response = {
        "code": cached["code"],
        "name": cached.get("name", ""),
        "industry": cached.get("industry", ""),
        "price": price,
        "change": change,
        "open": realtime["open"] if realtime else cached.get("open_price", 0),
        "high": realtime["high"] if realtime else cached.get("high_price", 0),
        "low": realtime["low"] if realtime else cached.get("low_price", 0),
        "prev_close": realtime.get("prev_close", 0) if realtime else cached.get("prev_close", 0),
        "volume": realtime["volume"] if realtime else cached.get("volume", 0),
        "amount": realtime["amount"] if realtime else cached.get("amount", 0),
        "market_cap": realtime.get("market_cap", 0) if realtime else cached.get("market_cap", 0),
        "indicators": cached.get("indicators", {}),
        "suggestion": cached.get("suggestion", {}),
        "reasons": cached.get("reasons", []),
        "score": cached.get("score", 0),
        "summary": cached.get("ai_summary", ""),
        "cached": True,
        "cache_info": {
            "cached": True,
            "analysis_updated_at": cached.get("full_analysis_updated_at", ""),
            "quote_fresh": realtime is not None,
        },
    }

    # AI 分析
    ai_analysis = {}
    if cached.get("ai_company"):
        ai_analysis["company"] = cached["ai_company"]
    if cached.get("ai_fundamental"):
        ai_analysis["fundamental"] = cached["ai_fundamental"]
    if cached.get("ai_recommendation"):
        ai_analysis["ai_recommendation"] = cached["ai_recommendation"]
    if ai_analysis:
        response["ai_analysis"] = ai_analysis
        response["ai_ranking_score"] = cached.get("ai_ranking_score", 0)

    return response
