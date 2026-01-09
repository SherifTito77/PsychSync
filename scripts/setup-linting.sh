#!/bin/bash
# Setup script for linting tools and configurations
# This script installs all necessary linting tools and configurations

set -e  # Exit on error

echo "=================================="
echo "PsychSync Linting Setup Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.14 or higher."
    exit 1
fi

print_success "Python found: $(python3 --version)"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 20 or higher."
    exit 1
fi

print_success "Node.js found: $(node --version)"

# Install Python linting tools
echo ""
echo "Installing Python linting tools..."

pip_install="pip install --upgrade pip"
pip_install+=" && pip install ruff"
pip_install+=" && pip install mypy"
pip_install+=" && pip install bandit[toml]"
pip_install+=" && pip install pre-commit"
pip_install+=" && pip install pydantic"
pip_install+=" && pip install types-requests"
pip_install+=" && pip install types-redis"
pip_install+=" && pip install sqlalchemy"

if eval $pip_install; then
    print_success "Python linting tools installed successfully"
else
    print_error "Failed to install Python linting tools"
    exit 1
fi

# Install pre-commit hooks
echo ""
echo "Installing pre-commit hooks..."
if pre-commit install; then
    print_success "Pre-commit hooks installed"
else
    print_error "Failed to install pre-commit hooks"
    exit 1
fi

# Install frontend dependencies
echo ""
echo "Installing frontend linting tools..."
cd frontend

if npm install; then
    print_success "Frontend dependencies installed"
else
    print_error "Failed to install frontend dependencies"
    exit 1
fi

cd ..

# Run initial linting check
echo ""
echo "Running initial linting check..."
echo ""

echo "Checking Python code..."
if ruff check --output-format=concise; then
    print_success "Python linting passed"
else
    print_warning "Python linting found issues. Run 'ruff check --fix .' to auto-fix."
fi

echo ""
echo "Checking Python formatting..."
if ruff format --check; then
    print_success "Python formatting passed"
else
    print_warning "Python formatting needs adjustment. Run 'ruff format .' to fix."
fi

echo ""
echo "Checking frontend code..."
cd frontend
if npm run lint; then
    print_success "Frontend linting passed"
else
    print_warning "Frontend linting found issues. Run 'npm run lint:fix' to auto-fix."
fi

cd ..

# Generate secrets baseline
echo ""
echo "Generating secrets baseline..."
if detect-secrets scan > .secrets.baseline 2>/dev/null; then
    print_success "Secrets baseline generated (.secrets.baseline)"
    print_warning "Review .secrets.baseline and remove any real secrets before committing"
else
    print_warning "Failed to generate secrets baseline (optional tool)"
fi

# Print summary
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Review the documentation:"
echo "   - docs/CODE_QUALITY_STANDARDS.md"
echo "   - docs/LINTING_QUICKSTART.md"
echo ""
echo "2. Configure your editor:"
echo "   - Install EditorConfig plugin"
echo "   - Install Ruff extension (Python)"
echo "   - Install ESLint extension (TypeScript/React)"
echo ""
echo "3. Fix any existing linting issues:"
echo "   Python:   ruff check --fix ."
echo "   Python:   ruff format ."
echo "   Frontend: cd frontend && npm run lint:fix"
echo ""
echo "4. Run pre-commit manually to test:"
echo "   pre-commit run --all-files"
echo ""
echo "5. Commit your changes (hooks will run automatically):"
echo "   git add ."
echo "   git commit -m 'chore: setup linting configuration'"
echo ""

# Check if there are any linting errors
echo "Current Status:"
echo ""

python_issues=$(ruff check . 2>&1 | grep -c ".*" || true)
if [ "$python_issues" -gt 0 ]; then
    print_warning "Python has $python_issues linting issues"
else
    print_success "Python: No linting issues"
fi

echo ""
print_success "Linting setup is complete!"
echo ""
echo "For help, run: ruff check --help"
echo "For help, run: eslint --help (in frontend directory)"
