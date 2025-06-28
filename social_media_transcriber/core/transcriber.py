"""
Audio transcription module using Parakeet-MLX.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional

from ..config.settings import Settings
from ..utils.file_utils import ensure_directory_exists, process_audio_for_transcription

class AudioTranscriber:
    """Transcribes audio using Parakeet-MLX with speed optimization support."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the transcriber.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings or Settings()
    
    def set_speed_multiplier(self, speed_multiplier: float) -> None:
        """
        Set the audio speed multiplier for transcription optimization.
        
        Higher values result in faster transcription with minimal quality loss:
        - 1.0 = Normal speed (no optimization)
        - 2.0 = 2x speed (good balance)
        - 3.0 = 3x speed (recommended default)
        
        Args:
            speed_multiplier: Speed multiplier (1.0 to 3.0 recommended)
        """
        if speed_multiplier <= 0:
            raise ValueError("Speed multiplier must be positive")
        if speed_multiplier > 10:
            print(f"⚠️ Warning: Speed multiplier {speed_multiplier}x is very high and may affect quality")
        
        self.settings.audio_speed_multiplier = speed_multiplier
        print(f"🎛️ Audio speed multiplier set to {speed_multiplier}x")

    def transcribe_audio(self, audio_file: Path, output_file: Path, verbose: bool = False) -> Path:
        """
        Transcribe audio file to text using Parakeet-MLX with speed optimization.
        
        This method implements audio speed optimization to reduce transcription time and token usage.
        The audio is processed through ffmpeg at the configured speed multiplier (default 2x)
        before transcription, resulting in faster processing with minimal quality loss.
        
        Args:
            audio_file: Path to the audio file (any format supported by ffmpeg)
            output_file: Path for the output transcript file
            verbose: Enable verbose output including real-time transcription words
            
        Returns:
            Path to the generated transcript file
            
        Raises:
            subprocess.CalledProcessError: If audio processing or transcription fails
            FileNotFoundError: If audio file doesn't exist
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Ensure output directory exists
        ensure_directory_exists(output_file.parent)
        
        # Process audio for optimal transcription (speed up + format conversion)
        processed_audio = None
        try:
            processed_audio = process_audio_for_transcription(
                input_path=audio_file,
                speed_multiplier=self.settings.audio_speed_multiplier,
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
                preserve_pitch=True  # Keep pitch natural for better transcription accuracy
            )
            
            print(f"🚀 Audio processed at {self.settings.audio_speed_multiplier}x speed for faster transcription")
            
            # Run Parakeet-MLX transcription on the processed audio
            cmd = [
                "parakeet-mlx",
                str(processed_audio),
                "--output-format", "txt",
                "--output-dir", str(output_file.parent),
                "--output-template", output_file.stem
            ]
            
            if verbose:
                print(f"🎤 Starting transcription with real-time output...")
                print(f"📝 Words will appear below as they are transcribed:")
                print("─" * 60)
                
                # Add verbose flag to parakeet-mlx and run with real-time output
                cmd.append("--verbose")
                
                # Run with real-time output by not capturing stdout/stderr
                proc = subprocess.run(cmd, check=True, text=True)
                
                print("─" * 60)
                print("✅ Transcription completed!")
            else:
                # Run quietly as before
                proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if not output_file.exists():
                raise FileNotFoundError(f"Transcription failed: {output_file} not found")
            
            return output_file
            
        finally:
            # Clean up temporary processed audio file
            if processed_audio and processed_audio.exists():
                processed_audio.unlink()
                # Clean up parent directory if it's a temp directory
                if processed_audio.parent.name.startswith("tmp"):
                    try:
                        processed_audio.parent.rmdir()
                    except OSError:
                        pass  # Directory not empty or other issue
    
    def transcribe_from_url(self, url: str, output_file: Path, verbose: bool = False) -> Path:
        """
        Download video and transcribe its audio.
        
        Args:
            url: Video URL (TikTok, YouTube, etc.)
            output_file: Path for the output transcript file
            verbose: Enable verbose output including real-time transcription
            
        Returns:
            Path to the generated transcript file
        """
        from .downloader import VideoDownloader
        
        # Download and convert audio
        downloader = VideoDownloader(self.settings)
        audio_file = downloader.download_audio_only(url)
        
        try:
            # Transcribe the audio
            return self.transcribe_audio(audio_file, output_file, verbose)
        finally:
            # Clean up temporary audio file
            if audio_file.exists():
                audio_file.unlink()
            # Clean up parent directory if it's a temp directory
            if audio_file.parent.name.startswith("tmp"):
                try:
                    audio_file.parent.rmdir()
                except OSError:
                    pass  # Directory not empty or other issue
    
    def read_transcript(self, transcript_file: Path) -> str:
        """
        Read transcript content from file.
        
        Args:
            transcript_file: Path to the transcript file
            
        Returns:
            Transcript content as string
            
        Raises:
            FileNotFoundError: If transcript file doesn't exist
        """
        if not transcript_file.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
        
        with open(transcript_file, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def benchmark_speed_settings(self, audio_file: Path, speed_multipliers: List[float] = [1.0, 2.0, 3.0]) -> Dict[float, float]:
        """
        Benchmark different speed multipliers to find optimal settings.
        
        This method helps determine the best speed multiplier for your use case by
        testing transcription times at different speeds on a sample audio file.
        
        Args:
            audio_file: Sample audio file to benchmark
            speed_multipliers: List of speed multipliers to test
            
        Returns:
            Dictionary mapping speed multiplier to transcription time in seconds
        """
        import time
        import tempfile
        
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        results = {}
        original_speed = self.settings.audio_speed_multiplier
        
        for speed in speed_multipliers:
            print(f"🧪 Testing {speed}x speed...")
            
            # Set the speed multiplier
            self.settings.audio_speed_multiplier = speed
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
                tmp_output = Path(tmp_file.name)
            
            try:
                # Time the transcription
                start_time = time.time()
                self.transcribe_audio(audio_file, tmp_output)
                end_time = time.time()
                
                transcription_time = end_time - start_time
                results[speed] = transcription_time
                
                print(f"  ⏱️ {speed}x speed: {transcription_time:.2f}s")
                
            except Exception as e:
                print(f"  ❌ {speed}x speed failed: {e}")
                results[speed] = float('inf')  # Mark as failed
            
            finally:
                # Clean up temp file
                if tmp_output.exists():
                    tmp_output.unlink()
        
        # Restore original speed setting
        self.settings.audio_speed_multiplier = original_speed
        
        # Print summary
        print("\n📊 Benchmark Results:")
        for speed, time_taken in results.items():
            if time_taken != float('inf'):
                speed_improvement = results[1.0] / time_taken if 1.0 in results and results[1.0] > 0 else 1.0
                print(f"  {speed}x speed: {time_taken:.2f}s ({speed_improvement:.1f}x faster than normal)")
            else:
                print(f"  {speed}x speed: FAILED")
        
        return results
