#!/bin/bash
echo "🎨 Starting PsychSync Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start Vite dev server
echo "🌐 Starting Vite server on http://localhost:5173"
npm run dev
