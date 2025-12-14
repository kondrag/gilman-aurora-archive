# Aurora Archive Unit Tests

This directory contains unit tests for the Aurora Archive project.

## Test Structure

- `test_weather_fetcher.py` - Tests for weather data fetching functionality
- `test_config.py` - Tests for configuration management
- `test_utils.py` - Tests for utility functions
- `test_file_processor.py` - Tests for file processing and media categorization
- `test_html_generator.py` - Tests for HTML generation functionality

## Running Tests

### Using the test runner (recommended):
```bash
# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py src/test/test_utils.py

# Run specific test method
python run_tests.py src/test/test_utils.py::TestUtils::test_format_file_size_bytes

# Run tests quietly
python run_tests.py --quiet
```

### Using pytest directly:
```bash
# Run all tests
PYTHONPATH=src uv run pytest src/test -v

# Run specific test file
PYTHONPATH=src uv run pytest src/test/test_utils.py -v

# Run specific test method
PYTHONPATH=src uv run pytest src/test/test_utils.py::TestUtils::test_format_file_size_bytes -v
```

## Test Coverage

The tests cover:

### WeatherFetcher (`test_weather_fetcher.py`)
- Initialization and configuration
- Moon data calculation (with astroplan integration)
- Sunrise/sunset calculations
- Fallback data handling
- Network operations (mocked)
- Kp index formatting
- G-scale level calculation

### Config (`test_config.py`)
- Configuration loading from JSON files
- Default values when config file is missing
- Invalid JSON handling
- Individual config methods (get_latitude, get_longitude, etc.)
- Singleton pattern

### Utils (`test_utils.py`)
- File size formatting
- Duration formatting
- Path operations
- Safe filename generation
- Logging setup

### FileProcessor (`test_file_processor.py`)
- Media file and day media dataclasses
- File scanning and categorization
- Filename parsing for different media types
- File size operations
- Date and day handling

### HTMLGenerator (`test_html_generator.py`)
- Template loading and rendering
- Static file copying
- Media data formatting
- Output directory creation

## Writing New Tests

When adding new tests:

1. Follow the existing naming convention: `test_<module_name>.py`
2. Use descriptive test method names: `test_<functionality>_when_<condition>`
3. Use fixtures for common test data
4. Mock external dependencies (network calls, file I/O)
5. Test both success and failure cases
6. Use the `@pytest.mark.unit` decorator for pure unit tests

## Test Dependencies

The tests use:
- `pytest` - Test framework
- `pytest-mock` - Mocking utilities
- `unittest.mock` - Mock objects and patches

## Notes

- Tests are designed to run in isolation without external dependencies
- Network operations are mocked to avoid actual API calls
- File system operations use temporary directories where possible
- The test runner automatically sets up the Python path for imports