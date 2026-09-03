#!/bin/bash

# PsychSync Localhost Development Startup Script
# This script starts all services for local development

echo "🚀 Starting PsychSync Localhost Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env.dev file exists
if [ ! -f ".env.dev" ]; then
    echo "❌ .env.dev file not found. Please create it from the example."
    exit 1
fi

echo "📦 Building and starting Docker containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check database connection
echo "🔍 Checking database connection..."
until docker-compose exec -T db pg_isready -U psychsync_user -d psychsync_db; do
    echo "⏳ Waiting for database to be ready..."
    sleep 2
done

echo "✅ Database is ready!"

# Check Redis connection
echo "🔍 Checking Redis connection..."
until docker-compose exec -T redis redis-cli ping; do
    echo "⏳ Waiting for Redis to be ready..."
    sleep 2
done

echo "✅ Redis is ready!"

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec -T backend python -m alembic upgrade head

echo "🎉 All services are ready!"
echo ""
echo "🌐 Application URLs:"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs:    http://localhost:8000/docs"
echo "   • Frontend:    http://localhost:5173 (start with 'npm run dev')"
echo "   • Database:    localhost:5432"
echo "   • Redis:       localhost:6379"
echo ""
echo "🛠️ To start the frontend, run:"
echo "   cd frontend && npm run dev"
echo ""
echo "🛑 To stop all services, run:"
echo "   docker-compose down"
