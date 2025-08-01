# setup.sh
#!/bin/bash
# Setup script for the Social Media Transcriber

echo "Setting up Social Media Transcriber..."

# --- Python Setup ---
echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Installing package in editable mode..."
pip install -e .

# --- Node.js & Prettier Setup ---
echo "Checking for Node.js and npm..."

if ! command -v node &> /dev/null
then
    echo "🚨 Node.js could not be found."
    echo "Please install Node.js (which includes npm) to enable auto-formatting."
    echo "Recommended method is via nvm: https://github.com/nvm-sh/nvm"
else
    echo "✅ Node.js found."
    echo "Installing Prettier for automatic MDX formatting..."
    npm install --save-dev --save-exact prettier
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the tool:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Use the transcriber CLI: transcriber [command] [options]"
echo ""
echo "Examples:"
echo "  # Transcribe a single video with enhancement and formatting:"
echo "  transcriber run \"https://www.youtube.com/watch?v=VIDEO_ID\" --enhance"
echo ""
echo "  # Get help:"
echo "  transcriber --help"