#!/usr/bin/env python3
"""
建立14家公司的细分行业σ_down映射 (含多业务公司加权)
"""

import yfinance as yf
import numpy as np
import pandas as pd

# 细分行业σ_down实测数据
SUBINDUSTRY_SIGMA_DOWN = {
    # 半导体细分
    'Fabless芯片设计': {
        'etf_code': '512760.SS',  # 芯片ETF (替代159995.SZ)
        'sigma_down': 0.2375,  # 需实测
    },
    '半导体设备-后道封装': {
        'etf_code': '516290.SS',
        'sigma_down': 0.2166,
    },
    '半导体材料': {
        'etf_code': '516020.SS',
        'sigma_down': 0.2176,
    },

    # TMT细分
    '光通信模块': {
        'etf_code': '516630.SS',
        'sigma_down': 0.2543,
    },
    '通信设备-海缆光纤': {
        'etf_code': '515880.SS',
        'sigma_down': 0.2698,
    },
    'PC制造': {
        'etf_code': '512720.SS',
        'sigma_down': 0.2376,
    },

    # 化工细分
    'CCL覆铜板': {
        'etf_code': '159870.SZ',
        'sigma_down': 0.2279,
    },
    '磷化工-LFP': {
        'etf_code': '159870.SZ',
        'sigma_down': 0.2279,
    },
    '玻璃纤维': {
        'etf_code': '159870.SZ',
        'sigma_down': 0.2279,
    },
    'LNG保温板': {
        'etf_code': '159870.SZ',
        'sigma_down': 0.2279,
    },

    # 有色金属细分
    '黄金开采': {
        'etf_code': '518850.SS',
        'sigma_down': 0.1306,
    },
    '铜矿开采': {
        'etf_code': '562800.SS',
        'sigma_down': 0.2302,
    },

    # 电力/能源
    '输变电设备': {
        'etf_code': '159611.SZ',
        'sigma_down': 0.1313,
    },
    '多晶硅': {
        'etf_code': '516290.SS',  # 暂用半导体设备ETF
        'sigma_down': 0.2166,
    },
}

# 14家公司的细分行业暴露
COMPANY_SUBINDUSTRY_EXPOSURE = {
    '澜起科技': {
        'exposures': [
            ('Fabless芯片设计', 1.0),
        ],
        'expected_return_1y': 0.045,  # 从V7.2提取
        'notes': '纯内存接口芯片Fabless设计'
    },

    '光迅科技': {
        'exposures': [
            ('光通信模块', 1.0),
        ],
        'expected_return_1y': 0.087,
        'notes': '纯光通信模块(800G/1.6T),垂直整合'
    },

    '生益科技': {
        'exposures': [
            ('CCL覆铜板', 1.0),
        ],
        'expected_return_1y': 0.020,
        'notes': '纯CCL覆铜板'
    },

    '建滔积层板': {
        'exposures': [
            ('CCL覆铜板', 1.0),
        ],
        'expected_return_1y': 0.086,
        'notes': '纯CCL覆铜板,成本优势'
    },

    'ASMPT': {
        'exposures': [
            ('半导体设备-后道封装', 1.0),
        ],
        'expected_return_1y': 0.147,
        'notes': '纯后道封装设备(先进封装+传统)'
    },

    '紫金矿业': {
        'exposures': [
            ('铜矿开采', 0.60),  # 铜为主
            ('黄金开采', 0.40),  # 黄金为辅
        ],
        'expected_return_1y': -0.240,
        'notes': '铜金一体化矿业,60%铜+40%黄金(利润权重)'
    },

    '中金黄金': {
        'exposures': [
            ('黄金开采', 1.0),
        ],
        'expected_return_1y': -0.295,
        'notes': '纯黄金开采'
    },

    '川恒股份': {
        'exposures': [
            ('磷化工-LFP', 1.0),
        ],
        'expected_return_1y': 0.129,
        'notes': 'LFP磷酸铁前驱体+磷肥'
    },

    '中国巨石': {
        'exposures': [
            ('玻璃纤维', 1.0),
        ],
        'expected_return_1y': -0.067,
        'notes': '纯玻纤'
    },

    '雅克科技': {
        'exposures': [
            ('半导体材料', 0.70),  # 光刻胶+前驱体为主
            ('LNG保温板', 0.30),   # LNG传统业务
        ],
        'expected_return_1y': 0.011,
        'notes': '70%半导体材料(光刻胶+前驱体)+30%LNG(利润权重)'
    },

    '中天科技': {
        'exposures': [
            ('通信设备-海缆光纤', 1.0),
        ],
        'expected_return_1y': 0.076,
        'notes': '海缆+光纤光缆+新能源(分部估值简化为通信设备)'
    },

    '江西铜业': {
        'exposures': [
            ('铜矿开采', 1.0),
        ],
        'expected_return_1y': -0.036,
        'notes': '纯铜矿+冶炼一体化'
    },

    '特变电工': {
        'exposures': [
            ('输变电设备', 0.60),  # 变压器+线缆为主
            ('多晶硅', 0.40),      # 多晶硅亏损拖累
        ],
        'expected_return_1y': -0.068,
        'notes': '60%输变电(盈利)+40%多晶硅(亏损)(利润权重)'
    },

    '联想集团': {
        'exposures': [
            ('PC制造', 1.0),
        ],
        'expected_return_1y': 0.042,
        'notes': '纯PC制造(AI PC)'
    },
}

def calculate_weighted_sigma_down(exposures):
    """计算加权σ_down (多业务公司)"""
    total_sigma = 0.0
    for subindustry, weight in exposures:
        sigma = SUBINDUSTRY_SIGMA_DOWN[subindustry]['sigma_down']
        total_sigma += weight * sigma
    return total_sigma

def calculate_vtr(expected_return, sigma_down):
    """计算VTR"""
    return expected_return / sigma_down

def fetch_chip_design_sigma():
    """实时获取芯片设计ETF的σ_down"""
    try:
        stock = yf.Ticker('512760.SS')  # 芯片ETF
        hist = stock.history(period='1y')
        returns = hist['Close'].pct_change().dropna()
        downside = returns[returns < 0]
        sigma_down = downside.std() * np.sqrt(252)
        return sigma_down
    except:
        return 0.2375  # 默认值

def main():
    # 更新Fabless芯片设计的σ_down
    chip_design_sigma = fetch_chip_design_sigma()
    SUBINDUSTRY_SIGMA_DOWN['Fabless芯片设计']['sigma_down'] = chip_design_sigma

    print("=" * 120)
    print("14家公司细分行业σ_down映射 (含多业务公司加权)")
    print("=" * 120)
    print()

    results = []

    print(f"{'公司':<12} {'细分行业暴露':<40} {'σ_down':<10} {'期望收益':<10} {'VTR':<8} {'V7.2大行业VTR':<15}")
    print("-" * 120)

    # V7.2大行业VTR (对比用)
    v72_vtr = {
        '澜起科技': 0.19, 'ASMPT': 0.61, '光迅科技': 0.37, '中天科技': 0.32, '联想集团': 0.18,
        '生益科技': 0.09, '建滔积层板': 0.38, '川恒股份': 0.57, '中国巨石': -0.29,
        '雅克科技': 0.05, '紫金矿业': -1.25, '中金黄金': -2.26, '江西铜业': -0.15, '特变电工': -0.29
    }

    for company, data in COMPANY_SUBINDUSTRY_EXPOSURE.items():
        # 计算加权σ_down
        sigma_down = calculate_weighted_sigma_down(data['exposures'])

        # 计算VTR
        expected_return = data['expected_return_1y']
        vtr = calculate_vtr(expected_return, sigma_down)

        # 行业暴露字符串
        if len(data['exposures']) == 1:
            exposure_str = f"{data['exposures'][0][0]} (100%)"
        else:
            exposure_str = ' + '.join([f"{sub}({w*100:.0f}%)" for sub, w in data['exposures']])

        # V7.2对比
        v72_vtr_val = v72_vtr.get(company, 0)
        vtr_change = ((vtr - v72_vtr_val) / abs(v72_vtr_val) * 100) if v72_vtr_val != 0 else 0

        results.append({
            'company': company,
            'exposures': exposure_str,
            'sigma_down': sigma_down,
            'expected_return': expected_return,
            'vtr': vtr,
            'v72_vtr': v72_vtr_val,
            'vtr_change_pct': vtr_change,
            'notes': data['notes']
        })

        change_icon = '🔺' if vtr_change > 5 else ('🔻' if vtr_change < -5 else '  ')
        print(f"{company:<12} {exposure_str:<40} {sigma_down*100:>6.2f}% {expected_return*100:>8.1f}% "
              f"{vtr:>8.2f} {v72_vtr_val:>6.2f} {change_icon}")

    print("=" * 120)
    print()

    # 排序并生成新VTR榜单
    results_sorted = sorted(results, key=lambda x: x['vtr'], reverse=True)

    print("=" * 120)
    print("V7.3 VTR排名 (细分行业σ_down)")
    print("=" * 120)
    print()

    print(f"{'排名':<6} {'公司':<12} {'VTR':<10} {'期望收益':<10} {'σ_down':<10} {'vs V7.2':<12} {'评级':<10}")
    print("-" * 120)

    # 计算新的分位阈值
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

        change_str = f"{r['vtr_change_pct']:+.1f}%"
        print(f"{rank:<6} {r['company']:<12} {r['vtr']:>8.2f} {r['expected_return']*100:>8.1f}% "
              f"{r['sigma_down']*100:>8.2f}% {change_str:>10} {rating:<10}")

    print("=" * 120)
    print(f"\nVTR阈值 (基于细分行业σ_down):")
    print(f"  ⭐优秀 (Top30%): VTR ≥ {p70:.2f}")
    print(f"  ✓平衡 (30-70%): {p30:.2f} ≤ VTR < {p70:.2f}")
    print(f"  ⚠️不佳 (Bottom30%): VTR < {p30:.2f}")
    print()

    # 重大变化标的
    print("=" * 120)
    print("重大变化标的 (VTR变化>10%)")
    print("=" * 120)
    print()

    major_changes = [r for r in results if abs(r['vtr_change_pct']) > 10]
    major_changes.sort(key=lambda x: abs(x['vtr_change_pct']), reverse=True)

    if major_changes:
        print(f"{'公司':<12} {'V7.2 VTR':<10} {'V7.3 VTR':<10} {'变化':<10} {'原因':<50}")
        print("-" * 120)

        for r in major_changes:
            print(f"{r['company']:<12} {r['v72_vtr']:>8.2f} {r['vtr']:>8.2f} "
                  f"{r['vtr_change_pct']:>8.1f}% {r['notes']:<50}")
    else:
        print("无重大变化 (细分行业σ_down与大行业接近)")

    print("=" * 120)
    print()

    # 保存结果
    df = pd.DataFrame(results)
    df.to_csv('data/company_subindustry_vtr.csv', index=False, encoding='utf-8-sig')
    print("✅ 结果已保存至: data/company_subindustry_vtr.csv")

    return results_sorted

if __name__ == '__main__':
    results = main()
