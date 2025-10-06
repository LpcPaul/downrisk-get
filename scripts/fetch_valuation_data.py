#!/usr/bin/env python3
"""
估值数据采集脚本
使用yfinance API获取实时PE/PB等估值指标
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import yaml
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_stock_valuation(ticker: str, market: str = "A股") -> dict:
    """
    获取股票估值数据

    Args:
        ticker: 股票代码
        market: 市场类型 (A股/港股)

    Returns:
        包含估值指标的字典
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
            'ticker': ticker,
            'market': market,
            'name': info.get('longName') or info.get('shortName', 'N/A'),
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'currency': info.get('currency', 'N/A'),

            # PE指标
            'pe_trailing': info.get('trailingPE'),  # PE TTM
            'pe_forward': info.get('forwardPE'),    # 预测PE

            # PB指标
            'pb': info.get('priceToBook'),

            # PS指标
            'ps_trailing': info.get('priceToSalesTrailing12Months'),

            # 其他估值指标
            'peg_ratio': info.get('pegRatio'),
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'ev_to_revenue': info.get('enterpriseToRevenue'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),

            # 盈利指标
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'roe': info.get('returnOnEquity'),

            # 增长指标
            'earnings_growth': info.get('earningsGrowth'),
            'revenue_growth': info.get('revenueGrowth'),

            # 其他
            'beta': info.get('beta'),
            'dividend_yield': info.get('dividendYield'),

            # 数据时间戳
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    except Exception as e:
        print(f"❌ 获取 {ticker} 数据失败: {e}")
        return {
            'ticker': ticker,
            'market': market,
            'error': str(e),
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def main():
    """主函数"""

    # 定义14家公司的股票代码
    companies = [
        # 港股
        {'name': '联想集团', 'ticker': '0992.HK', 'market': '港股'},
        {'name': 'ASMPT', 'ticker': '0522.HK', 'market': '港股'},
        {'name': '建滔积层板', 'ticker': '1888.HK', 'market': '港股'},
        {'name': '紫金矿业', 'ticker': '2899.HK', 'market': '港股'},

        # A股
        {'name': '澜起科技', 'ticker': '688008.SS', 'market': 'A股'},
        {'name': '中金黄金', 'ticker': '600489.SS', 'market': 'A股'},
        {'name': '中天科技', 'ticker': '600522.SS', 'market': 'A股'},
        {'name': '中国巨石', 'ticker': '600176.SS', 'market': 'A股'},
        {'name': '江西铜业', 'ticker': '600362.SS', 'market': 'A股'},
        {'name': '雅克科技', 'ticker': '002409.SZ', 'market': 'A股'},
        {'name': '生益科技', 'ticker': '600183.SS', 'market': 'A股'},
        {'name': '光迅科技', 'ticker': '002281.SZ', 'market': 'A股'},
        {'name': '特变电工', 'ticker': '600089.SS', 'market': 'A股'},
        {'name': '川恒股份', 'ticker': '002895.SZ', 'market': 'A股'},
    ]

    print("="*80)
    print("开始采集估值数据...")
    print("="*80)
    print()

    results = []

    for company in companies:
        print(f"正在获取 {company['name']} ({company['ticker']}) 的估值数据...")
        valuation = get_stock_valuation(company['ticker'], company['market'])
        valuation['company_name'] = company['name']
        results.append(valuation)

        # 打印关键指标
        if 'error' not in valuation:
            print(f"  ✓ PE(TTM): {valuation['pe_trailing']}")
            print(f"  ✓ PE(Forward): {valuation['pe_forward']}")
            print(f"  ✓ PB: {valuation['pb']}")
            print(f"  ✓ PEG: {valuation['peg_ratio']}")
        print()

    # 创建DataFrame
    df = pd.DataFrame(results)

    # 调整列顺序
    cols_order = [
        'company_name', 'ticker', 'market', 'name', 'current_price', 'currency',
        'pe_trailing', 'pe_forward', 'pb', 'ps_trailing', 'peg_ratio',
        'market_cap', 'beta', 'roe', 'earnings_growth', 'revenue_growth',
        'dividend_yield', 'fetch_time'
    ]

    existing_cols = [col for col in cols_order if col in df.columns]
    df = df[existing_cols + [col for col in df.columns if col not in existing_cols]]

    # 保存到Excel
    output_path = project_root / 'data' / 'valuation_data.xlsx'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 主数据表
        df.to_excel(writer, sheet_name='估值数据', index=False)

        # 关键指标汇总表
        summary_df = df[['company_name', 'ticker', 'market', 'pe_trailing',
                         'pe_forward', 'pb', 'peg_ratio', 'roe', 'beta']].copy()
        summary_df.to_excel(writer, sheet_name='关键指标', index=False)

        # PE分析表
        pe_df = df[['company_name', 'ticker', 'pe_trailing', 'pe_forward',
                    'peg_ratio', 'earnings_growth']].copy()
        pe_df = pe_df.sort_values('pe_trailing', ascending=True)
        pe_df.to_excel(writer, sheet_name='PE分析', index=False)

        # PB分析表
        pb_df = df[['company_name', 'ticker', 'pb', 'roe', 'market_cap']].copy()
        pb_df = pb_df.sort_values('pb', ascending=True)
        pb_df.to_excel(writer, sheet_name='PB分析', index=False)

    print("="*80)
    print(f"✓ 数据已保存到: {output_path}")
    print("="*80)
    print()

    # 打印汇总表
    print("关键估值指标汇总:")
    print("="*80)
    summary_display = summary_df.copy()
    summary_display['PE(TTM)'] = summary_display['pe_trailing'].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )
    summary_display['PB'] = summary_display['pb'].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )
    summary_display['PEG'] = summary_display['peg_ratio'].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
    )

    print(summary_display[['company_name', 'ticker', 'PE(TTM)', 'PB', 'PEG']].to_string(index=False))
    print()

    # 生成YAML配置
    yaml_data = {
        'valuation_data': [],
        'metadata': {
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_source': 'Yahoo Finance API (yfinance)',
            'total_companies': len(results)
        }
    }

    for result in results:
        if 'error' not in result:
            yaml_data['valuation_data'].append({
                'name': result['company_name'],
                'ticker': result['ticker'],
                'market': result['market'],
                'valuation': {
                    'pe_trailing': result.get('pe_trailing'),
                    'pe_forward': result.get('pe_forward'),
                    'pb': result.get('pb'),
                    'ps_trailing': result.get('ps_trailing'),
                    'peg_ratio': result.get('peg_ratio')
                },
                'fundamentals': {
                    'roe': result.get('roe'),
                    'beta': result.get('beta'),
                    'earnings_growth': result.get('earnings_growth'),
                    'revenue_growth': result.get('revenue_growth')
                }
            })

    # 保存YAML
    yaml_path = project_root / 'data' / 'valuation_data.yml'
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✓ YAML配置已保存到: {yaml_path}")
    print()

    return df


if __name__ == '__main__':
    main()
