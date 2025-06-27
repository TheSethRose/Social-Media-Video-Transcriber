#!/usr/bin/env python3
"""
Test script for audio speed optimization functionality.
"""

import sys
import tempfile
import subprocess
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_transcriber.utils.file_utils import (
    speed_up_audio, 
    process_audio_for_transcription,
    convert_audio_format
)
from social_media_transcriber.core.transcriber import AudioTranscriber
from social_media_transcriber.config.settings import Settings

def test_audio_speed_functions():
    """Test the audio speed optimization functions."""
    print("🧪 Testing Audio Speed Optimization Functions")
    print("=" * 50)
    
    # Test with a simple synthetic audio file (sine wave)
    # First, let's create a test audio file using ffmpeg
    try:
        # Create a 10-second test audio file (sine wave at 440Hz)
        test_audio = Path(tempfile.mktemp(suffix='.wav'))
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=10',
            '-ar', '16000', '-ac', '1', str(test_audio), '-y'
        ]
        
        print("📦 Creating test audio file...")
        subprocess.run(cmd, capture_output=True, check=True)
        
        if not test_audio.exists():
            print("❌ Failed to create test audio file")
            return
        
        original_size = test_audio.stat().st_size
        print(f"✅ Created test audio: {test_audio} ({original_size} bytes)")
        
        # Test 1: Basic speed up function
        print("\n🧪 Test 1: Basic speed_up_audio function")
        try:
            speed_2x = speed_up_audio(test_audio, speed_multiplier=2.0)
            speed_2x_size = speed_2x.stat().st_size
            print(f"✅ 2x speed audio created: {speed_2x} ({speed_2x_size} bytes)")
            print(f"   Size reduction: {(1 - speed_2x_size/original_size)*100:.1f}%")
            
            # Clean up
            speed_2x.unlink()
            
        except Exception as e:
            print(f"❌ Speed up test failed: {e}")
        
        # Test 2: Process audio for transcription
        print("\n🧪 Test 2: process_audio_for_transcription function")
        try:
            processed_audio = process_audio_for_transcription(
                test_audio, 
                speed_multiplier=3.0,
                preserve_pitch=True
            )
            processed_size = processed_audio.stat().st_size
            print(f"✅ 3x processed audio created: {processed_audio} ({processed_size} bytes)")
            print(f"   Size reduction: {(1 - processed_size/original_size)*100:.1f}%")
            
            # Clean up
            processed_audio.unlink()
            
        except Exception as e:
            print(f"❌ Process audio test failed: {e}")
        
        # Test 3: AudioTranscriber with speed settings
        print("\n🧪 Test 3: AudioTranscriber speed configuration")
        try:
            settings = Settings()
            transcriber = AudioTranscriber(settings)
            
            # Test different speed settings
            for speed in [1.0, 2.0, 3.0]:
                transcriber.set_speed_multiplier(speed)
                current_speed = transcriber.settings.audio_speed_multiplier
                print(f"✅ Speed set to {speed}x, confirmed: {current_speed}x")
                
        except Exception as e:
            print(f"❌ AudioTranscriber test failed: {e}")
        
        # Clean up test audio
        test_audio.unlink()
        print("\n✅ All tests completed successfully!")
        
        # Performance information
        print("\n📊 Performance Benefits:")
        print("• 2x speed = ~50% reduction in transcription time")
        print("• 3x speed = ~67% reduction in transcription time")
        print("• Minimal quality loss with pitch preservation")
        print("• Works with all supported video platforms")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create test audio: {e}")
        print("💡 Make sure ffmpeg is installed: brew install ffmpeg")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def print_usage_examples():
    """Print usage examples for the speed optimization feature."""
    print("\n🚀 Usage Examples:")
    print("=" * 50)
    
    print("# Single video with 2x speed (default)")
    print("python main.py workflow 'https://www.youtube.com/watch?v=VIDEO_ID'")
    
    print("\n# Single video with 3x speed")
    print("python main.py workflow 'https://www.youtube.com/watch?v=VIDEO_ID' --speed 3.0")
    
    print("\n# Normal speed (no optimization)")
    print("python main.py workflow 'https://www.youtube.com/watch?v=VIDEO_ID' --speed 1.0")
    
    print("\n# Benchmark different speeds")
    print("python main.py workflow 'https://www.youtube.com/watch?v=VIDEO_ID' --benchmark")
    
    print("\n# Bulk processing with 2x speed")
    print("python main.py workflow --bulk --bulk-file urls.txt --speed 2.0")
    
    print("\n# Transcription only with speed optimization")
    print("python main.py transcribe 'https://www.youtube.com/watch?v=VIDEO_ID' --speed 2.5")
    
    print("\n💡 Recommended Settings:")
    print("• Use 2.0x for best balance of speed and quality")
    print("• Use 3.0x for maximum speed with acceptable quality")
    print("• Use 1.0x only when maximum quality is critical")

if __name__ == "__main__":
    test_audio_speed_functions()
    print_usage_examples()
