#!/bin/bash

# Accessibility Testing Script for PsychSync Frontend
# Uses axe-core and Playwright to test accessibility issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "♿ Running Accessibility Tests..."
echo ""

# Check if dev server is running
if ! curl -s http://localhost:5174 > /dev/null; then
  echo -e "${YELLOW}⚠️  Dev server not running on port 5174. Starting it now...${NC}"
  npm run dev &
  DEV_SERVER_PID=$!
  echo "Waiting for dev server to start..."
  sleep 10
else
  echo -e "${GREEN}✅ Dev server is running${NC}"
  DEV_SERVER_PID=""
fi

# Function to run axe-core on a URL
test_page_accessibility() {
  local url=$1
  local page_name=$2

  echo -e "${BLUE}Testing: $page_name${NC}"
  echo "URL: $url"

  # Use Playwright with axe-core if available
  if command -v npx &> /dev/null; then
    # Create temporary test file
    cat > /tmp/a11y-test.js << EOL
const { chromium } = require('playwright');
const { AxeBuilder } = require('@axe-core/playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('$url', { waitUntil: 'networkidle' });

  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();

  await browser.close();

  if (accessibilityScanResults.violations.length > 0) {
    console.log(JSON.stringify({
      violations: accessibilityScanResults.violations,
      passes: accessibilityScanResults.passes.length
    }, null, 2));
    process.exit(1);
  } else {
    console.log(JSON.stringify({ violations: [], passes: accessibilityScanResults.passes.length }));
    process.exit(0);
  }
})();
EOL

    # Run the test
    if node /tmp/a11y-test.js 2>/dev/null; then
      echo -e "${GREEN}✅ PASSED: No accessibility violations${NC}"
      return 0
    else
      echo -e "${RED}❌ FAILED: Accessibility violations found${NC}"
      return 1
    fi
  else
    echo -e "${YELLOW}⚠️  Playwright not installed. Install with: npm install -D @axe-core/playwright playwright${NC}"
    return 1
  fi
}

# Array of pages to test
declare -a pages=(
  "http://localhost:5174/|Home Page"
  "http://localhost:5174/login|Login Page"
  "http://localhost:5174/register|Registration Page"
  "http://localhost:5174/dashboard|Dashboard"
)

echo "📋 Testing Key Pages:"
echo "────────────────────────────────────"

total_violations=0

for page in "${pages[@]}"; do
  IFS="|" read -r url name <<< "$page"
  echo ""

  if test_page_accessibility "$url" "$name"; then
    echo -e "  ${GREEN}✓ $name passed accessibility checks${NC}"
  else
    echo -e "  ${RED}✗ $name has accessibility issues${NC}"
    total_violations=$((total_violations + 1))
  fi
done

echo ""
echo "────────────────────────────────────"

# Run static analysis on component files
echo ""
echo "🔍 Static Accessibility Analysis:"
echo "────────────────────────────────────"

# Check for common accessibility issues in component files
echo ""
echo "Checking for missing ARIA labels..."

# Find button elements without aria-label
buttons_without_aria=$(grep -r "<button" frontend/src --include="*.tsx" --include="*.jsx" | grep -v "aria-label" | grep -v "aria-labelledby" | wc -l)

echo "  Buttons without aria-label: $buttons_without_aria"

# Find images without alt text
images_without_alt=$(grep -r "<img" frontend/src --include="*.tsx" --include="*.jsx" | grep -v "alt=" | wc -l)

echo "  Images without alt text: $images_without_alt"

# Find inputs without labels
inputs_without_labels=$(grep -r "<input" frontend/src --include="*.tsx" --include="*.jsx" | grep -v "aria-label" | grep -v "id=" | wc -l)

echo "  Inputs without proper labeling: $inputs_without_labels"

# Color contrast check (basic)
echo ""
echo "Checking color contrast..."
# This would require a more sophisticated tool
echo "  ⚠️  Color contrast analysis requires manual review or specialized tool"

# Generate report
echo ""
echo "📊 Accessibility Test Summary:"
echo "────────────────────────────────────"

if [ $total_violations -eq 0 ]; then
  echo -e "${GREEN}✅ All pages passed accessibility tests!${NC}"
  exit_code=0
else
  echo -e "${RED}❌ $total_violations page(s) failed accessibility tests${NC}"
  exit_code=1
fi

echo ""
echo "Static Analysis Results:"
echo "  • Buttons without aria-label: $buttons_without_aria"
echo "  • Images without alt text: $images_without_alt"
echo "  • Inputs without labels: $inputs_without_labels"

# Recommendations
echo ""
echo "💡 Accessibility Recommendations:"
echo "────────────────────────────────────"

if [ $buttons_without_aria -gt 10 ]; then
  echo -e "${YELLOW}• Add aria-label to icon-only buttons${NC}"
fi

if [ $images_without_alt -gt 0 ]; then
  echo -e "${YELLOW}• Add alt text to all images${NC}"
fi

if [ $inputs_without_labels -gt 0 ]; then
  echo -e "${YELLOW}• Ensure all inputs have associated labels${NC}"
fi

echo "• Test with keyboard navigation"
echo "• Test with screen reader (NVDA or VoiceOver)"
echo "• Check color contrast with WebAIM Contrast Checker"

# Cleanup
if [ ! -z "$DEV_SERVER_PID" ]; then
  echo ""
  echo "Stopping dev server..."
  kill $DEV_SERVER_PID 2>/dev/null || true
fi

rm -f /tmp/a11y-test.js

echo ""
if [ $exit_code -eq 0 ]; then
  echo -e "${GREEN}✅ Accessibility testing complete!${NC}"
else
  echo -e "${RED}❌ Accessibility issues found. Please review and fix.${NC}"
fi

exit $exit_code
