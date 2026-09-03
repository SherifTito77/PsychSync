# Zero-Downtime Deployment Strategy for PsychSync

## Executive Summary
This document outlines a comprehensive zero-downtime deployment strategy enabling continuous updates to PsychSync without service interruption.

---

## Table of Contents
1. [Deployment Architecture](#deployment-architecture)
2. [Blue-Green Deployment](#blue-green-deployment)
3. [Rolling Updates](#rolling-updates)
4. [Database Migrations](#database-migrations)
5. [Frontend Deployment](#frontend-deployment)
6. [Automation & CI/CD](#automation--cicd)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring & Validation](#monitoring--validation)

---

## Deployment Architecture

### Current Infrastructure
```
                    ┌─────────────┐
                    │   Load      │
                    │  Balancer   │
                    │   (Nginx)   │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────▼──────┐       ┌──────▼──────┐
         │   Server 1  │       │   Server 2  │
         │ (Primary)   │       │ (Standby)   │
         └─────────────┘       └─────────────┘
                │                     │
         ┌──────▼──────┐       ┌──────▼──────┐
         │   FastAPI   │       │   FastAPI   │
         │   (uvicorn) │       │   (uvicorn) │
         └──────┬──────┘       └──────┬──────┘
                │                     │
         ┌──────▼──────┐       ┌──────▼──────┐
         │ PostgreSQL  │◄─────►│ PostgreSQL  │
         │  (Primary)  │       │  (Replica)  │
         └─────────────┘       └─────────────┘
```

### Production Architecture
```
                    ┌─────────────┐
                    │    CDN      │
                    │ (Cloudflare)│
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │   Load Balancer     │
                │    (AWS ALB)        │
                │   / GCP Load Bl.    │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │ Pod A   │      │ Pod B   │      │ Pod C   │
   │(v1.0)   │      │(v1.1)   │      │(v1.0)   │
   └────┬────┘      └────┬────┘      └────┬────┘
        │                 │                  │
        └─────────────────┴──────────────────┘
                            │
                    ┌───────▼───────┐
                    │  Shared DB    │
                    │  (Primary +   │
                    │   Replicas)   │
                    └───────────────┘
```

---

## Blue-Green Deployment

### Strategy Overview
Maintain two identical production environments (Blue and Green). Deploy to the inactive environment, test, then switch traffic.

### Implementation

#### 1. Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Blue Environment (Current Production)
  backend-blue:
    image: psychsync-backend:${IMAGE_TAG:-latest}
    container_name: psychsync-backend-blue
    environment:
      - ENVIRONMENT=production
      - DEPLOYMENT_COLOR=blue
    networks:
      - psychsync-blue
    ports:
      - "8001:8000"

  frontend-blue:
    image: psychsync-frontend:${IMAGE_TAG:-latest}
    container_name: psychsync-frontend-blue
    environment:
      - VITE_API_URL=https://api.psychsync.com
    networks:
      - psychsync-blue
    ports:
      - "3001:80"

  # Green Environment (New Deployment)
  backend-green:
    image: psychsync-backend:${IMAGE_TAG:-latest}
    container_name: psychsync-backend-green
    environment:
      - ENVIRONMENT=production
      - DEPLOYMENT_COLOR=green
    networks:
      - psychsync-green
    ports:
      - "8002:8000"

  frontend-green:
    image: psychsync-frontend:${IMAGE_TAG:-latest}
    container_name: psychsync-frontend-green
    environment:
      - VITE_API_URL=https://api.psychsync.com
    networks:
      - psychsync-green
    ports:
      - "3002:80"

networks:
  psychsync-blue:
  psychsync-green:
```

#### 2. Nginx Load Balancer Configuration
```nginx
# /etc/nginx/conf.d/psychswitch.conf
upstream psychsync_backend {
    # Blue environment
    server localhost:8001 max_fails=3 fail_timeout=30s;
    # Green environment (commented out when not in use)
    # server localhost:8002 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.psychsync.com;

    ssl_certificate /etc/ssl/certs/psychsync.crt;
    ssl_certificate_key /etc/ssl/private/psychsync.key;

    location / {
        proxy_pass http://psychsync_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health check endpoint
        proxy_next_upstream error timeout http_502;
    }
}
```

#### 3. Deployment Script
```bash
#!/bin/bash
# scripts/deploy-blue-green.sh

set -e

COLOR=${1:-"green"}
IMAGE_TAG=${2:-"latest"}

echo "🚀 Starting Blue-Green Deployment to $COLOR environment"

# Step 1: Pull latest images
echo "📦 Pulling latest images..."
docker-compose pull

# Step 2: Deploy to inactive environment
echo "🔧 Deploying to $COLOR environment..."
docker-compose up -d backend-$COLOR frontend-$COLOR

# Step 3: Wait for containers to be healthy
echo "⏳ Waiting for containers to be healthy..."
sleep 30

# Step 4: Run smoke tests against new deployment
echo "🧪 Running smoke tests..."
./scripts/smoke-test.sh http://localhost:800$([ "$COLOR" == "green" ] && echo "2" || echo "1")

# Step 5: Update Nginx configuration
echo "🔄 Switching traffic to $COLOR environment..."
if [ "$COLOR" == "green" ]; then
    sed -i 's/server localhost:8001/# server localhost:8001/' /etc/nginx/conf.d/psychswitch.conf
    sed -i 's/# server localhost:8002/server localhost:8002/' /etc/nginx/conf.d/psychswitch.conf
else
    sed -i 's/# server localhost:8001/server localhost:8001/' /etc/nginx/conf.d/psychswitch.conf
    sed -i 's/server localhost:8002/# server localhost:8002/' /etc/nginx/conf.d/psychswitch.conf
fi

# Step 6: Reload Nginx
nginx -t && nginx -s reload

# Step 7: Monitor for errors
echo "📊 Monitoring for errors..."
sleep 60

# Check error rates
ERROR_COUNT=$(curl -s http://localhost:8000/health | jq .errors)
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "❌ High error rate detected! Rolling back..."
    ./scripts/rollback-blue-green.sh $COLOR
    exit 1
fi

# Step 8: Keep old environment running for 15 minutes (quick rollback)
echo "✅ Deployment successful! Old environment will remain for 15 minutes."
sleep 900

# Step 9: Shut down old environment
echo "🧹 Cleaning up old environment..."
if [ "$COLOR" == "green" ]; then
    docker-compose stop backend-blue frontend-blue
else
    docker-compose stop backend-green frontend-green
fi

echo "✨ Deployment complete!"
```

---

## Rolling Updates

### Strategy Overview
Gradually replace instances with new versions, maintaining service availability throughout.

### Kubernetes RollingUpdate Configuration
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: psychsync-backend
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1   # Never have more than 1 pod down
      maxSurge: 1         # Create 1 extra pod during update
  selector:
    matchLabels:
      app: psychsync-backend
  template:
    metadata:
      labels:
        app: psychsync-backend
        version: v1.1.0
    spec:
      containers:
      - name: backend
        image: psychsync/backend:v1.1.0
        ports:
        - containerPort: 8000
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Manual Rolling Update Script
```bash
#!/bin/bash
# scripts/rolling-update.sh

INSTANCES=("server1" "server2" "server3" "server4")
NEW_VERSION=$1

for instance in "${INSTANCES[@]}"; do
    echo "🔄 Updating $instance..."

    # Step 1: Remove instance from load balancer
    kubectl patch pod $instance -p '{"metadata":{"annotations":{"consul.hashicorp.com/service-unregister":"true"}}}'

    # Step 2: Wait for active connections to drain (60 seconds)
    echo "⏳ Draining connections from $instance..."
    sleep 60

    # Step 3: Deploy new version
    kubectl set image deployment/$instance backend=psychsync/backend:$NEW_VERSION

    # Step 4: Wait for readiness
    kubectl wait --for=condition=ready pod/$instance --timeout=120s

    # Step 5: Add back to load balancer
    kubectl patch pod $instance -p '{"metadata":{"annotations":{"consul.hashicorp.com/service-unregister":"false"}}}'

    # Step 6: Run health check
    curl -f http://$instance/health || {
        echo "❌ Health check failed for $instance!"
        exit 1
    }

    echo "✅ $instance updated successfully"
    sleep 30  # Stagger deployments
done

echo "✨ All instances updated!"
```

---

## Database Migrations

### Strategy: Expand and Contract Pattern

#### 1. Backward-Compatible Migrations
```python
from alembic import op
import sqlalchemy as sa

# Step 1: Add new column (nullable)
def upgrade():
    op.add_column('users',
        sa.Column('new_feature_enabled',
                  sa.Boolean(),
                  nullable=True)  # Start nullable!
    )

# Step 2: Deploy code that reads/writes both old and new
# Deploy application code here

# Step 3: Backfill data
def upgrade():
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    # Backfill new column based on existing data
    session.execute(
        "UPDATE users SET new_feature_enabled = true WHERE subscription_tier = 'premium'"
    )
    session.commit()

# Step 4: Make column non-nullable
def upgrade():
    op.alter_column('users',
        'new_feature_enabled',
        nullable=False)

# Step 5: Remove old column/tables (after all servers updated)
def downgrade():
    op.drop_column('users', 'old_field')
```

#### 2. Zero-Downtime Migration Script
```python
# scripts/migrate.py
import asyncio
from psycopg2 import OperationalError
from app.core.database import get_db
from alembic.config import Config
from alembic import command

async def run_migration_with_checkpoints(migration_revision: str):
    """
    Run migration in small batches with checkpoints.
    Allows rollback if issues arise.
    """

    # Check current database state
    current_revision = await get_current_revision()
    print(f"Current revision: {current_revision}")

    # Create checkpoint (backup)
    checkpoint_name = f"pre_migration_{migration_revision}"
    await create_checkpoint(checkpoint_name)

    try:
        # Step 1: Apply migration to test schema first
        await apply_migration_to_test_schema(migration_revision)
        print("✅ Migration applied to test schema")

        # Step 2: Run data validation
        validation_errors = await validate_migration()
        if validation_errors:
            raise Exception(f"Validation failed: {validation_errors}")

        # Step 3: Apply to production (with 5% traffic sampling)
        await enable_feature_flag(migration_revision, percentage=5)
        await asyncio.sleep(300)  # Monitor for 5 minutes

        # Step 4: Gradual rollout
        for percentage in [10, 25, 50, 75, 100]:
            await enable_feature_flag(migration_revision, percentage=percentage)
            await asyncio.sleep(300)  # Monitor each step

        # Step 5: Mark migration complete
        await mark_migration_complete(migration_revision)
        print("✅ Migration complete!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        await rollback_to_checkpoint(checkpoint_name)
        raise
```

#### 3. Data Migration with Batch Processing
```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

async def migrate_large_table(batch_size: int = 1000):
    """
    Migrate large tables in batches to avoid locking.
    """
    async for db in get_db():
        offset = 0
        total_processed = 0

        while True:
            # Process batch
            result = await db.execute(
                f"SELECT id FROM large_table LIMIT {batch_size} OFFSET {offset}"
            )
            rows = result.fetchall()

            if not rows:
                break

            # Process this batch
            for row in rows:
                # Transform and insert new data
                await process_row(row.id)

            total_processed += len(rows)
            offset += batch_size

            print(f"Processed {total_processed} rows")

            # Commit after each batch
            await db.commit()

            # Small sleep to avoid overwhelming database
            await asyncio.sleep(0.1)
```

---

## Frontend Deployment

### Strategy: Asset Versioning & Cache Invalidation

#### 1. Build with Asset Hashing
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    // Generate hashed filenames
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name]-[hash].js`,
        chunkFileNames: `assets/[name]-[hash].js`,
        assetFileNames: `assets/[name]-[hash].[ext]`
      }
    },
    // Generate manifest for version lookup
    manifest: true,
  }
})
```

#### 2. CDN Deployment with Cache Control
```bash
#!/bin/bash
# scripts/deploy-frontend.sh

# Build frontend
cd frontend
npm run build

# Upload to CDN with cache headers
aws s3 sync dist/ s3://psychsync-frontend/ \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.json"

# Upload index.html with short cache
aws s3 sync dist/ s3://psychsync-frontend/ \
    --include "index.html" \
    --include "*.json" \
    --cache-control "public, max-age=300"

# Invalidate CDN cache
aws cloudfront create-invalidation \
    --distribution-id E1234567890 \
    --paths "/*"

echo "✅ Frontend deployed!"
```

---

## Automation & CI/CD

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Zero-Downtime Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:

      - name: Checkout code
        uses: actions/checkout@v3

      - name: Run tests
        run: |
          pytest tests/ -v --cov=app
          npm run test --prefix frontend

      - name: Build Docker images
        run: |
          docker build -t psychsync-backend:${{ github.sha }} .
          docker tag psychsync-backend:${{ github.sha }} psychsync-backend:latest

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push psychsync-backend:${{ github.sha }}
          docker push psychsync-backend:latest

      - name: Run database migrations
        run: |
          kubectl exec -it deployment/psychsync-backend -- alembic upgrade head

      - name: Blue-Green Deployment
        run: |
          ./scripts/deploy-blue-green.sh green ${{ github.sha }}

      - name: Smoke tests
        run: ./scripts/smoke-test.sh https://api.psychsync.com

      - name: Rollback on failure
        if: failure()
        run: ./scripts/rollback-blue-green.sh green
```

---

## Rollback Procedures

### Automated Rollback Script
```bash
#!/bin/bash
# scripts/rollback.sh

DEPLOYMENT_ID=$1

echo "🔄 Rolling back deployment $DEPLOYMENT_ID..."

# Step 1: Switch traffic back to previous version
if [ "$DEPLOYMENT_ID" == "green" ]; then
    sed -i 's/server localhost:8002/# server localhost:8002/' /etc/nginx/conf.d/psychswitch.conf
    sed -i 's/# server localhost:8001/server localhost:8001/' /etc/nginx/conf.d/psychswitch.conf
else
    sed -i 's/server localhost:8001/# server localhost:8001/' /etc/nginx/conf.d/psychswitch.conf
    sed -i 's/# server localhost:8002/server localhost:8002/' /etc/nginx/conf.d/psychswitch.conf
fi

nginx -s reload

# Step 2: Rollback database migrations
CURRENT_REVISION=$(alembic current)
alembic downgrade ${CURRENT_REVISION%?}

# Step 3: Restore previous frontend version
aws s3 cp s3://psychsync-backups/frontend/$PREVIOUS_SHA/ /var/www/html/ --recursive

echo "✅ Rollback complete!"
```

---

## Monitoring & Validation

### Health Check Endpoints
```python
from fastapi import APIRouter
from app.core.database import SessionLocal

router = APIRouter()

@router.get("/health/liveness")
async def liveness():
    """Check if the service is running"""
    return {"status": "alive"}

@router.get("/health/readiness")
async def readiness():
    """Check if the service can handle traffic"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}

@router.get("/health/deep")
async def deep_health_check():
    """Comprehensive health check"""
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "external_apis": await check_external_apis(),
        "disk_space": await check_disk_space(),
    }

    all_healthy = all(check["healthy"] for check in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks
    }
```

### Deployment Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

deployment_duration = Histogram(
    'deployment_duration_seconds',
    'Time taken for deployment',
    ['environment', 'status']
)

deployment_success = Counter(
    'deployment_success_total',
    'Total successful deployments',
    ['environment']
)

deployment_rollback = Counter(
    'deployment_rollback_total',
    'Total rollbacks',
    ['environment', 'reason']
)

current_version = Gauge(
    'deployment_version',
    'Current deployed version',
    ['service', 'environment']
)
```

---

## Summary

### Key Strategies
1. **Blue-Green Deployment**: Complete environment switch
2. **Rolling Updates**: Gradual instance replacement
3. **Expand/Contract Migrations**: Backward-compatible database changes
4. **Asset Versioning**: Cache-busting frontend builds
5. **Automated Rollback**: Quick recovery on failure

### Success Metrics
- **Uptime**: 99.9%+ during deployments
- **Deployment Time**: < 10 minutes
- **Rollback Time**: < 2 minutes
- **Data Loss**: Zero data loss
- **Error Rate**: < 0.1% during deployment

---

**Status**: ✅ Complete
**Next**: Migration Rollback Strategy
