#!/bin/bash

# Optimized PsychSync Server Startup Script
# Multi-worker configuration for better performance under load

echo "🚀 Starting Optimized PsychSync API Server..."
echo "=================================================="

# Environment setup
export PYTHONPATH="/Users/sheriftito/Downloads/psychsync"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Change to project directory
cd "/Users/sheriftito/Downloads/psychsync"

echo "📊 Configuration:"
echo "   • Workers: 4 (multi-process)"
echo "   • Host: 0.0.0.0:8000"
echo "   • Worker Class: UvicornWorker"
echo "   • Timeout: 120 seconds"
echo "   • Log Level: Warning (production mode)"
echo "   • Access Log: Enabled"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if dependencies are available
echo "🔍 Checking dependencies..."
python -c "import uvicorn, fastapi; print('✅ Dependencies OK')" || {
    echo "❌ Missing dependencies. Installing..."
    pip install "uvicorn[standard]" fastapi
}

# Start optimized server
echo "🚀 Starting optimized server with 4 workers..."
echo "   Server will be available at: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs (if enabled)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="

# Optimized uvicorn configuration
exec uvicorn app.main:app \
    --workers 4 \
    --host 0.0.0.0 \
    --port 8000 \
    --timeout 120 \
    --access-log \
    --log-level warning \
    --no-use-colors \
    --limit-concurrency 1000 \
    --limit-max-requests 1000 \
    --limit-max-requests-jitter 100