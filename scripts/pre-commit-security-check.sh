#!/bin/bash
###############################################################################
# Pre-commit Security Hook for PsychSync
# Scans for hardcoded secrets, credentials, and sensitive data
###############################################################################

set -e

echo "🔍 Running security pre-commit checks..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Patterns to detect (case insensitive)
PATTERNS=(
    "password\s*=\s*['\"][^'\"]{8,}"           # Password assignments
    "api_key\s*=\s*['\"][^'\"]{20}"           # API keys
    "secret_key\s*=\s*['\"][^'\"]{20}"        # Secret keys
    "access_token\s*=\s*['\"][^'\"]{20}"      # Access tokens
    "private_key\s*=\s*['\"][^'\"]{20}"       # Private keys
    "auth_token\s*=\s*['\"][^'\"]{20}"        # Auth tokens
    "sk_live_[a-zA-Z0-9]{32,}"                # Stripe live keys
    "sk_test_[a-zA-Z0-9]{32,}"                # Stripe test keys
    "AKIA[0-9A-Z]{16}"                         # AWS access keys
    "AIza[0-9A-Za-z\\-_]{35}"                 # Google API keys
    "postgres?:\/\/.*:.*@"                    # PostgreSQL connection strings
    "mysql:\/\/.*:.*@"                        # MySQL connection strings
    "mongodb:\/\/.*:.*@"                      # MongoDB connection strings
    "ghp_[a-zA-Z0-9]{36}"                     # GitHub personal access tokens
    "xoxb-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}"  # Slack bot tokens
    "AKIA[0-9A-Z]{16}"                        # AWS access key ID
    "[0-9]{12}"                                # Possible credit card numbers
)

# File extensions to scan
EXTENSIONS="\.(ts|tsx|js|jsx|py|env|json|yaml|yml|toml|ini|conf)$"

# Files to exclude
EXCLUDES="(node_modules/|.venv/|venv/|__pycache__/|\.git/|dist/|build/|coverage/|\.(min\.|bundle\.)js)"

FOUND_ISSUES=0

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E "$EXTENSIONS" || true)

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No relevant files staged for commit"
    exit 0
fi

echo "📁 Scanning $(echo "$STAGED_FILES" | wc -l | tr -d ' ') staged files..."

# Scan each file
for FILE in $STAGED_FILES; do
    # Skip excluded directories
    if echo "$FILE" | grep -qE "$EXCLUDES"; then
        continue
    fi

    # Check each pattern
    for PATTERN in "${PATTERNS[@]}"; do
        if git diff --cached "$FILE" | grep -iE "$PATTERN" > /dev/null; then
            echo -e "${RED}❌ POTENTIAL SECRET FOUND in $FILE${NC}"
            echo -e "${YELLOW}Pattern matched: $PATTERN${NC}"
            echo -e "${YELLOW}Please remove the secret and use environment variables${NC}"
            FOUND_ISSUES=1
        fi
    done
done

# Check for .env files staged (should not commit these)
if echo "$STAGED_FILES" | grep -qE "\.env$"; then
    echo -e "${RED}❌ .env file should not be committed!${NC}"
    echo -e "${YELLOW}Add .env to .gitignore and use .env.example instead${NC}"
    FOUND_ISSUES=1
fi

if [ $FOUND_ISSUES -eq 1 ]; then
    echo ""
    echo -e "${RED}🚨 Security check failed! Please fix the issues above before committing.${NC}"
    echo -e "${YELLOW}To bypass this check (not recommended): git commit --no-verify${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Security checks passed!${NC}"
exit 0
