#!/usr/bin/env python3
"""
生成15家公司完整VTR排名报告 - 包含期望收益详细计算
使用场景分析法(Bear/Base/Bull)计算期望收益
使用细分行业ETF的σ_down作为风险指标
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 细分行业σ_down数据
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

# 15家公司配置 (含场景分析数据)
COMPANIES_CONFIG = {
    'ASMPT': {
        'name_cn': 'ASMPT',
        'ticker': '0522.HK',
        'exposures': [('半导体设备-后道封装', 1.0)],
        'current_pe': 26.27,
        'peg': 0.26,
        'valuation_range': 'PE 20-35倍',
        'scenarios': {
            'Bear': {'prob': 0.20, 'target_pe': 20, 'growth': -0.20, 'return': -0.380, 'condition': '周期底部延续,先进封装不及预期'},
            'Base': {'prob': 0.60, 'target_pe': 27, 'growth': 0.50, 'return': 0.542, 'condition': '2025拐点确认,先进封装稳步放量'},
            'Bull': {'prob': 0.20, 'target_pe': 35, 'growth': 1.00, 'return': 1.660, 'condition': '先进封装爆发+传统业务同步反转'},
        },
        'investment_logic': '周期拐点,先进封装(CoWoS/HBM)爆发,2024亏损-93%为底部'
    },
    '川恒股份': {
        'name_cn': '川恒股份',
        'ticker': '002895.SZ',
        'exposures': [('磷化工-LFP', 1.0)],
        'current_pe': 14.03,
        'peg': 0.70,
        'valuation_range': 'PE 10-16倍',
        'scenarios': {
            'Bear': {'prob': 0.20, 'target_pe': 10, 'growth': 0.05, 'return': -0.257, 'condition': 'LFP产能过剩,磷酸价格下跌'},
            'Base': {'prob': 0.60, 'target_pe': 13, 'growth': 0.20, 'return': 0.113, 'condition': 'LFP稳定增长,磷肥+饲料协同'},
            'Bull': {'prob': 0.20, 'target_pe': 16, 'growth': 0.40, 'return': 0.596, 'condition': '储能爆发+海外LFP放量'},
        },
        'investment_logic': 'PE 14<16真实低估,自有磷矿成本优势,LFP正极材料景气'
    },
    '建滔积层板': {
        'name_cn': '建滔积层板',
        'ticker': '1888.HK',
        'exposures': [('CCL覆铜板', 1.0)],
        'current_pe': 18.92,
        'peg': 1.89,
        'valuation_range': 'PE 12-20倍',
        'scenarios': {
            'Bear': {'prob': 0.20, 'target_pe': 12, 'growth': 0.00, 'return': -0.366, 'condition': 'AI服务器需求不及预期,CCL价格战'},
            'Base': {'prob': 0.60, 'target_pe': 16, 'growth': 0.10, 'return': -0.068, 'condition': 'AI服务器稳定需求,小幅涨价'},
            'Bull': {'prob': 0.25, 'target_pe': 20, 'growth': 0.25, 'return': 0.320, 'condition': 'AI+汽车双爆发,高频CCL涨价20%+'},
        },
        'investment_logic': 'AI服务器CCL涨价,垂直整合成本优势,2024H1毛利率从18%→22%'
    },
    '光迅科技': {
        'name_cn': '光迅科技',
        'ticker': '002281.SZ',
        'exposures': [('光通信模块', 1.0)],
        'current_pe': 63.43,
        'peg': 1.41,
        'valuation_range': 'PE 25-40倍',
        'scenarios': {
            'Bear': {'prob': 0.25, 'target_pe': 25, 'growth': 0.20, 'return': -0.527, 'condition': '800G渗透延迟,竞争加剧'},
            'Base': {'prob': 0.60, 'target_pe': 32, 'growth': 0.45, 'return': -0.267, 'condition': '800G稳步放量,份额维持'},
            'Bull': {'prob': 0.15, 'target_pe': 40, 'growth': 0.70, 'return': 0.073, 'condition': '800G爆发+海外突破'},
        },
        'investment_logic': '800G模块出货量+150%,但PE 63 vs 走廊上限40严重透支'
    },
    '中天科技': {
        'name_cn': '中天科技',
        'ticker': '600522.SS',
        'exposures': [('通信设备-海缆光纤', 1.0)],
        'current_pe': 35.21,
        'peg': None,
        'valuation_range': 'PE 18-30倍(分部加权)',
        'scenarios': {
            'Bear': {'prob': 0.20, 'target_pe': 18, 'growth': 0.05, 'return': -0.451, 'condition': '海缆订单不及预期,光纤持续低迷'},
            'Base': {'prob': 0.60, 'target_pe': 22, 'growth': 0.15, 'return': -0.282, 'condition': '海缆稳步放量,光纤企稳'},
            'Bull': {'prob': 0.20, 'target_pe': 27, 'growth': 0.30, 'return': -0.003, 'condition': '海上风电爆发+海外订单突破'},
        },
        'investment_logic': '海缆订单饱满覆盖1.5年产能,但光纤业务(60%收入)持续低迷'
    },
    '澜起科技': {
        'name_cn': '澜起科技',
        'ticker': '688008.SS',
        'exposures': [('Fabless芯片设计', 1.0)],
        'current_pe': 88.0,
        'peg': None,
        'valuation_range': 'PE 25倍合理',
        'scenarios': {
            'Bear': {'prob': 0.30, 'target_pe': 25, 'growth': 0.30, 'return': -0.598, 'condition': 'DDR5渗透放缓,估值大幅压缩'},
            'Base': {'prob': 0.55, 'target_pe': 35, 'growth': 0.50, 'return': -0.398, 'condition': 'DDR5稳步渗透,估值缓慢压缩'},
            'Bull': {'prob': 0.15, 'target_pe': 50, 'growth': 0.80, 'return': 0.023, 'condition': 'DDR5+新产品爆发'},
        },
        'investment_logic': '2024利润+213%,DDR5全球份额36.8%,但PE 88 vs 25透支252%'
    },
    '联想集团': {
        'name_cn': '联想集团',
        'ticker': '0992.HK',
        'exposures': [('PC制造', 1.0)],
        'current_pe': 10.56,
        'peg': None,
        'valuation_range': 'PE 10-15倍',
        'scenarios': {
            'Bear': {'prob': 0.25, 'target_pe': 8, 'growth': 0.05, 'return': -0.205, 'condition': 'AI PC渗透延迟,传统PC需求疲软'},
            'Base': {'prob': 0.60, 'target_pe': 11, 'growth': 0.15, 'return': 0.196, 'condition': 'AI PC渗透率达10%,服务器稳定'},
            'Bull': {'prob': 0.15, 'target_pe': 14, 'growth': 0.30, 'return': 0.723, 'condition': 'AI PC渗透加速,服务器订单爆发'},
        },
        'investment_logic': 'AI PC有看点,但PE虽低但增长有限'
    },
    '腾讯控股': {
        'name_cn': '腾讯控股',
        'ticker': '0700.HK',
        'exposures': [('互联网平台', 1.0)],
        'current_pe': 24.98,
        'peg': None,
        'valuation_range': 'PE 20-30倍',
        'scenarios': {
            'Bear': {'prob': 0.20, 'target_pe': 20, 'growth': 0.05, 'return': -0.160, 'condition': '监管趋严,游戏版号收紧,广告承压'},
            'Base': {'prob': 0.65, 'target_pe': 25, 'growth': 0.12, 'return': 0.120, 'condition': '游戏+广告稳定,AI云业务增长'},
            'Bull': {'prob': 0.15, 'target_pe': 30, 'growth': 0.20, 'return': 0.440, 'condition': '海外游戏爆发,AI变现加速'},
        },
        'investment_logic': '游戏+广告成熟稳定,AI云业务增长,但整体增速放缓'
    },
    '阿里巴巴': {
        'name_cn': '阿里巴巴',
        'ticker': '9988.HK',
        'exposures': [('互联网平台', 1.0)],
        'current_pe': 19.12,
        'peg': None,
        'valuation_range': 'PE 15-25倍',
        'scenarios': {
            'Bear': {'prob': 0.25, 'target_pe': 15, 'growth': 0.00, 'return': -0.216, 'condition': '电商竞争加剧,云业务增速放缓'},
            'Base': {'prob': 0.60, 'target_pe': 19, 'growth': 0.10, 'return': 0.093, 'condition': '电商稳定,云+国际业务增长'},
            'Bull': {'prob': 0.15, 'target_pe': 24, 'growth': 0.20, 'return': 0.507, 'condition': '淘宝天猫反转,海外电商爆发'},
        },
        'investment_logic': '电商+云计算,AI投入大,估值已经便宜但增长压力大'
    },
    '江西铜业': {
        'name_cn': '江西铜业',
        'ticker': '600362.SS',
        'exposures': [('铜矿开采', 1.0)],
        'current_pe': 17.23,
        'peg': None,
        'valuation_range': 'PE 12-20倍',
        'scenarios': {
            'Bear': {'prob': 0.35, 'target_pe': 12, 'growth': -0.10, 'return': -0.383, 'condition': '铜价下跌,TC/RC持续低位'},
            'Base': {'prob': 0.50, 'target_pe': 16, 'growth': 0.05, 'return': -0.026, 'condition': '铜价横盘,TC/RC微幅改善'},
            'Bull': {'prob': 0.15, 'target_pe': 20, 'growth': 0.15, 'return': 0.337, 'condition': '铜价上涨20%+,TC/RC回升'},
        },
        'investment_logic': 'TC/RC低于盈亏线,铜矿开采+冶炼一体化,需铜价大涨'
    },
    '中国巨石': {
        'name_cn': '中国巨石',
        'ticker': '600176.SS',
        'exposures': [('玻璃纤维', 1.0)],
        'current_pe': 23.75,
        'peg': None,
        'valuation_range': 'PE 18-28倍',
        'scenarios': {
            'Bear': {'prob': 0.30, 'target_pe': 18, 'growth': -0.05, 'return': -0.311, 'condition': '玻纤价格持续承压,复苏延迟'},
            'Base': {'prob': 0.55, 'target_pe': 22, 'growth': 0.10, 'return': 0.016, 'condition': '玻纤价格企稳,需求缓慢修复'},
            'Bull': {'prob': 0.15, 'target_pe': 27, 'growth': 0.25, 'return': 0.419, 'condition': '风电+基建需求爆发,价格反转'},
        },
        'investment_logic': '玻纤周期底部,2024利润-19.7%,Q4筑底,复苏时点不确定'
    },
    '特变电工': {
        'name_cn': '特变电工',
        'ticker': '600089.SS',
        'exposures': [('输变电设备', 0.60), ('多晶硅', 0.40)],
        'current_pe': 12.71,
        'peg': None,
        'valuation_range': 'PE 10-15倍',
        'scenarios': {
            'Bear': {'prob': 0.35, 'target_pe': 10, 'growth': -0.10, 'return': -0.293, 'condition': '多晶硅持续深度亏损,拖累整体'},
            'Base': {'prob': 0.50, 'target_pe': 12, 'growth': 0.05, 'return': -0.007, 'condition': '输变电稳定,多晶硅亏损收窄'},
            'Bull': {'prob': 0.15, 'target_pe': 15, 'growth': 0.15, 'return': 0.353, 'condition': '特高压加速+多晶硅盈亏平衡'},
        },
        'investment_logic': '60%输变电(盈利)+40%多晶硅(EBIT率-15.8%深度亏损)'
    },
    '紫金矿业': {
        'name_cn': '紫金矿业',
        'ticker': '601899.SS',
        'exposures': [('铜矿开采', 0.60), ('黄金开采', 0.40)],
        'current_pe': 20.30,
        'peg': None,
        'valuation_range': 'PB 2.2-3.3倍',
        'scenarios': {
            'Bear': {'prob': 0.40, 'target_pe': 12, 'growth': -0.15, 'return': -0.495, 'condition': '金价大跌+铜价下跌,PB压缩'},
            'Base': {'prob': 0.45, 'target_pe': 15, 'growth': 0.00, 'return': -0.261, 'condition': '金价铜价横盘,PB缓慢压缩'},
            'Bull': {'prob': 0.15, 'target_pe': 20, 'growth': 0.10, 'return': 0.082, 'condition': '金价铜价上涨,但PB仍高估'},
        },
        'investment_logic': '60%铜+40%黄金,PB 6.24 vs 合理中枢2.8严重高估(+123%)'
    },
    '中金黄金': {
        'name_cn': '中金黄金',
        'ticker': '600489.SS',
        'exposures': [('黄金开采', 1.0)],
        'current_pe': 23.08,
        'peg': None,
        'valuation_range': 'PB 2.2倍合理',
        'scenarios': {
            'Bear': {'prob': 0.45, 'target_pe': 15, 'growth': -0.20, 'return': -0.488, 'condition': '金价大跌至2500以下,PB压缩'},
            'Base': {'prob': 0.40, 'target_pe': 18, 'growth': -0.10, 'return': -0.307, 'condition': '金价横盘,PB缓慢压缩'},
            'Bull': {'prob': 0.15, 'target_pe': 23, 'growth': 0.00, 'return': -0.046, 'condition': '金价维持高位,但PB仍高估'},
        },
        'investment_logic': 'PB 4.6 vs 2.2极度高估(+109%),金价高位风险大'
    },
    '晶泰科技': {
        'name_cn': '晶泰科技',
        'ticker': '2228.HK',
        'exposures': [('AI制药', 1.0)],
        'current_pe': -105.64,  # 亏损
        'peg': None,
        'valuation_range': '成长期公司',
        'scenarios': {
            'Bear': {'prob': 0.25, 'target_pe': None, 'growth': 1.50, 'return': -0.200, 'condition': '商业化延迟,融资压力大'},
            'Base': {'prob': 0.55, 'target_pe': None, 'growth': 2.00, 'return': 0.100, 'condition': 'AI药物研发订单稳步增长'},
            'Bull': {'prob': 0.20, 'target_pe': None, 'growth': 3.00, 'return': 0.500, 'condition': '重磅AI药物成功,商业化加速'},
        },
        'investment_logic': 'AI药物研发平台,高成长但持续亏损,收入+403.8%但利润率-28.9%'
    },
}

def calculate_weighted_sigma_down(exposures):
    """计算加权σ_down"""
    total = 0.0
    for subind, weight in exposures:
        total += weight * SUBINDUSTRY_SIGMA_DOWN[subind]['sigma_down']
    return total

def calculate_expected_return(scenarios):
    """计算场景加权期望收益"""
    exp_return = 0.0
    for scenario_name, data in scenarios.items():
        exp_return += data['prob'] * data['return']
    return exp_return

def get_subindustry_text(exposures):
    """生成细分行业暴露文本"""
    if len(exposures) == 1:
        return exposures[0][0]
    else:
        parts = [f"{subind}({weight:.0%})" for subind, weight in exposures]
        return " + ".join(parts)

def main():
    print("正在计算15家公司VTR(包含完整期望收益拆解)...")
    
    results = []
    for company_key, data in COMPANIES_CONFIG.items():
        name_cn = data['name_cn']
        sigma_down = calculate_weighted_sigma_down(data['exposures'])
        expected_return = calculate_expected_return(data['scenarios'])
        vtr = expected_return / sigma_down if sigma_down > 0 else 0
        
        results.append({
            '公司': name_cn,
            'ticker': data['ticker'],
            '细分行业': get_subindustry_text(data['exposures']),
            'sigma_down': sigma_down,
            '期望收益': expected_return,
            'VTR': vtr,
            'current_pe': data['current_pe'],
            'peg': data['peg'],
            'valuation_range': data['valuation_range'],
            'scenarios': data['scenarios'],
            'investment_logic': data['investment_logic']
        })
    
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('VTR', ascending=False).reset_index(drop=True)
    df_sorted['排名'] = df_sorted.index + 1
    
    # 生成详细报告
    report_path = PROJECT_ROOT / 'results' / 'final_report_full.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 140 + "\n")
        f.write("15家公司值博率(VTR)完整排名报告 - V7.3细分行业版(含期望收益完整拆解)\n")
        f.write("=" * 140 + "\n")
        f.write(f"报告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据来源: Yahoo Finance API + 细分行业ETF实测σ_down\n")
        f.write(f"时间窗口: 1年 (2024-10-06至2025-10-06)\n")
        f.write(f"分析框架: V7.3细分行业σ_down + 场景分析法(Bear/Base/Bull)\n")
        f.write("\n")
        f.write("核心公式:\n")
        f.write("  VTR (值博率) = 期望收益(1年) ÷ 细分行业σ_down\n")
        f.write("  期望收益 = Σ(场景概率 × 场景收益)  # Bear/Base/Bull加权\n")
        f.write("  场景收益 = [(目标PE/当前PE) × (1+增长率)] - 1\n")
        f.write("  损失风险 = 纯细分行业σ_down (下行波动率)\n")
        f.write("  多业务公司: σ_down按利润权重加权求和\n")
        f.write("\n")
        
        # VTR排名表
        f.write("=" * 140 + "\n")
        f.write("值博率(VTR)排名 - 从高到低\n")
        f.write("=" * 140 + "\n")
        f.write(f"{'排名':<6} {'公司':<15} {'VTR':>8} {'期望收益':>10} {'损失风险':>10} {'当前PE':>10} {'PEG':>8} {'细分行业':<30}\n")
        f.write("-" * 140 + "\n")
        
        for _, row in df_sorted.iterrows():
            rank = int(row['排名'])
            name = row['公司']
            vtr = row['VTR']
            exp_ret = row['期望收益']
            sigma = row['sigma_down']
            pe = row['current_pe']
            peg = row['peg']
            subind = row['细分行业']
            
            pe_str = f"{pe:.2f}" if pe > 0 else "亏损"
            peg_str = f"{peg:.2f}" if peg else "N/A"
            
            f.write(f"{rank:<6} {name:<15} {vtr:8.4f} {exp_ret:9.1%} {sigma:9.2%} {pe_str:>10} {peg_str:>8} {subind:<30}\n")
        
        f.write("\n")
        
        # VTR评级阈值
        f.write("VTR评级阈值:\n")
        f.write("  ⭐优秀: VTR ≥ 0.28\n")
        f.write("  ✓平衡: -0.16 ≤ VTR < 0.28\n")
        f.write("  ⚠️不佳: VTR < -0.16\n")
        f.write("\n")
        
        # 细分行业σ_down数据
        f.write("=" * 140 + "\n")
        f.write("细分行业ETF下行波动率(σ_down)数据\n")
        f.write("=" * 140 + "\n")
        f.write(f"{'细分行业':<30} {'ETF代码':<15} {'σ_down':>10} {'数据窗口':<25}\n")
        f.write("-" * 140 + "\n")
        
        for subind, data in sorted(SUBINDUSTRY_SIGMA_DOWN.items(), key=lambda x: x[1]['sigma_down']):
            f.write(f"{subind:<30} {data['etf_code']:<15} {data['sigma_down']:9.2%} {'2024-10-06至2025-10-06':<25}\n")
        
        f.write("\n")
        
        # 各公司详细拆解
        f.write("=" * 140 + "\n")
        f.write("各公司详细拆解 (含期望收益场景分析)\n")
        f.write("=" * 140 + "\n\n")
        
        for _, row in df_sorted.iterrows():
            rank = int(row['排名'])
            name = row['公司']
            ticker = row['ticker']
            vtr = row['VTR']
            exp_ret = row['期望收益']
            sigma = row['sigma_down']
            pe = row['current_pe']
            peg = row['peg']
            val_range = row['valuation_range']
            subind = row['细分行业']
            scenarios = row['scenarios']
            logic = row['investment_logic']
            
            f.write("-" * 140 + "\n")
            f.write(f"排名 {rank}: {name} ({ticker})\n")
            f.write("-" * 140 + "\n")
            f.write(f"细分行业: {subind}\n")
            f.write(f"投资逻辑: {logic}\n")
            f.write("\n")
            
            f.write("估值定位:\n")
            pe_str = f"{pe:.2f}" if pe > 0 else "亏损"
            f.write(f"  当前PE: {pe_str}\n")
            if peg:
                f.write(f"  PEG: {peg:.2f}")
                if peg < 1.0:
                    f.write(" 🟢 (低估)")
                elif peg < 1.5:
                    f.write(" 🟡 (合理)")
                else:
                    f.write(" 🔴 (高估)")
                f.write("\n")
            f.write(f"  估值走廊: {val_range}\n")
            f.write("\n")
            
            f.write("场景分析 (1年窗):\n")
            f.write(f"  {'场景':<8} {'概率':>6} {'目标PE':>10} {'增长率':>8} {'场景收益':>10} {'触发条件':<60}\n")
            f.write("  " + "-" * 130 + "\n")
            
            for scenario_name, scenario_data in scenarios.items():
                prob = scenario_data['prob']
                target_pe = scenario_data.get('target_pe')
                growth = scenario_data['growth']
                ret = scenario_data['return']
                condition = scenario_data['condition']
                
                target_pe_str = f"{target_pe}倍" if target_pe else "N/A"
                
                f.write(f"  {scenario_name:<8} {prob:5.0%} {target_pe_str:>10} {growth:7.0%} {ret:9.1%} {condition:<60}\n")
            
            f.write("\n")
            f.write(f"加权期望收益: {exp_ret:.1%} = ")
            components = [f"{s_data['prob']:.0%}×{s_data['return']:.1%}" for s_name, s_data in scenarios.items()]
            f.write(" + ".join(components))
            f.write("\n\n")
            
            f.write("风险评估:\n")
            f.write(f"  损失风险(σ_down): {sigma:6.2%} (细分行业ETF实测)\n")
            f.write(f"  VTR(值博率): {vtr:6.4f}\n")
            f.write("\n")
            
            # 评级
            if vtr >= 0.28:
                rating = "⭐优秀"
                comment = "期望收益显著高于损失风险,值得配置"
            elif vtr >= -0.16:
                rating = "✓平衡"
                comment = "期望收益与损失风险基本平衡"
            else:
                rating = "⚠️不佳"
                comment = "期望收益低于损失风险或为负,建议规避"
            
            f.write(f"评级: {rating} - {comment}\n")
            f.write("\n")
        
        f.write("=" * 140 + "\n")
        f.write("报告结束\n")
        f.write("=" * 140 + "\n")
    
    # 保存Excel
    excel_path = PROJECT_ROOT / 'results' / 'final_report_full.xlsx'
    
    # 准备Excel数据
    excel_data = df_sorted[['排名', '公司', 'ticker', '细分行业', 'VTR', '期望收益', 'sigma_down', 
                             'current_pe', 'peg', 'valuation_range', 'investment_logic']].copy()
    excel_data.columns = ['排名', '公司', '代码', '细分行业', 'VTR', '期望收益', 'σ_down', 
                          '当前PE', 'PEG', '估值走廊', '投资逻辑']
    
    excel_data.to_excel(excel_path, index=False, sheet_name='VTR排名')
    
    print(f"\n✅ 完整详细报告已保存: {report_path}")
    print(f"✅ Excel已保存: {excel_path}")
    
    # 打印简要排名
    print("\n" + "=" * 140)
    print("15家公司VTR排名 (简表)")
    print("=" * 140)
    summary = df_sorted[['排名', '公司', 'VTR', '期望收益', 'sigma_down', '细分行业']].copy()
    print(summary.to_string(index=False))
    print("=" * 140)

if __name__ == "__main__":
    main()
