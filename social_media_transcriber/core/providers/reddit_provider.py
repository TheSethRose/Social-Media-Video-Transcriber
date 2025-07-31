# social_media_transcriber/core/providers/reddit_provider.py
"""Reddit video provider implementation."""

import re
from .base import BaseYtDlpProvider


class RedditProvider(BaseYtDlpProvider):
    """Provider for Reddit, supporting posts, subreddits, and user profiles."""

    @property
    def provider_name(self) -> str:
        return "Reddit"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www\.)?reddit\.com/"

    def get_content_type(self, url: str) -> str:
        """Determines if a Reddit URL is a post, subreddit, or user profile."""
        if re.search(r"/comments/", url):
            return "video"  # A single post is treated as a potential video
        if re.search(r"/r/([a-zA-Z0-9_]+)/?$", url):
            return "playlist"  # A subreddit is treated like a playlist
        if re.search(r"/user/([a-zA-Z0-9_-]+)/?$", url):
            return "profile"  # A user's page
        return "unknown"