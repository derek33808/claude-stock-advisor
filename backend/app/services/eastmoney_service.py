"""
东方财富 API 数据获取服务
全球可访问，用于获取 A 股实时和历史数据

增加了自动 fallback 到新浪财经的逻辑，当东方财富 API 不可用时自动切换
"""

import json
import time
import urllib.request
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# 配置
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

# 数据源状态追踪
_eastmoney_available = True
_last_eastmoney_check = None
_eastmoney_check_interval = timedelta(minutes=5)  # 5分钟后重试东方财富

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


def _get_market_code(code: str) -> str:
    """
    获取市场代码: 1=沪市, 0=深市

    上海市场 (1):
      - 60xxxx: 沪市A股主板
      - 68xxxx: 科创板
      - 9xxxxx: B股
      - 5xxxxx: 沪市ETF/LOF (510, 511, 512, 513, 515, 516, 518, 560, 588等)
      - 11xxxx: 可转债

    深圳市场 (0):
      - 00xxxx: 深市A股主板
      - 30xxxx: 创业板
      - 2xxxxx: B股
      - 159xxx: 深市ETF
      - 12xxxx: 可转债
    """
    # 上海市场
    if code.startswith('6'):  # 60xxxx 主板, 68xxxx 科创板
        return '1'
    if code.startswith('9'):  # B股
        return '1'
    if code.startswith('5'):  # 沪市ETF/LOF: 510, 511, 512, 513, 515, 516, 518, 560, 588等
        return '1'
    if code.startswith('11'):  # 沪市可转债
        return '1'

    # 深圳市场 (默认)
    # 00xxxx 深市主板, 30xxxx 创业板, 159xxx 深市ETF, 12xxxx 可转债
    return '0'


def get_stock_realtime(code: str) -> Optional[dict]:
    """
    获取单只股票实时行情

    Args:
        code: 股票代码 (如 600519, 000001)

    Returns:
        dict with price, change, etc.
    """
    market = _get_market_code(code)
    url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f58,f43,f44,f45,f46,f47,f48,f60,f170,f116'

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Referer', 'https://quote.eastmoney.com')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('utf-8')

            data = json.loads(content)
            if data.get('rc') != 0 or not data.get('data'):
                return None

            d = data['data']

            # ETF (5开头) 价格单位是厘(1/1000元)，普通股票是分(1/100元)
            is_etf = code.startswith('5') or code.startswith('159')
            price_divisor = 1000 if is_etf else 100

            price = d.get('f43', 0) / price_divisor if d.get('f43') else 0
            high = d.get('f44', 0) / price_divisor if d.get('f44') else 0
            low = d.get('f45', 0) / price_divisor if d.get('f45') else 0
            open_price = d.get('f46', 0) / price_divisor if d.get('f46') else 0
            prev_close = d.get('f60', 0) / price_divisor if d.get('f60') else price
            volume = d.get('f47', 0)  # 手
            amount = d.get('f48', 0)  # 元
            change = d.get('f170', 0) / 100 if d.get('f170') else 0  # 涨跌幅百分比
            market_cap = d.get('f116', 0) / 100000000 if d.get('f116') else 0  # 转为亿

            # 获取行业信息
            info = STOCK_INFO.get(code, {"name": d.get('f58', code), "industry": ""})

            return {
                "code": code,
                "name": d.get('f58', info["name"]),
                "price": round(price, 2),
                "change": round(change, 2),
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "prev_close": round(prev_close, 2),  # 昨收
                "volume": volume,
                "amount": amount,
                "turnover": 0,
                "market_cap": round(market_cap, 2),
                "industry": info.get("industry", ""),
            }

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                time.sleep(0.5)
                continue
            print(f"Error fetching realtime for {code}: {e}")
            return None

    return None


def get_stock_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    获取股票历史 K 线数据

    Args:
        code: 股票代码
        days: 获取天数

    Returns:
        DataFrame with columns: date, open, high, low, close, volume
    """
    market = _get_market_code(code)
    # klt=101 为日K
    url = (f'https://push2his.eastmoney.com/api/qt/stock/kline/get?'
           f'secid={market}.{code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&'
           f'klt=101&fqt=1&end=20500101&lmt={days + 30}')

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Referer', 'https://quote.eastmoney.com')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('utf-8')

            data = json.loads(content)
            if data.get('rc') != 0 or not data.get('data') or not data['data'].get('klines'):
                return None

            klines = data['data']['klines']

            records = []
            for line in klines:
                parts = line.split(',')
                if len(parts) >= 7:
                    records.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]),
                        'amount': float(parts[6]) if len(parts) > 6 else 0,
                    })

            if not records:
                return None

            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])

            # 只返回最近 N 天
            df = df.sort_values('date').tail(days).reset_index(drop=True)
            return df

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                time.sleep(0.5)
                continue
            print(f"Error fetching history for {code}: {e}")
            return None

    return None


def get_market_indices() -> dict:
    """
    获取大盘指数

    Returns:
        dict with sh_index, sz_index, etc.
    """
    # 上证指数: 1.000001, 深证成指: 0.399001
    url = 'https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids=1.000001,0.399001&fields=f3,f2,f14'

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            req.add_header('Referer', 'https://quote.eastmoney.com')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('utf-8')

            data = json.loads(content)

            result = {
                'sh_index': 3000,
                'sh_change': 0,
                'sz_index': 10000,
                'sz_change': 0,
                'sentiment': '中性'
            }

            if data.get('rc') == 0 and data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    name = item.get('f14', '')
                    price = item.get('f2', 0)
                    change = item.get('f3', 0)

                    if '上证' in name:
                        result['sh_index'] = round(price, 2)
                        result['sh_change'] = round(change, 2)
                    elif '深证' in name:
                        result['sz_index'] = round(price, 2)
                        result['sz_change'] = round(change, 2)

            # 判断市场情绪
            avg_change = (result['sh_change'] + result['sz_change']) / 2
            if avg_change > 1:
                result['sentiment'] = '偏多'
            elif avg_change < -1:
                result['sentiment'] = '偏空'
            else:
                result['sentiment'] = '中性'

            return result

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                time.sleep(0.5)
                continue
            print(f"Error fetching market indices: {e}")

    return {
        'sh_index': 0,
        'sh_change': 0,
        'sz_index': 0,
        'sz_change': 0,
        'sentiment': '未知'
    }


def search_stocks(keyword: str, limit: int = 20) -> list[dict]:
    """
    搜索股票 (从预定义列表中搜索)

    Args:
        keyword: 关键词
        limit: 返回数量

    Returns:
        list of {code, name, price, change}
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


# 兼容接口 - 带自动 fallback 到 Yahoo Finance（全球可访问）
def get_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    智能获取历史数据，东方财富失败时自动切换到 Yahoo Finance
    """
    global _eastmoney_available, _last_eastmoney_check

    # 检查是否需要重试东方财富
    if not _eastmoney_available and _last_eastmoney_check:
        if datetime.now() - _last_eastmoney_check > _eastmoney_check_interval:
            _eastmoney_available = True  # 重新尝试东方财富

    # 首先尝试东方财富
    if _eastmoney_available:
        result = get_stock_history(code, days)
        if result is not None and not result.empty:
            return result
        # 东方财富失败，标记为不可用
        print(f"[Fallback] 东方财富获取历史数据失败 {code}，切换到 Yahoo Finance")
        _eastmoney_available = False
        _last_eastmoney_check = datetime.now()

    # 尝试 Yahoo Finance（全球可访问）
    try:
        from app.services import yahoo_service
        result = yahoo_service.get_stock_history(code, days)
        if result is not None and not result.empty:
            print(f"[Fallback] 使用 Yahoo Finance 获取历史数据成功 {code}")
            return result
    except Exception as e:
        print(f"[Fallback] Yahoo Finance 也失败了 {code}: {e}")

    return None


def get_realtime(code: str) -> Optional[dict]:
    """
    获取实时行情，每次请求都先尝试东方财富，失败再用 Yahoo
    """
    # 每次请求都先尝试东方财富（不使用全局状态，避免一次失败影响后续请求）
    result = get_stock_realtime(code)
    if result is not None:
        return result

    # 东方财富失败，尝试 Yahoo Finance
    print(f"[Fallback] 东方财富获取实时行情失败 {code}，尝试 Yahoo Finance")
    try:
        from app.services import yahoo_service
        result = yahoo_service.get_stock_realtime(code)
        if result is not None:
            print(f"[Fallback] 使用 Yahoo Finance 获取实时行情成功 {code}")
            return result
    except Exception as e:
        print(f"[Fallback] Yahoo Finance 也失败了 {code}: {e}")

    return None


def get_market_indices_with_fallback() -> dict:
    """
    获取大盘指数，东方财富失败时自动切换到 Yahoo Finance
    """
    global _eastmoney_available, _last_eastmoney_check

    # 检查是否需要重试东方财富
    if not _eastmoney_available and _last_eastmoney_check:
        if datetime.now() - _last_eastmoney_check > _eastmoney_check_interval:
            _eastmoney_available = True

    # 首先尝试东方财富
    if _eastmoney_available:
        result = get_market_indices()
        if result and result.get('sh_index', 0) > 0:
            return result
        print("[Fallback] 东方财富获取大盘指数失败，切换到 Yahoo Finance")
        _eastmoney_available = False
        _last_eastmoney_check = datetime.now()

    # 尝试 Yahoo Finance（全球可访问）
    try:
        from app.services import yahoo_service
        result = yahoo_service.get_market_indices()
        if result and result.get('sh_index', 0) > 0:
            print("[Fallback] 使用 Yahoo Finance 获取大盘指数成功")
            return result
    except Exception as e:
        print(f"[Fallback] Yahoo Finance 获取大盘指数也失败了: {e}")

    return {
        'sh_index': 0,
        'sh_change': 0,
        'sz_index': 0,
        'sz_change': 0,
        'sentiment': '未知'
    }
