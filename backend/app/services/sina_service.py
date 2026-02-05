"""
新浪财经 API 数据获取服务
从境外访问更稳定，替代 AKShare
"""

import json
import re
import time
import urllib.request
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict

# 配置
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3

# 预定义的股票列表 (用于搜索)
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
    # 新增热门股
    ("002873", "新天药业", "医药"), ("600519", "贵州茅台", "白酒"),
]

# 构建股票代码到信息的映射
STOCK_INFO = {code: {"name": name, "industry": industry} for code, name, industry in STOCK_LIST}


def _get_symbol(code: str) -> str:
    """转换股票代码为新浪格式"""
    if code.startswith('6') or code.startswith('9'):
        return f'sh{code}'
    else:
        return f'sz{code}'


def get_stock_realtime(code: str) -> Optional[dict]:
    """
    获取单只股票实时行情

    Args:
        code: 股票代码 (如 600519, 000001)

    Returns:
        dict with price, change, etc.
    """
    symbol = _get_symbol(code)
    url = f'http://hq.sinajs.cn/list={symbol}'

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('Referer', 'http://finance.sina.com.cn')
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('gbk')

            match = re.search(r'hq_str_\w+="(.+)"', content)
            if not match:
                return None

            data = match.group(1).split(',')
            if len(data) < 32 or not data[3]:
                return None

            price = float(data[3])
            yesterday_close = float(data[2]) if data[2] else price
            change = (price - yesterday_close) / yesterday_close * 100 if yesterday_close else 0

            # 获取行业信息
            info = STOCK_INFO.get(code, {"name": data[0], "industry": ""})

            return {
                "code": code,
                "name": data[0],
                "price": price,
                "change": round(change, 2),
                "open": float(data[1]) if data[1] else 0,
                "high": float(data[4]) if data[4] else 0,
                "low": float(data[5]) if data[5] else 0,
                "volume": float(data[8]) / 100 if data[8] else 0,  # 转换为手
                "amount": float(data[9]) if data[9] else 0,
                "turnover": 0,  # 新浪API不提供换手率
                "market_cap": 0,  # 需要额外计算
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
    symbol = _get_symbol(code)
    url = (f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/'
           f'CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={days + 30}')

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
    url = 'http://hq.sinajs.cn/list=sh000001,sz399001'

    for retry in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            req.add_header('Referer', 'http://finance.sina.com.cn')
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read().decode('gbk')

            result = {
                'sh_index': 3000,
                'sh_change': 0,
                'sz_index': 10000,
                'sz_change': 0,
                'sentiment': '中性'
            }

            for line in content.strip().split('\n'):
                if 'sh000001' in line:
                    match = re.search(r'"(.+)"', line)
                    if match:
                        data = match.group(1).split(',')
                        if len(data) >= 4 and data[3]:
                            price = float(data[3])
                            yesterday = float(data[2]) if data[2] else price
                            change = (price - yesterday) / yesterday * 100 if yesterday else 0
                            result['sh_index'] = round(price, 2)
                            result['sh_change'] = round(change, 2)
                elif 'sz399001' in line:
                    match = re.search(r'"(.+)"', line)
                    if match:
                        data = match.group(1).split(',')
                        if len(data) >= 4 and data[3]:
                            price = float(data[3])
                            yesterday = float(data[2]) if data[2] else price
                            change = (price - yesterday) / yesterday * 100 if yesterday else 0
                            result['sz_index'] = round(price, 2)
                            result['sz_change'] = round(change, 2)

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


# 兼容 akshare_service 的接口
def get_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """智能获取历史数据"""
    return get_stock_history(code, days)


def get_realtime(code: str) -> Optional[dict]:
    """智能获取实时行情"""
    return get_stock_realtime(code)
