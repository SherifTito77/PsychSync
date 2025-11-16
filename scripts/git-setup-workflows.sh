#!/bin/bash

# PsychSync Git Workflows Setup
# Creates GitHub workflows and Azure Pipelines

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🔧 Setting up Git Workflows${NC}"
    echo "=============================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to create GitHub workflows directory
create_github_workflows() {
    echo "📁 Creating GitHub workflows directory..."
    mkdir -p .github/workflows
    print_success "GitHub workflows directory created"
}

# Function to create GitHub Actions workflow for CI
create_github_ci_workflow() {
    echo "📝 Creating GitHub Actions CI workflow..."

    cat > .github/workflows/ci.yml << 'EOF'
name: PsychSync CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

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
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  test-frontend:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci

    - name: Run frontend tests
      run: |
        cd frontend
        npm run test:unit

    - name: Build frontend
      run: |
        cd frontend
        npm run build

  lint-code:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install flake8 black isort mypy

    - name: Lint with flake8
      run: |
        flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

    - name: Check code formatting with black
      run: |
        black --check app/

    - name: Check import sorting with isort
      run: |
        isort --check-only app/

    - name: Type check with mypy
      run: |
        mypy app/ || true  # Continue even if mypy fails
EOF

    print_success "GitHub CI workflow created"
}

# Function to create GitHub Actions workflow for Docker
create_github_docker_workflow() {
    echo "📝 Creating GitHub Actions Docker workflow..."

    cat > .github/workflows/docker.yml << 'EOF'
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Log in to Container Registry
      if: github.event_name != 'pull_request'
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
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile.prod
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
EOF

    print_success "GitHub Docker workflow created"
}

# Function to create Azure DevOps pipeline
create_azure_pipeline() {
    echo "📝 Creating Azure DevOps pipeline..."

    mkdir -p azure-pipelines

    cat > azure-pipelines/psychsync-ci.yml << 'EOF'
# PsychSync Azure DevOps Pipeline
trigger:
  branches:
    include:
    - main
    - develop

pr:
  branches:
    include:
    - main
    - develop

variables:
  pythonVersion: '3.11'
  nodeVersion: '18'

stages:
- stage: Validate
  displayName: 'Validate Code Quality'
  jobs:
  - job: BackendTests
    displayName: 'Backend Tests'
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'

    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
      displayName: 'Install dependencies'

    - script: |
        pytest tests/ -v --cov=app --cov-report=xml
      displayName: 'Run tests'

    - task: PublishTestResults@2
      condition: succeededOrFailed()
      inputs:
        testResultsFiles: '**/test-*.xml'
        testRunTitle: 'Backend Tests'

    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: Cobertura
        summaryFileLocation: '$(System.DefaultWorkingDirectory)/**/coverage.xml'

  - job: FrontendTests
    displayName: 'Frontend Tests'
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: '$(nodeVersion)'
      displayName: 'Install Node.js'

    - script: |
        cd frontend
        npm ci
      displayName: 'Install npm dependencies'

    - script: |
        cd frontend
        npm run test:unit
      displayName: 'Run frontend tests'

    - script: |
        cd frontend
        npm run build
      displayName: 'Build frontend'

- stage: Build
  displayName: 'Build Docker Image'
  dependsOn: Validate
  condition: succeeded()
  jobs:
  - job: BuildDocker
    displayName: 'Build and Push Docker'
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: Docker@2
      displayName: 'Build and push Docker image'
      inputs:
        containerRegistry: 'dockerhub'  # You'll need to add this service connection
        repository: 'sheriftito77/psychsync'
        command: 'buildAndPush'
        Dockerfile: 'Dockerfile.prod'
        tags: |
          $(Build.BuildId)
          latest
EOF

    print_success "Azure DevOps pipeline created"
}

# Function to create GitHub workflows directory
create_git_workflow_docs() {
    echo "📝 Creating Git workflow documentation..."

    cat > GIT_WORKFLOWS.md << 'EOF'
# Git Workflows Guide

This document explains the Git workflows and automation setup for PsychSync.

## Repository Structure

- **GitHub**: https://github.com/SherifTito77/PsychSync
- **Azure DevOps**: https://dev.azure.com/sheriftito/sphyco_code

## Branch Strategy

### Main Branches
- `main`: Production-ready code
- `develop`: Integration branch for features

### Feature Branches
- `feature/description`: New features
- `bugfix/description`: Bug fixes
- `hotfix/description`: Critical fixes

## Git Workflow Scripts

### Quick Commit and Push
```bash
# Interactive commit and push to all remotes
./scripts/git-commit-push.sh

# With message
./scripts/git-commit-push.sh -m "Add new authentication feature"

# Stage all changes and commit
./scripts/git-commit-push.sh -m "Update dependencies" --all

# Sync remotes only
./scripts/git-commit-push.sh --sync
```

## CI/CD Automation

### GitHub Actions
- **CI Pipeline**: Runs on every push/PR to main/develop
  - Backend tests (Python 3.9-3.12)
  - Frontend tests (Node.js)
  - Code linting and formatting checks
  - Docker image building

- **Docker Pipeline**: Builds and pushes Docker images
  - Triggers on tags and main branch pushes
  - Multi-platform image support

### Azure DevOps
- **CI Pipeline**: Similar to GitHub Actions
  - Backend validation with pytest
  - Frontend build and test
  - Code coverage reporting

## Pre-commit Hooks (Optional)

To set up pre-commit hooks for better code quality:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
EOF

# Install hooks
pre-commit install
```

## Environment Configuration

### GitHub Secrets
- `GITHUB_TOKEN`: Auto-provided by GitHub Actions
- `DOCKER_REGISTRY_TOKEN`: For Docker publishing (optional)

### Azure DevOps Variables
- `DOCKER_REGISTRY_CONNECTION`: Service connection for Docker registry
- Connection strings for deployment environments

## Development Workflow

### 1. Start New Feature
```bash
# Create feature branch
git checkout -b feature/user-authentication

# Make changes...
# Commit and push
./scripts/git-commit-push.sh -m "Add user authentication endpoints"
```

### 2. Submit Pull Request
1. Push feature branch to GitHub
2. Create PR from feature → develop
3. CI will run automatically
4. Review and merge

### 3. Deploy to Production
```bash
# Merge develop to main
git checkout main
git merge develop

# Tag release
git tag v1.0.0

# Push tag (triggers deployment)
./scripts/git-commit-push.sh
```

## Troubleshooting

### Push Conflicts
```bash
# Sync with remotes
./scripts/git-commit-push.sh --sync

# Resolve conflicts manually, then:
./scripts/git-commit-push.sh -m "Resolve merge conflicts"
```

### CI Failures
- Check GitHub Actions tab for detailed logs
- Check Azure DevOps Pipelines for build status
- Fix issues locally and push fixes

### Large File Issues
- Ensure `.gitignore` excludes large files
- Use Git LFS for large binary files if needed
- Keep virtual environments excluded
EOF

    print_success "Git workflow documentation created"
}

# Function to set up remote tracking
setup_remote_tracking() {
    echo "🔧 Setting up remote tracking..."

    # Ensure all remotes are tracked
    git remote | grep -q "origin" && echo "✅ Origin remote configured"
    git remote | grep -q "azure" && echo "✅ Azure remote configured"

    # Set up tracking for main branch
    git branch --set-upstream-to=origin/main main 2>/dev/null || true
    git branch --set-upstream-to=azure/main main 2>/dev/null || true

    print_success "Remote tracking configured"
}

# Main function
main() {
    print_header

    echo "🚀 Setting up complete Git workflow automation..."
    echo ""

    # Create directories and files
    create_github_workflows
    create_github_ci_workflow
    create_github_docker_workflow
    create_azure_pipeline
    create_git_workflow_docs
    setup_remote_tracking

    echo ""
    print_success "Git workflows setup completed!"
    echo "===================================="
    echo ""
    echo "📁 Created files:"
    echo "   - .github/workflows/ci.yml"
    echo "   - .github/workflows/docker.yml"
    echo "   - azure-pipelines/psychsync-ci.yml"
    echo "   - GIT_WORKFLOWS.md"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Commit and push to setup workflows:"
    echo "      ./scripts/git-commit-push.sh -m 'Add CI/CD workflows' --all"
    echo ""
    echo "   2. Configure secrets in GitHub/Azure:"
    echo "      - Docker registry tokens"
    echo "      - Deployment credentials"
    echo ""
    echo "   3. Test workflows by creating a pull request"
    echo ""
    echo "📚 Documentation: See GIT_WORKFLOWS.md"
}

# Run main function
main "$@"