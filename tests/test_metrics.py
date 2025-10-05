"""
测试指标计算模块
"""

import numpy as np
import pandas as pd
import pytest
from volrisk.metrics import (
    semidev_annual,
    total_volatility_annual,
    max_drawdown,
    calculate_all_metrics,
    validate_data_quality
)


def test_semidev_annual():
    """测试下行标准差计算"""
    # 创建测试数据：包含上涨和下跌
    prices = pd.Series([100, 102, 98, 103, 97, 105])

    sigma_down = semidev_annual(prices, mar=0.0)

    # 应该只计算负收益部分
    assert sigma_down > 0
    assert not np.isnan(sigma_down)


def test_total_volatility_annual():
    """测试总波动率计算"""
    prices = pd.Series([100, 102, 98, 103, 97, 105])

    sigma_total = total_volatility_annual(prices)

    assert sigma_total > 0
    assert not np.isnan(sigma_total)


def test_max_drawdown():
    """测试最大回撤计算"""
    # 创建有明显回撤的价格序列
    prices = pd.Series([100, 110, 120, 90, 100, 110])

    mdd = max_drawdown(prices)

    # 从120跌到90，回撤应该是 (90-120)/120 = -0.25
    assert mdd < 0
    assert abs(mdd - (-0.25)) < 0.01


def test_calculate_all_metrics():
    """测试计算所有指标"""
    prices = pd.Series([100, 102, 98, 103, 97, 105, 110, 108, 112, 115])

    metrics = calculate_all_metrics(prices)

    assert 'sigma_down' in metrics
    assert 'sigma_total' in metrics
    assert 'mdd' in metrics
    assert 'sample_days' in metrics
    assert 'trading_days' in metrics

    assert metrics['sigma_down'] > 0
    assert metrics['sigma_total'] > 0
    assert metrics['mdd'] < 0
    assert metrics['sample_days'] == len(prices)


def test_validate_data_quality():
    """测试数据质量验证"""
    # 足够的数据
    good_prices = pd.Series(range(200))
    valid, msg = validate_data_quality(good_prices, min_days=150)
    assert valid
    assert msg == ""

    # 数据不足
    bad_prices = pd.Series(range(100))
    valid, msg = validate_data_quality(bad_prices, min_days=150)
    assert not valid
    assert "不足" in msg

    # 空数据
    empty_prices = pd.Series([])
    valid, msg = validate_data_quality(empty_prices)
    assert not valid


def test_semidev_only_downside():
    """测试下行标准差只考虑下行波动"""
    # 创建只有上涨的序列
    up_only = pd.Series([100, 101, 102, 103, 104, 105])
    sigma_down_up = semidev_annual(up_only, mar=0.0)

    # 应该接近0（因为没有负收益）
    assert sigma_down_up >= 0
    assert sigma_down_up < 0.01  # 非常小

    # 创建有下跌的序列
    mixed = pd.Series([100, 95, 98, 92, 96, 90])
    sigma_down_mixed = semidev_annual(mixed, mar=0.0)

    # 应该明显大于只上涨的情况
    assert sigma_down_mixed > sigma_down_up
