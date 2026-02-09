"""
全局刷新 API 端点（SSE）
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import json
import asyncio
from app.services import comprehensive_analysis_service, token_monitor_service

router = APIRouter()

# 并发保护
_active_refreshes = {}


class RefreshAllRequest(BaseModel):
    user_id: str
    codes: List[str]


@router.post("/refresh/all")
async def refresh_all(data: RefreshAllRequest):
    """
    全局刷新（SSE）

    Body:
        - user_id: 用户ID
        - codes: 股票代码列表

    Returns:
        SSE 流，实时返回刷新进度
    """
    user_id = data.user_id
    codes = data.codes

    async def generate_progress():
        total = len(codes)
        completed = 0

        # 检查并发保护
        if user_id in _active_refreshes:
            yield f"data: {json.dumps({'event': 'error', 'message': '刷新进行中，请稍候'})}\n\n"
            return

        _active_refreshes[user_id] = {'status': 'running', 'progress': 0}

        try:
            for code in codes:
                try:
                    # 刷新单只股票
                    await comprehensive_analysis_service.generate_comprehensive_analysis(code)
                    completed += 1

                    # 发送进度
                    progress = {
                        'event': 'progress',
                        'progress': int(completed / total * 100),
                        'current': f'正在分析 {code}...',
                        'completed': completed,
                        'total': total
                    }
                    yield f"data: {json.dumps(progress)}\n\n"

                    # Heartbeat (每3只股票)
                    if completed % 3 == 0:
                        yield f": heartbeat\n\n"

                    # 短暂延迟，避免过快
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"Error refreshing {code}: {e}")
                    continue

            # 获取 Token 使用情况
            token_usage = await token_monitor_service.token_monitor.check_limit()

            # 完成
            complete_data = {
                'event': 'complete',
                'completed': completed,
                'total': total,
                'token_usage': token_usage
            }
            yield f"data: {json.dumps(complete_data)}\n\n"

        finally:
            if user_id in _active_refreshes:
                del _active_refreshes[user_id]

    return StreamingResponse(generate_progress(), media_type="text/event-stream")


@router.get("/refresh/status")
async def get_refresh_status(user_id: str):
    """
    获取刷新状态

    Query:
        - user_id: 用户ID

    Returns:
        刷新状态
    """
    status = _active_refreshes.get(user_id)

    if not status:
        return {
            'is_active': False
        }

    return {
        'is_active': True,
        **status
    }
