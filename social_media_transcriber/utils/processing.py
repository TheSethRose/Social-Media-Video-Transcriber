# social_media_transcriber/utils/processing.py
"""
Core processing logic for handling video URLs, including downloading,
transcription, and file organization.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from rich.console import Console
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn,
                           TimeElapsedColumn)

from social_media_transcriber.config.settings import Settings
from social_media_transcriber.core.downloader import Downloader
from social_media_transcriber.core.transcriber import AudioTranscriber
from social_media_transcriber.utils.file_utils import sanitize_folder_name
from social_media_transcriber.utils.llm_utils import enhance_transcript_with_llm

logger = logging.getLogger(__name__)


def _expand_url(
    url: str, downloader: Downloader, context: List[str]
) -> Generator[Tuple[str, List[str]], None, None]:
    # This function is correct and needs no changes.
    provider = downloader.get_provider(url)
    if not provider:
        logger.warning("No provider found for URL, skipping: %s", url)
        return
    content_type = provider.get_content_type(url)
    if content_type == "unknown":
        logger.warning("Skipping URL with unknown content type: %s", url)
        return
    if content_type in ("channel", "playlist", "profile"):
        logger.info("Expanding %s: '%s'", content_type, url)
        try:
            metadata = provider.get_metadata(url, download=True)
            name = sanitize_folder_name(metadata.get("title", f"Unknown {content_type}"))
            new_context = context + [name]
            if "entries" in metadata and metadata["entries"]:
                for entry in metadata["entries"]:
                    entry_url = entry.get("webpage_url") or entry.get("url")
                    if entry_url:
                        yield from _expand_url(entry_url, downloader, new_context)
            else:
                logger.warning("'%s' at %s contains no videos.", name, url)
        except Exception as e:
            logger.error("Failed to expand %s at %s: %s", content_type, url, e)
    elif content_type == "video":
        yield url, context
    else:
        logger.warning("Unhandled content type '%s' for URL: %s", content_type, url)


def process_urls(
    urls: List[str],
    output_dir: Path,
    transcriber: AudioTranscriber,
    downloader: Downloader,
    max_workers: int = 4,
    settings: Optional[Settings] = None,
    enhance_transcript: bool = False,
    console: Optional[Console] = None,
) -> Dict[str, Optional[Path]]:
    """
    Processes a list of URLs, showing a progress bar and returning results.
    """
    results: Dict[str, Optional[Path]] = {}
    tasks = []

    logger.info("Discovering and expanding all video URLs...")
    for url in urls:
        tasks.extend(list(_expand_url(url, downloader, [])))

    total_tasks = len(tasks)
    logger.info("Found %d total videos to process.", total_tasks)
    if not total_tasks:
        return {}

    # Define the progress bar
    progress_bar = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("({task.completed} of {task.total})"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )

    with progress_bar:
        main_task_id = progress_bar.add_task("[yellow]Transcribing...", total=total_tasks)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(
                    _process_single_url,
                    url,
                    context_path,
                    output_dir,
                    downloader,
                    transcriber,
                    settings,
                    enhance_transcript,
                ): (url, context_path)
                for url, context_path in tasks
            }

            for future in as_completed(future_to_task):
                task_url, _ = future_to_task[future]
                try:
                    result_path = future.result()
                    results[task_url] = result_path  # Store path or None for failure
                except Exception as exc:
                    logger.exception("Error processing '%s': %s", task_url, exc)
                    results[task_url] = None  # Store None for exception
                finally:
                    progress_bar.update(main_task_id, advance=1)

    return results


def _process_single_url(
    url: str,
    context_path: List[str],
    base_output_dir: Path,
    downloader: Downloader,
    transcriber: AudioTranscriber,
    settings: Optional[Settings] = None,
    enhance_transcript: bool = False
) -> Optional[Path]:
    """
    Worker function to process a single video URL.
    """
    provider = downloader.get_provider(url)
    if not provider:
        return None

    if context_path:
        target_dir = base_output_dir.joinpath(*context_path)
    else:
        target_dir = base_output_dir / "unsorted"

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        metadata = provider.get_metadata(url, download=True)
        audio_file = provider.download_audio(url, target_dir, metadata)
    except Exception as e:
        logger.error("Failed to download audio for %s: %s", url, e)
        return None

    # Determine the correct final file extension.
    file_extension = ".mdx" if enhance_transcript and settings and settings.llm_api_key else ".txt"
    final_transcript_path = audio_file.with_suffix(file_extension)

    transcribed_file, title = transcriber.transcribe_audio(audio_file, final_transcript_path)

    # --- UPDATED: Enhancement and Formatting Logic ---
    if enhance_transcript and settings and settings.llm_api_key:
        try:
            logger.info("Enhancement enabled. API key present: %s", bool(settings.llm_api_key))
            logger.info("Enhancing transcript with LLM: %s", transcribed_file)
            logger.info("Using LLM model: %s", settings.llm_model)
            with transcribed_file.open('r+', encoding='utf-8') as f:
                raw_text = f.read()
                if raw_text.strip():
                    logger.info("Raw transcript length: %d characters", len(raw_text))
                    enhanced_text = enhance_transcript_with_llm(raw_text, settings, title)
                    logger.info("Enhanced transcript length: %d characters", len(enhanced_text))
                    
                    # Check if text actually changed
                    if enhanced_text.strip() == raw_text.strip():
                        logger.warning("LLM returned identical text - no enhancement made")
                    else:
                        logger.info("LLM successfully enhanced the transcript")
                    
                    f.seek(0)
                    f.write(f"# {title}\n\n{enhanced_text}\n")
                    f.truncate()
                    logger.info("Successfully wrote enhanced transcript to file")
                else:
                    logger.warning("Raw transcript is empty, skipping enhancement")
                    f.seek(0)
                    f.write(f"# {title}\n\n")
                    f.truncate()
        except Exception as e:
            logger.error("Could not enhance transcript %s: %s", transcribed_file, e)
            logger.exception("Full exception traceback:")
            # Fall back to raw text with title
            with transcribed_file.open('r+', encoding='utf-8') as f:
                raw_text = f.read()
                f.seek(0)
                f.write(f"# {title}\n\n{raw_text}")
                f.truncate()
    else:
         # If enhancement is not enabled, just add the title to the raw text.
        with transcribed_file.open('r+', encoding='utf-8') as f:
            raw_text = f.read()
            f.seek(0)
            f.write(f"# {title}\n\n{raw_text}")
            f.truncate()

    audio_file.unlink()
    return transcribed_file