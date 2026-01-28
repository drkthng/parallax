import polars as pl
import pytest
import numpy as np
from src.core.stats import CorrelationEngine

def test_correlation_identity():
    # Identity correlation (1.0)
    data = pl.Series("s1", [1.0, 2.0, 3.0, 4.0, 5.0])
    corr = CorrelationEngine.calculate_correlation(data, data)
    assert float(corr) == pytest.approx(1.0)

def test_correlation_inverse():
    # Inverse correlation (-1.0)
    s1 = pl.Series("s1", [1.0, 2.0, 3.0, 4.0, 5.0])
    s2 = pl.Series("s2", [5.0, 4.0, 3.0, 2.0, 1.0])
    corr = CorrelationEngine.calculate_correlation(s1, s2)
    assert float(corr) == pytest.approx(-1.0)

def test_calculate_volatility():
    # Known volatility calculation
    # Using a simple set of log returns
    # prices = [100, 101, 102, 101, 100]
    # returns = [0.01, 0.0099, -0.0098, -0.0099] approximately
    data = pl.Series("returns", [0.01, 0.02, -0.01, 0.03, -0.02])
    # Std dev of [0.01, 0.02, -0.01, 0.03, -0.02]
    expected_std = np.std([0.01, 0.02, -0.01, 0.03, -0.02], ddof=1)
    expected_vol = expected_std * np.sqrt(252)
    
    vol = CorrelationEngine.calculate_volatility(data, periods=252)
    assert vol == pytest.approx(expected_vol)
