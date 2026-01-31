import polars as pl
import numpy as np
from typing import Protocol
from datetime import datetime, timedelta

class MarketDataLoader(Protocol):
    """Abstract base class for loading market data."""
    def load_price_history(self, symbol: str, n_days: int = 100) -> pl.DataFrame:
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
    def load_price_history(self, symbol: str, n_days: int = 100) -> pl.DataFrame:
        """
        Generates random walk data for a specified number of days.
        
        Args:
            symbol (str): Ticker symbol.
            n_days (int): Number of days to generate.
            
        Returns:
            pl.DataFrame: Synthetic price data.
        """
        # Use symbol-dependent seed for deterministic but diverse data
        # Hash might vary per session, so we use a stable hash if needed, but hash() is fine for mock
        seed_val = abs(hash(symbol)) % (2**32 - 1)
        rng = np.random.default_rng(seed_val)
        
        # Realism: Data ends NOW.
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days)
        dates = [start_date + timedelta(days=i) for i in range(n_days)]
        
        # Random walk: starting at 100, daily returns ~ N(0, 0.015)
        # Increase volatility slightly for more interesting plots
        returns = rng.normal(0, 0.015, n_days)
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pl.DataFrame({
            "date": dates,
            "close": prices
        })
        
        # Ensure correct column order and types as per interface requirements
        return df.select(["date", "close"])
