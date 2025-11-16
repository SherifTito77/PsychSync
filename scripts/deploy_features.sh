#!/bin/bash

# ============================================
# PsychSync Feature Deployment Script
# ============================================
# 
# This script helps deploy all new features:
# - Slack Bot Integration
# - Offline Mode / PWA
# - Push Notifications
# - GDPR Compliance
#
# Usage: ./scripts/deploy_features.sh [options]
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ENV_FILE="$BACKEND_DIR/.env"

# ============================================
# HELPER FUNCTIONS
# ============================================

print_step() {
    echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}\n"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is required but not installed."
        exit 1
    fi
}

# ============================================
# MAIN DEPLOYMENT STEPS
# ============================================

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════╗
║   PsychSync Feature Deployment        ║
║   v2.0.0                              ║
╚═══════════════════════════════════════╝
EOF
echo -e "${NC}"

# Step 1: Pre-flight checks
print_step "Step 1: Pre-flight checks"

check_command "python3"
check_command "pip"
check_command "npm"
check_command "psql"

print_success "All required tools are installed"

# Step 2: Check environment file
print_step "Step 2: Checking environment configuration"

if [ ! -f "$ENV_FILE" ]; then
    print_warning "No .env file found. Creating from template..."
    cp "$BACKEND_DIR/.env.example" "$ENV_FILE"
    print_warning "Please update $ENV_FILE with your configuration"
    exit 1
fi

# Check for required environment variables
required_vars=("DATABASE_URL" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE"; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "Missing required environment variables: ${missing_vars[*]}"
    exit 1
fi

print_success "Environment configuration looks good"

# Step 3: Install backend dependencies
print_step "Step 3: Installing backend dependencies"

cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_warning "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install new dependencies
print_warning "Installing Slack SDK..."
pip install slack-sdk slack-bolt

print_warning "Installing Web Push..."
pip install pywebpush

print_success "Backend dependencies installed"

# Step 4: Run database migrations
print_step "Step 4: Running database migrations"

# Check if database is accessible
if psql "$DATABASE_URL" -c '\q' 2>/dev/null; then
    print_success "Database connection successful"
    
    # Run migrations
    alembic upgrade head
    print_success "Database migrations completed"
else
    print_error "Cannot connect to database. Please check DATABASE_URL"
    exit 1
fi

# Step 5: Generate VAPID keys for push notifications
print_step "Step 5: Generating VAPID keys for push notifications"

if ! grep -q "^VAPID_PUBLIC_KEY=" "$ENV_FILE"; then
    print_warning "Generating VAPID keys..."
    
    python3 << 'PYTHON_SCRIPT'
from pywebpush import vapid_gen
import os

# Generate keys
vapid = vapid_gen.Vapid()
vapid.generate_keys()

# Get keys
private_key = vapid.private_key.private_bytes().hex()
public_key = vapid.public_key.public_bytes().hex()

print(f"\nAdd these to your .env file:")
print(f"VAPID_PUBLIC_KEY={public_key}")
print(f"VAPID_PRIVATE_KEY={private_key}")
print()
PYTHON_SCRIPT
    
    print_warning "Please add VAPID keys to .env file and run script again"
    exit 1
else
    print_success "VAPID keys already configured"
fi

# Step 6: Install frontend dependencies
print_step "Step 6: Installing frontend dependencies"

cd "$FRONTEND_DIR"

npm install

print_success "Frontend dependencies installed"

# Step 7: Copy PWA files
print_step "Step 7: Setting up PWA files"

# Check if files exist in public directory
pwa_files=("service-worker.js" "manifest.json" "offline.html")
missing_pwa=()

for file in "${pwa_files[@]}"; do
    if [ ! -f "$FRONTEND_DIR/public/$file" ]; then
        missing_pwa+=("$file")
    fi
done

if [ ${#missing_pwa[@]} -gt 0 ]; then
    print_warning "Missing PWA files: ${missing_pwa[*]}"
    print_warning "Please ensure these files are in frontend/public/"
else
    print_success "PWA files are in place"
fi

# Step 8: Generate PWA icons
print_step "Step 8: Checking PWA icons"

icon_sizes=(72 96 128 144 152 192 384 512)
icons_dir="$FRONTEND_DIR/public/assets/icons"

if [ ! -d "$icons_dir" ]; then
    mkdir -p "$icons_dir"
    print_warning "Created icons directory: $icons_dir"
    print_warning "Please generate PWA icons in sizes: ${icon_sizes[*]}"
else
    print_success "Icons directory exists"
fi

# Step 9: Slack Bot Setup Checklist
print_step "Step 9: Slack Bot Configuration"

slack_vars=("SLACK_BOT_TOKEN" "SLACK_SIGNING_SECRET" "SLACK_CLIENT_ID" "SLACK_CLIENT_SECRET")
slack_configured=true

for var in "${slack_vars[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE"; then
        slack_configured=false
        break
    fi
done

if [ "$slack_configured" = false ]; then
    print_warning "Slack bot not yet configured"
    echo ""
    echo "To configure Slack bot:"
    echo "1. Go to https://api.slack.com/apps"
    echo "2. Create a new app"
    echo "3. Configure OAuth scopes and permissions"
    echo "4. Add environment variables to .env"
    echo ""
    echo "See SLACK_BOT_SETUP_GUIDE.md for detailed instructions"
    echo ""
else
    print_success "Slack bot configured"
fi

# Step 10: Build frontend
print_step "Step 10: Building frontend"

cd "$FRONTEND_DIR"

# Set VAPID public key for frontend
if grep -q "^VAPID_PUBLIC_KEY=" "$ENV_FILE"; then
    VAPID_PUBLIC=$(grep "^VAPID_PUBLIC_KEY=" "$ENV_FILE" | cut -d '=' -f2)
    echo "REACT_APP_VAPID_PUBLIC_KEY=$VAPID_PUBLIC" >> .env.local
fi

npm run build

print_success "Frontend built successfully"

# Step 11: Run tests
print_step "Step 11: Running tests"

# Backend tests
cd "$BACKEND_DIR"
print_warning "Running backend tests..."
python -m pytest tests/ -v || print_warning "Some backend tests failed"

# Frontend tests
cd "$FRONTEND_DIR"
print_warning "Running frontend tests..."
npm test -- --watchAll=false || print_warning "Some frontend tests failed"

# Step 12: Health checks
print_step "Step 12: Running health checks"

cd "$BACKEND_DIR"

python3 << 'PYTHON_SCRIPT'
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

print("\n🔍 Health Checks:\n")

# Check database
try:
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    print("✅ Database connection: OK")
    conn.close()
except Exception as e:
    print(f"❌ Database connection: FAILED - {str(e)}")

# Check Slack configuration
slack_vars = ['SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET']
slack_ok = all(os.getenv(var) for var in slack_vars)
print(f"{'✅' if slack_ok else '⚠️ '} Slack configuration: {'OK' if slack_ok else 'INCOMPLETE'}")

# Check VAPID keys
vapid_ok = os.getenv('VAPID_PUBLIC_KEY') and os.getenv('VAPID_PRIVATE_KEY')
print(f"{'✅' if vapid_ok else '❌'} VAPID keys: {'OK' if vapid_ok else 'MISSING'}")

# Check required directories
import pathlib
dirs = ['exports', 'logs', 'uploads']
for d in dirs:
    path = pathlib.Path(d)
    path.mkdir(exist_ok=True)
    print(f"✅ Directory {d}: {'EXISTS' if path.exists() else 'CREATED'}")

print()
PYTHON_SCRIPT

# Final summary
print_step "Deployment Summary"

echo "=========================================="
echo "Deployment Status:"
echo "=========================================="
echo ""
echo "✅ Backend dependencies installed"
echo "✅ Database migrations completed"
echo "✅ Frontend built successfully"
echo ""

if [ "$slack_configured" = true ]; then
    echo "✅ Slack bot configured"
else
    echo "⚠️  Slack bot needs configuration"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Review and complete Slack bot setup:"
echo "   - See SLACK_BOT_SETUP_GUIDE.md"
echo ""
echo "2. Generate PWA icons:"
echo "   - Create icons in sizes: 72, 96, 128, 144, 152, 192, 384, 512"
echo "   - Place in: frontend/public/assets/icons/"
echo ""
echo "3. Test features:"
echo "   - Slack commands: /psychsync, /checkin, /wellness, /assess"
echo "   - Offline mode: Disable network in DevTools"
echo "   - Push notifications: Enable in settings"
echo "   - GDPR: Test export and deletion"
echo ""
echo "4. Start services:"
echo "   - Backend: uvicorn app.main:app --reload"
echo "   - Frontend: npm start"
echo "   - Prometheus: docker-compose up prometheus"
echo ""
echo "5. Review documentation:"
echo "   - IMPLEMENTATION_GUIDE.md"
echo "   - FINAL_IMPLEMENTATION_STATUS.md"
echo ""
echo "=========================================="
echo ""

print_success "Deployment preparation complete!"

echo ""
echo "To start the application:"
echo "  cd $BACKEND_DIR && uvicorn app.main:app --reload"
echo ""
echo "For detailed deployment instructions, see:"
echo "  COMPLETE_IMPLEMENTATION_CHECKLIST.md"
echo ""
