#!/bin/bash

# GitHub Branch Protection Setup Script
# Configures branch protection rules via GitHub CLI

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🔒 Setting up GitHub Branch Protection${NC}"
    echo "===================================="
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

# Function to check if GitHub CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        echo ""
        echo "Install GitHub CLI:"
        echo "  macOS: brew install gh"
        echo "  Ubuntu: sudo apt install gh"
        echo "  Other: https://cli.github.com/manual/installation"
        echo ""
        echo "After installation, run: gh auth login"
        exit 1
    fi

    # Check if user is authenticated
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI is not authenticated"
        echo "Run: gh auth login"
        exit 1
    fi

    print_success "GitHub CLI is authenticated"
}

# Function to get repository info
get_repo_info() {
    REPO_OWNER=$(gh repo view --json owner --jq '.owner.login')
    REPO_NAME=$(gh repo view --json name --jq '.name')
    FULL_REPO="$REPO_OWNER/$REPO_NAME"

    print_success "Repository: $FULL_REPO"
}

# Function to create branch protection for main
protect_main_branch() {
    echo "🔒 Configuring protection for 'main' branch..."

    gh api \
      --method PUT \
      -H "Accept: application/vnd.github.v3+json" \
      "repos/$FULL_REPO/branches/main/protection" \
      --field required_status_checks='{"strict":true,"contexts":["Backend Tests (3.9)","Backend Tests (3.10)","Backend Tests (3.11)","Backend Tests (3.12)","Frontend Tests","Lint Code"]}' \
      --field enforce_admins=true \
      --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
      --field restrictions=null \
      --field allow_force_pushes=false \
      --field allow_deletions=false > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        print_success "Main branch protection configured"
    else
        print_warning "Main branch protection may already exist or failed"
    fi
}

# Function to create branch protection for develop
protect_develop_branch() {
    echo "🔒 Configuring protection for 'develop' branch..."

    # First check if develop branch exists
    if ! gh api "repos/$FULL_REPO/branches/develop" --jq '.name' > /dev/null 2>&1; then
        echo "📝 Creating 'develop' branch..."
        git checkout -b develop main
        git push -u origin develop
        git checkout main
    fi

    gh api \
      --method PUT \
      -H "Accept: application/vnd.github.v3+json" \
      "repos/$FULL_REPO/branches/develop/protection" \
      --field required_status_checks='{"strict":true,"contexts":["Backend Tests (3.11)","Frontend Tests","Lint Code"]}' \
      --field enforce_admins=false \
      --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":false,"require_code_owner_reviews":false}' \
      --field restrictions=null \
      --field allow_force_pushes=true \
      --field allow_deletions=false > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        print_success "Develop branch protection configured"
    else
        print_warning "Develop branch protection may already exist or failed"
    fi
}

# Function to create CODEOWNERS file
create_codeowners() {
    echo "📝 Creating CODEOWNERS file..."

    cat > .github/CODEOWNERS << 'EOF'
# CODEOWNERS File
# This file defines individuals or teams that are responsible for code review

# Global owners - will be requested for review on all PRs
* @SherifTito77

# Backend code
app/ @SherifTito77

# Frontend code
frontend/ @SherifTito77

# Infrastructure and deployment
*.yml @SherifTito77
*.yaml @SherifTito77
.github/ @SherifTito77
azure-pipelines/ @SherifTito77

# Database
app/db/ @SherifTito77
alembic/ @SherifTito77

# AI/ML code
ai/ @SherifTito77

# Documentation
*.md @SherifTito77
docs/ @SherifTito77

# Scripts
scripts/ @SherifTito77
EOF

    print_success "CODEOWNERS file created"
}

# Function to create issue and PR templates
create_templates() {
    echo "📝 Creating GitHub templates..."

    mkdir -p .github/ISSUE_TEMPLATE
    mkdir -p .github/PULL_REQUEST_TEMPLATE

    # Bug report template
    cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. macOS 13.0]
 - Browser: [e.g. chrome, safari]
 - Frontend Version: [e.g. v1.0.0]
 - Backend Version: [e.g. v1.0.0]

**Additional context**
Add any other context about the problem here.
EOF

    # Feature request template
    cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: 'enhancement'
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
EOF

    # PR template
    cat > .github/PULL_REQUEST_TEMPLATE.md << 'EOF'
## Pull Request Template

### Description
Brief description of the changes in this pull request.

### Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

### Testing
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Manual testing completed
- [ ] New tests added for new functionality

### Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules
EOF

    print_success "GitHub templates created"
}

# Function to show setup summary
show_summary() {
    echo ""
    print_success "Branch protection setup completed!"
    echo "======================================"
    echo ""
    echo "🔧 Configured:"
    echo "   ✅ Main branch protection"
    echo "   ✅ Develop branch protection"
    echo "   ✅ CODEOWNERS file"
    echo "   ✅ Issue and PR templates"
    echo ""
    echo "🌐 Repository: https://github.com/$FULL_REPO/settings/branches"
    echo ""
    echo "📝 Manual setup may be required for:"
    echo "   - Review branch protection rules in GitHub settings"
    echo "   - Add team members to CODEOWNERS"
    echo "   - Configure notification settings"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Commit and push protection settings:"
    echo "      ./scripts/git-commit-push.sh -m 'Add branch protection and templates' --all"
    echo "   2. Test branch protection by creating a PR"
    echo "   3. Configure team access and notifications"
}

# Main function
main() {
    print_header

    # Check dependencies
    check_gh_cli

    # Get repository info
    get_repo_info

    # Set up branch protection
    protect_main_branch
    protect_develop_branch

    # Create supporting files
    create_codeowners
    create_templates

    # Show summary
    show_summary
}

# Run main function
main "$@"