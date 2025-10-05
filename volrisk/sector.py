"""
行业ETF处理模块
处理行业ETF数据，支持多ETF混合，计算行业层面的风险指标
"""

from typing import Dict, List, Optional
from pathlib import Path
import yaml
import pandas as pd
from pydantic import BaseModel, Field

from .data import DataFetcher
from .metrics import calculate_all_metrics, validate_data_quality


class SectorConfig(BaseModel):
    """行业配置"""
    tickers: List[str] = Field(..., description="ETF代码列表")
    weights: List[float] = Field(..., description="权重列表，必须与tickers长度相同")

    def validate_weights(self):
        """验证权重"""
        if len(self.tickers) != len(self.weights):
            raise ValueError(f"权重数量({len(self.weights)})与ticker数量({len(self.tickers)})不匹配")
        if abs(sum(self.weights) - 1.0) > 0.001:
            raise ValueError(f"权重之和必须为1.0，当前为{sum(self.weights)}")


class SectorsConfig(BaseModel):
    """多行业配置"""
    sectors: Dict[str, SectorConfig]

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'SectorsConfig':
        """从YAML文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


class SectorMetrics:
    """行业指标"""

    def __init__(
        self,
        sector_name: str,
        tickers: List[str],
        weights: List[float],
        sigma_down: float,
        sigma_total: float,
        mdd: float,
        sample_days: int,
        trading_days: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        self.sector_name = sector_name
        self.tickers = tickers
        self.weights = weights
        self.sigma_down = sigma_down
        self.sigma_total = sigma_total
        self.mdd = mdd
        self.sample_days = sample_days
        self.trading_days = trading_days
        self.start_date = start_date
        self.end_date = end_date

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'sector_name': self.sector_name,
            'tickers': ','.join(self.tickers),
            'weights': ','.join([f"{w:.2f}" for w in self.weights]),
            'sigma_down': self.sigma_down,
            'sigma_total': self.sigma_total,
            'mdd': abs(self.mdd),  # 输出为正值
            'sample_days': self.sample_days,
            'trading_days': self.trading_days,
            'start_date': self.start_date,
            'end_date': self.end_date
        }


class SectorAnalyzer:
    """行业分析器"""

    def __init__(self, data_fetcher: Optional[DataFetcher] = None):
        """
        初始化行业分析器

        Args:
            data_fetcher: 数据获取器实例，如果为None则创建新实例
        """
        self.data_fetcher = data_fetcher or DataFetcher()

    def calculate_sector_metrics(
        self,
        sector_name: str,
        tickers: List[str],
        weights: List[float],
        start: Optional[str] = None,
        end: Optional[str] = None,
        period: str = "1y",
        mar: float = 0.0,
        min_days: int = 150
    ) -> Optional[SectorMetrics]:
        """
        计算单个行业的指标

        支持多ETF加权混合

        Args:
            sector_name: 行业名称
            tickers: ETF代码列表
            weights: 权重列表
            start: 开始日期
            end: 结束日期
            period: 时间周期
            mar: 最低可接受收益
            min_days: 最少交易日数

        Returns:
            SectorMetrics对象，如果数据不足则返回None
        """
        if len(tickers) != len(weights):
            print(f"错误: {sector_name} 的ticker数量与权重数量不匹配")
            return None

        if abs(sum(weights) - 1.0) > 0.001:
            print(f"警告: {sector_name} 的权重之和不为1.0: {sum(weights)}")

        # 获取所有ETF的数据
        all_metrics = []
        all_data = []

        for ticker in tickers:
            adj_close = self.data_fetcher.fetch(
                ticker,
                start=start,
                end=end,
                period=period
            )

            if adj_close is None:
                print(f"错误: 无法获取 {ticker} 的数据")
                return None

            # 验证数据质量
            valid, error_msg = validate_data_quality(adj_close, min_days)
            if not valid:
                print(f"错误: {ticker} 数据质量不足: {error_msg}")
                return None

            # 计算指标
            metrics = calculate_all_metrics(adj_close, mar)
            all_metrics.append(metrics)
            all_data.append(adj_close)

        # 加权平均计算行业指标
        weighted_sigma_down = sum(
            m['sigma_down'] * w for m, w in zip(all_metrics, weights)
        )
        weighted_sigma_total = sum(
            m['sigma_total'] * w for m, w in zip(all_metrics, weights)
        )
        weighted_mdd = sum(
            m['mdd'] * w for m, w in zip(all_metrics, weights)
        )

        # 使用第一个ETF的日期范围（假设对齐）
        first_data = all_data[0]
        start_date = str(first_data.index[0].date()) if len(first_data) > 0 else None
        end_date = str(first_data.index[-1].date()) if len(first_data) > 0 else None

        return SectorMetrics(
            sector_name=sector_name,
            tickers=tickers,
            weights=weights,
            sigma_down=weighted_sigma_down,
            sigma_total=weighted_sigma_total,
            mdd=weighted_mdd,
            sample_days=all_metrics[0]['sample_days'],
            trading_days=all_metrics[0]['trading_days'],
            start_date=start_date,
            end_date=end_date
        )

    def calculate_all_sectors(
        self,
        config: SectorsConfig,
        **kwargs
    ) -> Dict[str, SectorMetrics]:
        """
        计算所有行业的指标

        Args:
            config: 行业配置
            **kwargs: 传递给calculate_sector_metrics的参数

        Returns:
            字典，键为行业名称，值为SectorMetrics对象
        """
        results = {}

        for sector_name, sector_config in config.sectors.items():
            print(f"\n正在计算 {sector_name} 的指标...")

            try:
                sector_config.validate_weights()
            except ValueError as e:
                print(f"错误: {sector_name} 配置无效: {e}")
                continue

            metrics = self.calculate_sector_metrics(
                sector_name=sector_name,
                tickers=sector_config.tickers,
                weights=sector_config.weights,
                **kwargs
            )

            if metrics is not None:
                results[sector_name] = metrics
                print(f"✓ {sector_name}: σ_down={metrics.sigma_down:.4f}, "
                      f"σ_total={metrics.sigma_total:.4f}, MDD={abs(metrics.mdd):.4f}")
            else:
                print(f"✗ {sector_name}: 计算失败")

        return results

    def calculate_mixed_sector_metrics(
        self,
        sector_mix: Dict[str, float],
        sector_metrics_dict: Dict[str, SectorMetrics]
    ) -> Optional[Dict[str, float]]:
        """
        计算混合行业的指标（如紫金矿业的60%有色+40%黄金）

        Args:
            sector_mix: 行业权重字典，如 {"NONFER": 0.6, "GOLD": 0.4}
            sector_metrics_dict: 已计算的行业指标字典

        Returns:
            混合后的指标字典
        """
        if abs(sum(sector_mix.values()) - 1.0) > 0.001:
            print(f"警告: 混合权重之和不为1.0: {sum(sector_mix.values())}")

        # 检查所有行业是否都有数据
        for sector_name in sector_mix.keys():
            if sector_name not in sector_metrics_dict:
                print(f"错误: 行业 {sector_name} 没有指标数据")
                return None

        # 加权平均
        sigma_down = sum(
            sector_metrics_dict[s].sigma_down * w
            for s, w in sector_mix.items()
        )
        sigma_total = sum(
            sector_metrics_dict[s].sigma_total * w
            for s, w in sector_mix.items()
        )
        mdd = sum(
            sector_metrics_dict[s].mdd * w
            for s, w in sector_mix.items()
        )

        return {
            'sigma_down': sigma_down,
            'sigma_total': sigma_total,
            'mdd': mdd
        }
