"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

@pytest.fixture
def sample_datetime():
    """Provide a sample datetime for testing."""
    from datetime import datetime, timezone
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

@pytest.fixture
def sample_path():
    """Provide a sample path for testing."""
    return Path("/test/sample_file.mp4")