"""
Audio transcription module using Parakeet-MLX.
"""

import subprocess
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..utils.file_utils import ensure_directory_exists

class AudioTranscriber:
    """Transcribes audio using Parakeet-MLX."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the transcriber.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings or Settings()
    
    def transcribe_audio(self, audio_file: Path, output_file: Path) -> Path:
        """
        Transcribe audio file to text using Parakeet-MLX.
        
        Args:
            audio_file: Path to the audio file (WAV format)
            output_file: Path for the output transcript file
            
        Returns:
            Path to the generated transcript file
            
        Raises:
            subprocess.CalledProcessError: If transcription fails
            FileNotFoundError: If audio file doesn't exist
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Ensure output directory exists
        ensure_directory_exists(output_file.parent)
        
        # Run Parakeet-MLX transcription
        cmd = [
            "parakeet-mlx",
            str(audio_file),
            "--output-format", "txt",
            "--output-dir", str(output_file.parent),
            "--output-template", output_file.stem
        ]
        
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if not output_file.exists():
            raise FileNotFoundError(f"Transcription failed: {output_file} not found")
        
        return output_file
    
    def transcribe_from_url(self, url: str, output_file: Path) -> Path:
        """
        Download video and transcribe its audio.
        
        Args:
            url: Video URL (TikTok, YouTube, etc.)
            output_file: Path for the output transcript file
            
        Returns:
            Path to the generated transcript file
        """
        from .downloader import VideoDownloader
        
        # Download and convert audio
        downloader = VideoDownloader(self.settings)
        audio_file = downloader.download_audio_only(url)
        
        try:
            # Transcribe the audio
            return self.transcribe_audio(audio_file, output_file)
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
