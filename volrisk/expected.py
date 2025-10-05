"""
期望收益计算模块
支持多种估值倍数模型（PE, EV/EBITDA, EV/Sales）
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class ValuationModel(BaseModel):
    """估值模型配置"""
    type: Literal["PE", "EV/EBITDA", "EV/Sales"] = Field(..., description="估值倍数类型")
    current_multiple: float = Field(..., description="当前倍数", gt=0)
    target_multiple: float = Field(..., description="目标倍数", gt=0)
    growth_12m: float = Field(..., description="未来12个月增长率")
    dividend_yield: float = Field(default=0.0, description="股息率", ge=0)
    buyback_yield: float = Field(default=0.0, description="回购收益率", ge=0)
    execution_prob: float = Field(default=1.0, description="执行概率", ge=0, le=1)


def calculate_expected_return_from_model(model: ValuationModel) -> dict:
    """
    根据估值模型计算期望收益

    公式：
    ER_raw = (TargetMultiple / CurrentMultiple × (1 + growth) - 1)
             + DividendYield + NetBuybackYield
    ER = ER_raw × ExecutionProb

    Args:
        model: 估值模型配置

    Returns:
        字典，包含原始期望收益和执行后期望收益
    """
    # 倍数重定价收益
    multiple_return = (model.target_multiple / model.current_multiple) * (1 + model.growth_12m) - 1

    # 原始期望收益
    er_raw = multiple_return + model.dividend_yield + model.buyback_yield

    # 执行后期望收益
    er = er_raw * model.execution_prob

    return {
        'er_raw': er_raw,
        'er': er,
        'multiple_return': multiple_return,
        'dividend_yield': model.dividend_yield,
        'buyback_yield': model.buyback_yield,
        'execution_prob': model.execution_prob
    }


def calculate_expected_return(
    expected_return: Optional[float] = None,
    model: Optional[ValuationModel] = None
) -> tuple[float, dict]:
    """
    计算期望收益（支持两种方式）

    方式1：直接提供expected_return（主观/快捷）
    方式2：通过model计算（基于估值模型）

    Args:
        expected_return: 直接指定的期望收益（优先使用）
        model: 估值模型（当expected_return为None时使用）

    Returns:
        (期望收益, 详细信息字典)
    """
    if expected_return is not None:
        # 方式1：直接使用提供的期望收益
        return expected_return, {
            'er': expected_return,
            'er_raw': expected_return,
            'source': 'direct'
        }

    if model is not None:
        # 方式2：从模型计算
        details = calculate_expected_return_from_model(model)
        details['source'] = 'model'
        return details['er'], details

    raise ValueError("必须提供 expected_return 或 model 之一")


class ExpectedReturnCalculator:
    """期望收益计算器"""

    @staticmethod
    def from_pe_model(
        current_pe: float,
        target_pe: float,
        eps_growth: float,
        dividend_yield: float = 0.0,
        buyback_yield: float = 0.0,
        execution_prob: float = 1.0
    ) -> dict:
        """
        基于PE模型计算期望收益

        Args:
            current_pe: 当前PE
            target_pe: 目标PE
            eps_growth: EPS增长率
            dividend_yield: 股息率
            buyback_yield: 回购收益率
            execution_prob: 执行概率

        Returns:
            期望收益详细信息
        """
        model = ValuationModel(
            type="PE",
            current_multiple=current_pe,
            target_multiple=target_pe,
            growth_12m=eps_growth,
            dividend_yield=dividend_yield,
            buyback_yield=buyback_yield,
            execution_prob=execution_prob
        )
        return calculate_expected_return_from_model(model)

    @staticmethod
    def from_ev_ebitda_model(
        current_ev_ebitda: float,
        target_ev_ebitda: float,
        ebitda_growth: float,
        dividend_yield: float = 0.0,
        buyback_yield: float = 0.0,
        execution_prob: float = 1.0
    ) -> dict:
        """
        基于EV/EBITDA模型计算期望收益

        Args:
            current_ev_ebitda: 当前EV/EBITDA
            target_ev_ebitda: 目标EV/EBITDA
            ebitda_growth: EBITDA增长率
            dividend_yield: 股息率
            buyback_yield: 回购收益率
            execution_prob: 执行概率

        Returns:
            期望收益详细信息
        """
        model = ValuationModel(
            type="EV/EBITDA",
            current_multiple=current_ev_ebitda,
            target_multiple=target_ev_ebitda,
            growth_12m=ebitda_growth,
            dividend_yield=dividend_yield,
            buyback_yield=buyback_yield,
            execution_prob=execution_prob
        )
        return calculate_expected_return_from_model(model)

    @staticmethod
    def from_ev_sales_model(
        current_ev_sales: float,
        target_ev_sales: float,
        sales_growth: float,
        dividend_yield: float = 0.0,
        buyback_yield: float = 0.0,
        execution_prob: float = 1.0
    ) -> dict:
        """
        基于EV/Sales模型计算期望收益

        Args:
            current_ev_sales: 当前EV/Sales
            target_ev_sales: 目标EV/Sales
            sales_growth: 销售增长率
            dividend_yield: 股息率
            buyback_yield: 回购收益率
            execution_prob: 执行概率

        Returns:
            期望收益详细信息
        """
        model = ValuationModel(
            type="EV/Sales",
            current_multiple=current_ev_sales,
            target_multiple=target_ev_sales,
            growth_12m=sales_growth,
            dividend_yield=dividend_yield,
            buyback_yield=buyback_yield,
            execution_prob=execution_prob
        )
        return calculate_expected_return_from_model(model)
