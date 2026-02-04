from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import stock, recommendations, stats

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="A股智能交易策略指导系统 API",
    version="2.0.0",
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
