# PsychSync Production Deployment Guide

## Architecture: Vercel + AWS App Runner + Supabase + Upstash

```
Your Mac (git push only)
       │
       ▼
    GitHub ──────────────────────────────────────┐
       │                                         │
       │ (auto-deploy on push)                   │ (auto-deploy on push)
       ▼                                         ▼
  Vercel (Frontend)                    AWS App Runner (Backend)
  app.psychsync.com                    api.psychsync.com
       │                                         │
       │ HTTPS API calls                  ┌──────┼──────┐
       └─────────────────────────────────►│      │      │
                                          ▼      ▼      ▼
                                     Supabase  Upstash   S3
                                    (Postgres) (Redis) (Files)
```

**You do NOT need Docker on your machine.** Everything builds remotely.

---

## Prerequisites

On your Mac, you only need:
- Git
- Node.js 18+ (for frontend dev)
- Python 3.11+ (for backend dev)
- VS Code (or any editor)

Accounts needed:
- [GitHub](https://github.com) (you have this)
- [Vercel](https://vercel.com) — frontend hosting
- [AWS](https://aws.amazon.com) — backend hosting (App Runner)
- [Supabase](https://supabase.com) — managed PostgreSQL
- [Upstash](https://upstash.com) — serverless Redis

---

## Step 1: Supabase (PostgreSQL)

### 1.1 Create Project
1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose a region close to your users (e.g., `us-east-1`)
4. Set a strong database password — save it securely
5. Wait for project to provision (~2 minutes)

### 1.2 Get Connection String
1. Go to Project Settings → Database
2. Copy the **Connection string (URI)** under "Connection pooling" (port 6543)
3. Format for your FastAPI app:
   ```
   postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

### 1.3 Run Migrations
From your Mac (one-time setup):
```bash
# Install psycopg2 locally for Alembic
pip install psycopg2-binary alembic sqlalchemy

# Set the DATABASE_URL temporarily
export DATABASE_URL="postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"

# Run migrations
alembic upgrade head
```

### 1.4 Important Supabase Settings
- **Connection pooling**: Use port `6543` (PgBouncer) not `5432` (direct)
- **SSL**: Always enabled by default on Supabase
- **Pool size**: Supabase free = 60 connections; Pro = 200+. Set `DATABASE_POOL_SIZE=15` and `DATABASE_MAX_OVERFLOW=5` for App Runner to stay under limits.

---

## Step 2: Upstash (Redis)

### 2.1 Create Database
1. Go to [console.upstash.com](https://console.upstash.com)
2. Click "Create Database"
3. Choose the same region as Supabase
4. Enable TLS (default)
5. Copy the **Redis URL** (format: `rediss://default:[password]@[endpoint]:6379`)

### 2.2 Configuration Notes
- Upstash uses `rediss://` (with double-s) for TLS
- Free tier: 10,000 commands/day (enough for development)
- Pay-as-you-go: $0.2 per 100K commands (production)
- Your existing Redis code (`redis==5.0.1`) works with Upstash out of the box

---

## Step 3: AWS App Runner (Backend)

### 3.1 Initial Setup
1. Go to AWS Console → App Runner
2. Click "Create service"
3. Source: **Source code repository**
4. Connect to your GitHub repo
5. Branch: `main` (or your deploy branch)
6. Build settings: Choose "Use configuration file" → it reads `apprunner.yaml`

### 3.2 How It Works
- App Runner pulls your code from GitHub on every push to `main`
- It installs dependencies from `requirements-prod.txt`
- It starts your FastAPI app with the command in `apprunner.yaml`
- It auto-scales based on traffic (including scaling to 0 when idle)
- **No Docker needed** — App Runner builds from source

### 3.3 Environment Variables
In AWS App Runner console → Configuration → Environment variables, set:

```
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres
REDIS_URL=rediss://default:[pass]@[endpoint].upstash.io:6379
SECRET_KEY=[generate: python -c "import secrets; print(secrets.token_urlsafe(128))"]
ENCRYPTION_KEY=[generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"]
FRONTEND_URL=https://app.psychsync.com
ALLOWED_HOSTS=api.psychsync.com,*.awsapprunner.com
CORS_ORIGINS=https://app.psychsync.com
DB_SSL_MODE=require
DATABASE_POOL_SIZE=15
DATABASE_MAX_OVERFLOW=5
PORT=8000
WORKERS=2
```

### 3.4 Custom Domain
1. App Runner → Custom domains → Add domain
2. Add `api.psychsync.com`
3. Create the CNAME record in your DNS provider
4. SSL certificate is automatically provisioned

### 3.5 Scaling Configuration
In App Runner console (or via `apprunner.yaml`):
- **Min instances**: 1 (or 0 if you want scale-to-zero)
- **Max instances**: 10
- **Max concurrency**: 80 requests per instance
- **CPU**: 1 vCPU
- **Memory**: 2 GB

### 3.6 Cost Estimate
| Traffic | Approx. Cost |
|---------|-------------|
| Idle (scale to 0) | ~$0/mo |
| Low (1 instance always on) | ~$7-15/mo |
| Medium (2-3 instances) | ~$25-45/mo |
| High (5+ instances) | ~$60-100/mo |

---

## Step 4: Vercel (Frontend)

### 4.1 Connect Repository
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Set **Root Directory** to `frontend`
4. Framework Preset: **Vite** (auto-detected)
5. Build command: `npm run build`
6. Output directory: `dist`

### 4.2 Environment Variables
In Vercel Dashboard → Settings → Environment Variables:
```
VITE_API_URL=https://api.psychsync.com
VITE_APP_ENV=production
VITE_APP_NAME=PsychSync
```

Also create `frontend/.env.production` locally (safe to commit — no secrets):
```bash
echo 'VITE_API_URL=https://api.psychsync.com
VITE_APP_ENV=production
VITE_APP_NAME=PsychSync' > frontend/.env.production
```

### 4.3 Custom Domain
1. Vercel → Domains → Add
2. Add `app.psychsync.com`
3. Configure DNS (A record or CNAME as Vercel instructs)

### 4.4 Configuration
The `vercel.json` in `frontend/` handles:
- SPA routing (all paths → `index.html`)
- Security headers
- API rewrites (optional fallback)

### 4.5 Cost
- **Hobby (personal)**: $0/mo — non-commercial only
- **Pro (commercial)**: $20/mo — recommended for SaaS launch

---

## Step 5: CI/CD Flow

### How Deployments Work

```
git push to main
       │
       ├──► Vercel auto-deploys frontend (30-60s)
       │
       └──► AWS App Runner auto-deploys backend (2-5min)
            - Installs Python dependencies
            - Starts uvicorn
            - Health check passes → traffic switches
            - Old instance drains connections
```

### GitHub Actions (Optional Enhancement)
Your existing CI workflows (security scans, tests) still run. Add a step to only deploy if tests pass:

```yaml
# In .github/workflows/cicd-pipeline.yaml, the existing pipeline
# already runs tests. App Runner watches the branch directly,
# so protect `main` with branch protection rules requiring
# CI to pass before merge.
```

### Recommended Branch Strategy
```
feature/* → PR → main (protected: require CI pass)
                   │
                   ├──► Vercel deploys preview on PR
                   └──► App Runner deploys on merge to main
```

---

## Step 6: DNS & SSL

### DNS Records (at your domain registrar)

| Type | Name | Value |
|------|------|-------|
| CNAME | `app` | `cname.vercel-dns.com` |
| CNAME | `api` | `[your-service].awsapprunner.com` |

SSL is automatic on both Vercel and App Runner.

---

## Step 7: Local Development

You develop locally without Docker:

```bash
# Terminal 1: Backend
cd /Users/sheriftito/Downloads/psychsync
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/psychsync"
export REDIS_URL="redis://localhost:6379"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

For local PostgreSQL + Redis (via Homebrew):
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
createdb psychsync
```

Or connect to your Supabase instance directly for development:
```bash
export DATABASE_URL="postgresql+asyncpg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres"
```

---

## Step 8: Database Backups

### Supabase Free Tier
- No automatic backups — do manual exports:
  ```bash
  pg_dump "postgresql://..." > backup_$(date +%Y%m%d).sql
  ```

### Supabase Pro ($25/mo)
- Daily automatic backups, 7-day retention
- Point-in-time recovery (PITR) on higher plans

### Recommended: Add S3 backup script
```bash
# Run weekly from your Mac or a GitHub Action
pg_dump "$DATABASE_URL" | gzip | aws s3 cp - s3://psychsync-backups/$(date +%Y%m%d).sql.gz
```

---

## Troubleshooting

### App Runner build fails
- Check `requirements.txt` has no OS-specific packages that need compilation
- `torch` and ML libraries are large — consider a separate `requirements-prod.txt` without them if not needed in production API
- App Runner has a 3GB image size limit

### Supabase connection errors
- Use port `6543` (pooler), not `5432`
- Ensure `DATABASE_POOL_SIZE` ≤ 15 to avoid exhausting pool
- Check if project is paused (free tier pauses after 1 week inactivity)

### Vercel 404 on refresh
- Ensure `vercel.json` has the SPA rewrite rule (`"destination": "/index.html"`)

### CORS errors
- Set `CORS_ORIGINS=https://app.psychsync.com` in App Runner env vars
- Include `FRONTEND_URL=https://app.psychsync.com`

### Redis connection timeout
- Upstash uses `rediss://` (TLS) — make sure URL has double-s
- If using `redis==5.0.1`, TLS works automatically with the `rediss://` scheme

---

## Cost Summary

### Development/Testing (can be $0)
| Service | Plan | Cost |
|---------|------|------|
| Vercel | Hobby | $0 |
| AWS App Runner | Scale to 0 | ~$0 |
| Supabase | Free | $0 |
| Upstash | Free | $0 |
| **Total** | | **~$0** |

### Early Production (first users)
| Service | Plan | Cost |
|---------|------|------|
| Vercel | Pro | $20/mo |
| AWS App Runner | 1 instance | ~$15/mo |
| Supabase | Pro | $25/mo |
| Upstash | Pay-as-you-go | ~$5/mo |
| **Total** | | **~$65/mo** |

### Growing SaaS
| Service | Plan | Cost |
|---------|------|------|
| Vercel | Pro | $20/mo |
| AWS App Runner | 3-5 instances | ~$50-80/mo |
| Supabase | Pro (scaled) | $25-100/mo |
| Upstash | Pro | $10-30/mo |
| **Total** | | **~$100-230/mo** |

---

## Migration Path

When PsychSync outgrows this setup:

1. **More compute** → increase App Runner instances (max 25)
2. **More database** → Supabase compute add-ons or migrate to AWS RDS
3. **Background jobs** → Add AWS SQS + Lambda workers
4. **Full orchestration** → Move to ECS Fargate or EKS (use existing K8s manifests)
5. **Multi-region** → Add CloudFront CDN in front of App Runner

The code doesn't change — only infrastructure configuration.
