#!/bin/bash

# ==========================================
# PsychSync Production Deployment Script
# ==========================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/psychsync/deploy-production.log"
BACKUP_DIR="/var/backups/psychsync"
HELM_CHART="$PROJECT_ROOT/helm/psychsync"
NAMESPACE="psychsync"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Pre-flight checks
preflight_checks() {
    log "🔍 Running pre-flight checks..."

    # Check if running in production environment
    if [[ "${ENVIRONMENT:-}" != "production" ]]; then
        error "This script should only be run in production environment"
        error "Set ENVIRONMENT=production and try again"
        exit 1
    fi

    # Check required tools
    local tools=("kubectl" "helm" "docker" "aws" "jq")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            error "Required tool not found: $tool"
            exit 1
        fi
    done

    # Check Kubernetes connection
    if ! kubectl cluster-info >/dev/null 2>&1; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check Helm
    if ! helm repo list >/dev/null 2>&1; then
        error "Cannot access Helm repositories"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        error "AWS credentials not configured"
        exit 1
    fi

    success "Pre-flight checks passed"
}

# Create necessary directories
setup_directories() {
    log "📁 Setting up directories..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    success "Directories created"
}

# Load environment variables
load_environment() {
    log "🔧 Loading environment variables..."

    if [[ -f "$PROJECT_ROOT/deploy/production-config.env" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "$PROJECT_ROOT/deploy/production-config.env"
        set +a
        success "Environment variables loaded"
    else
        error "Production configuration file not found"
        exit 1
    fi
}

# Create database backup
create_database_backup() {
    log "💾 Creating database backup..."

    local backup_file="$BACKUP_DIR/pre-deploy-backup-$(date +%Y%m%d-%H%M%S).sql"

    # Get database credentials from Kubernetes secret
    local db_host db_port db_user db_password db_name
    db_host=$(kubectl get secret psychsync-secrets -n "$NAMESPACE" -o jsonpath='{.data.database-host}' | base64 -d)
    db_port=$(kubectl get secret psychsync-secrets -n "$NAMESPACE" -o jsonpath='{.data.database-port}' | base64 -d)
    db_user=$(kubectl get secret psychsync-secrets -n "$NAMESPACE" -o jsonpath='{.data.database-user}' | base64 -d)
    db_password=$(kubectl get secret psychsync-secrets -n "$NAMESPACE" -o jsonpath='{.data.database-password}' | base64 -d)
    db_name="psychsync"

    # Create backup using pg_dump
    if PGPASSWORD="$db_password" pg_dump -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" \
        --no-owner --no-privileges --compress=9 \
        --file="$backup_file" 2>>"$LOG_FILE"; then
        success "Database backup created: $backup_file"

        # Upload backup to S3
        local s3_key="backups/$(basename "$backup_file")"
        if aws s3 cp "$backup_file" "s3://psychsync-backups-prod/$s3_key" \
            --server-side-encryption AES256 2>>"$LOG_FILE"; then
            success "Backup uploaded to S3: $s3_key"
        else
            warning "Failed to upload backup to S3"
        fi
    else
        error "Failed to create database backup"
        exit 1
    fi
}

# Build and push Docker image
build_and_push_image() {
    log "🐳 Building Docker image..."

    local image_tag="ghcr.io/psychsync/backend:$(date +%Y%m%d-%H%M%S)"
    local git_sha=$(git rev-parse --short HEAD)

    # Build Docker image
    if docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$git_sha" \
        --build-arg VERSION="$(date +%Y%m%d-%H%M%S)" \
        -t "$image_tag" \
        -t "ghcr.io/psychsync/backend:latest" \
        "$PROJECT_ROOT" 2>>"$LOG_FILE"; then
        success "Docker image built: $image_tag"
    else
        error "Failed to build Docker image"
        exit 1
    fi

    # Push to container registry
    if docker push "$image-tag" 2>>"$LOG_FILE" && docker push "ghcr.io/psychsync/backend:latest" 2>>"$LOG_FILE"; then
        success "Docker images pushed to registry"
        echo "$image_tag" > /tmp/deployed-image-tag.txt
    else
        error "Failed to push Docker images"
        exit 1
    fi
}

# Update Helm dependencies
update_helm_dependencies() {
    log "📦 Updating Helm dependencies..."

    if helm dependency update "$HELM_CHART" 2>>"$LOG_FILE"; then
        success "Helm dependencies updated"
    else
        error "Failed to update Helm dependencies"
        exit 1
    fi
}

# Deploy using Blue-Green strategy
blue_green_deploy() {
    log "🚀 Starting Blue-Green deployment..."

    local image_tag=$(cat /tmp/deployed-image-tag.txt)
    local active_color="green"
    local new_color="blue"

    # Determine current active color
    if kubectl get service psychsvc-active -n "$NAMESPACE" -o jsonpath='{.spec.selector.color}' 2>/dev/null | grep -q "blue"; then
        active_color="blue"
        new_color="green"
    fi

    log "Current active color: $active_color"
    log "Deploying new version to color: $new_color"

    # Deploy new version
    if helm upgrade --install "psychsync-$new_color" "$HELM_CHART" \
        --namespace "$NAMESPACE" \
        --set image.tag="$image_tag" \
        --set environment="production" \
        --set deployment.color="$new_color" \
        --set service.type="ClusterIP" \
        --set ingress.enabled=false \
        --set resources.requests.memory="1Gi" \
        --set resources.requests.cpu="500m" \
        --set resources.limits.memory="4Gi" \
        --set resources.limits.cpu="2000m" \
        --set replicaCount=5 \
        --set autoscaling.enabled=true \
        --set autoscaling.minReplicas=5 \
        --set autoscaling.maxReplicas=20 \
        --set monitoring.enabled=true \
        --set backup.enabled=true \
        --wait \
        --timeout=10m 2>>"$LOG_FILE"; then

        success "New deployment created: $new_color"

        # Wait for pods to be ready
        log "⏳ Waiting for pods to be ready..."
        if kubectl wait --for=condition=ready pod \
            -l app=psychsync,color="$new_color" \
            -n "$NAMESPACE" \
            --timeout=600s 2>>"$LOG_FILE"; then

            success "All pods are ready"

            # Health check
            log "🏥 Running health checks..."
            local health_url="http://psychsync-$new_color.$NAMESPACE.svc.cluster.local/health"

            for i in {1..30}; do
                if kubectl run "health-check-$new_color" --image=curlimages/curl --rm -i --restart=Never \
                    -- curl -f -s "$health_url" >/dev/null 2>&1; then
                    success "Health check passed"
                    break
                fi

                if [[ $i -eq 30 ]]; then
                    error "Health check failed after 30 attempts"
                    exit 1
                fi

                log "Health check attempt $i/30..."
                sleep 10
            done

            # Switch traffic to new deployment
            log "🔄 Switching traffic to new deployment..."
            if kubectl patch service psychsvc-active -n "$NAMESPACE" \
                -p "{\"spec\":{\"selector\":{\"color\":\"$new_color\"}}}" 2>>"$LOG_FILE"; then

                success "Traffic switched to $new_color deployment"

                # Wait and monitor
                log "⏳ Monitoring new deployment..."
                sleep 30

                # Verify deployment is working
                if kubectl run "verification-check" --image=curlimages/curl --rm -i --restart=Never \
                    -- curl -f -s "https://api.psychsync.com/health" >/dev/null 2>&1; then

                    success "Deployment verification passed"

                    # Clean up old deployment after successful switch
                    log "🧹 Cleaning up old deployment: $active_color"
                    helm uninstall "psychsync-$active_color" -n "$NAMESPACE" 2>>"$LOG_FILE" || true

                    success "Blue-Green deployment completed successfully"
                else
                    error "Deployment verification failed - rolling back"
                    kubectl patch service psychsvc-active -n "$NAMESPACE" \
                        -p "{\"spec\":{\"selector\":{\"color\":\"$active_color\"}}}" 2>>"$LOG_FILE"
                    exit 1
                fi
            else
                error "Failed to switch traffic"
                exit 1
            fi
        else
            error "Pods failed to become ready"
            exit 1
        fi
    else
        error "Helm deployment failed"
        exit 1
    fi
}

# Update monitoring configuration
update_monitoring() {
    log "📊 Updating monitoring configuration..."

    # Update Prometheus rules
    if kubectl apply -f "$PROJECT_ROOT/monitoring/prometheus/rules/" -n monitoring 2>>"$LOG_FILE"; then
        success "Prometheus rules updated"
    else
        warning "Failed to update Prometheus rules"
    fi

    # Update Grafana dashboards
    if kubectl apply -f "$PROJECT_ROOT/monitoring/grafana/dashboards/" -n monitoring 2>>"$LOG_FILE"; then
        success "Grafana dashboards updated"
    else
        warning "Failed to update Grafana dashboards"
    fi
}

# Run smoke tests
run_smoke_tests() {
    log "🧪 Running smoke tests..."

    # Test API endpoints
    local endpoints=(
        "https://api.psychsync.com/health"
        "https://api.psychsync.com/api/v1/users/me"
        "https://api.psychsync.com/api/v1/assessments"
        "https://api.psychsync.com/api/v1/teams"
    )

    for endpoint in "${endpoints[@]}"; do
        log "Testing: $endpoint"
        if curl -f -s -o /dev/null "$endpoint" 2>>"$LOG_FILE"; then
            success "✅ $endpoint"
        else
            error "❌ $endpoint"
            return 1
        fi
    done

    # Test database connectivity
    log "Testing database connectivity..."
    if kubectl run "db-test" --image=postgres:15-alpine --rm -i --restart=Never \
        -- psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
        success "✅ Database connectivity"
    else
        error "❌ Database connectivity"
        return 1
    fi

    # Test Redis connectivity
    log "Testing Redis connectivity..."
    if kubectl run "redis-test" --image=redis:7-alpine --rm -i --restart=Never \
        -- redis-cli -h redis-cluster.psychsync.internal ping >/dev/null 2>&1; then
        success "✅ Redis connectivity"
    else
        error "❌ Redis connectivity"
        return 1
    fi

    success "All smoke tests passed"
}

# Update feature flags
update_feature_flags() {
    log "🎯 Updating feature flags..."

    # Launch new features gradually
    local flags=(
        "new_ui_theme:0.25"
        "ai_insights:0.10"
        "enhanced_search:0.50"
        "advanced_analytics:1.0"
    )

    for flag_config in "${flags[@]}"; do
        local flag_name="${flag_config%:*}"
        local flag_value="${flag_config#*:}"

        log "Setting $flag_name to $flag_value"

        # Call feature flag service
        curl -X POST "https://api.psychsync.com/admin/feature-flags/$flag_name" \
            -H "Authorization: Bearer $ADMIN_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"enabled\": true, \"rollout_percentage\": $flag_value}" \
            2>>"$LOG_FILE" || warning "Failed to update $flag_name"
    done

    success "Feature flags updated"
}

# Generate deployment report
generate_deployment_report() {
    log "📋 Generating deployment report..."

    local report_file="$BACKUP_DIR/deployment-report-$(date +%Y%m%d-%H%M%S).json"
    local image_tag=$(cat /tmp/deployed-image-tag.txt)

    cat > "$report_file" << EOF
{
    "deployment": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "environment": "production",
        "image_tag": "$image_tag",
        "git_sha": "$(git rev-parse HEAD)",
        "git_branch": "$(git rev-parse --abbrev-ref HEAD)",
        "deployed_by": "$(whoami)",
        "deployment_type": "blue_green",
        "status": "success"
    },
    "infrastructure": {
        "namespace": "$NAMESPACE",
        "replicas": "$(kubectl get deployment psychsync-blue -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo 'N/A')",
        "pods": "$(kubectl get pods -n "$NAMESPACE" -l app=psychsync --no-headers | wc -l | tr -d ' ')",
        "services": "$(kubectl get services -n "$NAMESPACE" --no-headers | wc -l | tr -d ' ')"
    },
    "monitoring": {
        "prometheus_url": "https://prometheus.psychsync.com",
        "grafana_url": "https://grafana.psychsync.com",
        "jaeger_url": "https://jaeger.psychsync.com"
    },
    "backup": {
        "database_backup": "$(ls -t "$BACKUP_DIR"/pre-deploy-backup-*.sql | head -1 | xargs basename)",
        "s3_backup_location": "s3://psychsync-backups-prod/backups/"
    }
}
EOF

    success "Deployment report generated: $report_file"

    # Send notification to Slack
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{
                \"text\": \"🚀 PsychSync Production Deployment Completed Successfully\",
                \"attachments\": [{
                    \"color\": \"good\",
                    \"fields\": [{
                        \"title\": \"Environment\",
                        \"value\": \"Production\",
                        \"short\": true
                    }, {
                        \"title\": \"Image Tag\",
                        \"value\": \"$image_tag\",
                        \"short\": true
                    }, {
                        \"title\": \"Deployed By\",
                        \"value\": \"$(whoami)\",
                        \"short\": true
                    }, {
                        \"title\": \"Deployment Type\",
                        \"value\": \"Blue-Green\",
                        \"short\": true
                    }]
                }]
            }" 2>>"$LOG_FILE" || warning "Failed to send Slack notification"
    fi
}

# Cleanup temporary files
cleanup() {
    log "🧹 Cleaning up temporary files..."
    rm -f /tmp/deployed-image-tag.txt
    success "Cleanup completed"
}

# Main execution
main() {
    log "🚀 Starting PsychSync Production Deployment"
    log "============================================"

    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Execute deployment steps
    preflight_checks
    setup_directories
    load_environment
    create_database_backup
    build_and_push_image
    update_helm_dependencies
    blue_green_deploy
    update_monitoring
    run_smoke_tests
    update_feature_flags
    generate_deployment_report
    cleanup

    log "============================================"
    success "🎉 Production deployment completed successfully!"
    log "📊 Monitoring: https://grafana.psychsync.com"
    log "📈 Metrics: https://prometheus.psychsync.com"
    log "🔍 Tracing: https://jaeger.psychsync.com"
    log "🌐 Application: https://app.psychsync.com"
}

# Error handling
trap 'error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
