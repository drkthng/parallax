import polars as pl
import numpy as np
from typing import Protocol, Optional
from datetime import datetime, timedelta
import os

class MarketDataLoader(Protocol):
    """Abstract base class for loading market data."""
    def load_price_history(
        self, 
        symbol: str, 
        n_days: int = 100, 
        start_date: Optional[datetime] = None
    ) -> pl.DataFrame:
        """
        Loads the price history for a given symbol.
        
        Args:
            symbol (str): The ticker symbol.
            n_days (int): Number of days to look back (used if start_date is None).
            start_date (datetime, optional): Specific start date for the query.
            
        Returns:
            pl.DataFrame: A DataFrame with columns ['date', 'close'].
        """
        ...

class MockLoader(MarketDataLoader):
    """Generates synthetic random walk data for testing."""
    def load_price_history(
        self, 
        symbol: str, 
        n_days: int = 100, 
        start_date: Optional[datetime] = None
    ) -> pl.DataFrame:
        """
        Generates random walk data.
        
        Args:
            symbol (str): Ticker symbol.
            n_days (int): Number of days to generate (used if start_date is None).
            start_date (datetime, optional): If provided, calculates days from then until now.
        """
        # Use symbol-dependent seed for deterministic but diverse data
        # Hash might vary per session, so we use a stable hash if needed, but hash() is fine for mock
        seed_val = abs(hash(symbol)) % (2**32 - 1)
        rng = np.random.default_rng(seed_val)
        
        if start_date:
            actual_start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # User wants n_days TO START from start_date
            # But we must cap it at NOW to avoid future data
            end_boundary = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = actual_start_date + timedelta(days=n_days)
            
            if target_end > end_boundary:
                # Truncate n_days to reality
                delta = end_boundary - actual_start_date
                actual_n_days = max(1, delta.days)
            else:
                actual_n_days = n_days
        else:
            # Traditional lookback from NOW
            end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            actual_n_days = n_days
            actual_start_date = end_date - timedelta(days=n_days)

        dates = [actual_start_date + timedelta(days=i) for i in range(actual_n_days)]
        
        # Random walk: starting at 100, daily returns ~ N(0, 0.015)
        # Increase volatility slightly for more interesting plots
        returns = rng.normal(0, 0.015, actual_n_days)
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pl.DataFrame({
            "date": dates,
            "close": prices
        })
        
        # Ensure correct column order and types as per interface requirements
        return df.select(["date", "close"])

class CsvLoader(MarketDataLoader):
    """Loads market data from CSV files in a 'data/csv/' directory."""
    
    def __init__(self, csv_dir: str = "data/csv"):
        self.csv_dir = csv_dir
        # Ensure directory exists
        os.makedirs(self.csv_dir, exist_ok=True)

    def load_price_history(self, symbol: str, n_days: int = 100) -> pl.DataFrame:
        file_path = os.path.join(self.csv_dir, f"{symbol}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file for {symbol} not found at {file_path}. Please add it.")
            
        # Attempt to load CSV
        # We expect 'Date' and 'Close' (case insensitive)
        try:
            df = pl.read_csv(file_path)
            
            # Normalize column names to lowercase
            df = df.rename({col: col.lower() for col in df.columns})
            
            # Map common variants to 'date' and 'close'
            # e.g. "adj close" -> "close" preference? 
            # For now, let's keep it simple: looking for 'date' and 'close'
            
            if "date" not in df.columns:
                 raise ValueError(f"CSV must contain a 'Date' column. Found: {df.columns}")
            
            # Find a close column
            close_col = "close"
            if "close" not in df.columns:
                if "adj close" in df.columns:
                    df = df.rename({"adj close": "close"})
                elif "adj_close" in df.columns:
                    df = df.rename({"adj_close": "close"})
                else:
                     raise ValueError(f"CSV must contain a 'Close' or 'Adj Close' column. Found: {df.columns}")
            
            # Parse Date logic if needed (Polars usually auto-detects, but let's be safe)
            if df["date"].dtype == pl.Utf8:
                # Try common formats
                try:
                    df = df.with_columns(pl.col("date").str.strptime(pl.Date, "%Y-%m-%d"))
                except:
                     pass # Let polars handle it or error out later
            
            # Cast to datetime for consistency with standard
            df = df.with_columns(pl.col("date").cast(pl.Datetime))
            
            if start_date:
                start_limit = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_boundary = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                target_end = start_limit + timedelta(days=n_days)
                end_limit = min(target_end, end_boundary)
            else:
                end_limit = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                start_limit = end_limit - timedelta(days=n_days)
            
            df = df.filter(
                (pl.col("date") >= start_limit) & 
                (pl.col("date") <= end_limit) 
            )
            
            # Select and Sort
            return df.select(["date", "close"]).sort("date")

        except Exception as e:
            raise RuntimeError(f"Failed to load CSV for {symbol}: {str(e)}")


class NorgateLoader(MarketDataLoader):
    """Loads market data using the Norgate Data Python SDK."""
    
    def __init__(self):
        try:
            import norgatedata
            self.nd = norgatedata
        except ImportError:
            raise ImportError("Norgate Data SDK not found. Please install 'norgatedata' or use another data source.")

    def load_price_history(self, symbol: str, n_days: int = 100) -> pl.DataFrame:
        if not hasattr(self, 'nd'):
             raise ImportError("Norgate Data SDK not initialized.")
             
        # Map generic symbols to Norgate symbols if needed
        # e.g. "BTC" -> "BTCUSD" might be needed depending on the database
        # For now, we assume user passes valid Norgate symbols (e.g. '$SPX', 'AAPL')
        
        if start_date:
            actual_start_date = start_date
            end_boundary = datetime.now()
            target_end = start_date + timedelta(days=n_days)
            actual_end_date = min(target_end, end_boundary)
        else:
            actual_end_date = datetime.now()
            actual_start_date = actual_end_date - timedelta(days=n_days)
        
        try:
            # Use PriceAdjustmentType.TotalReturn (includes dividends/splits)
            timeseries = self.nd.price_timeseries(
                symbol,
                start_date=actual_start_date,
                end_date=actual_end_date,
                stock_price_adjustment_setting=self.nd.StockPriceAdjustmentType.TOTALRETURN,
                padding_setting=self.nd.PaddingType.NONE
            )
            
            if timeseries is None:
                raise ValueError(f"No data found for symbol '{symbol}' in Norgate Data.")
                
            # Convert numpy structured array to Polars DataFrame
            # Norgate struct fields: 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover', 'Unadjusted Close'
            df = pl.from_numpy(timeseries)
            
            # Rename and Cast
            # Norgate dates are usually numpy datetime64[ns]
            df = df.rename({"Date": "date", "Close": "close"})
            
            # Ensure proper datetime type
            df = df.with_columns(pl.col("date").cast(pl.Datetime))
            
            return df.select(["date", "close"])
            
        except Exception as e:
             raise RuntimeError(f"Norgate Load Error for {symbol}: {str(e)}")
