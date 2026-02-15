"""
选股策略服务
实现各种选股策略和综合筛选
"""

import asyncio
import pandas as pd
from typing import Optional
from app.services import eastmoney_service, indicator_service
from app.services.ai_analysis_service import get_full_ai_analysis


def filter_basic(stocks_df: pd.DataFrame) -> pd.DataFrame:
    """
    基础过滤器
    - 排除 ST/*ST 股票
    - 排除停牌股票
    - 流通市值 > 10 亿
    - 日均成交额 > 5000 万
    """
    df = stocks_df.copy()

    # 排除 ST
    df = df[~df["名称"].str.contains("ST", na=False)]

    # 排除停牌（最新价为空或0）
    df = df[df["最新价"].notna() & (df["最新价"] > 0)]

    # 流通市值 > 10 亿
    if "流通市值" in df.columns:
        df = df[df["流通市值"] > 10_0000_0000]

    # 成交额 > 5000 万
    if "成交额" in df.columns:
        df = df[df["成交额"] > 5000_0000]

    return df


def macd_golden_cross(df: pd.DataFrame) -> bool:
    """
    MACD 金叉策略

    条件:
    1. DIF 从下向上穿越 DEA（金叉）
    2. 或 MACD 柱由负转正
    """
    try:
        from ta.trend import MACD

        macd_indicator = MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        hist_line = macd_indicator.macd_diff()

        if macd_line is None or len(macd_line) < 2:
            return False

        dif = macd_line.iloc[-1]
        dea = signal_line.iloc[-1]
        prev_dif = macd_line.iloc[-2]
        prev_dea = signal_line.iloc[-2]

        # 金叉
        if prev_dif <= prev_dea and dif > dea:
            return True

        # MACD 柱转正
        hist = hist_line.iloc[-1]
        prev_hist = hist_line.iloc[-2]
        if prev_hist < 0 and hist > 0:
            return True

        return False
    except Exception:
        return False


def rsi_oversold_bounce(df: pd.DataFrame) -> bool:
    """
    RSI 超卖反弹策略

    条件:
    1. RSI6 近5日曾跌破30
    2. RSI6 正在回升
    3. RSI6 < 50
    """
    try:
        from ta.momentum import RSIIndicator

        rsi6_indicator = RSIIndicator(df["close"], window=6)
        rsi6 = rsi6_indicator.rsi()

        if rsi6 is None or len(rsi6) < 5:
            return False

        rsi6_val = rsi6.iloc[-1]
        prev_rsi6 = rsi6.iloc[-2]

        # 近5日曾超卖
        was_oversold = rsi6.tail(5).min() < 30

        # 正在回升
        recovering = rsi6_val > prev_rsi6

        # RSI < 50
        not_overbought = rsi6_val < 50

        return was_oversold and recovering and not_overbought
    except Exception:
        return False


def ma_bullish_alignment(df: pd.DataFrame) -> bool:
    """
    均线多头排列策略

    条件:
    1. MA5 > MA10 > MA20
    2. 股价站上 MA5
    3. MA5 向上倾斜
    """
    try:
        from ta.trend import SMAIndicator

        ma5 = SMAIndicator(df["close"], window=5).sma_indicator()
        ma10 = SMAIndicator(df["close"], window=10).sma_indicator()
        ma20 = SMAIndicator(df["close"], window=20).sma_indicator()

        if ma5 is None or ma10 is None or ma20 is None:
            return False

        ma5_val = ma5.iloc[-1]
        ma10_val = ma10.iloc[-1]
        ma20_val = ma20.iloc[-1]
        close = df["close"].iloc[-1]

        # 多头排列
        bullish = ma5_val > ma10_val > ma20_val

        # 站上 MA5
        above_ma5 = close > ma5_val

        # MA5 向上
        ma5_rising = ma5_val > ma5.iloc[-2]

        return bullish and above_ma5 and ma5_rising
    except Exception:
        return False


def volume_price_confirmation(df: pd.DataFrame) -> bool:
    """
    量价配合策略

    条件:
    1. 价格上涨
    2. 成交量 > 5日均量 * 1.5
    3. 非跳空高开
    """
    try:
        close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        volume = df["volume"].iloc[-1]
        vol_ma5 = df["volume"].tail(5).mean()
        open_price = df["open"].iloc[-1]

        # 价格上涨
        price_up = close > prev_close

        # 放量
        volume_increase = volume > vol_ma5 * 1.5

        # 非跳空
        no_gap = open_price < prev_close * 1.03

        return price_up and volume_increase and no_gap
    except Exception:
        return False


def check_strategies(df: pd.DataFrame) -> dict:
    """
    检查所有策略

    Returns:
        dict with strategy results
    """
    return {
        "macd_golden_cross": macd_golden_cross(df),
        "rsi_oversold_bounce": rsi_oversold_bounce(df),
        "ma_bullish_alignment": ma_bullish_alignment(df),
        "volume_price_confirmation": volume_price_confirmation(df),
    }


async def analyze_stock(code: str) -> Optional[dict]:
    """
    完整分析单只股票

    Args:
        code: 股票代码

    Returns:
        dict with full analysis
    """
    # 获取历史数据
    df = await eastmoney_service.get_history(code, days=60)
    if df is None or df.empty:
        return None

    # 获取实时行情
    realtime = await eastmoney_service.get_realtime(code)
    if realtime is None:
        return None

    # 计算技术指标
    indicators = indicator_service.calculate_indicators(df)

    # 生成交易建议
    suggestion = indicator_service.calculate_trading_suggestion(df, indicators, current_price=realtime["price"])

    # 生成推荐理由
    reasons = indicator_service.generate_reasons(indicators)

    # 计算综合评分
    score = indicator_service.calculate_score(indicators, suggestion)

    # 检查策略
    strategies = check_strategies(df)

    return {
        "code": code,
        "name": realtime["name"],
        "industry": realtime.get("industry", ""),
        "price": realtime["price"],
        "change": realtime["change"],
        "market_cap": realtime.get("market_cap", 0),
        "indicators": indicators,
        "suggestion": suggestion,
        "reasons": reasons,
        "score": score,
        "strategies": strategies,
    }


def _build_recommendation(analysis: dict, ai_analysis=None) -> dict:
    """将分析结果格式化为推荐条目"""
    return {
        "code": analysis["code"],
        "name": analysis["name"],
        "industry": analysis["industry"],
        "price": analysis["price"],
        "change": analysis["change"],
        "score": analysis["score"],
        "buy_price_low": analysis["suggestion"]["buy_price_low"],
        "buy_price_high": analysis["suggestion"]["buy_price_high"],
        "stop_loss": analysis["suggestion"]["stop_loss"],
        "take_profit_1": analysis["suggestion"]["take_profit_1"],
        "take_profit_2": analysis["suggestion"]["take_profit_2"],
        "holding_days": analysis["suggestion"]["holding_days"],
        "position_ratio": analysis["suggestion"]["position"],
        "risk_level": analysis["suggestion"]["risk_level"],
        "reasons": analysis["reasons"],
        "ai_analysis": ai_analysis,
    }


async def generate_daily_recommendations(top_n: int = 10) -> list[dict]:
    """
    生成每日推荐（全并行优化，~2 分钟内完成）

    两轮筛选：
    1. 并行技术分析全部股票（Semaphore=5），按综合分排序
    2. 并行 AI 分析 top 5（Semaphore=3），其余仅技术面
    """
    try:
        from app.services.eastmoney_service import STOCK_LIST

        # ---- 第一轮：并行技术分析 (Semaphore=5, ~40s) ----
        analysis_sem = asyncio.Semaphore(5)

        async def _safe_analyze(code):
            async with analysis_sem:
                try:
                    return await analyze_stock(code)
                except Exception as e:
                    print(f"Error analyzing {code}: {e}")
                    return None

        results = await asyncio.gather(
            *[_safe_analyze(code) for code, _, _ in STOCK_LIST],
            return_exceptions=True,
        )

        all_analyzed = []
        for r in results:
            if isinstance(r, dict) and r.get("score", 0) > 0:
                strategies = r["strategies"]
                has_signal = any(strategies.values())
                r["_sort_score"] = r["score"] + (5 if has_signal else 0)
                all_analyzed.append(r)

        if not all_analyzed:
            return []

        all_analyzed.sort(key=lambda x: x["_sort_score"], reverse=True)

        # 候选池
        candidates = [a for a in all_analyzed if a["score"] >= 50]
        if len(candidates) < top_n:
            existing = {c["code"] for c in candidates}
            for a in all_analyzed:
                if a["code"] not in existing:
                    candidates.append(a)
                if len(candidates) >= top_n:
                    break
        candidates = candidates[:top_n]

        print(f"[Recommend] 分析 {len(all_analyzed)} 只, 候选 {len(candidates)} 只")

        # ---- 第二轮：并行 AI 分析 top 5 (Semaphore=3, ~90s) ----
        ai_sem = asyncio.Semaphore(3)
        ai_top_n = min(5, len(candidates))  # 只对前 5 名做 AI 分析

        async def _enrich_with_ai(analysis):
            async with ai_sem:
                try:
                    ai_result = await get_full_ai_analysis(
                        name=analysis["name"],
                        code=analysis["code"],
                        industry=analysis["industry"],
                        price=analysis["price"],
                        change=analysis["change"],
                        market_cap=analysis.get("market_cap", 0),
                        score=analysis["score"],
                        indicators=analysis.get("indicators", {}),
                        suggestion=analysis["suggestion"],
                    )
                    print(f"[AI] {analysis['name']} AI分析完成")
                    return ai_result
                except Exception as e:
                    print(f"[AI] {analysis['name']} AI分析失败: {e}")
                    return None

        # 并行获取前 5 名的 AI 分析
        ai_results = await asyncio.gather(
            *[_enrich_with_ai(c) for c in candidates[:ai_top_n]],
            return_exceptions=True,
        )

        # 组装推荐列表
        recommendations = []
        for i, analysis in enumerate(candidates):
            ai_data = None
            if i < ai_top_n and not isinstance(ai_results[i], Exception):
                ai_data = ai_results[i]
            recommendations.append(_build_recommendation(analysis, ai_data))

        return recommendations

    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return []
