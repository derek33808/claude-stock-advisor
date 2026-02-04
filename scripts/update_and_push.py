#!/usr/bin/env python3
"""
Stock Advisor - Render Cron Job 自动更新脚本

工作流程:
1. 克隆 GitHub 仓库
2. 运行数据生成脚本
3. 提交并推送更新
4. Render Web Service 自动重新部署

环境变量:
- GIT_TOKEN: GitHub Personal Access Token (需要 repo 权限)
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Optional

import akshare as ak
import numpy as np
import pandas as pd
from tqdm import tqdm

# ============ 配置 ============
REPO_URL = "https://github.com/derek33808/claude-stock-advisor.git"
WORK_DIR = "/tmp/stock-advisor-update"
OUTPUT_FILE = "public/data/recommendations.json"
TOP_RECOMMENDATIONS = 5
TOP_ALL_STOCKS = 100
MAX_STOCKS_TO_ANALYZE = 80  # 减少分析数量，加快速度


# ============ 技术指标计算函数 ============

def calc_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(close, fast)
    ema_slow = calc_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = calc_ema(dif, signal)
    macd = (dif - dea) * 2
    return dif, dea, macd


def calc_rsi(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_kdj(high: pd.Series, low: pd.Series, close: pd.Series, n=9, m1=3, m2=3):
    low_n = low.rolling(window=n).min()
    high_n = high.rolling(window=n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()
    d = k.ewm(alpha=1/m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period=14) -> pd.Series:
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


# ============ 数据获取 ============

def get_stock_list() -> pd.DataFrame:
    print("📋 获取股票列表...")
    try:
        df = ak.stock_zh_a_spot_em()
        print(f"   获取到 {len(df)} 支股票")
        return df
    except Exception as e:
        print(f"   ❌ 获取失败: {e}")
        return pd.DataFrame()


def get_stock_history(code: str, days: int = 120) -> Optional[pd.DataFrame]:
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        if df is None or df.empty:
            return None
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            '成交额': 'amount', '换手率': 'turnover'
        })
        df['date'] = pd.to_datetime(df['date'])
        return df.sort_values('date').tail(days).reset_index(drop=True)
    except Exception:
        return None


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) < 60:
        return df
    df['ma5'] = calc_sma(df['close'], 5)
    df['ma10'] = calc_sma(df['close'], 10)
    df['ma20'] = calc_sma(df['close'], 20)
    df['ma60'] = calc_sma(df['close'], 60)
    df['dif'], df['dea'], df['macd'] = calc_macd(df['close'])
    df['rsi6'] = calc_rsi(df['close'], 6)
    df['k'], df['d'], df['j'] = calc_kdj(df['high'], df['low'], df['close'])
    df['atr'] = calc_atr(df['high'], df['low'], df['close'])
    df['vol_ma5'] = calc_sma(df['volume'], 5)
    return df


def check_basic_filter(row: pd.Series) -> bool:
    name = str(row.get('名称', ''))
    if 'ST' in name or '*ST' in name:
        return False
    change = float(row.get('涨跌幅', 0) or 0)
    amount = float(row.get('成交额', 0) or 0)
    if change == 0 and amount == 0:
        return False
    if amount < 100000000:  # 1亿成交额
        return False
    market_cap = float(row.get('总市值', 0) or 0)
    if market_cap < 5000000000:  # 50亿市值
        return False
    return True


def evaluate_technical(df: pd.DataFrame) -> tuple:
    if df is None or len(df) < 60:
        return 0, []
    score, reasons = 0, []
    latest, prev = df.iloc[-1], df.iloc[-2]

    # MACD
    if pd.notna(latest.get('dif')) and pd.notna(latest.get('dea')):
        dif, dea = latest['dif'], latest['dea']
        prev_dif, prev_dea = prev.get('dif', 0), prev.get('dea', 0)
        if pd.notna(prev_dif) and pd.notna(prev_dea):
            if prev_dif < prev_dea and dif > dea:
                score += 25
                reasons.append("MACD金叉")
            elif dif > dea:
                score += 15
                reasons.append("MACD多头")

    # RSI
    rsi6 = latest.get('rsi6', 50)
    if pd.notna(rsi6):
        if 30 <= rsi6 <= 50:
            score += 25
            reasons.append(f"RSI={rsi6:.0f}健康")
        elif 50 < rsi6 <= 70:
            score += 20

    # 均线
    close = latest['close']
    ma5, ma10, ma20 = latest.get('ma5', 0), latest.get('ma10', 0), latest.get('ma20', 0)
    if pd.notna(ma5) and pd.notna(ma20):
        if close > ma5 > ma10 > ma20:
            score += 25
            reasons.append("均线多头排列")
        elif close > ma20:
            score += 15

    # 量价
    vol, vol_ma5 = latest.get('volume', 0), latest.get('vol_ma5', 0)
    price_change = (close - prev['close']) / prev['close'] if prev['close'] > 0 else 0
    if pd.notna(vol) and pd.notna(vol_ma5) and vol_ma5 > 0:
        vol_ratio = vol / vol_ma5
        if price_change > 0 and vol_ratio > 1.5:
            score += 25
            reasons.append(f"放量上涨{vol_ratio:.1f}x")
        elif price_change > 0 and vol_ratio > 1.2:
            score += 15

    return min(score, 100), reasons


def evaluate_fundamental(row: pd.Series) -> tuple:
    score, reasons = 0, []
    pe = float(row.get('市盈率-动态', 0) or 0)
    if 0 < pe < 20:
        score += 35
        reasons.append(f"PE={pe:.1f}低估")
    elif 20 <= pe < 35:
        score += 25

    pb = float(row.get('市净率', 0) or 0)
    if 0 < pb < 2:
        score += 35
        reasons.append(f"PB={pb:.1f}低估")
    elif 2 <= pb < 5:
        score += 25

    change = float(row.get('涨跌幅', 0) or 0)
    if 0 < change <= 3:
        score += 30
        reasons.append(f"涨{change:.1f}%")

    return min(score, 100), reasons


def calculate_trading_plan(df: pd.DataFrame, current_price: float) -> dict:
    default = {
        'buyPriceLow': round(current_price * 0.97, 2),
        'buyPriceHigh': round(current_price * 0.99, 2),
        'stopLoss': round(current_price * 0.95, 2),
        'takeProfit1': round(current_price * 1.06, 2),
        'takeProfit2': round(current_price * 1.12, 2),
        'holdingDays': '5-10个交易日',
        'positionRatio': '10%',
        'riskLevel': 'medium'
    }
    if df is None or len(df) < 20:
        return default

    latest = df.iloc[-1]
    atr = latest.get('atr', current_price * 0.03)
    if pd.isna(atr):
        atr = current_price * 0.03

    low_20 = df['low'].tail(20).min()
    support = max(low_20 * 1.02, current_price * 0.95)
    buy_low = max(current_price * 0.97, support)
    stop_loss = min(buy_low - atr * 1.5, support * 0.97)
    risk = buy_low - stop_loss
    take_profit_1 = buy_low + risk * 2
    take_profit_2 = buy_low + risk * 3

    volatility = atr / current_price
    if volatility < 0.02:
        risk_level, position = 'low', '15-20%'
    elif volatility < 0.04:
        risk_level, position = 'medium', '10-15%'
    else:
        risk_level, position = 'high', '5-10%'

    return {
        'buyPriceLow': round(buy_low, 2),
        'buyPriceHigh': round(current_price * 0.99, 2),
        'stopLoss': round(stop_loss, 2),
        'takeProfit1': round(take_profit_1, 2),
        'takeProfit2': round(take_profit_2, 2),
        'holdingDays': '5-15个交易日',
        'positionRatio': position,
        'riskLevel': risk_level
    }


def analyze_stock(row: pd.Series) -> Optional[dict]:
    code, name = str(row['代码']), str(row['名称'])
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
    print("📊 获取市场数据...")
    try:
        index_df = ak.stock_zh_index_spot_em()
        sh_row = index_df[index_df['代码'] == '000001'].iloc[0]
        sz_row = index_df[index_df['代码'] == '399001'].iloc[0]
        sh_change, sz_change = float(sh_row['涨跌幅']), float(sz_row['涨跌幅'])
        avg_change = (sh_change + sz_change) / 2
        sentiment = '偏多' if avg_change > 1 else '偏空' if avg_change < -1 else '中性'
        return {
            'shIndex': {'value': float(sh_row['最新价']), 'change': sh_change},
            'szIndex': {'value': float(sz_row['最新价']), 'change': sz_change},
            'sentiment': sentiment
        }
    except Exception as e:
        print(f"   ⚠️ 获取指数失败: {e}")
        return {
            'shIndex': {'value': 3000, 'change': 0},
            'szIndex': {'value': 10000, 'change': 0},
            'sentiment': '中性'
        }


def generate_data(output_path: str):
    """生成股票推荐数据"""
    stock_list = get_stock_list()
    if stock_list.empty:
        raise Exception("无法获取股票列表")

    print("\n🔍 基础过滤...")
    filtered = stock_list[stock_list.apply(check_basic_filter, axis=1)]
    filtered = filtered.sort_values('成交额', ascending=False).head(MAX_STOCKS_TO_ANALYZE)
    print(f"   分析 {len(filtered)} 支高活跃度股票")

    print("\n📈 分析股票...")
    results = []
    for _, row in tqdm(filtered.iterrows(), total=len(filtered)):
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

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已生成: {output_path}")
    print(f"   推荐: {len(output['recommendations'])} 支")
    print(f"   分析库: {len(output['allStocks'])} 支")


def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"  > {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[:500])
    if result.returncode != 0 and result.stderr:
        print(f"  Error: {result.stderr[:200]}")
    return result.returncode == 0


def main():
    print("=" * 50)
    print(f"🚀 Stock Advisor 自动更新 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    git_token = os.environ.get('GIT_TOKEN')
    if not git_token:
        print("❌ GIT_TOKEN 未设置")
        return 1

    # 清理工作目录
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)

    # 克隆仓库
    print("\n📥 克隆仓库...")
    repo_url_with_token = REPO_URL.replace("https://", f"https://{git_token}@")
    if not run_command(f'git clone {repo_url_with_token} {WORK_DIR}'):
        print("❌ 克隆失败")
        return 1

    # 生成数据
    print("\n📊 生成数据...")
    output_path = os.path.join(WORK_DIR, OUTPUT_FILE)
    try:
        generate_data(output_path)
    except Exception as e:
        print(f"❌ 数据生成失败: {e}")
        return 1

    # 提交并推送
    print("\n📤 提交并推送...")
    run_command('git config user.email "render-bot@stock-advisor.app"', cwd=WORK_DIR)
    run_command('git config user.name "Render Bot"', cwd=WORK_DIR)
    run_command(f'git add {OUTPUT_FILE}', cwd=WORK_DIR)

    # 检查是否有变化
    result = subprocess.run('git diff --cached --quiet', shell=True, cwd=WORK_DIR)
    if result.returncode == 0:
        print("   没有数据变化，跳过推送")
        return 0

    commit_msg = f"📊 更新数据 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if not run_command(f'git commit -m "{commit_msg}"', cwd=WORK_DIR):
        print("❌ 提交失败")
        return 1

    if not run_command('git push origin main', cwd=WORK_DIR):
        print("❌ 推送失败")
        return 1

    print("\n" + "=" * 50)
    print("✅ 更新完成！Render 将自动重新部署")
    print("=" * 50)
    return 0


if __name__ == '__main__':
    sys.exit(main())
