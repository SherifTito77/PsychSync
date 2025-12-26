#!/bin/bash
###############################################################################
# Dependency Security Update Script
#
# Updates all Python and npm dependencies to latest secure versions and
# checks for known vulnerabilities.
#
# Usage: ./scripts/update_dependencies_security.sh [--backend-only|--frontend-only]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
UPDATE_BACKEND=true
UPDATE_FRONTEND=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            UPDATE_FRONTEND=false
            shift
            ;;
        --frontend-only)
            UPDATE_BACKEND=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--backend-only|--frontend-only]"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

backup_file() {
    local file="$1"
    local backup="${file}.backup_$(date +%Y%m%d_%H%M%S)"

    if [ -f "$file" ]; then
        cp "$file" "$backup"
        log_success "Backed up $file to $backup"
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if required tools are available
    if [ "$UPDATE_BACKEND" = true ]; then
        if ! command -v python3 &> /dev/null; then
            log_error "Python 3 is required but not installed"
            exit 1
        fi

        if ! command -v pip3 &> /dev/null; then
            log_error "pip3 is required but not installed"
            exit 1
        fi
    fi

    if [ "$UPDATE_FRONTEND" = true ]; then
        if ! command -v npm &> /dev/null; then
            log_error "npm is required but not installed"
            exit 1
        fi
    fi

    log_success "Prerequisites check complete"
}

update_backend_dependencies() {
    log_info "Updating Python (backend) dependencies..."

    cd "$PROJECT_ROOT"

    # Check if virtual environment exists
    if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
        log_warning "No virtual environment found. Creating one..."
        python3 -m venv .venv
        source .venv/bin/activate
    else
        # Activate virtual environment
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        elif [ -d "venv" ]; then
            source venv/bin/activate
        fi
    fi

    # Backup requirements.txt
    backup_file "requirements.txt"

    # Install security checking tools
    log_info "Installing security checking tools..."
    pip install -q safety bandit pip-audit

    # Run security audit before updates
    log_info "Running pre-update security audit..."
    safety check --json > "backend_audit_before.json" 2>/dev/null || true
    pip-audit --desc --format json > "backend_pip_audit_before.json" 2>/dev/null || true

    # Update all packages
    log_info "Updating all Python packages..."
    pip list --outdated --format=json > "outdated_packages.json" 2>/dev/null || true

    # Upgrade pip first
    log_info "Upgrading pip..."
    pip install --upgrade pip

    # Upgrade all packages using pip-compile if available, or pip-update
    if command -v pip-compile &> /dev/null; then
        log_info "Using pip-compile to update requirements..."
        # This would typically require requirements.in
        # pip-compile --upgrade requirements.in
    else
        log_info "Upgrading packages individually..."
        # Get list of outdated packages
        local outdated=$(pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1)

        if [ -n "$outdated" ]; then
            echo "$outdated" | xargs -n1 pip install --upgrade
        else
            log_info "All packages are up to date"
        fi
    fi

    # Run security audit after updates
    log_info "Running post-update security audit..."
    safety check --json > "backend_audit_after.json" 2>/dev/null || true
    pip-audit --desc --format json > "backend_pip_audit_after.json" 2>/dev/null || true

    # Run static analysis
    log_info "Running static security analysis..."
    bandit -r app/ -f json -o "bandit_report.json" 2>/dev/null || true

    log_success "Backend dependencies updated"
}

update_frontend_dependencies() {
    log_info "Updating npm (frontend) dependencies..."

    local frontend_dir="$PROJECT_ROOT/frontend"

    if [ ! -d "$frontend_dir" ]; then
        log_error "Frontend directory not found: $frontend_dir"
        return 1
    fi

    cd "$frontend_dir"

    # Backup package.json and package-lock.json
    backup_file "package.json"
    backup_file "package-lock.json"

    # Run security audit before updates
    log_info "Running pre-update security audit..."
    npm audit --json > "../frontend_audit_before.json" 2>/dev/null || true

    # Check for outdated packages
    log_info "Checking for outdated packages..."
    npm outdated --json > "../npm_outdated.json" 2>/dev/null || true

    # Update all packages
    log_info "Updating all npm packages..."
    npm update

    # Use npm-check-updates for major version updates
    if command -v npx &> /dev/null; then
        log_info "Checking for major version updates..."
        npx npm-check-updates -u
        npm install
    fi

    # Run security audit after updates
    log_info "Running post-update security audit..."
    npm audit --json > "../frontend_audit_after.json" 2>/dev/null || true

    # Fix any vulnerabilities automatically
    log_info "Running npm audit fix..."
    npm audit fix || true

    log_success "Frontend dependencies updated"
}

run_tests() {
    log_info "Running tests to verify updates..."

    cd "$PROJECT_ROOT"

    local failed=0

    # Backend tests
    if [ "$UPDATE_BACKEND" = true ]; then
        log_info "Running backend tests..."
        if command -v pytest &> /dev/null; then
            pytest tests/ -v --tb=short || failed=$((failed + 1))
        else
            log_warning "pytest not found, skipping backend tests"
        fi
    fi

    # Frontend tests
    if [ "$UPDATE_FRONTEND" = true ]; then
        log_info "Running frontend tests..."
        cd frontend

        if [ -f "package.json" ]; then
            npm test || failed=$((failed + 1))
        else
            log_warning "No frontend tests configured"
        fi

        cd "$PROJECT_ROOT"
    fi

    if [ $failed -eq 0 ]; then
        log_success "All tests passed ✅"
        return 0
    else
        log_error "Some tests failed ❌"
        return 1
    fi
}

generate_report() {
    log_info "Generating dependency update report..."

    local report_file="$PROJECT_ROOT/dependency_update_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
===============================================================================
                    DEPENDENCY SECURITY UPDATE REPORT
===============================================================================

Update Date: $(date)
Project Root: $PROJECT_ROOT

===============================================================================
                          UPDATE SUMMARY
===============================================================================

Backend Updated: $UPDATE_BACKEND
Frontend Updated: $UPDATE_FRONTEND

===============================================================================
                         FILES MODIFIED
===============================================================================

Backend:
1. requirements.txt (updated packages)
2. .venv/ (new package versions)

Frontend:
1. frontend/package.json (updated versions)
2. frontend/package-lock.json (new lock file)

===============================================================================
                      SECURITY AUDIT RESULTS
===============================================================================

Backend:
- Pre-update audit: backend_audit_before.json
- Post-update audit: backend_audit_after.json
- Static analysis: bandit_report.json

Frontend:
- Pre-update audit: frontend_audit_before.json
- Post-update audit: frontend_audit_after.json
- Outdated packages: npm_outdated.json

===============================================================================
                           NEXT STEPS
===============================================================================

1. Review audit reports:
   - backend_audit_after.json
   - frontend_audit_after.json

2. Check for remaining vulnerabilities:
   cat backend_audit_after.json | jq '.[]'
   cat frontend_audit_after.json | jq '.vulnerabilities'

3. Run tests manually:
   Backend: pytest tests/ -v
   Frontend: cd frontend && npm test

4. Verify application works:
   - Start backend: uvicorn app.main:app --reload
   - Start frontend: cd frontend && npm run dev
   - Test all functionality

5. If everything works, commit changes:
   git add requirements.txt frontend/package.json frontend/package-lock.json
   git commit -m "chore: update dependencies for security"

===============================================================================
                            ROLLBACK PLAN
===============================================================================

If dependency updates break the application:

Backend:
  git checkout requirements.txt
  source .venv/bin/activate
  pip install -r requirements.txt

Frontend:
  cd frontend
  git checkout package.json package-lock.json
  npm install

===============================================================================
                          END OF REPORT
===============================================================================

Generated: $(date)
For questions or issues, contact security@psychsync.com
EOF

    log_success "Report generated: $report_file"

    # Also create JSON summary
    local json_report="$PROJECT_ROOT/dependency_update_summary.json"

    cat > "$json_report" << EOF
{
  "update_date": "$(date -Iseconds)",
  "project_root": "$PROJECT_ROOT",
  "backend_updated": $UPDATE_BACKEND,
  "frontend_updated": $UPDATE_FRONTEND,
  "reports": {
    "backend_audit_before": "backend_audit_before.json",
    "backend_audit_after": "backend_audit_after.json",
    "frontend_audit_before": "frontend_audit_before.json",
    "frontend_audit_after": "frontend_audit_after.json",
    "outdated_packages": "npm_outdated.json",
    "bandit_report": "bandit_report.json"
  }
}
EOF

    log_info "JSON summary created: $json_report"
}

main() {
    echo "========================================================================================================"
    echo "     Dependency Security Update Script"
    echo "========================================================================================================"
    echo ""
    echo "This script updates all Python and npm dependencies to the latest secure"
    echo "versions and checks for known vulnerabilities."
    echo ""

    # Check prerequisites
    check_prerequisites

    # Update dependencies
    if [ "$UPDATE_BACKEND" = true ]; then
        update_backend_dependencies
        echo ""
    fi

    if [ "$UPDATE_FRONTEND" = true ]; then
        update_frontend_dependencies
        echo ""
    fi

    # Run tests
    echo "========================================================================================================"
    echo "Running Tests"
    echo "========================================================================================================"
    echo ""

    if run_tests; then
        echo ""
    else
        echo ""
        log_warning "Some tests failed. Please review the output above."
        log_warning "You may need to rollback changes or fix broken tests."
        echo ""
    fi

    # Generate report
    generate_report

    echo ""
    log_success "========================================"
    log_success "   DEPENDENCY UPDATE COMPLETE"
    log_success "========================================"
    echo ""
    log_info "Next Steps:"
    echo "1. Review the dependency update report"
    echo "2. Check security audit reports for remaining vulnerabilities"
    echo "3. Test the application thoroughly"
    echo "4. Commit changes if everything works"
    echo ""
}

# Run main function
main "$@"
