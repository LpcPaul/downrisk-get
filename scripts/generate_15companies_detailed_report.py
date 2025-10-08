#!/usr/bin/env python3
"""
生成15家公司详细VTR排名报告 (V7.3细分行业ETF版本)
严格按照PROJECT_EXECUTION_WORKFLOW.md执行:
1. 使用从Yahoo Finance获取的真实财报数据
2. 基于财报趋势、行业分析、个股研究生成场景分析
3. 使用细分行业ETF的σ_down作为风险指标
4. 多业务公司使用利润权重加权
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 细分行业σ_down数据 (2024-10-06至2025-10-06实测)
SUBINDUSTRY_SIGMA_DOWN = {
    'Fabless芯片设计': {'etf_code': '512760.SS', 'sigma_down': 0.2401},
    '半导体设备-后道封装': {'etf_code': '516290.SS', 'sigma_down': 0.2166},
    '半导体材料': {'etf_code': '516020.SS', 'sigma_down': 0.2176},
    '光通信模块': {'etf_code': '516630.SS', 'sigma_down': 0.2543},
    '通信设备-海缆光纤': {'etf_code': '515880.SS', 'sigma_down': 0.2698},
    'PC制造': {'etf_code': '512720.SS', 'sigma_down': 0.2376},
    '互联网平台': {'etf_code': '159638.SZ', 'sigma_down': 0.2589},
    'CCL覆铜板': {'etf_code': '159870.SZ', 'sigma_down': 0.2279},
    '磷化工-LFP': {'etf_code': '159870.SZ', 'sigma_down': 0.2279},
    '玻璃纤维': {'etf_code': '159870.SZ', 'sigma_down': 0.2279},
    '黄金开采': {'etf_code': '518850.SS', 'sigma_down': 0.1306},
    '铜矿开采': {'etf_code': '562800.SS', 'sigma_down': 0.2302},
    '输变电设备': {'etf_code': '159611.SZ', 'sigma_down': 0.1313},
    '多晶硅': {'etf_code': '516290.SS', 'sigma_down': 0.2166},
    'AI制药': {'etf_code': '512010.SS', 'sigma_down': 0.2854},
}

# 基于真实财报数据的场景分析配置
COMPANIES_SCENARIO_CONFIG = {
    'ASMPT': {
        'exposures': [('半导体设备-后道封装', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.20,
                'target_pe': 18,  # 低于历史中位数
                'growth': -0.15,  # 营收继续下滑
                'condition': '周期底部延续,先进封装不及预期'
            },
            'Base': {
                'prob': 0.60,
                'target_pe': 22,  # Forward PE当前21.7
                'growth': 0.25,  # 营收增长25% (财报显示正在复苏)
                'condition': '2025拐点确认,先进封装稳步放量'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 28,  # 周期高点
                'growth': 0.50,  # 营收高增长
                'condition': '先进封装爆发+传统业务同步反转'
            }
        },
        'notes': '周期拐点,先进封装(CoWoS/HBM)爆发,PE 151高是因为利润底部'
    },
    '川恒股份': {
        'exposures': [('磷化工-LFP', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.20,
                'target_pe': 10,
                'growth': -0.10,
                'condition': 'LFP需求下滑,磷肥价格低迷'
            },
            'Base': {
                'prob': 0.60,
                'target_pe': 14,  # 当前PE 14.4
                'growth': 0.20,  # 财报显示营收增长29.6%,盈利增长56.5%
                'condition': 'LFP稳定增长,自有磷矿成本优势显现'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 18,
                'growth': 0.40,
                'condition': 'LFP爆发式增长,磷肥价格回升'
            }
        },
        'notes': 'LFP正极材料+磷肥,自有磷矿成本优势,ROE 16.9%优秀'
    },
    '晶泰科技': {
        'exposures': [('AI制药', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.25,
                'target_pe': -5,  # 亏损股,用负PE表示持续亏损
                'growth': 0.20,
                'condition': 'AI制药商业化慢,亏损扩大'
            },
            'Base': {
                'prob': 0.50,
                'target_pe': -3,
                'growth': 0.50,  # 高成长但亏损收窄
                'condition': '订单增长,亏损收窄,商业化进展'
            },
            'Bull': {
                'prob': 0.25,
                'target_pe': 35,  # 盈利后给予成长股估值
                'growth': 1.00,
                'condition': 'AI制药突破,订单爆发,扭亏为盈'
            }
        },
        'notes': 'AI药物研发平台,高成长但亏损,ROE -3.6%,PB 8.5高'
    },
    '建滔积层板': {
        'exposures': [('CCL覆铜板', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.20,
                'target_pe': 18,
                'growth': -0.10,
                'condition': 'AI服务器需求不及预期,CCL价格下跌'
            },
            'Base': {
                'prob': 0.60,
                'target_pe': 24,  # 当前PE 24.5
                'growth': 0.15,
                'condition': 'AI服务器稳定增长,CCL涨价,成本优势'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 30,
                'growth': 0.35,
                'condition': 'AI服务器爆发,CCL大幅涨价'
            }
        },
        'notes': 'AI服务器CCL涨价,成本优势明显,ROE 10.2%'
    },
    '光迅科技': {
        'exposures': [('光通信模块', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.25,
                'target_pe': 30,
                'growth': 0.05,
                'condition': '800G放量不及预期,竞争加剧'
            },
            'Base': {
                'prob': 0.55,
                'target_pe': 40,  # 当前PE 46.7,略高估
                'growth': 0.20,
                'condition': '800G稳步放量,但竞争激烈'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 55,
                'growth': 0.40,
                'condition': '800G爆发,份额提升'
            }
        },
        'notes': '800G放量,但PE 46.7 vs 行业合理30-40透支,ROE 10.6%'
    },
    '腾讯控股': {
        'exposures': [('互联网平台', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.20,
                'target_pe': 18,
                'growth': 0.05,
                'condition': '监管收紧,游戏广告增长放缓'
            },
            'Base': {
                'prob': 0.60,
                'target_pe': 22,  # 当前PE 25.6
                'growth': 0.12,
                'condition': '游戏+广告稳定,AI云业务增长'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 28,
                'growth': 0.20,
                'condition': 'AI业务爆发,游戏超预期'
            }
        },
        'notes': '游戏+广告稳定,AI云业务增长,ROE 18.5%优秀'
    },
    '中天科技': {
        'exposures': [('通信设备-海缆光纤', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.25,
                'target_pe': 12,
                'growth': -0.05,
                'condition': '海缆订单延迟,光纤持续低迷'
            },
            'Base': {
                'prob': 0.55,
                'target_pe': 16,  # 当前PE 15.8
                'growth': 0.10,
                'condition': '海缆订单饱满,光纤业务筑底'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 22,
                'growth': 0.25,
                'condition': '海缆+光纤双轮驱动'
            }
        },
        'notes': '海缆订单饱满,但光纤业务低迷,ROE 7.7%一般'
    },
    '阿里巴巴': {
        'exposures': [('互联网平台', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.25,
                'target_pe': 10,
                'growth': 0.03,
                'condition': '电商增长乏力,云业务竞争激烈'
            },
            'Base': {
                'prob': 0.55,
                'target_pe': 13,  # 当前PE 13.5
                'growth': 0.08,
                'condition': '电商稳定,云计算AI投入见效'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 18,
                'growth': 0.15,
                'condition': '电商复苏,云业务加速'
            }
        },
        'notes': '电商云计算,AI投入大,ROE 10.8%'
    },
    '澜起科技': {
        'exposures': [('Fabless芯片设计', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.25,
                'target_pe': 25,
                'growth': -0.05,
                'condition': '服务器需求下滑,DDR5渗透慢'
            },
            'Base': {
                'prob': 0.55,
                'target_pe': 35,  # 当前PE 53远高于合理值25-30
                'growth': 0.10,
                'condition': 'DDR5稳定渗透,份额稳定'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 45,
                'growth': 0.25,
                'condition': 'AI服务器拉动DDR5爆发'
            }
        },
        'notes': '内存接口芯片,PE 53 vs 合理25-30严重透支,ROE 21.5%优秀'
    },
    '联想集团': {
        'exposures': [('PC制造', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.20,
                'target_pe': 8,
                'growth': -0.05,
                'condition': 'PC需求持续下滑,AI PC不及预期'
            },
            'Base': {
                'prob': 0.60,
                'target_pe': 11,  # 当前PE 12.8
                'growth': 0.08,
                'condition': 'AI PC缓慢渗透,PC市场筑底'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 15,
                'growth': 0.20,
                'condition': 'AI PC爆发,PC市场复苏'
            }
        },
        'notes': 'AI PC有看点,但PE 12.8偏高,ROE 30.7%极好'
    },
    '江西铜业': {
        'exposures': [('铜矿开采', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.30,
                'target_pe': 10,
                'growth': -0.15,
                'condition': '铜价下跌,TC/RC持续低位'
            },
            'Base': {
                'prob': 0.50,
                'target_pe': 13,  # 当前PE 12.5
                'growth': -0.05,
                'condition': '铜价震荡,TC/RC低于盈亏线'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 16,
                'growth': 0.10,
                'condition': '铜价上涨,TC/RC改善'
            }
        },
        'notes': '铜矿开采+冶炼一体化,TC/RC低于盈亏线,ROE 9.1%'
    },
    '中国巨石': {
        'exposures': [('玻璃纤维', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.30,
                'target_pe': 15,
                'growth': -0.10,
                'condition': '玻纤需求持续低迷,价格战'
            },
            'Base': {
                'prob': 0.50,
                'target_pe': 20,  # 当前PE 21.9
                'growth': 0.00,
                'condition': '玻纤周期底部,复苏时点不确定'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 28,
                'growth': 0.20,
                'condition': '玻纤周期反转,需求复苏'
            }
        },
        'notes': '玻纤周期底部,复苏时点不确定,ROE 10.6%,财报显示营收增长但利润波动'
    },
    '特变电工': {
        'exposures': [('输变电设备', 0.60), ('多晶硅', 0.40)],
        'scenarios': {
            'Bear': {
                'prob': 0.35,
                'target_pe': 15,
                'growth': -0.10,
                'condition': '输变电需求下滑,多晶硅深度亏损'
            },
            'Base': {
                'prob': 0.45,
                'target_pe': 20,  # 当前PE 21.4
                'growth': -0.05,
                'condition': '60%输变电盈利,40%多晶硅深度亏损拖累'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 25,
                'growth': 0.10,
                'condition': '输变电增长,多晶硅亏损收窄'
            }
        },
        'notes': '60%输变电(盈利)+40%多晶硅(深度亏损),ROE 4.0%差,财报显示2024Q4大幅亏损'
    },
    '紫金矿业': {
        'exposures': [('铜矿开采', 0.60), ('黄金开采', 0.40)],
        'scenarios': {
            'Bear': {
                'prob': 0.35,
                'target_pe': 12,
                'growth': -0.15,
                'condition': '铜价金价双杀,成本上升'
            },
            'Base': {
                'prob': 0.45,
                'target_pe': 14,  # 当前PE 19.8, PB 5.5 vs 历史2.8严重高估
                'growth': -0.10,
                'condition': '60%铜+40%黄金,PB 5.5 vs 2.8严重高估'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 18,
                'growth': 0.05,
                'condition': '铜价金价上涨,产量增长'
            }
        },
        'notes': '60%铜+40%黄金,PB 5.5 vs 历史2.8严重高估,ROE 28.2%极高但股价已充分反映'
    },
    '中金黄金': {
        'exposures': [('黄金开采', 1.0)],
        'scenarios': {
            'Bear': {
                'prob': 0.40,
                'target_pe': 12,
                'growth': -0.20,
                'condition': '金价大跌,成本高企'
            },
            'Base': {
                'prob': 0.40,
                'target_pe': 15,  # 当前PE 24.4, PB 3.8 vs 2.2极度高估
                'growth': -0.15,
                'condition': 'PB 3.8 vs 2.2极度高估,金价高位'
            },
            'Bull': {
                'prob': 0.20,
                'target_pe': 20,
                'growth': 0.00,
                'condition': '金价持续高位'
            }
        },
        'notes': 'PB 3.8 vs 历史2.2极度高估,金价高位,ROE 16.9%但股价已充分反映'
    },
}

def load_financial_data():
    """加载财报数据"""
    json_path = PROJECT_ROOT / 'data' / 'fundamental_research' / 'financial_data.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_weighted_sigma_down(exposures):
    """计算加权σ_down"""
    total = 0.0
    for subind, weight in exposures:
        total += weight * SUBINDUSTRY_SIGMA_DOWN[subind]['sigma_down']
    return total

def get_subindustry_text(exposures):
    """生成细分行业暴露文本"""
    if len(exposures) == 1:
        return exposures[0][0]
    else:
        parts = [f"{subind}({weight:.0%})" for subind, weight in exposures]
        return " + ".join(parts)

def calculate_scenario_return(current_pe, target_pe, growth):
    """
    计算单个场景的收益率
    公式: [(目标PE / 当前PE) × (1 + 增长率)] - 1
    """
    if current_pe > 0:
        return (target_pe / current_pe) * (1 + growth) - 1
    else:
        # 亏损股特殊处理
        if target_pe > 0:
            # 扭亏为盈,给予高收益
            return (1 + growth) * 0.8  # 简化处理
        else:
            # 持续亏损
            return (1 + growth) * 0.3 - 1

def calculate_expected_return(company_name, current_pe, scenarios):
    """计算场景加权期望收益"""
    exp_return = 0.0
    scenario_details = []

    for scenario_name, data in [('Bear', scenarios['Bear']),
                                 ('Base', scenarios['Base']),
                                 ('Bull', scenarios['Bull'])]:
        scenario_return = calculate_scenario_return(
            current_pe,
            data['target_pe'],
            data['growth']
        )
        exp_return += data['prob'] * scenario_return
        scenario_details.append({
            'name': scenario_name,
            'prob': data['prob'],
            'target_pe': data['target_pe'],
            'growth': data['growth'],
            'return': scenario_return,
            'condition': data['condition']
        })

    return exp_return, scenario_details

def main():
    print("=" * 120)
    print("正在生成15家公司详细VTR排名报告 (基于真实财报数据)")
    print("=" * 120)

    # 加载财报数据
    financial_data = load_financial_data()

    results = []
    for company_name, config in COMPANIES_SCENARIO_CONFIG.items():
        # 获取财报数据
        fin_data = financial_data.get(company_name, {})
        trailing_pe = fin_data.get('info', {}).get('trailingPE', 'N/A')
        forward_pe = fin_data.get('info', {}).get('forwardPE', 'N/A')
        current_pb = fin_data.get('info', {}).get('priceToBook', 'N/A')
        roe = fin_data.get('info', {}).get('returnOnEquity', 'N/A')

        # 使用Forward PE作为基准(更适合前瞻性分析),如果没有则用Trailing PE
        baseline_pe = forward_pe if isinstance(forward_pe, (int, float)) else trailing_pe
        baseline_pe = baseline_pe if isinstance(baseline_pe, (int, float)) else 20  # 默认PE

        # 计算风险指标
        sigma_down = calculate_weighted_sigma_down(config['exposures'])

        # 计算期望收益
        expected_return, scenario_details = calculate_expected_return(
            company_name,
            baseline_pe,
            config['scenarios']
        )

        # 计算VTR
        vtr = expected_return / sigma_down if sigma_down > 0 else 0

        results.append({
            '公司': company_name,
            '细分行业': get_subindustry_text(config['exposures']),
            'sigma_down': sigma_down,
            '期望收益': expected_return,
            'VTR': vtr,
            'trailing_pe': trailing_pe,
            'forward_pe': forward_pe,
            'baseline_pe': baseline_pe,
            'current_pb': current_pb,
            'roe': roe,
            'scenario_details': scenario_details,
            'notes': config['notes']
        })

    df = pd.DataFrame(results)
    df_sorted = df.sort_values('VTR', ascending=False).reset_index(drop=True)
    df_sorted['排名'] = df_sorted.index + 1

    # 生成详细报告
    report_path = PROJECT_ROOT / 'results' / 'final_detailed_report.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 120 + "\n")
        f.write("15家公司值博率(VTR)详细排名报告 - V7.3细分行业版\n")
        f.write("=" * 120 + "\n")
        f.write(f"报告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据来源: Yahoo Finance API + 细分行业ETF实测σ_down\n")
        f.write(f"时间窗口: 1年 (2024-10-06至2025-10-06)\n")
        f.write(f"分析框架: V7.3细分行业σ_down方法论\n")
        f.write("\n")
        f.write("核心公式:\n")
        f.write("  VTR (值博率) = 期望收益(1年) ÷ 细分行业σ_down\n")
        f.write("  期望收益: 基于场景分析法 (Bear/Base/Bull加权)\n")
        f.write("  损失风险: 纯细分行业σ_down (下行波动率)\n")
        f.write("  多业务公司: σ_down按利润权重加权求和\n")
        f.write("\n")

        # VTR排名表
        f.write("=" * 120 + "\n")
        f.write("值博率(VTR)排名 - 从高到低\n")
        f.write("=" * 120 + "\n")
        f.write(f"{'排名':<6} {'公司':<15} {'VTR':>8} {'期望收益':>10} {'损失风险':>10} {'基准PE':>10} {'细分行业':<30}\n")
        f.write("-" * 120 + "\n")

        for _, row in df_sorted.iterrows():
            rank = int(row['排名'])
            name = row['公司']
            vtr = row['VTR']
            exp_ret = row['期望收益']
            sigma = row['sigma_down']
            pe = row['baseline_pe']
            subind = row['细分行业']

            pe_str = f"{pe:.1f}" if isinstance(pe, (int, float)) else "N/A"
            f.write(f"{rank:<6} {name:<15} {vtr:8.4f} {exp_ret:9.1%} {sigma:9.1%} {pe_str:>10} {subind:<30}\n")

        f.write("\n")

        # VTR阈值说明
        f.write("VTR评级阈值:\n")
        f.write("  ⭐优秀: VTR ≥ 0.28\n")
        f.write("  ✓平衡: -0.16 ≤ VTR < 0.28\n")
        f.write("  ⚠️不佳: VTR < -0.16\n")
        f.write("\n")

        # 细分行业σ_down数据
        f.write("=" * 120 + "\n")
        f.write("细分行业ETF下行波动率(σ_down)数据\n")
        f.write("=" * 120 + "\n")
        f.write(f"{'细分行业':<30} {'ETF代码':<15} {'σ_down':>10} {'数据窗口':<25}\n")
        f.write("-" * 120 + "\n")

        for subind, data in sorted(SUBINDUSTRY_SIGMA_DOWN.items(), key=lambda x: x[1]['sigma_down']):
            f.write(f"{subind:<30} {data['etf_code']:<15} {data['sigma_down']:9.2%} {'2024-10-06至2025-10-06':<25}\n")

        f.write("\n")

        # 各公司详细拆解
        f.write("=" * 120 + "\n")
        f.write("各公司详细拆解\n")
        f.write("=" * 120 + "\n\n")

        for _, row in df_sorted.iterrows():
            rank = int(row['排名'])
            name = row['公司']
            vtr = row['VTR']
            exp_ret = row['期望收益']
            sigma = row['sigma_down']
            subind = row['细分行业']
            notes = row['notes']
            trailing_pe = row['trailing_pe']
            forward_pe = row['forward_pe']
            baseline_pe = row['baseline_pe']
            pb = row['current_pb']
            roe = row['roe']
            scenario_details = row['scenario_details']

            f.write("-" * 120 + "\n")
            f.write(f"排名 {rank}: {name}\n")
            f.write("-" * 120 + "\n")
            f.write(f"细分行业: {subind}\n")
            f.write(f"投资逻辑: {notes}\n")
            f.write("\n")

            # 估值指标
            f.write(f"当前估值:\n")
            trailing_pe_str = f"{trailing_pe:.1f}" if isinstance(trailing_pe, (int, float)) else "N/A"
            forward_pe_str = f"{forward_pe:.1f}" if isinstance(forward_pe, (int, float)) else "N/A"
            baseline_pe_str = f"{baseline_pe:.1f}" if isinstance(baseline_pe, (int, float)) else "N/A"
            pb_str = f"{pb:.1f}" if isinstance(pb, (int, float)) else "N/A"
            roe_str = f"{roe:.1%}" if isinstance(roe, (int, float)) else "N/A"
            f.write(f"  PE(Trailing): {trailing_pe_str}  PE(Forward): {forward_pe_str}  [基准: {baseline_pe_str}]\n")
            f.write(f"  PB: {pb_str}\n")
            f.write(f"  ROE: {roe_str}\n")
            f.write("\n")

            # 场景分析
            f.write(f"场景分析 (1年窗口):\n")
            for scenario in scenario_details:
                f.write(f"  {scenario['name']} ({scenario['prob']:.0%}): ")
                f.write(f"目标PE {scenario['target_pe']:.0f}倍, ")
                f.write(f"增长率{scenario['growth']:+.0%}, ")
                f.write(f"场景收益{scenario['return']:+.1%}\n")
                f.write(f"    条件: {scenario['condition']}\n")

            f.write("\n")
            f.write(f"加权期望收益: {exp_ret:.1%}\n")
            f.write("\n")

            f.write("VTR指标:\n")
            f.write(f"  期望收益(1年): {exp_ret:6.1%}\n")
            f.write(f"  损失风险(σ_down): {sigma:6.2%}\n")
            f.write(f"  VTR(值博率): {vtr:6.4f}\n")
            f.write("\n")

            # 评级
            if vtr >= 0.28:
                rating = "⭐优秀"
            elif vtr >= -0.16:
                rating = "✓平衡"
            else:
                rating = "⚠️不佳"
            f.write(f"评级: {rating}\n")
            f.write("\n")

        f.write("=" * 120 + "\n")
        f.write("报告结束\n")
        f.write("=" * 120 + "\n")

    print(f"\n✅ 详细报告已保存: {report_path}")

    # 打印简要排名
    print("\n" + "=" * 120)
    print("15家公司VTR排名 (简表)")
    print("=" * 120)
    for _, row in df_sorted.iterrows():
        rank = int(row['排名'])
        name = row['公司']
        vtr = row['VTR']
        exp_ret = row['期望收益']
        print(f"{rank:2}. {name:<12} VTR={vtr:7.4f}  期望收益={exp_ret:+6.1%}  风险={row['sigma_down']:5.1%}")
    print("=" * 120)

if __name__ == "__main__":
    main()
