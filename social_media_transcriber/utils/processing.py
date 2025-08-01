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
from social_media_transcriber.utils.llm_utils import enhance_transcript_with_llm, format_mdx_with_prettier

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

    # Create processing directory for intermediate files
    processing_dir = base_output_dir.parent / "processing"
    if context_path:
        processing_target_dir = processing_dir.joinpath(*context_path)
        final_output_dir = base_output_dir.joinpath(*context_path)
    else:
        processing_target_dir = processing_dir / "unsorted"
        final_output_dir = base_output_dir / "unsorted"

    processing_target_dir.mkdir(parents=True, exist_ok=True)
    final_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        metadata = provider.get_metadata(url, download=True)
        # Download to processing directory
        downloaded_file = provider.download_audio(url, processing_target_dir, metadata)
    except Exception as e:
        logger.error("Failed to download audio/transcript for %s: %s", url, e)
        return None

    # Check if we got a transcript file (from YouTube transcript extraction)
    # or an audio file (needs transcription)
    is_transcript_file = downloaded_file.suffix == '.txt' and 'transcript' in downloaded_file.name
    intermediate_transcript_file = None  # Initialize for cleanup
    
    if is_transcript_file:
        # We already have a transcript file, no need for audio transcription
        logger.info("Using extracted transcript file: %s", downloaded_file)
        title = metadata.get('title', 'Unknown Video')
        
        # Read the transcript content
        with downloaded_file.open('r', encoding='utf-8') as f:
            raw_text = f.read()
        
        # Determine the final output file path
        if enhance_transcript and settings and settings.llm_api_key:
            final_file = final_output_dir / f"{downloaded_file.stem.replace('_transcript', '')}.mdx"
        else:
            final_file = final_output_dir / f"{downloaded_file.stem.replace('_transcript', '')}.txt"
    else:
        # We have an audio file, need to transcribe it
        logger.info("Transcribing audio file: %s", downloaded_file)
        
        # Create intermediate transcript file in processing directory
        processing_transcript_path = downloaded_file.with_suffix('.txt')
        intermediate_transcript_file, title = transcriber.transcribe_audio(downloaded_file, processing_transcript_path)
        
        # Read the transcribed content
        with intermediate_transcript_file.open('r', encoding='utf-8') as f:
            raw_text = f.read()
            
        # Determine the final output file path
        if enhance_transcript and settings and settings.llm_api_key:
            final_file = final_output_dir / f"{downloaded_file.stem}.mdx"
        else:
            final_file = final_output_dir / f"{downloaded_file.stem}.txt"

    # --- UPDATED: Enhancement and Formatting Logic ---
    if enhance_transcript and settings and settings.llm_api_key:
        try:
            logger.info("Enhancement enabled. API key present: %s", bool(settings.llm_api_key))
            logger.info("Enhancing transcript with LLM: %s", final_file)
            logger.info("Using LLM model: %s", settings.llm_model)
            
            if raw_text.strip():
                logger.info("Raw transcript length: %d characters", len(raw_text))
                enhanced_text = enhance_transcript_with_llm(raw_text, settings, title)
                logger.info("Enhanced transcript length: %d characters", len(enhanced_text))
                
                # Check if text actually changed
                if enhanced_text.strip() == raw_text.strip():
                    logger.warning("LLM returned identical text - no enhancement made")
                else:
                    logger.info("LLM successfully enhanced the transcript")
                
                # Apply Prettier formatting to the enhanced MDX content
                if final_file.suffix.lower() == '.mdx':
                    logger.info("Applying Prettier formatting to MDX file")
                    formatted_text = format_mdx_with_prettier(enhanced_text)
                    if formatted_text != enhanced_text:
                        logger.info("Prettier successfully formatted the MDX content")
                        enhanced_text = formatted_text
                    else:
                        logger.info("No formatting changes needed by Prettier")
                
                with final_file.open('w', encoding='utf-8') as f:
                    f.write(enhanced_text)
                    logger.info("Successfully wrote enhanced transcript to file")
            else:
                logger.warning("Raw transcript is empty, skipping enhancement")
                with final_file.open('w', encoding='utf-8') as f:
                    f.write("")  # Write empty file
        except Exception as e:
            logger.error("Could not enhance transcript %s: %s", final_file, e)
            logger.exception("Full exception traceback:")
            # Fall back to raw text with title
            with final_file.open('w', encoding='utf-8') as f:
                f.write(raw_text)
    else:
         # If enhancement is not enabled, just ensure the raw text is in the file
        with final_file.open('w', encoding='utf-8') as f:
            f.write(raw_text)

    # Clean up files appropriately - everything stays in processing directory
    if is_transcript_file:
        # For transcript files, clean up the original .txt processing file
        if downloaded_file.exists():
            downloaded_file.unlink()
            logger.info("Cleaned up processing transcript file: %s", downloaded_file)
    else:
        # For audio files, clean up the downloaded audio file and intermediate transcript
        if downloaded_file.exists():
            downloaded_file.unlink()
            logger.info("Cleaned up audio file: %s", downloaded_file)
        # Also clean up the intermediate transcript file if it exists
        if intermediate_transcript_file and intermediate_transcript_file.exists():
            intermediate_transcript_file.unlink()
            logger.info("Cleaned up intermediate transcript file: %s", intermediate_transcript_file)
    
    return final_file