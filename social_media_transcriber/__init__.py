"""
Social Media Video Transcriber

A Python package for downloading videos from TikTok, YouTube, Facebook, and Instagram,
and transcribing their audio using Parakeet-MLX.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .core.downloader import VideoDownloader, TikTokDownloader
from .core.transcriber import AudioTranscriber
from .utils.bulk_processor import BulkProcessor

__all__ = [
    "VideoDownloader",
    "TikTokDownloader", 
    "AudioTranscriber", 
    "BulkProcessor"
]
