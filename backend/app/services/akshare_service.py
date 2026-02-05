"""
AKShare 数据获取服务
获取 A 股和 ETF 的实时行情和历史数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import time

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1  # 秒


def get_stock_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    获取股票历史日线数据

    Args:
        code: 股票代码 (如 "600519" 或 "000001")
        days: 获取天数

    Returns:
        DataFrame with columns: date, open, high, low, close, volume, amount
    """
    try:
        # 计算日期范围
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

        # 尝试获取股票数据
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"  # 前复权
        )

        if df.empty:
            return None

        # 重命名列
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "change",
            "换手率": "turnover",
        })

        # 只保留最近 N 天
        df = df.tail(days).reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Error fetching stock {code}: {e}")
        return None


def get_etf_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    获取 ETF 历史日线数据

    Args:
        code: ETF 代码 (如 "512930", "159915")
        days: 获取天数

    Returns:
        DataFrame with columns: date, open, high, low, close, volume, amount
    """
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

        df = ak.fund_etf_hist_em(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )

        if df.empty:
            return None

        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "change",
            "换手率": "turnover",
        })

        df = df.tail(days).reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Error fetching ETF {code}: {e}")
        return None


def get_stock_realtime(code: str) -> Optional[dict]:
    """
    获取股票实时行情

    Args:
        code: 股票代码

    Returns:
        dict with price, change, open, high, low, volume, amount
    """
    try:
        # 获取全市场行情
        df = ak.stock_zh_a_spot_em()

        # 查找指定股票
        row = df[df["代码"] == code]

        if row.empty:
            return None

        row = row.iloc[0]

        return {
            "code": code,
            "name": row["名称"],
            "price": float(row["最新价"]) if pd.notna(row["最新价"]) else 0,
            "change": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else 0,
            "open": float(row["今开"]) if pd.notna(row["今开"]) else 0,
            "high": float(row["最高"]) if pd.notna(row["最高"]) else 0,
            "low": float(row["最低"]) if pd.notna(row["最低"]) else 0,
            "volume": float(row["成交量"]) if pd.notna(row["成交量"]) else 0,
            "amount": float(row["成交额"]) if pd.notna(row["成交额"]) else 0,
            "turnover": float(row["换手率"]) if pd.notna(row["换手率"]) else 0,
            "market_cap": float(row["总市值"]) / 100000000 if pd.notna(row["总市值"]) else 0,  # 转换为亿
            "industry": row.get("所属行业", ""),
        }

    except Exception as e:
        print(f"Error fetching realtime for {code}: {e}")
        return None


def get_etf_realtime(code: str) -> Optional[dict]:
    """
    获取 ETF 实时行情

    Args:
        code: ETF 代码

    Returns:
        dict with price, change, etc.
    """
    try:
        df = ak.fund_etf_spot_em()

        row = df[df["代码"] == code]

        if row.empty:
            return None

        row = row.iloc[0]

        return {
            "code": code,
            "name": row["名称"],
            "price": float(row["最新价"]) if pd.notna(row["最新价"]) else 0,
            "change": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else 0,
            "open": float(row["今开"]) if pd.notna(row["今开"]) else 0,
            "high": float(row["最高"]) if pd.notna(row["最高"]) else 0,
            "low": float(row["最低"]) if pd.notna(row["最低"]) else 0,
            "volume": float(row["成交量"]) if pd.notna(row["成交量"]) else 0,
            "amount": float(row["成交额"]) if pd.notna(row["成交额"]) else 0,
            "industry": "ETF",
        }

    except Exception as e:
        print(f"Error fetching ETF realtime for {code}: {e}")
        return None


def get_history(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """
    智能获取历史数据（自动判断股票或 ETF）

    Args:
        code: 证券代码
        days: 获取天数

    Returns:
        DataFrame
    """
    # 先尝试股票
    df = get_stock_history(code, days)
    if df is not None and not df.empty:
        return df

    # 再尝试 ETF
    df = get_etf_history(code, days)
    return df


def get_realtime(code: str) -> Optional[dict]:
    """
    智能获取实时行情（自动判断股票或 ETF）

    Args:
        code: 证券代码

    Returns:
        dict
    """
    # 先尝试股票
    data = get_stock_realtime(code)
    if data is not None:
        return data

    # 再尝试 ETF
    data = get_etf_realtime(code)
    return data


def get_market_indices() -> dict:
    """
    获取大盘指数

    Returns:
        dict with sh_index, sz_index, etc.
    """
    try:
        df = ak.stock_zh_index_spot_em()

        sh = df[df["代码"] == "000001"]  # 上证指数
        sz = df[df["代码"] == "399001"]  # 深证成指

        sh_index = float(sh["最新价"].iloc[0]) if not sh.empty else 0
        sh_change = float(sh["涨跌幅"].iloc[0]) if not sh.empty else 0
        sz_index = float(sz["最新价"].iloc[0]) if not sz.empty else 0
        sz_change = float(sz["涨跌幅"].iloc[0]) if not sz.empty else 0

        # 判断市场情绪
        avg_change = (sh_change + sz_change) / 2
        if avg_change > 1:
            sentiment = "偏多"
        elif avg_change < -1:
            sentiment = "偏空"
        else:
            sentiment = "中性"

        return {
            "sh_index": round(sh_index, 2),
            "sh_change": round(sh_change, 2),
            "sz_index": round(sz_index, 2),
            "sz_change": round(sz_change, 2),
            "sentiment": sentiment,
        }

    except Exception as e:
        print(f"Error fetching market indices: {e}")
        return {
            "sh_index": 0,
            "sh_change": 0,
            "sz_index": 0,
            "sz_change": 0,
            "sentiment": "未知",
        }


def search_stocks(keyword: str, limit: int = 20) -> list[dict]:
    """
    搜索股票

    Args:
        keyword: 关键词（代码或名称）
        limit: 返回数量限制

    Returns:
        list of {code, name, industry}
    """
    try:
        df = ak.stock_zh_a_spot_em()

        # 按代码或名称搜索
        mask = df["代码"].str.contains(keyword) | df["名称"].str.contains(keyword, na=False)
        results = df[mask].head(limit)

        return [
            {
                "code": row["代码"],
                "name": row["名称"],
                "price": float(row["最新价"]) if pd.notna(row["最新价"]) else 0,
                "change": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else 0,
            }
            for _, row in results.iterrows()
        ]

    except Exception as e:
        print(f"Error searching stocks: {e}")
        return []
