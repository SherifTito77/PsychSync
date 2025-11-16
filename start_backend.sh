#!/bin/bash
echo "🚀 Starting PsychSync Backend..."

# Navigate to project root
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH="$(pwd):${PYTHONPATH}"

# Activate virtual environment
source .venv/bin/activate

# Check if .env.local exists, otherwise use .env
if [ -f "app/.env.local" ]; then
    ENV_FILE="app/.env.local"
elif [ -f "app/.env" ]; then
    ENV_FILE="app/.env"
else
    echo "❌ No environment file found! Create app/.env.local"
    exit 1
fi

# Load environment variables
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)

# Check database connection
echo "📊 Checking database connection..."
psql "$DATABASE_URL" -c "SELECT 'Database connected!' as status;" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Database connected!"
else
    echo "❌ Database connection failed!"
    echo "DATABASE_URL: $DATABASE_URL"
    exit 1
fi

# Navigate to app directory
cd app

# Start FastAPI with uvicorn
echo "🌐 Starting FastAPI server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
