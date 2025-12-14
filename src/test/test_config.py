"""
Unit tests for config module.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
import json
import os
from pathlib import Path

# Import the config module functions directly
import sys
sys.path.insert(0, 'src')
from config import get_config, Config


class TestConfig:
    """Test cases for Config class."""

    def test_config_init_default_values(self):
        """Test Config initialization with default values."""
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config = Config()

                # Test default values
                assert config.get("location.name", "default") == "Gilman, Wisconsin"
                assert config.get_latitude() == 45.17
                assert config.get_longitude() == -90.82
                assert config.get_timezone() == "America/Chicago"

    def test_config_load_from_file(self):
        """Test loading configuration from JSON file."""
        test_config_data = {
            "location": {
                "name": "Test City",
                "latitude": 40.0,
                "longitude": -80.0,
                "timezone": "America/New_York"
            },
            "api_keys": {
                "openweathermap": "test_api_key"
            },
            "thresholds": {
                "kp_warning": 5
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()

                assert config.get("location.name") == "Test City"
                assert config.get_latitude() == 40.0
                assert config.get_longitude() == -80.0
                assert config.get_timezone() == "America/New_York"
                assert config.get("api_keys.openweathermap") == "test_api_key"

    def test_config_file_not_exists(self):
        """Test Config when config file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            config = Config()

            # Should use default values
            assert config.get("location.name", "default") == "Gilman, Wisconsin"

    def test_config_invalid_json(self):
        """Test Config with invalid JSON file."""
        with patch('builtins.open', mock_open(read_data='invalid json')):
            with patch('os.path.exists', return_value=True):
                config = Config()

                # Should use default values
                assert config.get("location.name", "default") == "Gilman, Wisconsin"

    def test_get_method(self):
        """Test the get method with default values."""
        test_config_data = {
            "existing_key": "existing_value",
            "nested": {
                "key": "nested_value"
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()

                # Test existing key
                assert config.get("existing_key") == "existing_value"

                # Test nested key
                assert config.get("nested.key") == "nested_value"

                # Test missing key with default
                assert config.get("missing_key", "default_value") == "default_value"

                # Test missing key without default
                assert config.get("missing_key") is None

    def test_get_latitude(self):
        """Test get_latitude method."""
        test_config_data = {
            "location": {
                "latitude": 35.5
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_latitude() == 35.5

    def test_get_longitude(self):
        """Test get_longitude method."""
        test_config_data = {
            "location": {
                "longitude": -85.0
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_longitude() == -85.0

    def test_get_timezone(self):
        """Test get_timezone method."""
        test_config_data = {
            "location": {
                "timezone": "Europe/London"
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_timezone() == "Europe/London"

    def test_get_openweathermap_api_key(self):
        """Test get_openweathermap_api_key method."""
        test_config_data = {
            "api_keys": {
                "openweathermap": "test_weather_key"
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_openweathermap_api_key() == "test_weather_key"

    def test_get_user_agent(self):
        """Test get_user_agent method."""
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config = Config()
                user_agent = config.get_user_agent()

                # Should include default components
                assert "AuroraArchive" in user_agent
                assert "gilman-skywatch-archive" in user_agent

    def test_get_user_agent_custom(self):
        """Test get_user_agent method with custom user agent."""
        test_config_data = {
            "user_agent": "Custom-Aurora-Tracker/1.0"
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_user_agent() == "Custom-Aurora-Tracker/1.0"

    def test_get_fallback_atmospheric_forecast_days(self):
        """Test get_fallback_atmospheric_forecast_days method."""
        # Test with custom value
        test_config_data = {
            "forecast": {
                "fallback_atmospheric_days": 5
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_fallback_atmospheric_forecast_days() == 5

        # Test with default value
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_fallback_atmospheric_forecast_days() == 3

    def test_get_noaa_kp_forecast_hours(self):
        """Test get_noaa_kp_forecast_hours method."""
        # Test with custom value
        test_config_data = {
            "forecast": {
                "noaa_kp_hours": 12
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_noaa_kp_forecast_hours() == 12

        # Test with default value
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_noaa_kp_forecast_hours() == 3

    def test_get_swpc_kp_forecast_hours(self):
        """Test get_swpc_kp_forecast_hours method."""
        # Test with custom value
        test_config_data = {
            "forecast": {
                "swpc_kp_hours": 6
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_swpc_kp_forecast_hours() == 6

        # Test with default value
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config = Config()
                assert config.get_swpc_kp_forecast_hours() == 3

    def test_config_validation_invalid_latitude(self):
        """Test config validation with invalid latitude."""
        test_config_data = {
            "location": {
                "latitude": 95.0  # Invalid latitude
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                # Should fall back to default value
                assert config.get_latitude() == 45.17

    def test_config_validation_invalid_longitude(self):
        """Test config validation with invalid longitude."""
        test_config_data = {
            "location": {
                "longitude": 185.0  # Invalid longitude
            }
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(test_config_data))):
            with patch('os.path.exists', return_value=True):
                config = Config()
                # Should fall back to default value
                assert config.get_longitude() == -90.82


class TestConfigSingleton:
    """Test cases for config singleton pattern."""

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config1 = get_config()
                config2 = get_config()

                # Should be the same instance (singleton pattern)
                assert config1 is config2

    @patch('config._config_instance', None)
    def test_get_config_creates_instance(self):
        """Test that get_config creates an instance when none exists."""
        with patch('builtins.open', mock_open(read_data='{}')):
            with patch('os.path.exists', return_value=True):
                config = get_config()

                assert isinstance(config, Config)
                assert config is not None