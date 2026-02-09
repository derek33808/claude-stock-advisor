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
    strategy_service,
    cache_service,
)
from app.db.supabase import supabase, get_supabase
from app.db import supabase as db

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('cron', hour=17, minute=0, id='daily_recommendations')
async def daily_recommendations_job():
    """
    每日17:00自动生成推荐股票
    仅在交易日执行
    """
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Daily recommendations job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] ⏭️  Not a trading day, skipping recommendation generation")
        return

    try:
        # 生成推荐
        print("[Scheduler] 🔄 Generating daily recommendations...")
        start_time = datetime.now()
        recommendations = await strategy_service.generate_daily_recommendations(top_n=10)
        generation_time = (datetime.now() - start_time).total_seconds()
        print(f"[Scheduler] ✅ Generation completed in {generation_time:.2f}s")

        if not recommendations:
            error_msg = "Failed to generate recommendations - empty result"
            print(f"[Scheduler] ❌ {error_msg}")
            # TODO: 发送告警通知（可接入钉钉/企业微信/邮件）
            return

        # 保存到数据库
        today = datetime.now().strftime("%Y-%m-%d")
        await db.save_recommendations(today, recommendations)
        print(f"[Scheduler] 💾 Saved {len(recommendations)} recommendations to database")

        # 保存市场概览（带 fallback）
        market = eastmoney_service.get_market_indices_with_fallback()
        await db.save_market_overview(today, market)
        print("[Scheduler] 💾 Saved market overview")

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] ✅ Job completed successfully in {total_time:.2f}s")
        print(f"[Scheduler] Recommendations: {len(recommendations)} stocks")
        print(f"[Scheduler] ========================================")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] ❌ Job failed after {error_time:.2f}s")
        print(f"[Scheduler] Error: {type(e).__name__}: {str(e)}")
        print(f"[Scheduler] ========================================")
        # TODO: 发送告警通知（可接入钉钉/企业微信/邮件）
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


@scheduler.scheduled_job('cron', hour=17, minute=10, id='cache_warm')
async def cache_warm_job():
    """
    每日17:10 缓存预热
    在推荐生成(17:00)之后执行
    预热推荐股 + 自选股的完整分析缓存
    """
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Cache warm-up job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] ⏭️  Not a trading day, skipping cache warm-up")
        return

    try:
        codes = set()

        # 推荐股
        _, recs = await db.get_latest_recommendations()
        for rec in recs:
            codes.add(rec['code'])
        print(f"[Scheduler] 📋 Recommendations: {len(recs)} stocks")

        # 自选股
        sb = get_supabase()
        result = sb.table('watchlist').select('code').execute()
        watchlist_codes = set(item['code'] for item in result.data) if result.data else set()
        codes.update(watchlist_codes)
        print(f"[Scheduler] 📋 Watchlist: {len(watchlist_codes)} stocks (total unique: {len(codes)})")

        # 逐个分析并写入缓存（17:25前必须结束，避免与17:30快照重叠）
        from app.api.stock import _do_full_analysis
        success_count = 0
        failed_count = 0
        deadline = job_start_time.replace(hour=17, minute=25, second=0)

        for idx, code in enumerate(codes, 1):
            if datetime.now() > deadline:
                print(f"[Scheduler] ⏰ Deadline reached (17:25), stopping. Completed {idx-1}/{len(codes)}")
                break
            try:
                print(f"[Scheduler] 🔄 Warming cache {idx}/{len(codes)}: {code}")
                await _do_full_analysis(code, ai_analysis=False)
                success_count += 1
            except Exception as e:
                failed_count += 1
                print(f"[Scheduler] ❌ Cache warm failed for {code}: {e}")
                continue

        # 批量获取实时价格并更新内存缓存
        batch_quotes = eastmoney_service.get_batch_realtime(list(codes))
        cache_service.set_cached_quotes_batch(batch_quotes)

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] ✅ Cache warm-up completed in {total_time:.2f}s")
        print(f"[Scheduler] Success: {success_count}/{len(codes)}")
        if failed_count > 0:
            print(f"[Scheduler] ⚠️  Failed: {failed_count}/{len(codes)}")
        print(f"[Scheduler] ========================================")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ❌ Cache warm-up failed after {error_time:.2f}s: {e}")
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


@scheduler.scheduled_job('cron', hour=17, minute=30, id='daily_snapshot')
async def daily_snapshot_job():
    """
    每日17:30保存所有自选股的分析快照
    仅在交易日执行
    """
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Daily snapshot job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] ⏭️  Not a trading day, skipping snapshot")
        return

    try:
        # 获取所有用户的自选股
        print("[Scheduler] 📋 Fetching watchlist items...")
        result = supabase.table('watchlist').select('*').execute()

        if not result.data:
            print("[Scheduler] ℹ️  No watchlist items found")
            return

        total_items = len(result.data)
        print(f"[Scheduler] 📊 Found {total_items} watchlist items")

        saved_count = 0
        failed_count = 0

        for idx, item in enumerate(result.data, 1):
            try:
                print(f"[Scheduler] 🔄 Processing {idx}/{total_items}: {item['code']}")

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
                print(f"[Scheduler] ✅ Saved snapshot for {item['code']}")

            except Exception as e:
                failed_count += 1
                print(f"[Scheduler] ❌ Error saving snapshot for {item['code']}: {str(e)}")
                continue

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] ✅ Job completed in {total_time:.2f}s")
        print(f"[Scheduler] Success: {saved_count}/{total_items}")
        if failed_count > 0:
            print(f"[Scheduler] ⚠️  Failed: {failed_count}/{total_items}")
        print(f"[Scheduler] ========================================")


@scheduler.scheduled_job('cron', hour=18, minute=0, id='evaluation_job')
async def evaluation_job():
    """
    每日18:00评估5个交易日前的预测
    仅在交易日执行
    """
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Evaluation job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    # 仅在交易日执行
    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] ⏭️  Not a trading day, skipping evaluation")
        return

    try:
        # 计算5个交易日前的日期
        print("[Scheduler] 📅 Calculating evaluation date...")
        evaluation_date = trading_calendar.add_trading_days(date.today(), -5)

        if not evaluation_date:
            print("[Scheduler] ❌ Cannot calculate evaluation date")
            return

        print(f"[Scheduler] 📊 Evaluating predictions from {evaluation_date}")

        # 获取该日期的所有分析记录
        result = supabase.table('analysis_history') \
            .select('*') \
            .eq('analysis_date', str(evaluation_date)) \
            .execute()

        if not result.data:
            print(f"[Scheduler] ℹ️  No analyses found for {evaluation_date}")
            return

        total_analyses = len(result.data)
        print(f"[Scheduler] 📋 Found {total_analyses} analyses to evaluate")

        evaluated_count = 0
        failed_count = 0

        for idx, analysis in enumerate(result.data, 1):
            try:
                print(f"[Scheduler] 🔄 Evaluating {idx}/{total_analyses}: {analysis['code']}")

                # 评估预测
                await prediction_tracking_service.evaluate_prediction(analysis['id'])
                evaluated_count += 1
                print(f"[Scheduler] ✅ Evaluated {analysis['code']}")

            except Exception as e:
                failed_count += 1
                print(f"[Scheduler] ❌ Error evaluating {analysis['id']}: {str(e)}")
                continue

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] ✅ Job completed in {total_time:.2f}s")
        print(f"[Scheduler] Success: {evaluated_count}/{total_analyses}")
        if failed_count > 0:
            print(f"[Scheduler] ⚠️  Failed: {failed_count}/{total_analyses}")
        print(f"[Scheduler] ========================================")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] ❌ Job failed after {error_time:.2f}s")
        print(f"[Scheduler] Error: {type(e).__name__}: {str(e)}")
        print(f"[Scheduler] ========================================")
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


def start_scheduler():
    """启动调度器"""
    scheduler.start()
    print("[Scheduler] Started")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    print("[Scheduler] Stopped")
