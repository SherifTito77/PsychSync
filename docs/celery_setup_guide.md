# Celery Setup Guide for PsychSync

## Prerequisites

### 1. Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
Download from: https://github.com/microsoftarchive/redis/releases

Or use Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Verify Redis is Running
```bash
redis-cli ping
# Should return: PONG
```

## Installation

### 1. Install Python Dependencies
```bash
pip install celery[redis]==5.3.4
pip install kombu==5.3.4
pip install redis==5.0.1
```

### 2. Update requirements.txt
Add to your `requirements.txt`:
```txt
celery[redis]==5.3.4
kombu==5.3.4
redis==5.0.1
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and update these values:
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Update app/core/config.py

Add the Celery configuration from the artifact `celery_settings_additions` to your `Settings` class in `app/core/config.py`.

## Running Celery

### Option 1: Run Everything Separately (Development)

**Terminal 1 - FastAPI Server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
celery -A app.core.celery_worker.celery_app worker \
  --loglevel=info \
  -Q default,scoring,reports,notifications,maintenance
```

**Terminal 3 - Celery Beat (Scheduler):**
```bash
celery -A app.core.celery_worker.celery_app beat \
  --loglevel=info
```

### Option 2: Run Worker with Beat (Development)

**Terminal 1 - FastAPI Server:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 - Celery Worker + Beat:**
```bash
celery -A app.core.celery_worker.celery_app worker \
  --beat \
  --loglevel=info \
  -Q default,scoring,reports,notifications,maintenance
```

### Option 3: Use Process Manager (Production)

Create a `Procfile` or use supervisord:

**Procfile:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.core.celery_worker.celery_app worker --loglevel=info -Q default,scoring,reports,notifications,maintenance
beat: celery -A app.core.celery_worker.celery_app beat --loglevel=info
```

**supervisord.conf:**
```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A app.core.celery_worker.celery_app worker --loglevel=info -Q default,scoring,reports,notifications,maintenance
directory=/path/to/psychsync
user=your-user
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.error.log
autostart=true
autorestart=true
startsecs=10

[program:celery_beat]
command=/path/to/venv/bin/celery -A app.core.celery_worker.celery_app beat --loglevel=info
directory=/path/to/psychsync
user=your-user
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.error.log
autostart=true
autorestart=true
startsecs=10
```

## Verify Installation

### 1. Test Redis Connection
```bash
python -c "import redis; r = redis.Redis(host='localhost', port=6379); print(r.ping())"
# Should print: True
```

### 2. Test Celery Worker
```bash
# In one terminal, start worker
celery -A app.core.celery_worker.celery_app worker --loglevel=info

# In another terminal, test a task
python -c "from app.core.celery_worker import debug_task; result = debug_task.delay(); print(result.get())"
```

### 3. Check Celery Status
```bash
celery -A app.core.celery_worker.celery_app inspect active
celery -A app.core.celery_worker.celery_app inspect stats
```

## Monitoring

### Flower (Web-based Monitoring)

Install Flower:
```bash
pip install flower
```

Run Flower:
```bash
celery -A app.core.celery_worker.celery_app flower --port=5555
```

Access at: http://localhost:5555

## Troubleshooting

### Error: "Unable to load celery application"

**Solution:** Make sure you're in the project root and the import path is correct:
```bash
cd /path/to/psychsync
celery -A app.core.celery_worker.celery_app worker --loglevel=info
```

### Error: "Can't connect to Redis"

**Check if Redis is running:**
```bash
redis-cli ping
```

**Check Redis logs:**
```bash
# macOS
tail -f /usr/local/var/log/redis.log

# Linux
tail -f /var/log/redis/redis-server.log
```

**Restart Redis:**
```bash
# macOS
brew services restart redis

# Linux
sudo systemctl restart redis-server
```

### Error: "'settings' object has no attribute 'celery_broker_url'"

**Solution:** Add Celery configuration to `app/core/config.py` as shown in the setup guide.

### Tasks Not Executing

**Check worker is running:**
```bash
celery -A app.core.celery_worker.celery_app inspect active
```

**Check queue names:**
```bash
celery -A app.core.celery_worker.celery_app inspect active_queues
```

**Purge queues (development only):**
```bash
celery -A app.core.celery_worker.celery_app purge
```

## Task Management

### List All Registered Tasks
```bash
celery -A app.core.celery_worker.celery_app inspect registered
```

### View Active Tasks
```bash
celery -A app.core.celery_worker.celery_app inspect active
```

### View Scheduled Tasks (Beat)
```bash
celery -A app.core.celery_worker.celery_app inspect scheduled
```

### Revoke a Task
```python
from app.core.celery_worker import revoke_task
revoke_task('task-id-here', terminate=True)
```

## Production Deployment

### 1. Use Separate Redis Instance
```bash
# In .env
CELERY_BROKER_URL=redis://redis-server:6379/0
CELERY_RESULT_BACKEND=redis://redis-server:6379/1
```

### 2. Configure Worker Concurrency
```bash
celery -A app.core.celery_worker.celery_app worker \
  --concurrency=4 \
  --loglevel=info \
  -Q default,scoring,reports,notifications,maintenance
```

### 3. Use Multiple Workers for Different Queues
```bash
# Worker for high-priority tasks
celery -A app.core.celery_worker.celery_app worker \
  --concurrency=4 \
  -Q scoring,notifications \
  --loglevel=info

# Worker for background tasks
celery -A app.core.celery_worker.celery_app worker \
  --concurrency=2 \
  -Q reports,maintenance \
  --loglevel=info
```

### 4. Enable Result Backend Persistence
Already configured in `celery_worker.py`:
```python
result_persistent=True
result_expires=86400  # 24 hours
```

## Docker Setup (Optional)

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery_worker:
    build: .
    command: celery -A app.core.celery_worker.celery_app worker --loglevel=info -Q default,scoring,reports,notifications,maintenance
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - DATABASE_URL=${DATABASE_URL}

  celery_beat:
    build: .
    command: celery -A app.core.celery_worker.celery_app beat --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

volumes:
  redis_data:
```

## Next Steps

1. ✅ Install Redis and verify it's running
2. ✅ Install Celery dependencies
3. ✅ Configure environment variables
4. ✅ Update `app/core/config.py`
5. ✅ Start Celery worker
6. ✅ Start Celery beat (for scheduled tasks)
7. ✅ Test with a simple task
8. 🔄 Implement your custom tasks in `app/tasks/`
9. 🔄 Set up monitoring with Flower
10. 🔄 Configure for production deployment

## Useful Commands Reference

```bash
# Start worker
celery -A app.core.celery_worker.celery_app worker --loglevel=info -Q default,scoring,reports,notifications,maintenance

# Start beat (scheduler)
celery -A app.core.celery_worker.celery_app beat --loglevel=info

# Worker + Beat together (development)
celery -A app.core.celery_worker.celery_app worker --beat --loglevel=info

# Check status
celery -A app.core.celery_worker.celery_app inspect active

# Purge all queues (DANGER!)
celery -A app.core.celery_worker.celery_app purge

# Monitor with Flower
celery -A app.core.celery_worker.celery_app flower

# Test Redis
redis-cli ping
```
