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

logger = logging.getLogger(__name__)


class Downloader:
    """
    A universal downloader that delegates to the appropriate provider.
    """
    def __init__(self) -> None:
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
        """
        discovered_providers = []
        package_path = providers.__path__
        package_name = providers.__name__

        for _, module_name, _ in pkgutil.iter_modules(package_path, prefix=f"{package_name}."):
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
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
        """
        for provider in self._providers:
            if provider.validate_url(url):
                logger.debug("Provider '%s' selected for URL: %s", provider.provider_name, url)
                return provider
        logger.warning("No supported provider found for URL: %s", url)
        return None