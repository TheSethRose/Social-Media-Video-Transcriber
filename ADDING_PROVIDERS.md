# Adding New Video Providers

This guide explains how to add support for new video platforms to the Video Transcribe tool.

## Overview

The tool uses a provider-based architecture where each video platform implements the `VideoProvider` abstract base class. This makes adding new platforms straightforward and maintains consistency across the codebase.

## Provider Architecture

### Abstract Base Class

All providers inherit from `VideoProvider` in `/tiktok_transcribe/core/video_provider.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional

class VideoProvider(ABC):
    """Abstract base class for video providers."""
    
    @abstractmethod
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from URL."""
        pass
    
    @abstractmethod
    def get_video_info(self, video_id: str) -> Dict:
        """Get video metadata."""
        pass
    
    @abstractmethod
    def download_video(self, video_id: str, output_path: str) -> str:
        """Download video and return path to downloaded file."""
        pass
    
    @abstractmethod
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is supported by this provider."""
        pass
```

### Required Methods

Each provider must implement four key methods:

1. **`extract_video_id(url)`** - Extract unique video identifier from URL
2. **`get_video_info(video_id)`** - Retrieve video metadata (title, duration, etc.)
3. **`download_video(video_id, output_path)`** - Download video file
4. **`is_supported_url(url)`** - Validate if URL belongs to this platform

## Step-by-Step Implementation

### 1. Create Provider Class

Create a new file in `/tiktok_transcribe/core/` for your provider:

```python
# /tiktok_transcribe/core/instagram_provider.py

import re
import requests
from typing import Dict
from .video_provider import VideoProvider

class InstagramProvider(VideoProvider):
    """Instagram video provider implementation."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is an Instagram video."""
        instagram_patterns = [
            r'instagram\.com/p/',
            r'instagram\.com/reel/',
            r'instagram\.com/tv/'
        ]
        return any(re.search(pattern, url) for pattern in instagram_patterns)
    
    def extract_video_id(self, url: str) -> str:
        """Extract Instagram post ID from URL."""
        match = re.search(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)', url)
        if not match:
            raise ValueError(f"Could not extract video ID from Instagram URL: {url}")
        return match.group(1)
    
    def get_video_info(self, video_id: str) -> Dict:
        """Get Instagram video metadata."""
        # Implementation depends on Instagram's API or scraping
        # This is a simplified example
        return {
            'id': video_id,
            'title': f'Instagram Video {video_id}',
            'platform': 'instagram',
            'url': f'https://www.instagram.com/p/{video_id}/'
        }
    
    def download_video(self, video_id: str, output_path: str) -> str:
        """Download Instagram video."""
        # Use yt-dlp or custom implementation
        import yt_dlp
        
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]'
        }
        
        url = f'https://www.instagram.com/p/{video_id}/'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return output_path
```

### 2. Register Provider

Add your provider to the provider registry in `/tiktok_transcribe/core/transcriber.py`:

```python
# In __init__ method of VideoTranscriber class
def __init__(self):
    self.providers = {
        'tiktok': TikTokProvider(),
        'youtube': YouTubeProvider(),
        'instagram': InstagramProvider(),  # Add new provider
    }
```

### 3. Update URL Handling

Add URL patterns to `/tiktok_transcribe/utils/file_utils.py`:

```python
def extract_video_id(url: str) -> str:
    """Extract video ID from supported video URLs."""
    
    # Existing TikTok patterns...
    # Existing YouTube patterns...
    
    # Instagram patterns
    instagram_match = re.search(r'/(?:p|reel|tv)/([A-Za-z0-9_-]+)', url)
    if instagram_match:
        return instagram_match.group(1)
    
    raise ValueError(f"Unsupported URL format: {url}")
```

### 4. Add Platform Detection

Update the provider detection logic:

```python
def detect_provider(url: str) -> str:
    """Detect which provider should handle this URL."""
    
    if 'tiktok.com' in url or 'vm.tiktok.com' in url:
        return 'tiktok'
    elif any(domain in url for domain in ['youtube.com', 'youtu.be']):
        return 'youtube'
    elif 'instagram.com' in url:
        return 'instagram'
    else:
        raise ValueError(f"Unsupported platform for URL: {url}")
```

## Implementation Examples

### Simple Provider (Direct API)

```python
class VimeoProvider(VideoProvider):
    """Vimeo provider using their API."""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token
        self.base_url = "https://api.vimeo.com"
    
    def is_supported_url(self, url: str) -> bool:
        return 'vimeo.com' in url
    
    def extract_video_id(self, url: str) -> str:
        match = re.search(r'vimeo\.com/(\d+)', url)
        if not match:
            raise ValueError("Invalid Vimeo URL")
        return match.group(1)
    
    def get_video_info(self, video_id: str) -> Dict:
        headers = {'Authorization': f'Bearer {self.api_token}'}
        response = requests.get(
            f"{self.base_url}/videos/{video_id}",
            headers=headers
        )
        data = response.json()
        
        return {
            'id': video_id,
            'title': data.get('name', ''),
            'duration': data.get('duration', 0),
            'platform': 'vimeo'
        }
    
    def download_video(self, video_id: str, output_path: str) -> str:
        # Use yt-dlp for downloading
        import yt_dlp
        
        ydl_opts = {'outtmpl': output_path}
        url = f'https://vimeo.com/{video_id}'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return output_path
```

### Complex Provider (Web Scraping)

```python
class TwitterProvider(VideoProvider):
    """Twitter/X video provider with web scraping."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set up session with proper headers, cookies, etc.
    
    def is_supported_url(self, url: str) -> bool:
        return any(domain in url for domain in ['twitter.com', 'x.com'])
    
    def extract_video_id(self, url: str) -> str:
        # Extract tweet ID from various Twitter URL formats
        patterns = [
            r'(?:twitter|x)\.com/[^/]+/status/(\d+)',
            r'(?:twitter|x)\.com/i/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Could not extract Tweet ID")
    
    def get_video_info(self, video_id: str) -> Dict:
        # Scrape tweet metadata or use Twitter API
        # This is complex due to Twitter's anti-bot measures
        pass
    
    def download_video(self, video_id: str, output_path: str) -> str:
        # Custom implementation or yt-dlp
        pass
```

## Best Practices

### Error Handling

```python
def download_video(self, video_id: str, output_path: str) -> str:
    """Download video with proper error handling."""
    
    try:
        # Download implementation
        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to download {self.platform_name} video {video_id}: {str(e)}")
```

### Logging

```python
import logging

class MyProvider(VideoProvider):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def download_video(self, video_id: str, output_path: str) -> str:
        self.logger.info(f"Downloading {self.platform_name} video: {video_id}")
        # Implementation
        self.logger.info(f"Successfully downloaded to: {output_path}")
        return output_path
```

### Configuration

```python
class ConfigurableProvider(VideoProvider):
    """Provider with configurable settings."""
    
    def __init__(self, **config):
        self.api_key = config.get('api_key')
        self.quality = config.get('quality', 'best')
        self.rate_limit = config.get('rate_limit', 1.0)
```

## Testing Your Provider

### Unit Tests

Create tests in `/tests/test_providers.py`:

```python
import pytest
from tiktok_transcribe.core.instagram_provider import InstagramProvider

class TestInstagramProvider:
    def setup_method(self):
        self.provider = InstagramProvider()
    
    def test_is_supported_url(self):
        assert self.provider.is_supported_url("https://www.instagram.com/p/ABC123/")
        assert not self.provider.is_supported_url("https://www.youtube.com/watch?v=123")
    
    def test_extract_video_id(self):
        url = "https://www.instagram.com/p/ABC123DEF/"
        assert self.provider.extract_video_id(url) == "ABC123DEF"
    
    def test_invalid_url(self):
        with pytest.raises(ValueError):
            self.provider.extract_video_id("https://invalid-url.com")
```

### Integration Tests

```python
def test_full_workflow():
    """Test complete video processing workflow."""
    provider = InstagramProvider()
    test_url = "https://www.instagram.com/p/VALID_POST_ID/"
    
    # Test URL validation
    assert provider.is_supported_url(test_url)
    
    # Test ID extraction
    video_id = provider.extract_video_id(test_url)
    assert video_id == "VALID_POST_ID"
    
    # Test metadata retrieval
    info = provider.get_video_info(video_id)
    assert 'title' in info
    assert 'platform' in info
```

## Common Patterns

### Using yt-dlp

Most providers can leverage yt-dlp for downloading:

```python
def download_video(self, video_id: str, output_path: str) -> str:
    """Download using yt-dlp."""
    import yt_dlp
    
    url = self.construct_url(video_id)
    
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]/best',
        'extractaudio': False,
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return output_path
```

### Handling Rate Limits

```python
import time
from functools import wraps

def rate_limit(delay: float):
    """Decorator to add rate limiting."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class RateLimitedProvider(VideoProvider):
    @rate_limit(1.0)  # 1 second delay
    def get_video_info(self, video_id: str) -> Dict:
        # Implementation
        pass
```

## Troubleshooting

### Common Issues

1. **Authentication Required**: Some platforms require API keys or authentication
2. **Rate Limiting**: Implement delays between requests
3. **Dynamic URLs**: Video URLs may be generated dynamically
4. **Anti-bot Protection**: May need to handle CAPTCHAs or IP blocking

### Debug Mode

Add verbose logging to help debug issues:

```python
def download_video(self, video_id: str, output_path: str) -> str:
    self.logger.debug(f"Starting download for {video_id}")
    self.logger.debug(f"Output path: {output_path}")
    
    try:
        result = self._actual_download(video_id, output_path)
        self.logger.debug(f"Download successful: {result}")
        return result
    except Exception as e:
        self.logger.error(f"Download failed: {str(e)}")
        raise
```

## Deployment Checklist

Before submitting your new provider:

- [ ] Implement all abstract methods
- [ ] Add comprehensive error handling
- [ ] Write unit tests
- [ ] Test with various URL formats
- [ ] Update documentation
- [ ] Add to provider registry
- [ ] Update URL handling utilities
- [ ] Test full workflow integration
- [ ] Consider rate limiting requirements
- [ ] Handle authentication if needed

## Example Pull Request

When contributing a new provider, include:

1. **Provider implementation** in `/core/`
2. **Updated provider registry** in main transcriber
3. **URL handling updates** in utilities
4. **Unit tests** for the provider
5. **Documentation updates** in README
6. **Example URLs** for testing

This ensures your provider integrates seamlessly with the existing codebase and maintains the tool's quality standards.
