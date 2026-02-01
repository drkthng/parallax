from typing import Tuple
from .loader import MarketDataLoader, MockLoader, CsvLoader, NorgateLoader
from .yahoo_loader import YFinanceLoader


class DataFactory:
    """Factory for creating data loaders based on source selection."""
    
    @staticmethod
    def get_loader(source: str) -> MarketDataLoader:
        """Get a data loader. Raises on failure."""
        if source == "Mock":
            return MockLoader()
        elif source == "CSV":
            return CsvLoader()
        elif source == "Norgate":
            # This might raise ImportError/ConnectionError, which should be caught by UI
            return NorgateLoader()
        elif source == "Yahoo":
            return YFinanceLoader()
        else:
            raise ValueError(f"Unknown data source: {source}")
    
    @staticmethod
    def get_loader_safe(source: str) -> Tuple[MarketDataLoader, str | None]:
        """
        Get a data loader with graceful fallback.
        
        Returns:
            Tuple of (loader, warning_message).
            If successful, warning_message is None.
            If fallback occurred, warning_message describes what happened.
        """
        if source == "Mock":
            return MockLoader(), None
        elif source == "CSV":
            try:
                return CsvLoader(), None
            except Exception as e:
                return MockLoader(), f"CSV loader failed ({e}), using Mock data."
        elif source == "Norgate":
            try:
                return NorgateLoader(), None
            except ImportError:
                return MockLoader(), "Norgate SDK not installed. Using Mock data instead."
            except ConnectionError as e:
                return MockLoader(), f"Norgate connection failed: {e}. Using Mock data instead."
            except Exception as e:
                return MockLoader(), f"Norgate error: {e}. Using Mock data instead."
        elif source == "Yahoo":
            try:
                # Basic import check or similar if yfinance was optional
                import yfinance
                return YFinanceLoader(), None
            except ImportError:
                return MockLoader(), "yfinance not installed. Using Mock data instead."
            except Exception as e:
                 return MockLoader(), f"Yahoo init failed: {e}. Using Mock data instead."
        else:
            return MockLoader(), f"Unknown source '{source}', using Mock data."
    
    @staticmethod
    def check_norgate_status() -> Tuple[bool, str]:
        """
        Check if Norgate Data is available and connected.
        
        Returns:
            Tuple of (is_available, status_message)
        """
        try:
            if NorgateLoader.is_available():
                return True, "Norgate Data connected and ready."
            else:
                return False, "Norgate Data Updater is not running."
        except Exception as e:
            return False, f"Norgate check failed: {e}"
