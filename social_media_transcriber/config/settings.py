# social_media_transcriber/config/settings.py
"""
Configuration settings for the Social Media Transcriber package.
"""

from pathlib import Path
from typing import Optional

# Default output directories
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_TRANSCRIPTS_DIR = DEFAULT_OUTPUT_DIR / "transcripts"

# Default bulk processing file
DEFAULT_BULK_FILE = "bulk.txt"

# Audio processing settings
AUDIO_SAMPLE_RATE = 16000  # 16kHz required by Parakeet-MLX
AUDIO_CHANNELS = 1  # Mono
AUDIO_SPEED_MULTIPLIER = 3.0  # Default audio speed-up (3x)

# File naming patterns
TRANSCRIPT_TITLE_TEMPLATE = "{title}_transcript.txt"
BULK_SESSION_TEMPLATE = "bulk_transcripts_{timestamp}"


class Settings:
    """Configuration settings container."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        transcripts_dir: Optional[Path] = None,
        bulk_file: Optional[str] = None
    ):
        """
        Initialize settings with optional overrides.

        Args:
            output_dir: The main directory for all output.
            transcripts_dir: The subdirectory for transcript files.
            bulk_file: The default filename for a list of URLs.
        """
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.transcripts_dir = (
            Path(transcripts_dir) if transcripts_dir else DEFAULT_TRANSCRIPTS_DIR
        )
        self.bulk_file = bulk_file or DEFAULT_BULK_FILE

        # Audio settings
        self.audio_sample_rate = AUDIO_SAMPLE_RATE
        self.audio_channels = AUDIO_CHANNELS
        self.audio_speed_multiplier = AUDIO_SPEED_MULTIPLIER

        # Templates
        self.transcript_title_template = TRANSCRIPT_TITLE_TEMPLATE
        self.bulk_session_template = BULK_SESSION_TEMPLATE