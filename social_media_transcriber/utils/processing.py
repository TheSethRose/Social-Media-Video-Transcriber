# social_media_transcriber/utils/processing.py
"""
Core processing logic for handling video URLs, including downloading,
transcription, and file organization.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from social_media_transcriber.core.downloader import Downloader
from social_media_transcriber.core.transcriber import AudioTranscriber
from social_media_transcriber.utils.file_utils import (
    sanitize_folder_name,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _expand_url(
    url: str, downloader: Downloader, context: List[str]
) -> Generator[Tuple[str, List[str]], None, None]:
    """
    Recursively expands a URL, yielding individual video URLs with their folder context.
    Handles nested structures like channels containing playlists.

    Args:
        url: The URL to expand.
        downloader: An instance of the Downloader class.
        context: The current folder hierarchy (e.g., ["Channel Name"]).

    Yields:
        A tuple containing a video URL and its full folder context path.
    """
    provider = downloader.get_provider(url)
    if not provider:
        logger.warning("No provider found for URL, skipping: %s", url)
        return

    # Use provider-specific method to get content type
    content_type = provider.get_content_type(url)

    if content_type in ("channel", "playlist", "profile"):
        logger.info("Expanding %s: '%s'", content_type, url)
        metadata = provider.get_metadata(url, download=True)
        # Sanitize the title and add it to the current context for the new folder level
        name = sanitize_folder_name(metadata.get("title", f"Unknown {content_type}"))
        new_context = context + [name]

        if "entries" in metadata and metadata["entries"]:
            for entry in metadata["entries"]:
                entry_url = entry.get("webpage_url") or entry.get("url")
                if entry_url:
                    # Recursively expand the entry URL with the new context
                    yield from _expand_url(entry_url, downloader, new_context)
        else:
            logger.warning("'%s' at %s contains no videos.", name, url)
    elif content_type == "video":
        # If it's a single video, yield it with the current context
        yield url, context
    else:
        logger.warning("Unhandled content type '%s' for URL: %s", content_type, url)


def process_urls(
    urls: List[str],
    output_dir: Path,
    transcriber: AudioTranscriber,
    downloader: Downloader,
    max_workers: int = 4
) -> Dict[str, Path]:
    """
    Processes a list of video URLs in parallel, creating structured output.
    """
    results: Dict[str, Path] = {}
    tasks = []
    # Initial expansion of all top-level URLs
    for url in urls:
        tasks.extend(list(_expand_url(url, downloader, [])))

    total_tasks = len(tasks)
    logger.info("Found %d total videos to process across all sources.", total_tasks)

    if not total_tasks:
        return {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(
                _process_single_url,
                url,
                context_path,
                output_dir,
                downloader,
                transcriber
            ): (url, context_path)
            for url, context_path in tasks
        }

        for i, future in enumerate(as_completed(future_to_task)):
            task_url, context = future_to_task[future]
            try:
                result_path = future.result()
                if result_path:
                    logger.info(
                        "SUCCESS (%d/%d): %s -> %s",
                        i + 1, total_tasks, task_url, result_path
                    )
                    results[task_url] = result_path
                else:
                    logger.error("FAILURE (%d/%d): %s", i + 1, total_tasks, task_url)

            except Exception as exc:
                logger.exception(
                    "ERROR (%d/%d): %s generated an exception: %s",
                    i + 1, total_tasks, task_url, exc
                )
    return results


def _process_single_url(
    url: str,
    context_path: List[str],
    base_output_dir: Path,
    downloader: Downloader,
    transcriber: AudioTranscriber
) -> Optional[Path]:
    """
    Worker function to process a single video URL.
    """
    provider = downloader.get_provider(url)
    if not provider:
        return None

    # Determine the target directory from the context path
    if context_path:
        # Join context parts to form a nested folder structure (e.g., "Channel/Playlist")
        target_dir = base_output_dir.joinpath(*context_path)
    else:
        # Fallback for single videos not in any context
        target_dir = base_output_dir / "unsorted"

    target_dir.mkdir(parents=True, exist_ok=True)

    # Use the provider to download audio, which now handles naming.
    # The provider needs the video title for this.
    try:
        metadata = provider.get_metadata(url, download=False)
        audio_file = provider.download_audio(url, target_dir, metadata)
    except Exception as e:
        logger.error("Failed to download audio for %s: %s", url, e)
        return None


    # Transcribe audio and clean up
    transcript_path = audio_file.with_suffix(".txt")
    transcribed_file = transcriber.transcribe_audio(audio_file, transcript_path)
    audio_file.unlink()

    return transcribed_file