"""
技术指标计算服务
使用 ta 库计算各种技术指标
"""

import math
import pandas as pd
import ta as ta_lib
from ta.trend import MACD, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from typing import Optional


def safe_round(value, decimals=2):
    """安全的四舍五入，处理 NaN 和 inf"""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return 0
    try:
        return round(float(value), decimals)
    except (ValueError, TypeError):
        return 0


def calculate_indicators(df: pd.DataFrame) -> dict:
    """
    计算所有技术指标

    Args:
        df: DataFrame with columns: date, open, high, low, close, volume

    Returns:
        dict with all indicators
    """
    if df is None or df.empty:
        return {}

    # 确保数据类型正确
    df = df.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    result = {}

    # ============================================
    # MACD (12, 26, 9)
    # ============================================
    try:
        macd_indicator = MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd_indicator.macd()
        signal_line = macd_indicator.macd_signal()
        hist_line = macd_indicator.macd_diff()

        if macd_line is not None and not macd_line.empty:
            dif = macd_line.iloc[-1]
            dea = signal_line.iloc[-1]
            hist = hist_line.iloc[-1]

            # 判断金叉/死叉
            prev_dif = macd_line.iloc[-2] if len(macd_line) > 1 else dif
            prev_dea = signal_line.iloc[-2] if len(signal_line) > 1 else dea

            if prev_dif <= prev_dea and dif > dea:
                signal = "金叉"
            elif prev_dif >= prev_dea and dif < dea:
                signal = "死叉"
            elif dif > dea:
                signal = "多头"
            else:
                signal = "空头"

            result["macd"] = {
                "dif": safe_round(dif, 3),
                "dea": safe_round(dea, 3),
                "hist": safe_round(hist, 3),
                "signal": signal,
            }
    except Exception as e:
        print(f"MACD calculation error: {e}")
        result["macd"] = {"dif": 0, "dea": 0, "hist": 0, "signal": "未知"}

    # ============================================
    # RSI (6, 12, 24)
    # ============================================
    try:
        rsi6_indicator = RSIIndicator(df["close"], window=6)
        rsi12_indicator = RSIIndicator(df["close"], window=12)
        rsi6 = rsi6_indicator.rsi()
        rsi12 = rsi12_indicator.rsi()

        rsi6_val = rsi6.iloc[-1] if rsi6 is not None and not rsi6.empty else 50
        rsi12_val = rsi12.iloc[-1] if rsi12 is not None and not rsi12.empty else 50

        # 判断状态
        if rsi6_val > 80:
            status = "超买"
        elif rsi6_val < 20:
            status = "超卖"
        elif rsi6_val > 70:
            status = "偏高"
        elif rsi6_val < 30:
            status = "偏低"
        else:
            status = "健康"

        result["rsi"] = {
            "rsi6": safe_round(rsi6_val, 1),
            "rsi12": safe_round(rsi12_val, 1),
            "status": status,
        }
    except Exception as e:
        print(f"RSI calculation error: {e}")
        result["rsi"] = {"rsi6": 50, "rsi12": 50, "status": "未知"}

    # ============================================
    # MA (5, 10, 20, 60)
    # ============================================
    try:
        ma5 = SMAIndicator(df["close"], window=5).sma_indicator()
        ma10 = SMAIndicator(df["close"], window=10).sma_indicator()
        ma20 = SMAIndicator(df["close"], window=20).sma_indicator()
        ma60 = SMAIndicator(df["close"], window=60).sma_indicator() if len(df) >= 60 else None

        ma5_val = ma5.iloc[-1] if ma5 is not None and not ma5.empty else 0
        ma10_val = ma10.iloc[-1] if ma10 is not None and not ma10.empty else 0
        ma20_val = ma20.iloc[-1] if ma20 is not None and not ma20.empty else 0
        ma60_val = ma60.iloc[-1] if ma60 is not None and not ma60.empty else 0

        # 判断趋势
        close = df["close"].iloc[-1]
        if ma5_val > ma10_val > ma20_val:
            if close > ma5_val:
                trend = "多头排列"
            else:
                trend = "多头回调"
        elif ma5_val < ma10_val < ma20_val:
            if close < ma5_val:
                trend = "空头排列"
            else:
                trend = "空头反弹"
        else:
            trend = "震荡"

        result["ma"] = {
            "ma5": safe_round(ma5_val, 2),
            "ma10": safe_round(ma10_val, 2),
            "ma20": safe_round(ma20_val, 2),
            "ma60": safe_round(ma60_val, 2),
            "trend": trend,
        }
    except Exception as e:
        print(f"MA calculation error: {e}")
        result["ma"] = {"ma5": 0, "ma10": 0, "ma20": 0, "ma60": 0, "trend": "未知"}

    # ============================================
    # KDJ (9, 3, 3)
    # ============================================
    try:
        stoch = StochasticOscillator(df["high"], df["low"], df["close"], window=9, smooth_window=3)
        k_line = stoch.stoch()
        d_line = stoch.stoch_signal()

        if k_line is not None and not k_line.empty:
            k = k_line.iloc[-1]
            d = d_line.iloc[-1]
            j = 3 * k - 2 * d

            result["kdj"] = {
                "k": safe_round(k, 1),
                "d": safe_round(d, 1),
                "j": safe_round(j, 1),
            }
    except Exception as e:
        print(f"KDJ calculation error: {e}")
        result["kdj"] = {"k": 50, "d": 50, "j": 50}

    # ============================================
    # BOLL (20, 2)
    # ============================================
    try:
        bbands = BollingerBands(df["close"], window=20, window_dev=2)
        upper = bbands.bollinger_hband().iloc[-1]
        mid = bbands.bollinger_mavg().iloc[-1]
        lower = bbands.bollinger_lband().iloc[-1]

        result["boll"] = {
            "upper": safe_round(upper, 2),
            "mid": safe_round(mid, 2),
            "lower": safe_round(lower, 2),
        }
    except Exception as e:
        print(f"BOLL calculation error: {e}")
        result["boll"] = {"upper": 0, "mid": 0, "lower": 0}

    # ============================================
    # ATR (14)
    # ============================================
    try:
        atr_indicator = AverageTrueRange(df["high"], df["low"], df["close"], window=14)
        atr = atr_indicator.average_true_range()
        if atr is not None and not atr.empty:
            result["atr"] = safe_round(atr.iloc[-1], 2)
    except Exception as e:
        print(f"ATR calculation error: {e}")
        result["atr"] = 0

    # ============================================
    # 成交量分析
    # ============================================
    try:
        vol = df["volume"].iloc[-1]
        vol_ma5 = df["volume"].tail(5).mean()
        vol_ma20 = df["volume"].tail(20).mean()

        vol_ratio = vol / vol_ma5 if vol_ma5 > 0 else 1

        if vol_ratio > 2:
            vol_status = "放量"
        elif vol_ratio > 1.5:
            vol_status = "温和放量"
        elif vol_ratio < 0.5:
            vol_status = "缩量"
        else:
            vol_status = "正常"

        result["volume"] = {
            "current": safe_round(vol, 0),
            "ma5": safe_round(vol_ma5, 0),
            "ma20": safe_round(vol_ma20, 0),
            "ratio": safe_round(vol_ratio, 2),
            "status": vol_status,
        }
    except Exception as e:
        print(f"Volume analysis error: {e}")
        result["volume"] = {"current": 0, "ma5": 0, "ma20": 0, "ratio": 1, "status": "未知"}

    return result


def calculate_trading_suggestion(df: pd.DataFrame, indicators: dict, current_price: float = None) -> dict:
    """
    根据技术指标生成交易建议

    Args:
        df: 历史数据
        indicators: 技术指标
        current_price: 实时价格（优先使用，避免历史数据与实时价格不一致）

    Returns:
        dict with buy_price, stop_loss, take_profit, etc.
    """
    if df is None or df.empty:
        return {}

    close = current_price if current_price else df["close"].iloc[-1]
    high_20 = df["high"].tail(20).max()
    low_20 = df["low"].tail(20).min()

    atr = indicators.get("atr", close * 0.03)  # 默认 3%

    # 支撑位（近20日低点上方2%）
    support = low_20 * 1.02

    # 阻力位（近20日高点）
    resistance = high_20

    # 买入价区间（当前价下方1-3%，但不低于支撑位）
    buy_price_low = max(close * 0.97, support)
    buy_price_high = close * 0.99

    # 止损价（买入价下方1.5倍ATR，或支撑位下方3%）
    stop_loss = min(buy_price_low - atr * 1.5, support * 0.97)

    # 止盈价（盈亏比 2:1 和 3:1）
    risk = buy_price_low - stop_loss
    take_profit_1 = buy_price_low + risk * 2
    take_profit_2 = buy_price_low + risk * 3

    # 风险等级
    atr_pct = atr / close * 100 if close > 0 else 0
    if atr_pct > 4:
        risk_level = "高"
        position = "5-10%"
    elif atr_pct > 2:
        risk_level = "中"
        position = "10-15%"
    else:
        risk_level = "低"
        position = "15-20%"

    # 综合判断操作建议
    macd_signal = indicators.get("macd", {}).get("signal", "")
    rsi_status = indicators.get("rsi", {}).get("status", "")
    ma_trend = indicators.get("ma", {}).get("trend", "")

    bullish_signals = 0
    if macd_signal in ["金叉", "多头"]:
        bullish_signals += 1
    if rsi_status in ["健康", "偏低", "超卖"]:
        bullish_signals += 1
    if ma_trend in ["多头排列", "多头回调"]:
        bullish_signals += 1

    if bullish_signals >= 2:
        action = "买入"
    elif bullish_signals == 1:
        action = "观望"
    else:
        action = "回避"

    return {
        "action": action,
        "buy_price_low": safe_round(buy_price_low, 2),
        "buy_price_high": safe_round(buy_price_high, 2),
        "stop_loss": safe_round(stop_loss, 2),
        "take_profit_1": safe_round(take_profit_1, 2),
        "take_profit_2": safe_round(take_profit_2, 2),
        "position": position,
        "holding_days": "5-15个交易日",
        "risk_level": risk_level,
    }


def generate_reasons(indicators: dict) -> dict:
    """
    根据技术指标生成推荐理由

    Args:
        indicators: 技术指标

    Returns:
        dict with technical, fundamental, capital reasons
    """
    technical = []
    fundamental = []
    capital = []

    # MACD
    macd = indicators.get("macd", {})
    if macd.get("signal") == "金叉":
        technical.append("MACD金叉")
    elif macd.get("signal") == "多头":
        technical.append("MACD多头排列")

    # RSI
    rsi = indicators.get("rsi", {})
    rsi_val = rsi.get("rsi6", 50)
    status = rsi.get("status", "")
    if status == "超卖":
        technical.append(f"RSI={rsi_val}超卖反弹")
    elif status in ["健康", "偏低"]:
        technical.append(f"RSI={rsi_val}{status}")

    # MA
    ma = indicators.get("ma", {})
    trend = ma.get("trend", "")
    if trend == "多头排列":
        technical.append("均线多头排列")
    elif trend == "多头回调":
        technical.append("均线多头回调")

    # Volume
    vol = indicators.get("volume", {})
    vol_status = vol.get("status", "")
    if vol_status in ["放量", "温和放量"]:
        technical.append(vol_status)

    # KDJ
    kdj = indicators.get("kdj", {})
    if kdj.get("j", 50) < 20:
        technical.append("KDJ超卖")

    return {
        "technical": technical,
        "fundamental": fundamental,  # 需要基本面数据
        "capital": capital,  # 需要资金流向数据
    }


def calculate_score(indicators: dict, suggestion: dict) -> int:
    """
    计算综合评分 (0-100)

    Args:
        indicators: 技术指标
        suggestion: 交易建议

    Returns:
        int score
    """
    score = 50  # 基础分

    # MACD (max +15)
    macd = indicators.get("macd", {})
    if macd.get("signal") == "金叉":
        score += 15
    elif macd.get("signal") == "多头":
        score += 10
    elif macd.get("signal") == "空头":
        score -= 5
    elif macd.get("signal") == "死叉":
        score -= 10

    # RSI (max +10)
    rsi = indicators.get("rsi", {})
    rsi_val = rsi.get("rsi6", 50)
    if 30 <= rsi_val <= 50:
        score += 10
    elif 20 <= rsi_val < 30:
        score += 8
    elif 50 < rsi_val <= 70:
        score += 5
    elif rsi_val > 70:
        score -= 5
    elif rsi_val < 20:
        score += 5  # 超卖可能反弹

    # MA (max +10)
    ma = indicators.get("ma", {})
    trend = ma.get("trend", "")
    if trend == "多头排列":
        score += 10
    elif trend == "多头回调":
        score += 5
    elif trend == "空头排列":
        score -= 10
    elif trend == "空头反弹":
        score -= 5

    # Volume (max +5)
    vol = indicators.get("volume", {})
    if vol.get("status") == "放量":
        score += 5
    elif vol.get("status") == "温和放量":
        score += 3
    elif vol.get("status") == "缩量":
        score -= 3

    # Risk adjustment
    if suggestion.get("risk_level") == "高":
        score -= 5
    elif suggestion.get("risk_level") == "低":
        score += 5

    # Clamp to 0-100
    return max(0, min(100, score))


def calculate_score_detailed(indicators: dict, suggestion: dict, current_price: float = 0, df: pd.DataFrame = None) -> dict:
    """
    计算多维度评分 (每个维度 0-100)

    Returns:
        dict with trend_score, momentum_score, volatility_score, volume_score, composite
    """
    # ===== 趋势得分 (0-100) =====
    trend_score = 50
    macd = indicators.get("macd", {})
    ma = indicators.get("ma", {})

    # MACD 方向
    if macd.get("signal") == "金叉":
        trend_score += 25
    elif macd.get("signal") == "多头":
        trend_score += 15
    elif macd.get("signal") == "空头":
        trend_score -= 15
    elif macd.get("signal") == "死叉":
        trend_score -= 25

    # MA 排列
    ma_trend = ma.get("trend", "")
    if ma_trend == "多头排列":
        trend_score += 20
    elif ma_trend == "多头回调":
        trend_score += 10
    elif ma_trend == "空头排列":
        trend_score -= 20
    elif ma_trend == "空头反弹":
        trend_score -= 10

    # 价格 vs MA5
    if current_price > 0 and ma.get("ma5", 0) > 0:
        if current_price > ma["ma5"]:
            trend_score += 5
        else:
            trend_score -= 5

    trend_score = max(0, min(100, trend_score))

    # ===== 动量得分 (0-100) =====
    momentum_score = 50
    rsi = indicators.get("rsi", {})
    kdj = indicators.get("kdj", {})
    rsi6 = rsi.get("rsi6", 50)

    # RSI 状态
    if 30 <= rsi6 <= 50:
        momentum_score += 20
    elif 20 <= rsi6 < 30:
        momentum_score += 15  # 超卖反弹
    elif 50 < rsi6 <= 70:
        momentum_score += 10
    elif rsi6 > 80:
        momentum_score -= 20  # 严重超买
    elif rsi6 > 70:
        momentum_score -= 10
    elif rsi6 < 20:
        momentum_score += 10  # 极度超卖

    # KDJ
    j_val = kdj.get("j", 50)
    if j_val < 20:
        momentum_score += 15  # 超卖
    elif j_val > 80:
        momentum_score -= 15  # 超买
    elif 20 <= j_val <= 50:
        momentum_score += 5

    # 近5日涨幅（如有 df）
    if df is not None and len(df) >= 5:
        try:
            close_5d_ago = float(df["close"].iloc[-5])
            close_now = float(df["close"].iloc[-1])
            pct_5d = (close_now - close_5d_ago) / close_5d_ago * 100
            if 0 < pct_5d <= 5:
                momentum_score += 10
            elif 5 < pct_5d <= 10:
                momentum_score += 5
            elif pct_5d > 10:
                momentum_score -= 5  # 涨太多
            elif -5 < pct_5d < 0:
                momentum_score += 5  # 小幅回调
            elif pct_5d <= -10:
                momentum_score -= 10
        except (ValueError, IndexError):
            pass

    momentum_score = max(0, min(100, momentum_score))

    # ===== 波动得分 (0-100, 高分=低波动=安全) =====
    volatility_score = 50
    atr = indicators.get("atr", 0)
    boll = indicators.get("boll", {})

    # ATR 占比
    if current_price > 0 and atr > 0:
        atr_pct = atr / current_price * 100
        if atr_pct < 2:
            volatility_score += 25  # 低波动
        elif atr_pct < 3:
            volatility_score += 10
        elif atr_pct > 5:
            volatility_score -= 25  # 高波动
        elif atr_pct > 4:
            volatility_score -= 10

    # BOLL 位置
    boll_upper = boll.get("upper", 0)
    boll_lower = boll.get("lower", 0)
    boll_mid = boll.get("mid", 0)
    if current_price > 0 and boll_upper > 0 and boll_lower > 0:
        boll_width = (boll_upper - boll_lower) / boll_mid * 100 if boll_mid > 0 else 0
        if boll_width < 5:
            volatility_score += 15  # 窄带=即将突破
        elif boll_width > 15:
            volatility_score -= 10

        if current_price >= boll_upper * 0.98:
            volatility_score -= 10  # 上轨附近风险
        elif current_price <= boll_lower * 1.02:
            volatility_score += 10  # 下轨附近安全

    volatility_score = max(0, min(100, volatility_score))

    # ===== 量能得分 (0-100) =====
    volume_score = 50
    vol = indicators.get("volume", {})
    vol_ratio = vol.get("ratio", 1)
    vol_status = vol.get("status", "正常")

    if vol_status == "温和放量":
        volume_score += 20
    elif vol_status == "放量":
        volume_score += 10
    elif vol_status == "缩量":
        volume_score -= 15
    elif vol_status == "正常":
        volume_score += 5

    # 量价关系（价涨量增=健康）
    if df is not None and len(df) >= 2:
        try:
            price_up = float(df["close"].iloc[-1]) > float(df["close"].iloc[-2])
            vol_up = float(df["volume"].iloc[-1]) > float(df["volume"].iloc[-2])
            if price_up and vol_up:
                volume_score += 15  # 价涨量增
            elif not price_up and vol_up:
                volume_score -= 10  # 价跌放量
            elif price_up and not vol_up:
                volume_score -= 5   # 价涨缩量
        except (ValueError, IndexError):
            pass

    volume_score = max(0, min(100, volume_score))

    # ===== 加权综合分 =====
    composite = int(
        trend_score * 0.35 +
        momentum_score * 0.25 +
        volatility_score * 0.20 +
        volume_score * 0.20
    )
    composite = max(0, min(100, composite))

    return {
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "volatility_score": volatility_score,
        "volume_score": volume_score,
        "composite": composite,
    }


def calculate_price_prediction(indicators: dict, current_price: float, df: pd.DataFrame = None) -> dict:
    """
    基于技术指标的5日价格预测

    使用 ATR、MA趋势、RSI、BOLL 综合估算

    Returns:
        dict with 5d_target_high, 5d_target_low, 5d_most_likely,
              probability_up, probability_down, probability_flat,
              expected_return_pct
    """
    if current_price <= 0:
        return _default_prediction(current_price)

    atr = indicators.get("atr", current_price * 0.03)
    if atr <= 0:
        atr = current_price * 0.03

    rsi = indicators.get("rsi", {})
    ma = indicators.get("ma", {})
    boll = indicators.get("boll", {})
    macd = indicators.get("macd", {})

    rsi6 = rsi.get("rsi6", 50)
    ma_trend = ma.get("trend", "震荡")
    macd_signal = macd.get("signal", "未知")
    boll_upper = boll.get("upper", current_price * 1.05)
    boll_lower = boll.get("lower", current_price * 0.95)

    # 基于 ATR 的 5 日波动区间（根号5倍 ATR）
    atr_5d = atr * math.sqrt(5)

    # 基础概率
    prob_up = 50
    prob_down = 30
    prob_flat = 20

    # MA 趋势调整
    if ma_trend == "多头排列":
        prob_up += 15
        prob_down -= 10
    elif ma_trend == "多头回调":
        prob_up += 5
        prob_down -= 3
    elif ma_trend == "空头排列":
        prob_up -= 15
        prob_down += 10
    elif ma_trend == "空头反弹":
        prob_up -= 5
        prob_down += 3

    # MACD 调整
    if macd_signal == "金叉":
        prob_up += 10
        prob_down -= 5
    elif macd_signal == "死叉":
        prob_up -= 10
        prob_down += 5

    # RSI 超买超卖调整
    if rsi6 > 80:
        prob_up -= 15
        prob_down += 10
    elif rsi6 > 70:
        prob_up -= 5
        prob_down += 3
    elif rsi6 < 20:
        prob_up += 15
        prob_down -= 10
    elif rsi6 < 30:
        prob_up += 5
        prob_down -= 3

    # 归一化概率
    total = prob_up + prob_down + prob_flat
    prob_up = max(5, min(85, int(prob_up / total * 100)))
    prob_down = max(5, min(85, int(prob_down / total * 100)))
    prob_flat = 100 - prob_up - prob_down
    if prob_flat < 5:
        excess = 5 - prob_flat
        prob_flat = 5
        if prob_up > prob_down:
            prob_up -= excess
        else:
            prob_down -= excess

    # 计算目标价
    # 上行偏移受趋势调整
    up_multiplier = 1.0
    down_multiplier = 1.0
    if ma_trend in ("多头排列", "多头回调"):
        up_multiplier = 1.2
        down_multiplier = 0.8
    elif ma_trend in ("空头排列", "空头反弹"):
        up_multiplier = 0.8
        down_multiplier = 1.2

    target_high = current_price + atr_5d * up_multiplier
    target_low = current_price - atr_5d * down_multiplier

    # 限制在 BOLL 范围内
    target_high = min(target_high, boll_upper * 1.02)
    target_low = max(target_low, boll_lower * 0.98)

    # 最可能价格
    if prob_up > prob_down:
        most_likely = current_price + (target_high - current_price) * 0.3
    elif prob_down > prob_up:
        most_likely = current_price - (current_price - target_low) * 0.3
    else:
        most_likely = current_price

    expected_return = (most_likely - current_price) / current_price * 100

    return {
        "5d_target_high": safe_round(target_high, 2),
        "5d_target_low": safe_round(target_low, 2),
        "5d_most_likely": safe_round(most_likely, 2),
        "probability_up": prob_up,
        "probability_down": prob_down,
        "probability_flat": prob_flat,
        "expected_return_pct": safe_round(expected_return, 2),
    }


def _default_prediction(current_price: float) -> dict:
    """默认预测值"""
    return {
        "5d_target_high": safe_round(current_price * 1.05, 2),
        "5d_target_low": safe_round(current_price * 0.95, 2),
        "5d_most_likely": safe_round(current_price, 2),
        "probability_up": 33,
        "probability_down": 33,
        "probability_flat": 34,
        "expected_return_pct": 0,
    }
