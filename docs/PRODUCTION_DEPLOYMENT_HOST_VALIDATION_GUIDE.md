# Production Deployment Guide - Host Validation Middleware

**Document Version:** 1.0
**Last Updated:** December 23, 2025
**Target Environment:** Production (Ubuntu 22.04 LTS / Debian 11+)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Configure Production ALLOWED_HOSTS](#step-1-configure-production-allowed_hosts)
4. [Step 2: Install Let's Encrypt SSL Certificate](#step-2-install-lets-encrypt-ssl-certificate)
5. [Step 3: Configure HTTPS on Port 8443](#step-3-configure-https-on-port-8443)
6. [Step 4: Verify StrictHostValidationMiddleware](#step-4-verify-stricthostvalidationmiddleware)
7. [Step 5: Deploy and Test](#step-5-deploy-and-test)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying the **Host Validation Middleware** to production with:
- ✅ Let's Encrypt SSL certificates (automated renewal)
- ✅ HTTPS on port 8443
- ✅ Strict host validation (no exemptions)
- ✅ Production domain configuration

**Estimated Time:** 30-45 minutes
**Difficulty:** Intermediate

---

## Prerequisites

### System Requirements

- **OS:** Ubuntu 22.04 LTS or Debian 11+
- **RAM:** 2GB minimum (4GB recommended)
- **CPU:** 2 cores minimum
- **Ports:** 80 (HTTP), 443 (HTTPS), 8443 (Alternative HTTPS)

### Domain Requirements

- ✅ Domain name purchased (e.g., `psychsync.com`)
- ✅ DNS A record pointing to server IP
- ✅ DNS propagation completed (check with `dig`)

### Software Requirements

```bash
# Check Python version (3.10+ required)
python3 --version

# Check if pip is installed
pip3 --version

# Check if git is installed
git --version
```

---

## Step 1: Configure Production ALLOWED_HOSTS

### 1.1 Update Environment Variables

Edit your production environment file:

```bash
# SSH into your production server
ssh user@your-server.com

# Navigate to project directory
cd /var/www/psychsync

# Edit .env.production
nano .env.production
```

**Add/update these lines:**

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Host header validation (CRITICAL - update with your domains)
ALLOWED_HOSTS=psychsync.com,www.psychsync.com,api.psychsync.com,app.psychsync.com

# CORS origins (update with your frontend URLs)
CORS_ORIGINS=https://psychsync.com,https://www.psychsync.com,https://app.psychsync.com

# Security settings
SECURE_COOKIES=true
CSRF_COOKIE_SECURE=true
```

**⚠️ CRITICAL:** Replace `psychsync.com` with your actual domain name!

### 1.2 Verify Configuration

```bash
# Verify the configuration was updated
grep ALLOWED_HOSTS .env.production
grep ENVIRONMENT .env.production
```

**Expected output:**
```
ALLOWED_HOSTS=psychsync.com,www.psychsync.com,api.psychsync.com,app.psychsync.com
ENVIRONMENT=production
```

---

## Step 2: Install Let's Encrypt SSL Certificate

### 2.1 Install Certbot

```bash
# Update package index
sudo apt update

# Install certbot and Nginx/Apache plugin
sudo apt install -y certbot python3-certbot-nginx

# OR for standalone mode (without web server)
sudo apt install -y certbot
```

### 2.2 Obtain SSL Certificate

#### Option A: Using Nginx (Recommended)

```bash
# Stop Nginx if it's running
sudo systemctl stop nginx

# Obtain certificate using standalone mode
sudo certbot certonly --standalone \
  -d psychsync.com \
  -d www.psychsync.com \
  -d api.psychsync.com \
  -d app.psychsync.com \
  --email admin@psychsync.com \
  --agree-tos \
  --no-eff-email \
  --staging  # Remove --staging for production certificate
```

#### Option B: Production Certificate (Real Domains Only)

```bash
# ⚠️ ONLY run this when DNS is fully propagated!
sudo certbot certonly --standalone \
  -d psychsync.com \
  -d www.psychsync.com \
  -d api.psychsync.com \
  -d app.psychsync.com \
  --email admin@psychsync.com \
  --agree-tos \
  --no-eff-email
```

**✅ Success message:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/psychsync.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/psychsync.com/privkey.pem
```

### 2.3 Verify Certificate Installation

```bash
# Check certificate files
sudo ls -la /etc/letsencrypt/live/psychsync.com/

# Verify certificate details
sudo openssl x509 -in /etc/letsencrypt/live/psychsync.com/fullchain.pem -text -noout | grep -E "Subject|Issuer|Not Before|Not After"
```

**Expected output:**
```
Subject: CN = psychsync.com
Issuer: C = US, O = Let's Encrypt, CN = R3
Not Before: Dec 23 00:00:00 2025 GMT
Not After: Mar 23 23:59:59 2026 GMT (90 days)
```

### 2.4 Set Up Auto-Renewal

Certbot automatically sets up a systemd timer or cron job. Verify it:

```bash
# Test auto-renewal (dry-run)
sudo certbot renew --dry-run

# Check systemd timer
sudo systemctl status certbot.timer

# OR check cron job
sudo crontab -l | grep certbot
```

**✅ Expected output:**
```
Congratulations, all simulated renewals succeeded.
```

---

## Step 3: Configure HTTPS on Port 8443

### 3.1 Create Systemd Service for uvicorn

Create the service file:

```bash
sudo nano /etc/systemd/system/psychsync-api.service
```

**Add the following content:**

```ini
[Unit]
Description=PsychSync API FastAPI Application
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/psychsync
Environment="PATH=/var/www/psychsync/venv/bin"
EnvironmentFile=/var/www/psychsync/.env.production

# Main command
ExecStart=/var/www/psychsync/venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8443 \
  --workers 4 \
  --loop uvloop \
  --http 11 \
  --ssl-keyfile /etc/letsencrypt/live/psychsync.com/privkey.pem \
  --ssl-certfile /etc/letsencrypt/live/psychsync.com/fullchain.pem \
  --log-level info

# Reload configuration
ExecReload=/bin/kill -s HUP $MAINPID

# Restart policy
Restart=always
RestartSec=5
StartLimitInterval=0

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/psychsync

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=psychsync-api

[Install]
WantedBy=multi-user.target
```

### 3.2 Create Production Startup Script

Create a helper script:

```bash
sudo nano /var/www/psychsync/scripts/start_production.sh
```

**Add the following:**

```bash
#!/bin/bash

set -e

echo "================================================"
echo "PsychSync Production Server Startup"
echo "================================================"
echo ""

# Configuration
PROJECT_DIR="/var/www/psychsync"
VENV_DIR="$PROJECT_DIR/venv"
ENV_FILE="$PROJECT_DIR/.env.production"
CERT_DIR="/etc/letsencrypt/live/psychsync.com"
LOG_DIR="$PROJECT_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Check prerequisites
echo "Checking prerequisites..."

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERROR: .env.production not found!"
    exit 1
fi

if [ ! -f "$CERT_DIR/privkey.pem" ]; then
    echo "❌ ERROR: SSL certificate not found at $CERT_DIR"
    echo "   Run: sudo certbot certonly --standalone -d psychsync.com"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ ERROR: Virtual environment not found!"
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# Load environment
export $(cat "$ENV_FILE" | grep -v '^#' | xargs)

# Display configuration
echo "Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Allowed Hosts: $ALLOWED_HOSTS"
echo "  SSL Certificate: $CERT_DIR/fullchain.pem"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  WARNING: Running as root. Consider using a dedicated user."
    echo "   Recommended: www-data (see systemd service file)"
    echo ""
fi

# Start server
echo "Starting FastAPI server on HTTPS port 8443..."
echo ""

cd "$PROJECT_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Start with uvicorn
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8443 \
    --workers 4 \
    --loop uvloop \
    --http 11 \
    --ssl-keyfile "$CERT_DIR/privkey.pem" \
    --ssl-certfile "$CERT_DIR/fullchain.pem" \
    --log-level info \
    --access-log \
    --log-config logging_config.ini
```

**Make it executable:**

```bash
chmod +x /var/www/psychsync/scripts/start_production.sh
```

### 3.3 Configure Nginx Reverse Proxy (Optional but Recommended)

If using Nginx as a reverse proxy:

```bash
sudo nano /etc/nginx/sites-available/psychsync-api
```

**Add the following configuration:**

```nginx
# Upstream configuration
upstream psychsync_backend {
    least_conn;
    server 127.0.0.1:8443;
    keepalive 64;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name psychsync.com www.psychsync.com api.psychsync.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name psychsync.com www.psychsync.com api.psychsync.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/psychsync.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/psychsync.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/psychsync.com/chain.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/psychsync_access.log;
    error_log /var/log/nginx/psychsync_error.log;

    # Proxy settings
    location / {
        proxy_pass https://psychsync_backend;
        proxy_http_version 1.1;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # SSL
        proxy_ssl_verify off;
    }

    # Health check endpoint (no proxy)
    location /health {
        proxy_pass https://psychsync_backend/health;
        access_log off;
    }
}
```

**Enable the site:**

```bash
sudo ln -s /etc/nginx/sites-available/psychsync-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3.4 Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable psychsync-api.service

# Start the service
sudo systemctl start psychsync-api.service

# Check status
sudo systemctl status psychsync-api.service
```

**✅ Expected output:**
```
● psychsync-api.service - PsychSync API FastAPI Application
     Loaded: loaded (/etc/systemd/system/psychsync-api.service; enabled)
     Active: active (running) since Mon 2025-12-23 10:00:00 UTC
   Main PID: 12345 (uvicorn)
      Tasks: 9 (limit: 4915)
     Memory: 250M
        CPU: 5%
     CGroup: /system.slice/psychsync-api.service
             └─12345 /var/www/psychsync/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8443
```

---

## Step 4: Verify StrictHostValidationMiddleware

### 4.1 Check Service Logs

```bash
# View recent logs
sudo journalctl -u psychsync-api.service -n 50 --no-pager

# Search for host validation messages
sudo journalctl -u psychsync-api.service | grep -i "host validation"
```

**✅ Expected output:**
```
2025-12-23 10:00:00 hostname psychsync-api[12345]: INFO - app.security.main - Strict Host validation middleware enabled (production mode)
2025-12-23 10:00:00 hostname psychsync-api[12345]: WARNING - app.middleware.host_validation - Strict host validation enabled - all requests will be validated
```

### 4.2 Test Middleware with curl

```bash
# Test 1: Valid host (should return 401 from auth, not 400 from middleware)
curl -I -H "Host: api.psychsync.com" https://api.psychsync.com/api/v1/users

# Test 2: Invalid host (should return 400 Bad Request)
curl -I -H "Host: evil.com" https://api.psychsync.com/api/v1/users

# Test 3: localhost (should be blocked in production)
curl -I -H "Host: localhost" https://api.psychsync.com/api/v1/users
```

**Expected Results:**

| Test | Host | Expected Result | Explanation |
|------|------|-----------------|-------------|
| 1 | `api.psychsync.com` | HTTP 401 | Passed to auth ✅ |
| 2 | `evil.com` | HTTP 400 | Blocked by middleware ✅ |
| 3 | `localhost` | HTTP 400 | Blocked in production ✅ |

### 4.3 Automated Verification Script

Create a verification script:

```bash
nano /var/www/psychsync/scripts/verify_production_host_validation.sh
```

**Add the following:**

```bash
#!/bin/bash

# Production Host Validation Verification Script
# Tests StrictHostValidationMiddleware in production environment

set -e

# Configuration
BASE_URL="https://api.psychsync.com"
VALID_HOST="api.psychsync.com"
INVALID_HOST="evil.com"
LOCALHOST_HOST="localhost"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "PRODUCTION HOST VALIDATION VERIFICATION"
echo "================================================"
echo ""
echo "Target: $BASE_URL"
echo "Time: $(date)"
echo ""

# Test counters
PASSED=0
FAILED=0

# Test 1: Valid host
echo "Test 1: Valid production host"
echo "-------------------------------------------"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $VALID_HOST" "$BASE_URL/api/v1/users")
if [ "$RESPONSE" = "401" ] || [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}: $VALID_HOST → HTTP $RESPONSE (passed through to app)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}: $VALID_HOST → HTTP $RESPONSE (unexpected)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Invalid host
echo "Test 2: Invalid host (should be BLOCKED)"
echo "-------------------------------------------"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $INVALID_HOST" "$BASE_URL/api/v1/users")
if [ "$RESPONSE" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC}: $INVALID_HOST → HTTP $RESPONSE (correctly blocked)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}: $INVALID_HOST → HTTP $RESPONSE (should be 400)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: localhost (should be blocked in production)
echo "Test 3: localhost (should be BLOCKED in production)"
echo "-------------------------------------------"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $LOCALHOST_HOST" "$BASE_URL/api/v1/users")
if [ "$RESPONSE" = "400" ]; then
    echo -e "${GREEN}✓ PASS${NC}: $LOCALHOST_HOST → HTTP $RESPONSE (correctly blocked)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}: $LOCALHOST_HOST → HTTP $RESPONSE (should be 400 in production)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "================================================"
echo "VERIFICATION SUMMARY"
echo "================================================"
echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "The StrictHostValidationMiddleware is working correctly!"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check:"
    echo "  1. ALLOWED_HOSTS is configured in .env.production"
    echo "  2. ENVIRONMENT=production is set"
    echo "  3. Service is using StrictHostValidationMiddleware"
    echo "  4. Service has been restarted after configuration changes"
    echo ""
    exit 1
fi
```

**Make it executable and run:**

```bash
chmod +x /var/www/psychsync/scripts/verify_production_host_validation.sh
/var/www/psychsync/scripts/verify_production_host_validation.sh
```

---

## Step 5: Deploy and Test

### 5.1 Pre-Deployment Checklist

```bash
# Run this checklist before deploying

echo "================================================"
echo "PRE-DEPLOYMENT CHECKLIST"
echo "================================================"
echo ""

# Check 1: DNS propagation
echo "1. Checking DNS propagation..."
dig +short psychsync.com | grep -E '^[0-9]'
if [ $? -eq 0 ]; then
    echo "   ✅ DNS is propagated"
else
    echo "   ❌ DNS not propagated - wait and retry"
    exit 1
fi

# Check 2: SSL certificate
echo "2. Checking SSL certificate..."
if [ -f "/etc/letsencrypt/live/psychsync.com/fullchain.pem" ]; then
    echo "   ✅ SSL certificate exists"
else
    echo "   ❌ SSL certificate missing - run certbot"
    exit 1
fi

# Check 3: Environment file
echo "3. Checking .env.production..."
if grep -q "ALLOWED_HOSTS" /var/www/psychsync/.env.production; then
    echo "   ✅ ALLOWED_HOSTS configured"
else
    echo "   ❌ ALLOWED_HOSTS not configured"
    exit 1
fi

if grep -q "ENVIRONMENT=production" /var/www/psychsync/.env.production; then
    echo "   ✅ ENVIRONMENT=production set"
else
    echo "   ❌ ENVIRONMENT not set to production"
    exit 1
fi

# Check 4: Service files
echo "4. Checking systemd service..."
if [ -f "/etc/systemd/system/psychsync-api.service" ]; then
    echo "   ✅ Systemd service file exists"
else
    echo "   ❌ Systemd service file missing"
    exit 1
fi

# Check 5: Nginx configuration (if using Nginx)
echo "5. Checking Nginx configuration..."
if [ -f "/etc/nginx/sites-available/psychsync-api" ]; then
    echo "   ✅ Nginx configuration exists"
    if nginx -t 2>/dev/null; then
        echo "   ✅ Nginx configuration valid"
    else
        echo "   ❌ Nginx configuration has errors"
        exit 1
    fi
else
    echo "   ⚠️  Nginx not configured (optional)"
fi

echo ""
echo "================================================"
echo "✅ ALL CHECKS PASSED - READY TO DEPLOY"
echo "================================================"
```

### 5.2 Deployment Commands

```bash
# 1. Stop existing service (if running)
sudo systemctl stop psychsync-api.service

# 2. Pull latest code
git pull origin main

# 3. Install/update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Run database migrations
alembic upgrade head

# 5. Restart service
sudo systemctl start psychsync-api.service

# 6. Check status
sudo systemctl status psychsync-api.service

# 7. Verify host validation
/var/www/psychsync/scripts/verify_production_host_validation.sh
```

---

## Monitoring and Maintenance

### 6.1 Log Monitoring

```bash
# View live logs
sudo journalctl -u psychsync-api.service -f

# View host validation security events
sudo journalctl -u psychsync-api.service | grep -i "host\|invalid\|blocked"

# View errors
sudo journalctl -u psychsync-api.service -p err

# View last 100 lines
sudo journalctl -u psychsync-api.service -n 100
```

### 6.2 SSL Certificate Monitoring

```bash
# Check certificate expiry
sudo certbot certificates

# Check auto-renewal timer
sudo systemctl status certbot.timer

# View renewal logs
sudo cat /var/log/letsencrypt/letsencrypt.log | tail -50
```

### 6.3 Health Checks

```bash
# API health check
curl https://api.psychsync.com/health

# SSL/TLS check
curl -vI https://api.psychsync.com 2>&1 | grep -E "TLS|SSL|subject|issuer"

# Security headers check
curl -I https://api.psychsync.com/health | grep -E "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options"
```

### 6.4 Performance Monitoring

```bash
# Check service resource usage
sudo systemctl status psychsync-api.service

# Check memory usage
ps aux | grep uvicorn

# Check open connections
sudo netstat -anp | grep 8443

# Check SSL handshake performance
openssl s_time -connect api.psychsync.com:443 -www / -new
```

---

## Troubleshooting

### Issue 1: Middleware Not Blocking Invalid Hosts

**Symptoms:**
- Invalid hosts returning 200 instead of 400
- All hosts being allowed through

**Solutions:**

1. **Check Environment Variable:**
```bash
grep "ENVIRONMENT" /var/www/psychsync/.env.production
# Should be: ENVIRONMENT=production
```

2. **Check ALLOWED_HOSTS:**
```bash
grep "ALLOWED_HOSTS" /var/www/psychsync/.env.production
# Should contain your production domains
```

3. **Check Service Logs:**
```bash
sudo journalctl -u psychsync-api.service | grep -i "middleware"
# Should see: "Strict Host validation middleware enabled (production mode)"
```

4. **Restart Service:**
```bash
sudo systemctl restart psychsync-api.service
```

### Issue 2: SSL Certificate Errors

**Symptoms:**
- "SSL certificate error" in browser
- "certificate verify failed" in curl

**Solutions:**

1. **Check Certificate Files:**
```bash
sudo ls -la /etc/letsencrypt/live/psychsync.com/
# Should show: fullchain.pem, privkey.pem, chain.pem
```

2. **Check Certificate Expiry:**
```bash
sudo certbot certificates
```

3. **Renew Certificate:**
```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx
sudo systemctl restart psychsync-api.service
```

4. **Check File Permissions:**
```bash
sudo ls -la /etc/letsencrypt/live/psychsync.com/privkey.pem
# Should be readable by the service user (www-data)
```

### Issue 3: Service Won't Start

**Symptoms:**
- `systemctl start` fails
- Service shows "failed" status

**Solutions:**

1. **Check Status:**
```bash
sudo systemctl status psychsync-api.service
```

2. **View Logs:**
```bash
sudo journalctl -u psychsync-api.service -n 100 --no-pager
```

3. **Common Issues:**

**Port already in use:**
```bash
# Check what's using port 8443
sudo lsof -i :8443

# Kill the process
sudo kill -9 <PID>
```

**Wrong path to certificate:**
```bash
# Verify certificate paths
sudo ls -la /etc/letsencrypt/live/psychsync.com/
```

**Virtual environment issues:**
```bash
# Recreate venv if needed
cd /var/www/psychsync
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 4: High Memory Usage

**Symptoms:**
- Service using >1GB RAM
- OOM (Out of Memory) errors

**Solutions:**

1. **Reduce Worker Count:**
```ini
# In /etc/systemd/system/psychsync-api.service
ExecStart=... --workers 2  # Reduce from 4 to 2
```

2. **Enable Worker Recycling:**
```ini
ExecStart=... --max-requests 1000 --max-requests-jitter 100
```

3. **Monitor Memory:**
```bash
watch -n 5 'ps aux | grep uvicorn'
```

---

## Security Best Practices

### 7.1 Firewall Configuration

```bash
# Configure UFW (Uncomplicated Firewall)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8443/tcp   # Block direct access to uvicorn (only through Nginx)
sudo ufw enable
sudo ufw status
```

### 7.2 Fail2Ban Configuration

```bash
# Install fail2ban
sudo apt install fail2ban

# Create jail configuration
sudo nano /etc/fail2ban/jail.local
```

**Add:**

```ini
[psychsync-api]
enabled = true
port = http,https
filter = psychsync-api
logpath = /var/log/nginx/psychsync_access.log
maxretry = 10
findtime = 600
bantime = 3600
```

### 7.3 Regular Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Check for security updates
sudo apt list --upgradable | grep -i security

# Auto-install security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Appendices

### Appendix A: Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Deployment environment | `production` | ✅ Yes |
| `ALLOWED_HOSTS` | Allowed host headers | `psychsync.com,www.psychsync.com` | ✅ Yes |
| `CORS_ORIGINS` | Allowed CORS origins | `https://psychsync.com` | ✅ Yes |
| `DEBUG` | Debug mode | `false` | ✅ Yes |
| `SECRET_KEY` | JWT signing key | `<random 128 chars>` | ✅ Yes |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` | ✅ Yes |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` | ✅ Yes |

### Appendix B: Port Reference

| Port | Protocol | Service | Public |
|------|----------|---------|--------|
| 22 | TCP | SSH | ⚠️ Yes (restrict) |
| 80 | TCP | HTTP (redirect) | ✅ Yes |
| 443 | TCP | HTTPS (Nginx) | ✅ Yes |
| 8443 | TCP | HTTPS (uvicorn) | ❌ No (internal) |

### Appendix C: Useful Commands

```bash
# Check certificate details
openssl s_client -connect api.psychsync.com:443 -servername api.psychsync.com

# Test TLS configuration
nmap --script ssl-enum-ciphers -p 443 api.psychsync.com

# Check DNS propagation
dig +short psychsync.com
nslookup psychsync.com

# Test from external location
curl -I https://api.psychsync.com/health

# Monitor server load
htop
```

---

## Support and Resources

- **Let's Encrypt Documentation:** https://letsencrypt.org/docs/
- **Certbot Documentation:** https://certbot.eff.org/docs/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/deployment/
- **Uvicorn Documentation:** https://www.uvicorn.org/deployment/

---

**Document Version:** 1.0
**Last Updated:** December 23, 2025
**Maintained By:** PsychSync Security Team

`★ Insight ─────────────────────────────────────`
**Defense in Depth:** This guide demonstrates multiple layers of security: network-level (firewall, fail2ban), transport-level (TLS 1.3, strong ciphers), application-level (host validation, CORS), and infrastructure-level (systemd hardening, SELinux). No single security control is sufficient - the combination creates a robust security posture.

**Automated Certificate Management:** Let's Encrypt with certbot eliminates the manual overhead of SSL certificate management. The 90-day expiry forces frequent renewal cycles, which means compromised certificates have a limited window of abuse. The auto-renewal systemd timer ensures certificates never expire unexpectedly.

**Production Hardening:** The systemd service configuration includes multiple security hardening measures: NoNewPrivileges, PrivateTmp, ProtectSystem, and ProtectHome. These Linux kernel features restrict what the process can do even if an attacker gains code execution, limiting the blast radius of potential exploits.

`─────────────────────────────────────────────────`

---

**End of Guide**
