"""
Utility functions for Simple Aurora Archive.
"""

import logging
import sys
from pathlib import Path

def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"

def get_relative_path(file_path: Path, base_path: Path) -> str:
    """Get relative path from base path."""
    try:
        return str(file_path.relative_to(base_path))
    except ValueError:
        return str(file_path)

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters."""
    import re
    # Replace spaces and special characters with underscores
    safe = re.sub(r'[^\w\-_\.]', '_', filename)
    # Remove consecutive underscores
    safe = re.sub(r'_+', '_', safe)
    # Remove leading/trailing underscores
    safe = safe.strip('_')
    return safe or 'file'