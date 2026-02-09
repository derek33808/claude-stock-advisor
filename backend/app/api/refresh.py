"""
全局刷新 API 端点（SSE）
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
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
    codes: Optional[List[str]] = None  # 可选，如果为空则从watchlist获取
    include_recommendations: bool = False  # 是否生成推荐
    include_watchlist: bool = False  # 是否包含自选股
    timeout_seconds: int = 600  # 超时时间（秒），默认10分钟


@router.post("/refresh/all")
async def refresh_all(data: RefreshAllRequest):
    """
    全局刷新（SSE）

    Body:
        - user_id: 用户ID
        - codes: 股票代码列表（可选，为空时从watchlist获取）
        - include_recommendations: 是否生成推荐（默认False）
        - include_watchlist: 是否包含自选股（默认False）

    Returns:
        SSE 流，实时返回刷新进度
    """
    user_id = data.user_id
    codes = data.codes or []
    include_recommendations = data.include_recommendations
    include_watchlist = data.include_watchlist
    timeout_seconds = data.timeout_seconds

    async def generate_progress():
        start_time = datetime.now()

        # 检查并发保护
        if user_id in _active_refreshes:
            yield f"data: {json.dumps({'event': 'error', 'message': '刷新进行中，请稍候'})}\n\n"
            return

        _active_refreshes[user_id] = {'status': 'running', 'progress': 0, 'start_time': start_time}

        try:
            tasks_completed = 0
            total_tasks = 0

            # 计算总任务数
            if include_recommendations:
                total_tasks += 1
            if include_watchlist or codes:
                # 如果需要从watchlist获取codes
                if include_watchlist and not codes:
                    from app.db.supabase import supabase
                    result = supabase.table('watchlist').select('code').eq('user_id', user_id).execute()
                    codes = [item['code'] for item in result.data] if result.data else []
                total_tasks += len(codes)

            if total_tasks == 0:
                yield f"data: {json.dumps({'event': 'error', 'message': '没有需要刷新的内容'})}\n\n"
                return

            # 步骤1: 生成推荐（如果需要）
            if include_recommendations:
                try:
                    yield f"data: {json.dumps({'event': 'progress', 'phase': 'recommendations', 'current': '正在生成推荐...', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"

                    # 生成推荐
                    recommendations = await strategy_service.generate_daily_recommendations(top_n=10)

                    if recommendations:
                        # 保存到数据库
                        today = datetime.now().strftime("%Y-%m-%d")
                        await db.save_recommendations(today, recommendations)

                        # 保存市场概览
                        market = eastmoney_service.get_market_indices_with_fallback()
                        await db.save_market_overview(today, market)

                    tasks_completed += 1
                    yield f"data: {json.dumps({'event': 'progress', 'phase': 'recommendations_done', 'current': f'推荐生成完成 ({len(recommendations)}支)', 'progress': int(tasks_completed / total_tasks * 100), 'completed': tasks_completed, 'total': total_tasks})}\n\n"

                except Exception as e:
                    print(f"Error generating recommendations: {e}")
                    yield f"data: {json.dumps({'event': 'warning', 'message': f'推荐生成失败: {str(e)}'})}\n\n"

            # 步骤2: 刷新股票（如果有codes）
            if codes:
                for idx, code in enumerate(codes):
                    # 超时检查
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > timeout_seconds:
                        yield f"data: {json.dumps({'event': 'timeout', 'message': f'操作超时（{elapsed:.0f}s > {timeout_seconds}s），已处理 {tasks_completed}/{total_tasks}', 'completed': tasks_completed, 'total': total_tasks})}\n\n"
                        return

                    try:
                        # 刷新单只股票
                        await comprehensive_analysis_service.generate_comprehensive_analysis(code)
                        tasks_completed += 1

                        # 发送进度
                        progress = {
                            'event': 'progress',
                            'phase': 'stocks',
                            'progress': int(tasks_completed / total_tasks * 100),
                            'current': f'正在分析 {code}... ({idx+1}/{len(codes)})',
                            'completed': tasks_completed,
                            'total': total_tasks
                        }
                        yield f"data: {json.dumps(progress)}\n\n"

                        # Heartbeat (每3只股票)
                        if (idx + 1) % 3 == 0:
                            yield f": heartbeat\n\n"

                        # 短暂延迟，避免过快
                        await asyncio.sleep(0.1)

                    except Exception as e:
                        print(f"Error refreshing {code}: {e}")
                        # 部分失败不中断整体流程
                        continue

            # 获取 Token 使用情况
            token_usage = await token_monitor_service.token_monitor.check_limit()

            # 完成
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
