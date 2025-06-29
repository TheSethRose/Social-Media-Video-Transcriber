"""
Command-line interface for complete workflow (transcription only).
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..core.transcriber import AudioTranscriber
from ..utils.bulk_processor import BulkProcessor
from ..utils.file_utils import extract_video_id, generate_filename

def create_workflow_parser() -> argparse.ArgumentParser:
    """Create argument parser for workflow CLI."""
    parser = argparse.ArgumentParser(
        description="Complete video processing workflow: download and transcribe videos from TikTok, YouTube, Facebook, and Instagram."
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
        help="Maximum number of concurrent workers (default: 4)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=3.0,
        help="Audio speed multiplier for faster transcription (1.0=normal, 2.0=2x, 3.0=3x - default: 3.0)"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark tests on different speed settings with the provided URL"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output including real-time transcription words"
    )
    
    return parser

def workflow_single(
    url: str, 
    transcript_file: str, 
    settings: Settings,
    max_videos: Optional[int] = None,
    max_workers: int = 4,
    speed_multiplier: float = 3.0,
    run_benchmark: bool = False,
    verbose: bool = False
) -> None:
    """
    Process a single video or playlist through the complete workflow.
    
    Args:
        url: Video URL (TikTok, YouTube video/playlist/channel, Facebook, or Instagram)
        transcript_file: Output transcript filename
        settings: Configuration settings
        max_videos: Maximum number of videos to process from channels
        max_workers: Number of workers for parallel processing
        speed_multiplier: Audio speed multiplier for faster transcription
        run_benchmark: Whether to run speed benchmark tests
    """
    from ..core.youtube_provider import YouTubeProvider
    from ..utils.bulk_processor import BulkProcessor
    from ..utils.file_utils import create_timestamped_directory
    from ..core.youtube_provider import YouTubeProvider
    from ..core.tiktok_provider import TikTokProvider
    
    # Check if this is a playlist/channel that needs expansion
    
    # YouTube playlist/channel detection
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
        print(f"🚀 Using {max_workers} workers for parallel processing")
        
        # Use bulk processing for multiple videos
        bulk_processor = BulkProcessor(settings, max_workers=max_workers)
        
        # Create a temporary file with the video URLs
        temp_bulk_file = Path("temp_playlist_urls.txt")
        try:
            with open(temp_bulk_file, 'w') as f:
                for video_url in video_urls:
                    f.write(f"{video_url}\n")
            
            # Process using bulk workflow
            successful, failed, output_dir = bulk_processor.process_bulk_workflow(
                temp_bulk_file,
                Path("output"),
                verbose=verbose
            )
            
            print(f"✅ Successfully processed: {len(successful)} videos")
            if failed:
                print(f"❌ Failed to process: {len(failed)} videos")
                
        finally:
            # Clean up temp file
            if temp_bulk_file.exists():
                temp_bulk_file.unlink()
        
        return
    
    # TikTok user profile detection
    tiktok_provider = TikTokProvider()
    if tiktok_provider.validate_url(url) and tiktok_provider.is_playlist_url(url):
        url_type = tiktok_provider.get_url_type(url)
        print(f"🎯 Detected TikTok {url_type}: {url}")
        
        # Extract individual video URLs
        video_urls = tiktok_provider.extract_video_urls(url, max_videos=max_videos)
        if not video_urls:
            print("❌ No videos found in user profile")
            return
        
        print(f"📋 Found {len(video_urls)} videos to process")
        print(f"🚀 Using {max_workers} workers for parallel processing")
        
        # Use bulk processing for multiple videos
        bulk_processor = BulkProcessor(settings, max_workers=max_workers)
        
        # Create a temporary file with the video URLs
        temp_bulk_file = Path("temp_tiktok_urls.txt")
        try:
            with open(temp_bulk_file, 'w') as f:
                for video_url in video_urls:
                    f.write(f"{video_url}\n")
            
            # Process using bulk workflow
            successful, failed, output_dir = bulk_processor.process_bulk_workflow(
                temp_bulk_file,
                Path("output"),
                verbose=verbose
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
    from ..core.downloader import VideoDownloader
    from ..utils.file_utils import generate_filename_from_metadata
    
    transcriber = AudioTranscriber(settings)
    downloader = VideoDownloader(settings)
    
    # Configure speed multiplier
    transcriber.set_speed_multiplier(speed_multiplier)
    
    # Run benchmark if requested
    if run_benchmark:
        print(f"🧪 Running speed benchmark on: {url}")
        try:
            # Download audio first for benchmarking
            temp_audio = downloader.download_audio_only(url)
            transcriber.benchmark_speed_settings(temp_audio)
            
            # Clean up temp audio
            if temp_audio.exists():
                temp_audio.unlink()
            
            return  # Exit after benchmark
        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            return
    
    transcript_path = Path(transcript_file)
    
    # Ensure output directories exist
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🎯 Processing single video: {url}")
    
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
                # Update the transcript path to use the generated filename
                transcript_path = transcript_path.parent / transcript_filename
                print(f"📝 Generated filename: {transcript_filename}")
        except Exception as e:
            print(f"⚠️ Could not extract title, using provided filename: {e}")
        
        # Step 1: Transcribe
        print("📝 Transcribing video...")
        transcriber.transcribe_from_url(url, transcript_path, verbose)
        print(f"✅ Transcript saved to: {transcript_path.absolute()}")
        
        print("🎉 Workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Main entry point for workflow CLI."""
    parser = create_workflow_parser()
    args = parser.parse_args()
    
    # Create settings
    settings = Settings(
        output_dir=Path(args.output_dir) if args.output_dir else Path("output")
    )
    
    if args.bulk:
        # Bulk processing mode
        bulk_path = Path(args.bulk_file)
        output_path = Path(args.output_dir) if args.output_dir else Path("output")
        
        if not bulk_path.exists():
            print(f"❌ Bulk file not found: {bulk_path}")
            sys.exit(1)
        
        processor = BulkProcessor(settings)
        
        print(f"🚀 Starting bulk workflow from: {bulk_path}")
        
        try:
            successful_urls, failed_urls, session_dir = processor.process_bulk_workflow(
                bulk_path,
                output_path,
                progress_callback=BulkProcessor.print_progress,
                verbose=args.verbose
            )
            
            processor.print_summary(
                successful_urls, 
                failed_urls, 
                session_dir, 
                "workflow"
            )
            
        except Exception as e:
            print(f"❌ Bulk workflow failed: {str(e)}")
            sys.exit(1)
    else:
        # Single video mode
        if not args.url:
            print("❌ URL is required for single video mode. Use --bulk for bulk processing.")
            parser.print_help()
            sys.exit(1)
        
        workflow_single(
            args.url, 
            args.transcript_file, 
            settings,
            max_videos=args.max_videos,
            max_workers=args.max_workers,
            speed_multiplier=args.speed,
            run_benchmark=args.benchmark,
            verbose=args.verbose
        )

if __name__ == "__main__":
    main()
