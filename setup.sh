# setup.sh
#!/bin/bash
# Setup script for the Social Media Transcriber

echo "Setting up Social Media Transcriber..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing package in editable mode..."
pip install -e .

echo "Setup complete!"
echo ""
echo "To use the tool:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Use the transcriber CLI: transcriber [command] [options]"
echo ""
echo "Examples:"
echo "  # Transcribe a single video URL:"
echo "  transcriber run \"https://www.youtube.com/watch?v=VIDEO_ID\""
echo ""
echo "  # Process multiple URLs from a file:"
echo "  transcriber run --file urls.txt"
echo ""
echo "  # Combine transcripts from a playlist folder:"
echo "  transcriber combine --channel \"My Playlist Name\""
echo ""
echo "  # Get help:"
echo "  transcriber --help"