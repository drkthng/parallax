import polars as pl
import numpy as np

class CorrelationEngine:
    """
    Engine for calculating core statistics such as correlation and volatility.
    """

    @staticmethod
    def calculate_correlation(s1: pl.Series, s2: pl.Series) -> float:
        """
        Calculates the Pearson correlation coefficient between two Polars Series.
        """
        # pl.corr returns an Expr; we need to evaluate it to get a scalar
        result = pl.select(pl.corr(s1, s2)).item()
        return float(result)

    @staticmethod
    def calculate_volatility(series: pl.Series, periods: int = 252) -> float:
        """
        Calculates the annualized volatility of a Polars Series.
        Assumes the series contains returns.
        """
        # ddof=1 for sample standard deviation
        daily_std = series.std(ddof=1)
        return float(daily_std * np.sqrt(periods))
