#!/bin/bash

# PsychSync Localhost Development Stop Script
echo "🛑 Stopping PsychSync Localhost Development Environment..."

# Stop backend and frontend processes if running
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm -f .backend.pid
fi

if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm -f .frontend.pid
fi

# Kill any remaining processes on ports 8000 and 5173
echo "Cleaning up any remaining processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Stop Docker services
echo "Stopping Docker services..."
docker-compose down

echo "✅ All services stopped successfully!"