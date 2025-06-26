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
    
    return parser

def transcribe_single(url: str, output_file: str, settings: Settings) -> None:
    """
    Transcribe a single video.
    
    Args:
        url: Video URL (TikTok or YouTube)
        output_file: Output file path
        settings: Configuration settings
    """
    transcriber = AudioTranscriber(settings)
    output_path = Path(output_file)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🎯 Transcribing single video: {url}")
    
    try:
        result_path = transcriber.transcribe_from_url(url, output_path)
        print(f"✅ Transcript saved to: {result_path.absolute()}")
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        sys.exit(1)

def transcribe_bulk(
    bulk_file: str, 
    output_dir: Optional[str], 
    settings: Settings
) -> None:
    """
    Transcribe multiple TikTok videos from bulk file.
    
    Args:
        bulk_file: Path to bulk file
        output_dir: Optional output directory
        settings: Configuration settings
    """
    bulk_path = Path(bulk_file)
    output_path = Path(output_dir) if output_dir else None
    
    if not bulk_path.exists():
        print(f"❌ Bulk file not found: {bulk_path}")
        sys.exit(1)
    
    processor = BulkProcessor(settings)
    
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
        transcribe_bulk(args.bulk_file, args.output_dir, settings)
    else:
        # Single video mode
        if not args.url:
            print("❌ URL is required for single video mode. Use --bulk for bulk processing.")
            parser.print_help()
            sys.exit(1)
        
        transcribe_single(args.url, args.output, settings)

if __name__ == "__main__":
    main()
