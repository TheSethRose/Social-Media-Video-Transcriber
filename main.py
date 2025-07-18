#!/usr/bin/env python3
"""
Main entry point for Social Media Video Transcriber.

This script provides a unified interface to all functionality:
- Transcription only (single or bulk)
- Complete workflow (single or bulk)
"""

import argparse
import sys
from pathlib import Path

# Add the package to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from social_media_transcriber.cli.transcribe_cli import main as transcribe_main
from social_media_transcriber.cli.workflow_cli import main as workflow_main

def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Social Media Video Transcriber - A complete workflow for processing TikTok, YouTube, Facebook, and Instagram videos",
        prog="main.py"
    )
    
    subparsers = parser.add_subparsers(
        dest="command", 
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Transcribe subcommand
    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe videos (TikTok, YouTube, Facebook, Instagram - single or bulk)"
    )
    transcribe_parser.add_argument("url", nargs='?', help="Video URL (TikTok, YouTube, Facebook, or Instagram - required for single mode)")
    transcribe_parser.add_argument("-o", "--output", default="transcript.txt", help="Output file (default: transcript.txt)")
    transcribe_parser.add_argument("--bulk", action="store_true", help="Process URLs from bulk.txt")
    transcribe_parser.add_argument("--bulk-file", default="bulk.txt", help="Bulk file path (default: bulk.txt)")
    transcribe_parser.add_argument("--output-dir", help="Output directory for bulk mode")
    transcribe_parser.add_argument("--speed", type=float, default=3.0, help="Audio speed multiplier (1.0=normal, 2.0=2x, 3.0=3x - default: 3.0)")
    
    # Workflow subcommand (default)
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Complete workflow: transcribe videos (default)"
    )
    workflow_parser.add_argument("url", nargs='?', help="Video URL (TikTok, YouTube, Facebook, or Instagram - required for single mode)")
    workflow_parser.add_argument("--bulk", action="store_true", help="Process URLs from bulk.txt")
    workflow_parser.add_argument("--bulk-file", default="bulk.txt", help="Bulk file path (default: bulk.txt)")
    workflow_parser.add_argument("--webhook-url", help="N8N webhook URL")
    workflow_parser.add_argument("--transcript-file", default="transcript.txt", help="Transcript filename (single mode)")
    workflow_parser.add_argument("--output-dir", help="Base output directory (bulk mode)")
    workflow_parser.add_argument("--max-videos", type=int, help="Maximum number of videos to process from channels")
    workflow_parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of concurrent workers (default: 4)")
    workflow_parser.add_argument("--speed", type=float, default=3.0, help="Audio speed multiplier (1.0=normal, 2.0=2x, 3.0=3x - default: 3.0)")
    workflow_parser.add_argument("--benchmark", action="store_true", help="Run benchmark tests on different speed settings")
    workflow_parser.add_argument("--verbose", action="store_true", help="Enable verbose output including real-time transcription words")
    
    return parser

def main() -> None:
    """Main entry point."""
    parser = create_main_parser()
    args = parser.parse_args()
    
    # If no command specified, default to workflow
    if not args.command:
        # Check if we have a URL argument (legacy single URL mode)
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # Legacy mode: python main.py <url>
            from social_media_transcriber.cli.workflow_cli import workflow_single
            from social_media_transcriber.config.settings import Settings
            
            url = sys.argv[1]
            settings = Settings()
            
            print("🔄 Running in legacy mode - complete workflow for single video")
            workflow_single(url, "transcript.txt", settings)
            return
        else:
            print("❌ No command specified. Use --help to see available commands.")
            parser.print_help()
            sys.exit(1)
    
    # Route to appropriate CLI module
    if args.command == "transcribe":
        # Reconstruct sys.argv for transcribe CLI
        sys.argv = ["transcribe.py"]
        if hasattr(args, 'url') and args.url:
            sys.argv.append(args.url)
        if args.output != "transcript.txt":
            sys.argv.extend(["-o", args.output])
        if args.bulk:
            sys.argv.append("--bulk")
        if args.bulk_file != "bulk.txt":
            sys.argv.extend(["--bulk-file", args.bulk_file])
        if args.output_dir:
            sys.argv.extend(["--output-dir", args.output_dir])
        if hasattr(args, 'speed') and args.speed != 3.0:
            sys.argv.extend(["--speed", str(args.speed)])
        
        transcribe_main()
        
    elif args.command == "workflow":
        # Reconstruct sys.argv for workflow CLI
        sys.argv = ["workflow.py"]
        if hasattr(args, 'url') and args.url:
            sys.argv.append(args.url)
        if args.bulk:
            sys.argv.append("--bulk")
        if args.bulk_file != "bulk.txt":
            sys.argv.extend(["--bulk-file", args.bulk_file])
        if args.webhook_url:
            sys.argv.extend(["--webhook-url", args.webhook_url])
        if args.transcript_file != "transcript.txt":
            sys.argv.extend(["--transcript-file", args.transcript_file])
        if args.output_dir:
            sys.argv.extend(["--output-dir", args.output_dir])
        if args.max_videos:
            sys.argv.extend(["--max-videos", str(args.max_videos)])
        if args.max_workers != 4:
            sys.argv.extend(["--max-workers", str(args.max_workers)])
        if hasattr(args, 'speed') and args.speed != 3.0:
            sys.argv.extend(["--speed", str(args.speed)])
        if hasattr(args, 'benchmark') and args.benchmark:
            sys.argv.append("--benchmark")
        if hasattr(args, 'verbose') and args.verbose:
            sys.argv.append("--verbose")
        
        workflow_main()

if __name__ == "__main__":
    main()