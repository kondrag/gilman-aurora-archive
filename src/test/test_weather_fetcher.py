"""
Unit tests for weather_fetcher module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json

from weather_fetcher import WeatherFetcher


class TestWeatherFetcher:
    """Test cases for WeatherFetcher class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.get_user_agent.return_value = "test-agent"
        config.get_latitude.return_value = 45.17
        config.get_longitude.return_value = -90.82
        config.get_timezone.return_value = "America/Chicago"
        config.get_openweathermap_api_key.return_value = "test-api-key"
        config.get.return_value = "test_value"
        return config

    @pytest.fixture
    def weather_fetcher(self, mock_config):
        """Create WeatherFetcher instance with mocked dependencies."""
        with patch('weather_fetcher.get_config', return_value=mock_config):
            return WeatherFetcher(skip_network=True)

    def test_init(self, weather_fetcher):
        """Test WeatherFetcher initialization."""
        assert weather_fetcher.skip_network is True
        assert weather_fetcher.config is not None
        assert weather_fetcher.session is not None
        assert weather_fetcher.site_lat == 45.17
        assert weather_fetcher.site_lon == -90.82
        assert weather_fetcher.timezone == "America/Chicago"

    def test_init_with_network(self, mock_config):
        """Test WeatherFetcher initialization with network access."""
        with patch('weather_fetcher.get_config', return_value=mock_config):
            wf = WeatherFetcher(skip_network=False)
            assert wf.skip_network is False

    @patch('weather_fetcher.moon_illumination')
    @patch('weather_fetcher.phase')
    @patch('weather_fetcher.moonrise')
    @patch('weather_fetcher.moonset')
    def test_get_moon_data_success(self, mock_moonset, mock_moonrise, mock_phase, mock_moon_illumination, weather_fetcher):
        """Test successful moon data retrieval."""
        # Setup mocks
        target_date = datetime(2024, 1, 15, tzinfo=ZoneInfo("America/Chicago"))

        mock_moonrise.return_value = datetime(2024, 1, 15, 8, 0, tzinfo=ZoneInfo("America/Chicago"))
        mock_moonset.return_value = datetime(2024, 1, 15, 20, 0, tzinfo=ZoneInfo("America/Chicago"))
        mock_phase.return_value = 0.25  # First quarter
        mock_moon_illumination.return_value = 0.5  # 50% illumination

        # Call method
        result = weather_fetcher._get_moon_data(target_date)

        # Verify results
        assert result['moonrise'] is not None
        assert result['moonset'] is not None
        assert result['phase_name'] == 'First Quarter'
        assert result['phase_percentage'] == 50.0  # astroplan illumination
        assert result['phase_decimal'] == 0.25
        assert result['method'] == 'astroplan'

    def test_get_moon_data_no_location(self, weather_fetcher):
        """Test moon data retrieval when location is not available."""
        weather_fetcher.gilman_location = None
        target_date = datetime(2024, 1, 15, tzinfo=ZoneInfo("America/Chicago"))

        result = weather_fetcher._get_moon_data(target_date)

        assert result['moonrise'] is None
        assert result['moonset'] is None
        assert result['phase_name'] is None
        assert result['phase_percentage'] is None
        assert result['method'] == 'fallback'

    @patch('weather_fetcher.moon_illumination')
    @patch('weather_fetcher.phase')
    @patch('weather_fetcher.moonrise')
    @patch('weather_fetcher.moonset')
    def test_get_moon_data_phase_names(self, mock_moonset, mock_moonrise, mock_phase, mock_moon_illumination, weather_fetcher):
        """Test moon phase name determination."""
        target_date = datetime(2024, 1, 15, tzinfo=ZoneInfo("America/Chicago"))

        mock_moonrise.return_value = datetime(2024, 1, 15, 8, 0, tzinfo=ZoneInfo("America/Chicago"))
        mock_moonset.return_value = datetime(2024, 1, 15, 20, 0, tzinfo=ZoneInfo("America/Chicago"))
        mock_moon_illumination.return_value = 0.5

        # Test different moon phases
        test_cases = [
            (0.01, "New Moon"),
            (0.1, "Waxing Crescent"),
            (0.25, "First Quarter"),
            (0.4, "Waxing Gibbous"),
            (0.5, "Full Moon"),
            (0.6, "Waning Gibbous"),
            (0.75, "Last Quarter"),
            (0.9, "Waning Crescent"),
            (0.98, "New Moon"),
        ]

        for phase_value, expected_name in test_cases:
            mock_phase.return_value = phase_value
            result = weather_fetcher._get_moon_data(target_date)
            assert result['phase_name'] == expected_name, f"Phase {phase_value} should be {expected_name}"

    def test_get_fallback_data(self, weather_fetcher):
        """Test fallback data generation."""
        result = weather_fetcher._get_fallback_data()

        assert result['status'] == 'offline'
        assert result['kp_index'] is None
        assert result['g_scale'] == weather_fetcher._get_g_scale_level(None)
        assert result['aurora_activity'] == 'Data unavailable'
        assert result['solar_wind']['speed'] is None
        assert result['solar_wind']['density'] is None
        assert result['solar_wind']['bz'] is None
        assert 'timestamp' in result

    def test_get_fallback_forecast(self, weather_fetcher):
        """Test fallback forecast generation."""
        result = weather_fetcher._get_fallback_forecast()

        assert len(result) == 3  # Should generate 3 days
        for day in result:
            assert 'day' in day
            assert 'date' in day
            assert day['kp_forecast'] is None
            assert day['aurora_chance'] == 'Data unavailable'
            assert day['status'] == 'offline'

    def test_get_fallback_atmospheric_forecast(self, weather_fetcher):
        """Test fallback atmospheric forecast generation."""
        result = weather_fetcher._get_fallback_atmospheric_forecast()

        assert 'forecast' in result
        assert len(result['forecast']) == 3
        assert result['location'] == 'Gilman, Wisconsin'
        assert result['source'] == 'Fallback data - API key required'
        assert result['api_required'] is True

        for day in result['forecast']:
            assert 'day' in day
            assert 'date' in day
            assert 'condition' in day
            assert day['icon'] is None
            assert day['high_temp'] is None
            assert day['low_temp'] is None

    @patch('weather_fetcher.sun')
    def test_get_sunrise_sunset_success(self, mock_sun, weather_fetcher):
        """Test successful sunrise/sunset calculation."""
        target_date = datetime(2024, 6, 21, tzinfo=ZoneInfo("America/Chicago"))

        mock_sun_data = {
            'sunrise': datetime(2024, 6, 21, 5, 15, tzinfo=ZoneInfo("America/Chicago")),
            'sunset': datetime(2024, 6, 21, 20, 30, tzinfo=ZoneInfo("America/Chicago")),
            'dawn': datetime(2024, 6, 21, 4, 30, tzinfo=ZoneInfo("America/Chicago")),
            'dusk': datetime(2024, 6, 21, 21, 15, tzinfo=ZoneInfo("America/Chicago")),
        }
        mock_sun.return_value = mock_sun_data

        result = weather_fetcher._get_sunrise_sunset(target_date)

        assert result['sunrise'] is not None
        assert result['sunset'] is not None
        assert result['civil_dawn'] is not None
        assert result['civil_dusk'] is not None
        assert result['method'] == 'astral'

    def test_get_sunrise_sunset_no_location(self, weather_fetcher):
        """Test sunrise/sunset calculation when location is not available."""
        weather_fetcher.gilman_location = None
        target_date = datetime(2024, 6, 21, tzinfo=ZoneInfo("America/Chicago"))

        result = weather_fetcher._get_sunrise_sunset(target_date)

        assert result['method'] == 'approximate'
        assert result['sunrise'] is not None  # Should have fallback values
        assert result['sunset'] is not None

    def test_get_g_scale_level(self, weather_fetcher):
        """Test G-scale level calculation."""
        test_cases = [
            (None, 0, "inactive"),
            (1, 1, "low"),
            (3, 3, "moderate"),
            (6, 6, "high"),
            (9, 9, "high"),
        ]

        for kp_value, expected_level, expected_class in test_cases:
            result = weather_fetcher._get_g_scale_level(kp_value)
            assert result == {
                'level': expected_level,
                'class': expected_class
            }

    def test_format_kp_index(self, weather_fetcher):
        """Test Kp index formatting."""
        # Test with valid KP index
        result = weather_fetcher._format_kp_index(4.5)
        assert result == '4.5'

        # Test with None
        result = weather_fetcher._format_kp_index(None)
        assert result == 'Data unavailable'

        # Test with invalid data (string)
        result = weather_fetcher._format_kp_index('4.5')
        assert result == 'Data unavailable'

    def test_fetch_json_skip_network(self, weather_fetcher):
        """Test JSON fetching when skip_network is True."""
        result = weather_fetcher._fetch_json("http://example.com/api")
        assert result is None

    @patch('requests.Session.get')
    def test_fetch_json_success(self, mock_get, mock_config):
        """Test successful JSON fetching."""
        # Create WeatherFetcher with network access
        with patch('weather_fetcher.get_config', return_value=mock_config):
            wf = WeatherFetcher(skip_network=False)

        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        result = wf._fetch_json("http://example.com/api")

        assert result == {"test": "data"}
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_fetch_json_error(self, mock_get, mock_config):
        """Test JSON fetching with error."""
        # Create WeatherFetcher with network access
        with patch('weather_fetcher.get_config', return_value=mock_config):
            wf = WeatherFetcher(skip_network=False)

        # Mock failed response
        mock_get.side_effect = Exception("Network error")

        result = wf._fetch_json("http://example.com/api")

        assert result is None

    def test_get_weather_data(self, weather_fetcher):
        """Test complete weather data retrieval."""
        with patch.object(weather_fetcher, '_get_current_data') as mock_current, \
             patch.object(weather_fetcher, '_get_forecast_data') as mock_forecast, \
             patch.object(weather_fetcher, '_get_atmospheric_forecast_data') as mock_atmospheric, \
             patch.object(weather_fetcher, '_get_clearsky_chart_data') as mock_clearsky, \
             patch.object(weather_fetcher, '_get_sunrise_sunset') as mock_sun, \
             patch.object(weather_fetcher, '_get_moon_data') as mock_moon:

            # Setup mocks
            mock_current.return_value = {"kp_index": 3, "aurora_activity": "Low"}
            mock_forecast.return_value = {"forecast": []}
            mock_atmospheric.return_value = {"forecast": []}
            mock_clearsky.return_value = {"chart_url": None}
            mock_sun.return_value = {"sunrise": None, "sunset": None}
            mock_moon.return_value = {"phase_name": "New Moon", "phase_percentage": 0}

            # Test current data
            result = weather_fetcher.get_weather_data(current_only=True)

            assert 'current' in result
            assert 'sun_times' in result
            assert 'moon_data' in result
            assert 'forecast' not in result
            assert 'atmospheric' not in result
            assert 'clearsky_chart' not in result

            mock_current.assert_called_once()
            mock_sun.assert_called_once()
            mock_moon.assert_called_once()

    @patch('weather_fetcher.moon_illumination')
    @patch('weather_fetcher.phase')
    @patch('weather_fetcher.moonrise')
    @patch('weather_fetcher.moonset')
    def test_get_moon_data_astroplan_illumination(self, mock_moonset, mock_moonrise, mock_phase, mock_moon_illumination, weather_fetcher):
        """Test that astroplan moon illumination is used correctly."""
        target_date = datetime(2024, 1, 15, tzinfo=ZoneInfo("America/Chicago"))

        mock_moonrise.return_value = datetime(2024, 1, 15, 8, 0, tzinfo=ZoneInfo("America/Chicago"))
        mock_moonset.return_value = datetime(2024, 1, 15, 20, 0, tzinfo=ZoneInfo("America/Chicago"))
        mock_phase.return_value = 0.25
        mock_moon_illumination.return_value = 0.95  # 95% illumination

        with patch('weather_fetcher.Time') as mock_time:
            mock_time.return_value = "mock_time_object"
            result = weather_fetcher._get_moon_data(target_date)

            mock_time.assert_called_once_with(target_date)
            mock_moon_illumination.assert_called_once_with("mock_time_object")
            assert result['phase_percentage'] == 95.0
            assert result['method'] == 'astroplan'

    def test_get_weather_data_full(self, weather_fetcher):
        """Test complete weather data retrieval including forecast and atmospheric."""
        with patch.object(weather_fetcher, '_get_current_data') as mock_current, \
             patch.object(weather_fetcher, '_get_forecast_data') as mock_forecast, \
             patch.object(weather_fetcher, '_get_atmospheric_forecast_data') as mock_atmospheric, \
             patch.object(weather_fetcher, '_get_clearsky_chart_data') as mock_clearsky, \
             patch.object(weather_fetcher, '_get_sunrise_sunset') as mock_sun, \
             patch.object(weather_fetcher, '_get_moon_data') as mock_moon:

            # Setup mocks
            mock_current.return_value = {"kp_index": 3, "aurora_activity": "Low"}
            mock_forecast.return_value = {"forecast": [{"day": "Tomorrow"}]}
            mock_atmospheric.return_value = {"forecast": [{"day": "Today"}]}
            mock_clearsky.return_value = {"chart_url": "http://example.com/chart.png"}
            mock_sun.return_value = {"sunrise": None, "sunset": None}
            mock_moon.return_value = {"phase_name": "New Moon", "phase_percentage": 0}

            result = weather_fetcher.get_weather_data()

            assert 'current' in result
            assert 'sun_times' in result
            assert 'moon_data' in result
            assert 'forecast' in result
            assert 'atmospheric' in result
            assert 'clearsky_chart' in result

            mock_current.assert_called_once()
            mock_forecast.assert_called_once()
            mock_atmospheric.assert_called_once()
            mock_clearsky.assert_called_once()
            mock_sun.assert_called_once()
            mock_moon.assert_called_once()