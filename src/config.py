"""
Configuration management for Aurora Skywatch Archive.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the Gilman Skywatch Archive."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to the configuration file. If None, uses default config.yml
        """
        self.config_file = config_file or Path(__file__).parent.parent / "config.yml"
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        try:
            # Load YAML configuration
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.warning(f"Configuration file {self.config_file} not found, using defaults")
                self._config = self._get_default_config()

            # Override with environment variables
            self._apply_env_overrides()

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "site": {
                "name": "Aurora Skywatch Archive",
                "subtitle": "Northern Lights & Sky Timelapse Observatory",
                "description": "Static HTML website generator for Aurora timelapse archive",
                "author": "Aurora Skywatch",
                "email": "admin@aurora-skywatch.local"
            },
            "location": {
                "name": "Observatory Location",
                "latitude": 45.17,
                "longitude": -90.82,
                "timezone": "America/Chicago"
            },
            "api_keys": {
                "openweathermap": None
            },
            "data_sources": {
                "noaa": {
                    "current_kp_url": "https://services.swpc.noaa.gov/text/daily-geomagnetic-indices.txt",
                    "forecast_url": "https://services.swpc.noaa.gov/text/3-day-forecast.txt",
                    "solar_wind_url": "https://services.swpc.noaa.gov/json/solar_wind_ace.json"
                },
                "clearsky": {
                    "base_url": "https://www.cleardarksky.com/c/",
                    "station": "LtBlrTsWIcsk.gif",
                    "title": "Clear Sky Chart for Observatory Location"
                }
            },
            "display": {
                "forecast_days": 3,
                "time_format": "%Y-%m-%d %I:%M %p",
                "date_format": "%B %d, %Y",
                "show_atmospheric_weather": True,
                "show_clearsky_chart": True
            },
            "advanced": {
                "request_timeout": 15,
                "user_agent": "Aurora Skywatch Archive (Educational/Non-commercial; admin@aurora-skywatch.local)",
                "debug": False
            }
        }

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Map environment variables to config paths (generic naming)
        env_mappings = {
            "AURORA_SITE_NAME": ["site", "name"],
            "AURORA_SITE_SUBTITLE": ["site", "subtitle"],
            "AURORA_SITE_DESCRIPTION": ["site", "description"],
            "AURORA_SITE_AUTHOR": ["site", "author"],
            "AURORA_SITE_EMAIL": ["site", "email"],

            "AURORA_LOCATION_NAME": ["location", "name"],
            "AURORA_LOCATION_LATITUDE": ["location", "latitude"],
            "AURORA_LOCATION_LONGITUDE": ["location", "longitude"],
            "AURORA_LOCATION_TIMEZONE": ["location", "timezone"],

            "AURORA_API_KEYS_OPENWEATHERMAP": ["api_keys", "openweathermap"],

            "AURORA_DISPLAY_FORECAST_DAYS": ["display", "forecast_days"],
            "AURORA_DISPLAY_SHOW_ATMOSPHERIC_WEATHER": ["display", "show_atmospheric_weather"],
            "AURORA_DISPLAY_SHOW_CLEARSKY_CHART": ["display", "show_clearsky_chart"],

            "AURORA_ADVANCED_REQUEST_TIMEOUT": ["advanced", "request_timeout"],
            "AURORA_ADVANCED_DEBUG": ["advanced", "debug"],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_path, self._convert_env_value(env_value))
                logger.debug(f"Environment override: {env_var} -> {'.'.join(config_path)}")

    def _set_nested_value(self, path: list, value: Any) -> None:
        """Set a nested value in the configuration dictionary."""
        current = self._config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Try boolean conversion
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False

        # Try numeric conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the value (e.g., 'site.name')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self._config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def get_site_name(self) -> str:
        """Get the site name."""
        return self.get("site.name", "Gilman Skywatch Archive")

    def get_location_config(self) -> Dict[str, Any]:
        """Get the location configuration."""
        return self.get("location", {
            "name": "Gilman, Wisconsin",
            "latitude": 45.17,
            "longitude": -90.82,
            "timezone": "America/Chicago"
        })

    def get_latitude(self) -> float:
        """Get the location latitude."""
        return float(self.get("location.latitude", 45.17))

    def get_longitude(self) -> float:
        """Get the location longitude."""
        return float(self.get("location.longitude", -90.82))

    def get_timezone(self) -> str:
        """Get the location timezone."""
        return self.get("location.timezone", "America/Chicago")

    def get_openweathermap_key(self) -> Optional[str]:
        """Get the OpenWeatherMap API key."""
        return self.get("api_keys.openweathermap")

    def get_noaa_urls(self) -> Dict[str, str]:
        """Get NOAA data source URLs."""
        return self.get("data_sources.noaa", {})

    def get_clearsky_config(self) -> Dict[str, str]:
        """Get Clear Sky chart configuration."""
        return self.get("data_sources.clearsky", {})

    def get_display_config(self) -> Dict[str, Any]:
        """Get display settings."""
        return self.get("display", {})

    def get_request_timeout(self) -> int:
        """Get the request timeout setting."""
        return int(self.get("advanced.request_timeout", 15))

    def get_user_agent(self) -> str:
        """Get the user agent string."""
        return self.get("advanced.user_agent", "Gilman Skywatch Archive")

    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return bool(self.get("advanced.debug", False))

    def reload(self) -> None:
        """Reload the configuration from file."""
        self._load_config()


# Global configuration instance
_config = None


def get_config(config_file: Optional[Path] = None) -> Config:
    """
    Get the global configuration instance.

    Args:
        config_file: Optional path to configuration file

    Returns:
        Configuration instance
    """
    global _config
    if _config is None:
        _config = Config(config_file)
    return _config


def reload_config(config_file: Optional[Path] = None) -> Config:
    """
    Reload the configuration from file.

    Args:
        config_file: Optional path to configuration file

    Returns:
        New configuration instance
    """
    global _config
    _config = Config(config_file)
    return _config