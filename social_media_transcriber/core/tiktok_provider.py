"""
TikTok video provider implementation with channel/user profile support.
"""

import re
import subprocess
import tempfile
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..config.settings import Settings
from .providers import VideoProvider

logger = logging.getLogger(__name__)

class TikTokProvider(VideoProvider):
    """TikTok video provider using yt-dlp with support for individual videos and user profiles."""
    
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
        """Validate if URL is a TikTok URL (video or user profile)."""
        try:
            return any(domain in url.lower() for domain in self.supported_domains)
        except Exception:
            return False
    
    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a TikTok user profile (equivalent to a playlist)."""
        if not self.validate_url(url):
            return False
        return self.get_url_type(url) == 'user'
    
    def get_url_type(self, url: str) -> str:
        """
        Determine the type of TikTok URL.
        
        Returns:
            'video' for individual video URLs
            'user' for user profile URLs
            'unknown' for unrecognized URLs
        """
        if not self.validate_url(url):
            return 'unknown'
        
        try:
            # User profile patterns: @username or user/username
            if re.search(r'tiktok\.com/@[^/]+/?$', url) or re.search(r'tiktok\.com/user/[^/]+/?$', url):
                return 'user'
            
            # Video patterns: @username/video/123 or vm.tiktok.com/shortcode
            if re.search(r'tiktok\.com/@[^/]+/video/\d+', url) or re.search(r'vm\.tiktok\.com/[a-zA-Z0-9]+', url):
                return 'video'
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def extract_username(self, url: str) -> str:
        """Extract username from TikTok user profile URL."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
        try:
            # Pattern for @username URLs
            match = re.search(r'tiktok\.com/@([^/]+)', url)
            if match:
                return match.group(1)
            
            # Pattern for user/username URLs
            match = re.search(r'tiktok\.com/user/([^/]+)', url)
            if match:
                return match.group(1)
            
            raise ValueError(f"Could not extract username from URL: {url}")
            
        except Exception as e:
            raise ValueError(f"Could not extract username from URL: {url}") from e
    
    def extract_video_urls(self, url: str, max_videos: Optional[int] = None) -> List[str]:
        """
        Extract individual video URLs from user profile or return single video URL.
        
        Args:
            url: TikTok URL (video or user profile)
            max_videos: Maximum number of videos to extract from user profile
        
        Returns:
            List of video URLs
        """
        if not self.validate_url(url):
            return []
        
        url_type = self.get_url_type(url)
        
        if url_type == 'video':
            return [url]
        
        if url_type == 'user':
            return self.extract_user_videos(url, max_videos)
        
        # If we can't determine the type, treat as single video
        return [url]
    
    def extract_user_videos(self, url: str, max_videos: Optional[int] = None) -> List[str]:
        """
        Extract all videos from a TikTok user profile.
        
        Args:
            url: TikTok user profile URL (e.g., https://www.tiktok.com/@username)
            max_videos: Maximum number of videos to extract
            
        Returns:
            List of individual video URLs
        """
        if not self.validate_url(url):
            return []
        
        url_type = self.get_url_type(url)
        if url_type != 'user':
            raise ValueError(f"URL is not a user profile URL: {url}")
        
        # Set default limit for user profiles to prevent processing thousands of videos
        if max_videos is None:
            max_videos = 20
            logger.info(f"TikTok user profile detected, limiting to {max_videos} recent videos (use max_videos parameter to change)")
        
        try:
            cmd = [
                'yt-dlp',
                '--flat-playlist',
                '--print', 'webpage_url',
                '--no-warnings'
            ]
            
            if max_videos:
                cmd.extend(['--playlist-end', str(max_videos)])
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            video_urls = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and self.validate_url(line):
                    video_urls.append(line)
            
            logger.info(f"Extracted {len(video_urls)} videos from TikTok user: {url}")
            
            # Note: TikTok videos can be very short (1-15 seconds) which is normal
            if video_urls:
                logger.info(f"Note: TikTok videos may be very short and contain minimal speech content")
            
            return video_urls
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting videos from TikTok user {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error extracting videos from TikTok user {url}: {e}")
            return []
    
    def get_playlist_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get TikTok user profile metadata.
        
        Args:
            url: TikTok user profile URL
            
        Returns:
            Dictionary containing user metadata
        """
        if not self.validate_url(url):
            return {
                'title': 'TikTok User',
                'playlist_id': 'unknown',
                'uploader': None,
                'description': None,
                'video_count': 0
            }
        
        url_type = self.get_url_type(url)
        if url_type != 'user':
            return {
                'title': 'TikTok Video',
                'playlist_id': 'unknown',
                'uploader': None,
                'description': None,
                'video_count': 0
            }
        
        try:
            username = self.extract_username(url)
            
            # Try to get user metadata using yt-dlp
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--flat-playlist',
                '--playlist-end', '1',  # Just get metadata, not all videos
                '--no-warnings',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the first line of JSON output
            lines = result.stdout.strip().split('\n')
            if lines and lines[0].strip():
                try:
                    metadata = json.loads(lines[0])
                    
                    return {
                        'title': metadata.get('uploader', metadata.get('playlist_uploader', f"TikTok @{username}")),
                        'playlist_id': username,
                        'uploader': metadata.get('uploader', metadata.get('playlist_uploader', username)),
                        'description': metadata.get('description', metadata.get('playlist_description')),
                        'video_count': metadata.get('playlist_count', 0)
                    }
                except json.JSONDecodeError:
                    pass
            
            # Fallback to basic metadata
            return {
                'title': f"TikTok @{username}",
                'playlist_id': username,
                'uploader': username,
                'description': None,
                'video_count': 0
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting TikTok user metadata for {url}: {e}")
            try:
                username = self.extract_username(url)
                return {
                    'title': f"TikTok @{username}",
                    'playlist_id': username,
                    'uploader': username,
                    'description': None,
                    'video_count': 0
                }
            except Exception:
                return {
                    'title': 'TikTok User',
                    'playlist_id': 'unknown',
                    'uploader': None,
                    'description': None,
                    'video_count': 0
                }
        except Exception as e:
            logger.error(f"Unexpected error getting TikTok user metadata for {url}: {e}")
            return {
                'title': 'TikTok User',
                'playlist_id': 'unknown',
                'uploader': None,
                'description': None,
                'video_count': 0
            }

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from TikTok URL."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
        try:
            # For user profile URLs, use the username as ID
            if self.get_url_type(url) == 'user':
                return self.extract_username(url)
            
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
    
    def get_video_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get TikTok video metadata using yt-dlp.
        
        Args:
            url: TikTok video URL
            
        Returns:
            Dictionary containing video metadata
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid TikTok URL: {url}")
        
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
                'title': metadata.get('title', 'TikTok Video'),
                'video_id': metadata.get('id', self.extract_video_id(url)),
                'uploader': metadata.get('uploader', metadata.get('creator', None)),
                'duration': metadata.get('duration'),
                'description': metadata.get('description'),
                'upload_date': metadata.get('upload_date'),
                'view_count': metadata.get('view_count'),
                'like_count': metadata.get('like_count')
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting TikTok metadata for {url}: {e}")
            # Fall back to basic metadata
            try:
                video_id = self.extract_video_id(url)
                return {
                    'title': f"TikTok_{video_id}",
                    'video_id': video_id,
                    'uploader': None,
                    'duration': None,
                    'description': None
                }
            except Exception:
                return {
                    'title': 'TikTok_Video',
                    'video_id': 'unknown',
                    'uploader': None,
                    'duration': None,
                    'description': None
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing TikTok metadata JSON for {url}: {e}")
            video_id = self.extract_video_id(url)
            return {
                'title': f"TikTok_{video_id}",
                'video_id': video_id,
                'uploader': None,
                'duration': None,
                'description': None
            }
        except Exception as e:
            logger.error(f"Unexpected error getting TikTok metadata for {url}: {e}")
            return {
                'title': 'TikTok_Video',
                'video_id': 'unknown',
                'uploader': None,
                'duration': None,
                'description': None
            }
