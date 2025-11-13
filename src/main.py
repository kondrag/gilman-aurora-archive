#!/usr/bin/env python3
"""
Main entry point for Simple Aurora Archive static website generator.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

from file_processor import FileProcessor
from weather_fetcher import WeatherFetcher
from html_generator import HTMLGenerator
from utils import setup_logging

def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate static HTML website for Aurora timelapse archive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/media/directory
  %(prog)s /home/user/aurora_videos --output index.html
  %(prog)s ./media --verbose
        """
    )

    parser.add_argument(
        "target_directory",
        help="Directory containing AuroraCam_, CloudCam_, SpaceWeather_ files and snapshot.jpg"
    )

    parser.add_argument(
        "--output", "-o",
        default="index.html",
        help="Output HTML filename (default: index.html)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--no-weather",
        action="store_true",
        help="Skip fetching NOAA weather data (useful for offline testing)"
    )

    return parser

def validate_target_directory(target_dir: Path) -> Path:
    """Validate that the target directory exists and is accessible."""
    if not target_dir.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

    if not target_dir.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {target_dir}")

    if not os.access(target_dir, os.R_OK):
        raise PermissionError(f"Cannot read from target directory: {target_dir}")

    return target_dir

def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    try:
        # Validate target directory
        target_dir = Path(args.target_directory).resolve()
        logger.info(f"Processing media directory: {target_dir}")
        validate_target_directory(target_dir)

        # Initialize components
        logger.info("Initializing components...")
        file_processor = FileProcessor(target_dir)
        weather_fetcher = WeatherFetcher(skip_network=args.no_weather)
        html_generator = HTMLGenerator()

        # Process media files
        logger.info("Processing media files...")
        media_data, snapshot = file_processor.process_files()
        if not media_data:
            logger.warning("No media files found in target directory")
            return 1

        logger.info(f"Found {len(media_data)} days of media content")

        # Generate HTML
        logger.info(f"Generating HTML website: {args.output}")
        output_path = target_dir / args.output

        # Fetch weather data (pass output directory so Clear Sky chart can be downloaded locally)
        logger.info("Fetching space weather data...")
        weather_data = weather_fetcher.get_weather_data(output_dir=output_path.parent)
        html_generator.generate_website(
            media_data=media_data,
            weather_data=weather_data,
            output_path=output_path,
            snapshot=snapshot
        )

        logger.info(f"Website generated successfully: {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error generating website: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())