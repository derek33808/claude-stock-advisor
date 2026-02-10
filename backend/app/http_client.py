"""
共享 httpx.AsyncClient 实例（带连接池）
用于替换全项目的同步 urllib 调用，避免阻塞 FastAPI 事件循环
"""

from typing import Optional
import httpx

# 全局 AsyncClient，在 FastAPI 生命周期内复用
_client: Optional[httpx.AsyncClient] = None

# 通用请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com",
}

# GLM API 请求头（不含 Authorization，调用时动态设置）
GLM_HEADERS = {
    "Content-Type": "application/json",
}


def get_client() -> httpx.AsyncClient:
    """获取全局 AsyncClient 实例"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(8.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
        )
    return _client


async def close_client():
    """关闭全局 AsyncClient（应用关闭时调用）"""
    global _client
    if _client and not _client.is_closed:
        await _client.close()
        _client = None
