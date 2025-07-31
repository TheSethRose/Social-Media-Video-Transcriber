# social_media_transcriber/core/providers/youtube_provider.py
"""YouTube video provider implementation."""

import re
from .base import BaseYtDlpProvider


class YouTubeProvider(BaseYtDlpProvider):
    """Provider for YouTube, supporting videos, playlists, and channels."""

    @property
    def provider_name(self) -> str:
        return "YouTube"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/"

    def get_content_type(self, url: str) -> str:
        """Determines if a YouTube URL is a video, playlist, or channel."""
        if re.search(r"/watch\?v=", url) or re.search(r"youtu\.be/", url):
            return "video"
        if re.search(r"/playlist\?list=", url):
            return "playlist"
        # Match channel URLs like /@channelname, /channel/UC..., /c/channelname
        if re.search(r"/(?:@|channel/|c/)", url):
            return "channel"
        return "unknown"