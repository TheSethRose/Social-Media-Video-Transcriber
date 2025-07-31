# Social Media Video Transcriber

A powerful Python tool for downloading and transcribing videos from multiple platforms (TikTok, YouTube, Facebook, Instagram) using Parakeet-MLX for high-quality speech-to-text conversion.

## ✨ Features

- **Multi-Platform Support**: Works with YouTube, TikTok, Facebook, and Instagram.
- **High-Quality Transcription**: Uses `Parakeet-MLX`, optimized for Apple Silicon.
- **Performance Optimized**: **3x faster transcription** by default using FFmpeg audio processing without sacrificing quality.
- **Bulk & Playlist Processing**: Automatically expands YouTube playlists/channels and processes URLs from a file in parallel.
- **Automatic Organization**: Creates folders named after YouTube playlist titles for easy navigation.
- **Developer Friendly**: Modular, provider-based architecture that's easy to extend.
- **Modern CLI**: Clean, intuitive command-line interface built with `click`.

## 🚀 Quick Start

### 1. Installation

First, ensure you have **Python 3.8+** and **FFmpeg** installed.

```bash
# Clone the repository
git clone <repository-url>
cd social-media-transcriber

# Run the setup script to create a virtual environment and install dependencies
chmod +x setup.sh
./setup.sh

# Activate the virtual environment
source venv/bin/activate
````

### 2. Basic Usage

The primary command is `run`. You can provide URLs directly or from a file.

```bash
# Get help and see all commands
transcriber --help

# Transcribe a single video (YouTube, TikTok, etc.)
transcriber run "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)"

# Transcribe a YouTube playlist (expands automatically)
transcriber run "[https://www.youtube.com/playlist?list=PLAYLIST_ID](https://www.youtube.com/playlist?list=PLAYLIST_ID)"

# Process multiple URLs from a text file
transcriber run --file urls.txt

# Use a different number of parallel workers
transcriber run --file urls.txt --max-workers 8

# Change the audio processing speed (default is 3.0)
transcriber run "URL" --speed 1.5
```

### 3. Combine Transcripts

After processing playlists, you can combine all transcripts in a folder into one file.

```bash
# Combine all transcripts in the default 'output' directory
transcriber combine

# Combine transcripts for a specific channel/playlist folder
transcriber combine --channel "My Awesome Playlist"
```

## 📁 Output Structure

The tool organizes transcripts intelligently.

**Playlists & Channels:**
Creates a sanitized folder named after the playlist or channel.

```bash
output/
└── MIT-6-034-Artificial-Intelligence-Fall-2010/
    ├── 1-Introduction-and-Scope_transcript.txt
    └── 2-Reasoning-Goal-Trees_transcript.txt
```

**Bulk Individual Videos:**
Groups all non-playlist videos into a single timestamped folder.

```bash
output/
└── bulk_transcripts_20250731_162845/
    ├── Some-Cool-Video_transcript.txt
    └── Another-Video_transcript.txt
```

## 🔧 Extending Support

See [docs/ADDING_PROVIDERS.md](docs/ADDING_PROVIDERS.md) for a detailed guide on adding new video platforms. The provider-based architecture makes it simple.

## 🛠️ Architecture

The project is structured for clarity and scalability.

```bash
social\_media\_transcriber/
├── core/
│   ├── providers/             \# \<--- Corrected Path
│   │   ├── base.py            \# Abstract & base yt-dlp provider
│   │   ├── youtube\_provider.py  \# Specific provider logic
│   │   └── ...                \# All other providers here
│   ├── downloader.py          \# Dynamically loads all providers
│   └── transcriber.py         \# Handles Parakeet-MLX transcription
├── utils/
│   ├── processing.py          \# Parallel URL processing logic
│   └── file\_utils.py          \# Filesystem and ffmpeg helpers
└── cli.py                     \# Click-based CLI commands

````
