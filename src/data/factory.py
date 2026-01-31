from .loader import MarketDataLoader, MockLoader, CsvLoader, NorgateLoader

class DataFactory:
    """Factory for creating data loaders based on source selection."""
    
    @staticmethod
    def get_loader(source: str) -> MarketDataLoader:
        if source == "Mock":
            return MockLoader()
        elif source == "CSV":
            return CsvLoader()
        elif source == "Norgate":
            # This might raise ImportError, which should be caught by UI
            return NorgateLoader()
        else:
            raise ValueError(f"Unknown data source: {source}")
