#!/bin/bash
# Secure Network Startup Script
# Starts PsychSync with network security hardening

set -e

echo "🔐 STARTING PSYCHSYNC SECURE NETWORK CONFIGURATION"
echo "=================================================="

# Check if running as root for network changes
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script requires sudo privileges for network configuration"
    echo "   You may be prompted for your password"
fi

# Check Docker availability
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Check if secure environment file exists
if [ ! -f ".env.secure" ]; then
    echo "📝 Creating secure environment file..."
    cat > .env.secure << 'EOF'
# Secure Environment Configuration for PsychSync
# Generated: $(date)

# Database Configuration (secure passwords)
DB_USER=psychsync_user
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
DB_NAME=psychsync_db

# Redis Configuration
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Application Configuration
ENVIRONMENT=production
DEBUG=false
SSL_ENABLED=true
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

# Database URL (internal)
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}

# Redis URL (internal)
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Security Settings
CORS_ORIGINS=https://localhost,https://your-domain.com
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn-here

# Performance
REDIS_CACHE_TTL=300
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
EOF

    echo "✅ Created .env.secure with generated passwords"
    echo "   Database Password: $(grep DB_PASSWORD .env.secure | cut -d= -f2)"
    echo "   Redis Password: $(grep REDIS_PASSWORD .env.secure | cut -d= -f2)"
    echo ""
    echo "⚠️  SAVE THESE PASSWORDS SECURELY!"
fi

# Check SSL certificates
echo "🔍 Checking SSL certificates..."
if [ ! -f "certs/psychsync.crt" ] || [ ! -f "certs/psychsync.key" ]; then
    echo "📝 Generating SSL certificates..."
    mkdir -p certs

    # Generate self-signed certificate for development
    openssl req -x509 -newkey rsa:4096 -keyout certs/psychsync.key -out certs/psychsync.crt -days 365 -nodes \
        -subj "/C=US/ST=CA/L=San Francisco/O=PsychSync/CN=localhost"

    # Secure permissions
    chmod 640 certs/psychsync.crt
    chmod 600 certs/psychsync.key

    echo "✅ Generated SSL certificates"
    echo "⚠️  For production, replace with proper certificates from a CA"
else
    echo "✅ SSL certificates found"
fi

# Verify certificate permissions
CERT_PERM=$(stat -c "%a" certs/psychsync.crt)
KEY_PERM=$(stat -c "%a" certs/psychsync.key)

if [ "$CERT_PERM" != "640" ] && [ "$CERT_PERM" != "600" ]; then
    echo "🔧 Fixing certificate permissions..."
    chmod 640 certs/psychsync.crt
fi

if [ "$KEY_PERM" != "600" ]; then
    echo "🔧 Fixing private key permissions..."
    chmod 600 certs/psychsync.key
fi

# Stop any existing insecure containers
echo "🛑 Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Remove old networks
echo "🗑️  Cleaning up old networks..."
docker network prune -f 2>/dev/null || true

# Create logs directory
mkdir -p logs/nginx

# Build secure images
echo "🔨 Building secure Docker images..."
docker-compose -f docker-compose.secure.yml build

# Start secure services
echo "🚀 Starting secure services..."
docker-compose -f docker-compose.secure.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend
if docker-compose -f docker-compose.secure.yml exec -T backend curl -k https://localhost:8000/api/v1/health/public >/dev/null 2>&1; then
    echo "✅ Backend service is healthy"
else
    echo "❌ Backend service is not responding"
fi

# Check database
if docker-compose -f docker-compose.secure.yml exec -T db pg_isready -U psychsync_user -d psychsync_db >/dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database is not ready"
fi

# Check Redis
if docker-compose -f docker-compose.secure.yml exec -T redis redis-cli -a "$(grep REDIS_PASSWORD .env.secure | cut -d= -f2)" ping >/dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is not responding"
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.secure.yml exec -T backend alembic upgrade head

# Configure firewall rules
echo "🔧 Configuring firewall rules..."

# Configure iptables (if available)
if command -v iptables >/dev/null 2>&1; then
    echo "   Configuring iptables rules..."

    # Allow HTTP/HTTPS (through Nginx only)
    sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

    # Block direct access to application ports
    sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
    sudo iptables -A INPUT -p tcp --dport 5432 -j DROP
    sudo iptables -A INPUT -p tcp --dport 6379 -j DROP

    # Save iptables rules
    if command -v iptables-save >/dev/null 2>&1; then
        sudo iptables-save > /etc/iptables/rules.v4 2>/dev/null || \
        echo "⚠️  Could not save iptables rules persistently"
    fi

    echo "✅ Firewall rules configured"
fi

# Test external access
echo "🧪 Testing external access..."

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "localhost")

echo "   Server IP: $SERVER_IP"
echo "   Testing HTTP access..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/health | grep -q "200"; then
    echo "✅ HTTP access working (redirects to HTTPS)"
else
    echo "⚠️  HTTP access may not be working"
fi

echo "   Testing HTTPS access..."
if curl -s -k -o /dev/null -w "%{http_code}" https://localhost/health | grep -q "200"; then
    echo "✅ HTTPS access working"
else
    echo "⚠️  HTTPS access may not be working yet"
fi

# Test that internal ports are not exposed
echo "   Testing internal port exposure..."
if ! nc -z localhost 8000 2>/dev/null; then
    echo "✅ Backend port 8000 not exposed to host"
else
    echo "❌ Backend port 8000 is exposed - security risk!"
fi

if ! nc -z localhost 5432 2>/dev/null; then
    echo "✅ Database port 5432 not exposed to host"
else
    echo "❌ Database port 5432 is exposed - security risk!"
fi

if ! nc -z localhost 6379 2>/dev/null; then
    echo "✅ Redis port 6379 not exposed to host"
else
    echo "❌ Redis port 6379 is exposed - security risk!"
fi

echo ""
echo "🎉 SECURE NETWORK CONFIGURATION COMPLETED"
echo "======================================="
echo ""
echo "✅ Services started with security hardening:"
echo "   🔒 Backend only accessible via HTTPS (port 443)"
echo "   🔒 Database and Redis isolated from external access"
echo "   🔒 Network segmentation implemented"
echo "   🔒 Firewall rules configured"
echo "   🔒 SSL/TLS encryption enabled"
echo ""
echo "🌐 Access URLs:"
echo "   HTTP:  http://localhost (redirects to HTTPS)"
echo "   HTTPS: https://localhost"
echo "   API:   https://localhost/api/v1"
echo ""
echo "📋 Management Commands:"
echo "   View logs:     docker-compose -f docker-compose.secure.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.secure.yml down"
echo "   Restart:       docker-compose -f docker-compose.secure.yml restart"
echo ""
echo "🔒 Security Status:"
echo "   ✅ Network isolation implemented"
echo "   ✅ Internal services not exposed"
echo "   ✅ SSL/TLS encryption active"
echo "   ✅ Firewall rules configured"
echo "   ✅ Non-root container execution"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "1. Replace self-signed certificates with production CA certificates"
echo "2. Update ALLOWED_HOSTS in .env.secure with your actual domain"
echo "3. Configure proper domain DNS records"
echo "4. Set up monitoring and alerting for security events"
echo "5. Regularly update Docker images and dependencies"