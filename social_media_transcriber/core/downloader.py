# social_media_transcriber/core/downloader.py
"""
Video downloader module responsible for identifying and delegating to the
correct video provider.
"""
import importlib
import inspect
import logging
import pkgutil
from typing import List, Optional

from . import providers
from .providers.base import BaseYtDlpProvider, VideoProvider

# Configure logging
logger = logging.getLogger(__name__)


class Downloader:
    """
    A universal downloader that delegates to the appropriate provider.

    This class dynamically discovers and loads all available `VideoProvider`
    implementations from the `social_media_transcriber.core.providers` package.
    """

    def __init__(self) -> None:
        """Initializes the downloader and dynamically loads all providers."""
        self._providers: List[VideoProvider] = self._discover_providers()
        provider_names = sorted([p.provider_name for p in self._providers])
        if not self._providers:
            logger.warning("No video providers were found or loaded.")
        else:
            logger.info(
                "Downloader initialized with %d providers: %s",
                len(provider_names),
                ", ".join(provider_names),
            )

    def _discover_providers(self) -> List[VideoProvider]:
        """
        Find and instantiate all VideoProvider classes in the providers package.

        Returns:
            A list of instantiated video provider objects.
        """
        discovered_providers = []
        # Get the path and name of the 'providers' package to search within.
        package_path = providers.__path__
        package_name = providers.__name__

        # Iterate over all modules in the 'providers' package.
        for _, module_name, _ in pkgutil.iter_modules(package_path, prefix=f"{package_name}."):
            try:
                # Dynamically import the discovered module.
                module = importlib.import_module(module_name)
                # Look for classes within the module that are providers.
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    # A class is a provider if it inherits from VideoProvider but
                    # is not VideoProvider or BaseYtDlpProvider itself.
                    if (
                        issubclass(obj, VideoProvider)
                        and obj is not VideoProvider
                        and obj is not BaseYtDlpProvider
                    ):
                        discovered_providers.append(obj())
            except Exception as e:
                logger.error("Failed to load provider from module %s: %s", module_name, e)

        return discovered_providers

    def get_provider(self, url: str) -> Optional[VideoProvider]:
        """
        Finds a suitable provider for the given URL.

        Args:
            url: The URL to find a provider for.

        Returns:
            An instance of a supported VideoProvider, or None if no provider
            is found.
        """
        for provider in self._providers:
            if provider.validate_url(url):
                logger.info("Provider '%s' selected for URL: %s", provider.provider_name, url)
                return provider
        logger.warning("No supported provider found for URL: %s", url)
        return None