#!/bin/bash
###############################################################################
# SBOM & Dependency Security Tool Installation
#
# Installs all required tools for SBOM generation, vulnerability scanning,
# and dependency security in compliance with NIST SSDF, SLSA, and SBOM+VEX
#
# Usage: scripts/install_sbstools.sh
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

check_installed() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

echo "========================================================================================================"
echo "     SBOM & Dependency Security Tool Installation"
echo "========================================================================================================"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

if ! check_installed python3; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

if ! check_installed npm; then
    log_error "npm is required but not installed"
    exit 1
fi

if ! check_installed docker; then
    log_warning "Docker not found - some tools may not work"
fi

log_success "Prerequisites check passed"

# Install Python tools
log_info "Installing Python SBOM and security tools..."

pip3 install --upgrade pip

# CycloneDX for Python
log_info "Installing CycloneDX for Python..."
pip3 install cyclonedx-bom --quiet
pip3 install cyclonedx-python --quiet

# Trivy for vulnerability scanning
log_info "Installing Trivy vulnerability scanner..."
if check_installed trivy; then
    log_success "Trivy already installed"
else
    log_info "Downloading Trivy..."
    wget -qO- https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    log_success "Trivy installed"
fi

# Safety (Safety CLI for security scanning)
log_info "Installing Safety CLI..."
pip3 install safety --quiet

# Bandit for Python security linting
log_info "Installing Bandit security linter..."
pip3 install bandit --quiet

# sigstore for signing
log_info "Installing sigstore for artifact signing..."
pip3 install sigstore --quiet

log_success "Python tools installed successfully"

# Install Node.js tools
log_info "Installing Node.js SBOM and security tools..."

cd "$PROJECT_ROOT/frontend" || exit 1

# npm audit fix
log_info "Running npm audit..."
npm audit --production || log_warning "Some vulnerabilities found"

# Install CycloneDX for Node.js
log_info "Installing CycloneDX for Node.js..."
npm install --save-dev @cyclonedx/cyclonedx-npm --quiet || log_warning "CycloneDX npm install failed"

# Sbomify (alternative SBOM tool)
log_info "Installing sbomify..."
npm install --save-dev sbomify --quiet || log_warning "sbomify install failed"

cd "$PROJECT_ROOT" || exit 1

log_success "Node.js tools installed successfully"

# Verify installations
log_info "Verifying installations..."

tools_ok=true

if check_installed cyclonedx-py; then
    log_success "✓ CycloneDX Python installed"
else
    log_error "✗ CycloneDX Python installation failed"
    tools_ok=false
fi

if check_installed trivy; then
    log_success "✓ Trivy installed"
else
    log_error "✗ Trivy installation failed"
    tools_ok=false
fi

if check_installed safety; then
    log_success "✓ Safety CLI installed"
else
    log_error "✗ Safety CLI installation failed"
    tools_ok=false
fi

if check_installed bandit; then
    log_success "✓ Bandit installed"
else
    log_error "✗ Bandit installation failed"
    tools_ok=false
fi

if check_installed sigstore; then
    log_success "✓ sigstore installed"
else
    log_error "✗ sigstore installation failed"
    tools_ok=false
fi

# Test CycloneDX for Python
log_info "Testing CycloneDX Python..."
python3 -c "import cyclonedx; print('CycloneDX Python OK')" || log_warning "CycloneDX Python test failed"

# Test Trivy
log_info "Testing Trivy..."
trivy --version || log_warning "Trivy test failed"

# Test Safety
log_info "Testing Safety CLI..."
safety --version || log_warning "Safety test failed"

# Test Bandit
log_info "Testing Bandit..."
bandit --version || log_warning "Bandit test failed"

echo ""
echo "========================================================================================================"
if [ "$tools_ok" = true ]; then
    log_success "All SBOM and security tools installed successfully!"
    echo ""
    echo "Next Steps:"
    echo "1. Run: scripts/generate_sbom.sh"
    echo "2. Scan: scripts/scan_dependencies.sh"
    echo "3. Verify: scripts/verify_sbom.sh"
else
    log_error "Some tools failed to install. Please check the errors above."
    exit 1
fi
echo "========================================================================================================"
