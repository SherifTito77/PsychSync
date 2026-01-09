#!/bin/bash
# Fix common syntax corruption patterns and B904 errors

set -e

# Function to fix a file
fix_file() {
    local file="$1"
    echo "Fixing: $file"

    # Create backup
    cp "$file" "$file.tmp"

    # Use Python to fix syntax corruption and add 'from e'
    python3 <<'PYTHON_SCRIPT'
import sys
import re

def fix_file_content(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix corrupted decorator lines that appear in middle of raise statements
    # Pattern: @check_rate_limit appearing between status_code and detail
    content = re.sub(
        r'(raise\s+\w+Exception\(\s*\n)\s*status_code=[^,\n]+,\n\n@check_rate_limit\([^)]+\)\s*\n\s+(detail=)',
        r'\1            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,\n            \2',
        content,
        flags=re.MULTILINE
    )

    # Fix another pattern
    content = re.sub(
        r'(raise\s+\w+Exception\(\s*)\n\n@check_rate_limit\([^)]+\)\s*\n\s+(status_code=[^,\n]+,\s*\n\s+detail=)',
        r'\1\2',
        content,
        flags=re.MULTILINE
    )

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    fix_file_content(sys.argv[1])
PYTHON_SCRIPT

    # Validate syntax
    if python3 -m py_compile "$file" 2>/dev/null; then
        # Apply ruff fix for B904
        ruff check "$file" --select B904 --fix --quiet
        echo "  ✓ Fixed"
        rm -f "$file.tmp"
        return 0
    else
        echo "  ✗ Still has syntax errors"
        mv "$file.tmp" "$file"
        return 1
    fi
}

# Main
export -f fix_file

# Get list of files with B904 errors
files=$(ruff check app/ --select B904 --output-format=json 2>/dev/null | \
    python3 -c "import sys,json; files=set([e['filename'] for e in json.load(sys.stdin)]); print('\n'.join(sorted(files)))")

total=0
fixed=0

for file in $files; do
    if [ -f "$file" ]; then
        total=$((total + 1))
        if fix_file "$file"; then
            fixed=$((fixed + 1))
        fi
    fi
done

echo ""
echo "=== Summary ==="
echo "Fixed: $fixed/$total files"
