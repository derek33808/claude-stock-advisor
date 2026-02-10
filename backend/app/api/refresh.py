"""
全局刷新 API 端点（SSE）
优化：并行刷新 + Semaphore 限制并发
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime
import json
import asyncio
from app.services import (
    comprehensive_analysis_service,
    token_monitor_service,
    strategy_service,
    eastmoney_service
)
from app.db import supabase as db

router = APIRouter()

# 并发保护
_active_refreshes = {}


class RefreshAllRequest(BaseModel):
    user_id: str
    codes: Optional[List[str]] = None
    include_recommendations: bool = False
    include_watchlist: bool = False
    timeout_seconds: int = 600


@router.post("/refresh/all")
async def refresh_all(data: RefreshAllRequest):
    """
    全局刷新（SSE）
    使用 asyncio.gather + Semaphore(3) 并行刷新股票
    """
    user_id = data.user_id
    codes = data.codes or []
    include_recommendations = data.include_recommendations
    include_watchlist = data.include_watchlist
    timeout_seconds = data.timeout_seconds

    async def generate_progress():
        start_time = datetime.now()

        if user_id in _active_refreshes:
            yield f"data: {json.dumps({'event': 'error', 'message': '刷新进行中，请稍候'})}\n\n"
            return

        _active_refreshes[user_id] = {'status': 'running', 'progress': 0, 'start_time': start_time}

        try:
            tasks_completed = 0
            total_tasks = 0

            if include_recommendations:
                total_tasks += 1
            if include_watchlist or codes:
                if include_watchlist and not codes:
                    from app.db.supabase import supabase
                    result = supabase.table('watchlist').select('code').eq('user_id', user_id).execute()
                    codes[:] = [item['code'] for item in result.data] if result.data else []
                total_tasks += len(codes)

            if total_tasks == 0:
                yield f"data: {json.dumps({'event': 'error', 'message': '没有需要刷新的内容'})}\n\n"
                return

            # 步骤1: 生成推荐（如果需要）
            if include_recommendations:
                try:
                    yield f"data: {json.dumps({'event': 'progress', 'phase': 'recommendations', 'current': '正在生成推荐...', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"

                    recommendations = await strategy_service.generate_daily_recommendations(top_n=10)

                    if recommendations:
                        today = datetime.now().strftime("%Y-%m-%d")
                        await db.save_recommendations(today, recommendations)

                        market = await eastmoney_service.get_market_indices_with_fallback()
                        await db.save_market_overview(today, market)

                    tasks_completed += 1
                    yield f"data: {json.dumps({'event': 'progress', 'phase': 'recommendations_done', 'current': f'推荐生成完成 ({len(recommendations)}支)', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"

                except Exception as e:
                    print(f"Error generating recommendations: {e}")
                    yield f"data: {json.dumps({'event': 'warning', 'message': f'推荐生成失败: {str(e)}'})}\n\n"

            # 步骤2: 并行刷新股票（带中间进度推送）
            if codes:
                semaphore = asyncio.Semaphore(3)
                progress_queue = asyncio.Queue()

                async def _refresh_one(stock_code: str) -> Tuple[str, bool]:
                    async with semaphore:
                        try:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            if elapsed > timeout_seconds:
                                await progress_queue.put((stock_code, False, '超时跳过'))
                                return stock_code, False

                            await comprehensive_analysis_service.generate_comprehensive_analysis(stock_code)
                            await progress_queue.put((stock_code, True, None))
                            return stock_code, True
                        except Exception as e:
                            print(f"Error refreshing {stock_code}: {e}")
                            await progress_queue.put((stock_code, False, str(e)))
                            return stock_code, False

                # 启动并行刷新任务
                # asyncio.gather 返回 Future（非 coroutine），不能传给 create_task
                gather_future = asyncio.gather(*[_refresh_one(c) for c in codes])

                # 实时消费进度队列，推送 SSE 事件
                finished = 0
                while finished < len(codes):
                    try:
                        stock_code, success, error = await asyncio.wait_for(
                            progress_queue.get(), timeout=120
                        )
                        finished += 1
                        if success:
                            tasks_completed += 1
                        yield f"data: {json.dumps({'event': 'progress', 'phase': 'stocks', 'current': f'已完成 {stock_code} ({finished}/{len(codes)})', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'event': 'progress', 'phase': 'stocks', 'current': f'处理中... ({finished}/{len(codes)})', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"

                # 确保 gather 完成
                await gather_future

                yield f"data: {json.dumps({'event': 'progress', 'phase': 'stocks_done', 'current': f'股票刷新完成 ({tasks_completed - (1 if include_recommendations else 0)}/{len(codes)})', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"

            # 获取 Token 使用情况
            token_usage = await token_monitor_service.token_monitor.check_limit()

            complete_data = {
                'event': 'complete',
                'completed': tasks_completed,
                'total': total_tasks,
                'recommendations_generated': include_recommendations,
                'stocks_refreshed': len(codes),
                'token_usage': token_usage
            }
            yield f"data: {json.dumps(complete_data)}\n\n"

        except Exception as e:
            error_data = {
                'event': 'error',
                'message': f'刷新失败: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"

        finally:
            if user_id in _active_refreshes:
                del _active_refreshes[user_id]

    return StreamingResponse(generate_progress(), media_type="text/event-stream")


@router.get("/refresh/status")
async def get_refresh_status(user_id: str = Query(..., description="用户ID")):
    """获取刷新状态"""
    status = _active_refreshes.get(user_id)

    if not status:
        return {
            'is_active': False
        }

    return {
        'is_active': True,
        **status
    }
