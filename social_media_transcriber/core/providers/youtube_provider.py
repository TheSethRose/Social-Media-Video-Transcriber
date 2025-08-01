# social_media_transcriber/core/providers/youtube_provider.py
"""YouTube video provider implementation."""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import yt_dlp
from .base import BaseYtDlpProvider

logger = logging.getLogger(__name__)


class YouTubeProvider(BaseYtDlpProvider):
    """Provider for YouTube, supporting videos, playlists, and channels."""

    @property
    def provider_name(self) -> str:
        return "YouTube"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/"

    def get_content_type(self, url: str) -> str:
        """Determines if a YouTube URL is a video, playlist, or channel."""
        if re.search(r"/watch\?v=", url) or re.search(r"youtu\.be/", url):
            return "video"
        if re.search(r"/playlist\?list=", url):
            return "playlist"
        # Match channel URLs like /@channelname, /channel/UC..., /c/channelname
        if re.search(r"/(?:@|channel/|c/)", url):
            return "channel"
        return "unknown"

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        # Regular youtube.com/watch?v=VIDEO_ID
        if match := re.search(r"youtube\.com/watch\?v=([^&]+)", url):
            return match.group(1)
        # Short youtu.be/VIDEO_ID
        if match := re.search(r"youtu\.be/([^?]+)", url):
            return match.group(1)
        # Embedded youtube.com/embed/VIDEO_ID
        if match := re.search(r"youtube\.com/embed/([^?]+)", url):
            return match.group(1)
        # Shortened youtu.be/VIDEO_ID with parameters
        if match := re.search(r"youtu\.be/([^?&]+)", url):
            return match.group(1)
        return None

    def get_youtube_transcript(self, url: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Attempt to extract transcript directly from YouTube.
        Returns tuple of (transcript_text, metadata) if successful, None otherwise.
        """
        try:
            video_id = self.extract_video_id(url)
            if not video_id:
                logger.debug("Could not extract video ID from URL: %s", url)
                return None

            logger.info("Attempting to extract transcript for video ID: %s", video_id)
            
            # Try to get transcript using yt-dlp's built-in transcript capability
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        logger.debug("No info extracted for video: %s", video_id)
                        return None
                    
                    # Check if transcript is available
                    subtitles = info.get('subtitles')
                    if subtitles and isinstance(subtitles, dict):
                        # Try English first, then any available language
                        for lang in ['en', 'en-US', 'en-GB', 'a.en']:
                            if lang in subtitles and subtitles[lang]:
                                subtitle_url = subtitles[lang][0].get('url')
                                if subtitle_url:
                                    import requests
                                    response = requests.get(subtitle_url, timeout=10)
                                    response.raise_for_status()
                                    
                                    # Parse the subtitle content (typically in SRT or VTT format)
                                    transcript_text = self._parse_subtitle_content(response.text)
                                    if transcript_text:
                                        logger.info("Successfully extracted transcript from YouTube subtitles")
                                        return transcript_text, info
                    
                    # Check automatic subtitles if no manual subtitles
                    auto_captions = info.get('automatic_captions')
                    if auto_captions and isinstance(auto_captions, dict):
                        for lang in ['en', 'en-US', 'en-GB']:
                            if lang in auto_captions and auto_captions[lang]:
                                subtitle_url = auto_captions[lang][0].get('url')
                                if subtitle_url:
                                    import requests
                                    response = requests.get(subtitle_url, timeout=10)
                                    response.raise_for_status()
                                    
                                    transcript_text = self._parse_subtitle_content(response.text)
                                    if transcript_text:
                                        logger.info("Successfully extracted transcript from YouTube automatic captions")
                                        return transcript_text, info
                    
                    logger.debug("No transcript available for video: %s", video_id)
                    return None
                    
                except Exception as e:
                    logger.debug("Failed to extract transcript using yt-dlp: %s", e)
                    return None
                    
        except Exception as e:
            logger.debug("Error during transcript extraction: %s", e)
            return None

    def _parse_subtitle_content(self, content: str) -> str:
        """Parse subtitle content (SRT/VTT/JSON format) into plain text."""
        try:
            # Check if content is JSON format (newer YouTube format)
            if content.strip().startswith('{'):
                import json
                data = json.loads(content)
                
                # Extract text from JSON structure
                transcript_lines = []
                if 'events' in data:
                    for event in data['events']:
                        if 'segs' in event:
                            for seg in event['segs']:
                                if 'utf8' in seg:
                                    text = seg['utf8'].strip()
                                    # Skip musical notes and empty content
                                    if text and text != '[♪♪♪]' and text != '[Music]':
                                        transcript_lines.append(text)
                
                return ' '.join(transcript_lines)
            
            # Handle traditional SRT/VTT format
            lines = content.strip().split('\n')
            transcript_lines = []
            
            for line in lines:
                # Skip SRT/VTT metadata and timing lines
                if line.strip() and not line.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-->', 'WEBVTT')):
                    # Remove HTML tags and clean up
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    clean_line = clean_line.strip()
                    if clean_line:
                        transcript_lines.append(clean_line)
            
            return ' '.join(transcript_lines)
            
        except Exception as e:
            logger.debug("Failed to parse subtitle content: %s", e)
            return ""

    def has_available_transcript(self, url: str) -> bool:
        """
        Check if a YouTube video has an available transcript without downloading it.
        Returns True if transcript is available, False otherwise.
        """
        try:
            transcript_result = self.get_youtube_transcript(url)
            if transcript_result:
                transcript_text, _ = transcript_result
                return len(transcript_text.strip()) > 0
            return False
        except Exception as e:
            logger.debug("Error checking transcript availability: %s", e)
            return False

    def download_audio(self, url: str, output_path: Path, metadata: Dict[str, Any]) -> Path:
        """
        Download audio from YouTube URL, trying transcript extraction first.
        If transcript is available, returns transcript file path instead of audio.
        """
        # First try to get transcript directly from YouTube
        transcript_result = self.get_youtube_transcript(url)
        if transcript_result:
            transcript_text, _ = transcript_result
            # Save transcript directly as a text file
            from social_media_transcriber.utils.file_utils import sanitize_folder_name
            
            title = metadata.get('title', 'Unknown')
            safe_title = sanitize_folder_name(title)
            transcript_file = output_path / f"{safe_title}_transcript.txt"
            
            try:
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                
                logger.info("Successfully extracted and saved transcript to: %s", transcript_file)
                logger.info("Skipping audio download - transcript already available")
                return transcript_file
                
            except Exception as e:
                logger.error("Failed to save transcript file: %s", e)
                # Fall back to audio download if transcript saving fails
        
        # Fall back to regular audio download if no transcript available or saving failed
        logger.info("No transcript available, falling back to audio download")
        return super().download_audio(url, output_path, metadata)