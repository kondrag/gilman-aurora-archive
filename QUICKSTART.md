# Gilman Skywatch Archive - Quick Start Guide

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Clone or download the project
cd gilman_skywatch_archive

# Install dependencies with uv
uv sync
```

### 2. Generate Your First Website

**Method 1: Using the convenience script**
```bash
./bin/generate-site.sh /path/to/your/media/files
```

**Method 2: Using Python directly**
```bash
uv run python src/main.py /path/to/your/media/files
```

### 3. Open the Website
```bash
# Open the generated website in your browser
firefox /path/to/your/media/files/index.html
```

## 📁 Media File Requirements

Your media directory should contain files with these naming patterns:

```
/your_media_directory/
├── AuroraCam_Monday.mp4      # Night timelapse
├── CloudCam_Monday.mp4       # Day timelapse
├── SpaceWeather_Monday.gif   # Space weather history
└── snapshot.jpg             # Current sky view
```

Replace `Monday` with any day of the week. Files are automatically detected and organized by date.

## 🎯 Example Usage

```bash
# Basic usage
./bin/generate-site.sh /home/user/aurora_videos

# With custom output filename
./bin/generate-site.sh /home/user/aurora_videos -o gallery.html

# Verbose output
./bin/generate-site.sh /home/user/aurora_videos --verbose

# Offline mode (no weather data)
./bin/generate-site.sh /home/user/aurora_videos --no-weather
```

## 🌟 What You Get

- **Responsive Website**: Works on desktop, tablet, and mobile
- **Dark Theme**: Professional aurora-viewing optimized design
- **Interactive Features**: Enhanced video players with keyboard shortcuts
- **Live Weather**: Real-time space weather data from NOAA (when online)
- **7-Day Archive**: Automatic sorting by date (newest first)

## 🎮 Keyboard Shortcuts

When viewing the website:
- `Space`: Play/pause videos
- `Arrow Left/Right`: Seek ±10 seconds
- `F`: Toggle fullscreen
- `M`: Mute/unmute
- `Alt+1/2/3`: Navigate to sections

## 🛠️ Troubleshooting

**"No media files found"**
- Check file naming follows the pattern
- Verify directory permissions
- Use `--verbose` for debugging

**Network errors**
- Use `--no-weather` for offline mode
- Check internet connection

For more details, see the full [README.md](README.md).