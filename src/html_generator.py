"""
HTML generator using Jinja2 templates.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template
import logging

from file_processor import DayMedia, MediaFile
from utils import format_file_size
from config import get_config

logger = logging.getLogger(__name__)

class HTMLGenerator:
    """Generates HTML websites using Jinja2 templates."""

    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"
        self.static_dir = Path(__file__).parent.parent / "static"
        self.config = get_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self):
        """Register custom Jinja2 filters."""
        def format_datetime_filter(dt_str: str) -> str:
            """Format datetime string for display in Gilman, WI local time."""
            try:
                if isinstance(dt_str, str):
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    dt = dt_str

                # Convert to local time using configured timezone
                from zoneinfo import ZoneInfo
                gilman_tz = ZoneInfo(self.config.get_timezone())

                # If datetime is timezone-aware, convert to Chicago time
                if dt.tzinfo is not None:
                    local_dt = dt.astimezone(gilman_tz)
                else:
                    # If datetime is naive, assume it's UTC
                    dt = dt.replace(tzinfo=ZoneInfo("UTC"))
                    local_dt = dt.astimezone(gilman_tz)

                # Format without timezone indicator since it's local time
                time_str = local_dt.strftime('%b %d, %I:%M %p')
                # Remove leading zero from hour (e.g., "06:59 AM" -> "6:59 AM")
                return time_str.replace(' 0', ' ')
            except (ValueError, AttributeError):
                return str(dt_str) if dt_str else "Unknown"

        def format_date_filter(dt) -> str:
            """Format date for display."""
            try:
                if isinstance(dt, str):
                    dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                elif hasattr(dt, 'date'):
                    dt_obj = dt
                else:
                    dt_obj = dt

                return dt_obj.strftime('%B %d, %Y')
            except (ValueError, AttributeError):
                return str(dt) if dt else "Unknown"

        def format_file_size_filter(size: int) -> str:
            """Format file size for display."""
            return format_file_size(size)

        def round_filter(value: float, precision: int = 1) -> float:
            """Round number to specified precision."""
            try:
                return round(value, precision)
            except (TypeError, ValueError):
                return value

        def safe_truncate(text: str, length: int = 50) -> str:
            """Safely truncate text."""
            if not text:
                return ""
            if len(text) <= length:
                return text
            return text[:length] + "..."

        def cache_buster_filter(media_file) -> str:
            """Add cache-busting parameter to media file URLs."""
            if not media_file or not hasattr(media_file, 'file_date'):
                if hasattr(media_file, 'path') and hasattr(media_file.path, 'name'):
                    return media_file.path.name
                elif hasattr(media_file, 'path'):
                    return str(media_file.path)
                else:
                    return ""

            # Use file modification timestamp as cache buster
            cache_bust = int(media_file.file_date.timestamp())
            if hasattr(media_file.path, 'name'):
                return f"{media_file.path.name}?v={cache_bust}"
            else:
                return f"{media_file.path}?v={cache_bust}"

        def cache_bust_thumbnail_filter(thumbnail_path) -> str:
            """Add cache-busting parameter to thumbnail paths."""
            if not thumbnail_path:
                return ""

            try:
                # Convert to string path
                path_str = str(thumbnail_path)

                # Get the actual file path to check modification time
                if hasattr(thumbnail_path, 'name'):
                    # It's a Path object, try to get modification time
                    full_path = self.static_dir.parent / thumbnail_path
                    if full_path.exists():
                        import os
                        cache_bust = int(os.path.getmtime(full_path))
                        return f"{thumbnail_path}?v={cache_bust}"
                    else:
                        # Fallback: use current timestamp
                        import time
                        cache_bust = int(time.time())
                        return f"{thumbnail_path}?v={cache_bust}"
                else:
                    # It's already a string path
                    full_path = self.static_dir.parent / thumbnail_path
                    if full_path.exists():
                        import os
                        cache_bust = int(os.path.getmtime(full_path))
                        return f"{thumbnail_path}?v={cache_bust}"
                    else:
                        # Fallback: use current timestamp
                        import time
                        cache_bust = int(time.time())
                        return f"{thumbnail_path}?v={cache_bust}"
            except Exception:
                # If anything goes wrong, return the path without cache busting
                return str(thumbnail_path)

        def get_moon_phase_icon(phase_decimal: float = None, phase_name: str = None) -> str:
            """Get Unicode moon phase icon based on phase decimal or phase name."""
            if phase_decimal is not None:
                # Use phase_decimal (0-1) where 0 is new moon, 0.5 is full moon
                phase = phase_decimal % 1.0  # Normalize to 0-1 range
                if phase < 0.03 or phase > 0.97:
                    return "🌑"  # New Moon
                elif phase < 0.22:
                    return "🌒"  # Waxing Crescent
                elif phase < 0.28:
                    return "🌓"  # First Quarter
                elif phase < 0.47:
                    return "🌔"  # Waxing Gibbous
                elif phase < 0.53:
                    return "🌕"  # Full Moon
                elif phase < 0.72:
                    return "🌖"  # Waning Gibbous
                elif phase < 0.78:
                    return "🌗"  # Last Quarter
                else:
                    return "🌘"  # Waning Crescent
            elif phase_name:
                # Fallback to phase name matching
                phase_name_lower = phase_name.lower()
                if "new" in phase_name_lower:
                    return "🌑"  # New Moon
                elif "waxing crescent" in phase_name_lower:
                    return "🌒"  # Waxing Crescent
                elif "first quarter" in phase_name_lower:
                    return "🌓"  # First Quarter
                elif "waxing gibbous" in phase_name_lower:
                    return "🌔"  # Waxing Gibbous
                elif "full" in phase_name_lower:
                    return "🌕"  # Full Moon
                elif "waning gibbous" in phase_name_lower:
                    return "🌖"  # Waning Gibbous
                elif "last quarter" in phase_name_lower:
                    return "🌗"  # Last Quarter
                elif "waning crescent" in phase_name_lower:
                    return "🌘"  # Waning Crescent
                else:
                    return "🌙"  # Default crescent moon
            else:
                return "🌙"  # Default crescent moon

        # Register filters
        self.env.filters['format_datetime'] = format_datetime_filter
        self.env.filters['format_date'] = format_date_filter
        self.env.filters['format_file_size'] = format_file_size_filter
        self.env.filters['round'] = round_filter
        self.env.filters['truncate'] = safe_truncate
        self.env.filters['cache_bust'] = cache_buster_filter
        self.env.filters['cache_bust_thumbnail'] = cache_bust_thumbnail_filter
        self.env.filters['moon_phase_icon'] = get_moon_phase_icon

        # Store reference for use in template data
        self.get_moon_phase_icon = get_moon_phase_icon

    def _prepare_template_data(self, media_data: List[DayMedia], weather_data: Dict[str, Any],
                              snapshot: Optional[MediaFile] = None) -> Dict[str, Any]:
        """Prepare data for template rendering."""

        # Add moon phase icon to weather data if moon data is available
        if weather_data.get('moon_data'):
            moon_data = weather_data['moon_data']
            if moon_data.get('phase_decimal') is not None:
                moon_data['phase_icon'] = self.get_moon_phase_icon(
                    phase_decimal=moon_data['phase_decimal'],
                    phase_name=moon_data.get('phase_name')
                )
            elif moon_data.get('phase_name'):
                moon_data['phase_icon'] = self.get_moon_phase_icon(
                    phase_name=moon_data['phase_name']
                )
            else:
                moon_data['phase_icon'] = '🌙'  # Default crescent moon

        return {
            'media_data': media_data,
            'weather_data': weather_data,
            'snapshot': snapshot,
            'current_year': datetime.now().year,
            'generation_time': datetime.now().isoformat(),
            'site': {
                'name': self.config.get_site_name(),
                'subtitle': self.config.get('site.subtitle', 'Northern Lights & Sky Timelapse Observatory'),
                'description': self.config.get('site.description', 'Static HTML website generator for Aurora timelapse archive'),
                'author': self.config.get('site.author', 'Gilman Skywatch'),
                'email': self.config.get('site.email', 'admin@gilman-skywatch.local'),
                'location': self.config.get_location_config()
            }
        }

    def _copy_static_files(self, output_dir: Path) -> None:
        """Copy static files to output directory."""
        if not self.static_dir.exists():
            self.logger.warning(f"Static directory does not exist: {self.static_dir}")
            return

        # Create static directory in output location
        output_static_dir = output_dir / "static"

        try:
            # Copy entire static directory structure
            import shutil

            if output_static_dir.exists():
                shutil.rmtree(output_static_dir)
            shutil.copytree(self.static_dir, output_static_dir)

            self.logger.debug(f"Copied static files to {output_static_dir}")

        except Exception as e:
            self.logger.error(f"Failed to copy static files: {e}")

    def _validate_template(self, template_path: Path) -> bool:
        """Validate that template file exists and is readable."""
        if not template_path.exists():
            self.logger.error(f"Template file does not exist: {template_path}")
            return False

        if not template_path.is_file():
            self.logger.error(f"Template path is not a file: {template_path}")
            return False

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    self.logger.error(f"Template file is empty: {template_path}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to read template {template_path}: {e}")
            return False

    def generate_website(self, media_data: List[DayMedia], weather_data: Dict[str, Any],
                         output_path: Path, snapshot: Optional[MediaFile] = None) -> bool:
        """
        Generate the complete website.

        Args:
            media_data: List of days with media content
            weather_data: Weather forecast and current conditions
            output_path: Path where HTML file should be written
            snapshot: Optional current snapshot image

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Generating website at {output_path}")

            # Validate template
            template_path = self.template_dir / "index.html"
            if not self._validate_template(template_path):
                return False

            # Load template
            template = self.env.get_template("index.html")

            # Prepare template data
            template_data = self._prepare_template_data(media_data, weather_data, snapshot)

            # Render HTML
            html_content = template.render(**template_data)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Copy static files
            self._copy_static_files(output_path.parent)

            self.logger.info(f"Website generated successfully: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate website: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return False

    def generate_minimal_website(self, media_data: List[DayMedia], output_path: Path,
                                snapshot: Optional[MediaFile] = None) -> bool:
        """
        Generate a minimal website without weather data (offline mode).

        Args:
            media_data: List of days with media content
            output_path: Path where HTML file should be written
            snapshot: Optional current snapshot image

        Returns:
            True if successful, False otherwise
        """
        # Create minimal weather data
        minimal_weather = {
            'current': {
                'kp_index': None,
                'aurora_activity': 'Offline mode',
                'status': 'offline'
            },
            'forecast': [],
            'last_updated': datetime.now().isoformat(),
            'source': 'Offline mode - no network access'
        }

        return self.generate_website(media_data, minimal_weather, output_path, snapshot)