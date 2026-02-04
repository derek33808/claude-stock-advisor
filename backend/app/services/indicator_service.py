"""
技术指标计算服务
使用 pandas-ta 计算各种技术指标
"""

import pandas as pd
import pandas_ta as ta
from typing import Optional


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
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            dif = macd.iloc[-1, 0]  # MACD_12_26_9
            dea = macd.iloc[-1, 2]  # MACDs_12_26_9
            hist = macd.iloc[-1, 1]  # MACDh_12_26_9

            # 判断金叉/死叉
            prev_dif = macd.iloc[-2, 0] if len(macd) > 1 else dif
            prev_dea = macd.iloc[-2, 2] if len(macd) > 1 else dea

            if prev_dif <= prev_dea and dif > dea:
                signal = "金叉"
            elif prev_dif >= prev_dea and dif < dea:
                signal = "死叉"
            elif dif > dea:
                signal = "多头"
            else:
                signal = "空头"

            result["macd"] = {
                "dif": round(dif, 3),
                "dea": round(dea, 3),
                "hist": round(hist, 3),
                "signal": signal,
            }
    except Exception as e:
        print(f"MACD calculation error: {e}")
        result["macd"] = {"dif": 0, "dea": 0, "hist": 0, "signal": "未知"}

    # ============================================
    # RSI (6, 12, 24)
    # ============================================
    try:
        rsi6 = ta.rsi(df["close"], length=6)
        rsi12 = ta.rsi(df["close"], length=12)

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
            "rsi6": round(rsi6_val, 1),
            "rsi12": round(rsi12_val, 1),
            "status": status,
        }
    except Exception as e:
        print(f"RSI calculation error: {e}")
        result["rsi"] = {"rsi6": 50, "rsi12": 50, "status": "未知"}

    # ============================================
    # MA (5, 10, 20, 60)
    # ============================================
    try:
        ma5 = ta.sma(df["close"], length=5)
        ma10 = ta.sma(df["close"], length=10)
        ma20 = ta.sma(df["close"], length=20)
        ma60 = ta.sma(df["close"], length=60) if len(df) >= 60 else None

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
            "ma5": round(ma5_val, 2),
            "ma10": round(ma10_val, 2),
            "ma20": round(ma20_val, 2),
            "ma60": round(ma60_val, 2),
            "trend": trend,
        }
    except Exception as e:
        print(f"MA calculation error: {e}")
        result["ma"] = {"ma5": 0, "ma10": 0, "ma20": 0, "ma60": 0, "trend": "未知"}

    # ============================================
    # KDJ (9, 3, 3)
    # ============================================
    try:
        stoch = ta.stoch(df["high"], df["low"], df["close"], k=9, d=3, smooth_k=3)
        if stoch is not None and not stoch.empty:
            k = stoch.iloc[-1, 0]  # STOCHk
            d = stoch.iloc[-1, 1]  # STOCHd
            j = 3 * k - 2 * d

            result["kdj"] = {
                "k": round(k, 1),
                "d": round(d, 1),
                "j": round(j, 1),
            }
    except Exception as e:
        print(f"KDJ calculation error: {e}")
        result["kdj"] = {"k": 50, "d": 50, "j": 50}

    # ============================================
    # BOLL (20, 2)
    # ============================================
    try:
        bbands = ta.bbands(df["close"], length=20, std=2)
        if bbands is not None and not bbands.empty:
            upper = bbands.iloc[-1, 0]  # BBU
            mid = bbands.iloc[-1, 1]  # BBM
            lower = bbands.iloc[-1, 2]  # BBL

            result["boll"] = {
                "upper": round(upper, 2),
                "mid": round(mid, 2),
                "lower": round(lower, 2),
            }
    except Exception as e:
        print(f"BOLL calculation error: {e}")
        result["boll"] = {"upper": 0, "mid": 0, "lower": 0}

    # ============================================
    # ATR (14)
    # ============================================
    try:
        atr = ta.atr(df["high"], df["low"], df["close"], length=14)
        if atr is not None and not atr.empty:
            result["atr"] = round(atr.iloc[-1], 2)
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
            "current": round(vol, 0),
            "ma5": round(vol_ma5, 0),
            "ma20": round(vol_ma20, 0),
            "ratio": round(vol_ratio, 2),
            "status": vol_status,
        }
    except Exception as e:
        print(f"Volume analysis error: {e}")
        result["volume"] = {"current": 0, "ma5": 0, "ma20": 0, "ratio": 1, "status": "未知"}

    return result


def calculate_trading_suggestion(df: pd.DataFrame, indicators: dict) -> dict:
    """
    根据技术指标生成交易建议

    Args:
        df: 历史数据
        indicators: 技术指标

    Returns:
        dict with buy_price, stop_loss, take_profit, etc.
    """
    if df is None or df.empty:
        return {}

    close = df["close"].iloc[-1]
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
        "buy_price_low": round(buy_price_low, 2),
        "buy_price_high": round(buy_price_high, 2),
        "stop_loss": round(stop_loss, 2),
        "take_profit_1": round(take_profit_1, 2),
        "take_profit_2": round(take_profit_2, 2),
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
