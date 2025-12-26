#!/bin/bash

# SSL Certificate Generation Script
# Generates self-signed SSL certificates for development/testing
# For production, use Let's Encrypt or a trusted CA

set -e

CERT_DIR="certs"
CERT_FILE="$CERT_DIR/psychsync.crt"
KEY_FILE="$CERT_DIR/psychsync.key"
CSR_FILE="$CERT_DIR/psychsync.csr"
CONFIG_FILE="$CERT_DIR/openssl.cnf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "SSL Certificate Generation Script"
echo "================================================"
echo ""

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}ERROR: openssl is not installed${NC}"
    echo "Install with: brew install openssl (macOS) or apt install openssl (Linux)"
    exit 1
fi

# Create certs directory if it doesn't exist
if [ ! -d "$CERT_DIR" ]; then
    echo "Creating certs directory..."
    mkdir -p "$CERT_DIR"
fi

# Parse arguments
DOMAIN=${1:-"localhost"}
IP_ADDRESSES=${2:-"127.0.0.1,::1"}

echo "Domain: $DOMAIN"
echo "IP Addresses: $IP_ADDRESSES"
echo ""

# Create OpenSSL configuration file
echo "Creating OpenSSL configuration..."
cat > "$CONFIG_FILE" <<EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req
req_extensions = v3_req

[dn]
C = US
ST = State
L = City
O = PsychSync
OU = Development
CN = $DOMAIN

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
DNS.3 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Add additional IP addresses if provided
IFS=',' read -ra IPS <<< "$IP_ADDRESSES"
IP_INDEX=2
for ip in "${IPS[@]}"; do
    ip=$(echo "$ip" | xargs) # trim whitespace
    if [ "$ip" != "127.0.0.1" ] && [ "$ip" != "::1" ]; then
        echo "IP.$IP_INDEX = $ip" >> "$CONFIG_FILE"
        IP_INDEX=$((IP_INDEX + 1))
    fi
done

# Check if certificate already exists
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}WARNING: Certificate files already exist${NC}"
    read -p "Do you want to overwrite them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping certificate generation"
        exit 0
    fi
    rm -f "$CERT_FILE" "$KEY_FILE" "$CSR_FILE"
fi

# Generate private key
echo "Generating private key..."
openssl genrsa -out "$KEY_FILE" 4096 2>/dev/null

# Set appropriate permissions
chmod 600 "$KEY_FILE"
echo -e "${GREEN}✓${NC} Private key generated: $KEY_FILE"

# Generate certificate signing request
echo "Generating certificate signing request..."
openssl req -new -key "$KEY_FILE" -out "$CSR_FILE" -config "$CONFIG_FILE"
echo -e "${GREEN}✓${NC} CSR generated: $CSR_FILE"

# Generate self-signed certificate (valid for 1 year)
echo "Generating self-signed certificate..."
openssl x509 -req -days 365 -in "$CSR_FILE" -signkey "$KEY_FILE" -out "$CERT_FILE" \
    -extensions v3_req -extfile "$CONFIG_FILE" 2>/dev/null
chmod 640 "$CERT_FILE"
echo -e "${GREEN}✓${NC} Certificate generated: $CERT_FILE"

# Display certificate information
echo ""
echo "================================================"
echo "Certificate Information"
echo "================================================"
openssl x509 -in "$CERT_FILE" -noout -subject
openssl x509 -in "$CERT_FILE" -noout -dates
openssl x509 -in "$CERT_FILE" -noout -issuer
echo ""

# Verify certificate
echo "Verifying certificate..."
if openssl x509 -in "$CERT_FILE" -noout -checkend 0 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Certificate is valid"
else
    echo -e "${RED}✗${NC} Certificate validation failed"
    exit 1
fi

# Check certificate permissions
echo ""
echo "Checking file permissions..."
KEY_PERM=$(stat -c "%a" "$KEY_FILE" 2>/dev/null || stat -f "%OLp" "$KEY_FILE" 2>/dev/null)
CERT_PERM=$(stat -c "%a" "$CERT_FILE" 2>/dev/null || stat -f "%OLp" "$CERT_FILE" 2>/dev/null)

if [ "$KEY_PERM" = "600" ] || [ "$KEY_PERM" = "0600" ]; then
    echo -e "${GREEN}✓${NC} Private key permissions correct: $KEY_PERM"
else
    echo -e "${YELLOW}⚠${NC} Private key permissions: $KEY_PERM (should be 600)"
fi

if [ "$CERT_PERM" = "640" ] || [ "$CERT_PERM" = "0640" ] || [ "$CERT_PERM" = "644" ] || [ "$CERT_PERM" = "0644" ]; then
    echo -e "${GREEN}✓${NC} Certificate permissions correct: $CERT_PERM"
else
    echo -e "${YELLOW}⚠${NC} Certificate permissions: $CERT_PERM (should be 640 or 644)"
fi

# Test certificate
echo ""
echo "================================================"
echo "Testing Certificate"
echo "================================================"
echo ""
echo "To test the certificate, run:"
echo "  openssl s_client -connect localhost:8443 -servername $DOMAIN"
echo ""
echo "Or start the application with HTTPS:"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile $KEY_FILE --ssl-certfile $CERT_FILE"
echo ""

# Display SANs
echo "Subject Alternative Names:"
openssl x509 -in "$CERT_FILE" -noout -text | grep -A 1 "Subject Alternative Name" || echo "  (No SANs found)"
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}SSL Certificate Generation Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Certificate files:"
echo "  Certificate: $CERT_FILE"
echo "  Private Key: $KEY_FILE"
echo "  Config:     $CONFIG_FILE"
echo ""
echo -e "${YELLOW}NOTE: This is a self-signed certificate for development.${NC}"
echo -e "${YELLOW}For production, use Let's Encrypt or a trusted CA.${NC}"
echo ""
