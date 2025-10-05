"""
测试风险计算模块
"""

import pytest
from volrisk.risk import (
    risk_semimdd,
    risk_scheme_c,
    calculate_risk,
    RiskConfig,
    RiskCalculator
)


def test_risk_semimdd():
    """测试 SemiMDD 风险计算"""
    sigma_down = 0.25
    mdd = -0.30
    idio = 1.10
    w = 0.5
    fragility_add = 0.025

    result = risk_semimdd(sigma_down, mdd, idio, w, fragility_add)

    assert 'total_risk' in result
    assert 'downside_component' in result
    assert 'mdd_component' in result
    assert 'mode' in result

    # 验证计算
    expected_downside = w * (sigma_down * idio)
    expected_mdd = (1 - w) * abs(mdd)
    expected_total = expected_downside + expected_mdd + fragility_add

    assert abs(result['downside_component'] - expected_downside) < 1e-6
    assert abs(result['mdd_component'] - expected_mdd) < 1e-6
    assert abs(result['total_risk'] - expected_total) < 1e-6
    assert result['mode'] == 'SemiMDD'


def test_risk_scheme_c():
    """测试 SchemeC 风险计算"""
    sigma_down = 0.25
    sigma_total = 0.30
    beta = 1.15
    fragility_add = 0.03

    result = risk_scheme_c(sigma_down, sigma_total, beta, fragility_add)

    assert 'total_risk' in result
    assert 'downside_component' in result
    assert 'total_vol_component' in result
    assert 'fragility_component' in result

    # 验证计算
    expected_downside = 0.6 * sigma_down
    expected_total_vol = 0.3 * (beta * sigma_total)
    expected_fragility = 0.1 * fragility_add
    expected_total = expected_downside + expected_total_vol + expected_fragility

    assert abs(result['downside_component'] - expected_downside) < 1e-6
    assert abs(result['total_vol_component'] - expected_total_vol) < 1e-6
    assert abs(result['fragility_component'] - expected_fragility) < 1e-6
    assert abs(result['total_risk'] - expected_total) < 1e-6
    assert result['mode'] == 'SchemeC'


def test_calculate_risk_semimdd():
    """测试使用配置计算 SemiMDD 风险"""
    config = RiskConfig(
        mode="SemiMDD",
        idio=1.10,
        w=0.5,
        fragility_add=0.02
    )

    result = calculate_risk(
        sigma_down=0.25,
        sigma_total=0.30,
        mdd=-0.28,
        config=config
    )

    assert result['mode'] == 'SemiMDD'
    assert result['total_risk'] > 0


def test_calculate_risk_scheme_c():
    """测试使用配置计算 SchemeC 风险"""
    config = RiskConfig(
        mode="SchemeC",
        beta=1.20,
        fragility_add=0.03
    )

    result = calculate_risk(
        sigma_down=0.25,
        sigma_total=0.30,
        mdd=-0.28,
        config=config
    )

    assert result['mode'] == 'SchemeC'
    assert result['total_risk'] > 0


def test_value_to_risk_ratio():
    """测试值博率计算"""
    expected_return = 0.40
    loss_risk = 0.20

    ratio = RiskCalculator.value_to_risk_ratio(expected_return, loss_risk)

    assert ratio == 2.0

    # 测试边界情况
    ratio_zero_risk = RiskCalculator.value_to_risk_ratio(0.5, 0)
    assert ratio_zero_risk == float('inf')


def test_risk_config_validation():
    """测试风险配置验证"""
    # 有效配置
    config1 = RiskConfig(mode="SemiMDD", idio=1.0, w=0.5)
    assert config1.mode == "SemiMDD"

    config2 = RiskConfig(mode="SchemeC", beta=1.2)
    assert config2.mode == "SchemeC"

    # 测试默认值
    config3 = RiskConfig()
    assert config3.mode == "SemiMDD"
    assert config3.w == 0.5
    assert config3.idio == 1.0
    assert config3.fragility_add == 0.0
