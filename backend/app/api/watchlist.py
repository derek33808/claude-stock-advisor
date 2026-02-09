"""
自选股 API 端点
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services import watchlist_service, eastmoney_service

router = APIRouter()


class WatchlistAddRequest(BaseModel):
    code: str
    user_id: str = "default_user"  # 默认用户ID
    name: str = None  # 可选，如果不提供则自动获取


class WatchlistRemoveRequest(BaseModel):
    code: str
    user_id: str = "default_user"  # 默认用户ID


@router.post("/watchlist/add")
async def add_watchlist(data: WatchlistAddRequest):
    """
    添加自选股

    Body:
        - code: 股票代码（必需）
        - user_id: 用户ID（可选，默认 "default_user"）
        - name: 股票名称（可选，自动获取）

    Returns:
        添加结果
    """
    try:
        # 如果没有提供 name，自动获取
        name = data.name
        if not name:
            quote = eastmoney_service.get_realtime(data.code)
            if quote:
                name = quote['name']
            else:
                raise HTTPException(status_code=404, detail=f"股票 {data.code} 不存在")

        result = await watchlist_service.add_to_watchlist(
            user_id=data.user_id,
            code=data.code,
            name=name
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


@router.delete("/watchlist/remove")
async def remove_watchlist(data: WatchlistRemoveRequest):
    """
    移除自选股

    Body:
        - user_id: 用户ID
        - code: 股票代码

    Returns:
        移除结果
    """
    try:
        result = await watchlist_service.remove_from_watchlist(
            user_id=data.user_id,
            code=data.code
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除失败: {str(e)}")


@router.get("/watchlist/list")
async def get_watchlist(user_id: str = Query("default_user", description="用户ID")):
    """
    获取自选股列表

    Query:
        - user_id: 用户ID（可选，默认 "default_user"）

    Returns:
        自选股列表（包含当前行情）
    """
    try:
        watchlist = await watchlist_service.get_watchlist(user_id)

        # 获取每只股票的实时行情
        for item in watchlist:
            quote = eastmoney_service.get_realtime(item['code'])
            if quote:
                item['price'] = quote['price']
                item['change'] = quote['change']

        return {
            'user_id': user_id,
            'count': len(watchlist),
            'watchlist': watchlist
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取自选股失败: {str(e)}")


@router.get("/watchlist/check/{code}")
async def check_watchlist(code: str, user_id: str = Query("default_user", description="用户ID")):
    """
    检查股票是否在自选股中

    Path:
        - code: 股票代码

    Query:
        - user_id: 用户ID（可选，默认 "default_user"）

    Returns:
        是否在自选股中
    """
    try:
        is_in = await watchlist_service.is_in_watchlist(user_id, code)

        return {
            'code': code,
            'is_in_watchlist': is_in
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")
