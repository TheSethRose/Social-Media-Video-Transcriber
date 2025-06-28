"""
Command-line interface for transcription functionality.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..core.transcriber import AudioTranscriber
from ..utils.bulk_processor import BulkProcessor
from ..utils.file_utils import extract_video_id, generate_filename

def create_transcribe_parser() -> argparse.ArgumentParser:
    """Create argument parser for transcription CLI."""
    parser = argparse.ArgumentParser(
        description="Download and transcribe videos (TikTok, YouTube). Supports bulk processing."
    )
    
    # Make URL optional for bulk mode
    parser.add_argument(
        "url", 
        nargs='?', 
        help="Video URL (TikTok or YouTube - required for single mode)"
    )
    parser.add_argument(
        "-o", "--output",
        default="output/transcripts/transcript.txt",
        help="Destination for the transcript (default: output/transcripts/transcript.txt) - ignored in bulk mode"
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Process all URLs from bulk.txt file instead of single URL"
    )
    parser.add_argument(
        "--bulk-file",
        default="bulk.txt",
        help="Path to bulk file containing URLs (default: bulk.txt)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for bulk mode (default: output)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=3.0,
        help="Audio speed multiplier for faster transcription (1.0=normal, 2.0=2x, 3.0=3x - default: 3.0)"
    )
    
    return parser

def transcribe_single(url: str, output_file: str, settings: Settings, speed_multiplier: float = 3.0) -> None:
    """
    Transcribe a single video or playlist.
    
    Args:
        url: Video URL (TikTok or YouTube) - can be single video or playlist
        output_file: Output file path (ignored for playlists)
        settings: Configuration settings
        speed_multiplier: Audio speed multiplier for faster transcription
    """
    from ..core.downloader import VideoDownloader
    from ..utils.file_utils import generate_filename_from_metadata
    from ..utils.bulk_processor import BulkProcessor
    
    transcriber = AudioTranscriber(settings)
    downloader = VideoDownloader(settings)
    output_path = Path(output_file)
    
    # Configure speed multiplier
    transcriber.set_speed_multiplier(speed_multiplier)
    
    # Check if this is a playlist
    try:
        provider = downloader.get_provider(url)
        if hasattr(provider, 'is_playlist_url') and provider.is_playlist_url(url):
            print(f"📋 Detected playlist URL, processing as playlist...")
            
            # Use bulk processor for playlist handling
            processor = BulkProcessor(settings)
            processor.transcriber.set_speed_multiplier(speed_multiplier)
            
            # Create a temporary "bulk file" with just this playlist URL
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(url + '\n')
                temp_file_path = Path(temp_file.name)
            
            try:
                # Process the playlist
                successful_urls, failed_urls, session_dir = processor.process_bulk_transcription(
                    temp_file_path,
                    output_path.parent,
                    progress_callback=BulkProcessor.print_progress
                )
                
                print(f"✅ Playlist processing complete!")
                print(f"📁 Output directory: {session_dir.absolute()}")
                print(f"✅ Successfully processed: {len(successful_urls)} videos")
                if failed_urls:
                    print(f"❌ Failed: {len(failed_urls)} videos")
                
            finally:
                # Clean up temporary file
                temp_file_path.unlink(missing_ok=True)
            
            return
    except Exception as e:
        print(f"⚠️ Error checking if URL is playlist: {e}")
        # Continue with single video processing
    
    # Single video processing
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🎯 Transcribing single video: {url}")
    
    try:
        # Generate title-based filename if possible
        try:
            provider = downloader.get_provider(url)
            metadata = provider.get_video_metadata(url)
            if metadata:
                # Generate filename using metadata
                transcript_filename = generate_filename_from_metadata(
                    settings.transcript_title_template,
                    metadata
                )
                # Update the output path to use the generated filename
                output_path = output_path.parent / transcript_filename
                print(f"📝 Generated filename: {transcript_filename}")
        except Exception as e:
            print(f"⚠️ Could not extract title, using provided filename: {e}")
        
        result_path = transcriber.transcribe_from_url(url, output_path)
        print(f"✅ Transcript saved to: {result_path.absolute()}")
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        sys.exit(1)

def transcribe_bulk(
    bulk_file: str, 
    output_dir: Optional[str], 
    settings: Settings,
    speed_multiplier: float = 3.0
) -> None:
    """
    Transcribe multiple TikTok videos from bulk file.
    
    Args:
        bulk_file: Path to bulk file
        output_dir: Optional output directory
        settings: Configuration settings
        speed_multiplier: Audio speed multiplier for faster transcription
    """
    bulk_path = Path(bulk_file)
    output_path = Path(output_dir) if output_dir else None
    
    if not bulk_path.exists():
        print(f"❌ Bulk file not found: {bulk_path}")
        sys.exit(1)
    
    processor = BulkProcessor(settings)
    
    # Configure speed multiplier for the transcriber
    processor.transcriber.set_speed_multiplier(speed_multiplier)
    
    print(f"🚀 Starting bulk transcription from: {bulk_path}")
    
    try:
        successful_urls, failed_urls, session_dir = processor.process_bulk_transcription(
            bulk_path,
            output_path,
            progress_callback=BulkProcessor.print_progress
        )
        
        processor.print_summary(
            successful_urls, 
            failed_urls, 
            session_dir, 
            "transcription"
        )
        
        # Update bulk file status
        if successful_urls:
            remaining = len(failed_urls)
            if remaining > 0:
                print(f"📝 {remaining} unprocessed URLs remain in {bulk_path}")
            else:
                print(f"📝 All URLs processed successfully. {bulk_path} is now empty.")
        
    except Exception as e:
        print(f"❌ Bulk transcription failed: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Main entry point for transcription CLI."""
    parser = create_transcribe_parser()
    args = parser.parse_args()
    
    # Create settings
    settings = Settings(
        output_dir=Path(args.output_dir) if args.output_dir else None
    )
    
    if args.bulk:
        # Bulk processing mode
        transcribe_bulk(args.bulk_file, args.output_dir, settings, speed_multiplier=args.speed)
    else:
        # Single video mode
        if not args.url:
            print("❌ URL is required for single video mode. Use --bulk for bulk processing.")
            parser.print_help()
            sys.exit(1)
        
        transcribe_single(args.url, args.output, settings, speed_multiplier=args.speed)

if __name__ == "__main__":
    main()
