#!/usr/bin/env python3
"""
计算细分行业ETF的σ_down (下行半方差)
基于用户反馈: 大行业ETF太粗糙,需要精确到细分行业
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

# 细分行业ETF映射 (基于PRECISE_INDUSTRY_SEGMENTATION_V7.md)
SUBINDUSTRY_ETFS = {
    # 半导体细分
    'Fabless芯片设计': {
        'etf_code': '159995.SZ',  # 集成电路ETF
        'etf_name': '集成电路ETF',
        'companies': ['澜起科技'],
        'notes': '内存接口芯片属于Fabless设计,用集成电路ETF'
    },
    '半导体设备-后道封装': {
        'etf_code': '516290.SS',  # 半导体设备ETF
        'etf_name': '半导体设备ETF',
        'companies': ['ASMPT'],
        'notes': 'ASMPT后道封装设备,专用半导体设备ETF'
    },
    '半导体材料': {
        'etf_code': '516020.SS',  # 电子化学品ETF
        'etf_name': '电子化学品ETF',
        'companies': ['雅克科技(70%)'],  # 雅克70%半导体材料
        'notes': '光刻胶+前驱体+蚀刻液属于电子化学品'
    },

    # TMT细分
    '光通信模块': {
        'etf_code': '516630.SS',  # 光通信ETF
        'etf_name': '光通信ETF',
        'companies': ['光迅科技'],
        'notes': '800G光模块,专用光通信ETF'
    },
    '通信设备-海缆光纤': {
        'etf_code': '515880.SS',  # 通信设备ETF
        'etf_name': '通信设备ETF',
        'companies': ['中天科技'],
        'notes': '海缆+光纤光缆属于通信设备'
    },
    'PC制造': {
        'etf_code': '512720.SS',  # 计算机ETF
        'etf_name': '计算机ETF',
        'companies': ['联想集团'],
        'notes': 'AI PC属于计算机硬件'
    },

    # 化工细分
    'CCL覆铜板': {
        'etf_code': '159870.SZ',  # 化工新材料ETF
        'etf_name': '化工新材料ETF',
        'companies': ['生益科技', '建滔积层板'],
        'notes': 'CCL属于电子化工材料'
    },
    '磷化工-LFP': {
        'etf_code': '159870.SZ',  # 化工新材料ETF (无更细分的磷化工ETF)
        'etf_name': '化工新材料ETF',
        'companies': ['川恒股份'],
        'notes': 'LFP磷酸铁前驱体属于新材料化工,暂用化工新材料ETF'
    },
    '玻璃纤维': {
        'etf_code': '159870.SZ',  # 化工新材料ETF
        'etf_name': '化工新材料ETF',
        'companies': ['中国巨石'],
        'notes': '玻纤属于化工新材料'
    },
    'LNG保温板': {
        'etf_code': '159870.SZ',  # 化工新材料ETF
        'etf_name': '化工新材料ETF',
        'companies': ['雅克科技(30%)'],  # 雅克30%LNG
        'notes': 'LNG保温板属于化工材料,雅克科技次要业务'
    },

    # 有色金属细分
    '黄金开采': {
        'etf_code': '518850.SS',  # 黄金ETF
        'etf_name': '黄金ETF',
        'companies': ['中金黄金', '紫金矿业(40%)'],
        'notes': '纯黄金矿业'
    },
    '铜矿开采': {
        'etf_code': '562800.SS',  # 铜ETF
        'etf_name': '铜ETF',
        'companies': ['江西铜业', '紫金矿业(60%)'],
        'notes': '铜矿+冶炼一体化'
    },

    # 能源/电力设备
    '输变电设备': {
        'etf_code': '159611.SZ',  # 电力设备ETF (如果没有则用工业ETF)
        'etf_name': '电力设备ETF',
        'companies': ['特变电工(60%)'],
        'notes': '变压器+线缆+EPC'
    },
    '多晶硅': {
        'etf_code': '516290.SS',  # 暂用半导体设备(多晶硅生产设备),或新能源ETF
        'etf_name': '光伏产业ETF',
        'companies': ['特变电工(40%)'],
        'notes': '多晶硅属于光伏上游,周期性强'
    },
}

def calculate_sigma_down(ticker, period='1y'):
    """
    计算单个ETF的σ_down (下行半方差年化)

    Parameters:
    - ticker: ETF代码
    - period: 数据窗口 (默认1年)

    Returns:
    - sigma_down: 下行波动率 (年化)
    - sigma_total: 总波动率 (年化)
    - sample_days: 样本天数
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if len(hist) < 50:
            return None, None, len(hist), "数据不足"

        returns = hist['Close'].pct_change().dropna()
        downside_returns = returns[returns < 0]

        if len(downside_returns) < 10:
            return None, None, len(returns), "负收益样本不足"

        sigma_down = downside_returns.std() * np.sqrt(252)
        sigma_total = returns.std() * np.sqrt(252)

        return sigma_down, sigma_total, len(returns), "成功"

    except Exception as e:
        return None, None, 0, str(e)

def main():
    print("=" * 100)
    print("细分行业ETF下行波动率计算")
    print(f"数据窗口: 2024-10-06至2025-10-06 (1年)")
    print(f"计算时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    print()

    results = []

    # 计算每个细分行业的σ_down
    for subindustry, info in SUBINDUSTRY_ETFS.items():
        etf_code = info['etf_code']
        etf_name = info['etf_name']

        print(f"正在计算: {subindustry:20} ({etf_code})")

        sigma_down, sigma_total, days, status = calculate_sigma_down(etf_code)

        if sigma_down is not None:
            results.append({
                'subindustry': subindustry,
                'etf_code': etf_code,
                'etf_name': etf_name,
                'sigma_down': sigma_down,
                'sigma_total': sigma_total,
                'days': days,
                'companies': ', '.join(info['companies']),
                'notes': info['notes']
            })

            status_icon = '✅' if sigma_down < 0.50 else '⚠️'
            print(f"  {status_icon} σ_down: {sigma_down*100:.2f}%  σ_total: {sigma_total*100:.2f}%  样本: {days}天")
        else:
            print(f"  ❌ 失败: {status}")

        print()

    # 生成汇总表
    print("=" * 100)
    print("细分行业σ_down汇总")
    print("=" * 100)
    print()

    df = pd.DataFrame(results)
    df = df.sort_values('sigma_down')

    print(f"{'细分行业':<25} {'ETF代码':<12} {'σ_down':<10} {'σ_total':<10} {'样本天数':<8} {'适用公司':<30}")
    print("-" * 100)

    for _, row in df.iterrows():
        print(f"{row['subindustry']:<25} {row['etf_code']:<12} "
              f"{row['sigma_down']*100:>6.2f}% {row['sigma_total']*100:>8.2f}% "
              f"{row['days']:>6}天 {row['companies']:<30}")

    print("=" * 100)
    print()

    # 对比大行业vs细分行业
    print("=" * 100)
    print("大行业 vs 细分行业 σ_down 对比")
    print("=" * 100)
    print()

    # 大行业数据 (V7.2)
    broad_industry = {
        'SEMI (半导体)': 0.2414,
        'TMT (科技/通信)': 0.2376,
        'CHEM (化工)': 0.2279,
        'GOLD (黄金)': 0.1306,
        'NONFER (有色金属)': 0.2330,
    }

    print(f"{'大行业':<20} {'σ_down':<10} {'细分行业':<30} {'σ_down':<10} {'差异':<10}")
    print("-" * 100)

    # 示例对比
    comparisons = [
        ('SEMI (半导体)', 0.2414, 'Fabless芯片设计', None),
        ('SEMI (半导体)', 0.2414, '半导体设备-后道封装', None),
        ('TMT (科技/通信)', 0.2376, '光通信模块', None),
        ('TMT (科技/通信)', 0.2376, '通信设备-海缆光纤', None),
        ('CHEM (化工)', 0.2279, 'CCL覆铜板', None),
        ('CHEM (化工)', 0.2279, '磷化工-LFP', None),
        ('GOLD (黄金)', 0.1306, '黄金开采', None),
        ('NONFER (有色金属)', 0.2330, '铜矿开采', None),
    ]

    for broad_name, broad_sigma, sub_name, _ in comparisons:
        sub_row = df[df['subindustry'] == sub_name]
        if not sub_row.empty:
            sub_sigma = sub_row.iloc[0]['sigma_down']
            diff = (sub_sigma - broad_sigma) / broad_sigma * 100
            diff_str = f"{diff:+.1f}%"

            print(f"{broad_name:<20} {broad_sigma*100:>6.2f}% {sub_name:<30} "
                  f"{sub_sigma*100:>6.2f}% {diff_str:>10}")

    print("=" * 100)
    print()

    # 保存结果
    output_file = 'data/subindustry_sigma_down.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ 结果已保存至: {output_file}")
    print()

    return df

if __name__ == '__main__':
    results_df = main()
