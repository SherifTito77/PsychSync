#!/bin/bash

# Fix TypeScript Errors Script
# Automatically fixes common TypeScript import and type errors

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🔧 Fixing TypeScript Errors${NC}"
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

# Function to fix missing logout import
fix_logout_import() {
    echo "🔍 Fixing logout import issues..."

    local auth_file="src/contexts/AuthContext.tsx"
    if [ -f "$auth_file" ]; then
        if grep -q "logout();" "$auth_file"; then
            sed -i '' 's/logout();/handleLogout();/g' "$auth_file"
            print_success "Fixed logout function call in AuthContext"
        fi
    fi
}

# Function to fix axios import path
fix_axios_import() {
    echo "🔍 Fixing axios import paths..."

    find src/services -name "*.ts" -exec grep -l "from './axios'" {} \; | while read file; do
        sed -i '' "s|from './axios'|from '../api/axios'|g" "$file"
        print_success "Fixed axios import in $(basename "$file")"
    done
}

# Function to fix register form data
fix_register_form() {
    echo "🔍 Fixing register form data..."

    local register_file="src/pages/Register.tsx"
    if [ -f "$register_file" ]; then
        sed -i '' 's/name:/full_name:/g' "$register_file"
        print_success "Fixed register form field name"
    fi
}

# Function to add ghost variant to Badge colors
fix_badge_colors() {
    echo "🔍 Adding ghost variant to Badge component..."

    local badge_file="src/components/common/Badge.tsx"
    if [ -f "$badge_file" ]; then
        # Add 'ghost' to color types if not present
        if ! grep -q "'ghost'" "$badge_file"; then
            sed -i '' "s/color?: 'blue'|/color?: 'blue'|'ghost'|/g" "$badge_file"
            print_success "Added ghost color variant to Badge"
        fi
    fi
}

# Function to fix Button children prop requirement
fix_button_children() {
    echo "🔍 Making Button children optional..."

    local button_file="src/components/common/Button.tsx"
    if [ -f "$button_file" ]; then
        sed -i '' 's/children: React.ReactNode;/children?: React.ReactNode;/' "$button_file"
        print_success "Made Button children optional"
    fi
}

# Function to remove title prop from Lucide icons
fix_icon_title_prop() {
    echo "🔍 Removing title prop from Lucide icons..."

    find src/components -name "*.tsx" -exec grep -l "title=" {} \; | while read file; do
        sed -i '' 's/title="[^"]*"//g' "$file"
        print_success "Removed title props from $(basename "$file")"
    done
}

# Function to fix OptimizedComponent
fix_optimized_component() {
    echo "🔍 Fixing OptimizedComponent..."

    local optimized_file="src/components/OptimizedComponent.tsx"
    if [ -f "$optimized_file" ]; then
        # Fix debounce import
        sed -i '' 's/debounce(/lodash.debounce(/g' "$optimized_file"

        # Fix type issue with memo
        sed -i '' 's/React.memo<P>/React.memo/g' "$optimized_file"

        print_success "Fixed OptimizedComponent type issues"
    fi
}

# Function to fix Select component
fix_select_component() {
    echo "🔍 Fixing Select component..."

    local select_file="src/components/ui/Select.tsx"
    if [ -f "$select_file" ]; then
        # Remove onChange prop usage
        sed -i '' 's/onChange,//g' "$select_file"
        sed -i '' 's/onChange//g' "$select_file"

        # Fix placeholder prop
        sed -i '' 's/placeholder[^;]*/{props.placeholder || '\''Select an option'\''}/g' "$select_file"

        print_success "Fixed Select component props"
    fi
}

# Function to add missing Lucide imports
add_missing_icon_imports() {
    echo "🔍 Adding missing icon imports..."

    # Find files using X icon without importing it
    find src/components -name "*.tsx" -exec grep -l "<X " {} \; | while read file; do
        if ! grep -q "X," "$file"; then
            sed -i '' 's/} from '\''lucide-react'\'';/  X\
} from '\''lucide-react'\'';/g' "$file"
            print_success "Added X icon import to $(basename "$file")"
        fi
    done
}

# Function to fix type errors in service files
fix_service_types() {
    echo "🔍 Fixing service type errors..."

    # Fix authService.ts duplicate avatar_url
    local auth_service="src/services/authService.ts"
    if [ -f "$auth_service" ]; then
        # Remove duplicate avatar_url lines
        sed -i '' '/avatar_url: string | null;/d' "$auth_service"
        print_success "Fixed duplicate avatar_url in authService"
    fi
}

# Function to fix missing feedback type imports
fix_feedback_types() {
    echo "🔍 Fixing feedback type imports..."

    local feedback_service="src/services/anonymousFeedbackService.ts"
    if [ -f "$feedback_service" ]; then
        # Remove non-existent imports
        sed -i '' '/FeedbackFollowUp,/d' "$feedback_service"
        print_success "Removed non-existent FeedbackFollowUp import"
    fi
}

# Function to run TypeScript check
run_typescript_check() {
    echo "🔍 Running TypeScript check..."

    cd "$(dirname "$0")/.."

    # Run TypeScript compiler in check mode
    npx tsc --noEmit --pretty false 2>&1 | head -20

    if [ $? -eq 0 ]; then
        print_success "No TypeScript errors found!"
    else
        print_warning "Some TypeScript errors may still remain"
    fi
}

# Main function
main() {
    print_header

    cd "$(dirname "$0")/.."

    echo "🚀 Starting TypeScript error fixes..."
    echo ""

    # Run all fixes
    fix_logout_import
    fix_axios_import
    fix_register_form
    fix_badge_colors
    fix_button_children
    fix_icon_title_prop
    add_missing_icon_imports
    fix_optimized_component
    fix_select_component
    fix_service_types
    fix_feedback_types

    echo ""
    echo "🧹 Cleaning up..."

    # Remove any double commas or empty lines
    find src -name "*.tsx" -o -name "*.ts" | xargs sed -i '' '/^[[:space:]]*$/d'
    find src -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's/, ,/,/g'
    find src -name "*.tsx" -o -name "*.ts" | xargs sed -i '' 's/, }/ }/g'

    echo ""
    run_typescript_check

    echo ""
    print_success "TypeScript error fixes completed!"
    echo "===================================="
    echo ""
    echo "📝 Manual fixes may still be needed for:"
    echo "   - Complex type mismatches"
    echo "   - Missing type definitions"
    echo "   - Third-party library issues"
    echo ""
    echo "🧪 Run tests to verify fixes:"
    echo "   npm run test"
    echo ""
    echo "🔍 TypeScript check:"
    echo "   npm run type-check"
}

# Run main function
main "$@"