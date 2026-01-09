#!/bin/bash

# Bundle Size Monitoring Script for PsychSync Frontend
# This script tracks bundle size changes and alerts if thresholds are exceeded

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BUILD_DIR="dist"
MAX_BUNDLE_SIZE_KB=500  # Maximum acceptable bundle size in KB
MAX_CHUNK_SIZE_KB=200   # Maximum acceptable chunk size in KB
SIZE_INCREASE_THRESHOLD=0.1  # Alert if size increases by more than 10%

# File to store previous bundle sizes
SIZES_FILE=".bundle-sizes.json"

echo "🔍 Analyzing bundle sizes..."

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
  echo -e "${RED}❌ Build directory not found. Run 'npm run build' first.${NC}"
  exit 1
fi

# Function to format bytes
format_bytes() {
  local bytes=$1
  if [ $bytes -lt 1024 ]; then
    echo "${bytes}B"
  elif [ $bytes -lt 1048576 ]; then
    echo "$((bytes / 1024))KB"
  else
    echo "$((bytes / 1048576))MB"
  fi
}

# Function to get file size
get_file_size() {
  local file=$1
  if [ -f "$file" ]; then
    stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0"
  else
    echo "0"
  fi
}

# Find all JS and CSS files
JS_FILES=$(find "$BUILD_DIR" -name "*.js" -type f 2>/dev/null || echo "")
CSS_FILES=$(find "$BUILD_DIR" -name "*.css" -type f 2>/dev/null || echo "")

echo ""
echo "📦 JavaScript Bundle Analysis:"
echo "────────────────────────────────────"

total_js_size=0
js_file_count=0

for file in $JS_FILES; do
  size=$(get_file_size "$file")
  total_js_size=$((total_js_size + size))
  js_file_count=$((js_file_count + 1))

  filename=$(basename "$file")
  size_human=$(format_bytes $size)

  # Check if file exceeds chunk size limit
  size_kb=$((size / 1024))
  if [ $size_kb -gt $MAX_CHUNK_SIZE_KB ]; then
    echo -e "${RED}⚠️  $filename: $size_human (exceeds ${MAX_CHUNK_SIZE_KB}KB limit)${NC}"
  else
    echo "  $filename: $size_human"
  fi
done

total_js_human=$(format_bytes $total_js_size)
echo -e "Total JS: ${GREEN}$total_js_human${NC} ($js_file_count files)"

# Check if total JS exceeds limit
total_js_kb=$((total_js_size / 1024))
if [ $total_js_kb -gt $MAX_BUNDLE_SIZE_KB ]; then
  echo -e "${RED}❌ Total JS bundle exceeds ${MAX_BUNDLE_SIZE_KB}KB limit!${NC}"
fi

echo ""
echo "🎨 CSS Bundle Analysis:"
echo "────────────────────────────────────"

total_css_size=0
css_file_count=0

for file in $CSS_FILES; do
  size=$(get_file_size "$file")
  total_css_size=$((total_css_size + size))
  css_file_count=$((css_file_count + 1))

  filename=$(basename "$file")
  size_human=$(format_bytes $size)

  echo "  $filename: $size_human"
done

total_css_human=$(format_bytes $total_css_size)
echo -e "Total CSS: ${GREEN}$total_css_human${NC} ($css_file_count files)"

# Calculate total bundle size
total_size=$((total_js_size + total_css_size))
total_human=$(format_bytes $total_size)

echo ""
echo "📊 Overall Bundle Size:"
echo "────────────────────────────────────"
echo -e "Total: ${GREEN}$total_human${NC}"

# Compare with previous build
if [ -f "$SIZES_FILE" ]; then
  previous_total=$(cat "$SIZES_FILE" | grep "total" | cut -d: -f2 | tr -d ' ')

  if [ ! -z "$previous_total" ] && [ "$previous_total" != "0" ]; then
    difference=$((total_size - previous_total))
    percentage_diff=$(echo "scale=2; ($difference / $previous_total) * 100" | bc 2>/dev/null || echo "0")

    echo ""
    echo "📈 Comparison with previous build:"
    echo "────────────────────────────────────"
    echo "Previous: $(format_bytes $previous_total)"
    echo "Current:  $total_human"

    if [ "$difference" -gt 0 ]; then
      # Bundle size increased
      percentage_check=$(echo "$percentage_diff > $SIZE_INCREASE_THRESHOLD" | bc 2>/dev/null || echo "0")

      if [ "$percentage_check" -eq 1 ]; then
        echo -e "${RED}⚠️  Bundle size increased by $(format_bytes $difference) (${percentage_diff}%)${NC}"
        echo -e "${YELLOW}   Review recent changes for bundle size impact${NC}"
      else
        echo -e "${YELLOW}⬆️  Bundle size increased by $(format_bytes $difference) (${percentage_diff}%)${NC}"
      fi
    elif [ "$difference" -lt 0 ]; then
      # Bundle size decreased
      abs_diff=$((difference * -1))
      abs_percentage=$(echo "$percentage_diff" | sed 's/-//')
      echo -e "${GREEN}✅ Bundle size decreased by $(format_bytes $abs_diff) (${abs_percentage}%)${NC}"
    else
      echo -e "${GREEN}✅ Bundle size unchanged${NC}"
    fi
  fi
fi

# Save current sizes for next comparison
echo "total:$total_size" > "$SIZES_FILE"
echo "js:$total_js_size" >> "$SIZES_FILE"
echo "css:$total_css_size" >> "$SIZES_FILE"

# Generate detailed report
echo ""
echo "📄 Detailed Report:"
echo "────────────────────────────────────"

# Find largest files
echo ""
echo "🔝 Largest JS Files (>50KB):"
echo "$JS_FILES" | while read file; do
  size=$(get_file_size "$file")
  size_kb=$((size / 1024))
  if [ $size_kb -gt 50 ]; then
    filename=$(basename "$file")
    size_human=$(format_bytes $size)
    echo "  • $filename: $size_human"
  fi
done

# Bundle recommendations
echo ""
echo "💡 Recommendations:"
echo "────────────────────────────────────"

total_kb=$((total_size / 1024))

if [ $total_kb -gt 1000 ]; then
  echo -e "${YELLOW}• Consider code splitting to reduce initial load${NC}"
fi

if [ $js_file_count -lt 3 ]; then
  echo -e "${YELLOW}• Split into multiple chunks for better caching${NC}"
fi

if [ $total_css_size -gt $((total_js_size / 2)) ]; then
  echo -e "${YELLOW}• CSS is large, consider purging unused styles${NC}"
fi

# Check for duplicate dependencies
echo ""
echo "🔍 Dependency Analysis:"
echo "────────────────────────────────────"
if command -v npx &> /dev/null; then
  echo "Run 'npx depcheck' to find unused dependencies"
  echo "Run 'npx bundlephobia-cli' to analyze dependency sizes"
fi

echo ""
echo -e "${GREEN}✅ Bundle analysis complete!${NC}"
echo ""
echo "💾 Size data saved to $SIZES_FILE"
echo ""
