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
        # Try different browsers for cookies in order of preference
        # Zen browser uses Firefox's cookie storage, but we'll try it specifically first
        self._cookie_browsers = ['zen', 'firefox', 'chrome', 'safari', 'edge']
        self._current_browser_idx = 0
        
        self._ydl_extract_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': True,  # Use 'flat' to quickly get playlist/channel entries
        }
        self._ydl_download_opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}],
        }
        
        # Add browser cookie support
        self._add_cookie_support()

    def _add_cookie_support(self) -> None:
        """Add browser cookie support to yt-dlp options."""
        if self._current_browser_idx < len(self._cookie_browsers):
            browser = self._cookie_browsers[self._current_browser_idx]
            
            # For Zen browser, we need to specify the profile path since it's Firefox-based
            # but has its own profile directory
            if browser == 'zen':
                # Try to find Zen browser profile path (macOS)
                import os
                zen_profile_path = os.path.expanduser("~/Library/Application Support/zen/Profiles")
                if os.path.exists(zen_profile_path):
                    # Find profiles in the Zen directory
                    profiles = [p for p in os.listdir(zen_profile_path) 
                               if os.path.isdir(os.path.join(zen_profile_path, p)) and not p.startswith('.')]
                    if profiles:
                        # Use the first profile found (there's usually just one)
                        profile_name = profiles[0]
                        profile_path = os.path.join(zen_profile_path, profile_name)
                        
                        # Use tuple format for yt-dlp Python API: (browser_name, profile_path)
                        cookie_config = ('firefox', profile_path)
                        self._ydl_extract_opts['cookiesfrombrowser'] = cookie_config
                        self._ydl_download_opts['cookiesfrombrowser'] = cookie_config
                        logger.info("Using cookies from Zen browser profile: %s", profile_name)
                        return
                
                # Fallback to regular firefox if Zen profile not found
                logger.warning("Zen browser profile not found, falling back to Firefox")
                browser = 'firefox'
            
            # Use the correct yt-dlp option format for cookies from browser
            # This is equivalent to --cookies-from-browser BROWSER
            self._ydl_extract_opts['cookiesfrombrowser'] = browser
            self._ydl_download_opts['cookiesfrombrowser'] = browser
            logger.info("Using cookies from %s browser", browser)

    def _try_next_browser(self) -> bool:
        """Try the next browser for cookies. Returns True if another browser is available."""
        self._current_browser_idx += 1
        if self._current_browser_idx < len(self._cookie_browsers):
            self._add_cookie_support()
            return True
        else:
            # Remove cookie support if all browsers failed
            self._ydl_extract_opts.pop('cookiesfrombrowser', None)
            self._ydl_download_opts.pop('cookiesfrombrowser', None)
            logger.warning("All browsers tried for cookies, falling back to no authentication")
            return False

    @property
    @abstractmethod
    def supported_pattern(self) -> str:
        """A regex pattern to match supported URLs for this provider."""
        raise NotImplementedError

    def validate_url(self, url: str) -> bool:
        """Validates if the URL matches the provider's supported domain and pattern."""
        return bool(re.search(self.supported_pattern, url))

    def get_metadata(self, url: str, download: bool = True) -> Dict[str, Any]:
        """Retrieves metadata using yt-dlp, with fallback browser cookie support."""
        max_retries = len(self._cookie_browsers) + 1  # +1 for no-cookie fallback
        
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(self._ydl_extract_opts) as ydl:
                    info = ydl.extract_info(url, download=download)
                    if not info:
                        raise RuntimeError(f"Could not extract metadata for URL: {url}")
                    
                    # Debug: Log the type and structure of info
                    logger.info(f"DEBUG: yt-dlp returned type: {type(info)}")
                    if isinstance(info, list):
                        logger.info(f"DEBUG: List with {len(info)} entries")
                        if info:
                            logger.info(f"DEBUG: First entry keys: {list(info[0].keys())[:10]}")
                    else:
                        logger.info(f"DEBUG: Dict with keys: {list(info.keys())[:10]}")
                    
                    # Handle flat extraction (returns list of entries)
                    if isinstance(info, list):
                        # This is a flat extraction result - create a playlist-like structure
                        if info:
                            # Use the first entry to get playlist info
                            first_entry = info[0]
                            playlist_info = {
                                'title': first_entry.get('playlist_title', first_entry.get('playlist', 'Unknown Playlist')),
                                'entries': info,
                                'playlist_count': len(info),
                                'playlist_id': first_entry.get('playlist_id'),
                                'uploader': first_entry.get('playlist_uploader'),
                                'channel': first_entry.get('playlist_channel'),
                            }
                            logger.info(f"DEBUG: Created playlist structure with {len(info)} entries")
                            return playlist_info
                        else:
                            raise RuntimeError(f"No entries found for URL: {url}")
                    else:
                        # This is a regular extraction result
                        return info
                    
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                
                # Check if it's a bot detection error
                if "Sign in to confirm you're not a bot" in error_msg and attempt < max_retries - 1:
                    logger.warning("Bot detection encountered with %s, trying next browser...", 
                                 self._cookie_browsers[self._current_browser_idx] if self._current_browser_idx < len(self._cookie_browsers) else "no cookies")
                    
                    if not self._try_next_browser():
                        logger.warning("No more browsers to try, attempting without cookies")
                    continue
                    
                # If it's the last attempt or a different error, raise it
                logger.error("yt-dlp failed to get metadata for %s: %s", url, e)
                raise RuntimeError(f"Metadata extraction failed for {url}") from e
                
        # This shouldn't be reached due to the loop logic, but just in case
        raise RuntimeError(f"Could not extract metadata for URL: {url}")

    def download_audio(self, url: str, output_path: Path, metadata: Dict[str, Any]) -> Path:
        """Downloads audio using yt-dlp and names it based on video title."""
        video_title = metadata.get("title", "Unknown Video")
        sanitized_title = sanitize_folder_name(video_title)
        
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Use simple filename template - yt-dlp will handle path resolution
        output_template = f"{sanitized_title}.%(ext)s"
        
        opts = self._ydl_download_opts.copy()
        opts['outtmpl'] = output_template
        
        # Set paths according to yt-dlp best practices
        opts['paths'] = {
            'home': str(output_path),
        }

        max_retries = len(self._cookie_browsers) + 1  # +1 for no-cookie fallback
        
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                    
                    # Find the downloaded file - yt-dlp places it in the home path
                    expected_file = output_path / f"{sanitized_title}.wav"
                    if expected_file.exists():
                        return expected_file
                    
                    # Fallback: search for any .wav file in output directory
                    wav_files = list(output_path.glob("*.wav"))
                    if wav_files:
                        return wav_files[0]
                        
                    raise RuntimeError("Audio file was not created after download.")
                    
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                
                # Check if it's a bot detection error
                if "Sign in to confirm you're not a bot" in error_msg and attempt < max_retries - 1:
                    logger.warning("Bot detection encountered during download with %s, trying next browser...", 
                                 self._cookie_browsers[self._current_browser_idx] if self._current_browser_idx < len(self._cookie_browsers) else "no cookies")
                    
                    if not self._try_next_browser():
                        logger.warning("No more browsers to try, attempting download without cookies")
                    
                    # Update opts with new cookie settings
                    opts = self._ydl_download_opts.copy()
                    opts['outtmpl'] = output_template
                    opts['paths'] = {'home': str(output_path)}
                    continue
                    
                # If it's the last attempt or a different error, raise it
                logger.error("yt-dlp failed to download audio for %s: %s", url, e)
                raise RuntimeError(f"Audio download failed for {url}") from e
                
        # This shouldn't be reached due to the loop logic, but just in case
        raise RuntimeError(f"Audio download failed for {url}")