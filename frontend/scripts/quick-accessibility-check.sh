#!/bin/bash

# Quick Static Accessibility Check for PsychSync Frontend
# Analyzes code for common accessibility issues without running the app

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}♿ Quick Accessibility Check${NC}"
echo "=========================================="
echo ""

# Initialize counters
total_issues=0
warnings=0

echo -e "${BLUE}🔍 Analyzing Component Files...${NC}"
echo "───────────────────────────────────"

# Check for buttons without aria-label or text content
echo ""
echo "1. Checking buttons for accessible names..."

buttons_total=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<button" | wc -l | tr -d ' ')
buttons_issue=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<button" | grep -v "aria-label" | grep -v "aria-labelledby" | wc -l | tr -d ' ')

echo "   Total buttons: $buttons_total"
echo "   Without aria-label: $buttons_issue"

if [ $buttons_issue -gt 0 ]; then
  echo -e "   ${YELLOW}⚠️  Some buttons may lack accessible names${NC}"
  warnings=$((warnings + 1))
else
  echo -e "   ${GREEN}✅ Buttons have accessible names${NC}"
fi

# Check for images without alt text
echo ""
echo "2. Checking images for alt text..."

images_total=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<img" | wc -l | tr -d ' ')
images_issue=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<img" | grep -v "alt=" | wc -l | tr -d ' ')

echo "   Total images: $images_total"
echo "   Without alt text: $images_issue"

if [ $images_issue -gt 0 ]; then
  echo -e "   ${YELLOW}⚠️  Some images lack alt text${NC}"
  warnings=$((warnings + 1))
else
  echo -e "   ${GREEN}✅ Images have alt text${NC}"
fi

# Check for form inputs without labels
echo ""
echo "3. Checking form inputs for labels..."

inputs_total=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<input\|<select\|<textarea" | wc -l | tr -d ' ')

echo "   Total form inputs: $inputs_total"

# Check for ARIA attributes
inputs_with_aria=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<input\|<select\|<textarea" | grep "aria-label\|aria-labelledby" | wc -l | tr -d ' ')
inputs_with_id=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<input\|<select\|<textarea" | grep 'id=' | wc -l | tr -d ' ')

echo "   With aria attributes: $inputs_with_aria"
echo "   With id attributes: $inputs_with_id"

if [ $inputs_with_aria -eq 0 ] && [ $inputs_with_id -eq 0 ]; then
  echo -e "   ${YELLOW}⚠️  Form inputs may lack proper labeling${NC}"
  warnings=$((warnings + 1))
else
  echo -e "   ${GREEN}✅ Form inputs have labeling${NC}"
fi

# Check for semantic HTML
echo ""
echo "4. Checking semantic HTML usage..."

semantic_tags=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "<header\|<nav\|<main\|<footer\|<article\|<section" | wc -l | tr -d ' ')

echo "   Semantic HTML elements used: $semantic_tags"

if [ $semantic_tags -gt 10 ]; then
  echo -e "   ${GREEN}✅ Good semantic HTML usage${NC}"
else
  echo -e "   ${YELLOW}⚠️  Consider using more semantic HTML${NC}"
  warnings=$((warnings + 1))
fi

# Check for ARIA attributes
echo ""
echo "5. Checking ARIA attributes usage..."

aria_labels=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "aria-label\|aria-labelledby\|aria-describedby" | wc -l | tr -d ' ')
aria_roles=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "role=" | wc -l | tr -d ' ')

echo "   ARIA labels: $aria_labels"
echo "   ARIA roles: $aria_roles"

if [ $aria_labels -gt 5 ]; then
  echo -e "   ${GREEN}✅ Good ARIA label usage${NC}"
else
  echo -e "   ${YELLOW}⚠️  Consider adding more ARIA labels${NC}"
  warnings=$((warnings + 1))
fi

# Check for keyboard accessibility
echo ""
echo "6. Checking keyboard accessibility support..."

keyboard_handlers=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "onKeyDown\|onKeyPress\|onKeyUp" | wc -l | tr -d ' ')

echo "   Keyboard event handlers: $keyboard_handlers"

if [ $keyboard_handlers -gt 5 ]; then
  echo -e "   ${GREEN}✅ Keyboard navigation implemented${NC}"
else
  echo -e "   ${YELLOW}⚠️  Consider adding keyboard navigation${NC}"
  warnings=$((warnings + 1))
fi

# Check for focus management
echo ""
echo "7. Checking focus management..."

focus_attrs=$(find src -name "*.tsx" -o -name "*.jsx" | xargs grep -h "autoFocus\|tabIndex\|onFocus" | wc -l | tr -d ' ')

echo "   Focus attributes found: $focus_attrs"

if [ $focus_attrs -gt 0 ]; then
  echo -e "   ${GREEN}✅ Focus management present${NC}"
else
  echo -e "   ${YELLOW}⚠️  Consider adding focus management${NC}"
  warnings=$((warnings + 1))
fi

# Check for accessibility tests
echo ""
echo "8. Checking for accessibility tests..."

test_files=$(find src/tests -name "*accessibility*" -o -name "*a11y*" 2>/dev/null | wc -l | tr -d ' ')

echo "   Accessibility test files: $test_files"

if [ $test_files -gt 0 ]; then
  echo -e "   ${GREEN}✅ Accessibility tests exist${NC}"
else
  echo -e "   ${YELLOW}⚠️  Consider adding accessibility tests${NC}"
  warnings=$((warnings + 1))
fi

# Check for CSS contrast issues (basic check)
echo ""
echo "9. Checking color configuration..."

css_files=$(find src -name "*.css" | wc -l | tr -d ' ')

if [ $css_files -gt 0 ]; then
  echo "   CSS files found: $css_files"
  echo -e "   ${YELLOW}⚠️  Color contrast requires manual review or specialized tool${NC}"
else
  echo "   No CSS files (using Tailwind)"
  echo -e "   ${GREEN}✅ Tailwind handles most contrast ratios${NC}"
fi

echo ""
echo "=========================================="
echo -e "${BLUE}📊 Summary${NC}"
echo "=========================================="

echo ""
echo "Issues found:"
echo "  • Buttons without accessible names: $buttons_issue"
echo "  • Images without alt text: $images_issue"
echo "  • Warnings: $warnings"

if [ $warnings -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ Great accessibility practices!${NC}"
  exit_code=0
else
  echo ""
  echo -e "${YELLOW}⚠️  $warnings warning(s) found${NC}"
  echo "   Review the suggestions above for improvement"
  exit_code=0  # Exit with 0 since these are warnings, not critical issues
fi

echo ""
echo -e "${BLUE}💡 Recommendations:${NC}"
echo "───────────────────────────────────"
echo "1. Add aria-label to icon-only buttons"
echo "2. Ensure all images have descriptive alt text"
echo "3. Test with keyboard navigation only"
echo "4. Test with screen reader (NVDA/VoiceOver)"
echo "5. Check color contrast with WebAIM Contrast Checker"
echo "6. Run Lighthouse accessibility audit"
echo "7. Test with axe DevTools extension"
echo ""

echo -e "${GREEN}✅ Accessibility check complete!${NC}"
echo ""

exit $exit_code
