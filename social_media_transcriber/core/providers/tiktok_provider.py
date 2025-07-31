# social_media_transcriber/core/providers/tiktok_provider.py
"""TikTok video provider implementation."""

import re
from .base import BaseYtDlpProvider


class TikTokProvider(BaseYtDlpProvider):
    """Provider for TikTok, supporting videos and user profiles."""

    @property
    def provider_name(self) -> str:
        return "TikTok"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?tiktok\.com/"
    
    def get_content_type(self, url: str) -> str:
        """Determines if a TikTok URL is a single video or a user profile."""
        # A URL with '/video/' is a single video
        if "/video/" in url:
            return "video"
        # A URL with an '@' but no '/video/' is a user profile
        if "/@" in url:
            return "profile"
        return "unknown"