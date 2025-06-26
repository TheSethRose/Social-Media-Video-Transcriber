"""
Configuration settings for TikTok Transcribe package.
"""

from pathlib import Path
from typing import Optional

# Default webhook URL for N8N AI agent
DEFAULT_WEBHOOK_URL = "https://n8n.seth-rose.dev/webhook/d43ce19f-ab1f-4152-90ba-b669b646f0c4"

# Default output directories
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_TRANSCRIPTS_DIR = DEFAULT_OUTPUT_DIR / "transcripts"

# Default bulk processing file
DEFAULT_BULK_FILE = "bulk.txt"

# Audio processing settings
AUDIO_SAMPLE_RATE = 16000  # 16kHz required by Parakeet-MLX
AUDIO_CHANNELS = 1  # Mono

# Video download settings
VIDEO_FORMAT = "b"  # Best quality format for yt-dlp

# File naming patterns
TRANSCRIPT_TEMPLATE = "transcript_{video_id}.txt"
BULK_SESSION_TEMPLATE = "bulk_{operation}_{timestamp}"

class Settings:
    """Configuration settings container."""
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        output_dir: Optional[Path] = None,
        transcripts_dir: Optional[Path] = None,
        bulk_file: Optional[str] = None
    ):
        """Initialize settings with optional overrides."""
        self.webhook_url = webhook_url or DEFAULT_WEBHOOK_URL
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.transcripts_dir = Path(transcripts_dir) if transcripts_dir else DEFAULT_TRANSCRIPTS_DIR
        self.bulk_file = bulk_file or DEFAULT_BULK_FILE
        
        # Audio settings
        self.audio_sample_rate = AUDIO_SAMPLE_RATE
        self.audio_channels = AUDIO_CHANNELS
        
        # Video settings
        self.video_format = VIDEO_FORMAT
        
        # Templates
        self.transcript_template = TRANSCRIPT_TEMPLATE
        self.bulk_session_template = BULK_SESSION_TEMPLATE
