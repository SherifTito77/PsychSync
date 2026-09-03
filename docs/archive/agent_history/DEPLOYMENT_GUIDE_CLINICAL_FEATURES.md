# Deployment Guide: Advanced Clinical Features

Complete deployment guide for Phase 1 & 2 clinical features including LSAS, EAT-26, Y-BOCS assessments, advanced analytics, telehealth video consultations, AI chatbot, and mobile apps.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Deployment](#database-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Mobile App Deployment](#mobile-app-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Infrastructure Requirements

**Minimum Production Configuration:**
- **Backend Server**: 4 CPU, 8GB RAM, 100GB SSD
- **Database Server**: PostgreSQL 14+ on dedicated instance
- **Redis**: 2GB RAM for caching and sessions
- **CDN**: CloudFront or similar for static assets
- **SSL Certificate**: Valid TLS certificate (Let's Encrypt or commercial)

**External Services:**
- Twilio Account (for video consultations)
- OpenAI API key (GPT-4 access)
- Email service (SendGrid, AWS SES, or similar)
- Firebase project (for mobile push notifications)

### Software Requirements

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Database**: PostgreSQL 14.0+
- **Frontend**: Node.js 18+, React 18+
- **Mobile**: React Native CLI, Android Studio, Xcode (macOS)
- **Web Server**: Nginx 1.21+

---

## Environment Configuration

### Backend Environment Variables

Create `/app/.env.production`:

```bash
# =================================================================
# API Configuration
# =================================================================
API_BASE_URL=https://api.psychsync.com/api/v1
FRONTEND_URL=https://psychsync.com
ENVIRONMENT=production

# =================================================================
# Database
# =================================================================
DATABASE_URL=postgresql+asyncpg://user:password@db-psychsync.prod.psychsync.com:5432/psychsync_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# =================================================================
# Redis
# =================================================================
REDIS_URL=redis://:password@redis-psychsync.prod.psychsync.com:6379/0
REDIS_SESSION_TTL=1800  # 30 minutes

# =================================================================
# Security
# =================================================================
SECRET_KEY=your-super-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# =================================================================
# OpenAI (for AI chatbot)
# =================================================================
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

# =================================================================
# Twilio Video (for telehealth)
# =================================================================
TWILIO_ACCOUNT_SID=ACyourtwilioaccountsid
TWILIO_AUTH_TOKEN=yourtwilioauthtoken
TWILIO_API_KEY=SKyourtwilioapikey
TWILIO_API_SECRET=yourtwilioapisecret

# =================================================================
# Email Service
# =================================================================
EMAIL_PROVIDER=sendgrid  # or ses, mailgun
SENDGRID_API_KEY=SG.yoursendgridapikey
EMAIL_FROM_ADDRESS=noreply@psychsync.com
EMAIL_FROM_NAME=PsychSync

# =================================================================
# Firebase (for mobile push notifications)
# =================================================================
FIREBASE_PROJECT_ID=your-firebase-project
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email

# =================================================================
# Monitoring & Logging
# =================================================================
SENTRY_DSN=https://your-sentry-dsn@sentry.io/projectid
LOG_LEVEL=INFO
ENABLE_ACCESS_LOGS=true

# =================================================================
# Feature Flags
# =================================================================
ENABLE_TELEHEALTH=true
ENABLE_AI_CHATBOT=true
ENABLE_CRISIS_DETECTION=true
ENABLE_ASSESSMENT_ANALYTICS=true
```

### Frontend Environment Variables

Create `/frontend/.env.production`:

```bash
# API Configuration
VITE_API_BASE_URL=https://api.psychsync.com/api/v1
VITE_WS_BASE_URL=wss://api.psychsync.com/ws

# Feature Flags
VITE_ENABLE_TELEHEALTH=true
VITE_ENABLE_AI_CHATBOT=true
VITE_ENABLE_ASSESSMENT_ANALYTICS=true

# External Services
VITE_TWILIO_ACCOUNT_SID=ACyourtwilioaccountsid

# Analytics (optional)
VITE_ENABLE_ANALYTICS=false
```

---

## Database Deployment

### Step 1: Apply Database Migrations

```bash
# Activate Python virtual environment
source venv/bin/activate

# Review pending migrations
alembic review-head

# Apply migrations in production
alembic upgrade head

# Verify migration success
alembic current
```

### Step 2: Verify Schema

Connect to PostgreSQL and verify tables:

```sql
-- Check new clinical tables
\dt clinical_*  -- Should show:
-- clinical_assessments_extended
-- assessment_trends
-- crisis_alerts
-- telehealth_sessions
-- chatbot_conversations
-- mobile_devices

-- Verify materialized view
\d+ population_health_stats

-- Check indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE tablename LIKE 'clinical_%'
   OR tablename = 'crisis_alerts';

-- Expected: 15+ indexes for performance
```

### Step 3: Seed Initial Data

```bash
# Run seed script (if applicable)
python -m app.scripts.seed_clinical_data

# Or manually create test assessments
python -c "
import asyncio
from app.db.session import get_async_db
from app.services.clinical.scoring_algorithms import LSASScorer

async def seed():
    async for db in get_async_db():
        # Create test assessments
        pass

asyncio.run(seed())
"
```

### Step 4: Configure Database Backups

```bash
# Setup automated backups
crontab -e

# Add daily backup at 2 AM UTC
0 2 * * * /app/scripts/backup_database.sh

# Weekly full backup on Sunday at 3 AM UTC
0 3 * * 0 /app/scripts/backup_database_full.sh
```

---

## Backend Deployment

### Step 1: Build and Deploy Application

```bash
# Navigate to project root
cd /path/to/psychsync

# Create production build
python -m build

# Deploy to production server
scp dist/psychsync-*.tar.gz user@production-server:/tmp/

# On production server:
ssh user@production-server
cd /app
tar -xzf /tmp/psychsync-*.tar.gz
cp -r psychsync/* ./

# Install dependencies
pip install --no-cache-dir -r requirements.txt

# Collect static files
python -m app.utils.collect_static

# Restart application
sudo systemctl restart psychsync-api
sudo systemctl restart psychsync-worker
```

### Step 2: Configure Uvicorn Service

Create `/etc/systemd/system/psychsync-api.service`:

```ini
[Unit]
Description=PsychSync FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=psychsync
Group=psychsync
WorkingDirectory=/app
Environment="PATH=/app/venv/bin"
ExecStart=/app/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --log-config logging_config.json
    --access-log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable psychsync-api
sudo systemctl start psychsync-api
sudo systemctl status psychsync-api
```

### Step 3: Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/psychsync-api`:

```nginx
upstream psychsync_backend {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8003 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.psychsync.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/psychsync_api.crt;
    ssl_certificate_key /etc/ssl/private/psychsync_api.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/psychsync_api_access.log;
    error_log /var/log/nginx/psychsync_api_error.log;

    # Proxy settings
    location / {
        proxy_pass http://psychsync_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support (for future real-time features)
    location /ws/ {
        proxy_pass http://psychsync_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Health check endpoint (doesn't require auth)
    location /health {
        proxy_pass http://psychsync_backend/health;
        access_log off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.psychsync.com;
    return 301 https://$server_name$request_uri;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/psychsync-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Verify Backend Deployment

```bash
# Health check
curl https://api.psychsync.com/health

# Should return:
# {"status": "healthy", "timestamp": "2024-01-20T10:00:00Z"}

# Test API endpoint
curl -X POST https://api.psychsync.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass"}'

# Check logs
sudo journalctl -u psychsync-api -f
```

---

## Frontend Deployment

### Step 1: Build Production Bundle

```bash
cd frontend

# Install dependencies
npm ci --production

# Create production build
npm run build

# Output will be in /frontend/dist/
```

### Step 2: Deploy to CDN

**Option A: AWS S3 + CloudFront**

```bash
# Upload to S3
aws s3 sync dist/ s3://psychsync-frontend-prod \
  --delete \
  --cache-control "public, max-age=31536000, immutable"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

**Option B: Traditional Server**

```bash
# Copy to web server
scp -r dist/* user@web-server:/var/www/psychsync/

# Set permissions
ssh user@web-server
sudo chown -R www-data:www-data /var/www/psychsync
sudo chmod -R 755 /var/www/psychsync
```

### Step 3: Configure Nginx for Frontend

Create `/etc/nginx/sites-available/psychsync-frontend`:

```nginx
server {
    listen 443 ssl http2;
    server_name psychsync.com www.psychsync.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/psychsync_frontend.crt;
    ssl_certificate_key /etc/ssl/private/psychsync_frontend.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;

    # Root directory
    root /var/www/psychsync;
    index index.html;

    # SPA routing - all routes go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass https://api.psychsync.com;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name psychsync.com www.psychsync.com;
    return 301 https://$server_name$request_uri;
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/psychsync-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Mobile App Deployment

### iOS App Store Deployment

#### Prerequisites
- Apple Developer Account ($99/year)
- Mac with Xcode 15+
- Distribution certificate
- Provisioning profiles

#### Build and Submit

```bash
cd mobile/psychsync_native

# Install dependencies
npm install

# Update bundle identifier
# Open ios/PsychSync.xcodeproj in Xcode
# Change Bundle Identifier to: com.psychsync.mobile

# Update version numbers
# In package.json: "version": "1.0.0"
# In ios/PsychSync/Info.plist: CFBundleShortVersionString = 1.0.0

# Build for archive
cd ios
xcodebuild -workspace PsychSync.xcworkspace \
  -scheme PsychSync \
  -configuration Release \
  -archivePath PsychSync.xcarchive \
  archive

# Export IPA
xcodebuild -exportArchive \
  -archivePath PsychSync.xcarchive \
  -exportPath ./build \
  -exportOptionsPlist ExportOptions.plist

# Upload to App Store Connect
xcrun altool --upload-app \
  --type ios \
  --file ./build/PsychSync.ipa \
  --username your-apple-id \
  --password app-specific-password
```

#### In App Store Connect:
1. Create new app
2. Fill in app information
3. Upload screenshots (required sizes)
4. Submit for review
5. Wait for approval (typically 1-3 days)

### Google Play Store Deployment

#### Prerequisites
- Google Play Developer Account ($25 one-time)
- Android Studio or command-line tools

#### Build and Submit

```bash
cd mobile/psychsync_native

# Generate signing key
keytool -genkey -v -keystore psychsync-release.keystore \
  -alias psychsync-key-alias \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# Store keystore securely
# Move to: ~/android-keystores/

# Configure signing in android/app/build.gradle:
android {
    signingConfigs {
        release {
            storeFile file('/path/to/psychsync-release.keystore')
            storePassword 'your-keystore-password'
            keyAlias 'psychsync-key-alias'
            keyPassword 'your-key-password'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}

# Build release bundle
cd android
./gradlew bundleRelease

# Output: android/app/build/outputs/bundle/release/app-release.aab

# Upload to Google Play Console:
# 1. Go to: https://play.google.com/console
# 2. Create new app
# 3. Upload AAB file
# 4. Fill in store listing
# 5. Submit for review
```

---

## Monitoring & Maintenance

### Application Monitoring

#### Setup Sentry for Error Tracking

```python
# In app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=settings.ENVIRONMENT,
)
```

#### Setup Application Performance Monitoring

```bash
# Install APM agent
pip install elastic-apm

# Configure in app/main.py
from elasticapm.contrib.fastapi import ElasticAPM, make_apm_client

apm = make_apm_client({
    'SERVICE_NAME': 'psychsync-api',
    'SERVER_URL': 'https://apm.psychsync.com:8200',
    'ENVIRONMENT': 'production',
})

app.add_middleware(ElasticAPM)
```

### Health Checks

Create `/app/scripts/health_check.sh`:

```bash
#!/bin/bash

# Check API health
API_HEALTH=$(curl -s https://api.psychsync.com/health | jq -r '.status')

if [ "$API_HEALTH" != "healthy" ]; then
    echo "CRITICAL: API health check failed"
    # Send alert to Slack/PagerDuty
    exit 1
fi

# Check database connectivity
DB_CHECK=$(psql -h db-psychsync.prod.psychsync.com -U user -d psychsync_prod -c "SELECT 1" 2>&1)

if [ $? -ne 0 ]; then
    echo "CRITICAL: Database connection failed"
    exit 1
fi

# Check Redis
REDIS_CHECK=$(redis-cli -h redis-psychsync.prod.psychsync.com PING)

if [ "$REDIS_CHECK" != "PONG" ]; then
    echo "WARNING: Redis not responding"
fi

echo "All health checks passed"
```

### Database Maintenance

```sql
-- Rebuild materialized views weekly
REFRESH MATERIALIZED VIEW CONCURRENTLY population_health_stats;

-- Update table statistics
ANALYZE clinical_assessments_extended;
ANALYZE crisis_alerts;
ANALYZE telehealth_sessions;

-- Check for table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum and reindex (run monthly during low traffic)
VACUUM ANALYZE clinical_assessments_extended;
REINDEX TABLE CONCURRENTLY clinical_assessments_extended;
```

---

## Rollback Procedures

### Backend Rollback

```bash
# If deployment fails, immediately rollback:

# 1. Revert to previous version
cd /app
git revert HEAD
pip install -r requirements.txt

# 2. Restart services
sudo systemctl restart psychsync-api

# 3. Verify health
curl https://api.psychsync.com/health

# 4. Check error logs
sudo journalctl -u psychsync-api --since "5 minutes ago" | tail -100
```

### Database Rollback

```bash
# If migration fails:

# 1. Identify current version
alembic current

# 2. Rollback to previous version
alembic downgrade -1

# 3. Verify data integrity
psql -h db-host -U user -d psychsync_prod -c "SELECT COUNT(*) FROM clinical_assessments_extended;"

# 4. If major corruption, restore from backup
pg_restore -h db-host -U user -d psychsync_prod /backups/psychsync_latest.dump
```

### Frontend Rollback

```bash
# Revert to previous frontend version:

# Option A: S3 rollback
aws s3 sync s3://psychsync-frontend-backup/ s3://psychsync-frontend-prod/ --delete
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"

# Option B: Server rollback
cd /var/www/psychsync
git revert HEAD
sudo systemctl reload nginx
```

---

## Post-Deployment Checklist

- [ ] All database migrations applied successfully
- [ ] Backend API responding on health endpoint
- [ ] Frontend loading without errors
- [ ] SSL certificates valid (check with: `openssl s_client -connect api.psychsync.com:443`)
- [ ] Authentication flow working (login, logout, token refresh)
- [ ] LSAS assessment submitting correctly
- [ ] EAT-26 assessment submitting correctly
- [ ] Y-BOCS assessment submitting correctly
- [ ] Crisis alerts being generated
- [ ] Analytics endpoints returning data
- [ ] Telehealth video sessions can be scheduled
- [ ] AI chatbot responding to messages
- [ ] Mobile apps can authenticate
- [ ] Error tracking (Sentry) receiving events
- [ ] APM dashboard showing metrics
- [ ] Database backups running successfully
- [ ] Monitoring alerts configured

---

## Support Contacts

**Technical Issues:**
- DevOps: devops@psychsync.com
- Backend Lead: backend-lead@psychsync.com
- Database Admin: dba@psychsync.com

**Clinical Issues:**
- Clinical Director: clinical-director@psychsync.com
- Crisis Response: oncall-clinician@psychsync.com

**Emergency Contacts:**
- On-Call Engineer: oncall@psychsync.com (PagerDuty)
- Crisis Hotline: 988

---

## Appendix: Configuration Files

### Alembic Production Config

```ini
# alembic.ini
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
sqlalchemy.url = postgresql+asyncpg://user:password@db-host:5432/psychsync_prod

[post_write_hooks]
# Format migration files with black
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 79 REVISION_SCRIPT_FILENAME

# Lint migration files
hooks = flake8
flake8.type = console_scripts
flake8.entrypoint = flake8
flake8.options = REVISION_SCRIPT_FILENAME
```

### Uvicorn Logging Config

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "default": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
      "datefmt": "%Y-%m-%d %H:%M:%S"
    },
    "access": {
      "format": "%(asctime)s - %(levelname)s - %(client)s - %(request_line)s - %(status_code)s",
      "datefmt": "%Y-%m-%d %H:%M:%S"
    }
  },
  "handlers": {
    "default": {
      "formatter": "default",
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "/var/log/psychsync/api.log",
      "maxBytes": 10485760,
      "backupCount": 10
    },
    "access": {
      "formatter": "access",
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "/var/log/psychsync/access.log",
      "maxBytes": 10485760,
      "backupCount": 10
    }
  },
  "loggers": {
    "": {
      "handlers": ["default"],
      "level": "INFO"
    },
    "uvicorn.access": {
      "handlers": ["access"],
      "level": "INFO",
      "propagate": false
    }
  }
}
```

---

**Document Version**: 1.0
**Last Updated**: 2024-01-20
**Maintained By**: DevOps Team
