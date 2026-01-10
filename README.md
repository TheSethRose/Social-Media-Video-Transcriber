# Social Media Video Transcriber

A Python tool for downloading and transcribing videos from multiple social media platforms. Uses `yt-dlp` for downloads and `parakeet-mlx` for transcription on Apple Silicon.

## Features

- **Multi-Platform Support**: YouTube, TikTok, Facebook, Instagram, Reddit, Twitch, Vimeo, X/Twitter
- **Entire Playlist/Channel Support**: Transcribe entire YouTube playlists or channels with automatic folder organization
- **Fast Transcription**: Audio speed optimization (2x-3x faster with pitch preservation)
- **Direct YouTube Transcripts**: Extracts existing subtitles when available (skips re-transcription)
- **LLM Enhancement**: Optional AI-powered transcript formatting via OpenRouter
- **CLI Interface**: Simple `transcriber` command for all operations

## Quick Start

```bash
# Install
pip install -e .

# Transcribe a single video
transcriber run "https://www.youtube.com/watch?v=VIDEO_ID"

# Transcribe an entire playlist (all videos, auto-organized)
transcriber run "https://www.youtube.com/playlist?list=PLAYLIST_ID"

# Transcribe a channel (all videos)
transcriber run "https://www.youtube.com/@channelname"

# With LLM enhancement
transcriber run "https://www.youtube.com/watch?v=VIDEO_ID" --enhance

# Process multiple URLs from a file
transcriber run --file urls.txt

# Combine transcript files from channels/playlists
transcriber transcripts -d output

# Combine .mdx files for LLM processing
transcriber combine /path/to/folder
```

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg (for audio processing)
- [UV](https://github.com/astral-sh/uv) recommended, or pip

### Setup

```bash
# Clone and install
git clone https://github.com/thesethrose/social-media-transcriber.git
cd social-media-video-transcriber

# Using UV (recommended)
uv venv
source .venv/bin/activate
uv pip install -e .

# Or using pip
pip install -e .
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key settings:
- `OPENROUTER_API_KEY`: For LLM transcript enhancement (optional)
- `TRANSCRIPT_OUTPUT_DIR`: Default output directory

## Documentation

See the [docs](docs/) directory for detailed guides:

- [Adding New Providers](docs/ADDING_PROVIDERS.md) - Extending platform support
- [Audio Speed Optimization](docs/AUDIO_SPEED_OPTIMIZATION.md) - Performance tuning
- [Playlist Folder Naming](docs/PLAYLIST_FOLDER_NAMING.md) - Output organization
- [Testing Guide](docs/TESTING_GUIDE.md) - Running tests

## Usage

### Basic Transcription

```bash
transcriber run "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Options

| Option | Description |
|--------|-------------|
| `-f, --file FILE` | File containing URLs (one per line) |
| `-o, --output-dir DIR` | Output directory for transcripts |
| `--speed SPEED` | Audio speed multiplier (1.0=normal, default: 2.0) |
| `--enhance` | Use LLM to format/enhance transcript |
| `-w, --max-workers N` | Concurrent workers (default: 4) |

### Combining Transcripts

```bash
# Combine all channel/playlist folders in output/
transcriber transcripts

# Combine specific channel or playlist
transcriber transcripts -c "Channel Name"

# Combine .mdx files for LLM processing
transcriber combine /path/to/folder
```

## Architecture

```
social_media_transcriber/
├── cli.py                 # Click CLI commands
├── config/
│   └── settings.py        # Configuration management
├── core/
│   ├── transcriber.py     # Audio transcription logic
│   ├── downloader.py      # Provider discovery/routing
│   └── providers/         # Platform-specific implementations
│       ├── base.py        # Base provider class
│       └── youtube_provider.py  # YouTube with transcript extraction
└── utils/
    ├── file_utils.py      # File operations
    └── processing.py      # Core URL processing
```

Adding a new platform is as simple as adding a provider file - no other changes needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your provider in `social_media_transcriber/core/providers/`
4. Run tests: `pytest`
5. Submit a pull request

See [Adding New Providers](docs/ADDING_PROVIDERS.md) for details.

## Dependencies

- `yt-dlp` - Video downloading
- `parakeet-mlx` - MLX-based transcription (Apple Silicon)
- `click` - CLI framework
- `rich` - Terminal output
- `python-dotenv` - Environment configuration

See `requirements.txt` for full list.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for excellent video downloading
- [parakeet-mlx](https://github.com/ml-explore/mlx-audio) for fast on-device transcription
