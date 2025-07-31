# social_media_transcriber/core/providers/vimeo_provider.py
"""Vimeo video provider implementation."""

import re
from .base import BaseYtDlpProvider


class VimeoProvider(BaseYtDlpProvider):
    """Provider for Vimeo, supporting videos, channels, and profiles."""

    @property
    def provider_name(self) -> str:
        return "Vimeo"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?vimeo\.com/"

    def get_content_type(self, url: str) -> str:
        """Determines if a Vimeo URL is a video, playlist, or user profile."""
        # URL pointing to a specific numeric video ID
        if re.search(r"vimeo\.com/(\d+)$", url):
            return "video"
        if re.search(r"/channels/", url) or re.search(r"/showcase/", url):
            return "playlist"
        # URL pointing to a user profile (typically non-numeric)
        if re.search(r"vimeo\.com/([a-zA-Z][a-zA-Z0-9_-]+)$", url):
            return "profile"
        return "unknown"