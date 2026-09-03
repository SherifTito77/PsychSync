#!/bin/bash

# PsychSync Lean Development Setup
# Sets up minimal virtual environment without heavy AI dependencies

set -e

echo "🌱 Setting up Lean PsychSync Development Environment"
echo "=================================================="

# Remove existing .venv if it exists
if [ -d ".venv" ]; then
    echo "🗑️  Removing existing virtual environment (1.5GB)..."
    rm -rf .venv
fi

# Create fresh virtual environment
echo "📦 Creating new virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install core dependencies only
echo "📥 Installing core dependencies..."
pip install -r requirements-dev.txt

echo ""
echo "✅ Lean development environment setup completed!"
echo "=============================================="
echo ""
echo "📊 Environment size:"
du -sh .venv

echo ""
echo "📝 Next steps:"
echo "   1. Start services: ./scripts/start-dev.sh"
echo "   2. Start backend: source .venv/bin/activate && uvicorn app.main:app --reload"
echo "   3. Add AI dependencies later: pip install -r requirements-ai.txt"
echo ""
echo "💡 This setup is ~300-400MB instead of 1.5GB!"
echo "🤖 Install AI packages when you need them with: pip install -r requirements-ai.txt"
