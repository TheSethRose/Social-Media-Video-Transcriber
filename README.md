# Social Media Video Transcriber

A powerful Python tool for downloading and transcribing videos from multiple platforms (TikTok, YouTube, Facebook, Instagram) using Parakeet-MLX for high-quality speech-to-text conversion.

## ✨ Features

### Video Sources
- **TikTok** - Individual videos with metadata extraction
- **YouTube** - Individual videos, playlists, and channels
- **Facebook** - Videos, Reels, and fb.watch URLs
- **Instagram** - Posts, Reels, IGTV, and Stories  
- **Extensible** - Easy to add new video providers (see [ADDING_PROVIDERS.md](ADDING_PROVIDERS.md))

### Processing Capabilities
- High-quality transcription using Parakeet-MLX (optimized for Apple Silicon)
- Bulk processing with automatic playlist/channel expansion
- Organized output with timestamped directories
- Progress tracking and comprehensive error handling

### Developer Features
- Modular, extensible architecture
- Comprehensive CLI with multiple commands
- Provider-based plugin system
- Type-safe Python with comprehensive documentation

## 🚀 Quick Start

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd TikTok-Transcribe
chmod +x setup.sh
./setup.sh
```

2. **Activate environment:**
```bash
source venv/bin/activate
```

### Basic Usage

```bash
# Single video (TikTok, YouTube, Facebook, or Instagram)
python main.py workflow "https://www.youtube.com/watch?v=VIDEO_ID"
python main.py workflow "https://www.tiktok.com/@user/video/123"
python main.py workflow "https://www.facebook.com/reel/VIDEO_ID"
python main.py workflow "https://www.instagram.com/p/POST_ID"

# YouTube playlist (automatically expands to individual videos)
python main.py workflow "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# YouTube channel (processes recent videos)
python main.py workflow "https://www.youtube.com/@channel_name"

# Bulk processing from file
python main.py workflow --bulk --bulk-file example_urls.txt

# Transcription only
python main.py transcribe "https://www.youtube.com/watch?v=VIDEO_ID"
python main.py transcribe "https://www.facebook.com/reel/VIDEO_ID"
python main.py transcribe "https://www.instagram.com/p/POST_ID"

# Help
python main.py --help
```

## 📁 Output Structure

All outputs are organized in timestamped directories:

```
output/
└── transcripts/
    └── 2024-12-07_14-30-45/
        ├── video_title_1_transcript.txt
        └── video_title_2_transcript.txt
```

## 📚 Available Commands

### Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `workflow` | Complete video processing (download → transcribe) | `python main.py workflow "URL"` |
| `transcribe` | Download and transcribe only | `python main.py transcribe "URL"` |
| `bulk` | Process multiple URLs | `python main.py bulk example_urls.txt` |

### Individual Components

| Command | Description | Example |
|---------|-------------|---------|
| `download` | Download video only | `python main.py download "URL" output_path` |
| `extract-audio` | Extract audio from video | `python main.py extract-audio video.mp4 audio.wav` |
| `transcribe-audio` | Transcribe audio file | `python main.py transcribe-audio audio.wav` |

### Utilities

| Command | Description | Example |
|---------|-------------|---------|
| `analyze` | Analyze transcript statistics | `python main.py analyze transcript.txt` |
| `validate` | Check supported URL formats | `python main.py validate "URL"` |

## 🌍 Supported Platforms

### Currently Supported
- **TikTok** - Individual videos with metadata extraction
- **YouTube** - Videos, playlists, channels (using yt-dlp)
- **Facebook** - Videos, Reels, and fb.watch URLs
- **Instagram** - Posts, Reels, IGTV, and Stories

### URL Patterns
```bash
# TikTok
https://www.tiktok.com/@user/video/123456789
https://vm.tiktok.com/SHORTURL

# YouTube Videos  
https://www.youtube.com/watch?v=VIDEO_ID
https://youtu.be/VIDEO_ID

# YouTube Playlists (auto-expands to individual videos)
https://www.youtube.com/playlist?list=PLAYLIST_ID

# YouTube Channels (processes recent videos)
https://www.youtube.com/@channel_name
https://www.youtube.com/channel/CHANNEL_ID
https://www.youtube.com/c/CHANNEL_NAME

# Facebook Videos and Reels
https://www.facebook.com/videos/VIDEO_ID
https://www.facebook.com/reel/VIDEO_ID
https://fb.watch/VIDEO_ID

# Instagram Content
https://www.instagram.com/p/POST_ID
https://www.instagram.com/reel/REEL_ID
https://www.instagram.com/tv/IGTV_ID
```

## 🔧 Advanced Usage

### Bulk Processing

1. **Create URL file:**
```bash
# example_urls.txt
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMt095B1GdUhWDj0n7
https://www.tiktok.com/@user/video/123456789
https://www.facebook.com/reel/2443188852722500
https://www.instagram.com/p/POST_ID
```

2. **Process all URLs:**
```bash
python main.py workflow --bulk --bulk-file example_urls.txt
```

### Custom Output Directories

```bash
# Specify custom output directory
python main.py workflow "URL" --output-dir custom_output/

# Custom transcript directory
python main.py workflow "URL" --transcript-dir transcripts/
```

### Configuration Options

```bash
# Verbose output
python main.py workflow "URL" --verbose
```

## 🛠️ Requirements

### System Requirements
- Python 3.8+
- macOS (recommended for Parakeet-MLX optimization)
- FFmpeg for audio processing

### Python Dependencies
- `parakeet-mlx` - High-quality transcription (Apple Silicon optimized)
- `yt-dlp` - Multi-platform video downloading (YouTube, Facebook, Instagram)
- `requests` - HTTP requests for TikTok and other providers
- `click` - CLI framework
- Additional utilities (see `requirements.txt`)

## 🏗️ Architecture

### Core Components

```
social_media_transcriber/
├── core/
│   ├── transcriber.py       # Parakeet-MLX integration
│   ├── providers.py         # Abstract provider base
│   ├── downloader.py        # Multi-platform video downloader
│   ├── tiktok_provider.py   # TikTok implementation
│   ├── youtube_provider.py  # YouTube implementation
│   ├── facebook_provider.py # Facebook implementation
│   └── instagram_provider.py# Instagram implementation
├── utils/
│   ├── bulk_processor.py    # Bulk processing with URL expansion
│   ├── file_utils.py        # File operations and validation
│   └── url_handler.py       # URL parsing and validation
└── cli/
    └── commands.py          # CLI command implementations
```

### Provider System

The tool uses a plugin-based provider system that makes adding new video platforms straightforward. Each provider implements the `VideoProvider` abstract base class with methods for:

- URL validation and platform-specific pattern matching
- Video ID extraction from various URL formats  
- Video downloading with platform-optimized settings
- Audio extraction and format handling
- Platform-specific error handling and retry logic

## 🚀 Extending Support

### Adding New Video Providers

See [ADDING_PROVIDERS.md](ADDING_PROVIDERS.md) for detailed instructions on implementing support for new video platforms.

### Quick Provider Template

```python
from core.providers import VideoProvider

class NewPlatformProvider(VideoProvider):
    def validate_url(self, url: str) -> bool:
        # Check if URL matches platform patterns
        pass
    
    def extract_video_id(self, url: str) -> str:
        # Extract unique video identifier
        pass
        
    def download_video(self, url: str, output_file: Path) -> Path:
        # Download video with platform-specific settings
        pass
```
        # Get video metadata
        pass
        
    def download_video(self, video_id: str, output_path: str) -> str:
        # Download video file
        pass
```

## 🧪 Testing

### Run Test Cases

```bash
# Test single video processing (all platforms)
python main.py workflow "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
python main.py workflow "https://www.tiktok.com/@user/video/123456789"
python main.py workflow "https://www.facebook.com/reel/2443188852722500"
python main.py workflow "https://www.instagram.com/p/POST_ID"

# Test playlist expansion  
python main.py workflow "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMt095B1GdUhWDj0n7"

# Test bulk processing
python main.py workflow --bulk --bulk-file example_urls.txt

# Test URL validation for all platforms
python main.py validate "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
python main.py validate "https://www.facebook.com/reel/2443188852722500"
python main.py validate "https://www.instagram.com/p/POST_ID"
python main.py analyze output/transcripts/latest/transcript.txt
```

## 📋 Troubleshooting

### Common Issues

1. **Parakeet-MLX Installation**
   ```bash
   # If installation fails, try:
   pip install --upgrade pip
   pip install parakeet-mlx --no-cache-dir
   ```

2. **FFmpeg Missing**
   ```bash
   # Install via Homebrew (macOS)
   brew install ffmpeg
   ```

3. **YouTube Download Errors**
   ```bash
   # Update yt-dlp for latest fixes
   pip install --upgrade yt-dlp
   ```

4. **Permission Errors**
   ```bash
   # Make setup script executable
   chmod +x setup.sh
   ```

### Debug Mode

```bash
# Enable verbose logging
python main.py workflow "URL" --verbose

# Check URL validation
python main.py validate "URL"

# Test individual components
python main.py download "URL" test_video.mp4
python main.py extract-audio test_video.mp4 test_audio.wav
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
git clone <your-fork>
cd TikTok-Transcribe
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- [Parakeet-MLX](https://github.com/Parakeet-MLX/parakeet-mlx) for high-quality transcription
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for robust video downloading
- Community contributors and testers
