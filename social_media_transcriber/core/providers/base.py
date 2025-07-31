# social_media_transcriber/core/providers/base.py
"""
Abstract base classes and core provider implementations for video platforms.
"""

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import yt_dlp
from social_media_transcriber.utils.file_utils import sanitize_folder_name

# Configure logging
logger = logging.getLogger(__name__)


class VideoProvider(ABC):
    """
    Abstract base class for a video provider.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Gets the name of the provider."""
        raise NotImplementedError

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """Validates if the given URL is supported by this provider."""
        raise NotImplementedError
    
    @abstractmethod
    def get_content_type(self, url: str) -> str:
        """
        Determines the type of content the URL points to.

        Returns:
            A string like "video", "playlist", "channel", "profile", or "unknown".
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self, url: str, download: bool = True) -> Dict[str, Any]:
        """Retrieves metadata for a given URL."""
        raise NotImplementedError

    @abstractmethod
    def download_audio(self, url: str, output_path: Path, metadata: Dict[str, Any]) -> Path:
        """
        Downloads the audio from a URL to the specified path, using metadata for naming.
        """
        raise NotImplementedError


class BaseYtDlpProvider(VideoProvider):
    """
    A base provider that uses yt-dlp to handle all core operations.
    """

    def __init__(self) -> None:
        """Initializes the yt-dlp provider."""
        self._ydl_extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': True,  # Use 'flat' to quickly get playlist/channel entries
        }
        self._ydl_download_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}],
        }

    @property
    @abstractmethod
    def supported_pattern(self) -> str:
        """A regex pattern to match supported URLs for this provider."""
        raise NotImplementedError

    def validate_url(self, url: str) -> bool:
        """Validates if the URL matches the provider's supported domain and pattern."""
        return bool(re.search(self.supported_pattern, url))

    def get_metadata(self, url: str, download: bool = True) -> Dict[str, Any]:
        """Retrieves metadata using yt-dlp."""
        try:
            with yt_dlp.YoutubeDL(self._ydl_extract_opts) as ydl:
                info = ydl.extract_info(url, download=download)
                if not info:
                    raise RuntimeError(f"Could not extract metadata for URL: {url}")
                return info
        except yt_dlp.utils.DownloadError as e:
            logger.error("yt-dlp failed to get metadata for %s: %s", url, e)
            raise RuntimeError(f"Metadata extraction failed for {url}") from e

    def download_audio(self, url: str, output_path: Path, metadata: Dict[str, Any]) -> Path:
        """Downloads audio using yt-dlp and names it based on video title."""
        video_title = metadata.get("title", "Unknown Video")
        sanitized_title = sanitize_folder_name(video_title)  # Re-use sanitizer for file names
        
        # Define a clean output filename using the title.
        output_template = str(output_path / f"{sanitized_title}.%(ext)s")
        
        opts = self._ydl_download_opts.copy()
        opts['outtmpl'] = output_template

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                # The final path will be the sanitized title with a .wav extension
                expected_file = output_path / f"{sanitized_title}.wav"
                if not expected_file.exists():
                    # Fallback for rare cases where title is not available/usable
                    files = list(output_path.glob("*.wav"))
                    if not files:
                        raise RuntimeError("Audio file was not created after download.")
                    return files[0]
                return expected_file
        except yt_dlp.utils.DownloadError as e:
            logger.error("yt-dlp failed to download audio for %s: %s", url, e)
            raise RuntimeError(f"Audio download failed for {url}") from e