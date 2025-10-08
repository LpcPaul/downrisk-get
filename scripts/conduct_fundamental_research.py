#!/usr/bin/env python3
"""
Step 1: 基本面研究 - 严格按照PROJECT_EXECUTION_WORKFLOW.md执行
收集15家公司的:
1. 财报数据 (最近4个季度)
2. 行业阶段分析
3. 个股业务期待点和风险点
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 15家公司配置
COMPANIES = {
    'ASMPT': {'ticker': '0522.HK', 'name': 'ASMPT', '细分行业': '半导体设备-后道封装'},
    '川恒股份': {'ticker': '002895.SZ', 'name': '川恒股份', '细分行业': '磷化工-LFP'},
    '晶泰科技': {'ticker': '2228.HK', 'name': '晶泰科技', '细分行业': 'AI制药'},
    '建滔积层板': {'ticker': '1888.HK', 'name': '建滔积层板', '细分行业': 'CCL覆铜板'},
    '光迅科技': {'ticker': '002281.SZ', 'name': '光迅科技', '细分行业': '光通信模块'},
    '腾讯控股': {'ticker': '0700.HK', 'name': '腾讯控股', '细分行业': '互联网平台'},
    '中天科技': {'ticker': '600522.SS', 'name': '中天科技', '细分行业': '通信设备-海缆光纤'},
    '阿里巴巴': {'ticker': '9988.HK', 'name': '阿里巴巴', '细分行业': '互联网平台'},
    '澜起科技': {'ticker': '688008.SS', 'name': '澜起科技', '细分行业': 'Fabless芯片设计'},
    '联想集团': {'ticker': '0992.HK', 'name': '联想集团', '细分行业': 'PC制造'},
    '江西铜业': {'ticker': '600362.SS', 'name': '江西铜业', '细分行业': '铜矿开采'},
    '中国巨石': {'ticker': '600176.SS', 'name': '中国巨石', '细分行业': '玻璃纤维'},
    '特变电工': {'ticker': '600089.SS', 'name': '特变电工', '细分行业': '输变电设备+多晶硅'},
    '紫金矿业': {'ticker': '601899.SS', 'name': '紫金矿业', '细分行业': '铜矿开采+黄金开采'},
    '中金黄金': {'ticker': '600489.SS', 'name': '中金黄金', '细分行业': '黄金开采'},
}

def fetch_financial_data(ticker, company_name):
    """
    从Yahoo Finance获取财报数据
    """
    print(f"\n{'='*80}")
    print(f"正在获取 {company_name} ({ticker}) 的财务数据...")
    print(f"{'='*80}")

    try:
        stock = yf.Ticker(ticker)

        # 获取基本信息
        info = stock.info

        # 获取季度财务数据
        quarterly_financials = stock.quarterly_financials
        quarterly_income = stock.quarterly_income_stmt
        quarterly_balance = stock.quarterly_balance_sheet
        quarterly_cashflow = stock.quarterly_cashflow

        # 获取年度财务数据作为补充
        annual_financials = stock.financials

        # 获取历史价格数据用于估值分析
        hist = stock.history(period="2y")

        result = {
            'company': company_name,
            'ticker': ticker,
            'info': {
                'marketCap': info.get('marketCap', 'N/A'),
                'trailingPE': info.get('trailingPE', 'N/A'),
                'forwardPE': info.get('forwardPE', 'N/A'),
                'priceToBook': info.get('priceToBook', 'N/A'),
                'profitMargins': info.get('profitMargins', 'N/A'),
                'operatingMargins': info.get('operatingMargins', 'N/A'),
                'returnOnEquity': info.get('returnOnEquity', 'N/A'),
                'returnOnAssets': info.get('returnOnAssets', 'N/A'),
                'debtToEquity': info.get('debtToEquity', 'N/A'),
                'currentRatio': info.get('currentRatio', 'N/A'),
                'freeCashflow': info.get('freeCashflow', 'N/A'),
                'operatingCashflow': info.get('operatingCashflow', 'N/A'),
                'revenueGrowth': info.get('revenueGrowth', 'N/A'),
                'earningsGrowth': info.get('earningsGrowth', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
            },
            'quarterly_data': {},
            'annual_data': {},
            'price_history': {
                'current_price': hist['Close'].iloc[-1] if len(hist) > 0 else 'N/A',
                '52w_high': hist['Close'].max() if len(hist) > 0 else 'N/A',
                '52w_low': hist['Close'].min() if len(hist) > 0 else 'N/A',
                'ytd_return': ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) if len(hist) > 0 else 'N/A',
            }
        }

        # 处理季度数据
        if not quarterly_income.empty:
            quarters = quarterly_income.columns[:4]  # 最近4个季度
            result['quarterly_data'] = {
                'periods': [q.strftime('%Y-Q%m') for q in quarters],
                'total_revenue': quarterly_income.loc['Total Revenue', quarters].tolist() if 'Total Revenue' in quarterly_income.index else [],
                'gross_profit': quarterly_income.loc['Gross Profit', quarters].tolist() if 'Gross Profit' in quarterly_income.index else [],
                'operating_income': quarterly_income.loc['Operating Income', quarters].tolist() if 'Operating Income' in quarterly_income.index else [],
                'net_income': quarterly_income.loc['Net Income', quarters].tolist() if 'Net Income' in quarterly_income.index else [],
            }

        # 处理现金流数据
        if not quarterly_cashflow.empty:
            quarters = quarterly_cashflow.columns[:4]
            if 'Operating Cash Flow' in quarterly_cashflow.index:
                result['quarterly_data']['operating_cashflow'] = quarterly_cashflow.loc['Operating Cash Flow', quarters].tolist()
            if 'Free Cash Flow' in quarterly_cashflow.index:
                result['quarterly_data']['free_cashflow'] = quarterly_cashflow.loc['Free Cash Flow', quarters].tolist()

        # 计算同比增长率 (如果有去年同期数据)
        if 'total_revenue' in result['quarterly_data'] and len(result['quarterly_data']['total_revenue']) >= 4:
            revenues = result['quarterly_data']['total_revenue']
            result['quarterly_data']['revenue_yoy_growth'] = [
                ((revenues[i] / revenues[i+4] - 1) * 100) if i+4 < len(revenues) and revenues[i+4] != 0 else None
                for i in range(min(4, len(revenues)))
            ]

        print(f"✅ {company_name} 数据获取成功")
        print(f"   - 当前PE: {result['info']['trailingPE']}")
        print(f"   - PB: {result['info']['priceToBook']}")
        print(f"   - ROE: {result['info']['returnOnEquity']}")
        print(f"   - 最近4季度数据: {len(result['quarterly_data'].get('periods', []))}个季度")

        return result

    except Exception as e:
        print(f"❌ {company_name} 数据获取失败: {str(e)}")
        return {
            'company': company_name,
            'ticker': ticker,
            'error': str(e),
            'info': {},
            'quarterly_data': {},
            'annual_data': {},
            'price_history': {}
        }

def analyze_quarterly_trends(quarterly_data):
    """
    分析季度数据趋势
    """
    if not quarterly_data or 'total_revenue' not in quarterly_data:
        return "数据不足,无法分析趋势"

    revenues = quarterly_data.get('total_revenue', [])
    if len(revenues) < 4:
        return "数据不足,无法分析趋势"

    # 计算环比增长
    qoq_growth = [(revenues[i] - revenues[i+1]) / revenues[i+1] * 100
                  for i in range(len(revenues)-1) if revenues[i+1] != 0]

    if len(qoq_growth) >= 3:
        if all(g > 5 for g in qoq_growth[:3]):
            return "加速增长 ⬆️⬆️"
        elif all(g > 0 for g in qoq_growth[:3]):
            return "平稳增长 ⬆️"
        elif all(g < -5 for g in qoq_growth[:3]):
            return "加速下滑 ⬇️⬇️"
        elif all(g < 0 for g in qoq_growth[:3]):
            return "平稳下滑 ⬇️"
        else:
            return "波动 〜"

    return "数据不足"

def generate_fundamental_report(data):
    """
    生成基本面研究报告
    """
    report = []
    report.append(f"\n{'='*100}")
    report.append(f"基本面研究报告: {data['company']} ({data['ticker']})")
    report.append(f"{'='*100}\n")

    if 'error' in data:
        report.append(f"⚠️ 数据获取失败: {data['error']}\n")
        return "\n".join(report)

    # 1. 财报分析
    report.append("📊 1. 财报分析 (最近4个季度)")
    report.append("-" * 100)

    info = data['info']
    quarterly = data['quarterly_data']

    report.append(f"\n估值指标:")
    report.append(f"  当前PE: {info.get('trailingPE', 'N/A')}")
    report.append(f"  PB: {info.get('priceToBook', 'N/A')}")
    report.append(f"  市值: {info.get('marketCap', 'N/A'):,.0f}" if isinstance(info.get('marketCap'), (int, float)) else f"  市值: N/A")

    report.append(f"\n盈利能力:")
    report.append(f"  毛利率: {info.get('profitMargins', 'N/A')}")
    report.append(f"  营业利润率: {info.get('operatingMargins', 'N/A')}")
    report.append(f"  ROE: {info.get('returnOnEquity', 'N/A')}")
    report.append(f"  ROA: {info.get('returnOnAssets', 'N/A')}")

    if quarterly.get('periods'):
        report.append(f"\n最近4个季度数据:")
        report.append(f"  季度: {' | '.join(quarterly['periods'])}")

        if quarterly.get('total_revenue'):
            revenues = quarterly['total_revenue']
            report.append(f"  营收: {' | '.join([f'{r/1e9:.2f}B' if r > 1e9 else f'{r/1e6:.2f}M' for r in revenues])}")
            trend = analyze_quarterly_trends(quarterly)
            report.append(f"  趋势: {trend}")

        if quarterly.get('net_income'):
            profits = quarterly['net_income']
            report.append(f"  净利润: {' | '.join([f'{p/1e9:.2f}B' if abs(p) > 1e9 else f'{p/1e6:.2f}M' for p in profits])}")

        if quarterly.get('revenue_yoy_growth'):
            yoy = quarterly['revenue_yoy_growth']
            yoy_str = ' | '.join([f'{g:.1f}%' if g is not None else 'N/A' for g in yoy])
            report.append(f"  营收同比: {yoy_str}")

    report.append(f"\n现金流:")
    report.append(f"  经营现金流: {info.get('operatingCashflow', 'N/A')}")
    report.append(f"  自由现金流: {info.get('freeCashflow', 'N/A')}")

    report.append(f"\n财务健康:")
    report.append(f"  资产负债率: {info.get('debtToEquity', 'N/A')}")
    report.append(f"  流动比率: {info.get('currentRatio', 'N/A')}")

    # 2. 股价表现
    price_hist = data['price_history']
    report.append(f"\n📈 2. 股价表现")
    report.append("-" * 100)
    report.append(f"  当前价: {price_hist.get('current_price', 'N/A')}")
    report.append(f"  52周高点: {price_hist.get('52w_high', 'N/A')}")
    report.append(f"  52周低点: {price_hist.get('52w_low', 'N/A')}")
    if isinstance(price_hist.get('ytd_return'), (int, float)):
        report.append(f"  年初至今回报: {price_hist['ytd_return']:.2%}")

    report.append("\n")
    return "\n".join(report)

def main():
    print("=" * 100)
    print("开始执行 Step 1: 基本面研究")
    print("=" * 100)
    print(f"研究对象: {len(COMPANIES)}家公司")
    print(f"数据来源: Yahoo Finance API")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建输出目录
    output_dir = PROJECT_ROOT / 'data' / 'fundamental_research'
    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集所有公司数据
    all_data = {}
    all_reports = []

    for company_name, config in COMPANIES.items():
        ticker = config['ticker']
        data = fetch_financial_data(ticker, company_name)
        data['细分行业'] = config['细分行业']

        all_data[company_name] = data

        # 生成个别报告
        report = generate_fundamental_report(data)
        all_reports.append(report)
        print(report)

    # 保存JSON数据
    json_path = output_dir / 'financial_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        # 转换numpy/pandas类型为Python原生类型
        import json
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            else:
                try:
                    if pd.isna(obj):
                        return None
                except (ValueError, TypeError):
                    pass
            return obj

        serializable_data = {}
        for k, v in all_data.items():
            serializable_data[k] = {}
            for key, value in v.items():
                if isinstance(value, dict):
                    serializable_data[k][key] = {
                        sub_k: convert_to_serializable(sub_v)
                        for sub_k, sub_v in value.items()
                    }
                else:
                    serializable_data[k][key] = convert_to_serializable(value)

        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

    # 保存综合报告
    report_path = output_dir / 'fundamental_research_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("15家公司基本面研究综合报告\n")
        f.write("=" * 100 + "\n")
        f.write(f"报告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据来源: Yahoo Finance API\n")
        f.write(f"研究范围: {len(COMPANIES)}家公司\n")
        f.write("\n")

        for report in all_reports:
            f.write(report)
            f.write("\n" + "=" * 100 + "\n\n")

    print("\n" + "=" * 100)
    print("✅ Step 1: 基本面研究完成")
    print("=" * 100)
    print(f"✅ JSON数据已保存: {json_path}")
    print(f"✅ 综合报告已保存: {report_path}")
    print("\n下一步: 进行行业研究和个股分析 (Step 1.2, 1.3)")

if __name__ == "__main__":
    main()
