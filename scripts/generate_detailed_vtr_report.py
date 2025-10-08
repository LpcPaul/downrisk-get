#!/usr/bin/env python3
"""生成详细的VTR排名报告,参考FINAL_RANKING_REPORT_V7.2.md格式"""

import sys
from pathlib import Path
import pandas as pd
import yaml
import numpy as np
from datetime import datetime
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def fetch_company_data(ticker):
    """从Yahoo Finance获取公司数据"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        if hist.empty:
            return None
            
        # 计算波动率
        returns = hist['Close'].pct_change().dropna()
        negative_returns = returns[returns < 0]
        
        sigma_total = returns.std() * np.sqrt(252)
        sigma_down = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        
        # Beta (使用相应市场指数)
        beta = info.get('beta', 1.0) or 1.0
        
        return {
            'name': info.get('longName', ticker),
            'ticker': ticker,
            'current_price': info.get('currentPrice', hist['Close'].iloc[-1]),
            'pe_ratio': info.get('forwardPE') or info.get('trailingPE'),
            'pb_ratio': info.get('priceToBook'),
            'roe': info.get('returnOnEquity'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'peg_ratio': info.get('pegRatio'),
            'beta': beta,
            'dividend_yield': info.get('dividendYield', 0),
            'sigma_total': sigma_total,
            'sigma_down': sigma_down,
            'market_cap': info.get('marketCap'),
        }
    except Exception as e:
        print(f"获取 {ticker} 数据失败: {e}")
        return None

def fetch_etf_sigma_down(etf_ticker, name):
    """获取ETF的下行波动率"""
    try:
        etf = yf.Ticker(etf_ticker)
        hist = etf.history(period="1y")
        
        if hist.empty:
            return None
            
        returns = hist['Close'].pct_change().dropna()
        negative_returns = returns[returns < 0]
        
        sigma_down = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        
        return {
            'name': name,
            'ticker': etf_ticker,
            'sigma_down': sigma_down,
            'trading_days': len(returns)
        }
    except Exception as e:
        print(f"获取ETF {etf_ticker} 数据失败: {e}")
        return None

def assign_industry(ticker, name):
    """为公司分配行业及对应的sigma_down"""
    industry_mapping = {
        '002895.SZ': ('CHEM', '化工'),  # 川恒股份
        '600362.SS': ('NONFER', '有色金属'),  # 江西铜业
        '0522.HK': ('SEMI', '半导体设备'),  # ASMPT
        '0700.HK': ('TMT', '互联网'),  # 腾讯
        '0992.HK': ('TMT', '计算机'),  # 联想
        '9988.HK': ('TMT', '互联网'),  # 阿里巴巴
        '600089.SS': ('ELECTRIC', '电力设备'),  # 特变电工
        '600176.SS': ('CHEM', '化工'),  # 中国巨石
        '600489.SS': ('GOLD', '黄金'),  # 中金黄金
        '600522.SS': ('TMT', '通信设备'),  # 中天科技
        '688008.SS': ('SEMI', '半导体'),  # 澜起科技
        '601899.SS': ('GOLD_NONFER', '有色金属'),  # 紫金矿业 (60%有色+40%黄金)
        '1888.HK': ('CHEM', '化工'),  # 建滔积层板
        '002281.SZ': ('TMT', '光通信'),  # 光迅科技
        '2228.HK': ('SEMI', '半导体材料'),  # 晶泰科技
    }
    
    return industry_mapping.get(ticker, ('TMT', '其他'))

def main():
    if len(sys.argv) < 2:
        print("用法: python generate_detailed_vtr_report.py config/companies_15batch.yml")
        sys.exit(1)
    
    config_path = PROJECT_ROOT / sys.argv[1]
    
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    companies_config = config.get('companies', [])
    
    print("=" * 100)
    print("开始获取公司数据...")
    print("=" * 100)
    
    # 获取行业ETF的sigma_down
    print("\n获取行业ETF下行波动率...")
    etf_data = {
        'SEMI': fetch_etf_sigma_down('512480.SS', '半导体ETF'),
        'TMT': fetch_etf_sigma_down('512720.SS', '计算机ETF'),
        'CHEM': fetch_etf_sigma_down('159870.SZ', '化工ETF'),
        'GOLD': fetch_etf_sigma_down('518850.SS', '黄金ETF'),
        'NONFER': fetch_etf_sigma_down('512400.SS', '有色金属ETF'),
        'ELECTRIC': fetch_etf_sigma_down('516850.SS', '电力设备ETF'),
    }
    
    # 打印ETF数据
    print("\n行业ETF下行波动率数据:")
    for industry, data in etf_data.items():
        if data:
            print(f"  {industry}: σ_down = {data['sigma_down']:.2%}, 交易日={data['trading_days']}")
    
    # 获取公司数据
    print("\n获取公司数据...")
    companies_data = []
    for comp in companies_config:
        ticker = comp['ticker']
        name = comp['name']
        print(f"  获取 {name} ({ticker})...")
        
        data = fetch_company_data(ticker)
        if data:
            industry_code, industry_name = assign_industry(ticker, name)
            data['industry_code'] = industry_code
            data['industry_name'] = industry_name
            
            # 分配行业sigma_down
            if industry_code == 'GOLD_NONFER':
                # 紫金矿业特殊处理: 60%有色 + 40%黄金
                etf_nonfer = etf_data.get('NONFER')
                etf_gold = etf_data.get('GOLD')
                if etf_nonfer and etf_gold:
                    data['industry_sigma_down'] = 0.6 * etf_nonfer['sigma_down'] + 0.4 * etf_gold['sigma_down']
                else:
                    data['industry_sigma_down'] = data['sigma_down']
            else:
                etf = etf_data.get(industry_code)
                data['industry_sigma_down'] = etf['sigma_down'] if etf else data['sigma_down']
            
            # 设置Frag (脆弱性)
            data['frag'] = 0.025  # 默认2.5%
            
            companies_data.append(data)
    
    # 转换为DataFrame
    df = pd.DataFrame(companies_data)
    
    # 计算VTR的各项指标
    print("\n计算VTR指标...")
    
    for idx, row in df.iterrows():
        # 基础增长率
        earnings_growth = row['earnings_growth'] if pd.notna(row['earnings_growth']) else 0
        revenue_growth = row['revenue_growth'] if pd.notna(row['revenue_growth']) else 0
        avg_growth = (earnings_growth + revenue_growth) / 2 if pd.notna(earnings_growth) and pd.notna(revenue_growth) else (earnings_growth or revenue_growth or 0)
        df.at[idx, 'base_growth'] = max(avg_growth, 0.05)  # 保底5%
        
        # 质量系数
        roe = row['roe'] if pd.notna(row['roe']) else 0
        if roe >= 0.15:
            quality_coeff = 1.1
        elif roe >= 0.10:
            quality_coeff = 1.0
        else:
            quality_coeff = 0.8
        df.at[idx, 'quality_coeff'] = quality_coeff
        
        # 估值系数
        pe = row['pe_ratio'] if pd.notna(row['pe_ratio']) else 0
        peg = row['peg_ratio'] if pd.notna(row['peg_ratio']) else 0
        
        if peg > 0 and peg < 1.0:
            val_coeff, val_label = 1.1, 'low'
        elif peg >= 1.0 and peg < 1.5:
            val_coeff, val_label = 1.0, 'fair'
        elif peg >= 1.5:
            val_coeff, val_label = 0.9, 'high'
        elif pe > 0 and pe < 20:
            val_coeff, val_label = 1.1, 'low'
        elif pe < 35:
            val_coeff, val_label = 1.0, 'fair'
        else:
            val_coeff, val_label = 0.9, 'high'
        
        df.at[idx, 'valuation_coeff'] = val_coeff
        df.at[idx, 'valuation_label'] = val_label
        
        # 风险系数
        beta = row['beta']
        frag = row['frag']
        risk_coeff = 1.0 - frag
        if beta >= 1.3:
            risk_coeff -= 0.05
        elif beta <= 0.8:
            risk_coeff += 0.02
        risk_coeff = np.clip(risk_coeff, 0.6, 1.05)
        df.at[idx, 'risk_coeff'] = risk_coeff
        
        # 期望收益
        expected_return = df.at[idx, 'base_growth'] * quality_coeff * val_coeff * risk_coeff
        df.at[idx, 'expected_return'] = expected_return
        
        # 损失风险 (使用行业sigma_down)
        industry_sigma_down = row['industry_sigma_down']
        df.at[idx, 'loss_risk'] = industry_sigma_down
        
        # VTR
        vtr = expected_return / industry_sigma_down if industry_sigma_down > 0 else 0
        df.at[idx, 'vtr'] = vtr
    
    # 排序
    df_sorted = df.sort_values('vtr', ascending=False)
    
    # 生成报告
    report_path = PROJECT_ROOT / 'results' / 'companies_request_report.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("15家公司值博率(VTR)详细排名报告\n")
        f.write("=" * 100 + "\n")
        f.write(f"报告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据来源: Yahoo Finance API (yfinance)\n")
        f.write(f"时间窗口: 1年\n")
        f.write("分析框架: 基于V7.2方法论 - 纯行业σ_down风险模型\n")
        f.write("\n")
        f.write("期望收益 = 基础增长 × 质量系数 × 估值系数 × 风险系数\n")
        f.write("损失风险 = 行业σ_down (下行波动率)\n")
        f.write("VTR = 期望收益 / 损失风险\n")
        f.write("\n")
        
        # 行业ETF数据
        f.write("-" * 100 + "\n")
        f.write("行业ETF下行波动率 (σ_down) - 1年窗口\n")
        f.write("-" * 100 + "\n")
        for industry, data in etf_data.items():
            if data:
                f.write(f"{industry:10s} ({data['ticker']}): σ_down = {data['sigma_down']:6.2%}, 交易日数 = {data['trading_days']}\n")
        f.write("\n")
        
        # 值博率排名
        f.write("=" * 100 + "\n")
        f.write("值博率(VTR)排名 - 从高到低\n")
        f.write("=" * 100 + "\n")
        f.write(f"{'排名':<6} {'公司':<15} {'VTR':>8} {'期望收益':>10} {'损失风险':>10} {'行业':<12}\n")
        f.write("-" * 100 + "\n")
        
        for rank, (idx, row) in enumerate(df_sorted.iterrows(), 1):
            name = row['name'][:15]
            vtr = row['vtr']
            exp_ret = row['expected_return']
            loss_risk = row['loss_risk']
            industry = row['industry_name'][:12]
            
            f.write(f"{rank:<6} {name:<15} {vtr:8.4f} {exp_ret:9.2%} {loss_risk:9.2%} {industry:<12}\n")
        
        f.write("\n")
        
        # 详细拆解
        f.write("=" * 100 + "\n")
        f.write("各公司详细拆解\n")
        f.write("=" * 100 + "\n\n")
        
        for rank, (idx, row) in enumerate(df_sorted.iterrows(), 1):
            f.write("-" * 100 + "\n")
            f.write(f"排名 {rank}: {row['name']} ({row['ticker']})\n")
            f.write("-" * 100 + "\n")
            f.write(f"行业: {row['industry_name']} ({row['industry_code']})\n")
            f.write(f"当前价格: {row['current_price']:.2f}\n")
            f.write(f"市值: {row['market_cap']/1e9:.2f}B USD\n" if pd.notna(row['market_cap']) else "")
            f.write("\n")
            
            f.write("估值指标:\n")
            f.write(f"  PE: {row['pe_ratio']:.2f}\n" if pd.notna(row['pe_ratio']) else "  PE: N/A\n")
            f.write(f"  PB: {row['pb_ratio']:.2f}\n" if pd.notna(row['pb_ratio']) else "  PB: N/A\n")
            f.write(f"  PEG: {row['peg_ratio']:.2f}\n" if pd.notna(row['peg_ratio']) else "  PEG: N/A\n")
            f.write(f"  估值分类: {row['valuation_label']}\n")
            f.write("\n")
            
            f.write("财务指标:\n")
            f.write(f"  ROE: {row['roe']:.2%}\n" if pd.notna(row['roe']) else "  ROE: N/A\n")
            f.write(f"  利润率: {row['profit_margin']:.2%}\n" if pd.notna(row['profit_margin']) else "  利润率: N/A\n")
            f.write(f"  营业利润率: {row['operating_margin']:.2%}\n" if pd.notna(row['operating_margin']) else "  营业利润率: N/A\n")
            f.write(f"  收入增长: {row['revenue_growth']:.2%}\n" if pd.notna(row['revenue_growth']) else "  收入增长: N/A\n")
            f.write(f"  盈利增长: {row['earnings_growth']:.2%}\n" if pd.notna(row['earnings_growth']) else "  盈利增长: N/A\n")
            f.write(f"  股息率: {row['dividend_yield']:.2%}\n")
            f.write("\n")
            
            f.write("风险指标:\n")
            f.write(f"  Beta: {row['beta']:.3f}\n")
            f.write(f"  个股σ_total: {row['sigma_total']:.2%}\n")
            f.write(f"  个股σ_down: {row['sigma_down']:.2%}\n")
            f.write(f"  行业σ_down: {row['industry_sigma_down']:.2%}\n")
            f.write(f"  脆弱性Frag: {row['frag']:.2%}\n")
            f.write("\n")
            
            f.write("VTR分解:\n")
            f.write(f"  基础增长率: {row['base_growth']:.2%}\n")
            f.write(f"  质量系数: {row['quality_coeff']:.2f}\n")
            f.write(f"  估值系数: {row['valuation_coeff']:.2f}\n")
            f.write(f"  风险系数: {row['risk_coeff']:.2f}\n")
            f.write(f"  期望收益: {row['expected_return']:.2%} = {row['base_growth']:.2%} × {row['quality_coeff']:.2f} × {row['valuation_coeff']:.2f} × {row['risk_coeff']:.2f}\n")
            f.write(f"  损失风险: {row['loss_risk']:.2%} (行业σ_down)\n")
            f.write(f"  VTR: {row['vtr']:.4f}\n")
            f.write("\n")
        
        f.write("=" * 100 + "\n")
        f.write("报告结束\n")
        f.write("=" * 100 + "\n")
    
    # 保存Excel
    excel_path = PROJECT_ROOT / 'results' / 'companies_request.xlsx'
    df_sorted.to_excel(excel_path, index=False)
    
    print(f"\n✓ 报告已保存: {report_path}")
    print(f"✓ Excel已保存: {excel_path}")

if __name__ == "__main__":
    main()
