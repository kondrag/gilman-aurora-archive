"""
Unit tests for html_generator module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path

from html_generator import HTMLGenerator
from file_processor import DayMedia, MediaFile


class TestHTMLGenerator:
    """Test cases for HTMLGenerator class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.get_timezone.return_value = "America/Chicago"
        config.get.return_value = "test_value"
        return config

    @pytest.fixture
    def html_generator(self, tmp_path):
        """Create HTMLGenerator instance with temporary directories."""
        template_dir = tmp_path / "templates"
        static_dir = tmp_path / "static"
        template_dir.mkdir()
        static_dir.mkdir()

        return HTMLGenerator(template_dir=template_dir)

    def test_init_default_paths(self):
        """Test HTMLGenerator initialization with default paths."""
        with patch('html_generator.get_config') as mock_get_config:
            mock_get_config.return_value = Mock()

            generator = HTMLGenerator()

            assert generator.template_dir.name == "templates"
            assert generator.static_dir.name == "static"
            assert generator.config is not None

    def test_init_custom_paths(self, tmp_path):
        """Test HTMLGenerator initialization with custom paths."""
        template_dir = tmp_path / "custom_templates"
        static_dir = tmp_path / "custom_static"
        template_dir.mkdir()
        static_dir.mkdir()

        with patch('html_generator.get_config') as mock_get_config:
            mock_get_config.return_value = Mock()

            generator = HTMLGenerator(template_dir=template_dir)

            assert generator.template_dir == template_dir
            # Static dir should still be default
            assert generator.static_dir.name == "static"

    @patch('html_generator.Environment')
    def test_setup_jinja_environment(self, mock_env_class, html_generator):
        """Test Jinja2 environment setup."""
        mock_env = Mock()
        mock_env_class.return_value = mock_env

        # Re-initialize to trigger environment setup
        with patch('html_generator.get_config'):
            HTMLGenerator(template_dir=html_generator.template_dir)

        mock_env_class.assert_called_once()

    @patch('html_generator.Path.exists')
    @patch('html_generator.Path.mkdir')
    def test_copy_static_files(self, mock_mkdir, mock_exists, html_generator):
        """Test copying static files."""
        mock_exists.return_value = True

        with patch('shutil.copytree') as mock_copy:
            html_generator.copy_static_files(Path("/output"))

            mock_copy.assert_called_once()

    def test_copy_static_files_source_not_exists(self, html_generator):
        """Test copying static files when source doesn't exist."""
        with patch.object(html_generator.static_dir, 'exists', return_value=False):
            # Should not raise an exception
            html_generator.copy_static_files(Path("/output"))

    @patch('html_generator.Environment')
    @patch('html_generator.get_config')
    def test_generate_index_html(self, mock_get_config, mock_env_class, tmp_path):
        """Test generating index HTML."""
        # Setup mocks
        mock_config = Mock()
        mock_config.get_timezone.return_value = "America/Chicago"
        mock_get_config.return_value = mock_config

        mock_env = Mock()
        mock_template = Mock()
        mock_template.render.return_value = "<html>test content</html>"
        mock_env.get_template.return_value = mock_template
        mock_env_class.return_value = mock_env

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        generator = HTMLGenerator(template_dir=template_dir)

        # Test data
        day_media_list = [
            DayMedia(
                date=datetime(2024, 1, 15, tzinfo=timezone.utc),
                day_name="Monday",
                aurora_video=MediaFile(
                    path=Path("/test/aurora.mp4"),
                    type="aurora",
                    day="Monday",
                    file_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
                    size=1024000
                )
            )
        ]

        weather_data = {
            "current": {"kp_index": 3, "aurora_activity": "Low"},
            "sun_times": {"sunrise": None, "sunset": None},
            "moon_data": {"phase_name": "New Moon", "phase_percentage": 0}
        }

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Generate HTML
        generator.generate_index_html(output_dir, day_media_list, weather_data)

        # Verify template was called with correct data
        mock_template.render.assert_called_once()
        render_args = mock_template.render.call_args[1]

        assert "media_data" in render_args
        assert "weather_data" in render_args
        assert "current_time" in render_args
        assert len(render_args["media_data"]) == 1
        assert render_args["weather_data"]["current"]["kp_index"] == 3

    def test_format_media_data(self, html_generator):
        """Test formatting media data for template."""
        # Test data
        media_file = MediaFile(
            path=Path("/test/aurora.mp4"),
            type="aurora",
            day="Monday",
            file_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            size=1024000
        )

        day_media = DayMedia(
            date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            day_name="Monday",
            aurora_video=media_file
        )

        day_media_list = [day_media]

        # Format data
        formatted_data = html_generator._format_media_data(day_media_list)

        assert len(formatted_data) == 1
        assert "day_name" in formatted_data[0]
        assert "date" in formatted_data[0]
        assert "media_items" in formatted_data[0]

        media_items = formatted_data[0]["media_items"]
        assert len(media_items) == 1
        assert media_items[0]["type"] == "Aurora Cam"
        assert media_items[0]["file_size"] == "1.0 MB"  # Formatted size

    def test_format_media_data_empty(self, html_generator):
        """Test formatting empty media data."""
        formatted_data = html_generator._format_media_data([])
        assert formatted_data == []

    def test_format_media_data_with_thumbnail(self, html_generator):
        """Test formatting media data with thumbnail."""
        # Test data with thumbnail
        media_file = MediaFile(
            path=Path("/test/aurora.mp4"),
            type="aurora",
            day="Monday",
            file_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            size=1024000,
            thumbnail_path=Path("/test/thumbnail.jpg")
        )

        day_media = DayMedia(
            date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            day_name="Monday",
            aurora_video=media_file
        )

        day_media_list = [day_media]

        # Format data
        formatted_data = html_generator._format_media_data(day_media_list)

        media_items = formatted_data[0]["media_items"]
        assert media_items[0]["thumbnail"] == "/test/thumbnail.jpg"

    @patch('html_generator.Path.exists')
    @patch('html_generator.Path.mkdir')
    def test_generate_index_html_output_directory_creation(self, mock_mkdir, mock_exists, html_generator):
        """Test that output directory is created if it doesn't exist."""
        mock_exists.return_value = False

        with patch('html_generator.Environment'):
            # Mock the template rendering
            with patch.object(html_generator, '_format_media_data', return_value=[]):
                html_generator.generate_index_html(
                    Path("/output"),
                    [],
                    {"current": {}, "sun_times": {}, "moon_data": {}}
                )

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_get_media_type_display_name(self, html_generator):
        """Test getting display names for media types."""
        assert html_generator._get_media_type_display_name("aurora") == "Aurora Cam"
        assert html_generator._get_media_type_display_name("cloud") == "Cloud Cam"
        assert html_generator._get_media_type_display_name("spaceweather") == "Space Weather"
        assert html_generator._get_media_type_display_name("snapshot") == "Daily Snapshot"
        assert html_generator._get_media_type_display_name("unknown") == "Unknown"