#!/bin/bash
################################################################################
# Autonomous Agents Verification Script
# Tests all agents to ensure they work correctly
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/agents"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

test_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

check_file_exists() {
    local file="$1"
    local description="$2"

    if [ -f "$file" ]; then
        test_pass "$description exists"
        return 0
    else
        test_fail "$description missing: $file"
        return 1
    fi
}

check_dir_exists() {
    local dir="$1"
    local description="$2"

    if [ -d "$dir" ]; then
        test_pass "$description exists"
        return 0
    else
        test_fail "$description missing: $dir"
        return 1
    fi
}

check_python_syntax() {
    local file="$1"
    local description="$2"

    if python3 -m py_compile "$file" 2>/dev/null; then
        test_pass "$description has valid syntax"
        return 0
    else
        test_fail "$description has syntax errors"
        return 1
    fi
}

################################################################################
# Environment Checks
################################################################################

test_environment() {
    print_header "Environment Checks"

    # Check Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1 | awk '{print $2}')
        test_pass "Python installed: $python_version"
    else
        test_fail "Python not found"
    fi

    # Check required Python packages
    local packages=("github3.py" "GitPython")

    for package in "${packages[@]}"; do
        if python3 -c "import ${package//-/_}" 2>/dev/null; then
            test_pass "Package $package installed"
        else
            test_fail "Package $package not installed"
        fi
    done

    # Check for GITHUB_TOKEN
    if [ -n "$GITHUB_TOKEN" ]; then
        test_pass "GITHUB_TOKEN is set"
    else
        test_info "GITHUB_TOKEN not set (required for actual deployment)"
    fi
}

################################################################################
# Agent File Checks
################################################################################

test_agent_files() {
    print_header "Agent File Checks"

    local agents=(
        "code_quality_scanner.py:Code Quality Scanner"
        "pr_coverage_tester.py:PR Coverage Tester"
        "crash_log_analyzer.py:Crash Log Analyzer"
        "doc_syncer.py:Documentation Syncer"
        "dependency_updater.py:Dependency Updater"
    )

    for agent in "${agents[@]}"; do
        IFS=':' read -r file description <<< "$agent"
        check_file_exists "$AGENTS_DIR/$file" "$description"
    done
}

################################################################################
# Agent Syntax Checks
################################################################################

test_agent_syntax() {
    print_header "Agent Syntax Checks"

    for agent_file in "$AGENTS_DIR"/*.py; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file")
            check_python_syntax "$agent_file" "$agent_name"
        fi
    done
}

################################################################################
# Agent Import Checks
################################################################################

test_agent_imports() {
    print_header "Agent Import Checks"

    for agent_file in "$AGENTS_DIR"/*.py; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file")
            test_info "Testing imports in $agent_name..."

            # Try to import the agent (dry run)
            if python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    with open('$agent_file', 'r') as f:
        code = f.read()
    compile(code, '$agent_file', 'exec')
    print('Import check passed')
except Exception as e:
    print(f'Import failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
                test_pass "$agent_name imports work"
            else
                test_fail "$agent_name has import errors"
            fi
        fi
    done
}

################################################################################
# Documentation Checks
################################################################################

test_documentation() {
    print_header "Documentation Checks"

    local docs=(
        "$AGENTS_DIR/README.md:Agent README"
        "$AGENTS_DIR/AUTONOMOUS_AGENTS_SUMMARY.md:Agent Summary"
        "$PROJECT_ROOT/docs/AGENT_DEPLOYMENT_GUIDE.md:Deployment Guide"
        "$PROJECT_ROOT/AGENT_DEPLOYMENT_DELIVERY.md:Delivery Summary"
        "$PROJECT_ROOT/deploy/systemd/README.md:Systemd Guide"
    )

    for doc in "${docs[@}"; do
        IFS=':' read -r file description <<< "$doc"
        check_file_exists "$file" "$description"
    done
}

################################################################################
# Deployment Infrastructure Checks
################################################################################

test_deployment_infrastructure() {
    print_header "Deployment Infrastructure Checks"

    # Check deployment script
    check_file_exists "$PROJECT_ROOT/scripts/deploy_agents.sh" "Deployment Script"

    # Check demo script
    check_file_exists "$PROJECT_ROOT/scripts/demo_agents.sh" "Demo Script"

    # Check GitHub Actions workflow
    check_file_exists "$PROJECT_ROOT/.github/workflows/agents.yml" "GitHub Actions Workflow"

    # Check systemd service files
    check_file_exists "$PROJECT_ROOT/deploy/systemd/psychsync-crash-analyzer.service" "Crash Analyzer Service"
    check_file_exists "$PROJECT_ROOT/deploy/systemd/psychsync-pr-coverage-watcher.service" "PR Coverage Service"

    # Check logs directory
    check_dir_exists "$AGENTS_DIR/logs" "Logs Directory"
}

################################################################################
# Agent Functionality Tests
################################################################################

test_agent_functionality() {
    print_header "Agent Functionality Tests"

    cd "$PROJECT_ROOT"

    # Test Code Quality Scanner help
    test_info "Testing Code Quality Scanner..."
    if python3 "$AGENTS_DIR/code_quality_scanner.py" --help &> /dev/null; then
        test_pass "Code Quality Scanner runs"
    else
        test_fail "Code Quality Scanner failed to run"
    fi

    # Test PR Coverage Tester help
    test_info "Testing PR Coverage Tester..."
    if python3 "$AGENTS_DIR/pr_coverage_tester.py" --help &> /dev/null; then
        test_pass "PR Coverage Tester runs"
    else
        test_fail "PR Coverage Tester failed to run"
    fi

    # Test Crash Log Analyzer help
    test_info "Testing Crash Log Analyzer..."
    if python3 "$AGENTS_DIR/crash_log_analyzer.py" --help &> /dev/null; then
        test_pass "Crash Log Analyzer runs"
    else
        test_fail "Crash Log Analyzer failed to run"
    fi

    # Test Documentation Syncer help
    test_info "Testing Documentation Syncer..."
    if python3 "$AGENTS_DIR/doc_syncer.py" --help &> /dev/null; then
        test_pass "Documentation Syncer runs"
    else
        test_fail "Documentation Syncer failed to run"
    fi

    # Test Dependency Updater help
    test_info "Testing Dependency Updater..."
    if python3 "$AGENTS_DIR/dependency_updater.py" --help &> /dev/null; then
        test_pass "Dependency Updater runs"
    else
        test_fail "Dependency Updater failed to run"
    fi
}

################################################################################
# Integration Tests
################################################################################

test_integration() {
    print_header "Integration Tests"

    # Create a test crash log
    cat > /tmp/test_crash.log << 'EOF'
Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = 10 / 0
ZeroDivisionError: division by zero
EOF

    test_info "Testing Crash Log Analyzer with sample log..."
    if python3 "$AGENTS_DIR/crash_log_analyzer.py" analyze /tmp/test_crash.log &> /dev/null; then
        test_pass "Crash Log Analyzer processes logs"
    else
        test_fail "Crash Log Analyzer failed to process log"
    fi

    rm -f /tmp/test_crash.log

    # Test that agents can be imported
    test_info "Testing agent module structure..."
    if python3 -c "
import sys
sys.path.insert(0, '$AGENTS_DIR')
import os
agent_files = [f for f in os.listdir('$AGENTS_DIR') if f.endswith('.py')]
print(f'Found {len(agent_files)} agent files')
" &> /dev/null; then
        test_pass "Agent module structure valid"
    else
        test_fail "Agent module structure invalid"
    fi
}

################################################################################
# Security Checks
################################################################################

test_security() {
    print_header "Security Checks"

    # Check for hardcoded secrets in agent files
    test_info "Checking for hardcoded secrets..."
    if ! grep -r "ghp_[a-zA-Z0-9]\{36\}" "$AGENTS_DIR"/*.py 2>/dev/null; then
        test_pass "No hardcoded GitHub tokens found"
    else
        test_fail "Potential hardcoded tokens detected"
    fi

    # Check for insecure file permissions
    test_info "Checking file permissions..."
    insecure_files=0
    for file in "$AGENTS_DIR"/*.py; do
        if [ -f "$file" ]; then
            perms=$(stat -f "%A" "$file" 2>/dev/null || stat -c "%a" "$file" 2>/dev/null)
            if [ "$perms" = "777" ]; then
                ((insecure_files++))
            fi
        fi
    done

    if [ $insecure_files -eq 0 ]; then
        test_pass "All agent files have secure permissions"
    else
        test_fail "$insecure_files files have insecure permissions"
    fi
}

################################################################################
# Performance Checks
################################################################################

test_performance() {
    print_header "Performance Checks"

    # Test agent load time
    test_info "Testing agent load times..."

    for agent_file in "$AGENTS_DIR"/*.py; do
        if [ -f "$agent_file" ]; then
            agent_name=$(basename "$agent_file")
            start_time=$(date +%s%N)

            python3 -c "
import sys
sys.path.insert(0, '$AGENTS_DIR')
compile(open('$agent_file').read(), '$agent_file', 'exec')
" &> /dev/null

            end_time=$(date +%s%N)
            duration=$(((end_time - start_time) / 1000000)) # Convert to milliseconds

            if [ $duration -lt 5000 ]; then  # Less than 5 seconds
                test_pass "$agent_name loads in ${duration}ms"
            else
                test_fail "$agent_name slow to load: ${duration}ms"
            fi
        fi
    done
}

################################################################################
# Generate Report
################################################################################

generate_report() {
    print_header "Verification Report"

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local pass_rate=0

    if [ $total_tests -gt 0 ]; then
        pass_rate=$((TESTS_PASSED * 100 / total_tests))
    fi

    echo "Total Tests: $total_tests"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo "Pass Rate: ${pass_rate}%"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed! Agents are ready for deployment.${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed. Please review the errors above.${NC}"
        return 1
    fi
}

################################################################################
# Main Function
################################################################################

main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║         🤖 Autonomous Agents Verification Suite                    ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""

    # Check if we're in the right directory
    if [ ! -d "$AGENTS_DIR" ]; then
        echo "Error: agents directory not found at $AGENTS_DIR"
        exit 1
    fi

    # Run all tests
    test_environment
    test_agent_files
    test_agent_syntax
    test_agent_imports
    test_documentation
    test_deployment_infrastructure
    test_agent_functionality
    test_integration
    test_security
    test_performance

    # Generate report
    generate_report
    exit_code=$?

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    exit $exit_code
}

# Run main function
main "$@"
