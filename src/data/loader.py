import polars as pl
import numpy as np
from typing import Protocol
from datetime import datetime, timedelta

class MarketDataLoader(Protocol):
    """Abstract base class for loading market data."""
    def load_price_history(self, symbol: str) -> pl.DataFrame:
        """
        Loads the price history for a given symbol.
        
        Args:
            symbol (str): The ticker symbol (e.g., 'BTC', 'AAPL').
            
        Returns:
            pl.DataFrame: A DataFrame with columns ['date', 'close'].
        """
        ...

class MockLoader(MarketDataLoader):
    """Generates synthetic random walk data for testing."""
    def load_price_history(self, symbol: str) -> pl.DataFrame:
        """
        Generates 100 days of random walk data.
        
        Args:
            symbol (str): Ticker symbol.
            
        Returns:
            pl.DataFrame: Synthetic price data.
        """
        np.random.seed(42)  # Deterministic for testing
        n_days = 100
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(n_days)]
        
        # Random walk: starting at 100, daily returns ~ N(0, 0.01)
        returns = np.random.normal(0, 0.01, n_days)
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pl.DataFrame({
            "date": dates,
            "close": prices
        })
        
        # Ensure correct column order and types as per interface requirements
        return df.select(["date", "close"])
