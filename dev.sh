#!/bin/bash

# Simple development starter for PsychSync
# Usage: ./dev.sh

echo "🚀 Starting PsychSync (automatic process management)..."

# Kill any existing processes automatically
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "python.*app.main:app" 2>/dev/null || true
pkill -f "npm.*dev.*517" 2>/dev/null || true

# Wait for processes to die
sleep 3

# Kill stubborn processes on specific ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:5174 | xargs kill -9 2>/dev/null || true

echo "✅ Cleanup complete"

# Start backend
echo "🔧 Starting backend..."
cd /Users/sheriftito/Downloads/psychsync
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
nohup uvicorn minimal_app:app --host 0.0.0.0 --port 8000 --reload > .backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
nohup npm run dev -- --port 5173 > ../.frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for servers to start
sleep 8

# Test if servers are working
echo "🔍 Testing servers..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is working"
else
    echo "❌ Backend failed to start"
    cat ../.backend.log | tail -10
    exit 1
fi

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend is working"
else
    echo "❌ Frontend failed to start"
    cat ../.frontend.log | tail -10
    exit 1
fi

echo ""
echo "🎉 PsychSync is ready!"
echo "Frontend: http://localhost:5173"
echo "Backend: http://localhost:8000"
echo ""
echo "💡 To stop: pkill -f uvicorn && pkill -f 'npm.*dev'"
echo "💡 To restart: just run ./dev.sh again"