import yfinance as yf
import pandas as pd
import polars as pl
try:
    import pyarrow
except ImportError:
    pyarrow = None

from typing import Optional
from datetime import datetime, timedelta
from .loader import MarketDataLoader

class YFinanceLoader(MarketDataLoader):
    """Loads market data using Yahoo Finance (yfinance)."""

    def load_price_history(
        self, 
        symbol: str, 
        n_days: int = 100, 
        start_date: Optional[datetime] = None
    ) -> pl.DataFrame:
        
        # Determine timeframe
        if start_date:
            actual_start_date = start_date
            end_boundary = datetime.now()
            target_end = start_date + timedelta(days=n_days)
            actual_end_date = min(target_end, end_boundary)
        else:
            actual_end_date = datetime.now()
            actual_start_date = actual_end_date - timedelta(days=n_days)
            
        # yfinance expects strings, YYYY-MM-DD
        start_str = actual_start_date.strftime("%Y-%m-%d")
        end_str = (actual_end_date + timedelta(days=1)).strftime("%Y-%m-%d") # +1 to include end date

        try:
            # Download data
            ticker = yf.Ticker(symbol)
            df_pandas = ticker.history(start=start_str, end=end_str, auto_adjust=True)
            
            if df_pandas.empty:
                raise ValueError(f"No data found for symbol '{symbol}' in Yahoo Finance.")
            
            # Reset index to get Date column
            df_pandas = df_pandas.reset_index()
            
            # Check for pyarrow and warn/fail explicity
            if pyarrow is None:
                raise ImportError("pyarrow is not installed. It is required for Yahoo Finance data loading. Please install it with: pip install pyarrow")

            # Convert to Polars
            df = pl.from_pandas(df_pandas)
            
            # Normalize columns
            # Yahoo commonly returns: Date, Open, High, Low, Close, Volume, Dividends, Stock Splits
            df = df.rename({col: col.lower() for col in df.columns})
            
            # Ensure proper datetime type
            # yfinance often returns datetime with timezone. We might want to warn or strip tz.
            # Polars conversion usually handles it, but let's be explicit about standardizing.
            if df["date"].dtype == pl.Datetime:
                 # Ensure no timezone for consistency with other loaders (or all loaders should be tz-aware?)
                 # For simplicty in this project, we might cast to naive or keep as is.
                 # Let's cast to Datetime("us") which is standard.
                 pass 
            
            df = df.with_columns(pl.col("date").cast(pl.Datetime))

            return df.select(["date", "close"]).sort("date")

        except Exception as e:
            raise RuntimeError(f"Yahoo Load Error for {symbol}: {str(e)}")
