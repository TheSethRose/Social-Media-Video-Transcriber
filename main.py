# main.py
#!/usr/bin/env python3
"""
Main entry point for the Social Media Transcriber application.
"""
import sys
from pathlib import Path

# Add the project's root directory to the Python path to ensure
# that modules can be imported correctly when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from social_media_transcriber.cli import cli


def main() -> None:
    """Runs the command-line interface."""
    cli()


if __name__ == "__main__":
    main()