#!/bin/bash

###############################################################################
# AI Agents Service Startup Script
#
# Starts the AI Agents service on port 5002
# Usage: ./start-ai-agents.sh
###############################################################################

set -e

echo "🤖 Starting PsychSync AI Agents Service..."
echo ""

# Default values
PORT=${PORT:-5002}
HOST=${HOST:-0.0.0.0}
RELOAD=${RELOAD:-true}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}Warning: Port $PORT is already in use${NC}"
    echo "Attempting to stop existing process..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo -e "${BLUE}Configuration:${NC}"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Reload: $RELOAD"
echo ""

# Set environment variables
export PORT=$PORT
export HOST=$HOST
export RELOAD=$RELOAD

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
fi

# Activate virtual environment
source .venv/bin/activate

echo -e "${GREEN}Starting AI Agents Service...${NC}"
echo ""
echo "📚 Documentation: http://localhost:$PORT/docs"
echo "📊 Agent Status: http://localhost:$PORT/api/v1/ai-agents/status"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Start the service
python3 ai_agents_service.py
