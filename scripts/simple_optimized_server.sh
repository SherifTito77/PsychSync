#!/bin/bash

# Simple Optimized Server Startup
echo "🚀 Starting Optimized PsychSync Server (Multi-Worker)"
echo "=================================================="

# Environment setup
export PYTHONPATH="/Users/sheriftito/Downloads/psychsync"
cd "/Users/sheriftito/Downloads/psychsync"

# Check virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

echo "📊 Configuration:"
echo "   • Workers: 4 processes"
echo "   • Host: 0.0.0.0:8000"
echo "   • Concurrent Requests: 1000 per worker"
echo "   • Max Requests: 10000 per worker (auto-restart)"
echo ""

# Start with optimized multi-worker configuration
echo "🚀 Starting server..."
exec uvicorn app.main:app \
    --workers 4 \
    --host 0.0.0.0 \
    --port 8000 \
    --limit-concurrency 1000 \
    --limit-max-requests 10000 \
    --log-level warning \
    --no-use-colors
