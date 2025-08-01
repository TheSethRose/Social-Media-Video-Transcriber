# social_media_transcriber/config/settings.py
"""
Configuration settings for the Social Media Transcriber package.

This module loads default values from environment variables, allowing for
flexible configuration without code changes.
"""
import os
from pathlib import Path
from typing import Optional

# These can remain as constants or fallbacks
FALLBACK_LLM_MODEL = "google/gemini-flash-1.5"
FALLBACK_OUTPUT_DIR = "output"
FALLBACK_AUDIO_SPEED = 3.0

class Settings:
    """
    Configuration settings container.

    Initializes by loading values from environment variables at runtime,
    ensuring .env file has been processed.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        bulk_file: Optional[str] = None
    ):
        """
        Initialize settings, loading from environment or using fallbacks.
        """
        # --- LLM settings are now loaded here ---
        self.llm_api_key = os.getenv("OPENROUTER_API_KEY")
        self.llm_api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.llm_model = os.getenv("DEFAULT_LLM_MODEL", FALLBACK_LLM_MODEL)

        # --- Other settings are also loaded here ---
        default_speed_str = os.getenv("DEFAULT_AUDIO_SPEED", str(FALLBACK_AUDIO_SPEED))
        try:
            self.audio_speed_multiplier = float(default_speed_str)
        except (ValueError, TypeError):
            self.audio_speed_multiplier = FALLBACK_AUDIO_SPEED

        # CLI options take precedence over environment variables for output_dir
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = Path(os.getenv("DEFAULT_OUTPUT_DIR", FALLBACK_OUTPUT_DIR))

        # Non-environment settings
        self.bulk_file = bulk_file or "bulk.txt"
        self.audio_sample_rate = 16000  # Required by Parakeet-MLX
        self.audio_channels = 1         # Mono

        # Templates
        self.transcript_title_template = "{title}_transcript.txt"
        self.bulk_session_template = "bulk_transcripts_{timestamp}"