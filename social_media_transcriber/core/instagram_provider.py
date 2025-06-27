"""
Instagram video provider implementation.
"""

import re
import subprocess
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

from .providers import VideoProvider

logger = logging.getLogger(__name__)

class InstagramProvider(VideoProvider):
    """Instagram video provider using yt-dlp."""
    
    def __init__(self):
        """Initialize Instagram provider."""
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("yt-dlp is required for Instagram support. Install with: pip install yt-dlp")
        except FileNotFoundError:
            raise RuntimeError("yt-dlp is required for Instagram support. Install with: pip install yt-dlp")
    
    @property
    def provider_name(self) -> str:
        """Name of the provider."""
        return "Instagram"
    
    @property
    def supported_domains(self) -> list[str]:
        """List of supported domains for this provider."""
        return [
            'instagram.com',
            'www.instagram.com',
            'm.instagram.com'
        ]
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is an Instagram URL."""
        try:
            # Check if domain is supported
            if not any(domain in url.lower() for domain in self.supported_domains):
                return False
            
            # Additional validation for Instagram URL patterns
            instagram_patterns = [
                r'/p/',                 # /p/ for posts
                r'/reel/',              # /reel/ for Instagram Reels
                r'/tv/',                # /tv/ for IGTV
                r'/stories/',           # /stories/ for Stories
            ]
            
            return any(re.search(pattern, url, re.IGNORECASE) for pattern in instagram_patterns)
            
        except Exception:
            return False
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from Instagram URL."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid Instagram URL: {url}")
        
        try:
            # Pattern for Instagram post/reel/tv IDs
            patterns = [
                r'/p/([a-zA-Z0-9_-]+)',      # /p/ABC123DEF
                r'/reel/([a-zA-Z0-9_-]+)',   # /reel/ABC123DEF
                r'/tv/([a-zA-Z0-9_-]+)',     # /tv/ABC123DEF
                r'/stories/[^/]+/(\d+)',     # /stories/username/1234567890
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # Fall back to using yt-dlp to get the ID
            cmd = ['yt-dlp', '--get-id', '--no-warnings', url]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                video_id = result.stdout.strip()
                if video_id:
                    return video_id
            except subprocess.CalledProcessError:
                pass
            
            # If all else fails, extract the shortcode from the URL
            shortcode_match = re.search(r'/(?:p|reel|tv)/([a-zA-Z0-9_-]+)', url)
            if shortcode_match:
                return shortcode_match.group(1)
            
            raise ValueError(f"Could not extract video ID from URL: {url}")
            
        except Exception as e:
            raise ValueError(f"Could not extract video ID from URL: {url}") from e
    
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download an Instagram video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid Instagram URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For some Instagram URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"instagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"instagram_{video_id}.%(ext)s")
        
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
            for ext in ['mp4', 'webm', 'mkv', 'avi']:
                potential_file = output_dir / f"{stem}.{ext}"
                if potential_file.exists():
                    logger.info(f"Downloaded Instagram video: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading Instagram video {url}: {e}")
            raise RuntimeError(f"Failed to download Instagram video: {e}")
    
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio only from an Instagram video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid Instagram URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For some Instagram URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"instagram_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"instagram_audio_{video_id}.%(ext)s")
        
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
                    logger.info(f"Downloaded Instagram audio: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded audio file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading Instagram audio {url}: {e}")
            raise RuntimeError(f"Failed to download Instagram audio: {e}")
    
    def get_video_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get Instagram video metadata using yt-dlp.
        
        Args:
            url: Instagram video URL
            
        Returns:
            Dictionary containing video metadata
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid Instagram URL: {url}")
        
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            metadata = json.loads(result.stdout)
            
            return {
                'title': metadata.get('title', 'Instagram Post'),
                'video_id': metadata.get('id', self.extract_video_id(url)),
                'uploader': metadata.get('uploader', metadata.get('channel', None)),
                'duration': metadata.get('duration'),
                'description': metadata.get('description'),
                'upload_date': metadata.get('upload_date'),
                'view_count': metadata.get('view_count'),
                'like_count': metadata.get('like_count')
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting Instagram metadata for {url}: {e}")
            # Fall back to basic metadata
            try:
                video_id = self.extract_video_id(url)
                return {
                    'title': f"Instagram_{video_id}",
                    'video_id': video_id,
                    'uploader': None,
                    'duration': None,
                    'description': None
                }
            except Exception:
                return {
                    'title': 'Instagram_Post',
                    'video_id': 'unknown',
                    'uploader': None,
                    'duration': None,
                    'description': None
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Instagram metadata JSON for {url}: {e}")
            video_id = self.extract_video_id(url)
            return {
                'title': f"Instagram_{video_id}",
                'video_id': video_id,
                'uploader': None,
                'duration': None,
                'description': None
            }
        except Exception as e:
            logger.error(f"Unexpected error getting Instagram metadata for {url}: {e}")
            return {
                'title': 'Instagram_Post',
                'video_id': 'unknown',
                'uploader': None,
                'duration': None,
                'description': None
            }
