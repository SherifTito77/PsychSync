#!/bin/bash

# PsychSync Localhost SSL Setup Script
# Creates SSL certificates for localhost development

set -e

CERT_DIR="certs"
LOCALHOST_CERT="$CERT_DIR/localhost.crt"
LOCALHOST_KEY="$CERT_DIR/localhost.key"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Setting up SSL for Localhost Development${NC}"
echo "=============================================="

# Create certs directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Function to create localhost certificate
create_localhost_cert() {
    echo "📋 Creating SSL certificate for localhost..."

    # Create a configuration file for the certificate
    cat > "$CERT_DIR/localhost.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

    # Generate private key
    openssl genrsa -out "$LOCALHOST_KEY" 2048

    # Generate certificate signing request
    openssl req -new -key "$LOCALHOST_KEY" -out "$CERT_DIR/localhost.csr" -config "$CERT_DIR/localhost.conf"

    # Generate self-signed certificate
    openssl x509 -req -in "$CERT_DIR/localhost.csr" -signkey "$LOCALHOST_KEY" -out "$LOCALHOST_CERT" -days 365 -extensions v3_req -extfile "$CERT_DIR/localhost.conf"

    # Clean up CSR file
    rm "$CERT_DIR/localhost.csr"

    echo -e "${GREEN}✅ SSL certificate created successfully${NC}"
}

# Function to trust the certificate on macOS
trust_certificate_macos() {
    echo "🔧 Adding certificate to macOS Keychain..."

    # Add to system keychain (requires sudo)
    if sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$LOCALHOST_CERT" 2>/dev/null; then
        echo -e "${GREEN}✅ Certificate added to system trust store${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not add to system trust store (requires admin privileges)${NC}"
        echo "You can manually add the certificate by:"
        echo "1. Double-clicking on $LOCALHOST_CERT"
        echo "2. Opening 'Keychain Access'"
        echo "3. Finding 'localhost' under 'Certificates'"
        echo "4. Double-clicking and setting 'When using this certificate' to 'Always Trust'"
    fi
}

# Check if certificates already exist
if [ -f "$LOCALHOST_CERT" ] && [ -f "$LOCALHOST_KEY" ]; then
    echo -e "${YELLOW}⚠️  SSL certificates already exist${NC}"
    echo "Do you want to regenerate them? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Using existing certificates"
        trust_certificate_macos
        exit 0
    fi
fi

# Create certificates
create_localhost_cert

# Trust the certificate
trust_certificate_macos

echo ""
echo -e "${GREEN}🎉 SSL setup completed!${NC}"
echo "=========================="
echo -e "${BLUE}Certificate:${NC} $LOCALHOST_CERT"
echo -e "${BLUE}Private Key:${NC} $LOCALHOST_KEY"
echo ""
echo "📝 Next steps:"
echo "1. Copy these files to your application configuration"
echo "2. Update your backend to use HTTPS"
echo "3. Update your frontend API base URL to use https://localhost:8000"
echo ""
echo "🌐 Test HTTPS: https://localhost:8000/health"
echo ""
echo -e "${YELLOW}⚠️  Note: You may see browser warnings initially.${NC}"
echo "This is normal for self-signed certificates."