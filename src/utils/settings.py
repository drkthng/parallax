"""Settings persistence manager for Parallax."""

import json
import os
from typing import Any, Optional
from pathlib import Path


class SettingsManager:
    """
    Manages persistent settings storage using JSON.
    Settings are stored in data/settings.json relative to project root.
    """
    
    # Default settings values
    DEFAULTS = {
        "asset_a": "Index",
        "proxy_assets": ["MSTR"],
        "proxy_weights": {},
        "show_tickers": [],
        "lookback_window": 100,
        "max_lookback_range": 365,
        "data_source": "Mock",
        "source_overrides": {},  # {symbol: source_name} e.g. {"BTC-USD": "Yahoo"}
        "persist_settings": False,  # Disabled by default
    }
    
    def __init__(self, settings_path: Optional[str] = None):
        """
        Initialize the settings manager.
        
        Args:
            settings_path: Custom path for settings file. 
                          Defaults to data/settings.json in project root.
        """
        if settings_path:
            self.settings_path = Path(settings_path)
        else:
            # Find project root (where data/ folder lives)
            project_root = Path(__file__).parent.parent.parent
            self.settings_path = project_root / "data" / "settings.json"
        
        # Ensure directory exists
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._cache: dict = {}
    
    def load(self) -> dict:
        """
        Load settings from disk.
        
        Returns:
            Dict of settings, merged with defaults for any missing keys.
        """
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                # Merge with defaults
                self._cache = {**self.DEFAULTS, **saved}
            except (json.JSONDecodeError, IOError):
                self._cache = self.DEFAULTS.copy()
        else:
            self._cache = self.DEFAULTS.copy()
        
        return self._cache
    
    def save(self, settings: dict) -> None:
        """
        Save settings to disk.
        
        Args:
            settings: Dict of settings to save.
        """
        self._cache = settings
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, default=str)
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a single setting value."""
        if not self._cache:
            self.load()
        return self._cache.get(key, default or self.DEFAULTS.get(key))
    
    def set(self, key: str, value: Any) -> None:
        """Set a single setting and save if persistence is enabled."""
        if not self._cache:
            self.load()
        self._cache[key] = value
        
        # Only auto-save if persistence is enabled
        if self._cache.get("persist_settings", False):
            self.save(self._cache)
    
    def clear(self) -> None:
        """Clear all saved settings (delete the file)."""
        self._cache = self.DEFAULTS.copy()
        if self.settings_path.exists():
            try:
                os.remove(self.settings_path)
            except IOError:
                pass
    
    def is_persistence_enabled(self) -> bool:
        """Check if persistence is currently enabled."""
        if not self._cache:
            self.load()
        return self._cache.get("persist_settings", False)


# Global singleton instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get or create the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
