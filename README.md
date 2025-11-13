# Gilman Skywatch Archive

A static HTML website generator for Gilman, WI Aurora timelapse archives and sky observation videos.

## Overview

The Gilman Skywatch Archive generates a beautiful, responsive website displaying:
- Nighttime Aurora timelapse videos
- Daytime cloud timelapse videos
- Space weather history images
- Current space weather conditions from NOAA
- 7-day archive with proper date sorting

## Features

- **Dark Theme**: Optimized for aurora viewing with a professional dark design
- **Responsive**: Works perfectly on desktop, tablet, and mobile devices
- **Interactive Features**: Enhanced video players, smooth scrolling, and keyboard shortcuts
- **NOAA Integration**: Live space weather data and 3-day forecasts
- **Automatic File Processing**: Smart detection and categorization of media files
- **Portable**: Run from anywhere with any media directory

## Installation

### Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone or download this repository
2. Install dependencies:

```bash
uv sync
```

## Usage

### Basic Usage

Generate a website for a directory containing Aurora media files:

```bash
python -m src.main /path/to/your/media/directory
```

### Convenience Script

Use the provided shell script for easier usage:

```bash
./bin/generate-site.sh /path/to/your/media/directory
```

### Advanced Options

```bash
# Specify output filename
python -m src.main /path/to/media --output gilman_skywatch.html

# Enable verbose logging
python -m src.main /path/to/media --verbose

# Skip network requests (offline mode)
python -m src.main /path/to/media --no-weather

# Using the installed command
aurora-archive /path/to/media/directory

# Using convenience script with options
./bin/generate-site.sh /path/to/media --verbose --output gallery.html
```

## Media File Organization

The script expects files with the following naming pattern in your target directory:

### Video Files
- `AuroraCam_Monday.mp4` - Nighttime aurora timelapse
- `CloudCam_Monday.mp4` - Daytime cloud timelapse
- (Replace `Monday` with any day of the week)

### Space Weather Files
- `SpaceWeather_Monday.gif` - Space weather history image
- (Replace `Monday` with any day of the week)

### Current Snapshot
- `snapshot.jpg` - Current sky view

### Example Directory Structure

```
/aurora_media/
├── AuroraCam_Friday.mp4
├── AuroraCam_Monday.mp4
├── AuroraCam_Saturday.mp4
├── AuroraCam_Sunday.mp4
├── AuroraCam_Thursday.mp4
├── AuroraCam_Tuesday.mp4
├── AuroraCam_Wednesday.mp4
├── CloudCam_Friday.mp4
├── CloudCam_Monday.mp4
├── CloudCam_Saturday.mp4
├── CloudCam_Sunday.mp4
├── CloudCam_Thursday.mp4
├── CloudCam_Tuesday.mp4
├── CloudCam_Wednesday.mp4
├── snapshot.jpg
├── SpaceWeather_Friday.gif
├── SpaceWeather_Monday.gif
├── SpaceWeather_Saturday.gif
├── SpaceWeather_Sunday.gif
├── SpaceWeather_Thursday.gif
├── SpaceWeather_Tuesday.gif
└── SpaceWeather_Wednesday.gif
```

## Generated Website Features

### Current Conditions
- Live Kp index display with color-coded alerts
- Current aurora activity levels
- 3-day aurora forecast from NOAA

### Media Archive
- **7-Day Layout**: Most recent content displayed first
- **Video Players**: HTML5 players with keyboard shortcuts
- **Responsive Grid**: Adapts to any screen size
- **File Information**: Size and timestamp display

### Interactive Features
- **Keyboard Shortcuts**:
  - `Space`: Play/pause videos
  - `Arrow Left/Right`: Seek video ±10 seconds
  - `F`: Toggle fullscreen
  - `M`: Mute/unmute
  - `Alt+1/2/3`: Navigate to sections

## Development

### Project Structure

```
simple_aurora_archive/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI interface
│   ├── file_processor.py    # Media file scanning
│   ├── weather_fetcher.py   # NOAA data integration
│   ├── html_generator.py    # HTML generation
│   └── utils.py             # Utility functions
├── static/
│   ├── css/style.css        # Dark theme styling
│   └── js/scripts.js        # Interactive features
├── templates/
│   └── index.html           # Main template
├── pyproject.toml           # Dependencies and config
└── README.md               # This file
```

### Running in Development

```bash
# Install in development mode
uv pip install -e .

# Run with Python
python -m src.main /path/to/test/media --verbose
```

### Testing

```bash
# Run tests (if implemented)
uv run pytest

# Test with sample directory structure
python -m src.main /path/to/test/files --verbose
```

## Configuration

### Environment Variables

- `UV_HTTP_TIMEOUT`: Request timeout for NOAA API calls (default: 30)
- `LOG_LEVEL`: Default logging level (default: INFO)

### Customization

- **CSS Theme**: Modify `static/css/style.css` for custom styling
- **Template Layout**: Edit `templates/index.html` for different page structure
- **Weather Sources**: Extend `weather_fetcher.py` for additional data sources

## Troubleshooting

### Common Issues

**"No media files found"**
- Ensure files follow the naming convention
- Check directory permissions
- Verify target directory path

**"Network timeout"**
- Use `--no-weather` flag for offline mode
- Check internet connection
- Verify NOAA website accessibility

**"Permission denied"**
- Ensure read access to target directory
- Check write permissions for output file

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python -m src.main /path/to/media --verbose
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Data Sources

- **Space Weather Data**: NOAA Space Weather Prediction Center
- **Weather Forecasts**: NOAA SWPC aurora forecasts
- **Timestamps**: File modification times

## Support

For issues, questions, or feature requests, please create an issue in the repository.