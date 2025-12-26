#!/bin/bash
# Dependency Allow-List Enforcement Script
# Blocks PRs that add dependencies not in the allow-list

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     PsychSync Dependency Allow-List Checker                   ║"
echo "║     Enforces dependency governance policies                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

VIOLATIONS_FOUND=0

# Check if we're in a PR context
if [ -z "$PR_NUMBER" ]; then
    echo -e "${YELLOW}⚠${NC}  Not in PR context, skipping allow-list check"
    exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Python Dependencies Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if requirements.txt changed
if git diff --name-only origin/main...HEAD | grep -q "requirements.txt"; then
    echo "Checking new Python dependencies..."
    echo ""

    # Get list of all packages in current requirements.txt
    if [ -f "requirements.txt" ]; then
        # Extract package names (before == or >)
        CURRENT_PACKAGES=$(grep -E '^[a-zA-Z0-9_-]+' requirements.txt | sed 's/[\[=<].*//' | sort)
        
        # Extract allowed packages from allow-list
        ALLOWED_PACKAGES=$(grep -E '^[a-zA-Z0-9_-]+' allowed-dependencies.txt | sed 's/[\[=<].*//' | sort)
        
        # Find packages in current but not in allowed
        NEW_PACKAGES=$(comm -23 <(echo "$CURRENT_PACKAGES") <(echo "$ALLOWED_PACKAGES") || true)
        
        if [ -n "$NEW_PACKAGES" ]; then
            echo -e "${RED}✗ BLOCKING: New dependencies not in allow-list:${NC}"
            echo ""
            echo "$NEW_PACKAGES" | while read pkg; do
                echo "  • $pkg"
            done
            echo ""
            echo "To add these packages:"
            echo "  1. Add them to allowed-dependencies.txt"
            echo "  2. Document the security rationale"
            echo "  3. Get security team approval"
            echo ""
            VIOLATIONS_FOUND=1
        else
            echo -e "${GREEN}✓${NC}  All Python dependencies are in the allow-list"
        fi
    fi
else
    echo -e "${GREEN}✓${NC}  No changes to requirements.txt"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "JavaScript/TypeScript Dependencies Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if package.json changed
if git diff --name-only origin/main...HEAD | grep -q "frontend/package.json"; then
    echo "Checking new JavaScript dependencies..."
    echo ""

    if [ -f "frontend/package.json" ]; then
        cd frontend
        
        # Get list of dependencies from package.json
        CURRENT_DEPS=$(node -e "
            const pkg = require('./package.json');
            const allDeps = {
                ...pkg.dependencies || {},
                ...pkg.devDependencies || {}
            };
            console.log(Object.keys(allDeps).join('\n'));
        " | sort)
        
        # Extract allowed packages from allow-list JSON
        ALLOWED_DEPS=$(node -e "
            const allowlist = require('./allowed-dependencies.json');
            const allowed = new Set();
            
            // Recursively extract all package names from allowlist
            function extractPackages(obj) {
                if (typeof obj === 'object' && obj !== null) {
                    Object.keys(obj).forEach(key => {
                        if (key.includes('@') || key === 'react' || key === 'axios' || key === 'vitest') {
                            // These are package names
                            if (!key.startsWith('min') && !key.startsWith('max') && 
                                !key.startsWith('reason') && !key.startsWith('security')) {
                                allowed.add(key);
                            }
                        }
                        extractPackages(obj[key]);
                    });
                }
            }
            
            extractPackages(allowlist.allowedDependencies || {});
            console.log(Array.from(allowed).join('\n'));
        " | sort)
        
        # Find packages in current but not in allowed
        NEW_DEPS=$(comm -23 <(echo "$CURRENT_DEPS") <(echo "$ALLOWED_DEPS") || true)
        
        if [ -n "$NEW_DEPS" ]; then
            echo -e "${RED}✗ BLOCKING: New dependencies not in allow-list:${NC}"
            echo ""
            echo "$NEW_DEPS" | while read dep; do
                echo "  • $dep"
            done
            echo ""
            echo "To add these packages:"
            echo "  1. Add them to frontend/allowed-dependencies.json"
            echo "  2. Document the security rationale"
            echo "  3. Get security team approval"
            echo ""
            VIOLATIONS_FOUND=1
        else
            echo -e "${GREEN}✓${NC}  All JavaScript dependencies are in the allow-list"
        fi
        
        cd ..
    fi
else
    echo -e "${GREEN}✓${NC}  No changes to frontend/package.json"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$VIOLATIONS_FOUND" -gt 0 ]; then
    echo -e "${RED}✗ ALLOW-LIST CHECK FAILED${NC}"
    echo ""
    echo "PR contains dependencies not in the allow-list."
    echo "This is a BLOCKING issue - the PR cannot be merged."
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ ALLOW-LIST CHECK PASSED${NC}"
    echo ""
    echo "All dependencies are approved and documented."
    echo ""
    exit 0
fi
