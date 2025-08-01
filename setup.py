# setup.py
"""
Setup script for the Social Media Transcriber package.
"""

from pathlib import Path
from setuptools import find_packages, setup

# Read the README file for the long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="social-media-transcriber",
    version="2.0.0",  # Bump version for new architecture
    author="Seth Rose",
    author_email="admin@sethrose.dev",
    description="A Python tool for downloading and transcribing videos from multiple social media platforms.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thesethrose/social-media-transcriber",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=[
        "yt-dlp>=2023.1.6",
        "requests>=2.28.0",
        "parakeet-mlx>=0.1.0",
        "click>=8.0.0",
        "mlx",
        "python-dotenv>=0.21.0"
    ],
    entry_points={
        "console_scripts": [
            "transcriber=social_media_transcriber.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)