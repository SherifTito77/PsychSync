#!/bin/bash

# PsychSync Local Development with HTTPS
# Starts backend with SSL/HTTPS support

set -e

CERT_DIR="certs"
BACKEND_CERT="$CERT_DIR/psychsync.crt"
BACKEND_KEY="$CERT_DIR/psychsync.key"

echo "🔐 Starting PsychSync with HTTPS"
echo "================================="

# Check if certificates exist
if [ ! -f "$BACKEND_CERT" ] || [ ! -f "$BACKEND_KEY" ]; then
    echo "❌ SSL certificates not found in $CERT_DIR/"
    echo "Please run: ./scripts/setup-localhost-ssl.sh"
    exit 1
fi

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

# Export environment variables for HTTPS
export SSL_CERT_PATH="$BACKEND_CERT"
export SSL_KEY_PATH="$BACKEND_KEY"

# Start HTTPS backend
echo "🚀 Starting FastAPI backend with HTTPS..."
source .venv/bin/activate
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --ssl-keyfile="$BACKEND_KEY" \
    --ssl-certfile="$BACKEND_CERT" &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if curl -k -s https://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully with HTTPS (PID: $BACKEND_PID)"
else
    echo "⚠️  Backend may still be starting..."
fi

# Update frontend to use HTTPS
echo "⚡ Starting React frontend with HTTPS API..."
cd frontend

# Create temporary .env file for HTTPS development
cat > .env.local << EOF
# HTTPS Development Environment
VITE_API_BASE_URL=https://localhost:8000
VITE_API_URL=https://localhost:8000/api/v1
VITE_APP_ENVIRONMENT=development-https
EOF

npm run dev &
FRONTEND_PID=$!

cd ..

# Wait a moment for frontend to start
sleep 3

echo ""
echo "🎉 Both services are starting up with HTTPS!"
echo "============================================"
echo "🔒 Backend API:  https://localhost:8000"
echo "⚡ Frontend:     http://localhost:5173"
echo "📚 API Docs:     https://localhost:8000/docs"
echo "📖 ReDoc:        https://localhost:8000/redoc"
echo ""
echo "📝 Logs will appear below. Press Ctrl+C to stop all services."
echo "🔐 SSL Certificates: $BACKEND_CERT"
echo "============================================================="

# Wait for both background processes
wait $BACKEND_PID $FRONTEND_PID