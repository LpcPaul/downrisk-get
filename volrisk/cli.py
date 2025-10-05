"""
CLI接口
使用 Typer 实现命令行接口
"""

from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
import typer

from .data import DataFetcher
from .sector import SectorAnalyzer, SectorsConfig
from .ranker import Ranker, CompaniesConfig

app = typer.Typer(
    name="volrisk",
    help="值博率分析工具 - 基于下行波动率的损失风险评估"
)


@app.command()
def fetch(
    ticker: str = typer.Argument(..., help="股票代码，如 512480.SS"),
    period: str = typer.Option("1y", help="时间周期（1y, 2y等）"),
    start: Optional[str] = typer.Option(None, help="开始日期（YYYY-MM-DD），优先于period"),
    end: Optional[str] = typer.Option(None, help="结束日期（YYYY-MM-DD）"),
    interval: str = typer.Option("1d", help="数据间隔（1d=日线）"),
    force: bool = typer.Option(False, "--force", help="强制刷新（忽略缓存）"),
):
    """
    获取单个股票/ETF的数据
    """
    fetcher = DataFetcher()

    print(f"正在获取 {ticker} 的数据...")
    data = fetcher.fetch(
        ticker=ticker,
        start=start,
        end=end,
        period=period,
        interval=interval,
        force_refresh=force
    )

    if data is not None:
        print(f"\n✓ 成功获取 {len(data)} 个交易日的数据")
        print(f"日期范围: {data.index[0].date()} 至 {data.index[-1].date()}")
        print(f"\n最近5天数据:")
        print(data.tail())
    else:
        print(f"✗ 获取数据失败")
        raise typer.Exit(code=1)


@app.command()
def calc_sector(
    config: str = typer.Option("config/sectors.yml", help="行业配置文件路径"),
    start: Optional[str] = typer.Option(None, help="开始日期（YYYY-MM-DD）"),
    end: Optional[str] = typer.Option(None, help="结束日期（YYYY-MM-DD）"),
    period: str = typer.Option("1y", help="时间周期"),
    mar: float = typer.Option(0.0, help="最低可接受收益（MAR）"),
    min_days: int = typer.Option(150, help="最少交易日数"),
):
    """
    计算行业ETF的风险指标
    """
    config_path = Path(config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        raise typer.Exit(code=1)

    # 加载配置
    print(f"加载配置: {config_path}")
    sectors_config = SectorsConfig.from_yaml(str(config_path))

    # 创建分析器
    analyzer = SectorAnalyzer()

    # 计算所有行业指标
    print(f"\n{'='*80}")
    print("开始计算行业指标...")
    print(f"{'='*80}")

    results = analyzer.calculate_all_sectors(
        config=sectors_config,
        start=start,
        end=end,
        period=period,
        mar=mar,
        min_days=min_days
    )

    # 输出摘要
    print(f"\n{'='*80}")
    print(f"行业指标汇总 (共 {len(results)} 个行业)")
    print(f"{'='*80}")

    for sector_name, metrics in results.items():
        print(f"\n{sector_name}:")
        print(f"  ETF: {', '.join(metrics.tickers)}")
        print(f"  权重: {', '.join([f'{w:.2f}' for w in metrics.weights])}")
        print(f"  下行波动率: {metrics.sigma_down:.4f} ({metrics.sigma_down*100:.2f}%)")
        print(f"  总波动率:   {metrics.sigma_total:.4f} ({metrics.sigma_total*100:.2f}%)")
        print(f"  最大回撤:   {abs(metrics.mdd):.4f} ({abs(metrics.mdd)*100:.2f}%)")
        print(f"  样本天数:   {metrics.sample_days} 天")
        print(f"  日期范围:   {metrics.start_date} 至 {metrics.end_date}")


@app.command()
def rank(
    companies: str = typer.Option("config/companies.yml", help="公司配置文件路径"),
    sectors: str = typer.Option("config/sectors.yml", help="行业配置文件路径"),
    output: str = typer.Option("output.xlsx", help="输出文件路径"),
    format: str = typer.Option("xlsx", help="输出格式（xlsx, csv, json）"),
    start: Optional[str] = typer.Option(None, help="开始日期（YYYY-MM-DD）"),
    end: Optional[str] = typer.Option(None, help="结束日期（YYYY-MM-DD）"),
    period: str = typer.Option("1y", help="时间周期"),
    mar: float = typer.Option(0.0, help="最低可接受收益（MAR）"),
):
    """
    计算公司值博率并排名
    """
    # 验证文件
    companies_path = Path(companies)
    sectors_path = Path(sectors)

    if not companies_path.exists():
        print(f"错误: 公司配置文件不存在: {companies_path}")
        raise typer.Exit(code=1)

    if not sectors_path.exists():
        print(f"错误: 行业配置文件不存在: {sectors_path}")
        raise typer.Exit(code=1)

    # 加载配置
    print(f"加载配置...")
    print(f"  - 行业配置: {sectors_path}")
    print(f"  - 公司配置: {companies_path}")

    sectors_config = SectorsConfig.from_yaml(str(sectors_path))
    companies_config = CompaniesConfig.from_yaml(str(companies_path))

    # 步骤1: 计算行业指标
    print(f"\n{'='*80}")
    print("步骤 1/2: 计算行业指标")
    print(f"{'='*80}")

    analyzer = SectorAnalyzer()
    sector_metrics = analyzer.calculate_all_sectors(
        config=sectors_config,
        start=start,
        end=end,
        period=period,
        mar=mar
    )

    if not sector_metrics:
        print("错误: 没有成功计算任何行业指标")
        raise typer.Exit(code=1)

    # 步骤2: 计算公司值博率
    print(f"\n{'='*80}")
    print("步骤 2/2: 计算公司值博率")
    print(f"{'='*80}")

    ranker = Ranker(sector_analyzer=analyzer)
    results = ranker.analyze_companies(
        companies_config=companies_config,
        sector_metrics=sector_metrics
    )

    if not results:
        print("错误: 没有成功分析任何公司")
        raise typer.Exit(code=1)

    # 步骤3: 排序并导出
    print(f"\n{'='*80}")
    print("导出结果")
    print(f"{'='*80}")

    ranker.rank_and_export(
        results=results,
        output_path=output,
        format=format
    )


@app.command()
def clear_cache(
    ticker: Optional[str] = typer.Option(None, help="只清除指定ticker的缓存")
):
    """
    清除缓存数据
    """
    fetcher = DataFetcher()

    if ticker:
        print(f"清除 {ticker} 的缓存...")
    else:
        print("清除所有缓存...")

    fetcher.clear_cache(ticker)


@app.command()
def version():
    """
    显示版本信息
    """
    from . import __version__
    print(f"volrisk version {__version__}")


def main():
    """主入口"""
    app()


if __name__ == "__main__":
    main()
