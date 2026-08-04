#!/bin/bash

# PsychSync Database Reset Script
# This script completely resets the database

echo "🗑️ Resetting PsychSync Database..."

# Stop services
docker-compose down

# Drop and recreate database
echo "💾 Dropping old database..."
dropdb -h localhost -U psychsync_user psychsync_db 2>/dev/null || echo "Database doesn't exist or couldn't connect"
echo "📦 Creating new database..."
createdb -h localhost -U psychsync_user psychsync_db

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10
until docker-compose exec -T db pg_isready -U psychsync_user -d psychsync_db; do
    echo "⏳ Waiting for database..."
    sleep 2
done

# Run migrations
echo "🗄️ Running database migrations..."
docker-compose exec -T backend python -m alembic upgrade head

echo "✅ Database reset complete!"
echo ""
echo "🌐 Your application is ready at:"
echo "   • Backend API: http://localhost:8000"
echo "   • Frontend:    http://localhost:5173"
