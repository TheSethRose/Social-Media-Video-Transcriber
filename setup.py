"""
Setup script for TikTok Transcribe & Thread Generator package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="tiktok-transcribe",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package for downloading TikTok videos, transcribing audio, and generating Twitter threads",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tiktok-transcribe",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "yt-dlp>=2023.1.6",
        "requests>=2.28.0",
        "parakeet-mlx>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "tiktok-transcribe=social_media_transcriber.cli.workflow_cli:main",
            "tiktok-transcribe-only=social_media_transcriber.cli.transcribe_cli:main",
            "tiktok-thread=social_media_transcriber.cli.thread_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
