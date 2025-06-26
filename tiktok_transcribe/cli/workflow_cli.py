"""
Command-line interface for complete workflow (transcription + thread generation).
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..core.transcriber import AudioTranscriber
from ..core.thread_generator import ThreadGenerator
from ..utils.bulk_processor import BulkProcessor
from ..utils.file_utils import extract_video_id, generate_filename

def create_workflow_parser() -> argparse.ArgumentParser:
    """Create argument parser for workflow CLI."""
    parser = argparse.ArgumentParser(
        description="Complete video processing workflow: download, transcribe, and generate thread files for TikTok, YouTube, Facebook, and Instagram videos."
    )
    
    # Make URL optional for bulk mode
    parser.add_argument(
        "url", 
        nargs='?', 
        help="Video URL (TikTok, YouTube, Facebook, or Instagram - required for single mode)"
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
        "--transcript-file",
        default="output/transcripts/transcript.txt",
        help="Transcript filename for single mode (default: output/transcripts/transcript.txt)"
    )
    parser.add_argument(
        "--thread-dir",
        default="output/threads",
        help="Thread output directory for single mode (default: output/threads)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Base output directory for bulk mode (default: output)"
    )
    parser.add_argument(
        "--max-videos",
        type=int,
        help="Maximum number of videos to process from channels (default: 10 for channels)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of concurrent threads (default: 4)"
    )
    parser.add_argument(
        "--threaded",
        action="store_true",
        help="Use multi-threaded processing for faster bulk operations"
    )
    parser.add_argument(
        "--threads",
        action="store_true",
        help="Generate Twitter threads (disabled by default)"
    )
    
    return parser

def workflow_single(
    url: str, 
    transcript_file: str, 
    thread_dir: str, 
    settings: Settings,
    max_videos: Optional[int] = None,
    max_workers: int = 4,
    use_threading: bool = False,
    generate_threads: bool = False
) -> None:
    """
    Process a single video or playlist through the complete workflow.
    
    Args:
        url: Video URL (TikTok, YouTube video/playlist/channel, Facebook, or Instagram)
        transcript_file: Output transcript filename
        thread_dir: Output directory for thread
        settings: Configuration settings
        max_videos: Maximum number of videos to process from channels
        max_workers: Number of threads for parallel processing
        use_threading: Whether to use multi-threaded processing
        generate_threads: Whether to generate Twitter threads (default: False)
    """
    from ..core.youtube_provider import YouTubeProvider
    from ..utils.bulk_processor import BulkProcessor
    from ..utils.file_utils import create_timestamped_directory
    
    # Check if this is a YouTube playlist/channel that needs expansion
    youtube_provider = YouTubeProvider()
    if youtube_provider.validate_url(url) and youtube_provider.is_playlist_url(url):
        url_type = youtube_provider.get_url_type(url)
        print(f"🎯 Detected YouTube {url_type}: {url}")
        
        # Extract individual video URLs
        video_urls = youtube_provider.extract_video_urls(url, max_videos=max_videos)
        if not video_urls:
            print("❌ No videos found in playlist/channel")
            return
        
        print(f"📋 Found {len(video_urls)} videos to process")
        if use_threading and len(video_urls) > 1:
            print(f"🚀 Using {max_workers} threads for parallel processing")
        
        # Use bulk processing for multiple videos
        bulk_processor = BulkProcessor(settings, max_workers=max_workers)
        
        # Create a temporary file with the video URLs
        temp_bulk_file = Path("temp_playlist_urls.txt")
        try:
            with open(temp_bulk_file, 'w') as f:
                for video_url in video_urls:
                    f.write(f"{video_url}\n")
            
            # Process using bulk workflow (threaded or sequential)
            if use_threading and len(video_urls) > 1:
                successful, failed, output_dir = bulk_processor.process_bulk_workflow_threaded(
                    temp_bulk_file,
                    Path("output"),
                    generate_threads=generate_threads
                )
            else:
                successful, failed, output_dir = bulk_processor.process_bulk_workflow(
                    temp_bulk_file,
                    Path("output"),
                    generate_threads=generate_threads
                )
            
            print(f"✅ Successfully processed: {len(successful)} videos")
            if failed:
                print(f"❌ Failed to process: {len(failed)} videos")
                
        finally:
            # Clean up temp file
            if temp_bulk_file.exists():
                temp_bulk_file.unlink()
        
        return
    
    # Single video processing
    transcriber = AudioTranscriber(settings)
    generator = ThreadGenerator(settings)
    
    transcript_path = Path(transcript_file)
    thread_path = Path(thread_dir)
    
    # Ensure output directories exist
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    thread_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🎯 Processing single video: {url}")
    
    try:
        # Step 1: Transcribe
        print("📝 Transcribing video...")
        transcriber.transcribe_from_url(url, transcript_path)
        print(f"✅ Transcript saved to: {transcript_path.absolute()}")
        
        # Step 2: Generate thread (if enabled)
        if generate_threads:
            print("🧵 Generating Twitter thread...")
            thread_file = generator.generate_thread_from_file(
                transcript_path, 
                thread_path
            )
            print(f"✅ Thread saved to: {thread_file.absolute()}")
        else:
            print("⏭️  Skipping Twitter thread generation")
        
        print("🎉 Workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        sys.exit(1)

def workflow_bulk(
    bulk_file: str, 
    output_dir: Optional[str], 
    settings: Settings,
    generate_threads: bool = False
) -> None:
    """
    Process multiple videos through the complete workflow.
    
    Args:
        bulk_file: Path to bulk file
        output_dir: Optional output directory
        settings: Configuration settings
        generate_threads: Whether to generate Twitter threads (default: False)
    """
    bulk_path = Path(bulk_file)
    output_path = Path(output_dir) if output_dir else Path("output")
    
    if not bulk_path.exists():
        print(f"❌ Bulk file not found: {bulk_path}")
        sys.exit(1)
    
    processor = BulkProcessor(settings)
    
    print(f"🚀 Starting bulk workflow from: {bulk_path}")
    
    try:
        successful_urls, failed_urls, session_dir = processor.process_bulk_workflow(
            bulk_path,
            output_path,
            generate_threads=generate_threads,
            progress_callback=BulkProcessor.print_progress
        )
        
        processor.print_summary(
            successful_urls, 
            failed_urls, 
            session_dir, 
            "workflow"
        )
        
        # Update bulk file status
        if successful_urls:
            remaining = len(failed_urls)
            if remaining > 0:
                print(f"📝 {remaining} unprocessed URLs remain in {bulk_path}")
            else:
                print(f"📝 All URLs processed successfully. {bulk_path} is now empty.")
        
    except Exception as e:
        print(f"❌ Bulk workflow failed: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Main entry point for workflow CLI."""
    parser = create_workflow_parser()
    args = parser.parse_args()
    
    # Create settings
    settings = Settings(
        output_dir=Path(args.output_dir) if args.output_dir else Path("output"),
        threads_dir=Path(args.thread_dir)
    )
    
    if args.bulk:
        # Bulk processing mode
        workflow_bulk(args.bulk_file, args.output_dir, settings, generate_threads=args.threads)
    else:
        # Single video mode
        if not args.url:
            print("❌ URL is required for single video mode. Use --bulk for bulk processing.")
            parser.print_help()
            sys.exit(1)
        
        workflow_single(
            args.url, 
            args.transcript_file, 
            args.thread_dir, 
            settings,
            max_videos=args.max_videos,
            max_workers=args.max_workers,
            use_threading=args.threaded,
            generate_threads=args.threads
        )

if __name__ == "__main__":
    main()
