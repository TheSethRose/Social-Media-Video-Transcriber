# Adding New Video Providers

This guide explains how to add support for new video platforms. The architecture makes this incredibly simple, especially for platforms supported by `yt-dlp`.

## Overview

The tool uses a provider-based system where `downloader.py` **dynamically discovers and loads** all provider classes from this directory. To add a new provider, you simply add a file here; no other files need to be edited.

The `BaseYtDlpProvider` class handles all the complex work like downloading and metadata extraction.

## Steps to Add a New Provider

### 1. Create the Provider File

Create a new file in `social_media_transcriber/core/providers/`, for example, `vimeo_provider.py`.

### 2. Implement the Provider Class

Your new class must inherit from `BaseYtDlpProvider`. You only need to implement two properties: `provider_name` and `supported_pattern`.

```python
# social_media_transcriber/core/providers/vimeo_provider.py
"""Vimeo video provider implementation."""

from .base import BaseYtDlpProvider

class VimeoProvider(BaseYtDlpProvider):
    """Provider for Vimeo, using the yt-dlp base."""

    @property
    def provider_name(self) -> str:
        return "Vimeo"

    @property
    def supported_pattern(self) -> str:
        return r"(?:https?://)?(?:www.)?vimeo.com/"
````

The `BaseYtDlpProvider` will automatically handle `download_audio`, `Youtube`, and `is_playlist` for any URL that matches your pattern.

### 3. Register the New Provider

**No action is needed!** The `Downloader` will automatically find and load your new `VimeoProvider` class the next time the application runs.

**That's it!** Your new provider is now fully integrated.

## For Platforms Not Supported by `yt-dlp`

If a platform is not supported by `yt-dlp`, you would need to inherit from the base `VideoProvider` ABC and implement the `download_audio` and `Youtube` methods yourself, likely using the platform's API or custom scraping techniques.

### 3. Other Documentation Files

The following documents contain outdated command-line examples that use the old `python main.py workflow` syntax. They should be updated to use the modern `transcriber run` command.

* **File to Update**: `docs/AUDIO_SPEED_OPTIMIZATION.md`
  * Change all instances of `python main.py workflow "URL"` to `transcriber run "URL"`.
  * Remove the `test_audio_speed.py` example, as that test file is not part of the final project structure.

* **File to Update**: `docs/IMPLEMENTATION_SUMMARY.md`
  * Update all command examples from `python main.py ...` to `transcriber ...`.
  * Correct the "Files Modified" section to reflect the new `cli.py` and `core/providers/` structure.

* **File to Update**: `docs/PLAYLIST_FOLDER_NAMING.md`
  * Change `python -m social_media_transcriber.cli.transcribe_cli "URL"` to `transcriber run "URL"`.

Once you make these documentation fixes, your project will be exceptionally clean, consistent, and ready for use.
