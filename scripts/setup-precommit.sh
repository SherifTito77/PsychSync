#!/bin/bash
# Setup pre-commit hooks for PsychSync
# Run this script once to install pre-commit hooks in your git repository

set -e

echo "🔧 Setting up pre-commit hooks for PsychSync..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "✅ Installing git hooks..."
pre-commit install

# Optional: Install pre-commit commit-msg hook (for commit message validation)
read -p "Install commit-msg hook? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pre-commit install --hook-type commit-msg
fi

# Run pre-commit on all files to check initial state
echo ""
echo "🧪 Running pre-commit on all files (this may take a while)..."
pre-commit run --all-files || true

echo ""
echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "📖 Usage:"
echo "  - Run on all files:       pre-commit run --all-files"
echo "  - Run on staged files:    git commit  (hooks run automatically)"
echo "  - Skip hooks (not recommended): git commit --no-verify"
echo ""
echo "🔄 Hooks will run automatically on each commit!"
