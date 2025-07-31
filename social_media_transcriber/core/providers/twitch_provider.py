# social_media_transcriber/core/providers/twitch_provider.py
"""Twitch video provider implementation."""

import re
from .base import BaseYtDlpProvider


class TwitchProvider(BaseYtDlpProvider):
    """Provider for Twitch, supporting VODs, clips, and channels."""

    @property
    def provider_name(self) -> str:
        return "Twitch"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.|clips\.)?twitch\.tv/"

    def get_content_type(self, url: str) -> str:
        """Determines if a Twitch URL is a video, clip, or channel."""
        if re.search(r"/(?:videos|clip)/", url) or "clips.twitch.tv" in url:
            return "video"
        # A URL to the base channel page
        if re.search(r"twitch\.tv/([a-zA-Z0-9_]+)/?$", url):
            return "channel"
        return "unknown"