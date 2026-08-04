#!/bin/bash
################################################################################
# Autonomous Agents Deployment Script
# Deploys and configures all autonomous agents for production use
################################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/agents"
LOGS_DIR="$AGENTS_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

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

check_env_var() {
    if [ -z "${!1}" ]; then
        log_error "Environment variable $1 is not set"
        log_info "Please set it: export $1=\"value\""
        return 1
    fi
    return 0
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check if we're in the right directory
    if [ ! -d "$AGENTS_DIR" ]; then
        log_error "Agents directory not found at $AGENTS_DIR"
        exit 1
    fi

    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python version: $python_version"

    # Check required environment variables
    log_info "Checking environment variables..."
    check_env_var "GITHUB_TOKEN" || exit 1
    check_env_var "GITHUB_REPOSITORY" || exit 1

    # Create logs directory
    if [ ! -d "$LOGS_DIR" ]; then
        log_info "Creating logs directory..."
        mkdir -p "$LOGS_DIR"
    fi

    # Check if required Python packages are installed
    log_info "Checking Python dependencies..."
    required_packages="github3.py GitPython pylint flake8 isort bandit safety autopep8"

    for package in $required_packages; do
        if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
            log_warning "Package '$package' not found. Installing..."
            pip install "$package"
        fi
    done

    log_success "Pre-flight checks passed!"
}

################################################################################
# Install Agent Dependencies
################################################################################

install_dependencies() {
    log_info "Installing agent dependencies..."

    cd "$PROJECT_ROOT"

    # Install Python packages
    log_info "Installing Python dependencies..."
    pip install --quiet \
        github3.py \
        GitPython \
        pylint \
        flake8 \
        isort \
        bandit \
        safety \
        autopep8 \
        pip-outdated \
        2>&1 | grep -v "already satisfied" || true

    log_success "Dependencies installed!"
}

################################################################################
# Setup Cron Jobs
################################################################################

setup_cron_jobs() {
    log_info "Setting up cron jobs..."

    # Backup existing crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

    # Create temporary crontab file
    tmp_cron=$(mktemp)

    # Get existing crontab (if any)
    crontab -l > "$tmp_cron" 2>/dev/null || touch "$tmp_cron"

    # Check if jobs already exist
    if grep -q "agents/code_quality_scanner.py" "$tmp_cron" 2>/dev/null; then
        log_warning "Cron jobs already exist. Skipping..."
        return
    fi

    # Add cron jobs
    cat >> "$tmp_cron" << 'EOF'

# =============================================================================
# PsychSync Autonomous Agents
# =============================================================================

# Daily code quality scan at 2 AM
0 2 * * * cd /Users/sheriftito/Downloads/psychsync && python3 agents/code_quality_scanner.py >> agents/logs/scanner.log 2>&1

# Weekly dependency update on Sunday at 3 AM
0 3 * * 0 cd /Users/sheriftito/Downloads/psychsync && python3 agents/dependency_updater.py schedule >> agents/logs/updater.log 2>&1

# Hourly documentation sync
0 * * * * cd /Users/sheriftito/Downloads/psychsync && python3 agents/doc_syncer.py scan >> agents/logs/docsyncer.log 2>&1

EOF

    # Install new crontab
    crontab "$tmp_cron"
    rm "$tmp_cron"

    log_success "Cron jobs installed!"
    log_info "View crontab: crontab -l"
}

################################################################################
# Setup Systemd Services (for continuous agents)
################################################################################

setup_systemd_services() {
    log_info "Setting up systemd services..."

    # Only run on Linux with systemd
    if ! command -v systemctl &> /dev/null; then
        log_warning "systemctl not found. Skipping systemd setup..."
        return
    fi

    current_user=$(whoami)

    # Create systemd service file for crash log analyzer
    cat > /tmp/psychsync-crash-analyzer.service << EOF
[Unit]
Description=PsychSync Crash Log Analyzer
After=network.target

[Service]
Type=simple
User=$current_user
WorkingDirectory=$PROJECT_ROOT
ExecStart=$(which python3) $AGENTS_DIR/crash_log_analyzer.py watch /var/log/app/errors.log
Restart=always
RestartSec=60
StandardOutput=append:$LOGS_DIR/crash_analyzer.log
StandardError=append:$LOGS_DIR/crash_analyzer.log

[Install]
WantedBy=multi-user.target
EOF

    # Copy service file (requires sudo)
    if [ "$EUID" -eq 0 ]; then
        cp /tmp/psychsync-crash-analyzer.service /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable psychsync-crash-analyzer.service
        log_success "Systemd service installed!"
    else
        log_warning "Not running as root. To install systemd service:"
        log_info "sudo cp /tmp/psychsync-crash-analyzer.service /etc/systemd/system/"
        log_info "sudo systemctl daemon-reload"
        log_info "sudo systemctl enable psychsync-crash-analyzer.service"
    fi

    rm -f /tmp/psychsync-crash-analyzer.service
}

################################################################################
# Configure Agent Settings
################################################################################

configure_agents() {
    log_info "Configuring agent settings..."

    # Create .env.agents file
    cat > "$PROJECT_ROOT/.env.agents" << 'EOF'
# Autonomous Agent Configuration
# Generated by deploy_agents.sh

# GitHub Settings
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPOSITORY=psychsync/psychsync

# Code Quality Scanner
ENABLE_PYLINT=true
ENABLE_FLAKE8=true
ENABLE_ISORT=true
ENABLE_BANDIT=true
ENABLE_SAFETY=true

# PR Coverage Tester
MIN_COVERAGE=90.0
MIN_FILE_COVERAGE=80.0
TEST_COMMAND=pytest

# Dependency Updater
MAX_UPDATES=3
BLOCKLIST=
REQUIRE_TESTS=true

# Crash Log Analyzer
CRASH_LOG_PATH=/var/log/app/errors.log
SENTRY_DSN=

# Documentation Syncer
SYNC_INTERVAL_MINUTES=60
EOF

    log_warning "Please edit .env.agents and set GITHUB_TOKEN"
    log_info "Configuration template created at .env.agents"
}

################################################################################
# Test Agent Deployment
################################################################################

test_deployment() {
    log_info "Testing agent deployment..."

    # Test code quality scanner
    log_info "Testing code quality scanner..."
    cd "$PROJECT_ROOT"
    python3 agents/code_quality_scanner.py --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "Code quality scanner: OK"
    else
        log_error "Code quality scanner: FAILED"
    fi

    # Test PR coverage tester
    log_info "Testing PR coverage tester..."
    python3 agents/pr_coverage_tester.py --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "PR coverage tester: OK"
    else
        log_error "PR coverage tester: FAILED"
    fi

    # Test crash log analyzer
    log_info "Testing crash log analyzer..."
    python3 agents/crash_log_analyzer.py --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "Crash log analyzer: OK"
    else
        log_error "Crash log analyzer: FAILED"
    fi

    # Test documentation syncer
    log_info "Testing documentation syncer..."
    python3 agents/doc_syncer.py --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "Documentation syncer: OK"
    else
        log_error "Documentation syncer: FAILED"
    fi

    # Test dependency updater
    log_info "Testing dependency updater..."
    python3 agents/dependency_updater.py --help > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_success "Dependency updater: OK"
    else
        log_error "Dependency updater: FAILED"
    fi
}

################################################################################
# Deploy to GitHub Actions
################################################################################

deploy_github_actions() {
    log_info "Setting up GitHub Actions workflows..."

    workflows_dir="$PROJECT_ROOT/.github/workflows"

    # Create workflows directory if it doesn't exist
    mkdir -p "$workflows_dir"

    # Copy workflow files (if they don't exist)
    if [ ! -f "$workflows_dir/agents.yml" ]; then
        log_warning "GitHub Actions workflow not found. Please create it manually."
        log_info "See agents/README.md for examples."
    fi

    log_success "GitHub Actions setup complete!"
}

################################################################################
# Main Deployment Flow
################################################################################

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          PsychSync Autonomous Agents Deployment               ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Parse command line arguments
    DEPLOY_TYPE="${1:-all}"

    case $DEPLOY_TYPE in
        all)
            log_info "Deploying all agents..."
            preflight_checks
            install_dependencies
            configure_agents
            setup_cron_jobs
            setup_systemd_services
            test_deployment
            deploy_github_actions
            ;;
        cron)
            log_info "Deploying cron jobs only..."
            preflight_checks
            setup_cron_jobs
            ;;
        systemd)
            log_info "Deploying systemd services only..."
            setup_systemd_services
            ;;
        test)
            log_info "Running deployment tests..."
            test_deployment
            ;;
        *)
            echo "Usage: $0 [all|cron|systemd|test]"
            echo ""
            echo "Options:"
            echo "  all     - Deploy everything (default)"
            echo "  cron    - Setup cron jobs only"
            echo "  systemd - Setup systemd services only"
            echo "  test    - Test deployment"
            exit 1
            ;;
    esac

    echo ""
    log_success "Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env.agents and set your GITHUB_TOKEN"
    echo "2. Source the configuration: source .env.agents"
    echo "3. View logs: tail -f agents/logs/*.log"
    echo "4. Check cron: crontab -l"
    echo ""
}

# Run main function
main "$@"
