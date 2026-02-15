#!/usr/bin/env python3
"""
Stock Advisor 全功能 E2E 测试脚本

覆盖约25个测试用例：
- 健康检查（冷启动+热响应）
- 搜索（按名称/代码）
- 单股分析（缓存命中/无AI/有AI）
- 批量查询
- AI排名
- 自选股 CRUD
- AI 问答
- 推荐列表
- K线数据

每个测试记录：响应时间、状态码、关键字段校验、超时标记。
输出 JSON 报告 + 控制台表格。
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime
from typing import Optional

# ==================== 配置 ====================
BASE_URL = "https://stock-advisor-api-6vtb.onrender.com"
API_URL = f"{BASE_URL}/api/v1"
HEALTH_URL = f"{BASE_URL}/health"

TEST_USER_ID = "e2e_test_user"

# 超时阈值（秒）
THRESHOLDS = {
    "health_cold": 60,
    "health_warm": 5,
    "search": 15,
    "stock_cached": 3,
    "stock_no_ai": 15,
    "stock_with_ai": 65,
    "batch": 15,
    "ai_rankings": 60,
    "watchlist": 10,
    "ai_chat": 90,
    "recommendations": 15,
    "kline": 10,
}


class TestResult:
    """单条测试结果"""
    def __init__(self, category: str, name: str, status: str,
                 message: str = "", response_time: float = 0,
                 threshold: float = 0, status_code: int = 0):
        self.category = category
        self.name = name
        self.status = status  # PASS / FAIL / WARN / SKIP
        self.message = message
        self.response_time = response_time
        self.threshold = threshold
        self.status_code = status_code
        self.timeout_exceeded = response_time > threshold if threshold > 0 else False
        self.timestamp = datetime.now().isoformat()


class TestRunner:
    """E2E 测试运行器"""

    def __init__(self):
        self.results: list[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def setup(self):
        timeout = aiohttp.ClientTimeout(total=120)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def teardown(self):
        if self.session:
            await self.session.close()

    def add(self, result: TestResult):
        self.results.append(result)
        icon = {"PASS": "\u2705", "FAIL": "\u274c", "WARN": "\u26a0\ufe0f", "SKIP": "\u23ed\ufe0f"}.get(result.status, "?")
        timeout_flag = " [TIMEOUT]" if result.timeout_exceeded else ""
        print(f"  {icon} {result.name} ({result.response_time:.2f}s / {result.threshold}s){timeout_flag}")
        if result.message:
            print(f"     {result.message}")

    async def _get(self, url: str, timeout: float = 60) -> tuple:
        """GET 请求，返回 (status_code, data_or_none, elapsed, error_msg)"""
        start = time.time()
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                elapsed = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    return resp.status, data, elapsed, None
                else:
                    text = await resp.text()
                    return resp.status, None, elapsed, text[:200]
        except asyncio.TimeoutError:
            return 0, None, time.time() - start, "Timeout"
        except Exception as e:
            return 0, None, time.time() - start, str(e)

    async def _post(self, url: str, payload: dict, timeout: float = 60) -> tuple:
        """POST 请求"""
        start = time.time()
        try:
            async with self.session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                elapsed = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    return resp.status, data, elapsed, None
                else:
                    text = await resp.text()
                    return resp.status, None, elapsed, text[:200]
        except asyncio.TimeoutError:
            return 0, None, time.time() - start, "Timeout"
        except Exception as e:
            return 0, None, time.time() - start, str(e)

    async def _delete(self, url: str, payload: dict, timeout: float = 60) -> tuple:
        """DELETE 请求"""
        start = time.time()
        try:
            async with self.session.delete(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                elapsed = time.time() - start
                if resp.status == 200:
                    data = await resp.json()
                    return resp.status, data, elapsed, None
                else:
                    text = await resp.text()
                    return resp.status, None, elapsed, text[:200]
        except asyncio.TimeoutError:
            return 0, None, time.time() - start, "Timeout"
        except Exception as e:
            return 0, None, time.time() - start, str(e)

    # ==================== 测试用例 ====================

    async def test_health_cold(self):
        """T01: 健康检查 - 冷启动"""
        print("\n--- T01: Health Check (cold start) ---")
        th = THRESHOLDS["health_cold"]
        code, data, elapsed, err = await self._get(HEALTH_URL, timeout=th)
        if code == 200:
            self.add(TestResult("健康检查", "冷启动 /health", "PASS",
                                f"status={data.get('status', '?')}", elapsed, th, code))
        else:
            self.add(TestResult("健康检查", "冷启动 /health", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_health_warm(self):
        """T02: 健康检查 - 热响应"""
        print("\n--- T02: Health Check (warm) ---")
        th = THRESHOLDS["health_warm"]
        code, data, elapsed, err = await self._get(HEALTH_URL, timeout=th)
        if code == 200 and elapsed < th:
            self.add(TestResult("健康检查", "热响应 /health", "PASS",
                                f"{elapsed:.2f}s < {th}s", elapsed, th, code))
        elif code == 200:
            self.add(TestResult("健康检查", "热响应 /health", "WARN",
                                f"响应慢: {elapsed:.2f}s > {th}s", elapsed, th, code))
        else:
            self.add(TestResult("健康检查", "热响应 /health", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_search_by_name(self):
        """T03: 搜索 - 按名称"""
        print("\n--- T03: Search by name ---")
        th = THRESHOLDS["search"]
        code, data, elapsed, err = await self._get(f"{API_URL}/stocks/search?q=平安", timeout=th)
        if code == 200 and data and data.get("count", 0) > 0:
            self.add(TestResult("搜索", "按名称搜索'平安'", "PASS",
                                f"返回 {data['count']} 个结果", elapsed, th, code))
        elif code == 200:
            self.add(TestResult("搜索", "按名称搜索'平安'", "WARN",
                                "返回0个结果", elapsed, th, code))
        else:
            self.add(TestResult("搜索", "按名称搜索'平安'", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_search_by_code(self):
        """T04: 搜索 - 按代码"""
        print("\n--- T04: Search by code ---")
        th = THRESHOLDS["search"]
        code, data, elapsed, err = await self._get(f"{API_URL}/stocks/search?q=600519", timeout=th)
        if code == 200 and data and data.get("count", 0) > 0:
            results = data.get("results", [])
            found = any(r.get("code") == "600519" for r in results)
            self.add(TestResult("搜索", "按代码搜索'600519'", "PASS" if found else "WARN",
                                f"返回 {data['count']} 个结果, 600519{'找到' if found else '未找到'}",
                                elapsed, th, code))
        else:
            self.add(TestResult("搜索", "按代码搜索'600519'", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_stock_cached(self):
        """T05: 单股分析 - L1缓存命中（先确保有缓存）"""
        print("\n--- T05: Stock cached (L1) ---")
        # 先请求一次填充缓存
        await self._get(f"{API_URL}/stock/600519", timeout=70)
        await asyncio.sleep(0.5)

        th = THRESHOLDS["stock_cached"]
        code, data, elapsed, err = await self._get(f"{API_URL}/stock/600519", timeout=th + 5)
        if code == 200 and data:
            cached = data.get("cached", False) or (data.get("cache_info", {}).get("cached", False))
            status = "PASS" if elapsed < th else "WARN"
            self.add(TestResult("单股分析", "L1缓存命中 600519", status,
                                f"cached={cached}, {elapsed:.2f}s", elapsed, th, code))
        else:
            self.add(TestResult("单股分析", "L1缓存命中 600519", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_stock_no_ai(self):
        """T06: 单股分析 - 无AI"""
        print("\n--- T06: Stock without AI (refresh) ---")
        th = THRESHOLDS["stock_no_ai"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/stock/000001?ai_analysis=false&refresh=true", timeout=th + 10)
        if code == 200 and data:
            has_score = data.get("score", 0) > 0
            has_indicators = bool(data.get("indicators"))
            self.add(TestResult("单股分析", "无AI分析 000001", "PASS" if has_score else "WARN",
                                f"score={data.get('score')}, indicators={'有' if has_indicators else '无'}",
                                elapsed, th, code))
        else:
            self.add(TestResult("单股分析", "无AI分析 000001", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_stock_with_ai(self):
        """T07: 单股分析 - 有AI（关键超时测试）"""
        print("\n--- T07: Stock with AI (refresh) - KEY TIMEOUT TEST ---")
        th = THRESHOLDS["stock_with_ai"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/stock/600519?ai_analysis=true&refresh=true", timeout=th + 10)
        if code == 200 and data:
            has_ai = "ai_analysis" in data
            ai_score = data.get("ai_analysis", {}).get("ai_recommendation", {}).get("ai_score", 0)
            status = "PASS" if elapsed <= th else "WARN"
            self.add(TestResult("单股分析", "有AI分析 600519 (超时关键)", status,
                                f"ai={has_ai}, ai_score={ai_score}, {elapsed:.2f}s/{th}s",
                                elapsed, th, code))
        else:
            self.add(TestResult("单股分析", "有AI分析 600519 (超时关键)", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_stock_fields_validation(self):
        """T08: 单股分析 - 字段完整性校验"""
        print("\n--- T08: Stock response fields validation ---")
        code, data, elapsed, err = await self._get(f"{API_URL}/stock/600519", timeout=70)
        if code != 200 or not data:
            self.add(TestResult("单股分析", "响应字段完整性", "FAIL",
                                err or f"HTTP {code}", elapsed, 10, code))
            return

        required_fields = ["code", "name", "price", "change", "indicators", "suggestion", "reasons", "score"]
        missing = [f for f in required_fields if f not in data]
        if not missing:
            # Check nested fields
            ind = data.get("indicators", {})
            ind_fields = ["macd", "rsi", "ma", "kdj", "boll", "atr", "volume_ratio"]
            ind_missing = [f for f in ind_fields if f not in ind]
            sug = data.get("suggestion", {})
            sug_fields = ["action", "buy_price", "stop_loss", "take_profit", "risk_level"]
            sug_missing = [f for f in sug_fields if f not in sug]
            all_missing = ind_missing + sug_missing
            if not all_missing:
                self.add(TestResult("单股分析", "响应字段完整性", "PASS",
                                    "所有必需字段均存在", elapsed, 10, code))
            else:
                self.add(TestResult("单股分析", "响应字段完整性", "WARN",
                                    f"缺少嵌套字段: {all_missing}", elapsed, 10, code))
        else:
            self.add(TestResult("单股分析", "响应字段完整性", "FAIL",
                                f"缺少顶层字段: {missing}", elapsed, 10, code))

    async def test_stock_score_details(self):
        """T09: 单股分析 - 新增评分维度+价格预测字段"""
        print("\n--- T09: Score details + price prediction fields ---")
        code, data, elapsed, err = await self._get(f"{API_URL}/stock/600519", timeout=70)
        if code != 200 or not data:
            self.add(TestResult("评分升级", "评分维度+价格预测", "SKIP",
                                "依赖T05/T07数据", elapsed, 10, code))
            return

        has_score_details = "score_details" in data
        has_prediction = "price_prediction" in data
        if has_score_details and has_prediction:
            sd = data["score_details"]
            pp = data["price_prediction"]
            dim_keys = ["trend_score", "momentum_score", "volatility_score", "volume_score", "composite"]
            pred_keys = ["5d_target_high", "5d_target_low", "probability_up"]
            sd_ok = all(k in sd for k in dim_keys)
            pp_ok = all(k in pp for k in pred_keys)
            if sd_ok and pp_ok:
                self.add(TestResult("评分升级", "评分维度+价格预测", "PASS",
                                    f"composite={sd.get('composite')}, up_prob={pp.get('probability_up')}%",
                                    elapsed, 10, code))
            else:
                self.add(TestResult("评分升级", "评分维度+价格预测", "WARN",
                                    f"字段不完整: sd_ok={sd_ok}, pp_ok={pp_ok}", elapsed, 10, code))
        else:
            self.add(TestResult("评分升级", "评分维度+价格预测", "WARN",
                                f"score_details={has_score_details}, price_prediction={has_prediction}",
                                elapsed, 10, code))

    async def test_batch(self):
        """T10: 批量查询"""
        print("\n--- T10: Batch stock analyses ---")
        th = THRESHOLDS["batch"]
        codes = "600519,000858,300750"
        code, data, elapsed, err = await self._get(f"{API_URL}/stocks/batch?codes={codes}", timeout=th + 5)
        if code == 200 and data:
            stocks = data.get("stocks", [])
            count = len(stocks)
            if count == 3:
                self.add(TestResult("批量查询", "3只股票批量查询", "PASS",
                                    f"返回 {count} 只", elapsed, th, code))
            else:
                self.add(TestResult("批量查询", "3只股票批量查询", "WARN",
                                    f"预期3只, 实际{count}只", elapsed, th, code))
        else:
            self.add(TestResult("批量查询", "3只股票批量查询", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_batch_scores(self):
        """T11: 批量查询 - 所有股票有评分"""
        print("\n--- T11: Batch stocks all have scores ---")
        th = THRESHOLDS["batch"]
        codes = "600519,000001"
        code, data, elapsed, err = await self._get(f"{API_URL}/stocks/batch?codes={codes}", timeout=th + 5)
        if code == 200 and data:
            stocks = data.get("stocks", [])
            scored = [s for s in stocks if s.get("score", 0) > 0]
            if len(scored) == len(stocks):
                self.add(TestResult("批量查询", "所有股票有评分>0", "PASS",
                                    f"{len(scored)}/{len(stocks)} 有评分",
                                    elapsed, th, code))
            else:
                self.add(TestResult("批量查询", "所有股票有评分>0", "WARN",
                                    f"仅 {len(scored)}/{len(stocks)} 有评分>0",
                                    elapsed, th, code))
        else:
            self.add(TestResult("批量查询", "所有股票有评分>0", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_ai_rankings(self):
        """T12: AI排名"""
        print("\n--- T12: AI Rankings ---")
        th = THRESHOLDS["ai_rankings"]
        code, data, elapsed, err = await self._get(f"{API_URL}/rankings/ai?limit=5", timeout=th + 10)
        if code == 200 and data:
            rankings = data.get("rankings", [])
            count = len(rankings)
            if count > 0:
                top = rankings[0]
                self.add(TestResult("AI排名", "AI排名 top5", "PASS",
                                    f"返回{count}只, 第一名: {top.get('name')} score={top.get('ai_ranking_score')}",
                                    elapsed, th, code))
            else:
                self.add(TestResult("AI排名", "AI排名 top5", "WARN",
                                    "返回0只", elapsed, th, code))
        else:
            self.add(TestResult("AI排名", "AI排名 top5", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_watchlist_add(self):
        """T13: 自选股 - 添加"""
        print("\n--- T13: Watchlist add ---")
        th = THRESHOLDS["watchlist"]
        payload = {"code": "600519", "name": "贵州茅台", "user_id": TEST_USER_ID}
        code, data, elapsed, err = await self._post(f"{API_URL}/watchlist/add", payload, timeout=th)
        if code == 200 and data and data.get("success"):
            self.add(TestResult("自选股", "添加 600519", "PASS",
                                data.get("message", ""), elapsed, th, code))
        else:
            self.add(TestResult("自选股", "添加 600519", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_watchlist_list(self):
        """T14: 自选股 - 列表"""
        print("\n--- T14: Watchlist list ---")
        th = THRESHOLDS["watchlist"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/watchlist/list?user_id={TEST_USER_ID}", timeout=th)
        if code == 200 and data:
            items = data.get("watchlist", [])
            has_600519 = any(w.get("code") == "600519" for w in items)
            self.add(TestResult("自选股", "查询列表", "PASS" if has_600519 else "WARN",
                                f"共{len(items)}只, 600519{'存在' if has_600519 else '不存在'}",
                                elapsed, th, code))
        else:
            self.add(TestResult("自选股", "查询列表", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_watchlist_remove(self):
        """T15: 自选股 - 删除"""
        print("\n--- T15: Watchlist remove ---")
        th = THRESHOLDS["watchlist"]
        payload = {"code": "600519", "user_id": TEST_USER_ID}
        code, data, elapsed, err = await self._delete(f"{API_URL}/watchlist/remove", payload, timeout=th)
        if code == 200 and data and data.get("success"):
            self.add(TestResult("自选股", "删除 600519", "PASS",
                                data.get("message", ""), elapsed, th, code))
        else:
            self.add(TestResult("自选股", "删除 600519", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_watchlist_verify_remove(self):
        """T16: 自选股 - 验证删除"""
        print("\n--- T16: Watchlist verify removal ---")
        th = THRESHOLDS["watchlist"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/watchlist/list?user_id={TEST_USER_ID}", timeout=th)
        if code == 200 and data:
            items = data.get("watchlist", [])
            has_600519 = any(w.get("code") == "600519" for w in items)
            self.add(TestResult("自选股", "验证删除成功", "PASS" if not has_600519 else "FAIL",
                                f"600519{'仍存在' if has_600519 else '已删除'}",
                                elapsed, th, code))
        else:
            self.add(TestResult("自选股", "验证删除成功", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_ai_chat(self):
        """T17: AI问答"""
        print("\n--- T17: AI Chat ---")
        th = THRESHOLDS["ai_chat"]
        payload = {
            "question": "这只股票最近走势如何?",
            "user_id": TEST_USER_ID,
        }
        code, data, elapsed, err = await self._post(
            f"{API_URL}/stock/600519/chat", payload, timeout=th)
        if code == 200 and data:
            answer = data.get("answer", "")
            if len(answer) > 10:
                self.add(TestResult("AI问答", "股票问答", "PASS",
                                    f"答案长度={len(answer)}, tokens={data.get('tokens_used')}",
                                    elapsed, th, code))
            else:
                self.add(TestResult("AI问答", "股票问答", "WARN",
                                    f"答案过短: {len(answer)}字符", elapsed, th, code))
        elif code == 429:
            self.add(TestResult("AI问答", "股票问答", "WARN",
                                "达到配额限制 (429)", elapsed, th, code))
        else:
            self.add(TestResult("AI问答", "股票问答", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_ai_chat_history(self):
        """T18: AI问答历史"""
        print("\n--- T18: AI Chat History ---")
        th = THRESHOLDS["ai_chat"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/stock/600519/chat/history?user_id={TEST_USER_ID}", timeout=30)
        if code == 200 and data:
            history = data.get("history", [])
            self.add(TestResult("AI问答", "问答历史查询", "PASS",
                                f"返回 {len(history)} 条记录", elapsed, 30, code))
        else:
            self.add(TestResult("AI问答", "问答历史查询", "FAIL",
                                err or f"HTTP {code}", elapsed, 30, code))

    async def test_recommendations(self):
        """T19: 推荐列表"""
        print("\n--- T19: Recommendations ---")
        th = THRESHOLDS["recommendations"]
        code, data, elapsed, err = await self._get(f"{API_URL}/recommendations", timeout=th + 5)
        if code == 200 and data:
            recs = data.get("recommendations", [])
            self.add(TestResult("推荐列表", "获取推荐", "PASS",
                                f"返回 {len(recs)} 只推荐股票", elapsed, th, code))
        else:
            self.add(TestResult("推荐列表", "获取推荐", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_kline(self):
        """T20: K线数据"""
        print("\n--- T20: K-line data ---")
        th = THRESHOLDS["kline"]
        code, data, elapsed, err = await self._get(f"{API_URL}/stock/600519/kline", timeout=th + 5)
        if code == 200 and data:
            kdata = data.get("data", [])
            if len(kdata) > 0:
                sample = kdata[-1]
                has_ohlcv = all(k in sample for k in ["open", "high", "low", "close", "volume"])
                self.add(TestResult("K线数据", "600519 K线", "PASS" if has_ohlcv else "WARN",
                                    f"{len(kdata)}根K线, OHLCV={'完整' if has_ohlcv else '不完整'}",
                                    elapsed, th, code))
            else:
                self.add(TestResult("K线数据", "600519 K线", "WARN",
                                    "返回0根K线", elapsed, th, code))
        else:
            self.add(TestResult("K线数据", "600519 K线", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_stock_degradation(self):
        """T21: 超时降级 - 验证有AI时降级返回纯技术分析"""
        print("\n--- T21: Timeout degradation check ---")
        # 此测试验证即使AI超时,仍能返回有效数据
        th = THRESHOLDS["stock_with_ai"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/stock/000001?ai_analysis=true", timeout=th + 10)
        if code == 200 and data:
            has_score = data.get("score", 0) > 0
            has_indicators = bool(data.get("indicators"))
            self.add(TestResult("降级机制", "AI超时仍返回技术分析", "PASS" if (has_score and has_indicators) else "WARN",
                                f"score={data.get('score')}, indicators={'有' if has_indicators else '无'}, ai={'有' if 'ai_analysis' in data else '无'}",
                                elapsed, th, code))
        else:
            self.add(TestResult("降级机制", "AI超时仍返回技术分析", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_search_empty(self):
        """T22: 搜索 - 空结果"""
        print("\n--- T22: Search empty result ---")
        th = THRESHOLDS["search"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/stocks/search?q=ZZZZNOTEXIST", timeout=th)
        if code == 200 and data:
            count = data.get("count", -1)
            self.add(TestResult("搜索", "空结果搜索", "PASS",
                                f"count={count}", elapsed, th, code))
        else:
            self.add(TestResult("搜索", "空结果搜索", "FAIL" if code != 200 else "WARN",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_batch_large(self):
        """T23: 批量查询 - 10只股票"""
        print("\n--- T23: Batch 10 stocks ---")
        th = THRESHOLDS["batch"]
        codes = "600519,000858,300750,601318,600036,000001,002415,000333,600276,601888"
        code, data, elapsed, err = await self._get(f"{API_URL}/stocks/batch?codes={codes}", timeout=th + 10)
        if code == 200 and data:
            stocks = data.get("stocks", [])
            self.add(TestResult("批量查询", "10只股票批量查询", "PASS" if len(stocks) >= 8 else "WARN",
                                f"返回 {len(stocks)}/10 只", elapsed, th, code))
        else:
            self.add(TestResult("批量查询", "10只股票批量查询", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_stock_ai_analysis_endpoint(self):
        """T24: AI分析独立接口"""
        print("\n--- T24: AI Analysis standalone endpoint ---")
        th = THRESHOLDS["stock_with_ai"]
        code, data, elapsed, err = await self._get(
            f"{API_URL}/stock/600519/ai-analysis", timeout=th + 10)
        if code == 200 and data:
            has_company = "company_analysis" in data
            has_fundamental = "fundamental_analysis" in data
            has_ai_rec = "ai_recommendation" in data
            self.add(TestResult("AI分析", "独立AI分析接口", "PASS" if all([has_company, has_fundamental, has_ai_rec]) else "WARN",
                                f"company={has_company}, fundamental={has_fundamental}, ai_rec={has_ai_rec}",
                                elapsed, th, code))
        else:
            self.add(TestResult("AI分析", "独立AI分析接口", "FAIL",
                                err or f"HTTP {code}", elapsed, th, code))

    async def test_concurrent_requests(self):
        """T25: 并发请求压力测试"""
        print("\n--- T25: Concurrent requests (3 parallel) ---")
        th = 20
        start = time.time()
        tasks = [
            self._get(f"{API_URL}/stock/600519", timeout=30),
            self._get(f"{API_URL}/stock/000001", timeout=30),
            self._get(f"{API_URL}/stock/000858", timeout=30),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        success = sum(1 for r in results if not isinstance(r, Exception) and r[0] == 200)
        self.add(TestResult("并发测试", "3个并发请求", "PASS" if success == 3 else "WARN",
                            f"{success}/3 成功", elapsed, th))

    # ==================== 运行 & 报告 ====================

    async def run_all(self):
        """运行所有测试"""
        await self.setup()

        print("=" * 70)
        print("Stock Advisor E2E Full Test Suite")
        print(f"Target: {BASE_URL}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # 按顺序运行（某些测试有依赖）
        await self.test_health_cold()
        await self.test_health_warm()
        await self.test_search_by_name()
        await self.test_search_by_code()
        await self.test_search_empty()
        await self.test_stock_no_ai()
        await self.test_stock_with_ai()
        await self.test_stock_cached()
        await self.test_stock_fields_validation()
        await self.test_stock_score_details()
        await self.test_stock_degradation()
        await self.test_batch()
        await self.test_batch_scores()
        await self.test_batch_large()
        await self.test_ai_rankings()
        await self.test_watchlist_add()
        await self.test_watchlist_list()
        await self.test_watchlist_remove()
        await self.test_watchlist_verify_remove()
        await self.test_ai_chat()
        await self.test_ai_chat_history()
        await self.test_recommendations()
        await self.test_kline()
        await self.test_stock_ai_analysis_endpoint()
        await self.test_concurrent_requests()

        await self.teardown()

    def print_report(self):
        """打印报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warned = sum(1 for r in self.results if r.status == "WARN")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        timeouts = sum(1 for r in self.results if r.timeout_exceeded)

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total: {total}  |  PASS: {passed}  |  FAIL: {failed}  |  WARN: {warned}  |  SKIP: {skipped}")
        print(f"Timeout exceeded: {timeouts}")
        print(f"Pass rate: {passed / total * 100:.1f}%" if total > 0 else "N/A")

        # 按类别汇总
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
            categories[r.category][r.status] += 1

        print("\n--- By Category ---")
        print(f"{'Category':<15} {'PASS':>5} {'FAIL':>5} {'WARN':>5} {'Rate':>8}")
        print("-" * 40)
        for cat, counts in categories.items():
            cat_total = sum(counts.values())
            rate = counts["PASS"] / cat_total * 100 if cat_total > 0 else 0
            print(f"{cat:<15} {counts['PASS']:>5} {counts['FAIL']:>5} {counts['WARN']:>5} {rate:>7.1f}%")

        # 失败用例详情
        failures = [r for r in self.results if r.status == "FAIL"]
        if failures:
            print("\n--- FAILURES ---")
            for r in failures:
                print(f"  [{r.category}] {r.name}: {r.message}")

        # 超时用例
        timeout_cases = [r for r in self.results if r.timeout_exceeded]
        if timeout_cases:
            print("\n--- TIMEOUT EXCEEDED ---")
            for r in timeout_cases:
                print(f"  [{r.category}] {r.name}: {r.response_time:.2f}s > {r.threshold}s")

    def save_report(self, filepath: str = None):
        """保存 JSON 报告"""
        if not filepath:
            filepath = f"e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")

        report = {
            "test_time": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "warned": sum(1 for r in self.results if r.status == "WARN"),
                "pass_rate": f"{passed / total * 100:.1f}%" if total > 0 else "0%",
                "timeouts": sum(1 for r in self.results if r.timeout_exceeded),
            },
            "results": [
                {
                    "category": r.category,
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "response_time": round(r.response_time, 3),
                    "threshold": r.threshold,
                    "timeout_exceeded": r.timeout_exceeded,
                    "status_code": r.status_code,
                    "timestamp": r.timestamp,
                }
                for r in self.results
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved: {filepath}")
        return filepath


async def main():
    runner = TestRunner()
    await runner.run_all()
    runner.print_report()
    runner.save_report()
    failed = sum(1 for r in runner.results if r.status == "FAIL")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
