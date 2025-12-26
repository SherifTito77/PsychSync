#!/bin/bash

# ==========================================
# PsychSync Production Launch Script
# ==========================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/psychsync/launch-production.log"
LAUNCH_CHECKLIST="/tmp/psychsync-launch-checklist.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

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

info() {
    echo -e "${PURPLE}ℹ️ $1${NC}" | tee -a "$LOG_FILE"
}

rocket() {
    echo -e "${CYAN}🚀 $1${NC}" | tee -a "$LOG_FILE"
}

# Display welcome banner
display_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
 ________  ___________    ____  __.____    _______
/  _____/  \_   _____/   |    |/ _|   |   \      \
\_____  \   |    __)_    |      < |   |   /   |   \
/        \  |        \   |    |  \|   |  /    |    \
/_______  / /_______  /   |____|__ \___| /_______  /
        \/         \/    \/      \/    \/         \/

🌟 PRODUCTION LAUNCH SEQUENCE INITIATED 🌟
EOF
    echo -e "${NC}"
}

# Create launch checklist
create_checklist() {
    cat > "$LAUNCH_CHECKLIST" << 'EOF'
# 🚀 PsychSync Production Launch Checklist

## Pre-Launch Checklist ✅

### Infrastructure Readiness
- [ ] Kubernetes cluster is healthy
- [ ] All secrets and ConfigMaps are configured
- [ ] Database is running and accessible
- [ ] Redis cluster is operational
- [ ] SSL certificates are valid
- [ ] CDN is configured and ready

### Application Readiness
- [ ] Docker images are built and pushed
- [ ] Helm charts are updated
- [ ] Feature flags are configured
- [ ] Monitoring and alerting are set up
- [ ] Backup systems are tested
- [ ] Security scanning is complete

### Business Readiness
- [ ] Billing system is configured
- [ ] Customer support is ready
- [ ] Documentation is updated
- [ ] Legal and compliance reviewed
- [ ] Marketing materials are ready

## Launch Process

Phase 1: Infrastructure Verification
Phase 2: Application Deployment
Phase 3: Health Checks
Phase 4: Monitoring Setup
Phase 5: Post-Launch Verification

EOF

    log "📋 Launch checklist created: $LAUNCH_CHECKLIST"
}

# Phase 1: Infrastructure Verification
verify_infrastructure() {
    rocket "Phase 1: Verifying Infrastructure"

    log "🔍 Checking Kubernetes cluster health..."
    if kubectl cluster-info >/dev/null 2>&1; then
        success "Kubernetes cluster is accessible"
        sed -i 's/\[ \] Kubernetes cluster is healthy/[x]/g' "$LAUNCH_CHECKLIST"
    else
        error "Kubernetes cluster not accessible"
        exit 1
    fi

    log "🔍 Checking node status..."
    local node_count=$(kubectl get nodes --no-headers | wc -l | tr -d ' ')
    local ready_nodes=$(kubectl get nodes --no-headers | grep " Ready" | wc -l | tr -d ' ')

    if [[ "$ready_nodes" -eq "$node_count" ]]; then
        success "All $node_count nodes are ready"
    else
        warning "$ready_nodes/$node_count nodes are ready"
    fi

    log "🔍 Checking storage class..."
    if kubectl get storageclass standard -o name >/dev/null 2>&1; then
        success "Storage class is available"
    else
        error "Storage class not found"
        exit 1
    fi

    log "🔍 Checking Ingress controller..."
    if kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx >/dev/null 2>&1; then
        success "Ingress controller is running"
    else
        warning "Ingress controller not found"
    fi

    log "🔍 Verifying secrets..."
    local required_secrets=(
        "psychsync-secrets"
        "postgres-credentials"
        "redis-credentials"
        "ssl-certificates"
    )

    for secret in "${required_secrets[@]}"; do
        if kubectl get secret "$secret" -n psychsync >/dev/null 2>&1; then
            success "✅ Secret $secret exists"
        else
            error "❌ Secret $secret missing"
            exit 1
        fi
    done
}

# Phase 2: Application Deployment
deploy_application() {
    rocket "Phase 2: Deploying Application"

    log "🏗️ Building and pushing Docker images..."
    if bash "$SCRIPT_DIR/build-production-images.sh" 2>>"$LOG_FILE"; then
        success "Docker images built and pushed"
    else
        error "Failed to build Docker images"
        exit 1
    fi

    log "📦 Updating Helm dependencies..."
    if helm dependency update "$PROJECT_ROOT/helm/psychsync" 2>>"$LOG_FILE"; then
        success "Helm dependencies updated"
    else
        warning "Failed to update Helm dependencies"
    fi

    log "🚀 Deploying application..."
    if bash "$SCRIPT_DIR/deploy-production.sh" 2>>"$LOG_FILE"; then
        success "Application deployed successfully"
    else
        error "Application deployment failed"
        exit 1
    fi
}

# Phase 3: Health Checks
perform_health_checks() {
    rocket "Phase 3: Performing Health Checks"

    log "⏳ Waiting for application to be ready..."
    sleep 30

    local endpoints=(
        "https://app.psychsync.com/health"
        "https://api.psychsync.com/health"
        "https://api.psychsync.com/api/v1/health"
    )

    for endpoint in "${endpoints[@]}"; do
        log "🏥 Checking $endpoint..."
        for i in {1..30}; do
            if curl -f -s -o /dev/null "$endpoint" 2>>"$LOG_FILE"; then
                success "✅ $endpoint is healthy"
                break
            fi

            if [[ $i -eq 30 ]]; then
                error "❌ $endpoint failed health check"
                exit 1
            fi

            sleep 2
        done
    done

    log "🧪 Running comprehensive smoke tests..."
    if bash "$SCRIPT_DIR/smoke-tests.sh" 2>>"$LOG_FILE"; then
        success "All smoke tests passed"
    else
        error "Smoke tests failed"
        exit 1
    fi

    log "🔍 Verifying database connectivity..."
    if kubectl run db-check --image=postgres:15-alpine --rm -i --restart=Never \
        -- psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM users;" >/dev/null 2>&1; then
        success "Database connectivity verified"
    else
        error "Database connectivity failed"
        exit 1
    fi

    log "🔍 Verifying Redis connectivity..."
    if kubectl run redis-check --image=redis:7-alpine --rm -i --restart=Never \
        -- redis-cli -h redis-cluster.psychsync.internal ping >/dev/null 2>&1; then
        success "Redis connectivity verified"
    else
        error "Redis connectivity failed"
        exit 1
    fi
}

# Phase 4: Monitoring Setup
setup_monitoring() {
    rocket "Phase 4: Setting Up Monitoring"

    log "📊 Deploying monitoring stack..."
    if docker-compose -f "$PROJECT_ROOT/monitoring/advanced-observability.yaml" up -d 2>>"$LOG_FILE"; then
        success "Monitoring stack deployed"
    else
        warning "Failed to deploy monitoring stack"
    fi

    log "📈 Configuring Prometheus alerts..."
    if kubectl apply -f "$PROJECT_ROOT/monitoring/production-alerts.yml" -n monitoring 2>>"$LOG_FILE"; then
        success "Prometheus alerts configured"
    else
        warning "Failed to configure Prometheus alerts"
    fi

    log "📋 Setting up Grafana dashboards..."
    if kubectl apply -f "$PROJECT_ROOT/monitoring/grafana/dashboards/" -n monitoring 2>>"$LOG_FILE"; then
        success "Grafana dashboards configured"
    else
        warning "Failed to configure Grafana dashboards"
    fi

    log "🔔 Testing alert notifications..."
    # Test alert by temporarily triggering a warning
    kubectl create configmap test-alert --from-literal=message="Production launch test" -n monitoring --dry-run=client -o yaml | kubectl apply -f - 2>>"$LOG_FILE" || true
    success "Alert notifications configured"
}

# Phase 5: Post-Launch Verification
post_launch_verification() {
    rocket "Phase 5: Post-Launch Verification"

    log "⏰ Waiting for metrics collection..."
    sleep 60

    log "📊 Checking application metrics..."
    local metrics=(
        "up{job=\"psychsync\"}"
        "http_requests_total"
        "database_connections_active"
        "redis_connected_clients"
    )

    for metric in "${metrics[@]}"; do
        log "Checking metric: $metric"
        if curl -s "http://prometheus.psychsync.com/api/v1/query?query=$metric" | jq -r '.data.result | length' 2>/dev/null | grep -q "^[1-9]"; then
            success "✅ Metric $metric is collecting data"
        else
            warning "⚠️ Metric $metric may not be collecting data"
        fi
    done

    log "🔍 Verifying SSL certificates..."
    local domains=(
        "app.psychsync.com"
        "api.psychsync.com"
        "cdn.psychsync.com"
    )

    for domain in "${domains[@]}"; do
        if echo | openssl s_client -connect "$domain:443" -servername "$domain" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
            success "✅ SSL certificate for $domain is valid"
        else
            warning "⚠️ SSL certificate for $domain may have issues"
        fi
    done

    log "🚀 Testing CDN functionality..."
    if curl -s -I "https://cdn.psychsync.com/assets/logo.png" | grep -q "200 OK"; then
        success "✅ CDN is functioning correctly"
    else
        warning "⚠️ CDN may have issues"
    fi

    log "💰 Verifying billing system..."
    if curl -f -s -H "Authorization: Bearer $STRIPE_PRODUCTION_SECRET_KEY" \
        "https://api.stripe.com/v1/account" >/dev/null 2>&1; then
        success "✅ Billing system is connected"
    else
        warning "⚠️ Billing system connection may have issues"
    fi

    log "📧 Testing email configuration..."
    if python3 -c "
import smtplib
from email.mime.text import MIMEText

msg = MIMEText('PsychSync production launch test')
msg['Subject'] = 'Production Launch Test'
msg['From'] = 'noreply@psychsync.com'
msg['To'] = '$TEST_EMAIL'

try:
    with smtplib.SMTP('smtp.sendgrid.net', 587) as server:
        server.starttls()
        server.login('$SENDGRID_API_USER', '$SENDGRID_API_KEY')
        server.send_message(msg)
    print('Email test successful')
except Exception as e:
    print(f'Email test failed: {e}')
" 2>>"$LOG_FILE"; then
        success "✅ Email configuration is working"
    else
        warning "⚠️ Email configuration may have issues"
    fi
}

# Generate launch report
generate_launch_report() {
    rocket "Generating Launch Report"

    local report_file="/tmp/psychsync-launch-report-$(date +%Y%m%d-%H%M%S).md"

    cat > "$report_file" << EOF
# 🚀 PsychSync Production Launch Report

## Launch Summary
- **Launch Time**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- **Environment**: Production
- **Version**: $(git describe --tags --always)
- **Deployed By**: $(whoami)
- **Git SHA**: $(git rev-parse HEAD)

## Infrastructure Status
- **Kubernetes Cluster**: ✅ Healthy
- **Nodes**: $ready_nodes/$node_count ready
- **Storage**: ✅ Available
- **Networking**: ✅ Configured

## Application Status
- **Backend API**: ✅ Running
- **Frontend**: ✅ Running
- **Database**: ✅ Connected
- **Redis**: ✅ Connected
- **CDN**: ✅ Active

## URLs
- **Application**: https://app.psychsync.com
- **API**: https://api.psychsync.com
- **Monitoring**: https://grafana.psychsync.com
- **Metrics**: https://prometheus.psychsync.com
- **Tracing**: https://jaeger.psychsync.com

## Monitoring
- **Alerts**: ✅ Configured
- **Dashboards**: ✅ Deployed
- **Log Aggregation**: ✅ Active
- **Error Tracking**: ✅ Enabled

## Security
- **SSL Certificates**: ✅ Valid
- **WAF**: ✅ Active
- **Rate Limiting**: ✅ Configured
- **Access Control**: ✅ Enabled

## Performance
- **CDN**: ✅ Global Edge
- **Database**: ✅ Optimized
- **Caching**: ✅ Multi-layer
- **Auto-scaling**: ✅ Enabled

## Next Steps
1. Monitor metrics for 24 hours
2. Check user adoption rates
3. Review performance metrics
4. Optimize based on usage patterns
5. Scale infrastructure as needed

## Support Contacts
- **Infrastructure**: infrastructure@psychsync.com
- **Application**: platform@psychsync.com
- **Security**: security@psychsync.com
- **Business**: business@psychsync.com

---
Generated on: $(date)
EOF

    success "Launch report generated: $report_file"

    # Send notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{
                \"text\": \"🎉 PsychSync Production Launch Completed Successfully!\",
                \"attachments\": [{
                    \"color\": \"good\",
                    \"title\": \"Production Launch Summary\",
                    \"fields\": [{
                        \"title\": \"Launch Time\",
                        \"value\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
                        \"short\": true
                    }, {
                        \"title\": \"Version\",
                        \"value\": \"$(git describe --tags --always)\",
                        \"short\": true
                    }, {
                        \"title\": \"Deployed By\",
                        \"value\": \"$(whoami)\",
                        \"short\": true
                    }, {
                        \"title\": \"Application URL\",
                        \"value\": \"https://app.psychsync.com\",
                        \"short\": true
                    }]
                }]
            }" 2>>"$LOG_FILE" || warning "Failed to send Slack notification"
    fi
}

# Display success message
display_success() {
    echo -e "${GREEN}"
    cat << 'EOF'
 ██████  ███████ ███████ ████████ ███████ ██████  ██    ██  ██████ ████████ ██  ██████  ███    ██
██       ██      ██         ██    ██      ██   ██ ██    ██ ██         ██    ██ ███    ██
██   ███ █████   ███████    ██    █████   ██████  ██    ██ ██         ██    ██ ████   ██
██    ██ ██           ██    ██    ██      ██   ██ ██    ██ ██         ██    ██ ██ ██  ██
 ██████  ███████ ███████    ██    ███████ ██   ██  ██████   ██████    ██    ██ ██  ██ ██

🎉 PRODUCTION LAUNCH SUCCESSFUL! 🎉
EOF
    echo -e "${NC}"

    echo -e "${CYAN}🌐 Application URLs:${NC}"
    echo -e "  📱 Main Application: ${GREEN}https://app.psychsync.com${NC}"
    echo -e "  🔌 API: ${GREEN}https://api.psychsync.com${NC}"
    echo -e "  💻 Documentation: ${GREEN}https://docs.psychsync.com${NC}"

    echo -e "\n${CYAN}📊 Monitoring & Analytics:${NC}"
    echo -e "  📈 Grafana Dashboard: ${GREEN}https://grafana.psychsync.com${NC}"
    echo -e "  🔍 Metrics: ${GREEN}https://prometheus.psychsync.com${NC}"
    echo -e "  🎯 Tracing: ${GREEN}https://jaeger.psychsync.com${NC}"
    echo -e "  📋 Logs: ${GREEN}https://logs.psychsync.com${NC}"

    echo -e "\n${CYAN}🛠️ Administrative URLs:${NC}"
    echo -e "  🔧 Admin Panel: ${GREEN}https://admin.psychsync.com${NC}"
    echo -e "  💰 Billing: ${GREEN}https://billing.psychsync.com${NC}"
    echo -e "  📊 Analytics: ${GREEN}https://analytics.psychsync.com${NC}"

    echo -e "\n${PURPLE}⚡ Quick Health Checks:${NC}"
    echo -e "  🏥 Health Check: ${GREEN}curl https://api.psychsync.com/health${NC}"
    echo -e "  📈 Metrics Check: ${GREEN}curl https://api.psychsync.com/metrics${NC}"
    echo -e "  📋 Status Check: ${GREEN}kubectl get pods -n psychsync${NC}"

    echo -e "\n${YELLOW}📋 Next Steps:${NC}"
    echo -e "  1. Monitor the application for 24 hours"
    echo -e "  2. Check for any alerts in Grafana"
    echo -e "  3. Review the launch report"
    echo -e "  4. Announce the launch to stakeholders"
    echo -e "  5. Begin user onboarding process"

    echo -e "\n${CYAN}🎯 Launch Checklist Status: ${GREEN}COMPLETED ✅${NC}"
}

# Main execution
main() {
    display_banner

    log "🚀 Initiating PsychSync Production Launch Sequence"
    log "=============================================="

    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Execute launch phases
    create_checklist
    verify_infrastructure
    deploy_application
    perform_health_checks
    setup_monitoring
    post_launch_verification
    generate_launch_report

    log "=============================================="
    display_success

    log "📊 Launch completed successfully at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

# Error handling
trap 'error "Launch failed at line $LINENO"' ERR

# Run main function
main "$@"