"""
Command-line interface for thread generation functionality.
"""

import argparse
import sys
from pathlib import Path

from ..config.settings import Settings
from ..core.thread_generator import ThreadGenerator

def create_thread_parser() -> argparse.ArgumentParser:
    """Create argument parser for thread generation CLI."""
    parser = argparse.ArgumentParser(
        description="Generate Twitter thread files from transcripts."
    )
    
    parser.add_argument(
        "transcript", 
        help="Path to transcript file (required)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output/threads",
        help="Output directory for threads (default: output/threads)"
    )
    
    return parser

def generate_thread(
    transcript_file: str, 
    output_dir: str, 
    settings: Settings
) -> None:
    """
    Generate a Twitter thread from a transcript file.
    
    Args:
        transcript_file: Path to transcript file
        output_dir: Output directory for thread
        settings: Configuration settings
    """
    transcript_path = Path(transcript_file)
    output_path = Path(output_dir)
    
    if not transcript_path.exists():
        print(f"❌ Transcript file not found: {transcript_path}")
        sys.exit(1)
    
    generator = ThreadGenerator(settings)
    
    print(f"🧵 Generating Twitter thread from: {transcript_path}")
    
    try:
        thread_file = generator.generate_thread_from_file(
            transcript_path, 
            output_path
        )
        
        print(f"✅ Thread saved to: {thread_file.absolute()}")
        
    except Exception as e:
        print(f"❌ Thread generation failed: {str(e)}")
        sys.exit(1)

def main() -> None:
    """Main entry point for thread generation CLI."""
    parser = create_thread_parser()
    args = parser.parse_args()
    
    # Create settings
    settings = Settings(
        threads_dir=Path(args.output_dir)
    )
    
    generate_thread(
        args.transcript, 
        args.output_dir, 
        settings
    )

if __name__ == "__main__":
    main()
