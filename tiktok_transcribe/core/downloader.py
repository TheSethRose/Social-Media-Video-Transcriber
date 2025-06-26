"""
Video downloader module with provider support.
"""

from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from .providers import VideoProvider
from .youtube_provider import YouTubeProvider
from .tiktok_provider import TikTokProvider
from .facebook_provider import FacebookProvider
from .instagram_provider import InstagramProvider

"""
Video downloader module with provider support.
"""

from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from .providers import VideoProvider
from .youtube_provider import YouTubeProvider
from .tiktok_provider import TikTokProvider
from .facebook_provider import FacebookProvider
from .instagram_provider import InstagramProvider

class VideoDownloader:
    """Universal video downloader that supports multiple providers."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the downloader with available providers."""
        self.settings = settings or Settings()
        self.providers = {
            "tiktok": TikTokProvider(self.settings),
            "youtube": YouTubeProvider(),
            "facebook": FacebookProvider(),
            "instagram": InstagramProvider()
        }
    
    def get_provider(self, url: str) -> VideoProvider:
        """Get the appropriate provider for a URL."""
        for provider in self.providers.values():
            if provider.validate_url(url):
                return provider
        
        raise ValueError(f"No supported provider found for URL: {url}")
    
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download a video using the appropriate provider."""
        provider = self.get_provider(url)
        return provider.download_video(url, output_file)
    
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio using the appropriate provider."""
        provider = self.get_provider(url)
        return provider.download_audio_only(url, output_file)
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID using the appropriate provider."""
        provider = self.get_provider(url)
        return provider.extract_video_id(url)

# Backward compatibility alias
TikTokDownloader = VideoDownloader
