#!/usr/bin/env python3
"""
Main entry point for the Social Media Transcriber application.
"""
import sys
from pathlib import Path

# Add the project's root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from social_media_transcriber.cli import cli

# Load environment variables from a .env file if it exists
load_dotenv()


def main() -> None:
    """Runs the command-line interface."""
    cli()


if __name__ == "__main__":
    main()