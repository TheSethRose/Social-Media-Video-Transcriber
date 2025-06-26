"""
TikTok Transcribe & Thread Generator

A Python package for downloading TikTok videos, transcribing their audio using Parakeet-MLX,
and generating Twitter threads using an N8N AI agent.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .core.downloader import VideoDownloader, TikTokDownloader
from .core.transcriber import AudioTranscriber
from .core.thread_generator import ThreadGenerator
from .utils.bulk_processor import BulkProcessor

__all__ = [
    "VideoDownloader",
    "TikTokDownloader", 
    "AudioTranscriber", 
    "ThreadGenerator",
    "BulkProcessor"
]
