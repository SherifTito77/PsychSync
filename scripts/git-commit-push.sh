#!/bin/bash

# PsychSync Git Commit and Push Script
# Manages commits to both GitHub and Azure DevOps

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🚀 PsychSync Git Push Manager${NC}"
    echo "================================"
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

# Function to check if working directory is clean
check_git_status() {
    if [ -n "$(git status --porcelain)" ]; then
        return 1  # Working directory is not clean
    else
        return 0  # Working directory is clean
    fi
}

# Function to show staged changes
show_staged_changes() {
    echo "📋 Staged changes:"
    git status --porcelain
    echo ""
}

# Function to get commit message
get_commit_message() {
    local message=""

    if [ -n "$1" ]; then
        message="$1"
    else
        echo "💬 Enter commit message (or press Ctrl+C to cancel):"
        read -r message
    fi

    if [ -z "$message" ]; then
        print_error "Commit message cannot be empty"
        exit 1
    fi

    echo "$message"
}

# Function to add changes to staging
stage_changes() {
    local add_all=${1:-false}

    if [ "$add_all" = true ]; then
        echo "📦 Adding all changes..."
        git add .
    else
        echo "📦 Adding changes interactively..."
        git add -A
    fi

    show_staged_changes
}

# Function to create commit
create_commit() {
    local message="$1"

    echo "💾 Creating commit..."
    git commit -m "$message"

    if [ $? -eq 0 ]; then
        print_success "Commit created successfully"
    else
        print_error "Failed to create commit"
        exit 1
    fi
}

# Function to push to remote
push_to_remote() {
    local remote="$1"
    local branch="$2"

    echo "📤 Pushing to $remote/$branch..."

    if git push "$remote" "$branch" 2>/dev/null; then
        print_success "Pushed to $remote successfully"
        return 0
    else
        print_warning "Push to $remote failed. Trying with --force-with-lease..."

        if git push --force-with-lease "$remote" "$branch" 2>/dev/null; then
            print_success "Force-pushed to $remote successfully"
            return 0
        else
            print_error "Failed to push to $remote"
            return 1
        fi
    fi
}

# Function to push to both remotes
push_to_all_remotes() {
    local branch="$1"
    local success_count=0
    local total_remotes=0

    echo ""
    echo "🌐 Pushing to all remotes..."

    # Get list of remotes (excluding origin, azureh duplicates)
    local remotes=($(git remote | grep -E '^(origin|azure)$' | sort -u))

    for remote in "${remotes[@]}"; do
        ((total_remotes++))
        if push_to_remote "$remote" "$branch"; then
            ((success_count++))
        fi
    done

    echo ""
    echo "📊 Push Summary: $success_count/$total_remotes remotes successful"

    if [ $success_count -eq $total_remotes ]; then
        print_success "All remotes updated successfully"
        return 0
    else
        print_warning "Some remotes failed to update"
        return 1
    fi
}

# Function to sync remotes
sync_remotes() {
    local branch="$1"

    echo "🔄 Syncing remotes..."

    # Fetch from all remotes
    for remote in $(git remote | sort -u); do
        echo "📥 Fetching from $remote..."
        git fetch "$remote" || print_warning "Failed to fetch from $remote"
    done

    echo ""
    print_success "All remotes synced"
}

# Main function
main() {
    local commit_message=""
    local add_all=false
    local sync_only=false
    local branch="main"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--message)
                commit_message="$2"
                shift 2
                ;;
            -a|--all)
                add_all=true
                shift
                ;;
            -s|--sync)
                sync_only=true
                shift
                ;;
            -b|--branch)
                branch="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  -m, --message MSG    Commit message"
                echo "  -a, --all           Stage all changes"
                echo "  -s, --sync          Sync remotes only"
                echo "  -b, --branch BRANCH Branch to push to (default: main)"
                echo "  -h, --help          Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0 -m 'Add new feature'"
                echo "  $0 -m 'Fix bug' --all"
                echo "  $0 --sync"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    print_header

    # Check if we're on the correct branch
    local current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$branch" ]; then
        echo "🔄 Switching to branch '$branch'..."
        git checkout "$branch" || {
            print_error "Failed to switch to branch '$branch'"
            exit 1
        }
    fi

    # Sync remotes first
    sync_remotes "$branch"

    # If sync only, we're done
    if [ "$sync_only" = true ]; then
        print_success "Sync completed"
        exit 0
    fi

    # Check if there are changes to commit
    if check_git_status; then
        print_warning "No changes to commit"
        echo ""
        echo "💡 Use '--sync' to sync remotes only"
        exit 0
    fi

    # Stage changes
    stage_changes "$add_all"

    # Get commit message
    commit_message=$(get_commit_message "$commit_message")

    # Create commit
    create_commit "$commit_message"

    # Push to all remotes
    push_to_all_remotes "$branch"

    echo ""
    print_success "Git operations completed successfully!"
    echo ""
    echo "🔗 Repository URLs:"
    echo "   GitHub: $(git remote get-url origin)"
    echo "   Azure:  $(git remote get-url azure 2>/dev/null || echo 'Not configured')"
    echo ""
    echo "📊 Current branch: $(git branch --show-current)"
    echo "📊 Commit hash: $(git rev-parse --short HEAD)"
}

# Run main function
main "$@"