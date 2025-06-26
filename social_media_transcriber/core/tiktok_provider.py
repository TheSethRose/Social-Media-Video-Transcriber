"""
TikTok video provider implementation.
"""

import re
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from .providers import VideoProvider

logger = logging.getLogger(__name__)

class TikTokProvider(VideoProvider):
    """TikTok video provider using yt-dlp."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize TikTok provider."""
        self.settings = settings or Settings()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("yt-dlp is required for TikTok support. Install with: pip install yt-dlp")
        except FileNotFoundError:
            raise RuntimeError("yt-dlp is required for TikTok support. Install with: pip install yt-dlp")
    
    @property
    def provider_name(self) -> str:
        """Name of the provider."""
        return "TikTok"
    
    @property
    def supported_domains(self) -> list[str]:
        """List of supported domains for this provider."""
        return [
            'tiktok.com',
            'www.tiktok.com',
            'vm.tiktok.com',
            'm.tiktok.com'
        ]
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is a TikTok URL."""
        try:
            return any(domain in url.lower() for domain in self.supported_domains)
        except Exception:
            return False
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
        try:
            # Pattern for regular TikTok videos: @username/video/1234567890
            pattern = r'tiktok\.com/@[^/]+/video/(\d+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            
            # Pattern for short URLs: vm.tiktok.com/abc123
            pattern = r'vm\.tiktok\.com/([a-zA-Z0-9]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            
            # Fall back to using yt-dlp to get the ID
            cmd = ['yt-dlp', '--get-id', '--no-warnings', url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_id = result.stdout.strip()
            if video_id:
                return video_id
            
            raise ValueError(f"Could not extract video ID from URL: {url}")
            
        except Exception as e:
            raise ValueError(f"Could not extract video ID from URL: {url}") from e
    
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download a TikTok video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For some TikTok URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"tiktok_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"tiktok_{video_id}.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '-f', 'best[height<=720]',  # Prefer 720p or lower for efficiency
            '-o', str(output_file),
            '--no-warnings',
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Find the actual output file (yt-dlp resolves the extension)
            output_dir = output_file.parent if output_file.parent != Path('.') else Path.cwd()
            stem = output_file.stem.replace('.%(ext)s', '')
            
            # Look for the downloaded file
            for ext in ['mp4', 'mov', 'webm', 'mkv', 'avi']:
                potential_file = output_dir / f"{stem}.{ext}"
                if potential_file.exists():
                    logger.info(f"Downloaded TikTok video: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading TikTok video {url}: {e}")
            raise RuntimeError(f"Failed to download TikTok video: {e}")
    
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio only from a TikTok video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For some TikTok URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"tiktok_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"tiktok_audio_{video_id}.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '-x',  # Extract audio
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '-o', str(output_file),
            '--no-warnings',
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Find the actual output file
            output_dir = output_file.parent if output_file.parent != Path('.') else Path.cwd()
            stem = output_file.stem.replace('.%(ext)s', '')
            
            # Look for the downloaded audio file
            for ext in ['mp3', 'wav', 'aac', 'm4a']:
                potential_file = output_dir / f"{stem}.{ext}"
                if potential_file.exists():
                    logger.info(f"Downloaded TikTok audio: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded audio file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading TikTok audio {url}: {e}")
            raise RuntimeError(f"Failed to download TikTok audio: {e}")
