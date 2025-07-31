# social_media_transcriber/core/providers/x_provider.py
"""X (formerly Twitter) video provider implementation."""

import re
from .base import BaseYtDlpProvider


class XProvider(BaseYtDlpProvider):
    """Provider for X (Twitter), supporting tweet videos and user profiles."""

    @property
    def provider_name(self) -> str:
        return "X (Twitter)"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/"

    def get_content_type(self, url: str) -> str:
        """Determines if an X/Twitter URL is a single tweet or a user profile."""
        # A URL to a specific tweet/status
        if re.search(r"/status/", url):
            return "video"
        # A URL to a user's profile page
        if re.search(r"\.com/([a-zA-Z0-9_]+)/?$", url):
            return "profile"
        return "unknown"