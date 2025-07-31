# social_media_transcriber/core/providers/facebook_provider.py
"""Facebook video provider implementation."""

import re
from .base import BaseYtDlpProvider


class FacebookProvider(BaseYtDlpProvider):
    """Provider for Facebook, supporting videos, reels, and pages."""

    @property
    def provider_name(self) -> str:
        return "Facebook"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?(?:facebook\.com|fb\.watch)/"

    def get_content_type(self, url: str) -> str:
        """Determines if a Facebook URL is a video or a profile/page."""
        # URLs for specific videos, reels, or watch pages
        if re.search(r"/(?:videos|watch|reel)/", url) or "fb.watch" in url:
            return "video"
        # URLs that are likely user profiles or pages
        if re.search(r"facebook\.com/([a-zA-Z0-9._-]+)/?$", url):
            return "profile"
        return "unknown"