#!/bin/bash

echo "🚀 Starting Product Management Prompts Service..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check Flask
if ! python3 -c "import flask" 2> /dev/null; then
    echo "📦 Installing Flask..."
    pip3 install flask flask-cors
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "✅ Starting server on http://0.0.0.0:5001"
echo "📝 Product Management Prompts: 50 expert prompts"
echo "🌐 Web Interface: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 product_prompt_service.py
