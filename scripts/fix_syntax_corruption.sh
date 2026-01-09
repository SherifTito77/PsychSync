#!/bin/bash
# Quick wrapper script to run syntax corruption fixer

echo "🔧 Syntax Corruption Fix Tool"
echo "================================"
echo ""
echo "This script fixes the decorator insertion pattern that corrupts Python files."
echo ""
echo "Usage:"
echo "  ./scripts/fix_syntax_corruption.sh [option]"
echo ""
echo "Options:"
echo "  --test     Test on api_fuzzer.py (dry-run mode)"
echo "  --apply    Apply fixes to all known corrupted files"
echo "  --help     Show full help"
echo ""

if [ "$1" = "--test" ]; then
    echo "🧪 Testing on api_fuzzer.py (dry-run mode)..."
    python scripts/fix_syntax_corruption.py --dry-run --file app/testing/api_fuzzer.py

elif [ "$1" = "--apply" ]; then
    echo "🚀 Applying fixes to all corrupted files..."
    echo "⚠️  This will modify files! Backups will be created."
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python scripts/fix_syntax_corruption.py --all
    else
        echo "❌ Cancelled"
    fi

elif [ "$1" = "--help" ]; then
    python scripts/fix_syntax_corruption.py --help

else
    echo "Error: Please specify an option"
    echo "Run with --help for usage information"
    exit 1
fi
