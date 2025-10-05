"""
数据获取模块
使用 yfinance 获取股票和ETF的历史数据，支持本地缓存
"""

import os
import time
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Union
import pandas as pd
import yfinance as yf


class DataFetcher:
    """数据获取器，支持缓存和重试机制"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化数据获取器

        Args:
            cache_dir: 缓存目录，默认为 ~/.cache/volrisk/
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/volrisk")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(
        self,
        ticker: str,
        start: Optional[str],
        end: Optional[str],
        period: Optional[str]
    ) -> Path:
        """生成缓存文件路径"""
        # 创建唯一的缓存键
        cache_key = f"{ticker}_{start}_{end}_{period}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{ticker}_{cache_hash}.parquet"

    def _load_from_cache(self, cache_path: Path, max_age_days: int = 1) -> Optional[pd.DataFrame]:
        """从缓存加载数据"""
        if not cache_path.exists():
            return None

        # 检查缓存文件的年龄
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age > timedelta(days=max_age_days):
            return None

        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            print(f"警告: 读取缓存失败 {cache_path}: {e}")
            return None

    def _save_to_cache(self, df: pd.DataFrame, cache_path: Path):
        """保存数据到缓存"""
        try:
            df.to_parquet(cache_path)
        except Exception as e:
            print(f"警告: 保存缓存失败 {cache_path}: {e}")

    def fetch(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True,
        force_refresh: bool = False,
        max_retries: int = 2
    ) -> Optional[pd.Series]:
        """
        获取股票/ETF的调整后收盘价数据

        Args:
            ticker: 股票代码（如 512480.SS）
            start: 开始日期（YYYY-MM-DD），优先于period
            end: 结束日期（YYYY-MM-DD）
            period: 时间周期（1y, 2y等），当start为None时使用
            interval: 数据间隔（1d=日线）
            use_cache: 是否使用缓存
            force_refresh: 是否强制刷新（忽略缓存）
            max_retries: 最大重试次数

        Returns:
            调整后收盘价的Series，索引为日期
        """
        # 尝试从缓存加载
        cache_path = self._get_cache_path(ticker, start, end, period)
        if use_cache and not force_refresh:
            cached_data = self._load_from_cache(cache_path)
            if cached_data is not None and 'Adj Close' in cached_data.columns:
                return cached_data['Adj Close']

        # 从yfinance获取数据
        for attempt in range(max_retries):
            try:
                # 如果指定了start，使用start/end；否则使用period
                if start is not None:
                    data = yf.download(
                        ticker,
                        start=start,
                        end=end,
                        interval=interval,
                        auto_adjust=True,
                        progress=False
                    )
                else:
                    data = yf.download(
                        ticker,
                        period=period,
                        interval=interval,
                        auto_adjust=True,
                        progress=False
                    )

                if data.empty:
                    print(f"警告: {ticker} 返回空数据")
                    if attempt < max_retries - 1:
                        print(f"重试中... ({attempt + 1}/{max_retries})")
                        time.sleep(1)
                        continue
                    return None

                # 处理多层列索引（当下载多个ticker时）
                if isinstance(data.columns, pd.MultiIndex):
                    data = data.xs(ticker, axis=1, level=1)

                # 确保有Adj Close列
                if 'Adj Close' not in data.columns and 'Close' in data.columns:
                    data['Adj Close'] = data['Close']

                if 'Adj Close' not in data.columns:
                    print(f"错误: {ticker} 没有Adj Close数据")
                    return None

                # 保存到缓存
                if use_cache:
                    self._save_to_cache(data, cache_path)

                # 返回Adj Close序列，去除NaN
                adj_close = data['Adj Close'].dropna()
                return adj_close

            except Exception as e:
                print(f"错误: 获取 {ticker} 数据失败: {e}")
                if attempt < max_retries - 1:
                    print(f"重试中... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    print(f"已达到最大重试次数，放弃获取 {ticker}")
                    return None

        return None

    def fetch_multiple(
        self,
        tickers: list[str],
        **kwargs
    ) -> dict[str, pd.Series]:
        """
        批量获取多个股票的数据

        Args:
            tickers: 股票代码列表
            **kwargs: 传递给fetch的其他参数

        Returns:
            字典，键为ticker，值为Adj Close序列
        """
        results = {}
        for ticker in tickers:
            print(f"正在获取 {ticker} 的数据...")
            data = self.fetch(ticker, **kwargs)
            if data is not None:
                results[ticker] = data
            else:
                print(f"跳过 {ticker}（数据获取失败）")

        return results

    def clear_cache(self, ticker: Optional[str] = None):
        """
        清除缓存

        Args:
            ticker: 如果指定，只清除该ticker的缓存；否则清除所有缓存
        """
        if ticker:
            pattern = f"{ticker}_*.parquet"
        else:
            pattern = "*.parquet"

        deleted = 0
        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
                deleted += 1
            except Exception as e:
                print(f"警告: 删除缓存文件失败 {cache_file}: {e}")

        print(f"已删除 {deleted} 个缓存文件")


# 便捷函数
def fetch_data(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    period: str = "1y",
    **kwargs
) -> Optional[pd.Series]:
    """
    便捷函数：获取单个股票的数据

    Args:
        ticker: 股票代码
        start: 开始日期
        end: 结束日期
        period: 时间周期
        **kwargs: 其他参数

    Returns:
        调整后收盘价序列
    """
    fetcher = DataFetcher()
    return fetcher.fetch(ticker, start=start, end=end, period=period, **kwargs)
