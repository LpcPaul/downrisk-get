#!/usr/bin/env python3
"""
计算修正后的VTR (V7.2)
使用纯行业σ_down作为风险分母 (不叠加β、Frag、MDD)
"""

# 行业ETF下行波动率 (σ_down) - 基于实际数据
SECTOR_SIGMA_DOWN = {
    'SEMI': 0.2414,      # 半导体 512480.SS
    'TMT': 0.2376,       # 科技/通信 512720.SS (计算机ETF替代)
    'CHEM': 0.2279,      # 化工 159870.SZ
    'GOLD': 0.1306,      # 黄金 518850.SS
    'NONFER': 0.2330,    # 有色金属 512400.SS
}

# 各公司行业暴露与权重
COMPANY_EXPOSURES = {
    '澜起科技': {
        'exposures': [('SEMI', 1.0)],
        'expected_return_1y': 0.045  # 从V7.1提取
    },
    '光迅科技': {
        'exposures': [('TMT', 1.0)],
        'expected_return_1y': 0.087
    },
    '生益科技': {
        'exposures': [('CHEM', 1.0)],
        'expected_return_1y': 0.020
    },
    '建滔积层板': {
        'exposures': [('CHEM', 1.0)],
        'expected_return_1y': 0.086
    },
    'ASMPT': {
        'exposures': [('SEMI', 1.0)],
        'expected_return_1y': 0.147
    },
    '紫金矿业': {
        'exposures': [('NONFER', 0.6), ('GOLD', 0.4)],
        'expected_return_1y': -0.240
    },
    '中金黄金': {
        'exposures': [('GOLD', 1.0)],
        'expected_return_1y': -0.295
    },
    '川恒股份': {
        'exposures': [('CHEM', 1.0)],
        'expected_return_1y': 0.129
    },
    '中国巨石': {
        'exposures': [('CHEM', 1.0)],
        'expected_return_1y': -0.067
    },
    '雅克科技': {
        'exposures': [('SEMI', 0.7), ('CHEM', 0.3)],
        'expected_return_1y': 0.011
    },
    '中天科技': {
        'exposures': [('TMT', 1.0)],
        'expected_return_1y': 0.076
    },
    '江西铜业': {
        'exposures': [('NONFER', 1.0)],
        'expected_return_1y': -0.036
    },
    '特变电工': {
        'exposures': [('SEMI', 0.5), ('CHEM', 0.5)],
        'expected_return_1y': -0.068
    },
    '联想集团': {
        'exposures': [('TMT', 1.0)],
        'expected_return_1y': 0.042
    },
}

def calculate_company_sigma_down(exposures):
    """计算公司加权σ_down"""
    total = 0.0
    for sector, weight in exposures:
        total += weight * SECTOR_SIGMA_DOWN[sector]
    return total

def calculate_vtr(expected_return, sigma_down):
    """计算值博率 VTR = 期望收益 / σ_down"""
    return expected_return / sigma_down

def main():
    results = []

    print("=" * 100)
    print("V7.2 修正后的VTR计算结果")
    print("=" * 100)
    print(f"{'公司':<12} {'行业暴露':<25} {'σ_down(修正)':<12} {'期望收益(1年)':<12} {'VTR':<8} {'V7.1旧VTR':<10}")
    print("-" * 100)

    for company, data in COMPANY_EXPOSURES.items():
        sigma_down = calculate_company_sigma_down(data['exposures'])
        expected_return = data['expected_return_1y']
        vtr = calculate_vtr(expected_return, sigma_down)

        # 行业暴露字符串
        exposure_str = '+'.join([f"{s}({w*100:.0f}%)" for s, w in data['exposures']])

        results.append({
            'company': company,
            'sigma_down': sigma_down,
            'expected_return': expected_return,
            'vtr': vtr,
            'exposure': exposure_str
        })

        print(f"{company:<12} {exposure_str:<25} {sigma_down*100:>6.2f}% {expected_return*100:>10.1f}% {vtr:>8.2f}")

    print("=" * 100)
    print()

    # 按VTR排序
    results_sorted = sorted(results, key=lambda x: x['vtr'], reverse=True)

    print("=" * 100)
    print("VTR排名 (值博率从高到低)")
    print("=" * 100)
    print(f"{'排名':<6} {'公司':<12} {'VTR':<10} {'期望收益':<12} {'风险σ_down':<12} {'评级':<10}")
    print("-" * 100)

    # 计算分位阈值
    vtr_values = [r['vtr'] for r in results_sorted]
    p70 = sorted(vtr_values)[int(len(vtr_values) * 0.7)]
    p30 = sorted(vtr_values)[int(len(vtr_values) * 0.3)]

    for rank, r in enumerate(results_sorted, 1):
        if r['vtr'] >= p70:
            rating = "⭐优秀"
        elif r['vtr'] >= p30:
            rating = "✓平衡"
        else:
            rating = "⚠️不佳"

        print(f"{rank:<6} {r['company']:<12} {r['vtr']:>8.2f} {r['expected_return']*100:>10.1f}% "
              f"{r['sigma_down']*100:>10.2f}% {rating:<10}")

    print("=" * 100)
    print(f"\nVTR阈值 (基于当期样本分位数):")
    print(f"  优秀 (Top30%): VTR ≥ {p70:.2f}")
    print(f"  平衡 (30-70%): {p30:.2f} ≤ VTR < {p70:.2f}")
    print(f"  不佳 (Bottom30%): VTR < {p30:.2f}")
    print()

    # 对比V7.1变化
    print("=" * 100)
    print("主要修正案例 (V7.1 → V7.2)")
    print("=" * 100)

    corrections = [
        ('生益科技', 0.7548, 0.2279, 0.020, 0.03, 0.09),
        ('建滔积层板', 0.6778, 0.2279, 0.086, 0.13, 0.38),
        ('川恒股份', 0.1503, 0.2279, 0.129, 0.86, 0.57),
        ('光迅科技', 0.5846, 0.2376, 0.087, 0.15, 0.37),
        ('中天科技', 0.5635, 0.2376, 0.076, 0.13, 0.32),
        ('联想集团', 0.8482, 0.2376, 0.042, 0.05, 0.18),
    ]

    print(f"{'公司':<12} {'V7.1 σ_down':<12} {'V7.2 σ_down':<12} {'收益':<10} {'V7.1 VTR':<10} {'V7.2 VTR':<10} {'变化':<10}")
    print("-" * 100)

    for company, old_sigma, new_sigma, ret, old_vtr, new_vtr in corrections:
        change = ((new_vtr - old_vtr) / old_vtr * 100) if old_vtr != 0 else 0
        change_str = f"{change:+.0f}%"
        print(f"{company:<12} {old_sigma*100:>10.2f}% {new_sigma*100:>10.2f}% {ret*100:>8.1f}% "
              f"{old_vtr:>10.2f} {new_vtr:>10.2f} {change_str:>10}")

    print("=" * 100)

if __name__ == '__main__':
    main()
