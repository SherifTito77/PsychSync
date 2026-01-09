#!/bin/bash

# PWA Verification Script for PsychSync Frontend
# Validates Progressive Web App configuration and features

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 PWA Verification Script${NC}"
echo "=========================================="
echo ""

# Function to check if file exists
check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✅${NC} $1 exists"
    return 0
  else
    echo -e "${RED}❌${NC} $1 missing"
    return 1
  fi
}

# Function to check if file contains content
check_content() {
  local file=$1
  local search_term=$2

  if grep -q "$search_term" "$file" 2>/dev/null; then
    echo -e "${GREEN}✅${NC} $file contains: $search_term"
    return 0
  else
    echo -e "${YELLOW}⚠️${NC}  $file missing: $search_term"
    return 1
  fi
}

echo -e "${BLUE}📋 PWA File Structure Check${NC}"
echo "───────────────────────────────────"

# Check core PWA files
files_to_check=(
  "public/manifest.json"
  "public/service-worker.js"
  "public/service-worker.ts"
  "dist/manifest.json"
  "dist/service-worker.js"
  "src/utils/pwaManager.ts"
  "src/components/PWAInstaller.tsx"
  "src/components/OfflineStatus.tsx"
)

all_files_exist=true
for file in "${files_to_check[@]}"; do
  if ! check_file "$file"; then
    all_files_exist=false
  fi
done

echo ""
echo -e "${BLUE}🎨 Manifest Configuration Check${NC}"
echo "───────────────────────────────────"

# Check manifest.json for required fields
manifest_file="public/manifest.json"

if [ -f "$manifest_file" ]; then
  echo "Checking manifest.json fields..."

  manifest_fields=(
    '"name"'
    '"short_name"'
    '"description"'
    '"start_url"'
    '"display"'
    '"theme_color"'
    '"background_color"'
    '"icons"'
  )

  for field in "${manifest_fields[@]}"; do
    check_content "$manifest_file" "$field"
  done

  # Check for at least one icon
  if grep -q '"icons"' "$manifest_file" && grep -q '"src"' "$manifest_file"; then
    icon_count=$(grep -o '"src"' "$manifest_file" | wc -l)
    echo -e "${GREEN}✅${NC} Icons found: $icon_count icon(s) defined"
  else
    echo -e "${YELLOW}⚠️${NC}  No icons found in manifest"
  fi
else
  echo -e "${RED}❌${NC} manifest.json not found"
  all_files_exist=false
fi

echo ""
echo -e "${BLUE}⚙️ Service Worker Check${NC}"
echo "───────────────────────────────────"

sw_file="public/service-worker.ts"

if [ -f "$sw_file" ]; then
  echo "Checking service-worker.ts implementation..."

  sw_features=(
    "install"
    "activate"
    "fetch"
    "CACHE_NAME"
    "caches.open"
  )

  for feature in "${sw_features[@]}"; do
    check_content "$sw_file" "$feature"
  done
else
  echo -e "${RED}❌${NC} service-worker.ts not found"
  all_files_exist=false
fi

echo ""
echo -e "${BLUE}🚀 PWA Manager Check${NC}"
echo "───────────────────────────────────"

pwa_manager_file="src/utils/pwaManager.ts"

if [ -f "$pwa_manager_file" ]; then
  echo "Checking pwaManager.ts implementation..."

  pwa_features=(
    "registerServiceWorker"
    "showInstallPrompt"
    "getInstallStatus"
    "getOfflineStatus"
    "class PWAManager"
  )

  for feature in "${pwa_features[@]}"; do
    check_content "$pwa_manager_file" "$feature"
  done
else
  echo -e "${RED}❌${NC} pwaManager.ts not found"
  all_files_exist=false
fi

echo ""
echo -e "${BLUE}📱 PWA Integration Check${NC}"
echo "───────────────────────────────────"

app_file="src/App.tsx"

if [ -f "$app_file" ]; then
  echo "Checking App.tsx PWA integration..."

  # Check if PWA manager is initialized
  if check_content "$app_file" "pwaManager.initialize"; then
    echo -e "${GREEN}✅${NC} PWA Manager is initialized in App.tsx"
  fi

  # Check if PWA components are imported
  if check_content "$app_file" "PWAInstaller"; then
    echo -e "${GREEN}✅${NC} PWAInstaller component imported"
  fi

  if check_content "$app_file" "OfflineStatus"; then
    echo -e "${GREEN}✅${NC} OfflineStatus component imported"
  fi
else
  echo -e "${RED}❌${NC} App.tsx not found"
  all_files_exist=false
fi

echo ""
echo -e "${BLUE}🎯 PWA Features Verification${NC}"
echo "───────────────────────────────────"

# Check for offline.html
if check_file "public/offline.html"; then
  echo -e "${GREEN}✅${NC} Offline fallback page exists"
else
  echo -e "${YELLOW}⚠️${NC}  offline.html not found (recommended)"
fi

# Check for icons
icon_dirs=("public/icons" "public/assets/icons")
icons_found=false

for dir in "${icon_dirs[@]}"; do
  if [ -d "$dir" ]; then
    icon_count=$(find "$dir" -type f \( -name "*.png" -o -name "*.svg" \) 2>/dev/null | wc -l)
    if [ $icon_count -gt 0 ]; then
      echo -e "${GREEN}✅${NC} Icon directory: $dir ($icon_count icons)"
      icons_found=true
    fi
  fi
done

if [ "$icons_found" = false ]; then
  echo -e "${YELLOW}⚠️${NC}  No icon directories found"
fi

echo ""
echo -e "${BLUE}🔐 HTTPS & Security Check${NC}"
echo "───────────────────────────────────"

# Check if service worker scope is correct
if [ -f "$sw_file" ]; then
  if grep -q "scope: '/'" "$sw_file" || grep -q "'/'" "$sw_file"; then
    echo -e "${GREEN}✅${NC} Service worker scope set to root"
  else
    echo -e "${YELLOW}⚠️${NC}  Service worker scope may not be root"
  fi
fi

# Check for HTTPS-only features
if [ -f "$pwa_manager_file" ]; then
  if check_content "$pwa_manager_file" "Notification"; then
    echo -e "${GREEN}✅${NC} Push notification support implemented"
  fi
fi

echo ""
echo -e "${BLUE}📊 Build Verification${NC}"
echo "───────────────────────────────────"

# Check if dist directory exists
if [ -d "dist" ]; then
  echo -e "${GREEN}✅${NC} Production build exists (dist/)"

  # Check if service worker is in dist
  if [ -f "dist/service-worker.js" ]; then
    echo -e "${GREEN}✅${NC} Service worker built successfully"
  fi

  # Check if manifest is in dist
  if [ -f "dist/manifest.json" ]; then
    echo -e "${GREEN}✅${NC} Manifest built successfully"
  fi

  # Check for index.html
  if [ -f "dist/index.html" ]; then
    # Check if manifest is linked
    if grep -q "manifest.json" "dist/index.html"; then
      echo -e "${GREEN}✅${NC} Manifest linked in index.html"
    else
      echo -e "${YELLOW}⚠️${NC}  Manifest not linked in index.html"
    fi
  fi
else
  echo -e "${YELLOW}⚠️${NC}  No production build found (run 'npm run build' first)"
fi

echo ""
echo -e "${BLUE}💡 PWA Best Practices Check${NC}"
echo "───────────────────────────────────"

# Check for theme color in index.html
if [ -f "index.html" ]; then
  if grep -q "theme-color" "index.html"; then
    echo -e "${GREEN}✅${NC} Theme color meta tag in index.html"
  else
    echo -e "${YELLOW}⚠️${NC}  Theme color meta tag missing (recommended)"
  fi
fi

# Check for viewport configuration
if [ -f "index.html" ]; then
  if grep -q "viewport" "index.html"; then
    echo -e "${GREEN}✅${NC} Viewport configured for mobile"
  else
    echo -e "${YELLOW}⚠️${NC}  Viewport configuration missing"
  fi
fi

# Check for apple-touch-icon
if [ -f "index.html" ]; then
  if grep -q "apple-touch-icon" "index.html"; then
    echo -e "${GREEN}✅${NC} Apple touch icon link present"
  else
    echo -e "${YELLOW}⚠️${NC}  Apple touch icon link missing (recommended for iOS)"
  fi
fi

echo ""
echo "=========================================="
echo -e "${BLUE}📋 Summary${NC}"
echo "=========================================="

if [ "$all_files_exist" = true ]; then
  echo -e "${GREEN}✅ All critical PWA files are present${NC}"
else
  echo -e "${YELLOW}⚠️${NC}  Some PWA files are missing"
fi

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "1. Test PWA in Chrome DevTools (Application tab)"
echo "2. Run Lighthouse PWA audit: lighthouse https://your-site.com --view"
echo "3. Test on real devices (Android & iOS)"
echo "4. Verify offline functionality"
echo "5. Test install prompts"
echo ""

echo -e "${GREEN}✅ PWA verification complete!${NC}"
echo ""
