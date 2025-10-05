"""
β回归计算模块
使用OLS回归或鲁棒回归计算个股相对行业的敏感度系数
"""

import numpy as np
import pandas as pd
from typing import Optional, Literal
import warnings


def beta_ols(
    stock_returns: pd.Series,
    sector_returns: pd.Series,
    min_overlap: int = 50
) -> tuple[float, dict]:
    """
    使用普通最小二乘法(OLS)回归计算β

    回归模型: r_stock = α + β * r_sector + ε

    Args:
        stock_returns: 个股收益率序列
        sector_returns: 行业收益率序列
        min_overlap: 最少重叠天数，默认50天

    Returns:
        (beta, regression_info)
        regression_info包含: alpha, beta, r_squared, std_err, n_obs
    """
    # 对齐时间序列（取交集）
    aligned = pd.DataFrame({
        'stock': stock_returns,
        'sector': sector_returns
    }).dropna()

    if len(aligned) < min_overlap:
        raise ValueError(
            f"重叠样本不足：需要至少{min_overlap}天，实际{len(aligned)}天"
        )

    X = aligned['sector'].values
    y = aligned['stock'].values

    # OLS回归
    # β = Cov(stock, sector) / Var(sector)
    # α = mean(stock) - β * mean(sector)

    cov_matrix = np.cov(X, y)
    var_sector = cov_matrix[0, 0]
    cov_stock_sector = cov_matrix[0, 1]

    if var_sector == 0:
        raise ValueError("行业收益方差为0，无法计算β")

    beta = cov_stock_sector / var_sector
    alpha = y.mean() - beta * X.mean()

    # 计算R²和标准误
    y_pred = alpha + beta * X
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)

    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # β的标准误
    n = len(aligned)
    mse = ss_res / (n - 2) if n > 2 else np.nan
    std_err = np.sqrt(mse / (var_sector * (n - 1))) if n > 2 else np.nan

    regression_info = {
        'alpha': alpha,
        'beta': beta,
        'r_squared': r_squared,
        'std_err': std_err,
        'n_obs': n,
        'method': 'OLS'
    }

    return beta, regression_info


def beta_huber(
    stock_returns: pd.Series,
    sector_returns: pd.Series,
    min_overlap: int = 50
) -> tuple[float, dict]:
    """
    使用Huber鲁棒回归计算β（对异常值更稳健）

    需要安装 scikit-learn

    Args:
        stock_returns: 个股收益率序列
        sector_returns: 行业收益率序列
        min_overlap: 最少重叠天数

    Returns:
        (beta, regression_info)
    """
    try:
        from sklearn.linear_model import HuberRegressor
    except ImportError:
        warnings.warn("scikit-learn未安装，回退到OLS方法")
        return beta_ols(stock_returns, sector_returns, min_overlap)

    # 对齐时间序列
    aligned = pd.DataFrame({
        'stock': stock_returns,
        'sector': sector_returns
    }).dropna()

    if len(aligned) < min_overlap:
        raise ValueError(
            f"重叠样本不足：需要至少{min_overlap}天，实际{len(aligned)}天"
        )

    X = aligned['sector'].values.reshape(-1, 1)
    y = aligned['stock'].values

    # Huber回归
    huber = HuberRegressor(epsilon=1.35, max_iter=100)
    huber.fit(X, y)

    beta = huber.coef_[0]
    alpha = huber.intercept_

    # 计算R²
    y_pred = huber.predict(X)
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    regression_info = {
        'alpha': alpha,
        'beta': beta,
        'r_squared': r_squared,
        'n_obs': len(aligned),
        'method': 'Huber'
    }

    return beta, regression_info


def calculate_beta(
    stock_returns: pd.Series,
    sector_returns: pd.Series,
    method: Literal['OLS', 'Huber'] = 'OLS',
    min_overlap: int = 50,
    fallback_beta: Optional[float] = None
) -> tuple[float, dict]:
    """
    计算个股相对行业的β系数

    Args:
        stock_returns: 个股收益率序列
        sector_returns: 行业收益率序列
        method: 回归方法，'OLS' 或 'Huber'
        min_overlap: 最少重叠天数
        fallback_beta: 回归失败时的备用β值

    Returns:
        (beta, regression_info)

    Raises:
        ValueError: 如果数据不足且未提供fallback_beta
    """
    try:
        if method == 'OLS':
            return beta_ols(stock_returns, sector_returns, min_overlap)
        elif method == 'Huber':
            return beta_huber(stock_returns, sector_returns, min_overlap)
        else:
            raise ValueError(f"不支持的回归方法: {method}")

    except Exception as e:
        if fallback_beta is not None:
            warnings.warn(f"β回归失败({e})，使用备用β={fallback_beta}")
            return fallback_beta, {
                'alpha': np.nan,
                'beta': fallback_beta,
                'r_squared': np.nan,
                'n_obs': 0,
                'method': 'Fallback',
                'error': str(e)
            }
        else:
            raise ValueError(f"β回归失败且未提供备用β: {e}")


class BetaCalculator:
    """β计算器，支持批量计算和缓存"""

    def __init__(
        self,
        method: Literal['OLS', 'Huber'] = 'OLS',
        min_overlap: int = 50
    ):
        """
        初始化β计算器

        Args:
            method: 回归方法
            min_overlap: 最少重叠天数
        """
        self.method = method
        self.min_overlap = min_overlap
        self._cache = {}

    def calculate(
        self,
        stock_returns: pd.Series,
        sector_returns: pd.Series,
        fallback_beta: Optional[float] = None,
        use_cache: bool = True
    ) -> tuple[float, dict]:
        """
        计算β系数

        Args:
            stock_returns: 个股收益率序列
            sector_returns: 行业收益率序列
            fallback_beta: 备用β值
            use_cache: 是否使用缓存

        Returns:
            (beta, regression_info)
        """
        # 生成缓存键
        cache_key = f"{id(stock_returns)}_{id(sector_returns)}_{self.method}"

        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        result = calculate_beta(
            stock_returns=stock_returns,
            sector_returns=sector_returns,
            method=self.method,
            min_overlap=self.min_overlap,
            fallback_beta=fallback_beta
        )

        if use_cache:
            self._cache[cache_key] = result

        return result

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
