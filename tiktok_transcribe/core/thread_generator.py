"""
Twitter thread generator module for creating formatted thread files.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..config.settings import Settings
from ..utils.file_utils import ensure_directory_exists, clean_filename

class ThreadGenerator:
    """Generates formatted Twitter thread files from transcripts."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize the thread generator.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings or Settings()
    
    def generate_thread(
        self, 
        transcript: str, 
        output_dir: Path, 
        webhook_url: Optional[str] = None
    ) -> Path:
        """
        Generate a Twitter thread file from a transcript.
        
        Args:
            transcript: The transcript text
            output_dir: Directory to save the generated thread
            webhook_url: Optional webhook URL (unused, kept for compatibility)
            
        Returns:
            Path to the generated thread file
        """
        # Create thread data from transcript
        thread_data = self._create_thread_data(transcript)
        
        # Save the thread to file
        return self._save_thread(thread_data, output_dir)
    
    def generate_thread_from_file(
        self, 
        transcript_file: Path, 
        output_dir: Path,
        webhook_url: Optional[str] = None
    ) -> Path:
        """
        Generate a Twitter thread from a transcript file.
        
        Args:
            transcript_file: Path to the transcript file
            output_dir: Directory to save the generated thread
            webhook_url: Optional webhook URL override
            
        Returns:
            Path to the generated thread file
        """
        # Read transcript from file
        if not transcript_file.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_file}")
        
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript = f.read().strip()
        
        return self.generate_thread(transcript, output_dir, webhook_url)
    
    def _create_thread_data(self, transcript: str) -> Dict[str, Any]:
        """
        Create thread data from transcript text.
        
        Args:
            transcript: The transcript text
            
        Returns:
            Thread data dictionary with topic and formatted content
        """
        # Extract a topic from the transcript (first meaningful sentence)
        lines = [line.strip() for line in transcript.split('\n') if line.strip()]
        topic = "Video Transcript"
        
        if lines:
            # Try to find a good topic from the first few lines
            for line in lines[:3]:
                if len(line) > 20 and not line.lower().startswith(('um', 'uh', 'so')):
                    topic = line[:50] + "..." if len(line) > 50 else line
                    break
        
        # Split transcript into manageable chunks for threads
        threads = self._split_into_threads(transcript)
        
        return {
            "topic": topic,
            "threads": threads
        }
    
    def _split_into_threads(self, transcript: str) -> List[str]:
        """
        Split transcript into thread-sized chunks.
        
        Args:
            transcript: The transcript text
            
        Returns:
            List of thread strings
        """
        # Clean up the transcript
        text = re.sub(r'\s+', ' ', transcript).strip()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        threads = []
        current_thread = ""
        max_length = 250  # Twitter thread length limit (with some buffer)
        
        for sentence in sentences:
            # Check if adding this sentence would exceed the limit
            if len(current_thread) + len(sentence) + 2 > max_length:
                if current_thread:
                    threads.append(current_thread.strip())
                    current_thread = sentence
                else:
                    # Sentence is too long, split it
                    threads.append(sentence[:max_length].strip())
            else:
                if current_thread:
                    current_thread += ". " + sentence
                else:
                    current_thread = sentence
        
        # Add the last thread if not empty
        if current_thread:
            threads.append(current_thread.strip())
        
        return threads or ["No content to process"]
    
    def _save_thread(self, thread_data: Dict[str, Any], output_dir: Path) -> Path:
        """
        Save thread data to a file.
        
        Args:
            thread_data: Thread data dictionary
            output_dir: Directory to save the thread file
            
        Returns:
            Path to the saved thread file
        """
        ensure_directory_exists(output_dir)
        
        # Extract topic for filename
        topic = thread_data.get("topic", "unknown_topic")
        topic = clean_filename(topic)
        
        # Generate filename
        filename = self.settings.thread_template.format(topic=topic)
        output_file = output_dir / filename
        
        # Save thread content
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write topic
            f.write(f"Topic: {thread_data.get('topic', 'N/A')}\n\n")
            
            # Write threads
            threads = thread_data.get("threads", [])
            for i, thread in enumerate(threads, 1):
                f.write(f"Thread {i}:\n")
                f.write(f"{thread}\n\n")
        
        return output_file
