#!/bin/bash
# Local complexity checking script
# Run this before committing to ensure code quality

set -e

echo "🔍 Checking code complexity..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if radon is installed
if ! command -v radon &> /dev/null; then
    echo "Installing radon..."
    pip install radon
fi

# Check Python complexity
echo "📊 Checking Python code complexity..."
echo ""

# Get high complexity functions
HIGH_COMPLEXITY=$(radon cc app/ -nb --min C | grep -c "^[A-Z]" || true)
AVG_COMPLEXITY=$(radon cc app/ -a --total-average | tail -1 | awk '{print $2}')

echo "Average Complexity: $AVG_COMPLEXITY"
echo "Functions with complexity > 15: $HIGH_COMPLEXITY"
echo ""

if [ "$HIGH_COMPLEXITY" -gt "10" ]; then
    print_error "Too many complex functions ($HIGH_COMPLEXITY > 10)"
    echo ""
    echo "Functions exceeding complexity threshold:"
    radon cc app/ -nb --min C
    echo ""
    echo "Please refactor these functions before committing."
    exit 1
else
    print_success "Python complexity acceptable"
fi

echo ""
echo "📊 Checking TypeScript complexity..."
echo ""

# Check if complexity-report is installed
if ! command -v cr &> /dev/null; then
    echo "Installing complexity-report..."
    npm install -g complexity-report
fi

# Check TypeScript complexity
cd frontend
COMPLEXITY_OUTPUT=$(cr src/**/*.ts --report json 2>/dev/null || echo "[]")

# Parse and display results
HIGH_TS_COMPLEXITY=$(echo $COMPLEXITY_OUTPUT | jq '[.complexity.report[].aggregate.cyclomatic] | map(. > 15) | length' 2>/dev/null || echo "0")

echo "Functions with complexity > 15: $HIGH_TS_COMPLEXITY"

if [ "$HIGH_TS_COMPLEXITY" -gt "5" ]; then
    print_error "Too many complex TypeScript functions"
    exit 1
else
    print_success "TypeScript complexity acceptable"
fi

cd ..

echo ""
echo "📊 Checking maintainability index..."
echo ""

# Check maintainability (should be > 50 for most files)
LOW_MI_FILES=$(radon mi app/ -nb --min C | grep -c "^[A-Z]" || true)

if [ "$LOW_MI_FILES" -gt "5" ]; then
    print_warning "$LOW_MI_FILES files have low maintainability index"
    echo "Consider refactoring these files:"
    radon mi app/ -nb --min C
else
    print_success "Maintainability index acceptable"
fi

echo ""
echo "─────────────────────────────────────────"
print_success "All complexity checks passed!"
echo "─────────────────────────────────────────"
echo ""
echo "📝 Summary:"
echo "  - Average Complexity: $AVG_COMPLEXITY"
echo "  - High Complexity Functions: $HIGH_COMPLEXITY"
echo "  - Low Maintainability Files: $LOW_MI_FILES"
echo ""
echo "💡 Tips for reducing complexity:"
echo "  - Extract helper functions"
echo "  - Use strategy pattern for multiple algorithms"
echo "  - Separate validation from business logic"
echo "  - Apply Single Responsibility Principle"
