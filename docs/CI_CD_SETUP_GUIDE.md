# PsychSync Enterprise CI/CD Pipeline Setup Guide

This comprehensive guide covers the setup, configuration, and deployment procedures for both GitHub Actions and Azure DevOps CI/CD pipelines.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [GitHub Actions Setup](#github-actions-setup)
4. [Azure DevOps Setup](#azure-devops-setup)
5. [Security Configuration](#security-configuration)
6. [Environment Setup](#environment-setup)
7. [Deployment Procedures](#deployment-procedures)
8. [Monitoring and Alerts](#monitoring-and-alerts)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Overview

The PsychSync platform features enterprise-grade CI/CD pipelines with:

- **Multi-stage validation**: Code quality, security scanning, comprehensive testing
- **Container security**: Docker image building, vulnerability scanning, SBOM generation
- **Performance testing**: Load testing and benchmarking
- **Automated deployments**: Staging and production environments with rollback capability
- **Comprehensive reporting**: Test analytics dashboards and executive summaries
- **Security compliance**: OWASP standards, PCI DSS considerations
- **Notification system**: Slack integration for deployment alerts

## Prerequisites

### Required Accounts and Services

1. **GitHub Repository** with admin access
2. **Azure Subscription** with:
   - Azure Container Registry (ACR)
   - Azure App Service (Web Apps)
   - Azure DevOps Organization
3. **Slack Workspace** (for notifications)
4. **Codecov Account** (for coverage reporting)

### Required Tools

- **Docker** and Docker Compose
- **Azure CLI** (`az`)
- **GitHub CLI** (`gh`)
- **Node.js 18+** and **Python 3.11+**
- **kubectl** (if using Kubernetes)

### Required Secrets and Credentials

#### GitHub Secrets
```
AZURE_CREDENTIALS          # Azure Service Principal JSON
CODECOV_TOKEN             # Codecov upload token
SLACK_WEBHOOK_URL         # Slack webhook for notifications
DOCKER_REGISTRY_PASSWORD  # ACR password
GITHUB_TOKEN              # GitHub PAT (automatic)
```

#### Azure DevOps Variable Groups
```
psychsync-secrets:
  - CODECOV_TOKEN
  - SLACK_WEBHOOK_URL
  - DOCKER_REGISTRY_PASSWORD
  - DB_CONNECTION_STRING
  - REDIS_CONNECTION_STRING

psychsync-configuration:
  - DOCKER_REGISTRY
  - CONTAINER_NAME
  - APP_SERVICE_STAGING
  - APP_SERVICE_PRODUCTION
  - RESOURCE_GROUP_STAGING
  - RESOURCE_GROUP_PRODUCTION
```

## GitHub Actions Setup

### Step 1: Create Azure Service Principal

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "psychsync-github-actions" \
  --role "Contributor" \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID" \
  --json-auth > azure-credentials.json

# Store the JSON output as AZURE_CREDENTIALS in GitHub Secrets
cat azure-credentials.json
```

### Step 2: Configure Container Registry

```bash
# Create Azure Container Registry
az acr create \
  --resource-group psychsync-rg \
  --name psychsyncacr \
  --sku Premium \
  --admin-enabled true

# Get ACR credentials
az acr credential show --name psychsyncacr

# Store in GitHub Secrets:
# DOCKER_REGISTRY=psychsyncacr.azurecr.io
# DOCKER_REGISTRY_PASSWORD=<password from above>
```

### Step 3: Create Web Apps

```bash
# Create staging web app
az webapp create \
  --resource-group psychsync-staging-rg \
  --plan psychsync-staging-plan \
  --name psychsync-staging \
  --runtime "PYTHON|3.12" \
  --deployment-container-image-name nginx

# Create production web app
az webapp create \
  --resource-group psychsync-production-rg \
  --plan psychsync-production-plan \
  --name psychsync-production \
  --runtime "PYTHON|3.12" \
  --deployment-container-image-name nginx

# Configure staging app for containers
az webapp config container set \
  --resource-group psychsync-staging-rg \
  --name psychsync-staging \
  --docker-custom-image-name nginx \
  --docker-registry-server-url https://psychsyncacr.azurecr.io

# Configure production app for containers
az webapp config container set \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --docker-custom-image-name nginx \
  --docker-registry-server-url https://psychsyncacr.azurecr.io
```

### Step 4: Set Up GitHub Secrets

```bash
# Using GitHub CLI
gh secret set AZURE_CREDENTIALS --body-file azure-credentials.json
gh secret set CODECOV_TOKEN --body "your-codecov-token"
gh secret set SLACK_WEBHOOK_URL --body "your-slack-webhook-url"
gh secret set DOCKER_REGISTRY_PASSWORD --body "your-acr-password"

# Or manually in GitHub UI:
# Repository > Settings > Secrets and variables > Actions
```

### Step 5: Deploy GitHub Actions Workflow

The workflow is already configured in `.github/workflows/github-actions-ci-cd.yml`. It includes:

- **Code Quality**: Black, isort, flake8, mypy, pylint, bandit, safety
- **Security Scanning**: Semgrep, Trivy, CodeQL, dependency checks
- **Testing**: Unit tests (Python 3.11 & 3.12), integration tests, performance tests
- **Docker**: Build, push, security scanning, SBOM generation
- **Deployment**: Staging and production with health checks and rollback

## Azure DevOps Setup

### Step 1: Create Azure DevOps Organization

1. Go to [Azure DevOps](https://dev.azure.com)
2. Create new organization: `psychsync-devops`
3. Create new project: `psychsync-platform`

### Step 2: Connect GitHub Repository

```bash
# Using Azure DevOps CLI
az devops login
az devops project create --name psychsync-platform
```

In Azure DevOps UI:
1. **Project Settings** > **Repos** > **GitHub connections**
2. Connect your GitHub repository
3. Select `psychsync` repository

### Step 3: Create Service Connection for Azure

1. **Project Settings** > **Service connections**
2. **New service connection** > **Azure Resource Manager**
3. Select **Service principal (automatic)**
4. Choose subscription and resource group
5. Name it: `psychsync-azure-subscription`

### Step 4: Create Container Registry Service Connection

1. **Project Settings** > **Service connections**
2. **New service connection** > **Docker Registry**
3. Select **Azure Container Registry**
4. Choose your ACR instance
5. Name it: `psychsync-registry`

### Step 5: Configure Variable Groups

Create two variable groups in **Library**:

#### psychsync-secrets
```
CODECOV_TOKEN = your-codecov-token
SLACK_WEBHOOK_URL = your-slack-webhook-url
DB_CONNECTION_STRING = your-db-connection-string
REDIS_CONNECTION_STRING = your-redis-connection-string
```

#### psychsync-configuration
```
DOCKER_REGISTRY = psychsyncacr.azurecr.io
CONTAINER_NAME = psychsync-api
APP_SERVICE_STAGING = psychsync-staging
APP_SERVICE_PRODUCTION = psychsync-production
RESOURCE_GROUP_STAGING = psychsync-staging-rg
RESOURCE_GROUP_PRODUCTION = psychsync-production-rg
MIN_CODE_COVERAGE = 80
MAX_SECURITY_VULNERABILITIES = 5
```

### Step 6: Deploy Azure DevOps Pipeline

The pipeline is configured in `azure-devops-pipeline.yml` and includes:

- **Validation Stage**: Code quality, linting, security scanning
- **Testing Stage**: Unit tests, integration tests, performance tests
- **Build Stage**: Docker build, frontend build, SBOM generation
- **Security Validation**: Container security analysis
- **Deployment Stages**: Staging and production with rollback
- **Cleanup Stage**: Artifact archiving and cleanup

## Security Configuration

### SSL/TLS Certificates

```bash
# Generate SSL certificates for production
./ssl_init_script.sh

# Upload certificates to Azure App Service
az webapp config ssl upload \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --certificate-file certs/api.psychsync.com.crt \
  --certificate-password your-ssl-password
```

### Environment Variables

#### Staging Environment
```bash
# App Service Configuration > Configuration > Application settings
DATABASE_URL=postgresql+asyncpg://user:pass@server:5432/psychsync_staging
REDIS_URL=redis://server:6379/1
ENVIRONMENT=staging
DEBUG=false
SECRET_KEY=your-staging-secret-key
```

#### Production Environment
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@server:5432/psychsync_production
REDIS_URL=redis://server:6379/0
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key
```

### Firewall and Network Security

```bash
# Configure Azure Web App networking
az webapp vnet-integration add \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --subnet psychsync-subnet \
  --vnet psychsync-vnet

# Configure access restrictions
az webapp config access-restriction add \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --rule-name AllowCorporateIP \
  --action Allow \
  --ip-address 203.0.113.0/24 \
  --priority 100
```

## Environment Setup

### Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/psychsync.git
cd psychsync

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up frontend
cd frontend
npm install
cd ..

# Copy environment files
cp .env.example .env.dev
# Edit .env.dev with your settings

# Start development services
docker-compose up -d postgres redis
```

### Staging Environment

```bash
# Deploy to staging via GitHub Actions
git checkout develop
git commit -m "deploy: prepare staging release"
git push origin develop

# Or trigger manually in GitHub Actions UI
# Repository > Actions > Enterprise CI/CD Pipeline > Run workflow
```

### Production Environment

```bash
# Deploy to production via GitHub Actions
git checkout main
git tag v1.0.0
git push origin main --tags

# Or trigger manually in Azure DevOps
# Pipelines > Azure DevOps Pipeline > Run pipeline
```

## Deployment Procedures

### Automated Deployment (Recommended)

#### From Development to Staging
1. Push to `develop` branch
2. Pipeline automatically runs and deploys to staging
3. Monitor deployment in GitHub Actions/Azure DevOps
4. Verify staging deployment health

#### From Staging to Production
1. Merge `develop` into `main` branch
2. Create and push version tag
3. Pipeline automatically runs production deployment
4. Monitor production deployment and health checks

### Manual Deployment (Emergency)

```bash
# Manual Docker deployment
docker build -t psychsync-api:latest .
docker tag psychsync-api:latest psychsyncacr.azurecr.io/psychsync-api:latest
docker push psychsyncacr.azurecr.io/psychsync-api:latest

# Update Azure Web App to use new image
az webapp config container set \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --docker-custom-image-name psychsyncacr.azurecr.io/psychsync-api:latest
```

### Rollback Procedures

#### Automatic Rollback
Both pipelines include automatic rollback if health checks fail.

#### Manual Rollback
```bash
# Rollback to previous version (GitHub Actions)
gh release create rollback-$(date +%Y%m%d) \
  --target previous-tag \
  --title "Emergency Rollback" \
  --notes "Rolling back due to deployment issues"

# Rollback with Azure CLI
az webapp config container set \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --docker-custom-image-name psychsyncacr.azurecr.io/psychsync-api:previous-tag
```

## Monitoring and Alerts

### Application Monitoring

```bash
# Enable Application Insights
az monitor app-insights component create \
  --app psychsync-prod-insights \
  --location eastus \
  --resource-group psychsync-production-rg \
  --application-type web

# Connect to web app
az webapp config appsettings set \
  --resource-group psychsync-production-rg \
  --name psychsync-production \
  --settings APPINSIGHTS_CONNECTION_STRING="your-connection-string"
```

### Log Analytics Setup

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group psychsync-production-rg \
  --workspace-name psychsync-logs
```

### Alert Configuration

#### GitHub Actions
- **Failed deployments**: Automatic Slack notification
- **Security vulnerabilities**: Email to security team
- **Performance degradation**: Slack alert to DevOps team

#### Azure DevOps
- **Pipeline failures**: Email to project team
- **Deployment failures**: Azure Monitor alert
- **Health check failures**: PagerDuty integration

### Custom Metrics

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
```

## Troubleshooting

### Common Issues

#### Pipeline Failures

**Issue: Docker build fails**
```bash
# Check Dockerfile syntax
docker build -t test .

# Debug build process
docker build --progress=plain -t test .
```

**Issue: Tests fail in pipeline but pass locally**
```bash
# Check environment differences
pip freeze > local-requirements.txt
# Compare with pipeline requirements

# Run tests with same environment
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

**Issue: Deployment health checks fail**
```bash
# Check application logs
az webapp log tail --resource-group psychsync-production-rg --name psychsync-production

# Check container logs
az webapp log tail --resource-group psychsync-production-rg --name psychsync-production --container
```

#### Database Issues

**Issue: Migration failures**
```bash
# Check current migration status
alembic current

# Force migration to specific version
alembic upgrade head

# Reset migration (development only)
alembic downgrade base
alembic upgrade head
```

#### Performance Issues

**Issue: Slow API responses**
```bash
# Check application metrics
curl http://localhost:8000/metrics

# Profile application
python -m cProfile -o profile.stats app/main.py

# Analyze with snakeviz
snakeviz profile.stats
```

### Debug Mode

#### Enable Debug Logging
```python
# app/core/logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed"
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"]
    }
}
```

#### Debug Commands
```bash
# Check pipeline status
gh run list --repo your-org/psychsync

# Get detailed run information
gh run view --repo your-org/psychsync <run-id>

# Download workflow artifacts
gh run download --repo your-org/psychsync <run-id>

# Azure DevOps pipeline logs
az pipelines runs list --project psychsync-platform
az pipelines runs show --project psychsync-platform --run-id <run-id>
```

## Best Practices

### Code Quality

1. **Pre-commit hooks**:
   ```bash
   # .pre-commit-config.yaml
   repos:
   - repo: https://github.com/psf/black
     rev: 22.3.0
     hooks:
     - id: black
   - repo: https://github.com/pycqa/isort
     rev: 5.10.1
     hooks:
     - id: isort
   - repo: https://github.com/pycqa/flake8
     rev: 4.0.1
     hooks:
     - id: flake8
   ```

2. **Branch protection**:
   - Require PR reviews
   - Require status checks to pass
   - Require up-to-date branches
   - Require linear history

### Security

1. **Secrets management**:
   - Never commit secrets to repository
   - Use environment-specific secrets
   - Rotate secrets regularly
   - Audit secret access

2. **Container security**:
   - Use multi-stage builds
   - Minimize attack surface
   - Regular base image updates
   - Scan images for vulnerabilities

3. **Infrastructure security**:
   - Use managed identities
   - Principle of least privilege
   - Network segmentation
   - Regular security audits

### Performance

1. **Caching strategy**:
   - Redis for session storage
   - CDN for static assets
   - Database query caching
   - API response caching

2. **Database optimization**:
   - Connection pooling
   - Query optimization
   - Regular index maintenance
   - Read replicas for scaling

3. **Monitoring**:
   - Application performance monitoring
   - Database performance metrics
   - Infrastructure monitoring
   - Custom business metrics

### Deployment

1. **Blue-green deployments**:
   - Zero downtime deployments
   - Instant rollback capability
   - Traffic shifting capabilities
   - A/B testing support

2. **Release strategy**:
   - Semantic versioning
   - Automated changelog generation
   - Release notes documentation
   - Feature flags for gradual rollout

3. **Disaster recovery**:
   - Automated backups
   - Multi-region deployment
   - Failover procedures
   - Recovery time objectives

## Additional Resources

- [Azure DevOps Documentation](https://docs.microsoft.com/en-us/azure/devops/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Security Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [PsychSync Architecture Guide](./ARCHITECTURE.md)
- [Testing Framework Documentation](./TESTING.md)

For additional support or questions, contact the DevOps team at devops@psychsync.com.
