"""
Unit tests for file_processor module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path

from file_processor import FileProcessor, MediaFile, DayMedia


class TestMediaFile:
    """Test cases for MediaFile dataclass."""

    def test_media_file_creation(self):
        """Test MediaFile creation."""
        test_path = Path("/test/video.mp4")
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)

        media_file = MediaFile(
            path=test_path,
            type="aurora",
            day="Monday",
            file_date=test_date,
            size=1024000
        )

        assert media_file.path == test_path
        assert media_file.type == "aurora"
        assert media_file.day == "Monday"
        assert media_file.file_date == test_date
        assert media_file.size == 1024000
        assert media_file.thumbnail_path is None

    def test_media_file_with_thumbnail(self):
        """Test MediaFile creation with thumbnail."""
        test_path = Path("/test/video.mp4")
        test_thumbnail = Path("/test/thumbnail.jpg")
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)

        media_file = MediaFile(
            path=test_path,
            type="aurora",
            day="Monday",
            file_date=test_date,
            size=1024000,
            thumbnail_path=test_thumbnail
        )

        assert media_file.thumbnail_path == test_thumbnail


class TestDayMedia:
    """Test cases for DayMedia dataclass."""

    def test_day_media_creation(self):
        """Test DayMedia creation."""
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        aurora_file = Mock(spec=MediaFile)

        day_media = DayMedia(
            date=test_date,
            day_name="Monday",
            aurora_video=aurora_file
        )

        assert day_media.date == test_date
        assert day_media.day_name == "Monday"
        assert day_media.aurora_video == aurora_file
        assert day_media.cloud_video is None
        assert day_media.spaceweather_image is None


class TestFileProcessor:
    """Test cases for FileProcessor class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.get_timezone.return_value = "America/Chicago"
        return config

    @pytest.fixture
    def file_processor(self, tmp_path):
        """Create FileProcessor instance with temporary directory."""
        return FileProcessor(tmp_path)

    def test_init(self, tmp_path):
        """Test FileProcessor initialization."""
        processor = FileProcessor(tmp_path)

        assert processor.target_directory == tmp_path
        assert processor.logger is not None
        assert processor.project_root.exists()

    def test_days_order_constant(self):
        """Test DAYS_ORDER constant."""
        expected = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        assert FileProcessor.DAYS_ORDER == expected

    @patch('file_processor.Path.stat')
    @patch('file_processor.Path.exists')
    def test_get_file_size(self, mock_exists, mock_stat, file_processor):
        """Test getting file size."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1024000)

        test_path = Path("/test/file.mp4")
        size = file_processor._get_file_size(test_path)

        assert size == 1024000
        mock_exists.assert_called_once()
        mock_stat.assert_called_once()

    @patch('file_processor.Path.exists')
    def test_get_file_size_not_exists(self, mock_exists, file_processor):
        """Test getting file size for non-existent file."""
        mock_exists.return_value = False

        test_path = Path("/test/file.mp4")
        size = file_processor._get_file_size(test_path)

        assert size == 0

    @patch('file_processor.Path.is_dir')
    @patch('file_processor.Path.exists')
    def test_scan_directory_empty(self, mock_exists, mock_is_dir, file_processor):
        """Test scanning empty directory."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        with patch.object(file_processor.target_directory, 'iterdir', return_value=[]):
            media_files = file_processor.scan_directory()

        assert len(media_files) == 0

    @patch('file_processor.Path.is_dir')
    @patch('file_processor.Path.exists')
    def test_scan_directory_not_exists(self, mock_exists, mock_is_dir, file_processor):
        """Test scanning non-existent directory."""
        mock_exists.return_value = False

        media_files = file_processor.scan_directory()

        assert len(media_files) == 0

    @patch('file_processor.Path.is_dir')
    @patch('file_processor.Path.exists')
    def test_scan_directory_not_directory(self, mock_exists, mock_is_dir, file_processor):
        """Test scanning path that is not a directory."""
        mock_exists.return_value = True
        mock_is_dir.return_value = False

        media_files = file_processor.scan_directory()

        assert len(media_files) == 0

    @patch.object(FileProcessor, '_get_file_size')
    @patch.object(FileProcessor, '_parse_filename')
    @patch('file_processor.Path.is_dir')
    @patch('file_processor.Path.exists')
    def test_scan_directory_with_files(self, mock_exists, mock_is_dir, mock_parse, mock_size, file_processor):
        """Test scanning directory with files."""
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Create mock file path
        mock_file = Mock(spec=Path)
        mock_file.is_file.return_value = True
        mock_file.name = "AuroraCam_Monday.mp4"

        mock_parse.return_value = {
            'type': 'aurora',
            'day': 'Monday',
            'date': datetime(2024, 1, 15, tzinfo=timezone.utc)
        }
        mock_size.return_value = 1024000

        with patch.object(file_processor.target_directory, 'iterdir', return_value=[mock_file]):
            media_files = file_processor.scan_directory()

        assert len(media_files) == 1
        assert media_files[0].type == 'aurora'
        assert media_files[0].day == 'Monday'
        assert media_files[0].size == 1024000

    def test_parse_filename_aurora_cam(self, file_processor):
        """Test parsing AuroraCam filename."""
        filename = "AuroraCam_Monday.mp4"
        result = file_processor._parse_filename(filename)

        assert result['type'] == 'aurora'
        assert result['day'] == 'Monday'
        assert 'date' in result

    def test_parse_filename_cloud_cam(self, file_processor):
        """Test parsing CloudCam filename."""
        filename = "CloudCam_Tuesday.mp4"
        result = file_processor._parse_filename(filename)

        assert result['type'] == 'cloud'
        assert result['day'] == 'Tuesday'
        assert 'date' in result

    def test_parse_filename_spaceweather(self, file_processor):
        """Test parsing SpaceWeather filename."""
        filename = "SpaceWeather_Wednesday.gif"
        result = file_processor._parse_filename(filename)

        assert result['type'] == 'spaceweather'
        assert result['day'] == 'Wednesday'
        assert 'date' in result

    def test_parse_filename_snapshot(self, file_processor):
        """Test parsing snapshot filename."""
        filename = "snapshot.jpg"
        result = file_processor._parse_filename(filename)

        assert result['type'] == 'snapshot'
        assert 'day' == 'Daily'
        assert 'date' in result

    def test_parse_filename_unrecognized(self, file_processor):
        """Test parsing unrecognized filename."""
        filename = "random_file.txt"
        result = file_processor._parse_filename(filename)

        assert result is None

    def test_parse_filename_empty(self, file_processor):
        """Test parsing empty filename."""
        filename = ""
        result = file_processor._parse_filename(filename)

        assert result is None

    def test_get_most_recent_monday(self, file_processor):
        """Test getting most recent Monday."""
        # Test with a known date (2024-01-17 is a Wednesday)
        test_date = datetime(2024, 1, 17, tzinfo=timezone.utc)
        monday = file_processor._get_most_recent_monday(test_date)

        # Should be 2024-01-15 (the Monday before)
        assert monday.year == 2024
        assert monday.month == 1
        assert monday.day == 15
        assert monday.weekday() == 0  # Monday

    def test_get_most_recent_monday_when_is_monday(self, file_processor):
        """Test getting most recent Monday when current day is Monday."""
        # Test with a Monday (2024-01-15 is a Monday)
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        monday = file_processor._get_most_recent_monday(test_date)

        # Should return the same date
        assert monday == test_date.date()

    def test_group_media_by_day_empty(self, file_processor):
        """Test grouping empty media list."""
        result = file_processor.group_media_by_day([])

        assert len(result) == 0

    def test_group_media_by_day_single_file(self, file_processor):
        """Test grouping single media file by day."""
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        media_file = MediaFile(
            path=Path("/test/aurora.mp4"),
            type="aurora",
            day="Monday",
            file_date=test_date,
            size=1024000
        )

        result = file_processor.group_media_by_day([media_file])

        assert len(result) == 1
        assert "2024-01-15" in result
        assert result["2024-01-15"].day_name == "Monday"
        assert result["2024-01-15"].aurora_video == media_file

    def test_group_media_by_day_multiple_files_same_day(self, file_processor):
        """Test grouping multiple media files from same day."""
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        aurora_file = MediaFile(
            path=Path("/test/aurora.mp4"),
            type="aurora",
            day="Monday",
            file_date=test_date,
            size=1024000
        )
        cloud_file = MediaFile(
            path=Path("/test/cloud.mp4"),
            type="cloud",
            day="Monday",
            file_date=test_date,
            size=2048000
        )
        spaceweather_file = MediaFile(
            path=Path("/test/spaceweather.gif"),
            type="spaceweather",
            day="Monday",
            file_date=test_date,
            size=512000
        )

        result = file_processor.group_media_by_day([aurora_file, cloud_file, spaceweather_file])

        assert len(result) == 1
        assert "2024-01-15" in result
        day_media = result["2024-01-15"]
        assert day_media.aurora_video == aurora_file
        assert day_media.cloud_video == cloud_file
        assert day_media.spaceweather_image == spaceweather_file

    def test_group_media_by_day_multiple_files_different_days(self, file_processor):
        """Test grouping multiple media files from different days."""
        monday_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        tuesday_date = datetime(2024, 1, 16, tzinfo=timezone.utc)

        monday_file = MediaFile(
            path=Path("/test/monday.mp4"),
            type="aurora",
            day="Monday",
            file_date=monday_date,
            size=1024000
        )
        tuesday_file = MediaFile(
            path=Path("/test/tuesday.mp4"),
            type="aurora",
            day="Tuesday",
            file_date=tuesday_date,
            size=1024000
        )

        result = file_processor.group_media_by_day([monday_file, tuesday_file])

        assert len(result) == 2
        assert "2024-01-15" in result
        assert "2024-01-16" in result
        assert result["2024-01-15"].day_name == "Monday"
        assert result["2024-01-16"].day_name == "Tuesday"

    def test_group_media_by_day_duplicate_types(self, file_processor):
        """Test grouping when multiple files of same type exist."""
        test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        aurora_file1 = MediaFile(
            path=Path("/test/aurora1.mp4"),
            type="aurora",
            day="Monday",
            file_date=test_date,
            size=1024000
        )
        aurora_file2 = MediaFile(
            path=Path("/test/aurora2.mp4"),
            type="aurora",
            day="Monday",
            file_date=test_date.replace(hour=1),  # One hour later
            size=2048000
        )

        result = file_processor.group_media_by_day([aurora_file1, aurora_file2])

        assert len(result) == 1
        day_media = result["2024-01-15"]
        # Should keep the most recent file (larger file size in this case)
        assert day_media.aurora_video == aurora_file2

    @patch('file_processor.Path.stat')
    @patch('file_processor.Path.exists')
    def test_get_file_size_exception(self, mock_exists, mock_stat, file_processor):
        """Test getting file size when exception occurs."""
        mock_exists.return_value = True
        mock_stat.side_effect = Exception("File system error")

        test_path = Path("/test/file.mp4")
        size = file_processor._get_file_size(test_path)

        assert size == 0

    def test_parse_filename_case_insensitive(self, file_processor):
        """Test parsing filename with different cases."""
        # Test lowercase
        filename = "auroracam_monday.mp4"
        result = file_processor._parse_filename(filename)
        assert result is not None

        # Test mixed case
        filename = "AuroraCam_Monday.mp4"
        result = file_processor._parse_filename(filename)
        assert result is not None
        assert result['type'] == 'aurora'

    def test_get_most_recent_monday_edge_case(self, file_processor):
        """Test getting most recent Monday with edge case dates."""
        # Test with Sunday (should return previous Monday)
        test_date = datetime(2024, 1, 21, tzinfo=timezone.utc)  # Sunday
        monday = file_processor._get_most_recent_monday(test_date)

        assert monday.weekday() == 0  # Monday
        assert monday.day == 15  # Should be the Monday of that week