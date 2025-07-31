# Audio Speed Optimization for Faster Transcription

This implementation adds audio speed optimization to the TikTok Transcriber, following the technique described in [this article](https://george.mand.is/2025/06/openai-charges-by-the-minute-so-make-the-minutes-shorter/).

## 🚀 What's New

### Speed Optimization Feature

- **Audio Speed Processing**: Automatically speeds up audio before transcription using ffmpeg
- **Configurable Speed**: Choose from 1.0x (normal) to 3.0x+ speeds
- **Pitch Preservation**: Maintains natural speech pitch for better transcription quality
- **Automatic Cleanup**: Temporary processed files are automatically removed
- **Quality Maintained**: Minimal transcription quality loss at recommended speeds

### Performance Benefits

- **2x Speed**: ~50% reduction in transcription time with minimal quality loss
- **3x Speed**: ~67% reduction in transcription time with acceptable quality
- **Token Efficiency**: Fewer tokens processed due to shorter audio duration
- **Cost Savings**: Reduced processing time = lower costs (when applicable)

## 🎛️ Usage

### Command Line Options

The `run` command supports the `--speed` parameter:

```bash
# Default 3x speed optimization
transcriber run "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)"

# Custom speed settings
transcriber run "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)" --speed 2.0
transcriber run "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)" --speed 1.0  # No optimization

# Bulk processing with speed optimization
transcriber run --file urls.txt --speed 3.0

# Benchmark different speeds
transcriber run "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)" --benchmark
````

### Programmatic Usage

```python
from social_media_transcriber.core.transcriber import AudioTranscriber
from social_media_transcriber.config.settings import Settings

# Initialize with custom speed
settings = Settings()
transcriber = AudioTranscriber(settings)

# Set speed multiplier
transcriber.set_speed_multiplier(2.0)  # 2x speed

# Or configure in settings
settings.audio_speed_multiplier = 3.0

# Benchmark different speeds
results = transcriber.benchmark_speed_settings(audio_file_path)
```

### Speed Guidelines

- **1.0x**: Normal speed, maximum quality (no optimization)
- **2.0x**: Good balance of speed and quality
- **3.0x**: Recommended default - excellent speed with acceptable quality
- **>3.0x**: Use with caution, may affect transcription quality

## 🛠️ Technical Implementation

### Audio Processing Pipeline

1. **Download**: Video downloaded using yt-dlp
2. **Extract**: Audio extracted from video
3. **Speed Processing**: Audio processed through ffmpeg with:
   - `atempo` filter for pitch preservation
   - Configurable speed multiplier
   - Format normalization (16kHz, mono, WAV)
4. **Transcribe**: Processed audio sent to Parakeet-MLX
5. **Cleanup**: Temporary files automatically removed

### FFmpeg Filters Used

```bash
# Pitch-preserving speed adjustment
ffmpeg -i input.wav -filter:a "atempo=2.0" output.wav

# For speeds > 2x, multiple atempo filters are chained:
ffmpeg -i input.wav -filter:a "atempo=2.0,atempo=1.5" output.wav  # 3x speed
```

### File Utility Functions

New functions added to `social_media_transcriber/utils/file_utils.py`:

- `speed_up_audio()`: Basic audio speed adjustment
- `process_audio_for_transcription()`: Complete audio processing pipeline
- `convert_audio_format()`: Audio format conversion

## 🧪 Testing

### Run the Test Suite

```bash
# Test audio speed functions
python test_audio_speed.py

# Manual testing with real URLs
python main.py workflow "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --benchmark
```

### Benchmark Results Example

```
🧪 Testing 1.0x speed: 45.2s
🧪 Testing 2.0x speed: 23.1s (2.0x faster than normal)
🧪 Testing 3.0x speed: 15.8s (2.9x faster than normal)
```

## 📊 Configuration

### Settings

The speed multiplier can be configured in several ways:

1. **Command Line**: `--speed 2.0`
2. **Environment**: Set in `Settings` class
3. **Runtime**: Using `transcriber.set_speed_multiplier()`

### Default Settings

```python
# In social_media_transcriber/config/settings.py
AUDIO_SPEED_MULTIPLIER = 2.0  # Default 2x speed
AUDIO_SAMPLE_RATE = 16000     # Required by Parakeet-MLX
AUDIO_CHANNELS = 1            # Mono audio
```

## 🔧 Requirements

### System Dependencies

- **FFmpeg**: Required for audio processing

  ```bash
  # macOS
  brew install ffmpeg
  
  # Ubuntu/Debian
  sudo apt update && sudo apt install ffmpeg
  ```

### Python Dependencies

No additional dependencies required - uses existing ffmpeg integration.

## 🚨 Important Notes

### Quality Considerations

- **Recommended Range**: 1.0x - 3.0x for optimal quality
- **Pitch Preservation**: Enabled by default using `atempo` filter
- **Format Standardization**: Audio normalized to 16kHz mono WAV
- **Quality Testing**: Use benchmark mode to test optimal speeds for your content

### Performance Impact

- **Processing Overhead**: Minimal - ffmpeg is very efficient
- **Storage**: Temporary files are automatically cleaned up
- **Memory**: No significant memory impact
- **Compatibility**: Works with all supported platforms (TikTok, YouTube, Facebook, Instagram)

### Backward Compatibility

- **Default Behavior**: 2x speed is now the default (can be changed to 1.0x)
- **Existing Scripts**: Add `--speed 1.0` to maintain original behavior
- **API Changes**: New optional parameters, existing code continues to work

## 🔄 Migration Guide

### Updating Existing Usage

```bash
# Old way (still works, now uses 2x speed by default)
python main.py workflow "URL"

# Explicitly set normal speed
python main.py workflow "URL" --speed 1.0

# Take advantage of speed optimization
python main.py workflow "URL" --speed 2.0  # or 3.0
```

### Code Updates

```python
# Old way
transcriber = AudioTranscriber(settings)
transcriber.transcribe_from_url(url, output_file)

# New way (optional speed configuration)
transcriber = AudioTranscriber(settings)
transcriber.set_speed_multiplier(2.0)  # Configure speed
transcriber.transcribe_from_url(url, output_file)
```

This implementation provides significant performance improvements while maintaining the simplicity and reliability of the original transcription system.
