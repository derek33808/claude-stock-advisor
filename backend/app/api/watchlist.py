"""
自选股 API 端点
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services import watchlist_service, eastmoney_service

router = APIRouter()


class WatchlistAddRequest(BaseModel):
    user_id: str
    code: str
    name: str


class WatchlistRemoveRequest(BaseModel):
    user_id: str
    code: str


@router.post("/watchlist/add")
async def add_watchlist(data: WatchlistAddRequest):
    """
    添加自选股

    Body:
        - user_id: 用户ID
        - code: 股票代码
        - name: 股票名称

    Returns:
        添加结果
    """
    try:
        result = await watchlist_service.add_to_watchlist(
            user_id=data.user_id,
            code=data.code,
            name=data.name
        )

        return result

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
async def get_watchlist(user_id: str = Query(..., description="用户ID")):
    """
    获取自选股列表

    Query:
        - user_id: 用户ID

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
async def check_watchlist(code: str, user_id: str = Query(..., description="用户ID")):
    """
    检查股票是否在自选股中

    Path:
        - code: 股票代码

    Query:
        - user_id: 用户ID

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
