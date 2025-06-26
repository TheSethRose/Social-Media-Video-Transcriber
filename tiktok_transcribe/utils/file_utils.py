"""
File utility functions for TikTok transcription.
"""

import re
import datetime
from pathlib import Path
from typing import List, Optional

def extract_video_id(url: str) -> str:
    """
    Extract video ID from video URL using appropriate provider.
    
    Args:
        url: Video URL (TikTok, YouTube, etc.)
        
    Returns:
        Video ID string or "unknown" if not found
    """
    # TikTok pattern
    tiktok_pattern = r'tiktok\.com/@[^/]+/video/(\d+)'
    match = re.search(tiktok_pattern, url)
    if match:
        return match.group(1)
    
    # YouTube patterns
    youtube_patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'youtube\.com/v/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return "unknown"

def load_urls_from_file(file_path: Path) -> List[str]:
    """
    Load URLs from a text file, filtering out comments and empty lines.
    
    Args:
        file_path: Path to the file containing URLs
        
    Returns:
        List of valid URLs
    """
    if not file_path.exists():
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]
    
    return urls

def save_urls_to_file(file_path: Path, urls: List[str]) -> None:
    """
    Save URLs to a text file.
    
    Args:
        file_path: Path to save the file
        urls: List of URLs to save
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(f"{url}\n")

def create_timestamped_directory(
    base_name: str, 
    parent_dir: Optional[Path] = None
) -> Path:
    """
    Create a directory with a timestamp suffix.
    
    Args:
        base_name: Base name for the directory
        parent_dir: Parent directory (defaults to current directory)
        
    Returns:
        Path to the created directory
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{base_name}_{timestamp}"
    
    if parent_dir:
        session_dir = parent_dir / dir_name
    else:
        session_dir = Path(dir_name)
    
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir

def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
    """
    directory.mkdir(parents=True, exist_ok=True)

def generate_filename(template: str, **kwargs) -> str:
    """
    Generate a filename from a template with keyword substitution.
    
    Args:
        template: Filename template with placeholders
        **kwargs: Values to substitute in the template
        
    Returns:
        Generated filename
    """
    return template.format(**kwargs)

def clean_filename(filename: str) -> str:
    """
    Clean a filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem use
    """
    # Remove or replace characters that aren't filesystem-safe
    invalid_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(invalid_chars, '_', filename)
    
    # Remove excessive whitespace and dots
    cleaned = re.sub(r'\s+', '_', cleaned)
    cleaned = re.sub(r'\.+', '.', cleaned)
    
    # Ensure it doesn't start or end with problematic characters
    cleaned = cleaned.strip('._-')
    
    return cleaned or "unnamed"
