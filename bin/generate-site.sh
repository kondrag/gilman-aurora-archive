#!/bin/bash

# Gilman Skywatch Archive Website Generator
# Convenience script for generating the Gilman, WI skywatch archive website

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default options
OUTPUT_FILE="index.html"
VERBOSE=""
NO_WEATHER=""

# Function to show help
show_help() {
    cat << EOF
Gilman Skywatch Archive Website Generator

Usage: $0 <media_directory> [OPTIONS]

Arguments:
    media_directory    Directory containing AuroraCam_, CloudCam_, SpaceWeather_ files

Options:
    -o, --output FILE      Output HTML filename (default: index.html)
    -v, --verbose          Enable verbose logging
    --no-weather           Skip NOAA weather data (offline mode)
    -h, --help             Show this help message

Examples:
    $0 /home/user/aurora_videos
    $0 /home/user/aurora_videos -o aurora_gallery.html -v
    $0 /home/user/aurora_videos --no-weather

EOF
}

# Parse command line arguments
MEDIA_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --no-weather)
            NO_WEATHER="--no-weather"
            shift
            ;;
        -*)
            echo "Error: Unknown option $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$MEDIA_DIR" ]]; then
                MEDIA_DIR="$1"
            else
                echo "Error: Multiple media directories specified"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if media directory is specified
if [[ -z "$MEDIA_DIR" ]]; then
    echo "Error: Media directory is required"
    show_help
    exit 1
fi

# Check if media directory exists
if [[ ! -d "$MEDIA_DIR" ]]; then
    echo "Error: Media directory does not exist: $MEDIA_DIR"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run the generator
echo "Generating Gilman Skywatch Archive website..."
echo "Media directory: $MEDIA_DIR"
echo "Output file: $OUTPUT_FILE"
echo ""

# Use uv to run the Python script
PYTHONPATH="$PROJECT_DIR/src" uv run python src/main.py "$MEDIA_DIR" --output "$OUTPUT_FILE" $VERBOSE $NO_WEATHER

echo ""
echo "✅ Website generated successfully!"
echo "📁 Output: $MEDIA_DIR/$OUTPUT_FILE"
echo "🌐 Open the file in your browser to view the website."