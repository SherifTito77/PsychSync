#!/bin/bash

# Unsafe Pattern Finder
# Scans your codebase for potential race conditions

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║        🔍 Scanning for Unsafe React Patterns                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Pattern 1: useEffect with async operations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Looking for: useEffect(() => { async ..."
grep -r "useEffect(() => {" src/ --include="*.tsx" --include="*.ts" -l | head -5 || echo "✅ No files found"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Pattern 2: setTimeout without cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Looking for: setTimeout"
grep -r "setTimeout" src/ --include="*.tsx" --include="*.ts" -n | grep -v "clearTimeout" | head -5 || echo "✅ No files found"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Pattern 3: setInterval without return cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Looking for: setInterval"
grep -r "setInterval" src/ --include="*.tsx" --include="*.ts" -n | head -5 || echo "✅ No files found"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Pattern 4: Fetch in useEffect without AbortController"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Looking for: fetch in useEffect"
grep -r "useEffect" src/ --include="*.tsx" --include="*.ts" -A 10 | grep "fetch(" | head -5 || echo "✅ No files found"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SAFE: Files using useAsyncEffect"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep -r "useAsyncEffect" src/ --include="*.tsx" --include="*.ts" -l || echo "   (none yet)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Files already safe:   $(grep -r "useAsyncEffect\|useSafeFetch\|useSafeInterval\|useSafeTimeout" src/ --include="*.tsx" --include="*.ts" -l | wc -l | tr -d ' ')"
echo ""
echo "📝 What to do next:"
echo "   1. Review files listed above"
echo "   2. See migration examples in: src/components/examples/MigrationGuide.tsx"
echo "   3. Replace unsafe patterns with safe hooks"
echo "   4. Test your changes"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
