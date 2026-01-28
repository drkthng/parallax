import pytest
import polars as pl
from src.data.loader import MockLoader

def test_mock_loader_btc():
    """Test that MockLoader returns a valid Polars DataFrame for BTC."""
    loader = MockLoader()
    symbol = "BTC"
    df = loader.load_price_history(symbol)
    
    # Check type
    assert isinstance(df, pl.DataFrame)
    
    # Check schema
    assert df.columns == ["date", "close"]
    assert df.schema["date"] in [pl.Date, pl.Datetime]
    assert df.schema["close"] in [pl.Float32, pl.Float64]
    
    # Check content
    assert len(df) > 0
    assert df["close"].null_count() == 0
    
    # Verify it's not all zeros (random walk should have some variance)
    assert df["close"].std() > 0

def test_mock_loader_consistency():
    """Test that MockLoader is deterministic (due to fixed seed)."""
    loader = MockLoader()
    df1 = loader.load_price_history("BTC")
    df2 = loader.load_price_history("BTC")
    
    assert df1.equals(df2)
