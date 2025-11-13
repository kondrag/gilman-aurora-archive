"""
Weather fetcher for NOAA space weather data.
"""

import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import logging
import json
import re
import os
from pathlib import Path
from config import get_config

logger = logging.getLogger(__name__)

# Import astral for precise sunrise/sunset calculations
try:
    from astral import LocationInfo
    from astral.sun import sun
    from astral.moon import moonrise, moonset, phase
    ASTRAL_AVAILABLE = True
except ImportError:
    ASTRAL_AVAILABLE = False
    logger.warning("Astral library not available, using fallback sunrise/sunset times")

class WeatherFetcher:
    """Fetches space weather data from NOAA APIs and web services."""

    def __init__(self, skip_network: bool = False):
        self.skip_network = skip_network
        self.config = get_config()

        # Initialize session with configurable user agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.get_user_agent(),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        # Location configuration from config file
        self.location_name = self.config.get("location.name", "Gilman, Wisconsin")
        self.gilman_lat = self.config.get_latitude()
        self.gilman_lon = self.config.get_longitude()
        self.timezone = self.config.get_timezone()

        # Gilman, WI location for sunrise/sunset calculations
        self.gilman_location = None
        if ASTRAL_AVAILABLE:
            try:
                self.gilman_location = LocationInfo(
                    self.location_name.split(',')[0].strip(),
                    self.location_name.split(',')[1].strip() if ',' in self.location_name else "",
                    self.timezone,
                    self.gilman_lat,
                    self.gilman_lon
                )
            except Exception as e:
                logger.warning(f"Failed to initialize location in astral: {e}")

    def _get_sunrise_sunset_fallback(self, target_date: datetime) -> Dict[str, Optional[datetime]]:
        """Fallback sunrise/sunset calculation using approximate times."""
        # Fallback to approximate times
        month = target_date.month
        if month in [11, 12, 1, 2]:  # Winter months
            sunrise_hour = 7.5  # 7:30 AM CST
            sunset_hour = 16.5   # 4:30 PM CST
        else:  # Summer months
            sunrise_hour = 6.5   # 6:30 AM CDT
            sunset_hour = 19.5   # 7:30 PM CDT

        # Convert to datetime objects
        sunrise = target_date.replace(hour=int(sunrise_hour), minute=int((sunrise_hour % 1) * 60), second=0, microsecond=0)
        sunset = target_date.replace(hour=int(sunset_hour), minute=int((sunset_hour % 1) * 60), second=0, microsecond=0)

        return {
            'sunrise': sunrise,
            'sunset': sunset,
            'civil_dawn': None,
            'civil_dusk': None,
            'civil_dawn_tomorrow': None,
            'nautical_dawn': None,
            'nautical_dusk': None,
            'nautical_dawn_tomorrow': None,
            'astronomical_dawn': None,
            'astronomical_dusk': None,
            'astronomical_dawn_tomorrow': None,
            'method': 'approximate'
        }

    def _get_sunrise_sunset(self, target_date: datetime) -> Dict[str, Optional[datetime]]:
        """Get precise sunrise and sunset times for Gilman, WI."""
        if not ASTRAL_AVAILABLE or not self.gilman_location:
            return self._get_sunrise_sunset_fallback(target_date)

        try:
            # Use astral for precise calculations
            s = sun(self.gilman_location.observer, date=target_date.date())

            # Calculate twilight times using solar depression angles
            # Civil twilight: 6° below horizon (suitable for most outdoor activities)
            # Nautical twilight: 12° below horizon (navigation by stars possible)
            # Astronomical twilight: 18° below horizon (full darkness, ideal for astronomy)
            from astral import Depression

            # Get dawn and dusk times for different solar depressions
            civil = sun(self.gilman_location.observer, date=target_date.date(), dawn_dusk_depression=Depression.CIVIL)
            nautical = sun(self.gilman_location.observer, date=target_date.date(), dawn_dusk_depression=Depression.NAUTICAL)
            astronomical = sun(self.gilman_location.observer, date=target_date.date(), dawn_dusk_depression=Depression.ASTRONOMICAL)

            # Get tomorrow's dawn times for twilight end calculations
            tomorrow = target_date + timedelta(days=1)
            civil_tomorrow = sun(self.gilman_location.observer, date=tomorrow.date(), dawn_dusk_depression=Depression.CIVIL)
            nautical_tomorrow = sun(self.gilman_location.observer, date=tomorrow.date(), dawn_dusk_depression=Depression.NAUTICAL)
            astronomical_tomorrow = sun(self.gilman_location.observer, date=tomorrow.date(), dawn_dusk_depression=Depression.ASTRONOMICAL)

            # The times from astral are already timezone-aware (UTC for America/Chicago)
            # No need to convert them again
            return {
                'sunrise': s['sunrise'],
                'sunset': s['sunset'],
                'civil_dawn': civil['dawn'],
                'civil_dusk': civil['dusk'],
                'civil_dawn_tomorrow': civil_tomorrow['dawn'],
                'nautical_dawn': nautical['dawn'],
                'nautical_dusk': nautical['dusk'],
                'nautical_dawn_tomorrow': nautical_tomorrow['dawn'],
                'astronomical_dawn': astronomical['dawn'],
                'astronomical_dusk': astronomical['dusk'],
                'astronomical_dawn_tomorrow': astronomical_tomorrow['dawn'],
                'method': 'astral'
            }
        except Exception as e:
            logger.error(f"Error calculating sunrise/sunset with astral: {e}")
            # Fallback to approximate times
            return self._get_sunrise_sunset_fallback(target_date)

    def _get_moon_data(self, target_date: datetime) -> Dict[str, Any]:
        """Get moon rise, moon set, and moon phase for Gilman, WI."""
        if not ASTRAL_AVAILABLE or not self.gilman_location:
            # Fallback to basic data
            return {
                'moonrise': None,
                'moonset': None,
                'phase_name': None,
                'phase_percentage': None,
                'phase_decimal': None,
                'method': 'fallback'
            }

        try:
            # Use astral for moon calculations
            moon_rise = moonrise(self.gilman_location.observer, date=target_date.date())
            moon_set = moonset(self.gilman_location.observer, date=target_date.date())

            # Get moon phase (0-1, where 0 is new moon, 0.5 is full moon)
            raw_phase_value = phase(target_date.date())
            phase_value = raw_phase_value % 1  # Normalize to 0-1 range

            # Determine moon phase name
            if phase_value < 0.03 or phase_value > 0.97:
                phase_name = "New Moon"
            elif phase_value < 0.22:
                phase_name = "Waxing Crescent"
            elif phase_value < 0.28:
                phase_name = "First Quarter"
            elif phase_value < 0.47:
                phase_name = "Waxing Gibbous"
            elif phase_value < 0.53:
                phase_name = "Full Moon"
            elif phase_value < 0.72:
                phase_name = "Waning Gibbous"
            elif phase_value < 0.78:
                phase_name = "Last Quarter"
            else:
                phase_name = "Waning Crescent"

            return {
                'moonrise': moon_rise,
                'moonset': moon_set,
                'phase_name': phase_name,
                'phase_percentage': round(phase_value * 100, 1),
                'phase_decimal': round(phase_value, 3),
                'method': 'astral'
            }
        except Exception as e:
            logger.error(f"Error calculating moon data with astral: {e}")
            # Fallback to basic data
            return {
                'moonrise': None,
                'moonset': None,
                'phase_name': None,
                'phase_percentage': None,
                'phase_decimal': None,
                'method': 'fallback'
            }

    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data when network fails."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'kp_index': None,
            'g_scale': self._get_g_scale_level(None),
            'aurora_activity': 'Data unavailable',
            'solar_wind': {'speed': None, 'density': None, 'bz': None},
            'status': 'offline'
        }

    def _get_fallback_forecast(self) -> List[Dict[str, Any]]:
        """Fallback forecast when network fails."""
        from zoneinfo import ZoneInfo
        location_tz = ZoneInfo(self.config.get_timezone())
        current_date = datetime.now(location_tz)
        result = []

        for i in range(3):
            future_date = current_date + timedelta(days=i + 1)
            result.append({
                'day': future_date.strftime('%A'),
                'date': future_date.strftime('%B %d'),
                'kp_forecast': None,
                'aurora_chance': 'Data unavailable',
                'status': 'offline'
            })

        return result

    def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch and parse JSON from a URL."""
        if self.skip_network:
            logger.info("Skipping network request (offline mode)")
            return None

        try:
            response = self.session.get(url, timeout=self.config.get_request_timeout())
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch JSON from {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {url}: {e}")
            return None

    def _fetch_text(self, url: str) -> Optional[str]:
        """Fetch text content from a URL."""
        if self.skip_network:
            logger.info("Skipping network request (offline mode)")
            return None

        try:
            response = self.session.get(url, timeout=self.config.get_request_timeout())
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch text from {url}: {e}")
            return None

    def get_current_conditions(self) -> Dict[str, Any]:
        """Get current space weather conditions from NOAA."""
        try:
            # Use the new NOAA Kp forecast JSON API
            noaa_urls = self.config.get_noaa_urls()
            kp_forecast_url = noaa_urls.get("kp_forecast_url", "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json")
            kp_data = self._fetch_json(kp_forecast_url)

            if kp_data and len(kp_data) > 1:  # First row is headers, data starts at index 1
                # Find the most recent observed data
                latest_observed = None
                for row in kp_data[1:]:  # Skip header row
                    if len(row) >= 4 and row[2] == 'observed':  # row[2] is the status field
                        if latest_observed is None or row[0] > latest_observed[0]:  # Compare timestamps
                            latest_observed = row

                if latest_observed and len(latest_observed) >= 3:
                    timestamp = latest_observed[0]  # time_tag
                    kp_index = latest_observed[1]   # kp
                    noaa_scale = latest_observed[3] if len(latest_observed) > 3 else None  # noaa_scale

                    try:
                        kp_value = float(kp_index)
                        logger.info(f"Successfully fetched real Kp index from NOAA JSON: {kp_value}")
                        return {
                            'timestamp': timestamp,
                            'kp_index': kp_value,
                            'g_scale': self._get_g_scale_level(kp_value),
                            'aurora_activity': self._get_aurora_activity_level(kp_value),
                            'solar_wind': self._get_solar_wind_data(),
                            'status': 'active'
                        }
                    except (ValueError, TypeError):
                        logger.error(f"Could not parse Kp value: {kp_index}")

            # Try the new NOAA Kp archive JSON API for current observed data
            logger.info("Trying new NOAA Kp archive JSON API")
            noaa_urls = self.config.get_noaa_urls()
            current_kp_url = noaa_urls.get("current_kp_url", "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json")
            current_kp_data = self._fetch_json(current_kp_url)

            if current_kp_data and len(current_kp_data) > 1:
                # Find the most recent observed data
                latest_observed = None
                for row in current_kp_data[1:]:  # Skip header row
                    if len(row) >= 4 and row[2] == 'observed':  # row[2] is the status field
                        if latest_observed is None or row[0] > latest_observed[0]:  # Compare timestamps
                            latest_observed = row

                if latest_observed and len(latest_observed) >= 3:
                    timestamp = latest_observed[0]  # time_tag
                    kp_index = latest_observed[1]   # kp
                    noaa_scale = latest_observed[3] if len(latest_observed) > 3 else None  # noaa_scale

                    try:
                        kp_value = float(kp_index)
                        logger.info(f"Successfully fetched current Kp index from NOAA archive JSON: {kp_value}")
                        return {
                            'timestamp': timestamp,
                            'kp_index': kp_value,
                            'g_scale': self._get_g_scale_level(kp_value),
                            'aurora_activity': self._get_aurora_activity_level(kp_value),
                            'solar_wind': self._get_solar_wind_data(),
                            'status': 'active'
                        }
                    except (ValueError, TypeError):
                        logger.error(f"Could not parse Kp value from archive: {kp_index}")

            # Fallback to text endpoint if JSON fails
            logger.info("JSON endpoints failed, trying text endpoint")
            text_data = self._fetch_text("https://services.swpc.noaa.gov/text/daily-geomagnetic-indices.txt")

            if text_data:
                kp_index = self._parse_kp_from_text(text_data)

                if kp_index is not None:
                    logger.info(f"Successfully parsed real Kp index from text: {kp_index}")
                    return {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'kp_index': kp_index,
                        'g_scale': self._get_g_scale_level(kp_index),
                        'aurora_activity': self._get_aurora_activity_level(kp_index),
                        'solar_wind': self._get_solar_wind_data(),
                        'status': 'active'
                    }

            # No real data available
            logger.warning("No real Kp data available from any NOAA source")
            return self._get_fallback_data()

        except Exception as e:
            logger.error(f"Error fetching current conditions: {e}")
            return self._get_fallback_data()

    def _parse_kp_from_text(self, text_data: str) -> Optional[float]:
        """Parse Kp index from NOAA text data."""
        try:
            lines = text_data.split('\n')

            # Look for the most recent day's data (typically at the end)
            for line in reversed(lines):
                # Skip lines that are headers or comments
                if line.strip() and not line.startswith('#') and not line.startswith(':'):
                    # Look for planetary Kp data pattern:
                    # 2025 11 12    -1  7-1-1-1-1-1-1-1    -1  7-1-1-1-1-1-1-1    44   8.67 -1.00 -1.00 -1.00 -1.00 -1.00 -1.00 -1.00
                    import re

                    # Pattern to match the planetary Kp values at the end of the line
                    # Example: 2025 11 12    -1  7-1-1-1-1-1-1-1    -1  7-1-1-1-1-1-1-1    44   8.67 -1.00 -1.00 -1.00 -1.00 -1.00 -1.00 -1.00
                    # We want the first decimal number after the sum (44 in this case), which is the planetary Kp
                    kp_pattern = r'\s+\d+\s+(\d+\.\d+)\s+-?\d+\.?\d*'

                    match = re.search(kp_pattern, line)
                    if match:
                        try:
                            kp_value = float(match.group(1))
                            # Sanity check: Kp values are typically 0-9
                            if 0 <= kp_value <= 9:
                                logger.info(f"Found Kp value {kp_value} in line: {line.strip()}")
                                return kp_value
                        except ValueError:
                            continue

                    # Alternative pattern for different formats
                    alt_patterns = [
                        r'(\d+\.\d+)\s*$',  # Number at end of line
                        r'\s+(\d+\.\d+)\s+-?\d+',  # Number followed by negative number
                    ]

                    for pattern in alt_patterns:
                        match = re.search(pattern, line)
                        if match:
                            try:
                                kp_value = float(match.group(1))
                                if 0 <= kp_value <= 9:
                                    logger.info(f"Found Kp value {kp_value} with alt pattern: {line.strip()}")
                                    return kp_value
                            except ValueError:
                                continue

            return None
        except Exception as e:
            logger.error(f"Error parsing Kp from text: {e}")
            return None

    def _get_g_scale_level(self, kp_index: Optional[float]) -> Dict[str, Any]:
        """Determine G-scale level and description based on Kp index."""
        if kp_index is None:
            return {
                'level': 'G0',
                'kp_min': None,
                'kp_max': None,
                'description': 'No storm activity'
            }
        elif kp_index >= 9:
            return {
                'level': 'G5',
                'kp_min': 9.0,
                'kp_max': 9.0,
                'description': 'Extreme Geomagnetic Storm'
            }
        elif kp_index >= 8:
            return {
                'level': 'G4',
                'kp_min': 8.0,
                'kp_max': 8.99,
                'description': 'Severe Geomagnetic Storm'
            }
        elif kp_index >= 7:
            return {
                'level': 'G3',
                'kp_min': 7.0,
                'kp_max': 7.99,
                'description': 'Strong Geomagnetic Storm'
            }
        elif kp_index >= 6:
            return {
                'level': 'G2',
                'kp_min': 6.0,
                'kp_max': 6.99,
                'description': 'Moderate Geomagnetic Storm'
            }
        elif kp_index >= 5:
            return {
                'level': 'G1',
                'kp_min': 5.0,
                'kp_max': 5.99,
                'description': 'Minor Geomagnetic Storm'
            }
        else:
            return {
                'level': 'G0',
                'kp_min': 0.0,
                'kp_max': 4.99,
                'description': 'No storm activity'
            }

    def _get_aurora_activity_level(self, kp_index: Optional[float]) -> str:
        """Determine aurora activity level based on Kp index."""
        if kp_index is None:
            return "Unknown"
        elif kp_index >= 7:
            return "Major Storm - Excellent aurora visibility"
        elif kp_index >= 6:
            return "Moderate Storm - Good aurora visibility"
        elif kp_index >= 5:
            return "Minor Storm - Possible aurora visibility"
        elif kp_index >= 4:
            return "Active - Aurora likely visible at high latitudes"
        elif kp_index >= 3:
            return "Quiet - Aurora may be visible overhead at high latitudes"
        else:
            return "Very Quiet - Unlikely aurora activity"

    def _get_solar_wind_data(self) -> Dict[str, Any]:
        """Get current solar wind data from DSCOVR satellite."""
        try:
            # Get DSCOVR magnetic field data (modern replacement for ACE)
            noaa_urls = self.config.get_noaa_urls()
            solar_wind_url = noaa_urls.get("solar_wind_url", "https://services.swpc.noaa.gov/json/dscovr/dscovr_mag_1s.json")
            solar_data = self._fetch_json(solar_wind_url)

            if solar_data and len(solar_data) > 0:
                latest = solar_data[0]
                # DSCOVR format: time_tag, bt (total field), bz_gsm (Bz GSM component)
                return {
                    'bt': latest.get('bt'),      # Total magnetic field strength
                    'bz_gsm': latest.get('bz_gsm'),  # Bz component in GSM coordinates
                    'time_tag': latest.get('time_tag'),  # Timestamp
                    'status': 'active'
                }
            else:
                return {
                    'bt': None,
                    'bz_gsm': None,
                    'time_tag': None,
                    'status': 'unavailable'
                }
        except Exception as e:
            logger.error(f"Error fetching DSCOVR solar wind data: {e}")
            return {
                'bt': None,
                'bz_gsm': None,
                'time_tag': None,
                'status': 'error'
            }

    def get_forecast(self) -> List[Dict[str, Any]]:
        """Get 3-day aurora forecast from NOAA."""
        try:
            # Use the new NOAA Kp forecast JSON API
            noaa_urls = self.config.get_noaa_urls()
            kp_forecast_url = noaa_urls.get("kp_forecast_url", "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json")
            forecast_data = self._fetch_json(kp_forecast_url)

            if forecast_data and len(forecast_data) > 1:  # First row is headers, data starts at index 1
                # Parse forecast data from the new JSON format
                result = []
                # Use local timezone for forecast dates (not UTC)
                from zoneinfo import ZoneInfo
                location_tz = ZoneInfo(self.config.get_timezone())
                current_date = datetime.now(location_tz)

                # Group data by date and find peak predicted values
                daily_peaks = {}

                for row in forecast_data[1:]:  # Skip header row
                    if len(row) >= 3:
                        timestamp_str = row[0]
                        kp_value = row[1]
                        status = row[2] if len(row) > 2 else 'observed'

                        try:
                            # Parse timestamp and extract date
                            timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
                            date_key = timestamp.date()

                            # Convert Kp to float
                            kp_float = float(kp_value)

                            # Only consider predicted/estimated data for future forecasts (exclude today)
                            if status in ['predicted', 'estimated'] and date_key > current_date.date():
                                if date_key not in daily_peaks:
                                    daily_peaks[date_key] = {
                                        'peak_kp': kp_float,
                                        'timestamps': []
                                    }

                                # Update peak Kp for this date
                                daily_peaks[date_key]['peak_kp'] = max(daily_peaks[date_key]['peak_kp'], kp_float)
                                daily_peaks[date_key]['timestamps'].append(timestamp)

                        except (ValueError, TypeError) as e:
                            logger.debug(f"Could not parse forecast row: {row}, error: {e}")
                            continue

                # Generate 3-day forecast from the processed data
                forecast_dates = sorted(daily_peaks.keys())
                for i, date_key in enumerate(forecast_dates[:3]):  # Limit to 3 days
                    day_data = daily_peaks[date_key]
                    peak_kp = day_data['peak_kp']

                    # Find the first timestamp for this date to get proper day name
                    first_timestamp = day_data['timestamps'][0] if day_data['timestamps'] else datetime.combine(date_key, datetime.min.time())

                    result.append({
                        'day': first_timestamp.strftime('%A'),
                        'date': first_timestamp.strftime('%B %d'),
                        'kp_forecast': f"Kp {peak_kp:.1f}",
                        'aurora_chance': self._get_aurora_activity_level(peak_kp),
                        'status': 'forecast'
                    })

                if len(result) >= 1:
                    logger.info(f"Successfully generated {len(result)} day forecast from NOAA JSON")
                    # If we have fewer than 3 days, fill the rest with fallback
                    while len(result) < 3:
                        future_date = current_date + timedelta(days=len(result) + 1)
                        result.append({
                            'day': future_date.strftime('%A'),
                            'date': future_date.strftime('%B %d'),
                            'kp_forecast': None,
                            'aurora_chance': 'Data unavailable',
                            'status': 'unavailable'
                        })
                    return result[:3]

            # Fallback to text endpoint if JSON fails
            logger.info("JSON forecast failed, trying text endpoint")
            noaa_urls = self.config.get_noaa_urls()
            forecast_text = self._fetch_text(noaa_urls.get("forecast_url", "https://services.swpc.noaa.gov/text/3-day-forecast.txt"))

            if forecast_text:
                forecast_data = self._parse_3day_forecast(forecast_text)
                if forecast_data:
                    logger.info(f"Successfully parsed {len(forecast_data)} day forecast from NOAA text")
                    return forecast_data

            # No real data available
            logger.warning("No real forecast data available from NOAA")
            return self._get_fallback_forecast()

        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            return self._get_fallback_forecast()

    def _parse_3day_forecast(self, forecast_text: str) -> List[Dict[str, Any]]:
        """Parse 3-day Kp forecast from NOAA text data."""
        try:
            lines = forecast_text.split('\n')
            from zoneinfo import ZoneInfo
            location_tz = ZoneInfo(self.config.get_timezone())
            current_date = datetime.now(location_tz)
            result = []

            # Parse the Kp index table
            # The format is:
            #              Nov 12       Nov 13       Nov 14
            # 00-03UT       5.00 (G1)    6.67 (G3)    4.67 (G1)
            # 03-06UT       7.33 (G3)    6.33 (G2)    4.00
            # etc.

            date_line = None
            kp_data = []

            for i, line in enumerate(lines):
                if 'NOAA Kp index breakdown' in line:
                    # Find the line with dates (skip empty lines)
                    date_line = None
                    for j in range(i + 1, len(lines)):
                        if 'Nov' in lines[j] or 'Dec' in lines[j] or 'Jan' in lines[j]:  # Look for month names
                            date_line = lines[j]
                            break

                    # Look for the time slot lines that follow
                    for j in range(i + 1, len(lines)):
                        time_line = lines[j]
                        if 'UT' in time_line and any(utc_slot in time_line for utc_slot in ['00-03', '03-06', '06-09', '09-12', '12-15', '15-18', '18-21', '21-00']):
                            kp_data.append(time_line)
                        elif 'Rationale' in time_line:
                            break
                    break

            if not date_line or not kp_data:
                logger.warning("Could not find forecast data table")
                return None

            # Extract dates from the header line
            dates = []
            parts = date_line.split()
            for part in parts:
                # Look for month names
                if part in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
                    idx = parts.index(part)
                    if idx + 1 < len(parts):
                        date_str = f"{part} {parts[idx + 1]}"
                        dates.append(date_str)

            # Parse Kp values for each day
            daily_kp_values = {0: [], 1: [], 2: []}  # Dict for each day

            for time_line in kp_data:
                # Extract time slot start hour (e.g., "00" from "00-03UT")
                time_match = re.search(r'(\d{2})-\d{2}UT', time_line)
                if not time_match:
                    continue

                hour_utc = int(time_match.group(1))

                # Extract Kp values from the line (look for decimal numbers)
                kp_matches = re.findall(r'\b\d+\.\d+\b', time_line)

                for day_idx, kp_value in enumerate(kp_matches[:3]):  # Take first 3 days
                    if day_idx < 3:
                        try:
                            daily_kp_values[day_idx].append((hour_utc, float(kp_value)))
                        except ValueError:
                            continue

            # Generate forecast for each day
            for day_idx in range(min(3, len(dates))):
                if day_idx in daily_kp_values and daily_kp_values[day_idx]:
                    # Find peak nighttime Kp for Gilman, WI
                    night_peak_kp = self._find_nighttime_peak_kp(daily_kp_values[day_idx], current_date, day_idx)

                    # Calculate date for this forecast day
                    forecast_date = current_date + timedelta(days=day_idx + 1)

                    result.append({
                        'day': forecast_date.strftime('%A'),
                        'date': forecast_date.strftime('%B %d'),
                        'kp_forecast': f"Kp {night_peak_kp:.1f}",
                        'aurora_chance': self._get_aurora_activity_level(night_peak_kp),
                        'status': 'forecast'
                    })

            return result[:3]

        except Exception as e:
            logger.error(f"Error parsing 3-day forecast: {e}")
            return None

    def _find_nighttime_peak_kp(self, kp_values: List[tuple], base_date: datetime, day_offset: int) -> float:
        """Find the peak Kp value during nighttime hours for Gilman, WI."""
        peak_kp = 0.0

        # Calculate forecast date
        forecast_date = base_date + timedelta(days=day_offset + 1)

        # Get precise sunrise/sunset times for the forecast day
        sun_times = self._get_sunrise_sunset(forecast_date)
        sunrise = sun_times['sunrise']
        sunset = sun_times['sunset']

        if not sunrise or not sunset:
            logger.warning(f"Could not calculate sunrise/sunset for {forecast_date.date()}, using fallback")
            return peak_kp

        # Convert sunrise/sunset to UTC for comparison with forecast data
        sunrise_utc = sunrise.astimezone(timezone.utc)
        sunset_utc = sunset.astimezone(timezone.utc)

        logger.debug(f"Nighttime Kp calculation for {forecast_date.date()}: "
                    f"Sunrise UTC: {sunrise_utc.strftime('%H:%M')}, "
                    f"Sunset UTC: {sunset_utc.strftime('%H:%M')}, "
                    f"Method: {sun_times['method']}")

        # Find peak Kp during nighttime hours (after sunset, before sunrise next day)
        for utc_hour, kp_value in kp_values:
            # Convert the hour to a datetime for proper comparison
            forecast_time_utc = forecast_date.replace(hour=utc_hour, minute=0, second=0, microsecond=0)
            forecast_time_utc = forecast_time_utc.astimezone(timezone.utc)

            # Check if it's nighttime (after sunset, before sunrise next day)
            # Handle both cases: evening after sunset and early morning before sunrise
            is_nighttime = False

            # Evening: after sunset (same day)
            if forecast_time_utc.time() >= sunset_utc.time():
                is_nighttime = True
            # Early morning: before sunrise (next day)
            elif forecast_time_utc.time() < sunrise_utc.time():
                is_nighttime = True

            if is_nighttime:
                peak_kp = max(peak_kp, kp_value)
                logger.debug(f"Nighttime Kp found: {kp_value:.1f} at {utc_hour:02d}:00 UTC")

        if peak_kp == 0.0:
            logger.warning(f"No nighttime Kp values found for {forecast_date.date()}, using daytime maximum")
            # Fallback to maximum Kp value if no nighttime values found
            peak_kp = max(kp_value for _, kp_value in kp_values) if kp_values else 0.0

        return peak_kp

    def _get_atmospheric_forecast(self) -> Dict[str, Any]:
        """Get 3-day atmospheric weather forecast for Gilman, WI."""
        if self.skip_network:
            logger.info("Skipping atmospheric weather request (offline mode)")
            return self._get_fallback_atmospheric_forecast()

        try:
            # Check if OpenWeatherMap API key is available
            api_key = self.config.get_openweathermap_key()
            if not api_key:
                logger.info("Atmospheric weather API requires OpenWeatherMap API key configuration")
                return self._get_fallback_atmospheric_forecast()

            # Use OpenWeatherMap 5-day forecast API (free tier)
            return self._fetch_openweather_forecast(api_key)

        except Exception as e:
            logger.error(f"Error fetching atmospheric forecast: {e}")
            return self._get_fallback_atmospheric_forecast()

    def _get_fallback_atmospheric_forecast(self) -> Dict[str, Any]:
        """Fallback atmospheric forecast when API is not configured."""
        from zoneinfo import ZoneInfo
        location_tz = ZoneInfo(self.config.get_timezone())
        current_date = datetime.now(location_tz)
        forecast_days = []

        # Generate 3-day placeholder forecast
        for i in range(3):
            future_date = current_date + timedelta(days=i + 1)
            forecast_days.append({
                'day': future_date.strftime('%A'),
                'date': future_date.strftime('%B %d'),
                'high_temp': None,
                'low_temp': None,
                'condition': 'Weather data unavailable',
                'icon': None,
                'description': 'Configure OpenWeatherMap API key for real data'
            })

        return {
            'forecast': forecast_days,
            'location': self.location_name,
            'last_updated': current_date.isoformat(),
            'source': 'Fallback data - API key required',
            'api_required': True
        }

    def _fetch_openweather_forecast(self, api_key: str) -> Dict[str, Any]:
        """Fetch atmospheric weather forecast from OpenWeatherMap API."""
        try:
            # Construct OpenWeatherMap API URL
            lat = self.gilman_lat
            lon = self.gilman_lon
            url = f"https://api.openweathermap.org/data/2.5/forecast"

            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'imperial',  # Use Fahrenheit for US audience
                'cnt': 40  # 5 days (3-hour intervals) to ensure we have enough data for today + 3 days
            }

            response = self.session.get(url, params=params, timeout=self.config.get_request_timeout())
            response.raise_for_status()
            data = response.json()

            # Parse the forecast data
            forecast_days = []
            daily_data = {}

            # Group forecasts by date
            for item in data['list']:
                dt = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
                date_str = dt.strftime('%Y-%m-%d')

                if date_str not in daily_data:
                    daily_data[date_str] = {
                        'temps': [],
                        'conditions': [],
                        'humidity': [],
                        'wind_speed': [],
                        'descriptions': []
                    }

                daily_data[date_str]['temps'].append(item['main']['temp'])
                daily_data[date_str]['conditions'].append(item['weather'][0]['main'])
                daily_data[date_str]['humidity'].append(item['main']['humidity'])
                daily_data[date_str]['wind_speed'].append(item.get('wind', {}).get('speed', 0))
                daily_data[date_str]['descriptions'].append(item['weather'][0]['description'])

                # Create daily summaries (include today for 4-day forecast)
            from zoneinfo import ZoneInfo
            location_tz = ZoneInfo(self.config.get_timezone())
            current_date = datetime.now(location_tz).strftime('%Y-%m-%d')
            forecast_days = []

            # Check if we have current conditions for today
            current_conditions_added = False
            if current_date in daily_data:
                # We have today's forecast data from the API
                day_data = daily_data[current_date]
                date_obj = datetime.strptime(current_date, '%Y-%m-%d')
                high_temp = max(day_data['temps']) if day_data['temps'] else None
                low_temp = min(day_data['temps']) if day_data['temps'] else None

                # Find most common condition and description
                conditions = day_data['conditions']
                descriptions = day_data['descriptions']
                most_common_condition = max(set(conditions), key=conditions.count) if conditions else None
                most_common_description = max(set(descriptions), key=descriptions.count) if descriptions else None

                forecast_days.append({
                    'day': 'Today',
                    'date': date_obj.strftime('%B %d'),
                    'high_temp': round(high_temp) if high_temp else None,
                    'low_temp': round(low_temp) if low_temp else None,
                    'condition': most_common_description or most_common_condition,
                    'icon': self._get_openweather_icon(most_common_condition) if most_common_condition else None
                })
                current_conditions_added = True
            else:
                # Today's data not available in API response, try to get current weather
                try:
                    current_weather = self._fetch_current_weather(api_key)
                    if current_weather:
                        forecast_days.append(current_weather)
                        current_conditions_added = True
                except Exception as e:
                    logger.warning(f"Could not fetch current weather for today: {e}")

            # Then add the next 3 days from forecast data
            forecast_count = 0
            for date_str, day_data in sorted(daily_data.items()):
                # Skip today if we already added it
                if date_str == current_date and current_conditions_added:
                    continue

                if forecast_count >= 3:  # Limit to 3 additional days (or 4 if no today data)
                    break

                forecast_count += 1

                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                high_temp = max(day_data['temps']) if day_data['temps'] else None
                low_temp = min(day_data['temps']) if day_data['temps'] else None

                # Get the most common condition
                from collections import Counter
                most_common_condition = Counter(day_data['conditions']).most_common(1)[0][0] if day_data['conditions'] else 'Unknown'
                avg_humidity = sum(day_data['humidity']) / len(day_data['humidity']) if day_data['humidity'] else None
                avg_wind = sum(day_data['wind_speed']) / len(day_data['wind_speed']) if day_data['wind_speed'] else None

                # Get a representative description
                description = day_data['descriptions'][0] if day_data['descriptions'] else 'Weather data unavailable'

                forecast_days.append({
                    'day': date_obj.strftime('%A'),
                    'date': date_obj.strftime('%B %d'),
                    'high_temp': round(high_temp) if high_temp else None,
                    'low_temp': round(low_temp) if low_temp else None,
                    'condition': most_common_condition,
                    'description': description.capitalize(),
                    'humidity': round(avg_humidity) if avg_humidity else None,
                    'wind_speed': round(avg_wind, 1) if avg_wind else None,
                    'icon': self._get_openweather_icon(most_common_condition)
                })

                if len(forecast_days) >= 4:  # Today + 3 forecast days
                    break

            return {
                'forecast': forecast_days,
                'location': self.location_name,
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'source': 'OpenWeatherMap API',
                'api_required': False
            }

        except Exception as e:
            logger.error(f"Error fetching OpenWeatherMap forecast: {e}")
            return self._get_fallback_atmospheric_forecast()

    def _fetch_current_weather(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Fetch current weather conditions from OpenWeatherMap API."""
        try:
            # Construct OpenWeatherMap current weather API URL
            lat = self.gilman_lat
            lon = self.gilman_lon
            url = f"https://api.openweathermap.org/data/2.5/weather"

            params = {
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'imperial'  # Use Fahrenheit for US audience
            }

            response = self.session.get(url, params=params, timeout=self.config.get_request_timeout())
            response.raise_for_status()
            data = response.json()

            # Extract current weather data
            from zoneinfo import ZoneInfo
            location_tz = ZoneInfo(self.config.get_timezone())
            current_date = datetime.now(location_tz)

            condition = data['weather'][0]['main']
            description = data['weather'][0]['description']
            temp = data['main']['temp']
            # For current weather, use current temperature for both high and low
            high_temp = round(temp)
            low_temp = round(temp)

            return {
                'day': 'Today',
                'date': current_date.strftime('%B %d'),
                'high_temp': high_temp,
                'low_temp': low_temp,
                'condition': description.title(),
                'icon': self._get_openweather_icon(condition)
            }

        except Exception as e:
            logger.error(f"Error fetching current weather from OpenWeatherMap: {e}")
            return None

    def _get_openweather_icon(self, condition: str) -> Optional[str]:
        """Convert OpenWeatherMap condition to icon name."""
        icon_map = {
            'Clear': '☀️',
            'Clouds': '☁️',
            'Rain': '🌧️',
            'Drizzle': '🌦️',
            'Thunderstorm': '⛈️',
            'Snow': '❄️',
            'Mist': '🌫️',
            'Fog': '🌫️',
            'Haze': '🌫️',
            'Dust': '🌫️',
            'Sand': '🌫️',
            'Ash': '🌋',
            'Squall': '💨',
            'Tornado': '🌪️'
        }
        return icon_map.get(condition)

    def _download_clearsky_chart(self, output_dir: Path) -> Dict[str, Any]:
        """Download Clear Sky Chart image directly to target directory."""
        if self.skip_network:
            logger.info("Skipping Clear Sky Chart download (offline mode)")
            return {}

        try:
            # Get Clear Sky chart configuration
            clearsky_config = self.config.get_clearsky_config()
            chart_url = f"{clearsky_config.get('base_url', 'https://www.cleardarksky.com/c/')}{clearsky_config.get('station', 'LtBlrTsWIcsk.gif')}?c=1036836"

            # Use consistent filename for rsync compatibility, save directly in target directory
            local_filename = "clearsky_chart.gif"
            local_path = output_dir / local_filename

            # Download the image
            response = self.session.get(chart_url, timeout=self.config.get_request_timeout())
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded Clear Sky Chart to {local_path} ({len(response.content)} bytes)")

            # Return local path info with cache-busting parameter
            current_time = datetime.now(timezone.utc)
            cache_bust = int(current_time.timestamp())

            return {
                'local_filename': local_filename,
                'local_path': f"{local_filename}?v={cache_bust}",
                'title': clearsky_config.get('title', f'Clear Sky Chart for {self.location_name}'),
                'alt': '48-hour astronomical observing forecast'
            }

        except Exception as e:
            logger.error(f"Failed to download Clear Sky Chart: {e}")
            return {}

    def get_weather_data(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Get complete weather data (current + forecast)."""
        current_date = datetime.now(timezone.utc)

        # Get today's sunrise/sunset for the Current Sky View section
        sun_times = self._get_sunrise_sunset(current_date)

        # Get moon data for the Current Sky View section
        moon_data = self._get_moon_data(current_date)

        # Get atmospheric weather forecast
        atmospheric_forecast = self._get_atmospheric_forecast()

        # Add Clear Sky chart if enabled
        clearsky_data = {}
        display_config = self.config.get_display_config()
        if display_config.get('show_clearsky_chart', True):
            if output_dir:
                # Download the image locally
                clearsky_data = self._download_clearsky_chart(output_dir)
            else:
                # Fallback to remote URL if no output directory provided
                clearsky_config = self.config.get_clearsky_config()
                clearsky_data = {
                    'url': f"{clearsky_config.get('base_url', 'https://www.cleardarksky.com/c/')}{clearsky_config.get('station', 'LtBlrTsWIcsk.gif')}?c=1036836",
                    'title': clearsky_config.get('title', f'Clear Sky Chart for {self.location_name}'),
                    'alt': '48-hour astronomical observing forecast'
                }

        # Calculate day and night durations
        day_duration = None
        night_duration = None
        if sun_times['sunrise'] and sun_times['sunset']:
            # Day duration = sunset - sunrise
            day_seconds = (sun_times['sunset'] - sun_times['sunrise']).total_seconds()
            day_hours = int(day_seconds // 3600)
            day_minutes = int((day_seconds % 3600) // 60)
            day_duration = f"{day_hours}h {day_minutes}m"

            # Night duration = 24h - day_duration
            night_seconds = 24 * 3600 - day_seconds
            night_hours = int(night_seconds // 3600)
            night_minutes = int((night_seconds % 3600) // 60)
            night_duration = f"{night_hours}h {night_minutes}m"

        return {
                'current': self.get_current_conditions(),
                'forecast': self.get_forecast(),
                'sun_times': {
                    'sunrise': sun_times['sunrise'].isoformat() if sun_times['sunrise'] else None,
                    'sunset': sun_times['sunset'].isoformat() if sun_times['sunset'] else None,
                    'civil_dawn': sun_times['civil_dawn'].isoformat() if sun_times.get('civil_dawn') else None,
                    'civil_dusk': sun_times['civil_dusk'].isoformat() if sun_times.get('civil_dusk') else None,
                    'civil_dawn_tomorrow': sun_times['civil_dawn_tomorrow'].isoformat() if sun_times.get('civil_dawn_tomorrow') else None,
                    'nautical_dawn': sun_times['nautical_dawn'].isoformat() if sun_times.get('nautical_dawn') else None,
                    'nautical_dusk': sun_times['nautical_dusk'].isoformat() if sun_times.get('nautical_dusk') else None,
                    'nautical_dawn_tomorrow': sun_times['nautical_dawn_tomorrow'].isoformat() if sun_times.get('nautical_dawn_tomorrow') else None,
                    'astronomical_dawn': sun_times['astronomical_dawn'].isoformat() if sun_times.get('astronomical_dawn') else None,
                    'astronomical_dusk': sun_times['astronomical_dusk'].isoformat() if sun_times.get('astronomical_dusk') else None,
                    'astronomical_dawn_tomorrow': sun_times['astronomical_dawn_tomorrow'].isoformat() if sun_times.get('astronomical_dawn_tomorrow') else None,
                    'day_duration': day_duration,
                    'night_duration': night_duration,
                    'method': sun_times['method'],
                    'location': self.location_name
                },
                'moon_data': {
                    'moonrise': moon_data['moonrise'].isoformat() if moon_data['moonrise'] else None,
                    'moonset': moon_data['moonset'].isoformat() if moon_data['moonset'] else None,
                    'phase_name': moon_data['phase_name'],
                    'phase_percentage': moon_data['phase_percentage'],
                    'phase_decimal': moon_data['phase_decimal'],
                    'method': moon_data['method'],
                    'location': self.location_name
                },
                'atmospheric': atmospheric_forecast,
                'clearsky_chart': clearsky_data,
                'last_updated': current_date.isoformat(),
                'source': 'NOAA Space Weather Prediction Center'
            }

    def _get_mock_data_for_testing(self) -> Dict[str, Any]:
        """Get mock data for testing when APIs are unavailable."""
        current_time = datetime.now(timezone.utc)

        mock_current = {
            'timestamp': current_time.isoformat(),
            'kp_index': 4.5,
            'aurora_activity': 'Active - Aurora likely visible at high latitudes',
            'solar_wind': {
                'speed': 450,
                'density': 5.2,
                'bz': -2.1,
                'status': 'active'
            },
            'status': 'active'
        }

        mock_forecast = []
        for i in range(3):
            future_time = current_time.timestamp() + (86400 * (i + 1))
            future_date = datetime.fromtimestamp(future_time, tz=timezone.utc)
            kp_values = [4.5, 5.2, 3.8]  # Sample Kp values

            mock_forecast.append({
                'day': future_date.strftime('%A'),
                'date': future_date.strftime('%B %d'),
                'kp_forecast': f"Kp {kp_values[i]:.1f}",
                'aurora_chance': self._get_aurora_activity_level(kp_values[i]),
                'status': 'forecast'
            })

        return {
            'current': mock_current,
            'forecast': mock_forecast,
            'last_updated': current_time.isoformat(),
            'source': 'Mock data for testing'
        }