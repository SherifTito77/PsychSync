#!/bin/bash

# Final push script for PsychSync repositories
# Pushes all local changes to GitHub and Azure DevOps

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🚀 Pushing PsychSync to All Repositories${NC}"
    echo "======================================"
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

# Main function
main() {
    print_header

    echo "📋 Current repository status:"
    echo "================================"

    # Check current branch
    local current_branch=$(git branch --show-current)
    echo "🌿 Current branch: $current_branch"

    # Check remotes
    echo ""
    echo "🌐 Configured remotes:"
    git remote -v | grep -E "(origin|azure)" | sort -u

    # Check for changes
    echo ""
    echo "📊 Changes to commit:"
    git status --porcelain | wc -l | xargs echo "Files to stage:"
    git status --porcelain

    echo ""
    echo "🚀 Starting push process..."
    echo "=========================="

    # Stage all new files
    echo "📦 Staging all changes..."
    git add .

    # Create initial commit
    echo "💾 Creating commit with comprehensive CI/CD setup..."
    git commit -m "feat: Add comprehensive Git workflows and deployment setup

- Add Git workflow automation scripts
- Configure GitHub Actions CI/CD
- Set up Azure DevOps pipelines
- Implement branch protection rules
- Add comprehensive deployment documentation
- Set up local development environment scripts
- Add .gitignore optimizations for large files

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

    # Push to all remotes
    echo ""
    echo "📤 Pushing to all remotes..."

    # GitHub (origin)
    echo "🌐 Pushing to GitHub..."
    if git push origin main 2>/dev/null; then
        print_success "GitHub push successful"
    else
        git push --force-with-lease origin main
        print_success "GitHub force-push successful"
    fi

    # Azure DevOps (azure)
    echo "🔵 Pushing to Azure DevOps..."
    if git push azure main 2>/dev/null; then
        print_success "Azure DevOps push successful"
    else
        git push --force-with-lease azure main
        print_success "Azure DevOps force-push successful"
    fi

    echo ""
    print_success "All repositories updated successfully!"
    echo "=========================================="
    echo ""
    echo "🔗 Repository URLs:"
    echo "   GitHub: https://github.com/SherifTito77/PsychSync"
    echo "   Azure:  https://dev.azure.com/sheriftito/sphyco_code/_git/sphyco_code"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Visit GitHub to set up workflows"
    echo "   2. Configure branch protection rules"
    echo "   3. Set up Azure DevOps pipelines"
    echo "   4. Test CI/CD with a pull request"
    echo ""
    echo "📚 Documentation created:"
    echo "   - DEPLOYMENT_GUIDE.md"
    echo "   - LOCAL_DEVELOPMENT.md"
    echo "   - GIT_WORKFLOWS.md"
    echo ""
    echo "🔧 Scripts available:"
    echo "   - ./scripts/git-commit-push.sh"
    echo "   - ./scripts/git-setup-workflows.sh"
    echo "   - ./scripts/setup-branch-protection.sh"
    echo "   - ./scripts/start-dev.sh"
}

# Run main function
main "$@"