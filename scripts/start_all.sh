#!/bin/bash
echo "🚀 Starting PsychSync (Localhost Mode)"
echo "======================================="

# Check PostgreSQL
echo "📊 Checking PostgreSQL..."
pg_isready -h localhost -p 5432 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not running!"
    echo "Start it with: brew services start postgresql@15"
    exit 1
fi

# Check Redis (optional)
echo "📊 Checking Redis..."
redis-cli ping &>/dev/null && echo "✅ Redis is running" || echo "⚠️  Redis is not running (optional)"

echo ""
echo "Starting services..."
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to kill all background processes
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Start Backend in background
echo "🔧 Starting Backend..."
./start_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Start Frontend in background
echo "🎨 Starting Frontend..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "✅ PsychSync is running!"
echo "======================================="
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo "======================================="
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
