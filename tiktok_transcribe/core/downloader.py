"""
Video downloader module with provider support.
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from .providers import VideoProvider
from .youtube_provider import YouTubeProvider

class TikTokProvider(VideoProvider):
    """TikTok video provider implementation."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize TikTok provider."""
        self.settings = settings or Settings()
    
    @property
    def provider_name(self) -> str:
        """Name of the provider."""
        return "TikTok"
    
    @property
    def supported_domains(self) -> list[str]:
        """List of supported domains."""
        return ["tiktok.com", "www.tiktok.com", "vm.tiktok.com"]
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is a TikTok URL."""
        return any(domain in url.lower() for domain in self.supported_domains)
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL."""
        pattern = r'tiktok\.com/@[^/]+/video/(\d+)'
        match = re.search(pattern, url)
        return match.group(1) if match else "unknown"
    
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download a TikTok video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
        if output_file is None:
            temp_dir = Path(tempfile.mkdtemp())
            output_file = temp_dir / "video.m4a"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "yt-dlp",
            "-q",
            "-f", self.settings.video_format,
            "-o", str(output_file),
            url
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if not output_file.exists():
            raise FileNotFoundError(f"Download failed: {output_file} not found")
        
        return output_file
    
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio from a TikTok video."""
        video_file = self.download_video(url)
        
        if output_file is None:
            output_file = video_file.parent / "audio.wav"
        
        self._convert_to_wav(video_file, output_file)
        return output_file
    
    def _convert_to_wav(self, input_file: Path, output_file: Path) -> None:
        """Convert audio/video file to WAV format."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_file),
            "-ar", str(self.settings.audio_sample_rate),
            "-ac", str(self.settings.audio_channels),
            "-vn",
            "-acodec", "pcm_s16le",
            str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)

class VideoDownloader:
    """Universal video downloader that supports multiple providers."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the downloader with available providers."""
        self.settings = settings or Settings()
        self.providers = {
            "tiktok": TikTokProvider(self.settings),
            "youtube": YouTubeProvider()
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
