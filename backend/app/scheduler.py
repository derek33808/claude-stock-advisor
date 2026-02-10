"""
定时任务调度器
每日自动生成推荐、保存自选股快照、评估预测
修复：移除 asyncio.new_event_loop() 反模式，使用直接 gather
"""

import asyncio
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
    """每日17:00自动生成推荐股票"""
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Daily recommendations job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping recommendation generation")
        return

    try:
        print("[Scheduler] Generating daily recommendations...")
        start_time = datetime.now()
        recommendations = await strategy_service.generate_daily_recommendations(top_n=10)
        generation_time = (datetime.now() - start_time).total_seconds()
        print(f"[Scheduler] Generation completed in {generation_time:.2f}s")

        if not recommendations:
            print("[Scheduler] Failed to generate recommendations - empty result")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        await db.save_recommendations(today, recommendations)
        print(f"[Scheduler] Saved {len(recommendations)} recommendations to database")

        market = await eastmoney_service.get_market_indices_with_fallback()
        await db.save_market_overview(today, market)
        print("[Scheduler] Saved market overview")

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] Job completed successfully in {total_time:.2f}s")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] Job failed after {error_time:.2f}s: {e}")
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


@scheduler.scheduled_job('cron', hour=17, minute=10, id='cache_warm')
async def cache_warm_job():
    """
    每日17:10 缓存预热
    使用 asyncio.gather + Semaphore 直接在主事件循环中并行
    """
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Cache warm-up job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping cache warm-up")
        return

    try:
        codes = set()

        # 推荐股
        _, recs = await db.get_latest_recommendations()
        for rec in recs:
            codes.add(rec['code'])
        print(f"[Scheduler] Recommendations: {len(recs)} stocks")

        # 自选股
        sb = get_supabase()
        result = sb.table('watchlist').select('code').execute()
        watchlist_codes = set(item['code'] for item in result.data) if result.data else set()
        codes.update(watchlist_codes)
        print(f"[Scheduler] Watchlist: {len(watchlist_codes)} stocks (total unique: {len(codes)})")

        # 直接在主事件循环中并行分析（不再创建新的事件循环）
        from app.api.stock import _do_full_analysis
        deadline = job_start_time.replace(hour=17, minute=25, second=0)

        semaphore = asyncio.Semaphore(3)

        async def _warm_one(stock_code: str) -> bool:
            if datetime.now() > deadline:
                return False
            async with semaphore:
                try:
                    await _do_full_analysis(stock_code, ai_analysis=False, skip_ai_summary=True)
                    print(f"[Scheduler] Warmed cache: {stock_code}")
                    return True
                except Exception as e:
                    print(f"[Scheduler] Cache warm failed for {stock_code}: {e}")
                    return False

        code_list = list(codes)
        print(f"[Scheduler] Warming cache for {len(code_list)} stocks (parallel, max 3)...")
        warm_results = await asyncio.gather(*[_warm_one(c) for c in code_list])
        success_count = sum(1 for r in warm_results if r)
        failed_count = sum(1 for r in warm_results if not r)

        # 批量获取实时价格并更新内存缓存
        batch_quotes = await eastmoney_service.get_batch_realtime(list(codes))
        cache_service.set_cached_quotes_batch(batch_quotes)

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] Cache warm-up completed in {total_time:.2f}s")
        print(f"[Scheduler] Success: {success_count}/{len(codes)}")
        if failed_count > 0:
            print(f"[Scheduler] Failed: {failed_count}/{len(codes)}")
        print(f"[Scheduler] ========================================")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] Cache warm-up failed after {error_time:.2f}s: {e}")
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


@scheduler.scheduled_job('cron', hour=17, minute=30, id='daily_snapshot')
async def daily_snapshot_job():
    """每日17:30保存所有自选股的分析快照"""
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Daily snapshot job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping snapshot")
        return

    try:
        print("[Scheduler] Fetching watchlist items...")
        result = supabase.table('watchlist').select('*').execute()

        if not result.data:
            print("[Scheduler] No watchlist items found")
            return

        total_items = len(result.data)
        print(f"[Scheduler] Found {total_items} watchlist items")

        saved_count = 0
        failed_count = 0

        for idx, item in enumerate(result.data, 1):
            try:
                print(f"[Scheduler] Processing {idx}/{total_items}: {item['code']}")

                analysis = await comprehensive_analysis_service.generate_comprehensive_analysis(
                    item['code']
                )

                await prediction_tracking_service.save_daily_snapshot(
                    code=item['code'],
                    user_id=item['user_id'],
                    analysis=analysis
                )

                saved_count += 1
                print(f"[Scheduler] Saved snapshot for {item['code']}")

            except Exception as e:
                failed_count += 1
                print(f"[Scheduler] Error saving snapshot for {item['code']}: {str(e)}")
                continue

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] Job completed in {total_time:.2f}s")
        print(f"[Scheduler] Success: {saved_count}/{total_items}")
        if failed_count > 0:
            print(f"[Scheduler] Failed: {failed_count}/{total_items}")
        print(f"[Scheduler] ========================================")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] Snapshot job failed after {error_time:.2f}s: {e}")
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


@scheduler.scheduled_job('cron', hour=18, minute=0, id='evaluation_job')
async def evaluation_job():
    """每日18:00评估5个交易日前的预测"""
    job_start_time = datetime.now()
    print(f"[Scheduler] ========================================")
    print(f"[Scheduler] Evaluation job started")
    print(f"[Scheduler] Date: {date.today()}, Time: {job_start_time.strftime('%H:%M:%S')}")
    print(f"[Scheduler] ========================================")

    if not trading_calendar.is_trading_day(date.today()):
        print("[Scheduler] Not a trading day, skipping evaluation")
        return

    try:
        print("[Scheduler] Calculating evaluation date...")
        evaluation_date = trading_calendar.add_trading_days(date.today(), -5)

        if not evaluation_date:
            print("[Scheduler] Cannot calculate evaluation date")
            return

        print(f"[Scheduler] Evaluating predictions from {evaluation_date}")

        result = supabase.table('analysis_history') \
            .select('*') \
            .eq('analysis_date', str(evaluation_date)) \
            .execute()

        if not result.data:
            print(f"[Scheduler] No analyses found for {evaluation_date}")
            return

        total_analyses = len(result.data)
        print(f"[Scheduler] Found {total_analyses} analyses to evaluate")

        evaluated_count = 0
        failed_count = 0

        for idx, analysis in enumerate(result.data, 1):
            try:
                print(f"[Scheduler] Evaluating {idx}/{total_analyses}: {analysis['code']}")

                await prediction_tracking_service.evaluate_prediction(analysis['id'])
                evaluated_count += 1
                print(f"[Scheduler] Evaluated {analysis['code']}")

            except Exception as e:
                failed_count += 1
                print(f"[Scheduler] Error evaluating {analysis['id']}: {str(e)}")
                continue

        total_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] ========================================")
        print(f"[Scheduler] Job completed in {total_time:.2f}s")
        print(f"[Scheduler] Success: {evaluated_count}/{total_analyses}")
        if failed_count > 0:
            print(f"[Scheduler] Failed: {failed_count}/{total_analyses}")
        print(f"[Scheduler] ========================================")

    except Exception as e:
        error_time = (datetime.now() - job_start_time).total_seconds()
        print(f"[Scheduler] Job failed after {error_time:.2f}s: {e}")
        import traceback
        print(f"[Scheduler] Stack trace:\n{traceback.format_exc()}")


@scheduler.scheduled_job('interval', minutes=13, id='keep_alive')
async def keep_alive_job():
    """
    每13分钟自我ping，防止Render免费版15分钟休眠。
    比GitHub Actions cron更可靠（GA cron不保证精确执行）。
    """
    try:
        from app.http_client import get_client
        client = get_client()
        resp = await client.get("https://stock-advisor-api-6vtb.onrender.com/health", timeout=10)
        print(f"[Keep-Alive] Ping OK - status {resp.status_code}")
    except Exception as e:
        print(f"[Keep-Alive] Ping failed: {e}")


def start_scheduler():
    """启动调度器"""
    scheduler.start()
    print("[Scheduler] Started (includes keep-alive every 13min)")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    print("[Scheduler] Stopped")
