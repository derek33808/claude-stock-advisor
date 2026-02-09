from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client instance (singleton)"""
    global _supabase_client

    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase URL and Key must be configured")

        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )

    return _supabase_client


# ============================================
# Recommendations CRUD
# ============================================

async def save_recommendations(date: str, recommendations: list[dict]) -> bool:
    """Save daily recommendations to database"""
    try:
        supabase = get_supabase()

        # Prepare data
        records = []
        for rec in recommendations:
            records.append({
                "date": date,
                "code": rec["code"],
                "name": rec["name"],
                "industry": rec.get("industry"),
                "score": rec["score"],
                "price": rec["price"],
                "change": rec["change"],
                "buy_price_low": rec["buy_price_low"],
                "buy_price_high": rec["buy_price_high"],
                "stop_loss": rec["stop_loss"],
                "take_profit_1": rec["take_profit_1"],
                "take_profit_2": rec["take_profit_2"],
                "reasons": rec.get("reasons", {}),
            })

        # Upsert (insert or update)
        supabase.table("recommendations").upsert(
            records,
            on_conflict="date,code"
        ).execute()

        return True
    except Exception as e:
        print(f"Error saving recommendations: {e}")
        return False


async def get_recommendations(date: str) -> list[dict]:
    """Get recommendations for a specific date"""
    try:
        supabase = get_supabase()

        response = supabase.table("recommendations") \
            .select("*") \
            .eq("date", date) \
            .order("score", desc=True) \
            .execute()

        return response.data
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []


async def get_latest_recommendations() -> tuple[str, list[dict]]:
    """Get the latest recommendations"""
    try:
        supabase = get_supabase()

        # Get the latest date
        response = supabase.table("recommendations") \
            .select("date") \
            .order("date", desc=True) \
            .limit(1) \
            .execute()

        if not response.data:
            return "", []

        latest_date = response.data[0]["date"]

        # Get recommendations for that date
        recs = await get_recommendations(latest_date)
        return latest_date, recs
    except Exception as e:
        print(f"Error getting latest recommendations: {e}")
        return "", []


# ============================================
# Market Overview CRUD
# ============================================

async def save_market_overview(date: str, overview: dict) -> bool:
    """Save market overview"""
    try:
        supabase = get_supabase()

        supabase.table("market_overview").upsert({
            "date": date,
            "sh_index": overview["sh_index"],
            "sh_change": overview["sh_change"],
            "sz_index": overview["sz_index"],
            "sz_change": overview["sz_change"],
            "sentiment": overview["sentiment"],
        }, on_conflict="date").execute()

        return True
    except Exception as e:
        print(f"Error saving market overview: {e}")
        return False


async def get_market_overview(date: str) -> dict | None:
    """Get market overview for a date"""
    try:
        supabase = get_supabase()

        response = supabase.table("market_overview") \
            .select("*") \
            .eq("date", date) \
            .limit(1) \
            .execute()

        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting market overview: {e}")
        return None


# ============================================
# Tracking CRUD
# ============================================

async def save_tracking_record(rec_id: str, track_date: str, price: float, change_pct: float, status: str) -> bool:
    """Save tracking record"""
    try:
        supabase = get_supabase()

        supabase.table("recommendation_tracking").insert({
            "recommendation_id": rec_id,
            "track_date": track_date,
            "price": price,
            "change_from_rec": change_pct,
            "status": status,
        }).execute()

        return True
    except Exception as e:
        print(f"Error saving tracking: {e}")
        return False


async def get_performance_stats(days: int = 30) -> dict:
    """Get strategy performance statistics"""
    try:
        supabase = get_supabase()

        # Get recommendations from last N days
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        response = supabase.table("recommendation_tracking") \
            .select("*, recommendations(*)") \
            .gte("track_date", start_date) \
            .execute()

        if not response.data:
            return {
                "total": 0,
                "win_count": 0,
                "loss_count": 0,
                "holding_count": 0,
                "win_rate": 0,
                "avg_return": 0,
                "profit_loss_ratio": 0,
            }

        # Calculate stats
        total = len(response.data)
        win_count = sum(1 for r in response.data if r["status"] == "take_profit")
        loss_count = sum(1 for r in response.data if r["status"] == "stop_loss")
        holding_count = sum(1 for r in response.data if r["status"] == "holding")

        returns = [r["change_from_rec"] for r in response.data if r["change_from_rec"]]
        avg_return = sum(returns) / len(returns) if returns else 0

        wins = [r["change_from_rec"] for r in response.data if r["status"] == "take_profit"]
        losses = [abs(r["change_from_rec"]) for r in response.data if r["status"] == "stop_loss"]

        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 1

        return {
            "total": total,
            "win_count": win_count,
            "loss_count": loss_count,
            "holding_count": holding_count,
            "win_rate": round(win_count / total * 100, 1) if total > 0 else 0,
            "avg_return": round(avg_return, 2),
            "profit_loss_ratio": round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
        }
    except Exception as e:
        print(f"Error getting performance stats: {e}")
        return {}


# ============================================
# Stock Cache CRUD
# ============================================

async def get_cached_stock(code: str) -> dict | None:
    """Get cached stock data"""
    try:
        supabase = get_supabase()

        response = supabase.table("stock_cache") \
            .select("*") \
            .eq("code", code) \
            .limit(1) \
            .execute()

        if not response.data:
            return None

        # Check if cache is fresh (less than 1 day old)
        from datetime import datetime
        cached = response.data[0]
        updated_at = datetime.fromisoformat(cached["updated_at"].replace("Z", "+00:00"))
        now = datetime.now(updated_at.tzinfo)

        if (now - updated_at).days >= 1:
            return None  # Cache expired

        return cached
    except Exception as e:
        print(f"Error getting cached stock: {e}")
        return None


async def save_stock_cache(code: str, name: str, industry: str, data: dict, indicators: dict) -> bool:
    """Save stock data to cache"""
    try:
        supabase = get_supabase()

        supabase.table("stock_cache").upsert({
            "code": code,
            "name": name,
            "industry": industry,
            "daily_data": data,
            "indicators": indicators,
        }, on_conflict="code").execute()

        return True
    except Exception as e:
        print(f"Error saving stock cache: {e}")
        return False


# Export global supabase instance for convenience
# This is lazy-initialized on first access
supabase = get_supabase()
