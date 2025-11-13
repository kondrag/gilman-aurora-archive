"""
File processor for scanning and categorizing Aurora media files.
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)

@dataclass
class MediaFile:
    """Represents a media file with metadata."""
    path: Path
    type: str  # 'aurora', 'cloud', 'spaceweather', 'snapshot'
    day: str   # 'Monday', 'Tuesday', etc.
    file_date: datetime
    size: int

@dataclass
class DayMedia:
    """Media content for a specific day."""
    date: datetime
    day_name: str
    aurora_video: Optional[MediaFile] = None
    cloud_video: Optional[MediaFile] = None
    spaceweather_image: Optional[MediaFile] = None

class FileProcessor:
    """Processes and categorizes Aurora media files."""

    # Days of the week in order for sorting
    DAYS_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __init__(self, target_directory: Path):
        self.target_directory = Path(target_directory)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _get_file_date(self, file_path: Path) -> datetime:
        """Get the file modification date in UTC."""
        try:
            # Use file modification time
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime, tz=timezone.utc)
        except (OSError, ValueError) as e:
            self.logger.warning(f"Could not get date for {file_path}: {e}")
            return datetime.now(timezone.utc)

    def _parse_day_from_filename(self, filename: str) -> Optional[str]:
        """Extract day of week from filename."""
        # Pattern: AuroraCam_Monday.mp4, CloudCam_Tuesday.mp4, SpaceWeather_Wednesday.gif
        patterns = [
            r'(?:AuroraCam|CloudCam|SpaceWeather)_([A-Za-z]+)\.(?:mp4|gif)',
            r'([A-Za-z]+)$'  # Fallback for any filename ending with day name
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                day = match.group(1).title()  # Capitalize first letter
                if day in self.DAYS_ORDER:
                    return day

        return None

    def _determine_file_type(self, filename: str) -> Optional[str]:
        """Determine file type from filename."""
        filename_lower = filename.lower()

        if filename_lower.startswith('auroracam') and filename_lower.endswith('.mp4'):
            return 'aurora'
        elif filename_lower.startswith('cloudcam') and filename_lower.endswith('.mp4'):
            return 'cloud'
        elif filename_lower.startswith('spaceweather') and filename_lower.endswith('.gif'):
            return 'spaceweather'
        elif filename_lower == 'snapshot.jpg':
            return 'snapshot'

        return None

    def _scan_files(self) -> List[MediaFile]:
        """Scan directory for media files."""
        media_files = []

        try:
            for file_path in self.target_directory.iterdir():
                if not file_path.is_file():
                    continue

                filename = file_path.name
                file_type = self._determine_file_type(filename)

                if file_type:
                    file_date = self._get_file_date(file_path)
                    day = self._parse_day_from_filename(filename) if file_type != 'snapshot' else None
                    size = file_path.stat().st_size

                    media_file = MediaFile(
                        path=file_path,
                        type=file_type,
                        day=day,
                        file_date=file_date,
                        size=size
                    )
                    media_files.append(media_file)
                    self.logger.debug(f"Found {file_type} file: {filename}")

        except OSError as e:
            self.logger.error(f"Error scanning directory {self.target_directory}: {e}")

        return media_files

    def _group_files_by_day(self, media_files: List[MediaFile]) -> Dict[str, DayMedia]:
        """Group media files by day of the week."""
        days_media = {}
        current_snapshot = None

        # First pass: handle snapshot and initialize days
        for media_file in media_files:
            if media_file.type == 'snapshot':
                current_snapshot = media_file
            elif media_file.day:
                days_media[media_file.day] = DayMedia(
                    date=media_file.file_date,
                    day_name=media_file.day
                )

        # Second pass: assign media to days
        for media_file in media_files:
            if media_file.day and media_file.day in days_media:
                day_media = days_media[media_file.day]

                if media_file.type == 'aurora':
                    day_media.aurora_video = media_file
                elif media_file.type == 'cloud':
                    day_media.cloud_video = media_file
                elif media_file.type == 'spaceweather':
                    day_media.spaceweather_image = media_file

        # Store snapshot reference if found
        if current_snapshot:
            days_media['_snapshot'] = current_snapshot

        return days_media

    def _sort_days_by_recency(self, days_media: Dict[str, DayMedia]) -> List[DayMedia]:
        """Sort days by recency (most recent first)."""
        # Filter out the snapshot key
        day_items = [(k, v) for k, v in days_media.items() if k != '_snapshot']

        # Sort by file date (most recent first)
        day_items.sort(key=lambda x: x[1].date, reverse=True)

        return [day_media for _, day_media in day_items]

    def process_files(self) -> Tuple[List[DayMedia], Optional[MediaFile]]:
        """
        Process all media files in the target directory.

        Returns:
            Tuple of (sorted_days_list, snapshot_file)
        """
        self.logger.info(f"Scanning for media files in {self.target_directory}")

        media_files = self._scan_files()

        if not media_files:
            self.logger.warning("No media files found")
            return [], None

        self.logger.info(f"Found {len(media_files)} media files")

        days_media = self._group_files_by_day(media_files)

        # Extract snapshot if available
        snapshot = days_media.pop('_snapshot', None)

        # Sort days by recency
        sorted_days = self._sort_days_by_recency(days_media)

        self.logger.info(f"Processed {len(sorted_days)} days of content")

        return sorted_days, snapshot