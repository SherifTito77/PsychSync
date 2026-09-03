#!/bin/bash

# PsychSync Localhost Development Starter Script
echo "🚀 Starting PsychSync Localhost Development Environment..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is busy
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use. Please stop the service using that port."
        return 1
    fi
    return 0
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ NPM is not installed. Please install NPM first."
    exit 1
fi

# Check if ports are available
echo "🔍 Checking port availability..."
if ! check_port 5432; then exit 1; fi  # PostgreSQL
if ! check_port 6379; then exit 1; fi  # Redis
if ! check_port 8000; then exit 1; fi  # Backend
if ! check_port 5173; then exit 1; fi  # Frontend

# Start database and Redis services
echo "🗄️ Starting database services..."
docker-compose up -d db redis

# Wait for databases to be ready
echo "⏳ Waiting for database services to be ready..."
sleep 10

# Check database connectivity
echo "🔍 Checking database connectivity..."
docker-compose exec -T db pg_isready -U psychsync_user -d psychsync_db
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
    exit 1
fi

# Check Redis connectivity
echo "🔍 Checking Redis connectivity..."
docker-compose exec -T redis redis-cli ping
if [ $? -eq 0 ]; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
    exit 1
fi

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend in background
echo "🔧 Starting backend server..."
PYTHONPATH=. python app/main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check backend health
echo "🔍 Checking backend health..."
curl -f http://localhost:8000/health >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend in background
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

# Check frontend health
echo "🔍 Checking frontend health..."
curl -f http://localhost:5173 >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend failed to start"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 PsychSync is now running!"
echo ""
echo "📍 Service URLs:"
echo "   🌐 Frontend:     http://localhost:5173"
echo "   🔧 Backend:      http://localhost:8000"
echo "   📚 API Docs:     http://localhost:8000/docs"
echo "   🔍 ReDoc:        http://localhost:8000/redoc"
echo ""
echo "🔧 Database Access:"
echo "   🐘 PostgreSQL:   localhost:5432"
echo "   🔴 Redis:        localhost:6379"
echo ""
echo "🛑 To stop all services, run: ./stop_dev.sh"
echo ""
echo "💡 To run in development mode with hot reload:"
echo "   Backend:  PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "   Frontend: cd frontend && npm run dev"

# Save PIDs for later cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "Press Ctrl+C to stop watching, or run ./stop_dev.sh to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; docker-compose down; exit 0' INT

# Keep script running
wait
