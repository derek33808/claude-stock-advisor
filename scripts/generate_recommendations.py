#!/usr/bin/env python3
"""
Stock Advisor - 股票推荐生成脚本

使用方法:
    cd stock-advisor/scripts
    pip3 install -r requirements.txt
    python3 generate_recommendations.py

输出:
    ../public/data/recommendations.json
"""

import json
import os
from datetime import datetime
from typing import Optional

import akshare as ak
import numpy as np
import pandas as pd

# 配置
OUTPUT_PATH = "../public/data/recommendations.json"
TOP_RECOMMENDATIONS = 5  # 今日推荐数量
TOP_ALL_STOCKS = 100     # 分析库股票数量


# ============ 技术指标计算函数 ============

def calc_sma(series: pd.Series, period: int) -> pd.Series:
    """简单移动平均线"""
    return series.rolling(window=period).mean()


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """指数移动平均线"""
    return series.ewm(span=period, adjust=False).mean()


def calc_macd(close: pd.Series, fast=12, slow=26, signal=9):
    """MACD指标"""
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = calc_ema(dif, signal)
    macd = (dif - dea) * 2
    return dif, dea, macd


def calc_rsi(close: pd.Series, period: int) -> pd.Series:
    """RSI指标"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calc_kdj(high: pd.Series, low: pd.Series, close: pd.Series, n=9, m1=3, m2=3):
    """KDJ指标"""
    low_n = low.rolling(window=n).min()
    high_n = high.rolling(window=n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()
    d = k.ewm(alpha=1/m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def calc_boll(close: pd.Series, period=20, std_dev=2):
    """布林带"""
    mid = calc_sma(close, period)
    std = close.rolling(window=period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return upper, mid, lower


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    """ATR波动率"""
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


# ============ 数据获取函数 ============

def get_stock_list() -> pd.DataFrame:
    """获取A股股票列表"""
    print("📋 获取股票列表...")
    try:
        df = ak.stock_zh_a_spot_em()
        print(f"   获取到 {len(df)} 支股票")
        return df
    except Exception as e:
        print(f"   ❌ 获取股票列表失败: {e}")
        return pd.DataFrame()


def get_stock_history(code: str, days: int = 120) -> Optional[pd.DataFrame]:
    """获取单只股票的历史数据"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        if df is None or df.empty:
            return None

        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '换手率': 'turnover'
        })

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').tail(days).reset_index(drop=True)

        return df
    except Exception:
        return None


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    if df is None or len(df) < 60:
        return df

    # 均线
    df['ma5'] = calc_sma(df['close'], 5)
    df['ma10'] = calc_sma(df['close'], 10)
    df['ma20'] = calc_sma(df['close'], 20)
    df['ma60'] = calc_sma(df['close'], 60)

    # MACD
    df['dif'], df['dea'], df['macd'] = calc_macd(df['close'])

    # RSI
    df['rsi6'] = calc_rsi(df['close'], 6)
    df['rsi12'] = calc_rsi(df['close'], 12)

    # KDJ
    df['k'], df['d'], df['j'] = calc_kdj(df['high'], df['low'], df['close'])

    # BOLL
    df['boll_upper'], df['boll_mid'], df['boll_lower'] = calc_boll(df['close'])

    # ATR
    df['atr'] = calc_atr(df['high'], df['low'], df['close'])

    # 成交量均线
    df['vol_ma5'] = calc_sma(df['volume'], 5)

    return df


def check_basic_filter(row: pd.Series) -> bool:
    """基础过滤"""
    name = str(row.get('名称', ''))

    if 'ST' in name or '*ST' in name:
        return False

    change = float(row.get('涨跌幅', 0) or 0)
    amount = float(row.get('成交额', 0) or 0)
    if change == 0 and amount == 0:
        return False

    if amount < 50000000:
        return False

    market_cap = float(row.get('总市值', 0) or 0)
    if market_cap < 1000000000:
        return False

    return True


def evaluate_technical(df: pd.DataFrame) -> tuple:
    """技术面评分"""
    if df is None or len(df) < 60:
        return 0, []

    score = 0
    reasons = []
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # MACD
    if pd.notna(latest.get('dif')) and pd.notna(latest.get('dea')):
        dif = latest['dif']
        dea = latest['dea']
        prev_dif = prev.get('dif', 0)
        prev_dea = prev.get('dea', 0)

        if pd.notna(prev_dif) and pd.notna(prev_dea):
            if prev_dif < prev_dea and dif > dea:
                score += 25
                reasons.append("MACD金叉，多头信号")
            elif dif > dea:
                score += 15
                reasons.append("MACD多头排列")
            elif dif > prev_dif:
                score += 10
                reasons.append("MACD有向上趋势")

    # RSI
    rsi6 = latest.get('rsi6', 50)
    if pd.notna(rsi6):
        if 30 <= rsi6 <= 50:
            score += 25
            reasons.append(f"RSI={rsi6:.0f}，处于健康区间")
        elif 50 < rsi6 <= 70:
            score += 20
            reasons.append(f"RSI={rsi6:.0f}，偏强但未超买")
        elif rsi6 < 30:
            score += 15
            reasons.append(f"RSI={rsi6:.0f}，超卖有反弹机会")

    # 均线
    close = latest['close']
    ma5 = latest.get('ma5', 0)
    ma10 = latest.get('ma10', 0)
    ma20 = latest.get('ma20', 0)

    if pd.notna(ma5) and pd.notna(ma20):
        if close > ma5 > ma10 > ma20:
            score += 25
            reasons.append("均线多头排列")
        elif close > ma20:
            score += 15
            reasons.append("股价站上MA20")
        elif close > ma5:
            score += 10
            reasons.append("股价站上MA5")

    # 量价
    vol = latest.get('volume', 0)
    vol_ma5 = latest.get('vol_ma5', 0)
    price_change = (close - prev['close']) / prev['close'] if prev['close'] > 0 else 0

    if pd.notna(vol) and pd.notna(vol_ma5) and vol_ma5 > 0:
        vol_ratio = vol / vol_ma5
        if price_change > 0 and vol_ratio > 1.5:
            score += 25
            reasons.append(f"放量上涨{vol_ratio:.1f}倍")
        elif price_change > 0 and vol_ratio > 1.2:
            score += 15
            reasons.append("温和放量上涨")

    return min(score, 100), reasons


def evaluate_fundamental(row: pd.Series) -> tuple:
    """基本面评分"""
    score = 0
    reasons = []

    pe = float(row.get('市盈率-动态', 0) or 0)
    if 0 < pe < 20:
        score += 35
        reasons.append(f"PE={pe:.1f}，估值偏低")
    elif 20 <= pe < 35:
        score += 25
        reasons.append(f"PE={pe:.1f}，估值合理")
    elif 35 <= pe < 50:
        score += 15

    pb = float(row.get('市净率', 0) or 0)
    if 0 < pb < 2:
        score += 35
        reasons.append(f"PB={pb:.1f}，资产被低估")
    elif 2 <= pb < 5:
        score += 25

    change = float(row.get('涨跌幅', 0) or 0)
    if 0 < change <= 3:
        score += 30
        reasons.append(f"今日上涨{change:.2f}%")
    elif 3 < change <= 6:
        score += 20

    return min(score, 100), reasons


def calculate_trading_plan(df: pd.DataFrame, current_price: float) -> dict:
    """计算交易计划"""
    if df is None or len(df) < 20:
        return {
            'buyPriceLow': round(current_price * 0.97, 2),
            'buyPriceHigh': round(current_price * 0.99, 2),
            'stopLoss': round(current_price * 0.95, 2),
            'takeProfit1': round(current_price * 1.06, 2),
            'takeProfit2': round(current_price * 1.12, 2),
            'holdingDays': '5-10个交易日',
            'positionRatio': '10%',
            'riskLevel': 'medium'
        }

    latest = df.iloc[-1]
    high_20 = df['high'].tail(20).max()
    low_20 = df['low'].tail(20).min()

    atr = latest.get('atr', current_price * 0.03)
    if pd.isna(atr):
        atr = current_price * 0.03

    support = max(low_20 * 1.02, current_price * 0.95)
    buy_low = max(current_price * 0.97, support)
    buy_high = current_price * 0.99
    stop_loss = min(buy_low - atr * 1.5, support * 0.97)

    risk = buy_low - stop_loss
    take_profit_1 = buy_low + risk * 2
    take_profit_2 = buy_low + risk * 3

    volatility = atr / current_price
    if volatility < 0.02:
        risk_level = 'low'
        position = '15-20%'
    elif volatility < 0.04:
        risk_level = 'medium'
        position = '10-15%'
    else:
        risk_level = 'high'
        position = '5-10%'

    return {
        'buyPriceLow': round(buy_low, 2),
        'buyPriceHigh': round(buy_high, 2),
        'stopLoss': round(stop_loss, 2),
        'takeProfit1': round(take_profit_1, 2),
        'takeProfit2': round(take_profit_2, 2),
        'holdingDays': '5-15个交易日',
        'positionRatio': position,
        'riskLevel': risk_level
    }


def analyze_stock(row: pd.Series) -> Optional[dict]:
    """分析单只股票"""
    code = str(row['代码'])
    name = str(row['名称'])

    df = get_stock_history(code)
    if df is None or len(df) < 60:
        return None

    df = calculate_indicators(df)
    tech_score, tech_reasons = evaluate_technical(df)
    fund_score, fund_reasons = evaluate_fundamental(row)

    total_score = int(tech_score * 0.6 + fund_score * 0.4)

    current_price = float(row.get('最新价', 0) or 0)
    change = float(row.get('涨跌幅', 0) or 0)

    trading_plan = calculate_trading_plan(df, current_price)

    return {
        'code': code,
        'name': name,
        'industry': str(row.get('所属行业', '未知')),
        'price': current_price,
        'change': change,
        'score': total_score,
        **trading_plan,
        'reasons': {
            'technical': tech_reasons,
            'fundamental': fund_reasons,
            'capital': []
        }
    }


def get_market_overview() -> dict:
    """获取市场概览"""
    print("📊 获取市场数据...")
    try:
        index_df = ak.stock_zh_index_spot_em()

        sh_row = index_df[index_df['代码'] == '000001'].iloc[0]
        sz_row = index_df[index_df['代码'] == '399001'].iloc[0]

        sh_change = float(sh_row['涨跌幅'])
        sz_change = float(sz_row['涨跌幅'])

        avg_change = (sh_change + sz_change) / 2
        if avg_change > 1:
            sentiment = '偏多'
        elif avg_change < -1:
            sentiment = '偏空'
        else:
            sentiment = '中性'

        return {
            'shIndex': {
                'value': float(sh_row['最新价']),
                'change': sh_change
            },
            'szIndex': {
                'value': float(sz_row['最新价']),
                'change': sz_change
            },
            'sentiment': sentiment
        }
    except Exception as e:
        print(f"   ⚠️ 获取指数失败: {e}")
        return {
            'shIndex': {'value': 3000, 'change': 0},
            'szIndex': {'value': 10000, 'change': 0},
            'sentiment': '中性'
        }


def main():
    print("=" * 50)
    print("🚀 Stock Advisor 数据生成脚本")
    print("=" * 50)

    stock_list = get_stock_list()
    if stock_list.empty:
        print("❌ 无法获取股票列表")
        return

    print("\n🔍 基础过滤...")
    filtered = stock_list[stock_list.apply(check_basic_filter, axis=1)]
    print(f"   过滤后 {len(filtered)} 支")

    filtered = filtered.sort_values('成交额', ascending=False).head(300)

    print("\n📈 分析股票...")
    results = []
    total = len(filtered)

    for idx, (_, row) in enumerate(filtered.iterrows()):
        if (idx + 1) % 30 == 0:
            print(f"   进度: {idx + 1}/{total}")

        result = analyze_stock(row)
        if result and result['score'] > 40:
            results.append(result)

    print(f"   完成，{len(results)} 支入选")

    results.sort(key=lambda x: x['score'], reverse=True)

    market = get_market_overview()

    now = datetime.now()
    output = {
        'date': now.strftime('%Y-%m-%d'),
        'updateTime': now.strftime('%H:%M'),
        'market': market,
        'recommendations': results[:TOP_RECOMMENDATIONS],
        'allStocks': results[:TOP_ALL_STOCKS]
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("✅ 完成!")
    print(f"   文件: {os.path.abspath(OUTPUT_PATH)}")
    print(f"   推荐: {len(output['recommendations'])} 支")
    print(f"   分析库: {len(output['allStocks'])} 支")
    print("\n📌 今日推荐:")
    for i, s in enumerate(output['recommendations'], 1):
        print(f"   {i}. {s['name']} ({s['code']}) 评分:{s['score']}")
    print("=" * 50)


if __name__ == '__main__':
    main()
