"""
File utility functions for TikTok transcription.
"""

import re
import datetime
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

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

def sanitize_folder_name(name: str, max_length: int = 100) -> str:
    """
    Sanitize a string to be safe for use as a folder name.
    
    Args:
        name: The original name string
        max_length: Maximum length for the folder name (default: 100)
        
    Returns:
        Sanitized folder name
    """
    # Remove or replace problematic characters
    # Keep alphanumeric, spaces, hyphens, underscores, and basic punctuation
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)  # Remove forbidden chars
    sanitized = re.sub(r'[^\w\s\-_.,()[\]{}]', '', sanitized)  # Keep only safe chars
    sanitized = re.sub(r'\s+', ' ', sanitized)  # Normalize whitespace
    sanitized = sanitized.strip()  # Remove leading/trailing whitespace
    
    # Truncate if too long, but try to keep whole words
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0]
    
    # Ensure we have something valid
    if not sanitized:
        sanitized = "unknown"
    
    return sanitized

def create_playlist_directory(
    playlist_title: str,
    parent_dir: Optional[Path] = None,
    fallback_name: str = "playlist"
) -> Path:
    """
    Create a directory named after a playlist title.
    
    Args:
        playlist_title: The playlist title to use for naming
        parent_dir: Parent directory (defaults to current directory)
        fallback_name: Fallback name if title is invalid
        
    Returns:
        Path to the created directory
    """
    # Sanitize the playlist title for use as a folder name
    folder_name = sanitize_folder_name(playlist_title)
    
    # If sanitization results in an empty or very short name, use fallback
    if len(folder_name.strip()) < 3:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{fallback_name}_{timestamp}"
    
    if parent_dir:
        playlist_dir = parent_dir / folder_name
    else:
        playlist_dir = Path(folder_name)
    
    # Handle potential naming conflicts by adding a number suffix
    original_name = folder_name
    counter = 1
    while playlist_dir.exists():
        folder_name = f"{original_name}_{counter}"
        if parent_dir:
            playlist_dir = parent_dir / folder_name
        else:
            playlist_dir = Path(folder_name)
        counter += 1
    
    playlist_dir.mkdir(parents=True, exist_ok=True)
    return playlist_dir

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

def generate_filename_from_metadata(template: str, metadata: Dict[str, Any], fallback_template: Optional[str] = None, **kwargs) -> str:
    """
    Generate a filename from a template using video metadata.
    
    Args:
        template: Filename template with placeholders for metadata fields
        metadata: Video metadata dictionary containing title, video_id, uploader, etc.
        fallback_template: Template to use if metadata is incomplete
        **kwargs: Additional values to substitute in the template
        
    Returns:
        Generated filename with cleaned title
    """
    # Start with metadata and add any additional kwargs
    format_data = metadata.copy()
    format_data.update(kwargs)
    
    # Clean the title for filesystem use
    if 'title' in format_data and format_data['title']:
        format_data['title'] = clean_filename(format_data['title'])
        
        # Truncate very long titles
        if len(format_data['title']) > 100:
            format_data['title'] = format_data['title'][:97] + "..."
    
    try:
        # Try to format with the preferred template
        return template.format(**format_data)
    except KeyError as e:
        # If a required field is missing, fall back to the fallback template or basic template
        if fallback_template:
            try:
                return fallback_template.format(**format_data)
            except KeyError:
                pass
        
        # Final fallback using video_id
        video_id = format_data.get('video_id', 'unknown')
        base_name = template.split('.')[0] if '.' in template else template
        extension = template.split('.')[-1] if '.' in template else 'txt'
        return f"{base_name}_{video_id}.{extension}"

def speed_up_audio(
    input_audio_path: Path, 
    speed_multiplier: float = 2.0,
    output_path: Optional[Path] = None,
    preserve_pitch: bool = True
) -> Path:
    """
    Speed up audio using ffmpeg while optionally preserving pitch.
    
    This function implements the audio speed optimization suggested for faster transcription.
    According to the source, running audio through ffmpeg at 2x or 3x speed before transcribing
    results in fewer tokens and less time waiting with almost no drop in transcription quality.
    
    Args:
        input_audio_path: Path to the input audio file
        speed_multiplier: Speed multiplier (1.0 = normal, 2.0 = 2x, 3.0 = 3x)
        output_path: Optional output path (defaults to temp file)
        preserve_pitch: Whether to preserve pitch while speeding up (uses atempo filter)
        
    Returns:
        Path to the speed-adjusted audio file
        
    Raises:
        subprocess.CalledProcessError: If ffmpeg command fails
        FileNotFoundError: If input audio file doesn't exist
    """
    if not input_audio_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
    
    if speed_multiplier <= 0:
        raise ValueError("Speed multiplier must be positive")
    
    # Create output path if not provided
    if output_path is None:
        # Create temporary file with same extension
        suffix = input_audio_path.suffix or '.wav'
        temp_file = tempfile.NamedTemporaryFile(suffix=f'_speed{speed_multiplier}x{suffix}', delete=False)
        output_path = Path(temp_file.name)
        temp_file.close()
    
    # Ensure output directory exists
    ensure_directory_exists(output_path.parent)
    
    # Build ffmpeg command
    cmd = ['ffmpeg', '-i', str(input_audio_path), '-y']  # -y to overwrite output
    
    if preserve_pitch and speed_multiplier != 1.0:
        # Use atempo filter to change speed while preserving pitch
        # atempo filter has a range limit of 0.5 to 100.0
        # For values outside this range, we need to chain multiple atempo filters
        if speed_multiplier > 2.0:
            # For speeds > 2x, chain multiple atempo filters
            # e.g., 3x = 1.5 * 2.0, 4x = 2.0 * 2.0
            filters = []
            remaining_speed = speed_multiplier
            while remaining_speed > 2.0:
                filters.append('atempo=2.0')
                remaining_speed /= 2.0
            if remaining_speed != 1.0:
                filters.append(f'atempo={remaining_speed:.3f}')
            filter_chain = ','.join(filters)
        else:
            # Single atempo filter for speeds <= 2x
            filter_chain = f'atempo={speed_multiplier:.3f}'
        
        cmd.extend(['-filter:a', filter_chain])
    else:
        # Simple speed change without pitch preservation (faster processing)
        # This changes both speed and pitch
        cmd.extend(['-filter:a', f'tempo={speed_multiplier:.3f}'])
    
    # Add output path
    cmd.append(str(output_path))
    
    try:
        # Run ffmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if not output_path.exists():
            raise FileNotFoundError(f"Speed adjustment failed: {output_path} not created")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        # Clean up output file if it was created
        if output_path.exists():
            output_path.unlink()
        
        error_msg = f"ffmpeg failed to speed up audio: {e.stderr if e.stderr else str(e)}"
        raise subprocess.CalledProcessError(e.returncode, cmd, error_msg)

def convert_audio_format(
    input_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
    channels: int = 1,
    audio_format: str = 'wav'
) -> Path:
    """
    Convert audio to the specified format and settings.
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        sample_rate: Target sample rate in Hz
        channels: Number of audio channels (1 = mono, 2 = stereo)
        audio_format: Output audio format
        
    Returns:
        Path to converted audio file
        
    Raises:
        subprocess.CalledProcessError: If conversion fails
        FileNotFoundError: If input file doesn't exist
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")
    
    # Ensure output directory exists
    ensure_directory_exists(output_path.parent)
    
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-ar', str(sample_rate),      # Sample rate
        '-ac', str(channels),         # Audio channels
        '-y',                         # Overwrite output
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if not output_path.exists():
            raise FileNotFoundError(f"Audio conversion failed: {output_path} not created")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        error_msg = f"ffmpeg failed to convert audio: {e.stderr if e.stderr else str(e)}"
        raise subprocess.CalledProcessError(e.returncode, cmd, error_msg)

def process_audio_for_transcription(
    input_path: Path,
    speed_multiplier: float = 2.0,
    sample_rate: int = 16000,
    channels: int = 1,
    preserve_pitch: bool = True,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Process audio file for optimal transcription by speeding it up and normalizing format.
    
    This function combines audio speed optimization with format normalization in a single step.
    It implements the speed optimization technique that reduces transcription time and token usage
    with minimal quality loss.
    
    Args:
        input_path: Path to input audio file
        speed_multiplier: Speed multiplier for faster transcription (2.0 recommended)
        sample_rate: Target sample rate (16000 Hz for Parakeet-MLX)
        channels: Audio channels (1 for mono)
        preserve_pitch: Whether to preserve pitch during speed change
        output_dir: Optional output directory (defaults to temp directory)
        
    Returns:
        Path to processed audio file ready for transcription
        
    Raises:
        subprocess.CalledProcessError: If processing fails
        FileNotFoundError: If input file doesn't exist
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")
    
    # Create output path
    if output_dir is None:
        # Use temp directory
        temp_file = tempfile.NamedTemporaryFile(suffix='_processed.wav', delete=False)
        output_path = Path(temp_file.name)
        temp_file.close()
    else:
        ensure_directory_exists(output_dir)
        output_path = output_dir / f"{input_path.stem}_speed{speed_multiplier}x_processed.wav"
    
    # Build comprehensive ffmpeg command that does both speed and format conversion
    cmd = ['ffmpeg', '-i', str(input_path), '-y']
    
    # Build filter chain
    filters = []
    
    # Speed adjustment filter
    if speed_multiplier != 1.0:
        if preserve_pitch and speed_multiplier > 2.0:
            # Chain multiple atempo filters for speeds > 2x
            remaining_speed = speed_multiplier
            while remaining_speed > 2.0:
                filters.append('atempo=2.0')
                remaining_speed /= 2.0
            if remaining_speed != 1.0:
                filters.append(f'atempo={remaining_speed:.3f}')
        elif preserve_pitch:
            filters.append(f'atempo={speed_multiplier:.3f}')
        else:
            filters.append(f'tempo={speed_multiplier:.3f}')
    
    # Apply filters if any
    if filters:
        cmd.extend(['-filter:a', ','.join(filters)])
    
    # Audio format settings
    cmd.extend([
        '-ar', str(sample_rate),    # Sample rate
        '-ac', str(channels),       # Channels
        '-acodec', 'pcm_s16le',     # PCM 16-bit little-endian for wav
        str(output_path)
    ])
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if not output_path.exists():
            raise FileNotFoundError(f"Audio processing failed: {output_path} not created")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        # Clean up output file if it was created
        if output_path.exists():
            output_path.unlink()
        
        error_msg = f"ffmpeg failed to process audio: {e.stderr if e.stderr else str(e)}"
        raise subprocess.CalledProcessError(e.returncode, cmd, error_msg)
