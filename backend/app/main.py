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
    """Debug endpoint to test stock data retrieval from all sources"""
    from app.services import eastmoney_service, yahoo_service, indicator_service
    import traceback

    result = {
        "code": code,
        "eastmoney": {"history": None, "realtime": None, "error": None},
        "yahoo": {"history": None, "realtime": None, "error": None},
        "combined": {"history": None, "realtime": None},
        "indicators": None,
    }

    # Test EastMoney directly
    try:
        df_em = eastmoney_service.get_stock_history(code, days=60)
        result["eastmoney"]["history"] = {
            "success": df_em is not None and not df_em.empty,
            "rows": len(df_em) if df_em is not None else 0
        }
        rt_em = eastmoney_service.get_stock_realtime(code)
        result["eastmoney"]["realtime"] = {
            "success": rt_em is not None,
            "price": rt_em.get("price") if rt_em else None
        }
    except Exception as e:
        result["eastmoney"]["error"] = str(e)

    # Test Yahoo directly
    try:
        df_yh = yahoo_service.get_stock_history(code, days=60)
        result["yahoo"]["history"] = {
            "success": df_yh is not None and not df_yh.empty,
            "rows": len(df_yh) if df_yh is not None else 0
        }
        rt_yh = yahoo_service.get_stock_realtime(code)
        result["yahoo"]["realtime"] = {
            "success": rt_yh is not None,
            "price": rt_yh.get("price") if rt_yh else None
        }
    except Exception as e:
        result["yahoo"]["error"] = str(e)

    # Test combined (with fallback)
    try:
        df = eastmoney_service.get_history(code, days=60)
        result["combined"]["history"] = {
            "success": df is not None and not df.empty,
            "rows": len(df) if df is not None else 0
        }
        rt = eastmoney_service.get_realtime(code)
        result["combined"]["realtime"] = {
            "success": rt is not None,
            "price": rt.get("price") if rt else None
        }

        # Test indicators if we have history
        if df is not None and not df.empty:
            indicators = indicator_service.calculate_indicators(df)
            result["indicators"] = {
                "success": indicators is not None,
                "keys": list(indicators.keys()) if indicators else []
            }
    except Exception as e:
        result["combined"]["error"] = str(e)

    return result
