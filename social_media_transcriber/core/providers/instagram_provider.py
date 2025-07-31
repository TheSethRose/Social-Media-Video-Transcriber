# social_media_transcriber/core/providers/instagram_provider.py
"""Instagram video provider implementation."""

import re
from .base import BaseYtDlpProvider


class InstagramProvider(BaseYtDlpProvider):
    """Provider for Instagram, supporting posts, reels, stories, and profiles."""

    @property
    def provider_name(self) -> str:
        return "Instagram"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?instagram\.com/"

    def get_content_type(self, url: str) -> str:
        """Determines if an Instagram URL is a video post or a user profile."""
        # URLs for specific posts (reels, videos, etc.)
        if re.search(r"/(?:p|reel|tv|stories)/", url):
            return "video"
        # URLs that point to a user's main page
        if re.search(r"instagram\.com/([a-zA-Z0-9._]+)/?$", url):
            return "profile"
        return "unknown"