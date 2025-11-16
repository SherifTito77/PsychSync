#!/bin/bash  #/setup_redis.sh
# File: setup_redis.sh (place in project root)
# Quick setup script for Redis caching
# Run with: bash setup_redis.sh

set -e  # Exit on error

echo "=========================================="
echo "PsychSync Redis Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew is not installed${NC}"
    echo "Install Homebrew first: https://brew.sh"
    exit 1
fi

# Step 1: Install Redis
echo -e "${YELLOW}Step 1: Installing Redis...${NC}"
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✅ Redis is already installed${NC}"
else
    echo "Installing Redis via Homebrew..."
    brew install redis
    echo -e "${GREEN}✅ Redis installed${NC}"
fi
echo ""

# Step 2: Start Redis
echo -e "${YELLOW}Step 2: Starting Redis service...${NC}"
brew services start redis
sleep 2
echo -e "${GREEN}✅ Redis service started${NC}"
echo ""

# Step 3: Test Redis connection
echo -e "${YELLOW}Step 3: Testing Redis connection...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running and responding${NC}"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
    exit 1
fi
echo ""

# Step 4: Install Python dependencies
echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please create a virtual environment first:"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    exit 1
fi

source .venv/bin/activate

echo "Installing Redis Python packages..."
pip install redis==5.0.1 hiredis==2.3.2 psutil==5.9.6 -q
echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Step 5: Check .env file
echo -e "${YELLOW}Step 5: Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from template..."
    
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://psychsync_user:password@localhost:5432/psychsync
DB_USER=psychsync_user
DB_PASSWORD=password
DB_NAME=psychsync
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Cache Settings
CACHE_ENABLED=true
CACHE_DEFAULT_EXPIRE=3600

# Security Settings
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
DEBUG=true
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# Logging
LOG_LEVEL=INFO
EOF
    
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please update .env with your actual values!${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check if Redis settings are in .env
    if ! grep -q "REDIS_HOST" .env; then
        echo -e "${YELLOW}⚠️  Adding Redis settings to .env...${NC}"
        cat >> .env << 'EOF'

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Cache Settings
CACHE_ENABLED=true
CACHE_DEFAULT_EXPIRE=3600
EOF
        echo -e "${GREEN}✅ Redis settings added to .env${NC}"
    fi
fi
echo ""

# Step 6: Run tests
echo -e "${YELLOW}Step 6: Running cache tests...${NC}"
if [ -f "test_cache_setup.py" ]; then
    python test_cache_setup.py
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo ""
        echo -e "${GREEN}=========================================="
        echo "🎉 Redis Setup Complete!"
        echo "==========================================${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Review and update .env file with your actual values"
        echo "2. Start your FastAPI application:"
        echo "   uvicorn app.main:app --reload"
        echo "3. Test health endpoint:"
        echo "   curl http://localhost:8000/api/v1/health"
        echo ""
        echo "Redis commands:"
        echo "  Start:   brew services start redis"
        echo "  Stop:    brew services stop redis"
        echo "  Restart: brew services restart redis"
        echo "  CLI:     redis-cli"
        echo ""
    else
        echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  test_cache_setup.py not found, skipping tests${NC}"
    echo -e "${GREEN}✅ Redis setup complete (tests not run)${NC}"
fi

echo ""
echo -e "${GREEN}✅ All done!${NC}"