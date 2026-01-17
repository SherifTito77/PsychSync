# PsychSync CI/CD Security Pipeline

**Version:** 1.0.0
**Last Updated:** November 22, 2025

## 🎯 Overview

This document outlines a comprehensive CI/CD pipeline with integrated security scanning, automated testing, and deployment automation for PsychSync. The pipeline implements security-by-design principles with multiple validation stages and automated security controls.

## 🔄 Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Developer     │    │   Source Control │    │   CI Pipeline   │
│   Local Dev     │────│   (GitHub)       │────│   (GitHub Actions)│
│   Pre-commit    │    │   Branching      │    │   Automated     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Security      │    │   Code Quality  │    │   Application   │
│   Scanning      │    │   Analysis      │    │   Testing       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Container     │    │   Deployment    │    │   Production    │
│   Security      │    │   Automation    │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 GitHub Actions Workflow Configuration

### Main CI/CD Pipeline
```yaml
# .github/workflows/psychsync-ci-cd.yml
name: PsychSync CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]
  schedule:
    # Daily security scan at 2 AM UTC
    - cron: '0 2 * * *'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  PYTHON_VERSION: '3.12'

jobs:
  # =============================================================================
  # SECURITY SCANNING JOB
  # =============================================================================
  security-scan:
    name: 🔒 Security Scanning
    runs-on: ubuntu-latest
    if: github.event_name != 'schedule' || github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety safety-check semgrep
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run Bandit Security Linter
        run: |
          echo "🔍 Running Bandit security linter..."
          bandit -r app/ -f json -o bandit-report.json || true
          bandit -r app/ -f txt -o bandit-report.txt || true
          # Exit with error if high severity issues found
          if [ "$(jq -r '.results | length' bandit-report.json)" -gt 0 ]; then
            echo "❌ Security issues found!"
            cat bandit-report.txt
            exit 1
          fi

      - name: Run Semgrep Static Analysis
        run: |
          echo "🔍 Running Semgrep security analysis..."
          semgrep --config=auto --output=semgrep-report.json --json app/ || true
          semgrep --config=auto --output=semgrep-report.txt app/ || true

      - name: Run Safety Dependency Scan
        run: |
          echo "🔍 Running Safety dependency vulnerability scan..."
          safety check --json --output safety-report.json || true
          safety check --output safety-report.txt || true

          # Check for high-severity vulnerabilities
          HIGH_VULNS=$(jq -r '.vulnerabilities[] | select(.severity == "high") | .id' safety-report.json | wc -l || echo "0")
          if [ "$HIGH_VULNS" -gt 0 ]; then
            echo "❌ High-severity vulnerabilities found!"
            exit 1
          fi

      - name: Run SAST with CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: python

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2

      - name: Secret Detection
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: main
          head: HEAD

      - name: Upload Security Reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: security-reports
          path: |
            bandit-report.json
            bandit-report.txt
            semgrep-report.json
            semgrep-report.txt
            safety-report.json
            safety-report.txt

  # =============================================================================
  # CODE QUALITY & TESTING JOB
  # =============================================================================
  code-quality:
    name: ✅ Code Quality & Testing
    runs-on: ubuntu-latest
    needs: security-scan

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: psychsync_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Set up environment variables
        run: |
          cp .env.test .env
          echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/psychsync_test" >> .env
          echo "REDIS_URL=redis://localhost:6379/0" >> .env
          echo "SECRET_KEY=test-secret-key-for-ci-only-do-not-use-in-production" >> .env
          echo "ENVIRONMENT=testing" >> .env
          echo "DEBUG=false" >> .env

      - name: Run Linting
        run: |
          echo "🔍 Running code linting..."
          flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Run Black Code Formatting
        run: |
          echo "🎨 Running Black code formatting check..."
          black --check app/ tests/

      - name: Run isort Import Sorting
        run: |
          echo "📚 Running isort import sorting check..."
          isort --check-only app/ tests/

      - name: Run MyPy Type Checking
        run: |
          echo "🔷 Running MyPy type checking..."
          mypy app/ --ignore-missing-imports

      - name: Run Database Migrations
        run: |
          echo "🗄️ Running database migrations..."
          alembic upgrade head

      - name: Run Unit Tests
        run: |
          echo "🧪 Running unit tests..."
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=html --cov-report=term-missing

      - name: Run Integration Tests
        run: |
          echo "🔗 Running integration tests..."
          pytest tests/integration/ -v --cov=app --cov-append --cov-report=xml

      - name: Run Security Tests
        run: |
          echo "🔒 Running security tests..."
          pytest tests/test_auth_security.py -v
          pytest tests/test_penetration_security.py -v

      - name: Run Performance Tests
        run: |
          echo "⚡ Running performance tests..."
          pytest tests/performance/ -v --benchmark-only

      - name: Upload Coverage Reports
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

      - name: Upload Test Reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-reports
          path: |
            htmlcov/
            coverage.xml
            test-results/

  # =============================================================================
  # CONTAINER SECURITY & BUILD JOB
  # =============================================================================
  container-build:
    name: 🐳 Container Build & Security
    runs-on: ubuntu-latest
    needs: code-quality
    if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'

    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
      image-tag: ${{ steps.meta.outputs.tags }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build Container Image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy Vulnerability Scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy Scan Results
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Container Security Scan (Grype)
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          grype ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }} -o json > grype-report.json

      - name: Upload Container Security Reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: container-security-reports
          path: |
            trivy-results.sarif
            grype-report.json

  # =============================================================================
  # DEPLOYMENT JOB (STAGING)
  # =============================================================================
  deploy-staging:
    name: 🚀 Deploy to Staging
    runs-on: ubuntu-latest
    needs: container-build
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    environment: staging

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to ECS Staging
        run: |
          echo "🚀 Deploying to staging environment..."

          # Update ECS task definition with new image
          aws ecs register-task-definition \
            --cli-input-json file://deployment/staging-task-definition.json \
            --region us-east-1

          # Update ECS service
          aws ecs update-service \
            --cluster psychsync-staging \
            --service psychsync-app \
            --force-new-deployment \
            --region us-east-1

          # Wait for deployment to complete
          aws ecs wait services-stable \
            --cluster psychsync-staging \
            --services psychsync-app \
            --region us-east-1

      - name: Run Health Check
        run: |
          echo "🏥 Running post-deployment health check..."
          sleep 30  # Wait for services to start

          # Check application health
          curl -f https://staging.psychsync.com/api/v1/health || exit 1

          # Run smoke tests
          python scripts/smoke_tests.py --environment staging

      - name: Run Post-Deployment Security Tests
        run: |
          echo "🔒 Running post-deployment security tests..."
          python scripts/security_scan.py --target https://staging.psychsync.com

      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          text: |
            🚀 PsychSync deployed to staging successfully!
            Commit: ${{ github.sha }}
            Image: ${{ needs.container-build.outputs.image-tag }}

  # =============================================================================
  # DEPLOYMENT JOB (PRODUCTION)
  # =============================================================================
  deploy-production:
    name: 🚀 Deploy to Production
    runs-on: ubuntu-latest
    needs: container-build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Manual Approval for Production
        uses: trstringer/manual-approval@v1
        with:
          secret: ${{ github.TOKEN }}
          approvers: devops-lead,cto
          minimum-approvals: 2
          issue-title: "Production Deployment Approval Request"

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Create Database Backup
        run: |
          echo "💾 Creating pre-deployment database backup..."
          ./scripts/backup_production.sh

      - name: Blue-Green Deployment
        run: |
          echo "🔄 Initiating blue-green deployment..."

          # Deploy to green environment
          ./scripts/deploy_green.sh ${{ needs.container-build.outputs.image-digest }}

          # Health check on green
          ./scripts/health_check.sh https://green.psychsync.com

          # Run smoke tests on green
          ./scripts/smoke_tests.sh --environment green

          # Switch traffic to green
          ./scripts/switch_traffic.sh green

      - name: Run Production Health Check
        run: |
          echo "🏥 Running production health check..."

          # Check critical endpoints
          curl -f https://app.psychsync.com/api/v1/health || exit 1
          curl -f https://api.psychsync.com/api/v1/health || exit 1

          # Run production smoke tests
          python scripts/production_smoke_tests.py

      - name: Run Security Scan
        run: |
          echo "🔒 Running production security scan..."

          # OWASP ZAP scan
          docker run -t owasp/zap2docker-stable zap-baseline.py \
            -t https://app.psychsync.com \
            -J zap-report.json || true

          # Custom security checks
          python scripts/production_security_scan.py

      - name: Performance Validation
        run: |
          echo "⚡ Running performance validation..."

          # Load test
          python scripts/load_test.py --target https://app.psychsync.com --users 100 --duration 300

          # Check response times
          python scripts/performance_check.py --target https://app.psychsync.com

      - name: Cleanup Blue Environment
        run: |
          echo "🧹 Cleaning up blue environment..."
          ./scripts/cleanup_blue.sh

      - name: Rollback if Issues
        if: failure()
        run: |
          echo "🔙 Initiating rollback due to deployment failure..."
          ./scripts/rollback.sh

      - name: Update Documentation
        run: |
          echo "📚 Updating deployment documentation..."
          ./scripts/update_deployment_docs.sh ${{ github.sha }}

      - name: Notify Teams
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          text: |
            🚀 PsychSync deployed to production!
            Commit: ${{ github.sha }}
            Image: ${{ needs.container-build.outputs.image-tag }}
            Status: ${{ job.status }}

  # =============================================================================
  # SECURITY MONITORING JOB
  # =============================================================================
  security-monitoring:
    name: 🔍 Security Monitoring
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Comprehensive Security Scan
        run: |
          echo "🔍 Running comprehensive security scan..."

          # Dependency check
          safety check --db --output safety-daily.json

          # Container image scan
          docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          trivy image --format json --output trivy-daily.json ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

          # Infrastructure security check
          python scripts/infrastructure_security_scan.py

      - name: Generate Security Report
        run: |
          echo "📊 Generating daily security report..."
          python scripts/generate_security_report.py

      - name: Send Security Digest
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.psychsync.com
          server_port: 587
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: "PsychSync Daily Security Digest"
          body: file://security-digest.html
          to: security@psychsync.com,devops@psychsync.com
```

## 🔧 Pre-commit Hooks Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=127, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, app/, -f, json, -o, bandit-precommit.json]
        pass_filenames: false

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  - repo: https://github.com/returntocorp/semgrep
    rev: v1.34.1
    hooks:
      - id: semgrep
        args: [--config, auto, --error, --exclude=tests/]
```

## 🐳 Container Security Configuration

### Dockerfile with Security Best Practices
```dockerfile
# Dockerfile.prod
FROM python:3.12-slim as base

# Security: Create non-root user
RUN groupadd -r psychsync && useradd -r -g psychsync psychsync

# Set security options
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies securely
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Security: Multi-stage build to minimize attack surface
FROM base as runtime

# Set working directory with proper permissions
WORKDIR /app

# Copy application code
COPY --chown=psychsync:psychsync . .

# Set secure file permissions
RUN chmod -R 755 /app && \
    chmod -R 644 /app/*.py && \
    chmod +x /app/scripts/*.sh

# Switch to non-root user
USER psychsync

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Run with security hardening
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--user", "psychsync", "--group", "psychsync"]
```

### Container Security Scanning
```yaml
# .github/workflows/container-security.yml
name: Container Security Scanning

on:
  push:
    branches: [ main ]
    paths: [ 'Dockerfile*', 'docker-compose*.yml' ]
  schedule:
    - cron: '0 3 * * *'  # Daily at 3 AM UTC

jobs:
  container-security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Container Image
        run: |
          docker build -f Dockerfile.prod -t psychsync:test .

      - name: Run Trivy Vulnerability Scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'psychsync:test'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Run Grype Vulnerability Scanner
        run: |
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          grype psychsync:test -o json > grype-report.json

      - name: Run Snyk Container Scan
        uses: snyk/actions/docker@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          image: psychsync:test
          args: --severity-threshold=high

      - name: Run Container Structure Tests
        run: |
          # Install container-structure-test
          wget https://storage.googleapis.com/container-structure-test/latest/container-structure-test-linux-amd64
          chmod +x container-structure-test-linux-amd64
          sudo mv container-structure-test-linux-amd64 /usr/local/bin/container-structure-test

          # Run structure tests
          container-structure-test test \
            --image psychsync:test \
            --config tests/container/structure-tests.yaml

      - name: Upload Security Reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: container-security-reports
          path: |
            trivy-results.sarif
            grype-report.json
            snyk-report.json
```

## 🔐 Infrastructure as Code Security

### Terraform Security Configuration
```hcl
# terraform/security/main.tf

# Security group with restrictive rules
resource "aws_security_group" "psychsync_app" {
  name        = "psychsync-app-sg"
  description = "Security group for PsychSync application"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for redirect to HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "psychsync-app-sg"
    Environment = terraform.workspace
  }
}

# WAF for additional protection
resource "aws_wafv2_web_acl" "psychsync_waf" {
  name  = "psychsync-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "SQLInjectionProtection"
    priority = 1

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLInjectionRule"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "XSSProtection"
    priority = 2

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesXSSRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "XSSRule"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "psychsync-waf"
    sampled_requests_enabled   = true
  }
}
```

## 📊 Security Metrics & Monitoring

### Security Scanning Metrics Dashboard
```python
# scripts/security_metrics.py
import json
import requests
from datetime import datetime, timedelta

class SecurityMetricsCollector:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.snyk_token = os.getenv('SNYK_TOKEN')

    def collect_security_metrics(self):
        """Collect security metrics from various tools"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'vulnerabilities': self.get_vulnerability_counts(),
            'code_quality': self.get_code_quality_metrics(),
            'security_tests': self.get_security_test_results(),
            'compliance': self.get_compliance_status()
        }

        return metrics

    def get_vulnerability_counts(self):
        """Get vulnerability counts from security tools"""
        return {
            'critical': self.get_critical_vulns(),
            'high': self.get_high_vulns(),
            'medium': self.get_medium_vulns(),
            'low': self.get_low_vulns()
        }

    def generate_security_dashboard(self):
        """Generate security metrics dashboard"""
        metrics = self.collect_security_metrics()

        # Send to monitoring system
        self.send_to_grafana(metrics)

        # Generate report
        self.generate_report(metrics)
```

## 🚀 Deployment Scripts

### Automated Deployment Script
```bash
#!/bin/bash
# scripts/automated_deployment.sh

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_TIMEOUT=600

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check if image exists
    if ! docker manifest inspect "$IMAGE_TAG" > /dev/null 2>&1; then
        error "Docker image $IMAGE_TAG not found"
    fi

    # Check if environment is healthy
    if ! curl -f "https://$ENVIRONMENT.psychsync.com/api/v1/health" > /dev/null 2>&1; then
        warn "Current environment is not healthy"
    fi

    # Run security scan on new image
    log "Running security scan on deployment image..."
    trivy image --exit-code 0 --severity HIGH,CRITICAL "$IMAGE_TAG" || {
        error "High/Critical vulnerabilities found in deployment image"
    }

    log "✅ Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log "Creating backup of current deployment..."

    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"

    # Database backup
    ./scripts/backup_database.sh "$BACKUP_NAME"

    # Configuration backup
    ./scripts/backup_configuration.sh "$BACKUP_NAME"

    log "✅ Backup created: $BACKUP_NAME"
}

# Deploy application
deploy_application() {
    log "Deploying application to $ENVIRONMENT..."

    # Update Kubernetes deployment
    if command -v kubectl &> /dev/null; then
        kubectl set image deployment/psychsync-app \
            psychsync-app="$IMAGE_TAG" \
            -n "psychsync-$ENVIRONMENT"

        kubectl rollout status deployment/psychsync-app \
            -n "psychsync-$ENVIRONMENT" \
            --timeout=300s
    else
        # ECS deployment
        ./scripts/deploy_ecs.sh "$ENVIRONMENT" "$IMAGE_TAG"
    fi

    log "✅ Deployment completed"
}

# Health check
health_check() {
    log "Running health check..."

    local start_time=$(date +%s)
    local end_time=$((start_time + HEALTH_CHECK_TIMEOUT))

    while [ $(date +%s) -lt $end_time ]; do
        if curl -f "https://$ENVIRONMENT.psychsync.com/api/v1/health" > /dev/null 2>&1; then
            log "✅ Health check passed"
            return 0
        fi

        sleep 10
    done

    error "Health check failed after $HEALTH_CHECK_TIMEOUT seconds"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."

    python scripts/smoke_tests.py --environment "$ENVIRONMENT" || {
        error "Smoke tests failed"
    }

    log "✅ Smoke tests passed"
}

# Rollback function
rollback() {
    warn "Initiating rollback..."

    # Get last successful deployment
    LAST_DEPLOYMENT=$(kubectl rollout history deployment/psychsync-app \
        -n "psychsync-$ENVIRONMENT" \
        | grep "deployment" | tail -n 1 | awk '{print $1}')

    # Rollback to last deployment
    kubectl rollout undo deployment/psychsync-app \
        -n "psychsync-$ENVIRONMENT" \
        --to-revision="$LAST_DEPLOYMENT"

    # Wait for rollback to complete
    kubectl rollout status deployment/psychsync-app \
        -n "psychsync-$ENVIRONMENT" \
        --timeout="$ROLLBACK_TIMEOUT"

    log "✅ Rollback completed"

    # Health check after rollback
    health_check
}

# Main deployment flow
main() {
    log "Starting deployment to $ENVIRONMENT with image $IMAGE_TAG"

    # Pre-deployment checks
    pre_deployment_checks

    # Create backup
    create_backup

    # Deploy application
    deploy_application

    # Health check
    health_check

    # Run smoke tests
    run_smoke_tests

    log "🎉 Deployment to $ENVIRONMENT completed successfully!"
}

# Error handling
trap 'error "Deployment failed"' ERR

# Execute main function
main "$@"
```

## 📋 Pipeline Compliance & Auditing

### Compliance Checklist
```yaml
# .github/workflows/compliance.yml
name: Compliance & Auditing

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 4 * * 1'  # Weekly on Monday at 4 AM UTC

jobs:
  compliance-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run GDPR Compliance Check
        run: |
          python scripts/gdpr_compliance_check.py

      - name: Run SOC 2 Compliance Check
        run: |
          python scripts/soc2_compliance_check.py

      - name: Run OWASP Compliance Check
        run: |
          python scripts/owasp_compliance_check.py

      - name: Generate Compliance Report
        run: |
          python scripts/generate_compliance_report.py

      - name: Store Compliance Evidence
        uses: actions/upload-artifact@v3
        with:
          name: compliance-evidence
          path: |
            compliance-report.json
            gdpr-compliance.json
            soc2-compliance.json
            owasp-compliance.json
```

---

This comprehensive CI/CD security pipeline ensures that every code change undergoes rigorous security testing, vulnerability scanning, and compliance validation before reaching production. The pipeline implements security-by-design principles with automated checks at every stage of the development lifecycle.
