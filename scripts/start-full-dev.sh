#!/bin/bash

# PsychSync Full Development Startup
# Starts both backend and frontend in parallel

set -e

echo "🚀 Starting PsychSync Full Development Environment"
echo "=================================================="

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    jobs -p | xargs -r kill
    echo "✅ All services stopped"
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./start-dev.sh first."
    exit 1
fi

# Start backend
echo "🚀 Starting FastAPI backend..."
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
else
    echo "⚠️  Backend may still be starting..."
fi

# Start frontend
echo "⚡ Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

cd ..

# Wait a moment for frontend to start
sleep 3

echo ""
echo "🎉 Both services are starting up!"
echo "================================="
echo "🚀 Backend API:  http://localhost:8000"
echo "⚡ Frontend:     http://localhost:5173"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "📖 ReDoc:        http://localhost:8000/redoc"
echo ""
echo "📝 Logs will appear below. Press Ctrl+C to stop all services."
echo "============================================================="

# Wait for both background processes
wait $BACKEND_PID $FRONTEND_PID