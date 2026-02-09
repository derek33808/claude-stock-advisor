"""
定时任务调度器
每日自动生成推荐、保存自选股快照、评估预测
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date, datetime
from app.services.trading_calendar_service import trading_calendar
from app.services import (
    watchlist_service,
    prediction_tracking_service,
    comprehensive_analysis_service,
    eastmoney_service,
    strategy_service
)
from app.db.supabase import supabase
from app.db import supabase as db

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('cron', hour=17, minute=0, id='daily_recommendations')
async def daily_recommendations_job():
    """
    每日17:00自动生成推荐股票
    仅在交易日执行
    """
    print(f"[Scheduler] Daily recommendations job started at {date.today()}")

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping recommendation generation")
        return

    try:
        # 生成推荐
        recommendations = await strategy_service.generate_daily_recommendations(top_n=10)

        if not recommendations:
            print("[Scheduler] Failed to generate recommendations")
            return

        # 保存到数据库
        today = datetime.now().strftime("%Y-%m-%d")
        await db.save_recommendations(today, recommendations)
        print(f"[Scheduler] Saved {len(recommendations)} recommendations")

        # 保存市场概览（带 fallback）
        market = eastmoney_service.get_market_indices_with_fallback()
        await db.save_market_overview(today, market)
        print("[Scheduler] Saved market overview")

        print(f"[Scheduler] Daily recommendations job completed successfully")

    except Exception as e:
        print(f"[Scheduler] Daily recommendations job failed: {e}")


@scheduler.scheduled_job('cron', hour=17, minute=30, id='daily_snapshot')
async def daily_snapshot_job():
    """
    每日17:30保存所有自选股的分析快照
    仅在交易日执行
    """
    print(f"[Scheduler] Daily snapshot job started at {date.today()}")

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping snapshot")
        return

    try:
        # 获取所有用户的自选股
        result = supabase.table('watchlist').select('*').execute()

        if not result.data:
            print("[Scheduler] No watchlist items found")
            return

        saved_count = 0
        for item in result.data:
            try:
                # 生成综合分析
                analysis = await comprehensive_analysis_service.generate_comprehensive_analysis(
                    item['code']
                )

                # 保存快照
                await prediction_tracking_service.save_daily_snapshot(
                    code=item['code'],
                    user_id=item['user_id'],
                    analysis=analysis
                )

                saved_count += 1

            except Exception as e:
                print(f"[Scheduler] Error saving snapshot for {item['code']}: {e}")
                continue

        print(f"[Scheduler] Saved {saved_count} snapshots")

    except Exception as e:
        print(f"[Scheduler] Daily snapshot job failed: {e}")


@scheduler.scheduled_job('cron', hour=18, minute=0, id='evaluation_job')
async def evaluation_job():
    """
    每日18:00评估5个交易日前的预测
    仅在交易日执行
    """
    print(f"[Scheduler] Evaluation job started at {date.today()}")

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping evaluation")
        return

    try:
        # 计算5个交易日前的日期
        evaluation_date = trading_calendar.add_trading_days(date.today(), -5)

        if not evaluation_date:
            print("[Scheduler] Cannot calculate evaluation date")
            return

        # 获取该日期的所有分析记录
        result = supabase.table('analysis_history') \
            .select('*') \
            .eq('analysis_date', str(evaluation_date)) \
            .execute()

        if not result.data:
            print(f"[Scheduler] No analyses found for {evaluation_date}")
            return

        evaluated_count = 0
        for analysis in result.data:
            try:
                # 评估预测
                await prediction_tracking_service.evaluate_prediction(analysis['id'])
                evaluated_count += 1

            except Exception as e:
                print(f"[Scheduler] Error evaluating {analysis['id']}: {e}")
                continue

        print(f"[Scheduler] Evaluated {evaluated_count} predictions")

    except Exception as e:
        print(f"[Scheduler] Evaluation job failed: {e}")


def start_scheduler():
    """启动调度器"""
    scheduler.start()
    print("[Scheduler] Started")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    print("[Scheduler] Stopped")
