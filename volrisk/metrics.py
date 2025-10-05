"""
指标计算模块
计算下行标准差、总波动率、最大回撤等风险指标
支持时间窗口可调和年化选项
"""

import numpy as np
import pandas as pd
from typing import Optional, Union


def get_returns(adj_close: pd.Series) -> pd.Series:
    """
    计算日收益率序列

    Args:
        adj_close: 调整后收盘价序列

    Returns:
        收益率序列 (r_t = P_t / P_{t-1} - 1)
    """
    return adj_close.pct_change().dropna()


def total_volatility(
    returns: pd.Series,
    annualize: bool = False,
    td_per_year: int = 252
) -> float:
    """
    计算总波动率（标准差）

    Args:
        returns: 收益率序列
        annualize: 是否年化
        td_per_year: 年化交易日数，默认252天

    Returns:
        总波动率（窗口尺度或年化）
    """
    if len(returns) == 0:
        return np.nan

    # 使用总体标准差 ddof=0
    vol = returns.std(ddof=0)

    # 是否年化
    if annualize:
        vol = vol * np.sqrt(td_per_year)

    return vol


def downside_volatility(
    returns: pd.Series,
    mar: float = 0.0,
    annualize: bool = False,
    td_per_year: int = 252
) -> float:
    """
    计算下行波动率（Sortino分母，半方差）

    严格使用日频半方差实测，不使用 σ/√2 估计

    Args:
        returns: 收益率序列
        mar: 最低可接受收益（MAR），默认为0
        annualize: 是否年化
        td_per_year: 年化交易日数

    Returns:
        下行波动率（窗口尺度或年化）
    """
    if len(returns) == 0:
        return np.nan

    # 计算下行偏差：只取低于MAR的收益
    downside = np.minimum(returns - mar, 0.0)

    # 计算半方差的标准差
    semi_variance = np.mean(downside ** 2)
    semi_std = np.sqrt(semi_variance)

    # 是否年化
    if annualize:
        semi_std = semi_std * np.sqrt(td_per_year)

    return semi_std


def max_drawdown(adj_close: pd.Series) -> float:
    """
    计算最大回撤（Maximum Drawdown）

    Args:
        adj_close: 调整后收盘价序列

    Returns:
        最大回撤（负值，如-0.25表示-25%的回撤）
    """
    if len(adj_close) == 0:
        return np.nan

    # 计算累计最大值
    cummax = adj_close.cummax()

    # 计算回撤序列
    drawdown = adj_close / cummax - 1.0

    # 返回最小值（最大回撤，负数）
    mdd = drawdown.min()

    return mdd


def calculate_all_metrics(
    adj_close: pd.Series,
    mar: float = 0.0,
    annualize: bool = True,
    td_per_year: int = 252
) -> dict:
    """
    计算所有风险指标

    Args:
        adj_close: 调整后收盘价序列
        mar: 最低可接受收益
        annualize: 是否年化波动率
        td_per_year: 年化交易日数

    Returns:
        包含所有指标的字典
    """
    returns = get_returns(adj_close)

    return {
        'returns': returns,  # 返回收益率序列（供β回归使用）
        'sigma_total': total_volatility(returns, annualize, td_per_year),
        'sigma_down': downside_volatility(returns, mar, annualize, td_per_year),
        'mdd': max_drawdown(adj_close),
        'sample_days': len(adj_close),
        'trading_days': len(returns),
        'annualize': annualize,
        'td_per_year': td_per_year
    }


def blend_volatilities(
    sector_metrics: dict,
    exposures: dict
) -> tuple[float, float]:
    """
    混合多行业的波动率（线性加权）

    用于处理多行业暴露的公司（如紫金矿业60%有色+40%黄金）

    Args:
        sector_metrics: {sector_name: metrics_dict} 行业指标字典
        exposures: {sector_name: weight} 行业权重字典

    Returns:
        (blended_sigma_total, blended_sigma_down)
    """
    if abs(sum(exposures.values()) - 1.0) > 0.001:
        raise ValueError(f"行业权重之和必须为1.0，当前为{sum(exposures.values())}")

    sigma_total = 0.0
    sigma_down = 0.0

    for sector, weight in exposures.items():
        if sector not in sector_metrics:
            raise ValueError(f"行业 {sector} 没有对应的指标数据")

        sigma_total += sector_metrics[sector]['sigma_total'] * weight
        sigma_down += sector_metrics[sector]['sigma_down'] * weight

    return sigma_total, sigma_down


def validate_data_quality(adj_close: pd.Series, min_days: int = 150) -> tuple[bool, str]:
    """
    验证数据质量

    Args:
        adj_close: 调整后收盘价序列
        min_days: 最少交易日数，默认150天（约半年）

    Returns:
        (是否有效, 错误信息)
    """
    if adj_close is None or len(adj_close) == 0:
        return False, "数据为空"

    if adj_close.isna().all():
        return False, "所有数据都是NaN"

    valid_days = len(adj_close.dropna())
    if valid_days < min_days:
        return False, f"有效交易日不足（{valid_days} < {min_days}）"

    return True, ""


# 向后兼容的函数别名
def semidev_annual(adj_close: pd.Series, mar: float = 0.0, trading_days: int = 252) -> float:
    """向后兼容：年化下行标准差"""
    returns = get_returns(adj_close)
    return downside_volatility(returns, mar, annualize=True, td_per_year=trading_days)


def total_volatility_annual(adj_close: pd.Series, trading_days: int = 252) -> float:
    """向后兼容：年化总波动率"""
    returns = get_returns(adj_close)
    return total_volatility(returns, annualize=True, td_per_year=trading_days)
