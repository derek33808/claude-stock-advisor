"""
预测追踪服务
保存每日分析快照，5天后评估预测准确度
"""

from datetime import date, datetime
from typing import Dict, Optional
from app.db.supabase import supabase
from app.services.trading_calendar_service import trading_calendar
from app.services import eastmoney_service


async def save_daily_snapshot(code: str, user_id: str, analysis: Dict) -> Dict:
    """
    保存每日分析快照

    Args:
        code: 股票代码
        user_id: 用户ID
        analysis: 综合分析结果

    Returns:
        保存结果
    """
    try:
        snapshot = {
            'code': code,
            'analysis_date': str(date.today()),
            'analysis_time': datetime.now().strftime('%H:%M:%S'),
            'price': analysis['quote']['price'],
            'change_percent': analysis['quote']['change'],
            'prediction_direction': analysis['comprehensive_summary'].get('action', '观望'),
            'prediction_text': analysis['technical_analysis'].get('prediction', ''),
            'target_price_low': analysis['trading_suggestion'].get('buy_price_low', 0),
            'target_price_high': analysis['trading_suggestion'].get('take_profit_2', 0),
            'analysis_content': analysis,
            'created_at': datetime.now().isoformat()
        }

        result = supabase.table('analysis_history').insert(snapshot).execute()

        return {
            'success': True,
            'snapshot_id': result.data[0]['id'] if result.data else None
        }

    except Exception as e:
        print(f"Error saving snapshot: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def evaluate_prediction(analysis_id: str) -> Optional[Dict]:
    """
    评估5天前的预测

    Args:
        analysis_id: 分析记录ID

    Returns:
        评估结果
    """
    try:
        # 获取分析记录
        analysis = supabase.table('analysis_history').select('*').eq('id', analysis_id).single().execute()

        if not analysis.data:
            return None

        record = analysis.data

        # 计算5个交易日后的日期
        analysis_date = date.fromisoformat(record['analysis_date'])
        evaluation_date = trading_calendar.add_trading_days(analysis_date, 5)

        if not evaluation_date:
            return None

        # 获取5天后的实际价格
        actual_price = await _get_price_on_date(record['code'], evaluation_date)

        if not actual_price:
            return None

        # 计算价格变化
        original_price = record['price']
        price_change = (actual_price - original_price) / original_price * 100

        # 判断方向准确性
        predicted_direction = record['prediction_direction']
        is_direction_correct = (
            (predicted_direction == '买入' and price_change > 0) or
            (predicted_direction == '卖出' and price_change < 0) or
            (predicted_direction == '观望' and abs(price_change) < 2)
        )

        # 判断目标价准确性
        target_low = record.get('target_price_low', 0)
        target_high = record.get('target_price_high', 0)
        is_target_reached = (target_low <= actual_price <= target_high) if target_low and target_high else False

        # 综合准确度分数 (0-100)
        accuracy_score = _calculate_accuracy_score(
            is_direction_correct,
            is_target_reached,
            abs(price_change)
        )

        # 保存评估结果
        evaluation = {
            'analysis_id': analysis_id,
            'evaluation_date': str(evaluation_date),
            'actual_price': actual_price,
            'price_change_percent': round(price_change, 2),
            'is_direction_correct': is_direction_correct,
            'is_target_reached': is_target_reached,
            'accuracy_score': accuracy_score,
            'evaluation_note': f"预测{predicted_direction}，实际{'上涨' if price_change > 0 else '下跌'}{abs(price_change):.2f}%",
            'created_at': datetime.now().isoformat()
        }

        result = supabase.table('prediction_tracking').insert(evaluation).execute()

        return evaluation

    except Exception as e:
        print(f"Error evaluating prediction: {e}")
        return None


async def _get_price_on_date(code: str, target_date: date) -> Optional[float]:
    """获取指定日期的收盘价"""
    try:
        # 获取历史数据
        history = eastmoney_service.get_history(code, days=10)

        if history is None or history.empty:
            return None

        # 查找目标日期的数据
        target_data = history[history['date'].dt.date == target_date]

        if not target_data.empty:
            return float(target_data.iloc[0]['close'])

        return None

    except Exception as e:
        print(f"Error getting price on date: {e}")
        return None


def _calculate_accuracy_score(
    is_direction_correct: bool,
    is_target_reached: bool,
    price_change_abs: float
) -> float:
    """
    计算准确度分数

    Args:
        is_direction_correct: 方向是否正确
        is_target_reached: 是否达到目标价
        price_change_abs: 价格变化绝对值

    Returns:
        准确度分数 (0-100)
    """
    score = 0

    # 方向准确性 (50分)
    if is_direction_correct:
        score += 50

    # 目标价准确性 (30分)
    if is_target_reached:
        score += 30

    # 价格变化幅度 (20分)
    if price_change_abs > 10:
        score += 20
    elif price_change_abs > 5:
        score += 15
    elif price_change_abs > 2:
        score += 10

    return score
