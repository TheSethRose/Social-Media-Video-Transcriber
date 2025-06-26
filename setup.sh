#!/bin/bash
# Setup script for TikTok Transcribe

echo "Setting up TikTok Transcribe..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

echo "Setup complete!"
echo ""
echo "To use the tool:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Use the unified CLI: python main.py [command] [options]"
echo ""
echo "Examples:"
echo "  # Single video workflow (TikTok or YouTube):"
echo "  python main.py workflow \"https://www.youtube.com/watch?v=VIDEO_ID\""
echo ""
echo "  # Bulk processing:"
echo "  python main.py workflow --bulk --bulk-file urls.txt"
echo ""
echo "  # Just transcription:"
echo "  python main.py transcribe \"https://www.tiktok.com/@user/video/123\""
echo ""
echo "  # Help:"
echo "  python main.py --help"
