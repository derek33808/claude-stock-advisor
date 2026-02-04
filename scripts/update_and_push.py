#!/usr/bin/env python3
"""
Stock Advisor - Render Cron Job 自动更新脚本 (Sina Finance API 版本)

使用新浪财经 API 获取数据，从境外访问更稳定

工作流程:
1. 克隆 GitHub 仓库
2. 通过新浪 API 获取股票数据
3. 计算技术指标和评分
4. 提交并推送更新

环境变量:
- GIT_TOKEN: GitHub Personal Access Token
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from typing import Optional, List, Dict

import numpy as np
import pandas as pd

# ============ 配置 ============
REPO_URL = "https://github.com/derek33808/claude-stock-advisor.git"
WORK_DIR = "/tmp/stock-advisor-update"
OUTPUT_FILE = "public/data/recommendations.json"
TOP_RECOMMENDATIONS = 5
TOP_ALL_STOCKS = 100
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

# 预定义的热门 A 股列表 (代码, 名称, 行业)
# 包含沪深 300 成分股中的代表性股票
STOCK_LIST = [
    # 白酒
    ("600519", "贵州茅台", "白酒"), ("000858", "五粮液", "白酒"), ("000568", "泸州老窖", "白酒"),
    ("002304", "洋河股份", "白酒"), ("000799", "酒鬼酒", "白酒"), ("603369", "今世缘", "白酒"),
    # 银行
    ("601398", "工商银行", "银行"), ("601939", "建设银行", "银行"), ("600036", "招商银行", "银行"),
    ("601166", "兴业银行", "银行"), ("600000", "浦发银行", "银行"), ("601288", "农业银行", "银行"),
    ("601328", "交通银行", "银行"), ("000001", "平安银行", "银行"), ("601818", "光大银行", "银行"),
    # 保险
    ("601318", "中国平安", "保险"), ("601628", "中国人寿", "保险"), ("601601", "中国太保", "保险"),
    # 科技
    ("000725", "京东方A", "面板"), ("002415", "海康威视", "安防"), ("300750", "宁德时代", "电池"),
    ("002594", "比亚迪", "汽车"), ("300059", "东方财富", "金融IT"), ("000063", "中兴通讯", "通信"),
    ("603501", "韦尔股份", "芯片"), ("002049", "紫光国微", "芯片"), ("688981", "中芯国际", "芯片"),
    # 新能源
    ("601012", "隆基绿能", "光伏"), ("300274", "阳光电源", "光伏"), ("002129", "中环股份", "光伏"),
    ("600438", "通威股份", "光伏"), ("601899", "紫金矿业", "有色"), ("002466", "天齐锂业", "锂电"),
    # 医药
    ("600276", "恒瑞医药", "医药"), ("000538", "云南白药", "医药"), ("300760", "迈瑞医疗", "医疗器械"),
    ("603259", "药明康德", "CXO"), ("000661", "长春高新", "生物药"), ("002007", "华兰生物", "血制品"),
    # 消费
    ("000651", "格力电器", "家电"), ("000333", "美的集团", "家电"), ("600887", "伊利股份", "乳业"),
    ("603288", "海天味业", "调味品"), ("002714", "牧原股份", "养殖"), ("600690", "海尔智家", "家电"),
    # 地产基建
    ("600048", "保利发展", "地产"), ("001979", "招商蛇口", "地产"), ("600585", "海螺水泥", "水泥"),
    ("601668", "中国建筑", "建筑"), ("601390", "中国中铁", "基建"),
    # 交通物流
    ("601111", "中国国航", "航空"), ("600029", "南方航空", "航空"), ("601006", "大秦铁路", "铁路"),
    ("600009", "上海机场", "机场"), ("002352", "顺丰控股", "快递"),
    # 能源
    ("600028", "中国石化", "石油"), ("601857", "中国石油", "石油"), ("600900", "长江电力", "电力"),
    ("600025", "华能水电", "电力"), ("601985", "中国核电", "核电"),
    # 军工
    ("600893", "航发动力", "航发"), ("000768", "中航西飞", "飞机"), ("600760", "中航沈飞", "飞机"),
    # 互联网传媒
    ("002602", "世纪华通", "游戏"), ("300413", "芒果超媒", "传媒"), ("002555", "三七互娱", "游戏"),
    # 券商
    ("600030", "中信证券", "券商"), ("601211", "国泰君安", "券商"), ("000776", "广发证券", "券商"),
    ("601688", "华泰证券", "券商"), ("600837", "海通证券", "券商"),
]


# ============ 新浪财经 API ============

def fetch_sina_realtime(codes: List[str]) -> Dict[str, dict]:
    """
    通过新浪财经 API 获取实时行情
    API: http://hq.sinajs.cn/list=sh600519,sz000001
    """
    results = {}
    # 分批请求，每批 50 个
    batch_size = 50

    for i in range(0, len(codes), batch_size):
        batch = codes[i:i + batch_size]
        symbols = []
        for code in batch:
            # 判断沪市还是深市
            if code.startswith('6') or code.startswith('9'):
                symbols.append(f'sh{code}')
            else:
                symbols.append(f'sz{code}')

        url = f'http://hq.sinajs.cn/list={",".join(symbols)}'

        for retry in range(MAX_RETRIES):
            try:
                req = urllib.request.Request(url)
                req.add_header('Referer', 'http://finance.sina.com.cn')
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                    content = response.read().decode('gbk')

                # 解析返回数据
                for line in content.strip().split('\n'):
                    if not line or '=' not in line:
                        continue
                    match = re.search(r'hq_str_(\w+)="(.+)"', line)
                    if not match:
                        continue
                    symbol = match.group(1)
                    data = match.group(2).split(',')
                    code = symbol[2:]  # 去掉 sh/sz 前缀

                    if len(data) >= 32:
                        results[code] = {
                            'name': data[0],
                            'open': float(data[1]) if data[1] else 0,
                            'yesterday_close': float(data[2]) if data[2] else 0,
                            'price': float(data[3]) if data[3] else 0,
                            'high': float(data[4]) if data[4] else 0,
                            'low': float(data[5]) if data[5] else 0,
                            'volume': float(data[8]) if data[8] else 0,  # 手
                            'amount': float(data[9]) if data[9] else 0,  # 元
                        }
                break
            except Exception as e:
                if retry < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                print(f"   ⚠️ 批次请求失败: {e}")

        time.sleep(0.3)  # 请求间隔

    return results


def fetch_sina_history(code: str, days: int = 120) -> Optional[pd.DataFrame]:
    """
    通过新浪财经 API 获取历史 K 线
    API: http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
    """
    if code.startswith('6') or code.startswith('9'):
        symbol = f'sh{code}'
    else:
        symbol = f'sz{code}'

    url = (f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/'
           f'CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={days}')

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('Referer', 'http://finance.sina.com.cn')
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('utf-8')

            if not content or content == 'null':
                return None

            data = json.loads(content)
            if not data:
                return None

            df = pd.DataFrame(data)
            df = df.rename(columns={
                'day': 'date', 'open': 'open', 'close': 'close',
                'high': 'high', 'low': 'low', 'volume': 'volume'
            })
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'close', 'high', 'low', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            return df.sort_values('date').reset_index(drop=True)

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return None

    return None


def fetch_sina_index() -> dict:
    """获取上证和深证指数"""
    url = 'http://hq.sinajs.cn/list=sh000001,sz399001'

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('Referer', 'http://finance.sina.com.cn')
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('gbk')

            result = {
                'shIndex': {'value': 3000, 'change': 0},
                'szIndex': {'value': 10000, 'change': 0},
                'sentiment': '中性'
            }

            for line in content.strip().split('\n'):
                if 'sh000001' in line:
                    data = line.split(',')
                    if len(data) >= 4:
                        price = float(data[3]) if data[3] else 3000
                        yesterday = float(data[2]) if data[2] else price
                        change = (price - yesterday) / yesterday * 100 if yesterday else 0
                        result['shIndex'] = {'value': round(price, 2), 'change': round(change, 2)}
                elif 'sz399001' in line:
                    data = line.split(',')
                    if len(data) >= 4:
                        price = float(data[3]) if data[3] else 10000
                        yesterday = float(data[2]) if data[2] else price
                        change = (price - yesterday) / yesterday * 100 if yesterday else 0
                        result['szIndex'] = {'value': round(price, 2), 'change': round(change, 2)}

            avg_change = (result['shIndex']['change'] + result['szIndex']['change']) / 2
            result['sentiment'] = '偏多' if avg_change > 0.5 else '偏空' if avg_change < -0.5 else '中性'

            return result

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            print(f"   ⚠️ 获取指数失败: {e}")

    return {
        'shIndex': {'value': 3000, 'change': 0},
        'szIndex': {'value': 10000, 'change': 0},
        'sentiment': '中性'
    }


# ============ 技术指标计算 ============

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


# ============ 评估函数 ============

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


def evaluate_price_position(realtime: dict, df: pd.DataFrame) -> tuple:
    """评估价格位置"""
    score, reasons = 0, []
    price = realtime.get('price', 0)
    yesterday = realtime.get('yesterday_close', price)

    if price <= 0 or yesterday <= 0:
        return 0, []

    change = (price - yesterday) / yesterday * 100

    # 涨跌幅评估
    if 0 < change <= 3:
        score += 30
        reasons.append(f"涨{change:.1f}%")
    elif -2 <= change <= 0:
        score += 20
        reasons.append(f"微跌{change:.1f}%")

    # 成交额评估
    amount = realtime.get('amount', 0)
    if amount > 500000000:  # 5亿以上
        score += 35
        reasons.append("成交活跃")
    elif amount > 100000000:  # 1亿以上
        score += 25

    # 价格位置（相对于当日高低点）
    high, low = realtime.get('high', price), realtime.get('low', price)
    if high > low:
        position = (price - low) / (high - low)
        if 0.5 <= position <= 0.8:
            score += 35
            reasons.append("价格位置良好")

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


# ============ 主流程 ============

def analyze_stock(code: str, name: str, industry: str, realtime: dict) -> Optional[dict]:
    """分析单只股票"""
    if realtime.get('price', 0) <= 0:
        return None

    # 获取历史数据
    df = fetch_sina_history(code)
    if df is None or len(df) < 60:
        return None

    df = calculate_indicators(df)

    # 技术面评分
    tech_score, tech_reasons = evaluate_technical(df)

    # 价格位置评分
    price_score, price_reasons = evaluate_price_position(realtime, df)

    # 综合评分
    total_score = int(tech_score * 0.6 + price_score * 0.4)

    current_price = realtime['price']
    change = (current_price - realtime['yesterday_close']) / realtime['yesterday_close'] * 100 if realtime['yesterday_close'] > 0 else 0

    trading_plan = calculate_trading_plan(df, current_price)

    return {
        'code': code,
        'name': name,
        'industry': industry,
        'price': round(current_price, 2),
        'change': round(change, 2),
        'score': total_score,
        **trading_plan,
        'reasons': {
            'technical': tech_reasons,
            'fundamental': price_reasons,
            'capital': []
        }
    }


def generate_data(output_path: str):
    """生成股票推荐数据"""
    print("📋 使用预定义股票列表...")
    print(f"   共 {len(STOCK_LIST)} 支股票")

    # 获取实时行情
    print("\n📊 获取实时行情...")
    codes = [s[0] for s in STOCK_LIST]
    realtime_data = fetch_sina_realtime(codes)
    print(f"   获取到 {len(realtime_data)} 支股票数据")

    if len(realtime_data) < 10:
        raise Exception(f"获取行情数据不足，仅获取 {len(realtime_data)} 支")

    # 分析股票
    print("\n📈 分析股票...")
    results = []
    for code, name, industry in STOCK_LIST:
        if code not in realtime_data:
            continue
        realtime = realtime_data[code]

        # 使用 API 返回的名称（如果有）
        actual_name = realtime.get('name', name) or name

        result = analyze_stock(code, actual_name, industry, realtime)
        if result and result['score'] > 40:
            results.append(result)
            print(f"   ✓ {code} {actual_name}: {result['score']}分")

        time.sleep(0.2)  # 请求间隔

    print(f"\n   完成，{len(results)} 支入选")
    results.sort(key=lambda x: x['score'], reverse=True)

    # 获取市场概览
    print("\n📊 获取市场指数...")
    market = fetch_sina_index()
    print(f"   上证: {market['shIndex']['value']} ({market['shIndex']['change']:+.2f}%)")
    print(f"   深证: {market['szIndex']['value']} ({market['szIndex']['change']:+.2f}%)")

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
    print("   (Sina Finance API 版本)")
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
