from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import stock, recommendations, stats

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A股智能交易策略指导系统 API",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stock.router, prefix="/api/v1", tags=["股票查询"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["推荐"])
app.include_router(stats.router, prefix="/api/v1", tags=["统计"])


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/debug/stock/{code}")
async def debug_stock(code: str):
    """Debug endpoint to test stock data retrieval"""
    from app.services import eastmoney_service, indicator_service
    import traceback

    result = {
        "code": code,
        "history": None,
        "realtime": None,
        "indicators": None,
        "error": None
    }

    try:
        # Test history
        df = eastmoney_service.get_history(code, days=60)
        result["history"] = {
            "success": df is not None and not df.empty,
            "rows": len(df) if df is not None else 0
        }

        # Test realtime
        rt = eastmoney_service.get_realtime(code)
        result["realtime"] = {
            "success": rt is not None,
            "price": rt.get("price") if rt else None
        }

        # Test indicators
        if df is not None and not df.empty:
            indicators = indicator_service.calculate_indicators(df)
            result["indicators"] = {
                "success": indicators is not None,
                "keys": list(indicators.keys()) if indicators else []
            }
    except Exception as e:
        result["error"] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }

    return result
