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
        if daily_std is None:
            return 0.0
        return float(daily_std * np.sqrt(periods))

    @staticmethod
    def calculate_tracking_error(s1_ret: pl.Series, s2_ret: pl.Series, periods: int = 252) -> float:
        """
        Calculates the annualized Tracking Error (volatility of return differences).
        TE = Stdev(Rp - Rb) * sqrt(T)
        """
        diff = s2_ret - s1_ret 
        # Note: Direction doesn't matter for Stdev, but conceptually (Proxy - Target)
        te = diff.std(ddof=1)
        if te is None:
            return 0.0
        return float(te * np.sqrt(periods))

    @staticmethod
    def calculate_period_tracking_error(s1_ret: pl.Series, s2_ret: pl.Series) -> float:
        """
        Calculates the Tracking Error over the specific period of the input series.
        TE_period = Stdev(Rp - Rb) * sqrt(N_samples)
        This represents the expected deviation over the realized timeframe.
        """
        return CorrelationEngine.calculate_tracking_error(s1_ret, s2_ret, periods=len(s1_ret))
