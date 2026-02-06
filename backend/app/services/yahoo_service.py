"""
Yahoo Finance API 数据获取服务（直接 HTTP 请求版本）
全球可访问，用于获取 A 股实时和历史数据

A股代码格式：
- 上海: 600519.SS (贵州茅台)
- 深圳: 000001.SZ (平安银行)
- 创业板: 300750.SZ (宁德时代)
- 科创板: 688981.SS (中芯国际)
"""

import json
import time
import urllib.request
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# 请求配置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# 预定义的股票列表 (用于搜索和行业信息)
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
    ("002873", "新天药业", "医药"),
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

# 构建股票代码到信息的映射
STOCK_INFO = {code: {"name": name, "industry": industry} for code, name, industry in STOCK_LIST}


def _to_yahoo_symbol(code: str) -> str:
    """
    将 A股代码转换为 Yahoo Finance 格式

    上海市场 (.SS): 6开头, 9开头, 5开头, 11开头
    深圳市场 (.SZ): 0开头, 3开头, 159开头, 12开头
    """
    if code.startswith('6') or code.startswith('9') or code.startswith('5') or code.startswith('11'):
        return f"{code}.SS"
    else:
        return f"{code}.SZ"


def _fetch_yahoo_chart(symbol: str, period1: int, period2: int, interval: str = "1d") -> Optional[dict]:
    """
    从 Yahoo Finance Chart API 获取数据
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={period1}&period2={period2}&interval={interval}"

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('utf-8')

            data = json.loads(content)

            if data.get('chart', {}).get('result'):
                return data['chart']['result'][0]
            return None

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                time.sleep(0.5 * (retry + 1))
                continue
            print(f"[Yahoo] Error fetching {symbol}: {e}")
            return None

    return None


def get_stock_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    获取股票历史 K 线数据

    Args:
        code: 股票代码 (如 600519, 000001)
        days: 获取天数

    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    try:
        symbol = _to_yahoo_symbol(code)

        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)

        period1 = int(start_date.timestamp())
        period2 = int(end_date.timestamp())

        data = _fetch_yahoo_chart(symbol, period1, period2)

        if not data:
            print(f"[Yahoo] No data for {code} ({symbol})")
            return None

        # 解析数据
        timestamps = data.get('timestamp', [])
        quote = data.get('indicators', {}).get('quote', [{}])[0]

        if not timestamps or not quote:
            return None

        # 构建 DataFrame
        records = []
        for i, ts in enumerate(timestamps):
            open_price = quote.get('open', [])[i] if i < len(quote.get('open', [])) else None
            high = quote.get('high', [])[i] if i < len(quote.get('high', [])) else None
            low = quote.get('low', [])[i] if i < len(quote.get('low', [])) else None
            close = quote.get('close', [])[i] if i < len(quote.get('close', [])) else None
            volume = quote.get('volume', [])[i] if i < len(quote.get('volume', [])) else None

            if close is not None:  # 只添加有效数据
                records.append({
                    'date': datetime.fromtimestamp(ts),
                    'open': float(open_price) if open_price else float(close),
                    'high': float(high) if high else float(close),
                    'low': float(low) if low else float(close),
                    'close': float(close),
                    'volume': float(volume) if volume else 0,
                })

        if not records:
            return None

        df = pd.DataFrame(records)
        df = df.sort_values('date').tail(days).reset_index(drop=True)

        print(f"[Yahoo] Got {len(df)} days of history for {code}")
        return df

    except Exception as e:
        print(f"[Yahoo] Error fetching history for {code}: {e}")
        return None


def get_stock_realtime(code: str) -> Optional[dict]:
    """
    获取单只股票实时行情

    Args:
        code: 股票代码 (如 600519, 000001)

    Returns:
        dict with price, change, etc.
    """
    try:
        symbol = _to_yahoo_symbol(code)

        # 获取最近几天数据来计算实时价格
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        period1 = int(start_date.timestamp())
        period2 = int(end_date.timestamp())

        data = _fetch_yahoo_chart(symbol, period1, period2)

        if not data:
            print(f"[Yahoo] No realtime data for {code}")
            return None

        meta = data.get('meta', {})
        quote = data.get('indicators', {}).get('quote', [{}])[0]
        timestamps = data.get('timestamp', [])

        # 获取收盘价数组
        closes = [c for c in quote.get('close', []) if c is not None]

        # 获取最新价格：优先用 meta，否则用收盘价数组最后一个
        price = meta.get('regularMarketPrice', 0)
        if not price and closes:
            price = closes[-1]

        if not price:
            return None

        # 获取昨收价：必须用收盘价数组倒数第二个（Yahoo 中国股票不提供 regularMarketPreviousClose）
        # chartPreviousClose 是图表起点（7天前），不是昨收！
        if len(closes) >= 2:
            prev_close = closes[-2]  # 正确的昨收
            print(f"[Yahoo Debug] {code}: price={price}, prev_close={prev_close} (from closes[-2])")
        else:
            # 只有一天数据时才用 meta 字段（不太准确但没办法）
            prev_close = meta.get('regularMarketPreviousClose') or meta.get('previousClose') or meta.get('chartPreviousClose', price)
            print(f"[Yahoo Debug] {code}: price={price}, prev_close={prev_close} (from meta, closes count={len(closes)})")

        change = ((price - prev_close) / prev_close * 100) if prev_close else 0
        print(f"[Yahoo Debug] {code}: calculated change={change:.2f}%")

        # 获取今日数据
        open_price = meta.get('regularMarketDayHigh', price)  # 如果没有，用现价代替
        high = meta.get('regularMarketDayHigh', price)
        low = meta.get('regularMarketDayLow', price)
        volume = meta.get('regularMarketVolume', 0)

        # 如果 meta 没有今日数据，从 quote 获取
        if quote.get('open') and quote['open'][-1]:
            open_price = quote['open'][-1]
        if quote.get('high') and quote['high'][-1]:
            high = quote['high'][-1]
        if quote.get('low') and quote['low'][-1]:
            low = quote['low'][-1]
        if quote.get('volume') and quote['volume'][-1]:
            volume = quote['volume'][-1]

        # 获取行业信息
        stock_info = STOCK_INFO.get(code, {"name": meta.get('shortName', code), "industry": ""})

        return {
            "code": code,
            "name": stock_info["name"],
            "price": round(float(price), 2),
            "change": round(float(change), 2),
            "open": round(float(open_price), 2) if open_price else round(float(price), 2),
            "high": round(float(high), 2) if high else round(float(price), 2),
            "low": round(float(low), 2) if low else round(float(price), 2),
            "prev_close": round(float(prev_close), 2) if prev_close else 0,  # 昨收
            "volume": int(volume) if volume else 0,
            "amount": 0,
            "turnover": 0,
            "market_cap": 0,
            "industry": stock_info.get("industry", ""),
        }

    except Exception as e:
        print(f"[Yahoo] Error fetching realtime for {code}: {e}")
        return None


def get_market_indices() -> dict:
    """
    获取大盘指数

    Returns:
        dict with sh_index, sz_index, etc.
    """
    result = {
        'sh_index': 0,
        'sh_change': 0,
        'sz_index': 0,
        'sz_change': 0,
        'sentiment': '中性'
    }

    # 计算时间范围（最近 5 天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    period1 = int(start_date.timestamp())
    period2 = int(end_date.timestamp())

    # 上证指数 000001.SS
    try:
        sh_data = _fetch_yahoo_chart("000001.SS", period1, period2)
        if sh_data:
            meta = sh_data.get('meta', {})
            price = meta.get('regularMarketPrice', 0)
            prev_close = meta.get('chartPreviousClose', price)

            if not price:
                quote = sh_data.get('indicators', {}).get('quote', [{}])[0]
                closes = [c for c in quote.get('close', []) if c is not None]
                if closes:
                    price = closes[-1]
                    prev_close = closes[-2] if len(closes) > 1 else price

            if price:
                result['sh_index'] = round(float(price), 2)
                result['sh_change'] = round(((price - prev_close) / prev_close * 100) if prev_close else 0, 2)
    except Exception as e:
        print(f"[Yahoo] Error fetching SH index: {e}")

    # 深证成指 399001.SZ
    try:
        sz_data = _fetch_yahoo_chart("399001.SZ", period1, period2)
        if sz_data:
            meta = sz_data.get('meta', {})
            price = meta.get('regularMarketPrice', 0)
            prev_close = meta.get('chartPreviousClose', price)

            if not price:
                quote = sz_data.get('indicators', {}).get('quote', [{}])[0]
                closes = [c for c in quote.get('close', []) if c is not None]
                if closes:
                    price = closes[-1]
                    prev_close = closes[-2] if len(closes) > 1 else price

            if price:
                result['sz_index'] = round(float(price), 2)
                result['sz_change'] = round(((price - prev_close) / prev_close * 100) if prev_close else 0, 2)
    except Exception as e:
        print(f"[Yahoo] Error fetching SZ index: {e}")

    # 判断市场情绪
    avg_change = (result['sh_change'] + result['sz_change']) / 2
    if avg_change > 1:
        result['sentiment'] = '偏多'
    elif avg_change < -1:
        result['sentiment'] = '偏空'
    else:
        result['sentiment'] = '中性'

    return result


def search_stocks(keyword: str, limit: int = 20) -> list[dict]:
    """
    搜索股票 (从预定义列表中搜索)
    """
    results = []

    for code, name, industry in STOCK_LIST:
        if keyword in code or keyword in name:
            # 获取实时价格
            realtime = get_stock_realtime(code)
            if realtime:
                results.append({
                    "code": code,
                    "name": name,
                    "price": realtime["price"],
                    "change": realtime["change"],
                })
            else:
                results.append({
                    "code": code,
                    "name": name,
                    "price": 0,
                    "change": 0,
                })

        if len(results) >= limit:
            break

    return results


# 兼容接口
def get_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """智能获取历史数据"""
    return get_stock_history(code, days)


def get_realtime(code: str) -> Optional[dict]:
    """智能获取实时行情"""
    return get_stock_realtime(code)
