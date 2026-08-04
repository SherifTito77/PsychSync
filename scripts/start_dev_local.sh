#!/bin/bash

# PsychSync Localhost Development Starter Script (Local Services)
echo "🚀 Starting PsychSync Localhost Development Environment (Local Services)..."

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

if ! command_exists psql; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    exit 1
fi

if ! command_exists redis-server; then
    echo "❌ Redis server is not installed. Please install Redis first."
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

# Check if Python dependencies are installed
echo "📦 Checking Python dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ FastAPI is not installed. Run: pip install -r requirements.txt"
    exit 1
fi

# Check if ports are available
echo "🔍 Checking port availability..."
if ! check_port 8000; then exit 1; fi  # Backend
if ! check_port 5173; then exit 1; fi  # Frontend

# Check if PostgreSQL is running and database exists
echo "🗄️ Checking PostgreSQL service..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL service."
    echo "   On macOS: brew services start postgresql"
    echo "   On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

# Check if database exists
if psql -h localhost -p 5432 -U postgres -lqt | cut -d \| -f 1 | grep -qw psychsync_db; then
    echo "✅ Database 'psychsync_db' exists"
else
    echo "⚠️ Database 'psychsync_db' does not exist. Creating it..."
    createdb -h localhost -p 5432 -U postgres psychsync_db
    if [ $? -eq 0 ]; then
        echo "✅ Database 'psychsync_db' created"

        # Create user
        psql -h localhost -p 5432 -U postgres -d psychsync_db -c "CREATE USER psychsync_user WITH PASSWORD 'password';"
        psql -h localhost -p 5432 -U postgres -d psychsync_db -c "GRANT ALL PRIVILEGES ON DATABASE psychsync_db TO psychsync_user;"
        psql -h localhost -p 5432 -U postgres -d psychsync_db -c "ALTER USER psychsync_user CREATEDB;"
    else
        echo "❌ Failed to create database. Please create it manually:"
        echo "   createdb -h localhost -p 5432 -U postgres psychsync_db"
        exit 1
    fi
fi

# Check Redis service
echo "🔴 Checking Redis service..."
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running. Please start Redis service."
    echo "   On macOS: brew services start redis"
    echo "   On Ubuntu: sudo systemctl start redis"
    exit 1
fi

# Run database migrations
echo "🔄 Running database migrations..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "✅ Database migrations completed"
    else
        echo "⚠️ Some migrations failed, but continuing..."
    fi
else
    echo "⚠️ No alembic.ini found, skipping migrations"
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
sleep 8

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
sleep 8

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
echo "   🐘 PostgreSQL:   localhost:5432 (database: psychsync_db, user: psychsync_user)"
echo "   🔴 Redis:        localhost:6379"
echo ""
echo "🛑 To stop all services, run: ./stop_dev.sh"
echo ""
echo "💡 Development commands:"
echo "   Backend logs:  tail -f logs/psychsync.log (if configured)"
echo "   Frontend dev:  cd frontend && npm run dev"
echo "   Backend dev:   PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "🗄️ Database management:"
echo "   Connect:       psql -h localhost -p 5432 -U psychsync_user -d psychsync_db"
echo "   Migrations:    alembic upgrade head"
echo "   New migration: alembic revision --autogenerate -m 'description'"

# Save PIDs for later cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "Press Ctrl+C to stop watching, or run ./stop_dev.sh to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; exit 0' INT

# Keep script running
wait
