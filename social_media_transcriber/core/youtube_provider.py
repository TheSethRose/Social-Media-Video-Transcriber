"""
YouTube video provider implementation.
"""

import re
import subprocess
import logging
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse, parse_qs

from .providers import VideoProvider

logger = logging.getLogger(__name__)

class YouTubeProvider(VideoProvider):
    """YouTube video provider using yt-dlp."""
    
    def __init__(self):
        """Initialize YouTube provider."""
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("yt-dlp is required for YouTube support. Install with: pip install yt-dlp")
        except FileNotFoundError:
            raise RuntimeError("yt-dlp is required for YouTube support. Install with: pip install yt-dlp")
    
    @property
    def provider_name(self) -> str:
        """Name of the provider."""
        return "YouTube"
    
    @property
    def supported_domains(self) -> list[str]:
        """List of supported domains for this provider."""
        return [
            'youtube.com',
            'www.youtube.com',
            'youtu.be',
            'm.youtube.com',
            'music.youtube.com'
        ]
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is a YouTube URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if domain is supported
            if not any(domain.endswith(d) for d in self.supported_domains):
                return False
            
            # Additional validation for YouTube URL patterns
            if 'youtube.com' in domain:
                return bool(
                    '/watch' in parsed.path or
                    '/playlist' in parsed.path or
                    '/channel' in parsed.path or
                    '/c/' in parsed.path or
                    '/user/' in parsed.path or
                    '/@' in parsed.path
                )
            elif 'youtu.be' in domain:
                return len(parsed.path) > 1  # Should have video ID
            
            return True
            
        except Exception:
            return False
    
    def get_url_type(self, url: str) -> str:
        """Get the type of YouTube URL."""
        if not self.validate_url(url):
            return 'unknown'
        
        try:
            parsed = urlparse(url)
            path = parsed.path
            query = parse_qs(parsed.query)
            
            # Playlist URL
            if '/playlist' in path or 'list' in query:
                return 'playlist'
            
            # Channel URLs
            if any(pattern in path for pattern in ['/channel/', '/c/', '/user/', '/@']):
                return 'channel'
            
            # Video URL (watch or youtu.be)
            if '/watch' in path or 'youtu.be' in parsed.netloc:
                return 'video'
            
            return 'video'  # Default to video for valid URLs
            
        except Exception:
            return 'unknown'
    
    def is_playlist_url(self, url: str) -> bool:
        """Check if URL is a playlist or channel."""
        url_type = self.get_url_type(url)
        return url_type in ['playlist', 'channel']
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        try:
            parsed = urlparse(url)
            
            # youtu.be format
            if 'youtu.be' in parsed.netloc:
                return parsed.path[1:]  # Remove leading slash
            
            # youtube.com format
            if 'youtube.com' in parsed.netloc:
                query = parse_qs(parsed.query)
                if 'v' in query:
                    return query['v'][0]
            
            raise ValueError(f"Could not extract video ID from URL: {url}")
            
        except Exception as e:
            raise ValueError(f"Could not extract video ID from URL: {url}") from e
    
    def extract_video_urls(self, url: str, max_videos: Optional[int] = None) -> List[str]:
        """
        Extract individual video URLs from playlist/channel.
        
        Args:
            url: YouTube URL (video, playlist, or channel)
            max_videos: Maximum number of videos to extract (for channels, defaults to 10)
        
        Returns:
            List of video URLs
        """
        if not self.validate_url(url):
            return []
        
        url_type = self.get_url_type(url)
        
        if url_type == 'video':
            return [url]
        
        # Set default limits for channels to prevent processing thousands of videos
        if url_type == 'channel' and max_videos is None:
            max_videos = 10
            logger.info(f"Channel detected, limiting to {max_videos} recent videos (use max_videos parameter to change)")
        
        try:
            # Use yt-dlp to extract video URLs from playlist/channel
            cmd = [
                'yt-dlp',
                '--flat-playlist',
                '--print', 'webpage_url',
                '--no-warnings'
            ]
            
            # For channels, limit to recent videos and exclude shorts
            if url_type == 'channel':
                if max_videos:
                    cmd.extend(['--playlist-end', str(max_videos * 2)])  # Get extra to filter shorts
                cmd.extend(['--match-filter', 'duration > 60'])  # Exclude shorts (< 1 minute)
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_urls = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Apply final limit after extraction and filtering
            if url_type == 'channel' and max_videos and len(video_urls) > max_videos:
                video_urls = video_urls[:max_videos]
                logger.info(f"Limited channel results to {max_videos} videos (excluding shorts)")
            
            if not video_urls:
                logger.warning(f"No videos found for URL: {url}")
                return []
            
            logger.info(f"Found {len(video_urls)} videos in {url_type}: {url}")
            return video_urls
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting videos from {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error extracting videos from {url}: {e}")
            return []
    
    def download_video(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download a YouTube video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For playlist/channel URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"youtube_{video_id}.%(ext)s")
        
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
                    logger.info(f"Downloaded YouTube video: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading YouTube video {url}: {e}")
            raise RuntimeError(f"Failed to download YouTube video: {e}")
    
    def download_audio_only(self, url: str, output_file: Optional[Path] = None) -> Path:
        """Download audio only from a YouTube video."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        try:
            video_id = self.extract_video_id(url)
        except ValueError:
            # For playlist/channel URLs, just use a timestamp-based filename
            from datetime import datetime
            video_id = f"youtube_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_file is None:
            output_file = Path(f"youtube_audio_{video_id}.%(ext)s")
        
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
                    logger.info(f"Downloaded YouTube audio: {potential_file}")
                    return potential_file
            
            # If we can't find it, return the original path
            logger.warning(f"Could not locate downloaded audio file, returning original path: {output_file}")
            return output_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading YouTube audio {url}: {e}")
            raise RuntimeError(f"Failed to download YouTube audio: {e}")
