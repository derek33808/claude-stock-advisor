"""
分析历史记录服务
查询历史分析记录，计算准确率统计
"""

from typing import List, Dict, Optional
from datetime import date, timedelta
from app.db.supabase import supabase


async def get_stock_history(code: str, user_id: str, days: int = 30) -> List[Dict]:
    """
    获取股票历史分析记录

    Args:
        code: 股票代码
        user_id: 用户ID
        days: 天数

    Returns:
        历史记录列表（包含评估结果）
    """
    try:
        start_date = str(date.today() - timedelta(days=days))

        # 查询分析历史
        result = supabase.table('analysis_history') \
            .select('*, prediction_tracking(*)') \
            .eq('code', code) \
            .gte('analysis_date', start_date) \
            .order('analysis_date', desc=True) \
            .execute()

        if not result.data:
            return []

        records = []
        for item in result.data:
            # 关联评估结果
            evaluation = None
            if item.get('prediction_tracking') and len(item['prediction_tracking']) > 0:
                evaluation = item['prediction_tracking'][0]

            records.append({
                **item,
                'evaluation': evaluation
            })

        return records

    except Exception as e:
        print(f"Error getting stock history: {e}")
        return []


async def get_accuracy_stats(code: str, user_id: str) -> Dict:
    """
    获取预测准确率统计

    Args:
        code: 股票代码
        user_id: 用户ID

    Returns:
        准确率统计
    """
    try:
        # 查询所有已评估的记录
        result = supabase.table('prediction_tracking') \
            .select('*, analysis_history!inner(code)') \
            .eq('analysis_history.code', code) \
            .execute()

        if not result.data:
            return {
                'total_predictions': 0,
                'correct_count': 0,
                'accuracy_rate': 0,
                'avg_accuracy_score': 0
            }

        evaluations = result.data
        total = len(evaluations)
        correct = sum(1 for e in evaluations if e.get('is_direction_correct'))
        avg_score = sum(e.get('accuracy_score', 0) for e in evaluations) / total if total > 0 else 0

        return {
            'total_predictions': total,
            'correct_count': correct,
            'accuracy_rate': round(correct / total, 3) if total > 0 else 0,
            'avg_accuracy_score': round(avg_score, 1)
        }

    except Exception as e:
        print(f"Error getting accuracy stats: {e}")
        return {
            'total_predictions': 0,
            'correct_count': 0,
            'accuracy_rate': 0,
            'avg_accuracy_score': 0
        }
