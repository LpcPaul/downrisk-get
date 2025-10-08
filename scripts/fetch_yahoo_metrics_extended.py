#!/usr/bin/env python3
"""Fetch extended Yahoo Finance metrics for custom company list."""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRADING_DAYS_PER_YEAR = 252

COMPANIES: List[Dict[str, str]] = [
    {"name": "雅克科技", "ticker": "002409.SZ", "market": "A股"},
    {"name": "赛腾股份", "ticker": "603283.SS", "market": "A股"},
    {"name": "生益科技", "ticker": "600183.SS", "market": "A股"},
    {"name": "建滔积层板", "ticker": "1888.HK", "market": "港股"},
    {"name": "锦波生物", "ticker": "300832.SZ", "market": "A股"},
    {"name": "中宠股份", "ticker": "002891.SZ", "market": "A股"},
    {"name": "爱美客", "ticker": "300896.SZ", "market": "A股"},
    {"name": "澜起科技", "ticker": "688008.SS", "market": "A股"},
    {"name": "长电科技", "ticker": "600584.SS", "market": "A股"},
    {"name": "中天科技", "ticker": "600522.SS", "market": "A股"},
    {"name": "中金黄金", "ticker": "600489.SS", "market": "A股"},
    {"name": "中国巨石", "ticker": "600176.SS", "market": "A股"},
    {"name": "舜宇光学", "ticker": "2382.HK", "market": "港股"},
    {"name": "申洲国际", "ticker": "2313.HK", "market": "港股"},
    {"name": "联想集团", "ticker": "0992.HK", "market": "港股"},
    {"name": "ASMPT", "ticker": "0522.HK", "market": "港股"},
    {"name": "汇川技术", "ticker": "300124.SZ", "market": "A股"},
]


def annualized_volatility(returns: pd.Series) -> float:
    if returns is None or returns.empty:
        return math.nan
    return returns.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR)


def annualized_downside_volatility(returns: pd.Series) -> float:
    if returns is None or returns.empty:
        return math.nan
    downside = np.minimum(returns, 0.0)
    semi_variance = np.mean(np.square(downside))
    return math.sqrt(semi_variance) * math.sqrt(TRADING_DAYS_PER_YEAR)


def fetch_price_series(ticker: str, period: str = "1y") -> pd.Series | None:
    try:
        data = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data = data.xs(ticker, axis=1, level=1)
        price_col = "Adj Close" if "Adj Close" in data.columns else "Close"
        return data[price_col].dropna()
    except Exception as exc:
        print(f"❌ 下载 {ticker} 行情失败: {exc}")
        return None


def fetch_company_snapshot(ticker: str) -> Dict[str, float | str | None]:
    stock = yf.Ticker(ticker)
    info: Dict[str, float | str | None] = {}
    try:
        info = stock.info
    except Exception as exc:
        print(f"⚠️ 无法获取 {ticker} info: {exc}")

    return {
        "name_long": info.get("longName") or info.get("shortName"),
        "currency": info.get("currency"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "pe_trailing": info.get("trailingPE"),
        "pe_forward": info.get("forwardPE"),
        "pb": info.get("priceToBook"),
        "ps_trailing": info.get("priceToSalesTrailing12Months"),
        "peg_ratio": info.get("pegRatio"),
        "beta_info": info.get("beta"),
        "roe": info.get("returnOnEquity"),
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "earnings_growth": info.get("earningsGrowth"),
        "revenue_growth": info.get("revenueGrowth"),
        "dividend_yield": info.get("dividendYield"),
    }


def main() -> None:
    records = []
    yaml_records = []

    print("=" * 100)
    print("开始采集 Yahoo Finance 数据……")
    print("=" * 100)

    for item in COMPANIES:
        name = item["name"]
        ticker = item["ticker"]
        market = item.get("market", "未知")
        print(f"获取 {name} ({ticker}) …")

        snapshot = fetch_company_snapshot(ticker)
        prices = fetch_price_series(ticker, period="1y")

        if prices is None or prices.empty:
            print(f"  ⚠️ {ticker} 无有效价格数据，跳过波动率计算。")
            sigma_total = math.nan
            sigma_down = math.nan
            trading_days = 0
            start_date = end_date = None
        else:
            returns = prices.pct_change().dropna()
            sigma_total = annualized_volatility(returns)
            sigma_down = annualized_downside_volatility(returns)
            trading_days = len(prices)
            start_date = prices.index[0].date().isoformat()
            end_date = prices.index[-1].date().isoformat()

        record = {
            "company_name": name,
            "ticker": ticker,
            "market": market,
            "currency": snapshot.get("currency"),
            "current_price": snapshot.get("current_price"),
            "market_cap": snapshot.get("market_cap"),
            "pe_trailing": snapshot.get("pe_trailing"),
            "pe_forward": snapshot.get("pe_forward"),
            "pb": snapshot.get("pb"),
            "ps_trailing": snapshot.get("ps_trailing"),
            "peg_ratio": snapshot.get("peg_ratio"),
            "beta_info": snapshot.get("beta_info"),
            "roe": snapshot.get("roe"),
            "profit_margin": snapshot.get("profit_margin"),
            "operating_margin": snapshot.get("operating_margin"),
            "earnings_growth": snapshot.get("earnings_growth"),
            "revenue_growth": snapshot.get("revenue_growth"),
            "dividend_yield": snapshot.get("dividend_yield"),
            "sigma_total": sigma_total,
            "sigma_down": sigma_down,
            "trading_days": trading_days,
            "start_date": start_date,
            "end_date": end_date,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        records.append(record)

        yaml_records.append({
            "name": name,
            "ticker": ticker,
            "market": market,
            "valuation": {
                "current_price": snapshot.get("current_price"),
                "pe_trailing": snapshot.get("pe_trailing"),
                "pe_forward": snapshot.get("pe_forward"),
                "pb": snapshot.get("pb"),
                "ps_trailing": snapshot.get("ps_trailing"),
                "peg_ratio": snapshot.get("peg_ratio"),
            },
            "fundamentals": {
                "beta": snapshot.get("beta_info"),
                "roe": snapshot.get("roe"),
                "profit_margin": snapshot.get("profit_margin"),
                "operating_margin": snapshot.get("operating_margin"),
                "earnings_growth": snapshot.get("earnings_growth"),
                "revenue_growth": snapshot.get("revenue_growth"),
                "dividend_yield": snapshot.get("dividend_yield"),
            },
            "volatility": {
                "sigma_total": sigma_total,
                "sigma_down": sigma_down,
                "trading_days": trading_days,
                "start_date": start_date,
                "end_date": end_date,
            },
        })

    df = pd.DataFrame(records)
    excel_path = OUTPUT_DIR / "yahoo_metrics_extended.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="metrics", index=False)
    print(f"✓ 数据已保存: {excel_path}")

    yaml_path = OUTPUT_DIR / "yahoo_metrics_extended.yml"
    import yaml

    payload = {
        "metadata": {
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Yahoo Finance API (yfinance)",
            "companies": len(yaml_records),
            "period": "1y",
            "trading_days_assumed": TRADING_DAYS_PER_YEAR,
        },
        "companies": yaml_records,
    }
    yaml_path.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"✓ YAML数据已保存: {yaml_path}")


if __name__ == "__main__":
    main()
