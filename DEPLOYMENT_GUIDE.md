# PsychSync Deployment Guide

This guide covers deploying PsychSync to GitHub and Azure DevOps, including CI/CD setup and best practices.

## 🚀 Quick Start

### 1. Repository Setup
```bash
# Configure both remotes
git remote set-url origin https://github.com/SherifTito77/PsychSync.git
git remote add azure https://dev.azure.com/sheriftito/sphyco_code/_git/sphyco_code

# Initial commit and push
./scripts/git-commit-push.sh -m "Initial setup with CI/CD workflows" --all
```

### 2. CI/CD Workflows
```bash
# Set up all workflows
./scripts/git-setup-workflows.sh

# Configure branch protection
./scripts/setup-branch-protection.sh
```

## 📁 Repository Structure

```
PsychSync/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # GitHub Actions CI/CD
│   │   └── docker.yml          # Docker build and push
│   ├── CODEOWNERS              # Code review assignments
│   └── PULL_REQUEST_TEMPLATE.md
├── azure-pipelines/
│   └── psychsync-ci.yml        # Azure DevOps pipeline
├── scripts/
│   ├── git-commit-push.sh      # Multi-remote Git operations
│   ├── git-setup-workflows.sh  # CI/CD setup script
│   └── setup-branch-protection.sh # GitHub protection rules
└── app/                         # FastAPI application
    └── frontend/                # React application
```

## 🔄 Git Workflow Scripts

### git-commit-push.sh
Automates commits and pushes to both GitHub and Azure DevOps:

```bash
# Interactive commit and push
./scripts/git-commit-push.sh

# With message
./scripts/git-commit-push.sh -m "Add user authentication"

# Stage all changes
./scripts/git-commit-push.sh -m "Update dependencies" --all

# Sync remotes only
./scripts/git-commit-push.sh --sync

# Push to specific branch
./scripts/git-commit-push.sh -b develop -m "Feature implementation"
```

### git-setup-workflows.sh
Creates comprehensive CI/CD automation:

```bash
# Set up all workflows
./scripts/git-setup-workflows.sh
```

Creates:
- GitHub Actions workflows
- Azure DevOps pipelines
- Workflow documentation
- Remote tracking setup

### setup-branch-protection.sh
Configures GitHub branch protection rules:

```bash
# Set up branch protection (requires GitHub CLI)
./scripts/setup-branch-protection.sh
```

## 🌐 Repository URLs

- **GitHub**: https://github.com/SherifTito77/PsychSync
- **Azure DevOps**: https://dev.azure.com/sheriftito/sphyco_code/_git/sphyco_code

## 🔄 Continuous Integration

### GitHub Actions

#### CI Pipeline (`.github/workflows/ci.yml`)
- **Triggers**: Push/PR to `main` and `develop` branches
- **Python Testing**: Version 3.9, 3.10, 3.11, 3.12
- **Frontend Testing**: Node.js 18 with npm
- **Code Quality**: Flake8, Black, Isort, MyPy
- **Coverage**: Reports to Codecov

#### Docker Pipeline (`.github/workflows/docker.yml`)
- **Triggers**: Tags and main branch pushes
- **Registry**: GitHub Container Registry (`ghcr.io`)
- **Multi-platform**: Linux/amd64 and Linux/arm64
- **Caching**: GitHub Actions cache layers

### Azure DevOps Pipeline

#### CI Pipeline (`azure-pipelines/psychsync-ci.yml`)
- **Stages**: Validate → Build
- **Backend Tests**: Python 3.11 with pytest
- **Frontend Tests**: Node.js with npm
- **Docker Build**: Multi-stage builds
- **Publish**: Test results and code coverage

## 🔒 Branch Protection

### Main Branch Protection
- **Required Status Checks**: All CI tests must pass
- **Required Reviews**: 1 approval required
- **Code Owner Reviews**: Required
- **Admin Enforcement**: Admins must follow rules
- **Force Pushes**: Disabled
- **Deletions**: Disabled

### Develop Branch Protection
- **Required Status Checks**: Core tests must pass
- **Required Reviews**: 1 approval required
- **Force Pushes**: Enabled (for rebasing)
- **Admin Enforcement**: Not required

### Setup Commands
```bash
# Manual setup via GitHub UI
# Repository Settings → Branches → Add rule

# Or automated setup via script
./scripts/setup-branch-protection.sh
```

## 🚢 Deployment Strategy

### Branch Strategy
1. **main**: Production-ready code
2. **develop**: Integration branch
3. **feature/***: Feature branches
4. **hotfix/***: Critical fixes

### Release Process
1. **Feature Development**
   ```bash
   git checkout -b feature/new-assessment
   # Make changes
   ./scripts/git-commit-push.sh -m "Add assessment feature"
   # Create PR to develop
   ```

2. **Integration**
   ```bash
   # Merge to develop after review
   git checkout develop
   git merge feature/new-assessment
   ./scripts/git-commit-push.sh -m "Integrate assessment feature"
   ```

3. **Release**
   ```bash
   # Tag and deploy from main
   git checkout main
   git merge develop
   git tag v1.1.0
   ./scripts/git-commit-push.sh --all
   ```

## 🐳 Docker Deployment

### Local Development
```bash
# Using existing Docker setup
docker-compose up --build

# Or new localhost setup
./scripts/start-full-dev.sh
```

### Production Docker
```bash
# Build production image
docker build -f Dockerfile.prod -t psychsync:latest .

# Run with environment
docker run -d \
  --name psychsync \
  -p 8000:8000 \
  --env-file .env.prod \
  psychsync:latest
```

### Registry Push
Images are automatically pushed to:
- **GitHub**: `ghcr.io/SherifTito77/psychsync`
- **Docker Hub**: `sheriftito77/psychsync` (if configured)

## 📊 Monitoring and Health Checks

### Application Health
- **Health Endpoint**: `GET /health`
- **Metrics**: `GET /metrics` (if enabled)
- **Logs**: Structured logging with levels

### CI/CD Monitoring
- **GitHub Actions**: Actions tab in repository
- **Azure DevOps**: Pipelines section
- **Coverage**: Codecov and test reports

## 🔧 Configuration

### Environment Variables
```bash
# Development
cp .env.localhost .env

# Production
cp .env.prod .env
```

### Secrets Management
- **GitHub**: Repository secrets
- **Azure DevOps**: Variable groups
- **Local**: `.env` files (never committed)

## 🛠️ Troubleshooting

### Git Issues
```bash
# Sync issues between remotes
./scripts/git-commit-push.sh --sync

# Branch conflicts
git pull origin main
git merge --no-ff origin/main

# Push failures
git push --force-with-lease origin main
```

### CI/CD Failures
1. **Check Logs**: GitHub Actions or Azure Pipelines
2. **Local Testing**: Run tests locally
3. **Dependency Issues**: Update requirements
4. **Configuration**: Verify environment variables

### Docker Issues
```bash
# Clean build
docker system prune -a
docker build --no-cache -f Dockerfile.prod .

# Debug container
docker run -it --entrypoint /bin/bash psychsync:latest
```

## 📚 Documentation

- **Local Development**: `LOCAL_DEVELOPMENT.md`
- **API Documentation**: http://localhost:8000/docs
- **Git Workflows**: `GIT_WORKFLOWS.md`
- **Project Overview**: `README.md`

## 🔗 External Links

- **GitHub Repository**: https://github.com/SherifTito77/PsychSync
- **Azure DevOps**: https://dev.azure.com/sheriftito/sphyco_code
- **Issues**: https://github.com/SherifTito77/PsychSync/issues
- **Discussions**: https://github.com/SherifTito77/PsychSync/discussions

## 👥 Team Collaboration

### Pull Request Process
1. Create feature branch from `develop`
2. Make changes and commit
3. Create PR to `develop` branch
4. Address review comments
5. Merge after approval

### Code Review Guidelines
- Review must pass CI checks
- Code owners automatically requested
- Follow style guidelines
- Add tests for new features

### Release Management
- Semantic versioning (v1.0.0)
- Automated releases via GitHub Actions
- Changelog maintenance
- Tagged releases trigger deployment

## 🚀 Next Steps

1. **Set up workflows**:
   ```bash
   ./scripts/git-setup-workflows.sh
   ./scripts/setup-branch-protection.sh
   ```

2. **Initial commit**:
   ```bash
   ./scripts/git-commit-push.sh -m "Add CI/CD workflows and branch protection" --all
   ```

3. **Test setup**:
   - Create test pull request
   - Verify CI passes
   - Check branch protection

4. **Configure team**:
   - Add team members to repositories
   - Set up notification preferences
   - Configure project boards

5. **Deploy first release**:
   - Merge to main
   - Tag release
   - Verify deployment