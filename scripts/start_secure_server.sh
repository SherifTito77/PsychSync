#!/bin/bash
# Secure Production Server Startup Script
# Starts PsychSync with HTTPS and security hardening

set -e

echo "🔐 STARTING PSYCHSYNC SECURE PRODUCTION SERVER"
echo "================================================"

# Check if SSL certificates exist
if [ ! -f "certs/psychsync.crt" ] || [ ! -f "certs/psychsync.key" ]; then
    echo "❌ SSL certificates not found!"
    echo "   Generating self-signed certificates for development..."
    mkdir -p certs

    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 -keyout certs/psychsync.key -out certs/psychsync.crt -days 365 -nodes \
        -subj "/C=US/ST=CA/L=San Francisco/O=PsychSync/CN=localhost"

    # Secure permissions
    chmod 640 certs/psychsync.crt
    chmod 600 certs/psychsync.key

    echo "✅ Self-signed certificates generated"
fi

# Verify certificate permissions
echo "🔍 Verifying SSL certificate permissions..."
CERT_PERM=$(stat -c "%a" certs/psychsync.crt)
KEY_PERM=$(stat -c "%a" certs/psychsync.key)

if [ "$CERT_PERM" != "640" ] && [ "$CERT_PERM" != "600" ]; then
    echo "⚠️  Fixing certificate permissions..."
    chmod 640 certs/psychsync.crt
fi

if [ "$KEY_PERM" != "600" ]; then
    echo "⚠️  Fixing private key permissions..."
    chmod 600 certs/psychsync.key
fi

echo "✅ Certificate permissions verified"
echo "   Certificate: $CERT_PERM (crt)"
echo "   Private Key: $KEY_PERM (key)"

# Set production environment
export ENVIRONMENT="production"
export DEBUG="false"

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis not running - starting Redis..."
    redis-server --daemonize yes --port 6379
    sleep 2
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
if ! pg_isready -q; then
    echo "❌ PostgreSQL not running!"
    echo "   Please start PostgreSQL before continuing"
    exit 1
fi

# Run database migrations
echo "🔍 Running database migrations..."
alembic upgrade head

# Verify SSL configuration with Python
echo "🔍 Verifying SSL configuration..."
python -c "
from app.core.ssl_config import ssl_config
result = ssl_config.verify_certificates()
if result['cert_valid']:
    print('✅ SSL configuration verified')
    print(f'   Certificate file: readable={result[\"cert_file_readable\"]}, permissions_ok={result[\"cert_permissions_ok\"]}')
    print(f'   Private key file: readable={result[\"key_file_readable\"]}, permissions_ok={result[\"key_permissions_ok\"]}')
else:
    print('❌ SSL configuration issues:')
    for issue in result.get('issues', []):
        print(f'   - {issue}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ SSL verification failed!"
    exit 1
fi

# Start the secure server
echo ""
echo "🚀 STARTING SECURE PSYCHSYNC SERVER"
echo "=================================="
echo "🔒 HTTPS Server: https://localhost:8443"
echo "📚 API Docs: https://localhost:8443/docs"
echo "🔍 ReDoc: https://localhost:8443/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start with production SSL configuration
python app/main.py

echo ""
echo "🛑 PsychSync server stopped"
