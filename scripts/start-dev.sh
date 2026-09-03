#!/bin/bash

# PsychSync Local Development Setup Script
# This script starts all required services for local development

set -e

echo "🚀 Starting PsychSync Local Development Environment"
echo "=================================================="

# Function to check if a service is running
check_service() {
    local service_name=$1
    local check_command=$2
    local port=$3

    echo "🔍 Checking $service_name..."

    if eval "$check_command" > /dev/null 2>&1; then
        echo "✅ $service_name is running on port $port"
        return 0
    else
        echo "❌ $service_name is not running"
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local start_command=$2

    echo "🔄 Starting $service_name..."
    eval "$start_command"

    # Give the service a moment to start
    sleep 2

    if [ $? -eq 0 ]; then
        echo "✅ $service_name started successfully"
        return 0
    else
        echo "❌ Failed to start $service_name"
        return 1
    fi
}

# Check and start PostgreSQL
if ! check_service "PostgreSQL" "pg_isready -h localhost -p 5432" "5432"; then
    echo "📊 Starting PostgreSQL..."
    brew services start postgresql@14 || brew services start postgresql
    sleep 3

    if ! check_service "PostgreSQL" "pg_isready -h localhost -p 5432" "5432"; then
        echo "❌ Failed to start PostgreSQL. Please check your installation."
        exit 1
    fi
fi

# Check and start Redis
if ! check_service "Redis" "redis-cli ping" "6379"; then
    echo "🔴 Starting Redis..."
    brew services start redis
    sleep 2

    if ! check_service "Redis" "redis-cli ping" "6379"; then
        echo "❌ Failed to start Redis. Please check your installation."
        exit 1
    fi
fi

# Verify database exists and is accessible
echo "🗄️  Verifying database access..."
if psql -U psychsync_user -d psychsync_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database 'psychsync_db' is accessible"
else
    echo "❌ Cannot access database 'psychsync_db'. Please check your configuration."
    exit 1
fi

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Create a test user if it doesn't exist
echo "👤 Creating test user (if needed)..."
python create_user.py --email test@psychsync.com --password test123 --name "Test User" 2>/dev/null || echo "Test user already exists or creation failed"

echo ""
echo "🎉 PsychSync development environment is ready!"
echo "=============================================="
echo "📊 PostgreSQL: localhost:5432 (psychsync_db)"
echo "🔴 Redis:       localhost:6379"
echo "🚀 Backend:     Will start on http://localhost:8000"
echo "⚡ Frontend:    Will start on http://localhost:5173"
echo ""
echo "📝 Next steps:"
echo "   1. Activate virtual environment: source .venv/bin/activate"
echo "   2. Start backend: uvicorn app.main:app --reload"
echo "   3. In another terminal, start frontend: cd frontend && npm run dev"
echo ""
echo "🌐 API Documentation: http://localhost:8000/docs"
echo "🌐 ReDoc Documentation: http://localhost:8000/redoc"
