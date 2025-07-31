# social_media_transcriber/core/transcriber.py
"""
Audio transcription module using Parakeet-MLX.
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from social_media_transcriber.config.settings import Settings
from social_media_transcriber.utils.file_utils import (
    ensure_directory_exists,
    process_audio_for_transcription,
)

# Configure logging
logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Transcribes audio using Parakeet-MLX with speed optimization support."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """
        Initialize the transcriber.

        Args:
            settings: Configuration settings object.
        """
        self.settings = settings or Settings()

    def set_speed_multiplier(self, speed_multiplier: float) -> None:
        """
        Set the audio speed multiplier for transcription optimization.

        Args:
            speed_multiplier: Speed multiplier (1.0 to 4.0 recommended).
                              1.0 = Normal, 2.0 = 2x speed.
        """
        if speed_multiplier <= 0:
            raise ValueError("Speed multiplier must be a positive number.")
        if speed_multiplier > 4.0:
            logger.warning(
                "Speed multiplier %.1fx is high and may affect quality.",
                speed_multiplier
            )
        self.settings.audio_speed_multiplier = speed_multiplier
        logger.info("Audio speed multiplier set to %.1fx", speed_multiplier)

    def _add_title_to_transcript(self, transcript_file: Path) -> None:
        """
        Adds the video title as a markdown header to the transcript file.

        Args:
            transcript_file: The path to the transcript file.
        """
        try:
            title = transcript_file.stem.replace('_transcript', '').replace('_', ' ')
            with transcript_file.open('r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(f"# {title}\n\n{content}")
        except IOError as e:
            logger.warning("Could not add title to transcript %s: %s", transcript_file, e)

    def transcribe_audio(
        self,
        audio_file: Path,
        output_file: Path,
        verbose: bool = False
    ) -> Path:
        """
        Transcribes an audio file to text using Parakeet-MLX.

        This method uses ffmpeg to apply speed optimization and format
        normalization before passing the audio to the Parakeet-MLX engine.

        Args:
            audio_file: Path to the source audio file.
            output_file: Path for the destination transcript file.
            verbose: If True, enables real-time transcription output.

        Returns:
            The path to the generated transcript file.

        Raises:
            FileNotFoundError: If the input audio file does not exist.
            subprocess.CalledProcessError: If ffmpeg or parakeet-mlx fails.
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        ensure_directory_exists(output_file.parent)
        processed_audio = None

        try:
            processed_audio = process_audio_for_transcription(
                input_path=audio_file,
                speed_multiplier=self.settings.audio_speed_multiplier,
            )
            logger.info(
                "Audio processed at %.1fx speed for faster transcription.",
                self.settings.audio_speed_multiplier
            )

            cmd = [
                "parakeet-mlx", str(processed_audio),
                "--output-format", "txt",
                "--output-dir", str(output_file.parent),
                "--output-template", output_file.stem,
            ]
            if verbose:
                cmd.append("--verbose")

            logger.info("Starting transcription for %s...", audio_file.name)
            subprocess.run(cmd, check=True, capture_output=not verbose, text=True)

            if not output_file.exists():
                raise FileNotFoundError(f"Transcription failed: {output_file} not created.")

            self._add_title_to_transcript(output_file)
            return output_file

        finally:
            if processed_audio and processed_audio.exists():
                processed_audio.unlink()
                # Attempt to clean up temp parent directory
                try:
                    if processed_audio.parent.name.startswith("tmp"):
                        processed_audio.parent.rmdir()
                except OSError:
                    pass  # Ignore if directory is not empty or other issues

    def benchmark_speed_settings(
        self, audio_file: Path, speed_multipliers: List[float] = None
    ) -> Dict[float, float]:
        """
        Benchmarks transcription times at different audio speeds.

        Args:
            audio_file: The sample audio file to use for benchmarking.
            speed_multipliers: A list of speeds to test (e.g., [1.0, 2.0, 3.0]).

        Returns:
            A dictionary mapping each speed to its transcription time in seconds.
        """
        if speed_multipliers is None:
            speed_multipliers = [1.0, 2.0, 3.0]

        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file for benchmark not found: {audio_file}")

        results: Dict[float, float] = {}
        original_speed = self.settings.audio_speed_multiplier

        for speed in speed_multipliers:
            logger.info("--- Benchmarking %.1fx speed ---", speed)
            self.set_speed_multiplier(speed)
            start_time = time.time()
            try:
                with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_f:
                    tmp_output = Path(tmp_f.name)
                self.transcribe_audio(audio_file, tmp_output)
                end_time = time.time()
                transcription_time = end_time - start_time
                results[speed] = transcription_time
                logger.info("Success! Time taken: %.2f seconds", transcription_time)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error("Benchmark failed for %.1fx speed: %s", speed, e)
                results[speed] = float('inf')
            finally:
                if 'tmp_output' in locals() and tmp_output.exists():
                    tmp_output.unlink()

        self.set_speed_multiplier(original_speed)  # Restore original setting
        logger.info("\n--- Benchmark Summary ---")
        base_time = results.get(1.0)
        for speed, time_taken in sorted(results.items()):
            if time_taken == float('inf'):
                logger.info("  %.1fx speed: FAILED", speed)
            elif base_time and base_time != float('inf'):
                improvement = base_time / time_taken if time_taken > 0 else 0
                logger.info(
                    "  %.1fx speed: %.2fs (%.2fx faster than normal)",
                    speed, time_taken, improvement
                )
            else:
                logger.info("  %.1fx speed: %.2fs", speed, time_taken)

        return results