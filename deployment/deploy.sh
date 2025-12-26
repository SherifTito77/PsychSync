#!/bin/bash

# PsychSync Production Deployment Script
# This script handles the deployment of the PsychSync application to production

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PRODUCTION_DIR="$PROJECT_ROOT/docker-compose/production"
BACKUP_DIR="/tmp/psychsync-deployment-backup"
LOG_FILE="/var/log/psychsync-deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

# Prerequisites check
check_prerequisites() {
    log "Checking deployment prerequisites..."

    # Check if running as root (required for Docker operations)
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root or with sudo"
        exit 1
    fi

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
        exit 1
    fi

    # Check if required files exist
    local required_files=(
        "$PROJECT_ROOT/.env.production"
        "$PRODUCTION_DIR/docker-compose.yml"
        "$SCRIPT_DIR/Dockerfile.backend.prod"
        "$SCRIPT_DIR/Dockerfile.frontend.prod"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file not found: $file"
            exit 1
        fi
    done

    # Check if SSL certificates exist
    if [[ ! -f "$PRODUCTION_DIR/nginx/ssl/psychsync.com.crt" ]]; then
        warn "SSL certificate not found. Please ensure SSL certificates are in place."
    fi

    log "Prerequisites check completed"
}

# Backup current deployment
backup_current() {
    log "Creating backup of current deployment..."
    mkdir -p "$BACKUP_DIR"

    # Backup environment files
    cp "$PROJECT_ROOT/.env.production" "$BACKUP_DIR/" 2>/dev/null || true

    # Backup database if running
    if docker-compose -f "$PRODUCTION_DIR/docker-compose.yml" ps -q db | grep -q .; then
        log "Creating database backup..."
        docker-compose -f "$PRODUCTION_DIR/docker-compose.yml" exec db pg_dump \
            -U psychsync_user -d psychsync_prod > "$BACKUP_DIR/pre-deployment-backup.sql" || {
            warn "Database backup failed, continuing anyway"
        }
    fi

    # Backup Docker volumes (optional, can be large)
    log "Backing up Docker volumes..."
    docker run --rm -v psychsync_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres-data.tar.gz -C /data . || {
        warn "PostgreSQL volume backup failed"
    }

    log "Backup completed: $BACKUP_DIR"
}

# Build and deploy
deploy() {
    log "Starting deployment process..."

    # Change to production directory
    cd "$PRODUCTION_DIR"

    # Pull latest images
    log "Pulling latest base images..."
    docker-compose pull

    # Build custom images
    log "Building application images..."
    docker-compose build --no-cache

    # Stop existing services
    log "Stopping existing services..."
    docker-compose down

    # Run database migrations
    log "Running database migrations..."
    docker-compose run --rm backend alembic upgrade head || {
        error "Database migration failed"
        exit 1
    }

    # Start services
    log "Starting services..."
    docker-compose up -d

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose ps | grep -q "healthy\|Up (healthy)"; then
            log "Services are healthy"
            break
        fi

        if [[ $attempt -eq $max_attempts ]]; then
            error "Services did not become healthy within expected time"
            docker-compose logs
            exit 1
        fi

        log "Waiting for services... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log "Deployment completed successfully"
}

# Health checks
health_checks() {
    log "Performing health checks..."

    # Check backend health
    local backend_health=$(curl -f -s http://localhost:8000/api/v1/health || echo "failed")
    if [[ "$backend_health" == "failed" ]]; then
        error "Backend health check failed"
        return 1
    fi
    log "Backend health check passed"

    # Check frontend accessibility
    local frontend_health=$(curl -f -s http://localhost:3000/health || echo "failed")
    if [[ "$frontend_health" == "failed" ]]; then
        warn "Frontend health check failed (this might be expected if behind reverse proxy)"
    else
        log "Frontend health check passed"
    fi

    # Check database connectivity
    if docker-compose exec -T db pg_isready -U psychsync_user -d psychsync_prod; then
        log "Database connectivity check passed"
    else
        error "Database connectivity check failed"
        return 1
    fi

    log "All health checks passed"
}

# Cleanup
cleanup() {
    log "Cleaning up..."

    # Remove unused Docker images
    docker image prune -f

    # Remove old backups (older than 7 days)
    find /tmp -name "psychsync-deployment-backup*" -mtime +7 -type d -exec rm -rf {} + 2>/dev/null || true

    log "Cleanup completed"
}

# Rollback function
rollback() {
    log "Rolling back deployment..."

    cd "$PRODUCTION_DIR"
    docker-compose down

    if [[ -f "$BACKUP_DIR/.env.production" ]]; then
        cp "$BACKUP_DIR/.env.production" "$PROJECT_ROOT/"
    fi

    # Restore database if backup exists
    if [[ -f "$BACKUP_DIR/pre-deployment-backup.sql" ]]; then
        log "Restoring database from backup..."
        docker-compose up -d db
        sleep 10
        docker-compose exec -T db psql -U psychsync_user -d psychsync_prod < "$BACKUP_DIR/pre-deployment-backup.sql"
    fi

    # Start previous version (this assumes images are still available)
    log "Starting previous version..."
    docker-compose up -d

    log "Rollback completed"
}

# Main execution
main() {
    log "Starting PsychSync production deployment..."

    # Check for command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            backup_current
            deploy
            health_checks
            cleanup
            ;;
        "rollback")
            rollback
            health_checks
            ;;
        "health-check")
            health_checks
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|health-check}"
            exit 1
            ;;
    esac

    log "Deployment process completed successfully!"
}

# Error handling
trap 'error "Deployment failed at line $LINENO"' ERR

# Execute main function
main "$@"