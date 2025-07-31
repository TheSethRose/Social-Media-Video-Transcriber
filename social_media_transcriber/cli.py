# social_media_transcriber/cli.py
"""
Command-line interface for the Social Media Transcriber.

This module provides a unified CLI for all application functionality,
built using the Click library.
"""

import logging
from pathlib import Path
from typing import List, Optional

import click

from social_media_transcriber.config.settings import Settings
from social_media_transcriber.core.downloader import Downloader
from social_media_transcriber.core.transcriber import AudioTranscriber
from social_media_transcriber.utils.file_utils import (
    combine_channel_transcripts,
    load_urls_from_file,
)
from social_media_transcriber.utils.processing import process_urls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli() -> None:
    """
    Social Media Transcriber.

    A tool to download and transcribe videos from YouTube, TikTok, and more.
    """
    # This function is the entry point for the CLI group.
    pass


@cli.command()
@click.argument("urls", nargs=-1)
@click.option(
    "-f", "--file", "file_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a text file containing URLs to process (one per line)."
)
@click.option(
    "-o", "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default="output",
    show_default=True,
    help="Directory to save the transcripts."
)
@click.option(
    "-w", "--max-workers",
    type=int,
    default=4,
    show_default=True,
    help="Number of concurrent threads to use."
)
@click.option(
    "--speed",
    type=float,
    default=3.0,
    show_default=True,
    help="Audio speed multiplier for faster transcription (1.0=normal)."
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output during transcription."
)
def run(
    urls: List[str],
    file_path: Optional[Path],
    output_dir: Path,
    max_workers: int,
    speed: float,
    verbose: bool
) -> None:
    """
    Download and transcribe videos from URLs or a file.

    You can provide one or more URLs directly as arguments or use the --file
    option to specify a text file containing multiple URLs.
    """
    if not urls and not file_path:
        raise click.UsageError("You must provide at least one URL or use the --file option.")

    all_urls = list(urls)
    if file_path:
        all_urls.extend(load_urls_from_file(file_path))

    if not all_urls:
        logger.warning("No URLs to process.")
        return

    logger.info("Starting transcription for %d URL(s).", len(all_urls))
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    settings = Settings(output_dir=output_dir)
    downloader = Downloader()
    transcriber = AudioTranscriber(settings=settings)
    transcriber.set_speed_multiplier(speed)

    # Process URLs
    results = process_urls(
        urls=all_urls,
        output_dir=output_dir,
        transcriber=transcriber,
        downloader=downloader,
        max_workers=max_workers,
    )

    logger.info("--- Processing Complete ---")
    logger.info("Successfully transcribed %d videos.", len(results))
    if len(results) < len(all_urls):
        logger.warning("Failed to transcribe %d videos.", len(all_urls) - len(results))
    logger.info("Output saved to: %s", output_dir.resolve())


@cli.command("combine")
@click.option(
    "-d", "--directory",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default="output",
    show_default=True,
    help="Directory containing the channel/playlist folders to combine."
)
@click.option(
    "-c", "--channel", "channel_name",
    type=str,
    help="Specific channel/playlist folder name to combine (optional)."
)
def combine_transcripts(directory: Path, channel_name: Optional[str]) -> None:
    """Combine multiple transcript files into a single file per channel."""
    logger.info("Combining transcripts in: %s", directory)
    results = combine_channel_transcripts(directory, channel_name)
    if results:
        click.echo(f"\n✅ Successfully created {len(results)} combined transcript files:")
        for channel, file_path in results.items():
            click.echo(f"  📁 {channel} -> {file_path}")
    else:
        click.echo("\n❌ No transcript files were combined.")


if __name__ == "__main__":
    cli()