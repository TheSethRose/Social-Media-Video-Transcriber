"""
Facebook video provider implementation.
"""

import re
import subprocess
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

from .providers import VideoProvider

logger = logging.getLogger(__name__)

class FacebookProvider(VideoProvider):
    """Facebook video provider using yt-dlp."""
    
    def __init__(self):
        """Initialize Facebook provider."""
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("yt-dlp is required for Facebook support. Install with: pip install yt-dlp")
        except FileNotFoundError:
            raise RuntimeError("yt-dlp is required for Facebook support. Install with: pip install yt-dlp")
    
    @property
    def provider_name(self) -> str:
        """Name of the provider."""
        return "Facebook"
    
    @property
    def supported_domains(self) -> list[str]:
        """List of supported domains for this provider."""
        return [
            'facebook.com',
            'www.facebook.com',
            'm.facebook.com',
            'fb.watch'
        ]
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is a Facebook URL."""
        try:
            # Check if domain is supported
            if not any(domain in url.lower() for domain in self.supported_domains):
                return False
            
            # Additional validation for Facebook URL patterns
            facebook_patterns = [
                r'/videos?/',           # /video/ or /videos/
                r'/watch/',             # /watch/
                r'/reel/',              # /reel/ for Facebook Reels
                r'fb\.watch/',          # fb.watch short URLs
                r'/posts/',             # /posts/ (some videos are in posts)
                r'/story\.php'          # story.php (some video content)
            ]
            
            return any(re.search(pattern, url, re.IGNORECASE) for pattern in facebook_patterns)
            
        except Exception:
            return False
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from Facebook URL."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid Facebook URL: {url}")
        
        try:
            # Pattern for Facebook video IDs in various formats
            patterns = [
                r'/videos?/(\d+)',                    # /video/1234567890 or /videos/1234567890
                r'/watch/?\?v=(\d+)',                 # /watch?v=1234567890
                r'/reel/(\d+)',                       # /reel/1234567890
                r'fb\.watch/([a-zA-Z0-9_-]+)',       # fb.watch/abc123
                r'/posts/(\d+)',                      # /posts/1234567890
                r'story_fbid=(\d+)',                  # story_fbid=1234567890
                r'/(\d+)/videos/(\d+)',               # /page_id/videos/video_id
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    # Return the last group (video ID) for patterns with multiple groups
                    return match.groups()[-1]
            
            # Fall back to using yt-dlp to get the ID
            cmd = ['yt-dlp', '--get-id', '--no-warnings', url]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                video_id = result.stdout.strip()
                if video_id:
                    return video_id
            except subprocess.CalledProcessError:
                pass
            
            # If all else fails, extract any long number from the URL
            number_match = re.search(r'(\d{10,})', url)
            if number_match:
                return number_match.group(1)
            
            raise ValueError(f"Could not extract video ID from URL: {url}")
            
        except Exception as e:
            raise ValueError(f"Could not extract video ID from URL: {url}") from e
    
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download a Facebook video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid Facebook URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For some Facebook URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"facebook_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"facebook_{video_id}.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '-f', 'sd/hd/best',  # Prefer sd, then hd, then best available for Facebook
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
                    logger.info(f"Downloaded Facebook video: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading Facebook video {url}: {e}")
            raise RuntimeError(f"Failed to download Facebook video: {e}")
    
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio only from a Facebook video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid Facebook URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For some Facebook URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"facebook_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"facebook_audio_{video_id}.%(ext)s")
        
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
                    logger.info(f"Downloaded Facebook audio: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded audio file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading Facebook audio {url}: {e}")
            raise RuntimeError(f"Failed to download Facebook audio: {e}")
    
    def get_video_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get Facebook video metadata using yt-dlp.
        
        Args:
            url: Facebook video URL
            
        Returns:
            Dictionary containing video metadata
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid Facebook URL: {url}")
        
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
                'title': metadata.get('title', 'Facebook Video'),
                'video_id': metadata.get('id', self.extract_video_id(url)),
                'uploader': metadata.get('uploader', metadata.get('channel', None)),
                'duration': metadata.get('duration'),
                'description': metadata.get('description'),
                'upload_date': metadata.get('upload_date'),
                'view_count': metadata.get('view_count'),
                'like_count': metadata.get('like_count')
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting Facebook metadata for {url}: {e}")
            # Fall back to basic metadata
            try:
                video_id = self.extract_video_id(url)
                return {
                    'title': f"Facebook_{video_id}",
                    'video_id': video_id,
                    'uploader': None,
                    'duration': None,
                    'description': None
                }
            except Exception:
                return {
                    'title': 'Facebook_Video',
                    'video_id': 'unknown',
                    'uploader': None,
                    'duration': None,
                    'description': None
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Facebook metadata JSON for {url}: {e}")
            video_id = self.extract_video_id(url)
            return {
                'title': f"Facebook_{video_id}",
                'video_id': video_id,
                'uploader': None,
                'duration': None,
                'description': None
            }
        except Exception as e:
            logger.error(f"Unexpected error getting Facebook metadata for {url}: {e}")
            return {
                'title': 'Facebook_Video',
                'video_id': 'unknown',
                'uploader': None,
                'duration': None,
                'description': None
            }
