# social_media_transcriber/core/transcriber.py
"""
Audio transcription module using Parakeet-MLX.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from social_media_transcriber.config.settings import Settings
from social_media_transcriber.utils.file_utils import (
    ensure_directory_exists,
    process_audio_for_transcription,
)

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Transcribes audio using Parakeet-MLX with speed optimization support."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()

    def set_speed_multiplier(self, speed_multiplier: float) -> None:
        if speed_multiplier <= 0:
            raise ValueError("Speed multiplier must be a positive number.")
        if speed_multiplier > 4.0:
            logger.warning(
                "Speed multiplier %.1fx is high and may affect quality.",
                speed_multiplier
            )
        self.settings.audio_speed_multiplier = speed_multiplier
        logger.info("Audio speed multiplier set to %.1fx", speed_multiplier)

    def _generate_title_from_filename(self, file_path: Path) -> str:
        """Generates a clean title from a file name, ignoring the extension."""
        return file_path.stem.replace('_transcript', '').replace('_', ' ')

    def transcribe_audio(
        self,
        audio_file: Path,
        final_output_path: Path, # The desired final path (e.g., with .mdx)
        verbose: bool = False
    ) -> Tuple[Path, str]:
        """
        Transcribes an audio file to text using Parakeet-MLX.
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        ensure_directory_exists(final_output_path.parent)
        processed_audio = None
        
        # parakeet-mlx always outputs .txt, so we create a temporary .txt path
        temp_txt_output = final_output_path.with_suffix('.txt')

        try:
            processed_audio = process_audio_for_transcription(
                input_path=audio_file,
                speed_multiplier=self.settings.audio_speed_multiplier,
            )
            logger.info(
                "✅ Audio processed at %.1fx speed for faster transcription.",
                self.settings.audio_speed_multiplier
            )

            cmd = [
                "parakeet-mlx", str(processed_audio),
                "--output-format", "txt",
                "--output-dir", str(temp_txt_output.parent),
                # Use the stem of the temp file for the output name
                "--output-template", temp_txt_output.stem,
            ]
            if verbose:
                cmd.append("--verbose")

            logger.info("🔄 Starting parakeet-mlx transcription: %s", audio_file.name)
            subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
            logger.info("✅ Parakeet-mlx transcription completed")

            if not temp_txt_output.exists():
                raise FileNotFoundError(f"Transcription failed: temporary file {temp_txt_output} not created.")

            # --- THIS IS THE FIX ---
            # Rename the generated .txt file to the desired final path (.mdx or .txt)
            if temp_txt_output != final_output_path:
                temp_txt_output.rename(final_output_path)
            # --- END OF FIX ---

            title = self._generate_title_from_filename(final_output_path)
            return final_output_path, title

        finally:
            # Cleanup
            if processed_audio and processed_audio.exists():
                processed_audio.unlink()
            # If the temp .txt file still exists (e.g., rename failed), remove it
            if temp_txt_output.exists() and temp_txt_output != final_output_path:
                temp_txt_output.unlink()
            
            try:
                if processed_audio and processed_audio.parent.name.startswith("tmp"):
                    processed_audio.parent.rmdir()
            except OSError:
                pass