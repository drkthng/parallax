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
        Generates deterministic random walk data anchored to dates.
        """
        # Determine the constant epoch for our mock history (e.g., 5 years ago)
        anchor_date = (datetime.now() - timedelta(days=365*5)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_boundary = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if start_date:
            actual_start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Duration is n_days but capped at now
            target_end = actual_start_date + timedelta(days=n_days)
            if target_end > end_boundary:
                target_end = end_boundary
        else:
            # Traditional lookback: n_days ending today
            actual_start_date = end_boundary - timedelta(days=n_days)
            target_end = end_boundary

        # To make it feel like one continuous history:
        # We calculate the returns for every day from anchor_date to target_end.
        # BUT to be efficient, we only need to seed for the dates we actually want.
        # However, a random walk P_t = P_0 * exp(sum(r_i)) needs all preceding returns.
        
        total_days_since_anchor = (target_end - anchor_date).days
        start_offset = (actual_start_date - anchor_date).days
        
        # Base seed for the symbol
        symbol_seed = abs(hash(symbol)) % (2**31)
        
        # Generate returns from anchor to end
        # (For large datasets we'd use a different approach, but for 100-3650 days this is fine)
        full_rng = np.random.default_rng(symbol_seed)
        all_returns = full_rng.normal(0, 0.015, max(1, total_days_since_anchor))
        
        # Calculate cumulative price from anchor (Base 100)
        prices = 100 * np.exp(np.cumsum(all_returns))
        
        # Slice the requested window
        requested_count = (target_end - actual_start_date).days
        if requested_count <= 0:
            # Fallback for edge cases
            return pl.DataFrame({"date": [actual_start_date], "close": [100.0]})
            
        view_prices = prices[start_offset : start_offset + requested_count]
        view_dates = [actual_start_date + timedelta(days=i) for i in range(len(view_prices))]
        
        return pl.DataFrame({
            "date": view_dates,
            "close": view_prices
        })

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
    
    _norgate_available: bool = False
    
    def __init__(self):
        try:
            import norgatedata
            self.nd = norgatedata
            
            # Check if the Norgate Data Updater is running and database is accessible
            if not self.nd.status():
                raise ConnectionError(
                    "Norgate Data Updater is not running or database is inaccessible. "
                    "Please start the Norgate Data Updater application."
                )
            NorgateLoader._norgate_available = True
            
        except ImportError:
            NorgateLoader._norgate_available = False
            raise ImportError("Norgate Data SDK not found. Please install 'norgatedata' or use another data source.")
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Norgate Data SDK is available and connected."""
        try:
            import norgatedata
            return norgatedata.status()
        except ImportError:
            return False
        except Exception:
            return False

    def load_price_history(
        self, 
        symbol: str, 
        n_days: int = 100, 
        start_date: Optional[datetime] = None
    ) -> pl.DataFrame:
        if not hasattr(self, 'nd'):
            raise ImportError("Norgate Data SDK not initialized.")
        
        # Symbol mapping for common aliases
        symbol_map = {
            "Index": "$SPX",  # S&P 500 Index
            "BTC": "BTC-USD",  # Bitcoin
            "SPY": "SPY",
            "NDX": "$NDX",
            "GLD": "GLD",
        }
        norgate_symbol = symbol_map.get(symbol, symbol)
        
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
                norgate_symbol,
                start_date=actual_start_date,
                end_date=actual_end_date,
                stock_price_adjustment_setting=self.nd.StockPriceAdjustmentType.TOTALRETURN,
                padding_setting=self.nd.PaddingType.NONE
            )
            
            if timeseries is None or len(timeseries) == 0:
                raise ValueError(f"No data found for symbol '{symbol}' (Norgate: '{norgate_symbol}'). Check if symbol exists in your Norgate subscription.")
            
            # Convert numpy structured array to Polars DataFrame
            df = pl.from_numpy(timeseries)
            
            # Rename columns to our standard format
            df = df.rename({"Date": "date", "Close": "close"})
            
            # Ensure proper datetime type
            df = df.with_columns(pl.col("date").cast(pl.Datetime))
            
            return df.select(["date", "close"])
            
        except ValueError:
            # Norgate SDK raises empty ValueError when symbol is not found
            raise ValueError(f"Symbol '{norgate_symbol}' not found in Norgate Data. Please check your subscription and symbol spelling.")
        except Exception as e:
            msg = str(e)
            if not msg:
                msg = f"{type(e).__name__} (No error message provided by SDK)"
            raise RuntimeError(f"Norgate Load Error for {symbol} ({norgate_symbol}): {msg}")
