"""
风险计算模块
完整的 Scheme C 风险模型实现
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class SchemeC_Weights(BaseModel):
    """Scheme C 权重配置"""
    w_down: float = Field(default=0.6, description="下行波动权重", ge=0, le=1)
    w_beta: float = Field(default=0.3, description="β×总波动权重", ge=0, le=1)
    w_frag: float = Field(default=0.1, description="脆弱度权重", ge=0, le=1)

    def validate_weights(self):
        """验证权重之和为1.0"""
        total = self.w_down + self.w_beta + self.w_frag
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Scheme C权重之和必须为1.0，当前为{total}")


class RiskConfig(BaseModel):
    """风险计算配置"""
    mode: Literal["SemiMDD", "SchemeC"] = Field(default="SchemeC", description="风险计算模式")

    # SchemeC 模式参数（新版，优先）
    beta: Optional[float] = Field(default=None, description="β系数（相对行业敏感度）", ge=0)
    frag: float = Field(default=0.0, description="脆弱度加点（百分点，如1.5表示1.5%）", ge=0, le=10.0)
    scheme_c_weights: Optional[SchemeC_Weights] = Field(
        default_factory=SchemeC_Weights,
        description="Scheme C权重配置"
    )

    # SemiMDD 模式参数（向后兼容）
    idio: float = Field(default=1.0, description="个体下行放大/收敛系数", ge=0.7, le=1.5)
    w: float = Field(default=0.5, description="SemiMDD权重", ge=0, le=1)

    # 通用参数（向后兼容）
    fragility_add: float = Field(default=0.0, description="脆弱度绝对加点（向后兼容）", ge=0, le=0.1)

    def model_post_init(self, __context):
        """后初始化：合并frag和fragility_add"""
        # 如果使用了旧参数fragility_add，转换为百分点
        if self.fragility_add > 0:
            self.frag = max(self.frag, self.fragility_add * 100)

        # 验证Scheme C权重
        if self.scheme_c_weights:
            self.scheme_c_weights.validate_weights()


def scheme_c_loss_risk(
    sigma_down: float,
    sigma_total: float,
    beta: float = 1.0,
    frag: float = 0.0,
    weights: Optional[SchemeC_Weights] = None
) -> dict:
    """
    计算 Scheme C 损失风险

    公式：
    LossRisk = w_down × σ_down + w_beta × (β × σ_total) + w_frag × Frag

    Args:
        sigma_down: 行业下行波动率
        sigma_total: 行业总波动率
        beta: 个股β系数（回归实测或先验）
        frag: 脆弱度加点（百分点，如1.5表示0.015）
        weights: Scheme C权重配置

    Returns:
        包含总风险和各组成部分的字典
    """
    if weights is None:
        weights = SchemeC_Weights()

    weights.validate_weights()

    # 转换frag为小数形式
    frag_decimal = frag / 100.0

    # 三项分解
    downside_component = weights.w_down * sigma_down
    beta_component = weights.w_beta * (beta * sigma_total)
    fragility_component = weights.w_frag * frag_decimal

    # 总风险
    total_risk = downside_component + beta_component + fragility_component

    return {
        'total_risk': total_risk,
        'downside_component': downside_component,
        'beta_component': beta_component,
        'fragility_component': fragility_component,
        'mode': 'SchemeC',
        'params': {
            'sigma_down': sigma_down,
            'sigma_total': sigma_total,
            'beta': beta,
            'frag': frag,
            'w_down': weights.w_down,
            'w_beta': weights.w_beta,
            'w_frag': weights.w_frag
        }
    }


def risk_semimdd(
    sigma_down: float,
    mdd: float,
    idio: float = 1.0,
    w: float = 0.5,
    fragility_add: float = 0.0
) -> dict:
    """
    计算 SemiMDD 风险（向后兼容）

    公式：
    LossRisk = w × (σ_down × Idio) + (1-w) × |MDD| + FragilityAdd

    Args:
        sigma_down: 行业下行标准差（年化）
        mdd: 行业最大回撤（负值）
        idio: 个体下行放大/收敛系数（≥0.7, ≤1.5）
        w: 权重（默认0.5）
        fragility_add: 脆弱度绝对加点（0~0.1）

    Returns:
        包含总风险和各组成部分的字典
    """
    # 下行波动部分
    downside_component = w * (sigma_down * idio)

    # MDD部分（取绝对值）
    mdd_component = (1 - w) * abs(mdd)

    # 总风险
    total_risk = downside_component + mdd_component + fragility_add

    return {
        'total_risk': total_risk,
        'downside_component': downside_component,
        'mdd_component': mdd_component,
        'fragility_add': fragility_add,
        'mode': 'SemiMDD',
        'params': {
            'sigma_down': sigma_down,
            'mdd': mdd,
            'idio': idio,
            'w': w
        }
    }


def risk_scheme_c(
    sigma_down: float,
    sigma_total: float,
    beta: float = 1.0,
    fragility_add: float = 0.0
) -> dict:
    """
    计算 SchemeC 风险（向后兼容，旧版API）

    Args:
        sigma_down: 行业下行标准差（年化）
        sigma_total: 行业总波动率（年化）
        beta: 公司对行业的敏感度系数
        fragility_add: 脆弱度绝对加点（0~0.1）

    Returns:
        包含总风险和各组成部分的字典
    """
    # 使用旧版固定权重 0.6/0.3/0.1
    # 下行波动部分（60%）
    downside_component = 0.6 * sigma_down

    # 总波动部分（30%）
    total_vol_component = 0.3 * (beta * sigma_total)

    # 脆弱度部分（10%）
    fragility_component = 0.1 * fragility_add

    # 总风险
    total_risk = downside_component + total_vol_component + fragility_component

    return {
        'total_risk': total_risk,
        'downside_component': downside_component,
        'total_vol_component': total_vol_component,
        'fragility_component': fragility_component,
        'mode': 'SchemeC',
        'params': {
            'sigma_down': sigma_down,
            'sigma_total': sigma_total,
            'beta': beta,
            'fragility_add': fragility_add
        }
    }


def calculate_risk(
    sigma_down: float,
    sigma_total: float,
    mdd: float,
    config: RiskConfig
) -> dict:
    """
    根据配置计算风险

    Args:
        sigma_down: 行业下行标准差
        sigma_total: 行业总波动率
        mdd: 行业最大回撤
        config: 风险配置

    Returns:
        风险计算结果字典
    """
    if config.mode == "SemiMDD":
        return risk_semimdd(
            sigma_down=sigma_down,
            mdd=mdd,
            idio=config.idio,
            w=config.w,
            fragility_add=config.fragility_add
        )
    elif config.mode == "SchemeC":
        # 使用新版Scheme C（支持自定义权重）
        beta = config.beta if config.beta is not None else 1.0
        return scheme_c_loss_risk(
            sigma_down=sigma_down,
            sigma_total=sigma_total,
            beta=beta,
            frag=config.frag,
            weights=config.scheme_c_weights
        )
    else:
        raise ValueError(f"不支持的风险模式: {config.mode}")


class RiskCalculator:
    """风险计算器"""

    @staticmethod
    def semimdd(
        sigma_down: float,
        mdd: float,
        idio: float = 1.0,
        w: float = 0.5,
        fragility_add: float = 0.0
    ) -> float:
        """
        计算 SemiMDD 风险（返回总风险值）

        Args:
            sigma_down: 行业下行标准差
            mdd: 行业最大回撤
            idio: 个体下行放大/收敛系数
            w: 权重
            fragility_add: 脆弱度加点

        Returns:
            总风险值
        """
        result = risk_semimdd(sigma_down, mdd, idio, w, fragility_add)
        return result['total_risk']

    @staticmethod
    def scheme_c(
        sigma_down: float,
        sigma_total: float,
        beta: float = 1.0,
        frag: float = 0.0,
        weights: Optional[SchemeC_Weights] = None
    ) -> float:
        """
        计算 Scheme C 风险（返回总风险值）

        Args:
            sigma_down: 行业下行标准差
            sigma_total: 行业总波动率
            beta: β系数
            frag: 脆弱度加点（百分点）
            weights: Scheme C权重配置

        Returns:
            总风险值
        """
        result = scheme_c_loss_risk(sigma_down, sigma_total, beta, frag, weights)
        return result['total_risk']

    @staticmethod
    def value_to_risk_ratio(expected_return: float, loss_risk: float) -> float:
        """
        计算值博率

        值博率 = 期望收益 / 损失风险

        Args:
            expected_return: 期望收益
            loss_risk: 损失风险

        Returns:
            值博率
        """
        if loss_risk <= 0:
            return float('inf')
        return expected_return / loss_risk
