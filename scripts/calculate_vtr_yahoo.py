#!/usr/bin/env python3
"""Calculate Value-to-Risk ratios using Yahoo Finance metrics and Scheme C risk."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict

from datetime import datetime

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_COMPANIES = PROJECT_ROOT / "config" / "companies_request.yml"
METRICS_PATH = DATA_DIR / "yahoo_metrics_extended.xlsx"
OUTPUT_EXCEL = DATA_DIR / "vtr_yahoo_results.xlsx"
OUTPUT_REPORT = PROJECT_ROOT / "results" / "vtr_yahoo_report.txt"
OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

TRADING_DAYS = 252

# Weights for expected return decomposition
# thresholds derived from docs/EXPECTED_RETURN_METHODOLOGY.md
PE_BUCKETS = [20, 35, 50]
PEG_BUCKETS = [1.0, 1.5, 2.0]
VAL_COEFF = {
    "low": 1.1,   # 低估
    "fair": 1.0,  # 合理
    "high": 0.9,  # 偏高
    "expensive": 0.7,  # 高估
}

# 质量系数映射（基于ROE与盈利质量分档）
def quality_coefficient(roe: float, profit_margin: float | None) -> float:
    if roe >= 0.15:
        return 1.1
    if roe >= 0.10:
        return 1.0
    return 0.8


def valuation_coefficient(pe: float, peg: float) -> float:
    label = "fair"
    if (pe > 0 and pe < PE_BUCKETS[0]) or (peg > 0 and peg < PEG_BUCKETS[0]):
        label = "low"
    elif (pe > 0 and pe < PE_BUCKETS[1]) or (peg > 0 and peg < PEG_BUCKETS[1]):
        label = "fair"
    elif (pe > 0 and pe < PE_BUCKETS[2]) or (peg > 0 and peg < PEG_BUCKETS[2]):
        label = "high"
    else:
        label = "expensive"
    return VAL_COEFF[label], label


def risk_coefficient(frag: float, beta: float) -> float:
    coeff = 1.0 - frag / 100.0  # frag以百分点表示
    if beta >= 1.3:
        coeff -= 0.05
    elif beta <= 0.8:
        coeff += 0.02
    return float(np.clip(coeff, 0.6, 1.05))


def safe(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, (float, int)) and not math.isnan(value):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_company_config() -> Dict[str, Dict[str, float]]:
    data = yaml.safe_load(CONFIG_COMPANIES.read_text(encoding="utf-8"))
    mapping: Dict[str, Dict[str, float]] = {}
    for item in data.get("companies", []):
        risk = item.get("risk", {})
        mapping[item["name"]] = {
            "beta": risk.get("beta"),
            "frag": risk.get("frag", 2.5),
        }
    return mapping


def compute_expected_return(row: pd.Series) -> Dict[str, float]:
    earnings_growth = safe(row.get("earnings_growth"), default=0.0)
    revenue_growth = safe(row.get("revenue_growth"), default=0.0)
    growth_candidates = [v for v in (earnings_growth, revenue_growth) if v not in (None, 0.0) and not math.isnan(v)]
    avg_growth = float(np.mean(growth_candidates)) if growth_candidates else 0.0

    base_growth = max(avg_growth, 0.05)  # 保底5%

    roe = safe(row.get("roe"), default=0.0)
    profit_margin = safe(row.get("profit_margin"), default=0.0)
    q_coeff = quality_coefficient(roe, profit_margin)

    pe_trailing = safe(row.get("pe_trailing"), default=math.nan)
    pe_forward = safe(row.get("pe_forward"), default=math.nan)
    pe_used = pe_forward if pe_forward > 0 else pe_trailing

    growth_for_peg = max(avg_growth, 0.01)
    peg = pe_used / (growth_for_peg * 100) if pe_used and pe_used > 0 else math.nan
    val_coeff, val_label = valuation_coefficient(pe_used, peg)

    # 风险系数在 compute_loss_risk 再处理，这里只返回估值内容
    expected_return = base_growth * q_coeff * val_coeff
    expected_return = float(np.clip(expected_return, -0.5, 0.8))

    return {
        "expected_return": expected_return,
        "avg_growth": avg_growth,
        "quality_coeff": q_coeff,
        "valuation_coeff": val_coeff,
        "valuation_label": val_label,
        "peg": peg,
        "pe_used": pe_used,
    }


def compute_loss_risk(row: pd.Series, config_risk: Dict[str, float]) -> Dict[str, float]:
    sigma_down = safe(row.get("sigma_down"), default=0.0)
    sigma_total = safe(row.get("sigma_total"), default=0.0)
    beta_yahoo = row.get("beta_info")

    beta_config = config_risk.get("beta")
    beta_used = beta_yahoo if beta_yahoo is not None else beta_config
    if beta_used is None or math.isnan(beta_used):
        beta_used = 1.0
    beta_used = abs(beta_used)

    frag = config_risk.get("frag", 2.5)
    risk_coeff = risk_coefficient(frag, beta_used)

    downside_component = 0.6 * sigma_down
    beta_component = 0.3 * (beta_used * sigma_total)
    frag_component = 0.1 * (frag / 100.0)
    loss_risk = downside_component + beta_component + frag_component

    return {
        "beta_used": beta_used,
        "frag": frag,
        "risk_coeff": risk_coeff,
        "downside_component": downside_component,
        "beta_component": beta_component,
        "frag_component": frag_component,
        "loss_risk": loss_risk,
    }


def main() -> None:
    config_risk_map = load_company_config()
    metrics_df = pd.read_excel(METRICS_PATH)

    results = []
    for _, row in metrics_df.iterrows():
        name = row["company_name"]
        risk_config = config_risk_map.get(name, {})

        expected = compute_expected_return(row)
        risk = compute_loss_risk(row, risk_config)
        loss_risk = risk["loss_risk"]
        expected_return_raw = expected["expected_return"]
        expected_return = expected_return_raw * risk["risk_coeff"]
        vtr = expected_return / loss_risk if loss_risk > 0 else float("inf")

        record = {
            "公司": name,
            "Ticker": row["ticker"],
            "市场": row["market"],
            "当前价": row["current_price"],
            "PE_TTM": row["pe_trailing"],
            "PE_Forward": row["pe_forward"],
            "PB": row["pb"],
            "ROE": row["roe"],
            "基础增长": expected["avg_growth"],
            "质量系数": expected["quality_coeff"],
            "估值系数": expected["valuation_coeff"],
            "风险系数": risk["risk_coeff"],
            "期望收益(调整前)": expected_return_raw,
            "期望收益": expected_return,
            "σ_total": row["sigma_total"],
            "σ_down": row["sigma_down"],
            "Beta": risk["beta_used"],
            "Frag%": risk["frag"],
            "风险_下行项": risk["downside_component"],
            "风险_β项": risk["beta_component"],
            "风险_脆弱项": risk["frag_component"],
            "损失风险": loss_risk,
            "值博率": vtr,
            "估值分类": expected["valuation_label"],
            "PEG": expected["peg"],
            "PE使用值": expected["pe_used"],
        }
        results.append(record)

    result_df = pd.DataFrame(results)
    result_df.sort_values(by="值博率", ascending=False, inplace=True)

    with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="VTR", index=False)
    print(f"✓ 结果已写入 {OUTPUT_EXCEL}")

    lines = []
    lines.append("================================================================")
    lines.append("基于Yahoo Finance数据的值博率报告")
    lines.append("================================================================")
    lines.append(f"数据来源: {METRICS_PATH.name}, 抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("期望收益 = 平均增长 × 质量系数 × 估值系数 × 风险系数")
    lines.append("损失风险 = 0.6×σ_down + 0.3×(β×σ_total) + 0.1×Frag")
    lines.append("")

    top_rows = result_df.head(10)
    lines.append("Top10 值博率")
    lines.append(top_rows[["公司", "值博率", "期望收益", "损失风险"]].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    lines.append("")

    lines.append("详细拆解")
    for _, row in result_df.iterrows():
        lines.append("----------------------------------------------------------------")
        lines.append(f"公司：{row['公司']} ({row['Ticker']})")
        lines.append(f"  期望收益 = {row['期望收益']:.4f} (基础增长 {row['基础增长']:.4f} × 质量 {row['质量系数']:.2f} × 估值 {row['估值系数']:.2f} × 风险 {row['风险系数']:.2f})")
        lines.append(f"    · ROE {row['ROE']:.4f}，估值分类 {row['估值分类']} (PEG {row['PEG'] if row['PEG'] is not None else 'NA'})")
        lines.append(f"  损失风险 = {row['损失风险']:.4f} (下行 {row['风险_下行项']:.4f} + β {row['风险_β项']:.4f} + 脆弱 {row['风险_脆弱项']:.4f})")
        lines.append(f"    · 采用β = {row['Beta']:.3f}，Frag = {row['Frag%']:.2f}%")
        lines.append(f"    · σ_down = {row['σ_down']:.4f}, σ_total = {row['σ_total']:.4f}")
        lines.append(f"  值博率 = {row['值博率']:.4f}")
    lines.append("----------------------------------------------------------------")

    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ 文本报告已写入 {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
