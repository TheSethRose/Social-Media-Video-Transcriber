"""
Abstract base classes for video providers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List

class VideoProvider(ABC):
    """Abstract base class for video providers (TikTok, YouTube, etc.)."""
    
    @abstractmethod
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download a video from the provider."""
        pass
    
    @abstractmethod
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio from a video."""
        pass
    
    @abstractmethod
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from URL."""
        pass
    
    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """Validate if URL belongs to this provider."""
        pass
    
    @abstractmethod
    def get_video_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get video metadata including title, uploader, etc.
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary containing video metadata with at least:
            - title: Video title
            - video_id: Video ID
            - uploader: Channel/user name (if available)
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider."""
        pass
    
    @property
    @abstractmethod
    def supported_domains(self) -> list[str]:
        """List of supported domains for this provider."""
        pass
    
    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a playlist/channel. Default: False for single-video providers."""
        return False
    
    def extract_video_urls(self, url: str) -> List[str]:
        """Extract individual video URLs from playlist/channel. Default: return single URL."""
        return [url] if self.validate_url(url) else []
    
    def get_playlist_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get playlist metadata including title, uploader, etc.
        Default implementation for providers that don't support playlists.
        
        Args:
            url: Playlist URL
            
        Returns:
            Dictionary containing playlist metadata with at least:
            - title: Playlist title
            - playlist_id: Playlist ID
            - uploader: Channel/user name (if available)
            - video_count: Number of videos (if available)
        """
        return {
            'title': 'Unknown Playlist',
            'playlist_id': 'unknown',
            'uploader': None,
            'description': None,
            'video_count': 0
        }
    
    def get_url_type(self, url: str) -> str:
        """
        Get the type of URL: 'video', 'playlist', 'channel', or 'unknown'.
        Default implementation returns 'video' for valid URLs.
        """
        return 'video' if self.validate_url(url) else 'unknown'
