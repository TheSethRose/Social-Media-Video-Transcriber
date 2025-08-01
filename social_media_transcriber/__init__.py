"""
Social Media Video Transcriber

A Python package for downloading videos from YouTube, TikTok, Facebook, and
Instagram, and transcribing their audio using Parakeet-MLX.
"""

__version__ = "2.0.0"

from .core.downloader import Downloader
from .core.transcriber import AudioTranscriber
from .utils.processing import process_urls

__all__ = [
    "Downloader",
    "AudioTranscriber",
    "process_urls",
]