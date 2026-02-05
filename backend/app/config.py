from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    app_name: str = "Stock Advisor API"
    debug: bool = False

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://stock-advisor.netlify.app",
        "https://claude-stock-advisor.netlify.app",
        "https://a-stock-advisor-cn.netlify.app",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
