#!/bin/bash
# setup_free.sh - Cost-Free PsychSync Email Analysis Setup Script
# This script sets up the entire system using only free/open-source tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🧠 PSYCHSYNC FREE EMAIL ANALYSIS SETUP               ║${NC}"
echo -e "${BLUE}║         Cost-Free Localhost Implementation                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# Check requirements
check_requirements() {
    echo -e "${YELLOW}🔍 Checking system requirements...${NC}"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi

    # Check Python (for local development)
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.11+${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All requirements met!${NC}"
}

# Generate encryption key
generate_encryption_key() {
    echo -e "${YELLOW}🔐 Generating encryption key...${NC}"

    python3 -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key().decode()
print(f'Generated Key: {key}')
print('Save this key in your .env file as EMAIL_ENCRYPTION_KEY')
"

    echo
    echo -e "${BLUE}Please copy the above key and save it securely.${NC}"
    read -p "Press Enter to continue..."
}

# Create environment file
create_env_file() {
    echo -e "${YELLOW}📝 Creating environment file...${NC}"

    if [ ! -f .env.free ]; then
        cat > .env.free << EOF
# PsychSync Free Email Analysis Environment
DATABASE_URL=postgresql://psychsync_user:psychsync_password_123@localhost:5432/psychsync_db
REDIS_URL=redis://localhost:6379/0

# Application Configuration
SECRET_KEY=free-dev-secret-key-change-in-production-psychsync-$(date +%s)
ENVIRONMENT=development
DEBUG=true

# Email Encryption (IMPORTANT: Generate your own key)
EMAIL_ENCRYPTION_KEY=your-fernet-key-here-generate-with-python-cryptography

# Free NLP Configuration
NLP_ENGINE=free
ENABLE_SENTIMENT_ANALYSIS=true
ENABLE_EMOTION_ANALYSIS=true
ENABLE_BEHAVIORAL_ANALYSIS=true

# Free Email Connector Configuration
USE_IMAP_CONNECTOR=true
DEFAULT_EMAIL_FETCH_LIMIT=1000
DEFAULT_EMAIL_FETCH_DAYS=30

# Celery Configuration (Free Redis)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Frontend Configuration
FRONTEND_URL=http://localhost:5173
VITE_API_URL=http://localhost:8000

# Feature Flags
ENABLE_EMAIL_ANALYSIS=true
ENABLE_CULTURE_METRICS=true
ENABLE_AI_COACHING=true

# Free Tier Limitations
MAX_USERS_PER_ORG=10
MAX_EMAIL_CONNECTIONS_PER_USER=3
MAX_ANALYSIS_HISTORY_DAYS=90
EOF

        echo -e "${GREEN}✅ Created .env.free file${NC}"
        echo -e "${YELLOW}⚠️  Please update EMAIL_ENCRYPTION_KEY with your generated key${NC}"
    else
        echo -e "${BLUE}ℹ️  .env.free file already exists${NC}"
    fi
}

# Install Python dependencies
install_dependencies() {
    echo -e "${YELLOW}📚 Installing Python dependencies...${NC}"

    # Check if virtual environment exists
    if [ ! -d "venv_free" ]; then
        echo -e "${BLUE}Creating Python virtual environment...${NC}"
        python3 -m venv venv_free
    fi

    # Activate virtual environment
    source venv_free/bin/activate

    # Install dependencies
    echo -e "${BLUE}Installing free Python packages...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt

    # Download NLP models
    echo -e "${BLUE}Downloading free NLP models...${NC}"
    python -m spacy download en_core_web_sm
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"

    echo -e "${GREEN}✅ Python dependencies installed${NC}"
}

# Setup database
setup_database() {
    echo -e "${YELLOW}🗄️  Setting up database...${NC}"

    # Start database using Docker
    echo -e "${BLUE}Starting PostgreSQL...${NC}"
    docker-compose -f docker-compose.free.yml up -d db

    # Wait for database to be ready
    echo -e "${BLUE}Waiting for database to be ready...${NC}"
    sleep 10

    # Check if database is ready
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f docker-compose.free.yml exec -T db pg_isready -U psychsync_user -d psychsync_db; then
            echo -e "${GREEN}✅ Database is ready${NC}"
            break
        fi

        echo -e "${YELLOW}Attempt $attempt/$max_attempts: Database not ready, waiting...${NC}"
        sleep 2
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        echo -e "${RED}❌ Database failed to start${NC}"
        exit 1
    fi

    # Run database migrations
    echo -e "${BLUE}Running database migrations...${NC}"
    source venv_free/bin/activate
    export DATABASE_URL="postgresql://psychsync_user:psychsync_password_123@localhost:5432/psychsync_db"

    if command -v alembic &> /dev/null; then
        alembic upgrade head
        echo -e "${GREEN}✅ Database migrations completed${NC}"
    else
        echo -e "${YELLOW}⚠️  Alembic not found. Please install it first: pip install alembic${NC}"
    fi
}

# Setup frontend
setup_frontend() {
    echo -e "${YELLOW}⚛️  Setting up frontend...${NC}"

    cd frontend

    # Install Node.js dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${BLUE}Installing Node.js dependencies...${NC}"
        npm install
        echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    else
        echo -e "${BLUE}ℹ️  Frontend dependencies already installed${NC}"
    fi

    cd ..
}

# Create startup script
create_startup_script() {
    echo -e "${YELLOW}🚀 Creating startup script...${NC}"

    cat > start_free.sh << 'EOF'
#!/bin/bash
# start_free.sh - Start PsychSync Free Email Analysis System

echo "🧠 Starting PsychSync Free Email Analysis..."

# Load environment
if [ -f .env.free ]; then
    export $(cat .env.free | grep -v '^#' | xargs)
else
    echo "❌ .env.free file not found. Please run setup_free.sh first."
    exit 1
fi

# Start all services
echo "🚀 Starting all services with Docker Compose..."
docker-compose -f docker-compose.free.yml up --build

# To stop services, press Ctrl+C and run:
# docker-compose -f docker-compose.free.yml down
EOF

    chmod +x start_free.sh
    echo -e "${GREEN}✅ Created start_free.sh${NC}"
}

# Create free email connector guide
create_email_guide() {
    echo -e "${YELLOW}📧 Creating email connector guide...${NC}"

    cat > FREE_EMAIL_SETUP.md << 'EOF'
# Free Email Connector Setup Guide

## Overview
This guide shows how to connect your email accounts for free using IMAP and App Passwords.

## Supported Providers

### Gmail (Google)
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate new app password for "Mail"
3. Use your Gmail address and the 16-character app password

### Outlook/Microsoft
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Go to Microsoft Account security
   - Advanced security options → App passwords
   - Create new app password
3. Use your Outlook email and app password

### Yahoo Mail
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Go to Yahoo Account security
   - App passwords → Generate app password
3. Use your Yahoo email and app password

## Custom IMAP Providers
For other email providers, you'll need:
- IMAP server hostname (e.g., mail.yourdomain.com)
- Port (usually 993 for SSL, 143 for STARTTLS)
- SSL/TLS settings

## Security Notes
- Never share your app passwords
- App passwords are specific to each application
- You can revoke app passwords anytime
- Use different app passwords for different applications

## Connecting in PsychSync
1. Go to Email Connections page
2. Click "Add Email Account"
3. Choose "IMAP Connection" (Free option)
4. Enter your email and app password
5. For custom providers, enter IMAP server details
6. Test connection and save
EOF

    echo -e "${GREEN}✅ Created FREE_EMAIL_SETUP.md${NC}"
}

# Main setup function
main() {
    echo -e "${BLUE}🎯 Starting PsychSync Free Email Analysis Setup...${NC}"
    echo

    check_requirements
    echo

    generate_encryption_key
    echo

    create_env_file
    echo

    install_dependencies
    echo

    setup_database
    echo

    setup_frontend
    echo

    create_startup_script
    echo

    create_email_guide
    echo

    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "1. Update EMAIL_ENCRYPTION_KEY in .env.free with your generated key"
    echo -e "2. Review .env.free and update any other settings"
    echo -e "3. Run: ./start_free.sh"
    echo -e "4. Open: http://localhost:5173 (Frontend)"
    echo -e "5. Open: http://localhost:8000/docs (API Documentation)"
    echo -e "6. Open: http://localhost:5050 (Database Admin)"
    echo -e "7. Open: http://localhost:8081 (Redis Admin)"
    echo
    echo -e "${YELLOW}📧 Read FREE_EMAIL_SETUP.md for email connection instructions${NC}"
    echo -e "${GREEN}🚀 Your free PsychSync Email Analysis system is ready!${NC}"
}

# Run main function
main "$@"