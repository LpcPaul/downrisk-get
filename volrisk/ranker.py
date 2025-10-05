"""
排名输出模块
汇总计算结果，排序并导出为Excel/CSV
"""

from typing import Dict, List, Optional, Union
from pathlib import Path
import pandas as pd
import yaml
from pydantic import BaseModel, Field

from .sector import SectorAnalyzer, SectorMetrics, SectorsConfig
from .expected import ValuationModel, calculate_expected_return
from .risk import RiskConfig, calculate_risk


class CompanyConfig(BaseModel):
    """公司配置"""
    name: str = Field(..., description="公司名称")
    sector: Optional[str] = Field(None, description="单一行业代码")
    sector_mix: Optional[Dict[str, float]] = Field(None, description="多行业权重混合")
    expected_return: Optional[float] = Field(None, description="直接指定的期望收益")
    model: Optional[ValuationModel] = Field(None, description="估值模型")
    risk: RiskConfig = Field(default_factory=RiskConfig, description="风险配置")

    def validate_sector(self):
        """验证行业配置"""
        if self.sector is None and self.sector_mix is None:
            raise ValueError(f"{self.name}: 必须指定 sector 或 sector_mix")
        if self.sector is not None and self.sector_mix is not None:
            raise ValueError(f"{self.name}: sector 和 sector_mix 不能同时指定")

    def validate_expected_return(self):
        """验证期望收益配置"""
        if self.expected_return is None and self.model is None:
            raise ValueError(f"{self.name}: 必须指定 expected_return 或 model")


class CompaniesConfig(BaseModel):
    """多公司配置"""
    companies: List[CompanyConfig]

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'CompaniesConfig':
        """从YAML文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)


class CompanyResult:
    """公司分析结果"""

    def __init__(
        self,
        name: str,
        sector_info: str,
        sigma_down: float,
        sigma_total: float,
        mdd: float,
        er_raw: float,
        er: float,
        loss_risk: float,
        value_to_risk: float,
        risk_details: dict,
        er_details: dict
    ):
        self.name = name
        self.sector_info = sector_info
        self.sigma_down = sigma_down
        self.sigma_total = sigma_total
        self.mdd = mdd
        self.er_raw = er_raw
        self.er = er
        self.loss_risk = loss_risk
        self.value_to_risk = value_to_risk
        self.risk_details = risk_details
        self.er_details = er_details

    def to_dict(self) -> dict:
        """转换为字典（用于DataFrame）"""
        base = {
            '公司名称': self.name,
            '行业代理': self.sector_info,
            'σ总波动': f"{self.sigma_total:.4f}",
            'σ下行': f"{self.sigma_down:.4f}",
            'MDD': f"{abs(self.mdd):.4f}",
            'ER原始': f"{self.er_raw:.4f}",
            'ER执行后': f"{self.er:.4f}",
            '损失风险': f"{self.loss_risk:.4f}",
            '值博率': f"{self.value_to_risk:.2f}",
        }

        # 添加风险参数
        if self.risk_details['mode'] == 'SemiMDD':
            base['Idio'] = f"{self.risk_details['params'].get('idio', 1.0):.2f}"
            base['W'] = f"{self.risk_details['params'].get('w', 0.5):.2f}"
        else:  # SchemeC
            base['Beta'] = f"{self.risk_details['params'].get('beta', 1.0):.2f}"

        # 添加脆弱度
        fragility = self.risk_details.get('fragility_add', 0.0)
        if fragility > 0:
            base['脆弱度加点'] = f"{fragility:.4f}"

        return base


class Ranker:
    """排名器"""

    def __init__(
        self,
        sector_analyzer: Optional[SectorAnalyzer] = None
    ):
        """
        初始化排名器

        Args:
            sector_analyzer: 行业分析器，如果为None则创建新实例
        """
        self.sector_analyzer = sector_analyzer or SectorAnalyzer()

    def analyze_companies(
        self,
        companies_config: CompaniesConfig,
        sector_metrics: Dict[str, SectorMetrics]
    ) -> List[CompanyResult]:
        """
        分析所有公司

        Args:
            companies_config: 公司配置
            sector_metrics: 行业指标字典

        Returns:
            公司结果列表
        """
        results = []

        for company_config in companies_config.companies:
            try:
                # 验证配置
                company_config.validate_sector()
                company_config.validate_expected_return()

                # 获取行业指标
                if company_config.sector is not None:
                    # 单一行业
                    sector_name = company_config.sector
                    if sector_name not in sector_metrics:
                        print(f"错误: {company_config.name} 的行业 {sector_name} 没有指标数据")
                        continue

                    metrics = sector_metrics[sector_name]
                    sigma_down = metrics.sigma_down
                    sigma_total = metrics.sigma_total
                    mdd = metrics.mdd
                    sector_info = f"{sector_name}({','.join(metrics.tickers)})"

                else:
                    # 混合行业
                    mixed_metrics = self.sector_analyzer.calculate_mixed_sector_metrics(
                        company_config.sector_mix,
                        sector_metrics
                    )
                    if mixed_metrics is None:
                        print(f"错误: {company_config.name} 的混合行业指标计算失败")
                        continue

                    sigma_down = mixed_metrics['sigma_down']
                    sigma_total = mixed_metrics['sigma_total']
                    mdd = mixed_metrics['mdd']

                    # 构建sector_info字符串
                    mix_parts = [f"{s}({w:.0%})" for s, w in company_config.sector_mix.items()]
                    sector_info = " + ".join(mix_parts)

                # 计算期望收益
                er, er_details = calculate_expected_return(
                    expected_return=company_config.expected_return,
                    model=company_config.model
                )

                # 计算风险
                risk_result = calculate_risk(
                    sigma_down=sigma_down,
                    sigma_total=sigma_total,
                    mdd=mdd,
                    config=company_config.risk
                )

                loss_risk = risk_result['total_risk']

                # 计算值博率
                value_to_risk = er / loss_risk if loss_risk > 0 else float('inf')

                # 创建结果
                result = CompanyResult(
                    name=company_config.name,
                    sector_info=sector_info,
                    sigma_down=sigma_down,
                    sigma_total=sigma_total,
                    mdd=mdd,
                    er_raw=er_details.get('er_raw', er),
                    er=er,
                    loss_risk=loss_risk,
                    value_to_risk=value_to_risk,
                    risk_details=risk_result,
                    er_details=er_details
                )

                results.append(result)
                print(f"✓ {company_config.name}: 值博率 = {value_to_risk:.2f}")

            except Exception as e:
                print(f"错误: 分析 {company_config.name} 失败: {e}")
                continue

        return results

    def rank_and_export(
        self,
        results: List[CompanyResult],
        output_path: str,
        format: str = "xlsx"
    ):
        """
        排序并导出结果

        Args:
            results: 公司结果列表
            output_path: 输出文件路径
            format: 输出格式（xlsx, csv, json）
        """
        if not results:
            print("警告: 没有结果可导出")
            return

        # 按值博率降序排序
        sorted_results = sorted(results, key=lambda x: x.value_to_risk, reverse=True)

        # 转换为DataFrame
        df = pd.DataFrame([r.to_dict() for r in sorted_results])

        # 添加排名列
        df.insert(0, '排名', range(1, len(df) + 1))

        # 导出
        output_path = Path(output_path)

        if format == "xlsx":
            df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"\n✓ 结果已导出到: {output_path}")
        elif format == "csv":
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"\n✓ 结果已导出到: {output_path}")
        elif format == "json":
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
            print(f"\n✓ 结果已导出到: {output_path}")
        else:
            raise ValueError(f"不支持的输出格式: {format}")

        # 打印前10名摘要
        print("\n" + "=" * 80)
        print("排名前10的公司:")
        print("=" * 80)
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:2d}. {result.name:12s} | 值博率: {result.value_to_risk:6.2f} | "
                  f"ER: {result.er:6.2%} | 风险: {result.loss_risk:6.2%}")
        print("=" * 80)

        return df
