"""
自选股管理服务
"""

from typing import List, Dict, Optional
from datetime import datetime
from app.db.supabase import supabase


async def add_to_watchlist(user_id: str, code: str, name: str) -> Dict:
    """
    添加到自选股

    Args:
        user_id: 用户ID
        code: 股票代码
        name: 股票名称

    Returns:
        添加结果
    """
    try:
        # 检查是否已存在
        existing = supabase.table('watchlist').select('*').eq('user_id', user_id).eq('code', code).execute()

        if existing.data and len(existing.data) > 0:
            return {
                'success': False,
                'message': '已在自选股中'
            }

        # 插入新记录
        result = supabase.table('watchlist').insert({
            'user_id': user_id,
            'code': code,
            'name': name,
            'added_at': datetime.now().isoformat()
        }).execute()

        return {
            'success': True,
            'message': '添加成功',
            'data': result.data[0] if result.data else None
        }

    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return {
            'success': False,
            'message': str(e)
        }


async def remove_from_watchlist(user_id: str, code: str) -> Dict:
    """移除自选股"""
    try:
        result = supabase.table('watchlist').delete().eq('user_id', user_id).eq('code', code).execute()

        return {
            'success': True,
            'message': '移除成功'
        }

    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return {
            'success': False,
            'message': str(e)
        }


async def get_watchlist(user_id: str) -> List[Dict]:
    """
    获取自选股列表

    Returns:
        自选股列表（包含当前行情）
    """
    try:
        result = supabase.table('watchlist').select('*').eq('user_id', user_id).execute()

        if not result.data:
            return []

        return result.data

    except Exception as e:
        print(f"Error getting watchlist: {e}")
        return []


async def is_in_watchlist(user_id: str, code: str) -> bool:
    """检查是否在自选股中"""
    try:
        result = supabase.table('watchlist').select('*').eq('user_id', user_id).eq('code', code).execute()

        return bool(result.data and len(result.data) > 0)

    except Exception as e:
        print(f"Error checking watchlist: {e}")
        return False
