#!/bin/bash
# PsychSync Production Deployment Script
# Zero-downtime deployment with blue-green strategy

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-production}
BACKUP_ENABLED=${2:-true}
HEALTH_CHECK_TIMEOUT=${3:-300}
ROLLBACK_ENABLED=${4:-true}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ID="deploy-$(date +%Y%m%d-%H%M%S)"
BLUE_APP_NAME="psychsync-blue"
GREEN_APP_NAME="psychsync-green"
CURRENT_APP="unknown"
NEW_APP="unknown"

# Health check URL
HEALTH_CHECK_URL="http://localhost:8000/health"

log "Starting PsychSync production deployment"
log "Deployment ID: $DEPLOYMENT_ID"
log "Environment: $ENVIRONMENT"

# Function to check if running as root
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Function to backup current deployment
backup_deployment() {
    if [[ "$BACKUP_ENABLED" != "true" ]]; then
        warning "Backup skipped - backup not enabled"
        return
    fi

    log "Creating deployment backup..."

    BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d)"
    mkdir -p "$BACKUP_DIR"

    # Backup database
    if command -v pg_dump &> /dev/null; then
        log "Creating database backup..."
        pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/database_backup_$(date +%H%M%S).sql"
        success "Database backup completed"
    else
        warning "pg_dump not found - database backup skipped"
    fi

    # Backup application files
    log "Creating application backup..."
    cp -r "$PROJECT_ROOT" "$BACKUP_DIR/app_backup_$(date +%H%M%S)" 2>/dev/null || true
    success "Application backup completed"
}

# Function to determine current active application
determine_current_app() {
    log "Determining currently active application..."

    # Check which service is currently active
    if docker ps --format "table {{.Names}}" | grep -q "$BLUE_APP_NAME"; then
        CURRENT_APP="blue"
        NEW_APP="green"
    elif docker ps --format "table {{.Names}}" | grep -q "$GREEN_APP_NAME"; then
        CURRENT_APP="green"
        NEW_APP="blue"
    else
        log "No active application found - starting with blue"
        CURRENT_APP="none"
        NEW_APP="blue"
    fi

    success "Current active app: $CURRENT_APP, New app will be: $NEW_APP"
}

# Function to run pre-deployment validation
run_pre_deployment_validation() {
    log "Running pre-deployment validation..."

    cd "$PROJECT_ROOT"

    # Run Python validation script
    if python "$SCRIPT_DIR/pre-deployment-validation.py" --environment "$ENVIRONMENT"; then
        success "Pre-deployment validation passed"
    else
        error "Pre-deployment validation failed"
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            rollback_deployment
        fi
        exit 1
    fi
}

# Function to build and deploy new version
build_and_deploy() {
    log "Building and deploying new PsychSync version ($NEW_APP)..."

    cd "$PROJECT_ROOT"

    # Build Docker image
    log "Building Docker image for $NEW_APP..."
    docker build -t "psychsync:$DEPLOYMENT_ID" .

    # Tag for blue/green deployment
    if [[ "$NEW_APP" == "blue" ]]; then
        docker tag "psychsync:$DEPLOYMENT_ID" "psychsync:blue-latest"
    else
        docker tag "psychsync:$DEPLOYMENT_ID" "psychsync:green-latest"
    fi

    success "Docker image built successfully"

    # Stop existing $NEW_APP container if it exists
    if docker ps -a --format "table {{.Names}}" | grep -q "$NEW_APP"; then
        log "Stopping existing $NEW_APP container..."
        docker stop "$NEW_APP" || true
        docker rm "$NEW_APP" || true
    fi

    # Start new container
    log "Starting new $NEW_APP container..."
    docker run -d \
        --name "$NEW_APP" \
        --restart unless-stopped \
        -p 8001:8000 \
        -e DATABASE_URL="$DATABASE_URL" \
        -e REDIS_URL="$REDIS_URL" \
        -e SECRET_KEY="$SECRET_KEY" \
        -e ENVIRONMENT="$ENVIRONMENT" \
        -e DEBUG="false" \
        --network psychsync-network \
        "psychsync:$DEPLOYMENT_ID"

    success "New $NEW_APP container started"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."

    # Run migrations in the new container
    docker exec "$NEW_APP" alembic upgrade head

    success "Database migrations completed"
}

# Function to perform health checks
health_check() {
    local app_name=$1
    local port=$2
    local max_attempts=$3
    local attempt=1

    log "Performing health check for $app_name on port $port..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            success "Health check passed for $app_name (attempt $attempt)"
            return 0
        fi

        log "Health check failed for $app_name (attempt $attempt/$max_attempts) - retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done

    error "Health check failed for $app_name after $max_attempts attempts"
    return 1
}

# Function to switch traffic to new deployment
switch_traffic() {
    log "Switching traffic to new deployment ($NEW_APP)..."

    # Update load balancer configuration
    if command -v nginx &> /dev/null; then
        # Update nginx configuration
        if [[ "$NEW_APP" == "blue" ]]; then
            sed -i 's/proxy_pass http:\/\/localhost:8001/proxy_pass http:\/\/localhost:8000/' /etc/nginx/sites-available/psychsync
        else
            sed -i 's/proxy_pass http:\/\/localhost:8000/proxy_pass http:\/\/localhost:8001/' /etc/nginx/sites-available/psychsync
        fi

        # Test nginx configuration
        nginx -t && systemctl reload nginx
        success "Traffic switched to $NEW_APP"
    else
        warning "Nginx not found - manual traffic switch required"
    fi
}

# Function to cleanup old deployment
cleanup_old_deployment() {
    if [[ "$CURRENT_APP" != "none" ]]; then
        log "Cleaning up old deployment ($CURRENT_APP)..."

        # Stop old container
        if docker ps --format "table {{.Names}}" | grep -q "$CURRENT_APP"; then
            docker stop "$CURRENT_APP"
            docker rm "$CURRENT_APP"
            success "Old deployment stopped and removed"
        fi

        # Clean up old Docker images
        docker image prune -f > /dev/null 2>&1 || true
    fi
}

# Function to rollback deployment
rollback_deployment() {
    error "Initiating deployment rollback..."

    if [[ "$CURRENT_APP" == "none" ]]; then
        error "Cannot rollback - no previous deployment found"
        exit 1
    fi

    log "Rolling back to $CURRENT_APP..."

    # Switch traffic back
    if command -v nginx &> /dev/null; then
        if [[ "$CURRENT_APP" == "blue" ]]; then
            sed -i 's/proxy_pass http:\/\/localhost:8001/proxy_pass http:\/\/localhost:8000/' /etc/nginx/sites-available/psychsync
        else
            sed -i 's/proxy_pass http:\/\/localhost:8000/proxy_pass http:\/\/localhost:8001/' /etc/nginx/sites-available/psychsync
        fi

        nginx -t && systemctl reload nginx
    fi

    # Stop new deployment
    if docker ps --format "table {{.Names}}" | grep -q "$NEW_APP"; then
        docker stop "$NEW_APP"
        docker rm "$NEW_APP"
    fi

    success "Rollback completed - traffic restored to $CURRENT_APP"
}

# Function to monitor deployment
monitor_deployment() {
    log "Monitoring deployment for 5 minutes..."

    # Monitor for common issues
    for i in {1..30}; do
        # Check container status
        if ! docker ps --format "table {{.Names}}" | grep -q "$NEW_APP"; then
            error "Container $NEW_APP stopped unexpectedly"
            if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
                rollback_deployment
            fi
            exit 1
        fi

        # Check error logs
        error_count=$(docker logs "$NEW_APP" --since=1m 2>&1 | grep -i error | wc -l)
        if [[ $error_count -gt 5 ]]; then
            warning "High error rate detected ($error_count errors in last minute)"
        fi

        sleep 10
    done

    success "Deployment monitoring completed - no critical issues detected"
}

# Function to create deployment report
create_deployment_report() {
    local status=$1

    REPORT_FILE="$PROJECT_ROOT/deployment_reports/deployment_$(date +%Y%m%d_%H%M%S).json"
    mkdir -p "$(dirname "$REPORT_FILE")"

    cat > "$REPORT_FILE" << EOF
{
    "deployment_id": "$DEPLOYMENT_ID",
    "environment": "$ENVIRONMENT",
    "timestamp": "$(date -Iseconds)",
    "status": "$status",
    "previous_app": "$CURRENT_APP",
    "new_app": "$NEW_APP",
    "backup_enabled": $BACKUP_ENABLED,
    "rollback_enabled": $ROLLBACK_ENABLED,
    "docker_image": "psychsync:$DEPLOYMENT_ID"
}
EOF

    success "Deployment report created: $REPORT_FILE"
}

# Main deployment flow
main() {
    log "Starting PsychSync zero-downtime deployment process"

    # Check prerequisites
    check_permissions

    # Create deployment backup
    backup_deployment

    # Run pre-deployment validation
    run_pre_deployment_validation

    # Determine current app for blue-green deployment
    determine_current_app

    # Build and deploy new version
    build_and_deploy

    # Run database migrations
    run_migrations

    # Perform health checks
    if ! health_check "$NEW_APP" 8001 30; then
        error "Health check failed for new deployment"
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            rollback_deployment
            create_deployment_report "FAILED_ROLLBACK"
        else
            create_deployment_report "FAILED"
        fi
        exit 1
    fi

    # Switch traffic to new deployment
    switch_traffic

    # Monitor new deployment
    monitor_deployment

    # Cleanup old deployment
    cleanup_old_deployment

    # Create success report
    create_deployment_report "SUCCESS"

    success "🎉 PsychSync deployment completed successfully!"
    success "New version ($NEW_APP) is now live and serving traffic"
    success "Deployment ID: $DEPLOYMENT_ID"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
