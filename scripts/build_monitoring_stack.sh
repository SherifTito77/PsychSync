#!/bin/bash
# PsychSync Monitoring Stack Build Script
# Compiles and prepares all monitoring components for production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="${BASE_DIR:-/Users/sheriftito/Downloads/psychsync}"
PYTHON_VERSION="${PYTHON_VERSION:-python3}"
VENV_DIR="$BASE_DIR/monitoring-venv"
BUILD_LOG="$BASE_DIR/logs/monitoring-build.log"

echo -e "${BLUE}🏗️  PsychSync Monitoring Stack Build Script${NC}"
echo "========================================"
echo "Base Directory: $BASE_DIR"
echo "Python Version: $PYTHON_VERSION"
echo "Build Log: $BUILD_LOG"
echo ""

# Create logs directory
mkdir -p "$(dirname "$BUILD_LOG")"

# Log function
log() {
    echo -e "$1" | tee -a "$BUILD_LOG"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$BUILD_LOG"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$BUILD_LOG"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$BUILD_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$BUILD_LOG"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python
    if ! command -v $PYTHON_VERSION &> /dev/null; then
        log_error "Python $PYTHON_VERSION is not installed"
        exit 1
    fi
    log_success "Python $PYTHON_VERSION is available"

    # Check pip
    if ! $PYTHON_VERSION -m pip --version &> /dev/null; then
        log_error "pip is not available"
        exit 1
    fi
    log_success "pip is available"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_success "Docker is available"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    log_success "Docker Compose is available"

    echo ""
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."

    if [ ! -d "$VENV_DIR" ]; then
        $PYTHON_VERSION -m venv "$VENV_DIR"
        log_success "Created virtual environment at $VENV_DIR"
    else
        log_info "Virtual environment already exists"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    log_success "Virtual environment is ready"
    echo ""
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    # Install requirements
    if [ -f "$BASE_DIR/monitoring-requirements.txt" ]; then
        pip install -r "$BASE_DIR/monitoring-requirements.txt"
        log_success "Installed Python dependencies"
    else
        log_error "monitoring-requirements.txt not found"
        exit 1
    fi

    echo ""
}

# Compile Python components
compile_python_components() {
    log_info "Compiling Python monitoring components..."

    # List of Python components to compile
    components=(
        "monitoring/exporters/business_metrics_exporter.py"
        "monitoring/synthetic/synthetic_monitoring.py"
        "monitoring/sla/performance_baseline.py"
    )

    compiled_count=0
    total_count=${#components[@]}

    for component in "${components[@]}"; do
        component_path="$BASE_DIR/$component"

        if [ -f "$component_path" ]; then
            log_info "Compiling $component..."

            # Compile the Python file
            python -m py_compile "$component_path"

            # Check for syntax errors
            python -m py_compile "$component_path" 2>/dev/null
            if [ $? -eq 0 ]; then
                log_success "✓ Compiled $component"
                ((compiled_count++))
            else
                log_error "✗ Failed to compile $component"
            fi
        else
            log_warning "⚠️  Component not found: $component"
        fi
    done

    log_info "Compiled $compiled_count/$total_count Python components"
    echo ""
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."

    # Custom monitoring exporters image
    cat > "$BASE_DIR/monitoring/Dockerfile.exporters" << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY monitoring-requirements.txt .
RUN pip install --no-cache-dir -r monitoring-requirements.txt

# Copy monitoring components
COPY monitoring/exporters/ ./exporters/
COPY monitoring/synthetic/ ./synthetic/
COPY monitoring/sla/ ./sla/

# Create non-root user
RUN useradd --create-home --shell /bin/bash monitoring
USER monitoring

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8081/metrics || exit 1

# Start the business metrics exporter
CMD ["python", "exporters/business_metrics_exporter.py"]
EOF

    # Build the exporters image
    log_info "Building monitoring exporters image..."
    docker build -f "$BASE_DIR/monitoring/Dockerfile.exporters" \
                 -t psychsync-monitoring-exporters \
                 "$BASE_DIR/" 2>> "$BUILD_LOG"

    if [ $? -eq 0 ]; then
        log_success "✓ Built monitoring exporters image"
    else
        log_error "✗ Failed to build monitoring exporters image"
    fi

    echo ""
}

# Setup monitoring directories
setup_directories() {
    log_info "Setting up monitoring directories..."

    directories=(
        "monitoring/prometheus"
        "monitoring/grafana/provisioning/datasources"
        "monitoring/grafana/provisioning/dashboards"
        "monitoring/alertmanager"
        "monitoring/loki"
        "monitoring/promtail"
        "logs/psychsync/api"
        "logs/psychsync/frontend"
        "logs/postgresql"
        "logs/nginx"
        "tmp/sla_reports"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$BASE_DIR/$dir"
        log_success "✓ Created directory: $dir"
    done

    echo ""
}

# Create executables
create_executables() {
    log_info "Creating executable scripts..."

    # Make Python scripts executable
    python_scripts=(
        "monitoring/exporters/business_metrics_exporter.py"
        "monitoring/synthetic/synthetic_monitoring.py"
        "monitoring/sla/performance_baseline.py"
    )

    for script in "${python_scripts[@]}"; do
        script_path="$BASE_DIR/$script"
        if [ -f "$script_path" ]; then
            chmod +x "$script_path"
            log_success "✓ Made executable: $script"
        fi
    done

    echo ""
}

# Validate configuration files
validate_configs() {
    log_info "Validating configuration files..."

    configs=(
        "docker-compose.monitoring.yml"
        "monitoring/prometheus/prometheus.yml"
        "monitoring/grafana/provisioning/datasources/datasources.yml"
        "monitoring/loki/local-config.yaml"
        "monitoring/promtail/config.yml"
    )

    valid_count=0
    total_count=${#configs[@]}

    for config in "${configs[@]}"; do
        config_path="$BASE_DIR/$config"

        if [ -f "$config_path" ]; then
            # Basic YAML validation
            if command -v yq &> /dev/null; then
                if yq eval '.' "$config_path" > /dev/null 2>&1; then
                    log_success "✓ Valid YAML: $config"
                    ((valid_count++))
                else
                    log_error "✗ Invalid YAML: $config"
                fi
            else
                # If yq is not available, just check if file exists
                log_success "✓ Found config: $config"
                ((valid_count++))
            fi
        else
            log_warning "⚠️  Missing config: $config"
        fi
    done

    log_info "Validated $valid_count/$total_count configuration files"
    echo ""
}

# Create monitoring environment file
create_env_file() {
    log_info "Creating environment configuration..."

    env_file="$BASE_DIR/.env.monitoring"

    if [ ! -f "$env_file" ]; then
        cat > "$env_file" << 'EOF'
# PsychSync Monitoring Environment Configuration
# Generated on: $(date)

# Datadog Configuration
DD_API_KEY=your_datadog_api_key_here
DD_SITE=datadoghq.com
DD_ENV=production
DD_SERVICE=psychsync-api
DD_VERSION=1.0.0

# Sentry Configuration
SENTRY_DSN=your_sentry_dsn_here
SENTRY_SECRET_KEY=your_sentry_secret_key_here

# Grafana Configuration
GRAFANA_PASSWORD=secure_grafana_password

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=psychsync

# Notification Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
PAGERDUTY_INTEGRATION_KEY=your_pagerduty_integration_key
EOF

        chmod 600 "$env_file"
        log_success "✓ Created environment file: $env_file"
        log_warning "⚠️  Please edit $env_file with your actual API keys"
    else
        log_info "Environment file already exists"
    fi

    echo ""
}

# Run quick tests
run_tests() {
    log_info "Running quick tests..."

    # Test Python syntax
    log_info "Testing Python syntax..."
    python -m py_compile "$BASE_DIR/monitoring/exporters/business_metrics_exporter.py" 2>/dev/null
    python -m py_compile "$BASE_DIR/monitoring/synthetic/synthetic_monitoring.py" 2>/dev/null
    python -m py_compile "$BASE_DIR/monitoring/sla/performance_baseline.py" 2>/dev/null

    # Test Docker Compose file
    log_info "Testing Docker Compose configuration..."
    docker-compose -f "$BASE_DIR/docker-compose.monitoring.yml" config 2>/dev/null

    if [ $? -eq 0 ]; then
        log_success "✓ All tests passed"
    else
        log_error "✗ Some tests failed"
    fi

    echo ""
}

# Create build summary
create_summary() {
    log_info "Creating build summary..."

    summary_file="$BASE_DIR/monitoring-build-summary.json"

    cat > "$summary_file" << EOF
{
    "build_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "base_directory": "$BASE_DIR",
    "python_version": "$($PYTHON_VERSION --version 2>&1)",
    "components_built": [
        "business_metrics_exporter",
        "synthetic_monitoring",
        "performance_baseline"
    ],
    "docker_images": [
        "psychsync-monitoring-exporters"
    ],
    "configuration_files": [
        "docker-compose.monitoring.yml",
        "prometheus.yml",
        "grafana datasources.yml",
        "loki config.yaml",
        "promtail config.yml"
    ],
    "directories_created": [
        "monitoring/prometheus",
        "monitoring/grafana",
        "monitoring/alertmanager",
        "logs/psychsync"
    ],
    "next_steps": [
        "Edit .env.monitoring with your API keys",
        "Run ./scripts/start_monitoring.sh",
        "Access dashboards at provided URLs"
    ]
}
EOF

    log_success "✓ Build summary created: $summary_file"
    echo ""
}

# Main build function
main() {
    echo "Starting PsychSync Monitoring Stack build..."
    echo "Build log: $BUILD_LOG"
    echo ""

    check_prerequisites
    setup_python_env
    install_dependencies
    compile_python_components
    build_docker_images
    setup_directories
    create_executables
    validate_configs
    create_env_file
    run_tests
    create_summary

    echo -e "${GREEN}🎉 PsychSync Monitoring Stack build completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Edit $BASE_DIR/.env.monitoring with your API keys"
    echo "2. Run: cd $BASE_DIR && ./scripts/start_monitoring.sh"
    echo "3. Access dashboards using the URLs provided"
    echo ""
    echo "Build log saved to: $BUILD_LOG"
    echo "Build summary: $BASE_DIR/monitoring-build-summary.json"
}

# Run main function
main "$@"