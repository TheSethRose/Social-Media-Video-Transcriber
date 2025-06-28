# Playlist Folder Naming

## Overview

When transcribing YouTube playlists, the application now automatically creates folders named after the playlist title, making it easy to organize transcripts by their source playlist.

## How It Works

### Playlist Detection
- When you provide a YouTube playlist URL, the system automatically detects it as a playlist
- The playlist title is extracted using yt-dlp's metadata capabilities
- Each video in the playlist is processed individually

### Folder Naming
- **Playlist URLs**: Creates a folder named after the playlist title (e.g., "MIT 6.034 Artificial Intelligence, Fall 2010")
- **Single Video URLs**: Uses the default output location or specified output directory
- **Mixed Bulk Processing**: Each playlist gets its own named folder, single videos go to a timestamped directory

### File Naming
- Individual video transcripts within the playlist folder are named using the video title
- Example: "1. Introduction and Scope_transcript.txt", "2. Reasoning Goal Trees and Problem Solving_transcript.txt"

## Usage Examples

### Single Playlist Transcription
```bash
# Direct playlist URL - creates playlist-named folder
python -m social_media_transcriber.cli.transcribe_cli "https://www.youtube.com/playlist?list=PLUl4u3cNGP63gFHB6xb-kVBiQHYe_4hSi"
```

This creates:
```
output/
└── MIT 6.034 Artificial Intelligence, Fall 2010/
    ├── 1. Introduction and Scope_transcript.txt
    ├── 2. Reasoning Goal Trees and Problem Solving_transcript.txt
    ├── 3. Reasoning Goal Trees and Rule-Based Expert Systems_transcript.txt
    └── ... (all videos in the playlist)
```

### Bulk Processing with Playlists
```bash
# Create bulk.txt with playlist URLs
echo "https://www.youtube.com/playlist?list=PLUl4u3cNGP63gFHB6xb-kVBiQHYe_4hSi" > bulk.txt
echo "https://www.youtube.com/watch?v=single_video_id" >> bulk.txt

# Process all URLs
python -m social_media_transcriber.cli.transcribe_cli --bulk
```

This creates:
```
output/
├── MIT 6.034 Artificial Intelligence, Fall 2010/
│   ├── 1. Introduction and Scope_transcript.txt
│   ├── 2. Reasoning Goal Trees and Problem Solving_transcript.txt
│   └── ... (all playlist videos)
└── bulk_transcription_20241227_143022/
    └── single_video_title_transcript.txt
```

## Technical Details

### Folder Name Sanitization
- Playlist titles are automatically sanitized for file system compatibility
- Removes forbidden characters: `<>:"/\\|?*`
- Keeps alphanumeric characters, spaces, hyphens, underscores, and basic punctuation
- Truncates long names while preserving whole words
- Handles naming conflicts by adding numeric suffixes

### Error Handling
- If playlist metadata extraction fails, falls back to generic folder names with timestamps
- Individual video failures don't stop playlist processing
- Maintains backward compatibility with single video transcription

### Performance
- Playlist metadata is extracted once per playlist (not per video)
- Uses efficient yt-dlp flat-playlist mode for fast expansion
- Maintains existing speed optimization features (3x audio speed by default)

## Supported Platforms

Currently, playlist folder naming is supported for:
- ✅ YouTube playlists
- ✅ YouTube channel URLs (limited to recent videos)

Future platform support:
- 🔄 Other platforms as provider support is added

## Benefits

1. **Organization**: Automatically organizes transcripts by their source playlist
2. **Recognition**: Easy to identify which playlist transcripts came from
3. **Scalability**: Handles multiple playlists in bulk processing
4. **Backward Compatibility**: Single video transcription works exactly as before
5. **User-Friendly**: No additional configuration required - just provide the playlist URL
