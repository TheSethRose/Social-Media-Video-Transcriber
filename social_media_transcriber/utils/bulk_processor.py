"""
Bulk processing module for handling multiple videos from various providers.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple, Callable

from ..config.settings import Settings
from ..core.transcriber import AudioTranscriber
from ..core.downloader import VideoDownloader
from ..utils.file_utils import (
    load_urls_from_file, 
    save_urls_to_file, 
    create_timestamped_directory,
    create_playlist_directory,
    extract_video_id,
    generate_filename,
    generate_filename_from_metadata
)

class BulkProcessor:
    """Handles bulk processing of multiple videos from various providers with multi-threading support."""
    
    def __init__(self, settings: Optional[Settings] = None, max_workers: int = 4):
        """
        Initialize the bulk processor.
        
        Args:
            settings: Configuration settings
            max_workers: Maximum number of concurrent threads (default: 4)
        """
        self.settings = settings or Settings()
        self.max_workers = max_workers
        self.transcriber = AudioTranscriber(self.settings)
        self.downloader = VideoDownloader(self.settings)
        self._progress_lock = threading.Lock()
    
    def expand_urls(self, urls: List[str]) -> List[str]:
        """
        Legacy method for backward compatibility with threaded processing.
        Expand URLs to individual video URLs without playlist context.
        
        Args:
            urls: List of URLs (may include playlists/channels)
            
        Returns:
            List of individual video URLs
        """
        expanded_data = self.expand_urls_with_context(urls)
        return [video_url for video_url, _, _ in expanded_data]
    
    def expand_urls_with_context(self, urls: List[str]) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """
        Expand URLs that may contain playlists or channels into individual video URLs,
        keeping track of which playlist/channel they came from.
        
        Args:
            urls: List of URLs (may include playlists/channels)
            
        Returns:
            List of tuples: (video_url, playlist_title, playlist_id)
            For non-playlist URLs: (video_url, None, None)
        """
        expanded_data = []
        
        for url in urls:
            try:
                # Get the appropriate provider for this URL
                provider = self.downloader.get_provider(url)
                
                # Check if this is a playlist/channel
                if hasattr(provider, 'is_playlist_url') and provider.is_playlist_url(url):
                    # Get playlist metadata first
                    playlist_title = None
                    playlist_id = None
                    
                    try:
                        # Try to get playlist metadata
                        playlist_metadata = provider.get_playlist_metadata(url)
                        playlist_title = playlist_metadata.get('title', 'Unknown Playlist')
                        playlist_id = playlist_metadata.get('playlist_id', 'unknown')
                        print(f"📋 Found playlist: {playlist_title}")
                    except (AttributeError, Exception) as e:
                        print(f"⚠️ Could not get playlist metadata for {url}: {e}")
                        playlist_title = "Unknown Playlist"
                        playlist_id = "unknown"
                    
                    # Now expand to individual video URLs
                    individual_urls = provider.extract_video_urls(url)
                    
                    # Add all videos with playlist context
                    for video_url in individual_urls:
                        expanded_data.append((video_url, playlist_title, playlist_id))
                    
                    # Print expansion info
                    if len(individual_urls) > 1:
                        print(f"� Expanded playlist into {len(individual_urls)} videos")
                    elif len(individual_urls) == 0:
                        print(f"⚠️ No videos found in playlist {url}")
                else:
                    # Single video URL
                    expanded_data.append((url, None, None))
                    
            except Exception as e:
                print(f"⚠️ Could not process URL {url}: {str(e)}")
                # If processing fails, treat as single video
                expanded_data.append((url, None, None))
        
        return expanded_data
    
    def generate_filename_with_metadata(self, provider, video_url: str) -> str:
        """Generate a filename using video metadata (title) with fallback to video_id.
        
        Args:
            provider: The video provider instance
            video_url: The video URL to extract metadata from
            
        Returns:
            Generated filename for the transcript
        """
        try:
            # Try to get video metadata for title-based filename
            metadata = provider.get_video_metadata(video_url)
            if metadata:
                return generate_filename_from_metadata(
                    self.settings.transcript_title_template,
                    metadata
                )
        except Exception as e:
            print(f"⚠️ Failed to get metadata for {video_url}: {e}")
        
        # Fallback to video_id based filename
        try:
            video_id = provider.extract_video_id(video_url)
            return generate_filename(
                self.settings.transcript_template,
                video_id=video_id
            )
        except Exception as e:
            print(f"⚠️ Failed to extract video_id for {video_url}: {e}")
            
        # Final fallback to generic filename
        return f"transcript_{int(time.time())}.txt"
    
    def process_bulk_transcription(
        self,
        bulk_file: Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[str], List[str], Path]:
        """
        Process multiple videos for transcription only.
        
        Args:
            bulk_file: Path to file containing URLs
            output_dir: Optional output directory override
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_urls, failed_urls, session_directory)
        """
        urls = load_urls_from_file(bulk_file)
        if not urls:
            raise ValueError(f"No URLs found in {bulk_file}")
        
        # Expand URLs with playlist context
        print(f"🔍 Expanding URLs...")
        expanded_data = self.expand_urls_with_context(urls)
        print(f"📹 Processing {len(expanded_data)} video(s) for transcription")
        
        # Create base session directory
        base_output_dir = output_dir or self.settings.output_dir
        
        # Group videos by playlist (None for non-playlist videos)
        playlist_groups = {}
        for video_url, playlist_title, playlist_id in expanded_data:
            if playlist_title:
                # Group by playlist
                key = (playlist_title, playlist_id)
                if key not in playlist_groups:
                    playlist_groups[key] = []
                playlist_groups[key].append(video_url)
            else:
                # Single videos go in a timestamped directory
                key = (None, None)
                if key not in playlist_groups:
                    playlist_groups[key] = []
                playlist_groups[key].append(video_url)
        
        successful_urls = []
        failed_urls = []
        session_dir = None
        
        # Process each group
        for (playlist_title, playlist_id), video_urls in playlist_groups.items():
            if playlist_title:
                # Create playlist-named directory
                group_dir = create_playlist_directory(
                    playlist_title,
                    base_output_dir,
                    f"playlist_{playlist_id}"
                )
                print(f"📁 Created playlist directory: {group_dir.name}")
            else:
                # Create timestamped directory for non-playlist videos
                group_dir = create_timestamped_directory(
                    "bulk_transcription",
                    base_output_dir
                )
                print(f"📁 Created session directory: {group_dir.name}")
            
            # Set session_dir to the first directory created (for return value)
            if session_dir is None:
                session_dir = group_dir
            
            # Process videos in this group
            for i, url in enumerate(video_urls, 1):
                total_in_group = len(video_urls)
                if progress_callback:
                    progress_callback(i, total_in_group, url)
                
                try:
                    # Get provider for this URL
                    provider = self.downloader.get_provider(url)
                    
                    # Generate transcript filename using metadata
                    transcript_filename = self.generate_filename_with_metadata(provider, url)
                    transcript_file = group_dir / transcript_filename
                    
                    # Transcribe the video
                    self.transcriber.transcribe_from_url(url, transcript_file)
                    successful_urls.append(url)
                    
                except Exception as e:
                    print(f"❌ Failed to process video {i}/{total_in_group}: {str(e)}")
                    failed_urls.append(url)
                    continue
        
        # Update bulk file (remove original URLs that had all their videos processed successfully)
        self._update_bulk_file_with_expansion_context(
            bulk_file, urls, successful_urls, expanded_data
        )
        
        return successful_urls, failed_urls, session_dir or base_output_dir
    
    def process_bulk_workflow(
        self,
        bulk_file: Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[str], List[str], Path]:
        """
        Process multiple videos for complete workflow (transcription only).
        
        Args:
            bulk_file: Path to file containing URLs
            output_dir: Optional output directory override
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_urls, failed_urls, session_directory)
        """
        # For now, workflow is just transcription, so delegate to the transcription method
        return self.process_bulk_transcription(bulk_file, output_dir, progress_callback)
    
    def _update_bulk_file(
        self, 
        bulk_file: Path, 
        original_urls: List[str], 
        successful_urls: List[str]
    ) -> None:
        """
        Update bulk file by removing successfully processed URLs.
        
        Args:
            bulk_file: Path to the bulk file
            original_urls: Original list of URLs
            successful_urls: URLs that were processed successfully
        """
        if successful_urls:
            remaining_urls = [url for url in original_urls if url not in successful_urls]
            save_urls_to_file(bulk_file, remaining_urls)
    
    def _update_bulk_file_with_expansion(
        self, 
        bulk_file: Path, 
        original_urls: List[str], 
        successful_urls: List[str],
        expanded_urls: List[str]
    ) -> None:
        """
        Update bulk file by removing original URLs whose expanded videos were all processed successfully.
        
        Args:
            bulk_file: Path to the bulk file
            original_urls: Original list of URLs (may include playlists/channels)
            successful_urls: Individual video URLs that were processed successfully
            expanded_urls: All individual video URLs that were expanded from originals
        """
        if not successful_urls:
            return
            
        remaining_original_urls = []
        
        for original_url in original_urls:
            try:
                # Get the expanded URLs for this original URL
                provider = self.downloader.get_provider(original_url)
                videos_from_this_url = provider.extract_video_urls(original_url)
                
                # Check if ALL videos from this original URL were processed successfully
                all_successful = all(video_url in successful_urls for video_url in videos_from_this_url)
                
                if not all_successful:
                    # Keep this original URL if not all its videos were processed
                    remaining_original_urls.append(original_url)
                    
            except Exception as e:
                print(f"⚠️ Error checking expansion for {original_url}: {str(e)}")
                # Keep the URL if we can't check it
                remaining_original_urls.append(original_url)
        
        # Save the remaining URLs back to the bulk file
        save_urls_to_file(bulk_file, remaining_original_urls)
    
    def _update_bulk_file_with_expansion_context(
        self, 
        bulk_file: Path, 
        original_urls: List[str], 
        successful_urls: List[str],
        expanded_data: List[Tuple[str, Optional[str], Optional[str]]]
    ) -> None:
        """
        Update bulk file by removing original URLs whose expanded videos were all processed successfully.
        
        Args:
            bulk_file: Path to the bulk file
            original_urls: Original list of URLs (may include playlists/channels)
            successful_urls: Individual video URLs that were processed successfully
            expanded_data: List of (video_url, playlist_title, playlist_id) tuples
        """
        if not successful_urls:
            return
            
        # Build a mapping from original URL to expanded videos
        original_to_expanded = {}
        
        for original_url in original_urls:
            try:
                # Get the expanded URLs for this original URL
                provider = self.downloader.get_provider(original_url)
                videos_from_this_url = provider.extract_video_urls(original_url)
                original_to_expanded[original_url] = videos_from_this_url
            except Exception as e:
                print(f"⚠️ Error checking expansion for {original_url}: {str(e)}")
                original_to_expanded[original_url] = [original_url]  # Treat as single video
        
        remaining_original_urls = []
        
        for original_url in original_urls:
            videos_from_this_url = original_to_expanded.get(original_url, [original_url])
            
            # Check if ALL videos from this original URL were processed successfully
            all_successful = all(video_url in successful_urls for video_url in videos_from_this_url)
            
            if not all_successful:
                # Keep this original URL if not all its videos were processed
                remaining_original_urls.append(original_url)
        
        # Save the remaining URLs back to the bulk file
        save_urls_to_file(bulk_file, remaining_original_urls)

    @staticmethod
    def print_progress(current: int, total: int, url: str) -> None:
        """
        Default progress callback that prints to console.
        
        Args:
            current: Current item number
            total: Total number of items
            url: Current URL being processed
        """
        print(f"\n📹 Processing video {current}/{total}: {url}")
    
    @staticmethod
    def print_summary(
        successful_urls: List[str], 
        failed_urls: List[str], 
        session_dir: Path,
        operation: str = "processing"
    ) -> None:
        """
        Print a summary of bulk processing results.
        
        Args:
            successful_urls: URLs that were processed successfully
            failed_urls: URLs that failed to process
            session_dir: Directory where output was saved
            operation: Type of operation (e.g., "processing", "transcription")
        """
        total = len(successful_urls) + len(failed_urls)
        
        print(f"\n🎉 Bulk {operation} completed!")
        print(f"✅ Successfully processed: {len(successful_urls)}/{total} videos")
        
        if failed_urls:
            print(f"❌ Failed: {len(failed_urls)} videos")
        
        print(f"📁 Output saved to: {session_dir.absolute()}")
    
    def _process_single_video_transcription(self, url: str, session_dir: Path, video_index: int, total_videos: int) -> Tuple[str, bool, str]:
        """
        Process a single video for transcription (thread-safe).
        
        Args:
            url: Video URL
            session_dir: Output directory
            video_index: Current video index (1-based)
            total_videos: Total number of videos
            
        Returns:
            Tuple of (url, success, error_message)
        """
        try:
            # Get provider for this URL
            provider = self.downloader.get_provider(url)
            
            # Generate transcript filename using metadata
            transcript_filename = self.generate_filename_with_metadata(provider, url)
            transcript_file = session_dir / transcript_filename
            
            with self._progress_lock:
                print(f"🎬 [{video_index}/{total_videos}] Processing: {url}")
            
            # Transcribe the video
            self.transcriber.transcribe_from_url(url, transcript_file)
            
            with self._progress_lock:
                print(f"✅ [{video_index}/{total_videos}] Completed: {transcript_file.name}")
            
            return url, True, ""
            
        except Exception as e:
            error_msg = str(e)
            with self._progress_lock:
                print(f"❌ [{video_index}/{total_videos}] Failed: {error_msg}")
            return url, False, error_msg
    
    def _process_single_video_workflow(self, url: str, session_dir: Path, video_index: int, total_videos: int) -> Tuple[str, bool, str]:
        """
        Process a single video for complete workflow (thread-safe).
        
        Args:
            url: Video URL
            session_dir: Output directory
            video_index: Current video index (1-based)
            total_videos: Total number of videos
            
        Returns:
            Tuple of (url, success, error_message)
        """
        try:
            # Get provider for this URL
            provider = self.downloader.get_provider(url)
            
            # Generate transcript filename using metadata
            transcript_filename = self.generate_filename_with_metadata(provider, url)
            transcript_file = session_dir / transcript_filename
            
            with self._progress_lock:
                print(f"🎬 [{video_index}/{total_videos}] Processing: {url}")
            
            # Step 1: Transcribe
            self.transcriber.transcribe_from_url(url, transcript_file)
            
            with self._progress_lock:
                print(f"✅ [{video_index}/{total_videos}] Completed: {transcript_file.name}")
            
            return url, True, ""
            
        except Exception as e:
            error_msg = str(e)
            with self._progress_lock:
                print(f"❌ [{video_index}/{total_videos}] Failed: {error_msg}")
            return url, False, error_msg

    def process_bulk_transcription_threaded(
        self,
        bulk_file: Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[str], List[str], Path]:
        """
        Process multiple videos for transcription only using multi-threading.
        
        Args:
            bulk_file: Path to file containing URLs
            output_dir: Optional output directory override
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_urls, failed_urls, session_directory)
        """
        urls = load_urls_from_file(bulk_file)
        if not urls:
            raise ValueError(f"No URLs found in {bulk_file}")
        
        # Expand URLs (playlists/channels into individual videos)
        print(f"🔍 Expanding URLs...")
        expanded_urls = self.expand_urls(urls)
        print(f"📹 Processing {len(expanded_urls)} video(s) with {self.max_workers} threads")
        
        # Create session directory
        session_dir = create_timestamped_directory(
            "bulk_transcription",
            output_dir or self.settings.output_dir
        )
        
        successful_urls = []
        failed_urls = []
        
        # Process videos in parallel
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(
                    self._process_single_video_transcription, 
                    url, 
                    session_dir, 
                    i + 1, 
                    len(expanded_urls)
                ): url 
                for i, url in enumerate(expanded_urls)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url, success, error_msg = future.result()
                if success:
                    successful_urls.append(url)
                else:
                    failed_urls.append(url)
                    
                if progress_callback:
                    progress_callback(
                        len(successful_urls) + len(failed_urls), 
                        len(expanded_urls), 
                        url
                    )
        
        elapsed_time = time.time() - start_time
        print(f"🏁 Completed in {elapsed_time:.1f}s - Success: {len(successful_urls)}, Failed: {len(failed_urls)}")
        
        # Update bulk file (remove original URLs that had all their videos processed successfully)
        self._update_bulk_file_with_expansion(bulk_file, urls, successful_urls, expanded_urls)
        
        return successful_urls, failed_urls, session_dir

    def process_bulk_workflow_threaded(
        self,
        bulk_file: Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[str], List[str], Path]:
        """
        Process multiple videos for complete workflow (transcription) using multi-threading.
        
        Args:
            bulk_file: Path to file containing URLs
            output_dir: Optional output directory override
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (successful_urls, failed_urls, session_directory)
        """
        urls = load_urls_from_file(bulk_file)
        if not urls:
            raise ValueError(f"No URLs found in {bulk_file}")
        
        # Expand URLs (playlists/channels into individual videos)
        print(f"🔍 Expanding URLs...")
        expanded_urls = self.expand_urls(urls)
        print(f"📹 Processing {len(expanded_urls)} video(s) with {self.max_workers} threads")
        
        # Create session directory
        session_dir = create_timestamped_directory(
            "bulk_processing",
            output_dir or self.settings.output_dir
        )
        
        successful_urls = []
        failed_urls = []
        
        # Process videos in parallel
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(
                    self._process_single_video_workflow, 
                    url, 
                    session_dir, 
                    i + 1, 
                    len(expanded_urls)
                ): url 
                for i, url in enumerate(expanded_urls)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url, success, error_msg = future.result()
                if success:
                    successful_urls.append(url)
                else:
                    failed_urls.append(url)
                    
                if progress_callback:
                    progress_callback(
                        len(successful_urls) + len(failed_urls), 
                        len(expanded_urls), 
                        url
                    )
        
        elapsed_time = time.time() - start_time
        print(f"🏁 Completed in {elapsed_time:.1f}s - Success: {len(successful_urls)}, Failed: {len(failed_urls)}")
        
        # Update bulk file (remove original URLs that had all their videos processed successfully)
        self._update_bulk_file_with_expansion(bulk_file, urls, successful_urls, expanded_urls)
        
        return successful_urls, failed_urls, session_dir
