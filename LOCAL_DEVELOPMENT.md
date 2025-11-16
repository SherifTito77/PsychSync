# PsychSync Local Development Guide

This guide covers setting up PsychSync for local development without Docker using free tools.

## 🚀 Quick Start

### Prerequisites
- macOS (or Linux with equivalent package managers)
- Homebrew (for macOS)
- Python 3.8+
- Node.js 16+
- PostgreSQL 14+
- Redis 6+

### Initial Setup

```bash
# 1. Install dependencies (if not already installed)
brew install postgresql@14 redis python@3.9 node

# 2. Start services
brew services start postgresql@14
brew services start redis

# 3. Set up the development environment
./scripts/start-dev.sh

# 4. Initialize database with seed data
./scripts/init-database.sh

# 5. Start full development environment
./scripts/start-full-dev.sh
```

## 📁 Development Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `start-dev.sh` | Initial environment setup and service checks | `./scripts/start-dev.sh` |
| `start-full-dev.sh` | Start both frontend and backend | `./scripts/start-full-dev.sh` |
| `start-dev-https.sh` | Start with HTTPS support | `./scripts/start-dev-https.sh` |
| `db-manage.sh` | Database operations | `./scripts/db-manage.sh [command]` |
| `init-database.sh` | Initialize database with seed data | `./scripts/init-database.sh` |
| `setup-localhost-ssl.sh` | Generate SSL certificates | `./scripts/setup-localhost-ssl.sh` |

## 🗄️ Database Management

### Database Commands
```bash
# Show database info
./scripts/db-manage.sh info

# Reset database (delete all data)
./scripts/db-manage.sh reset

# Create backup
./scripts/db-manage.sh backup

# Restore from backup
./scripts/db-manage.sh restore

# Connect with psql
./scripts/db-manage.sh connect

# Run migrations
./scripts/db-manage.sh migrate
```

### Database Credentials
- **Database**: `psychsync_db`
- **User**: `psychsync_user`
- **Password**: `password`
- **Host**: `localhost`
- **Port**: `5432`

### Development User
- **Email**: `dev@psychsync.com`
- **Password**: `dev123456`

## 🔧 Environment Configuration

### Backend Environment Files
- `.env.localhost` - Local development configuration
- `.env.dev` - Docker development configuration
- `.env.prod` - Production configuration

### Frontend Environment Files
- `frontend/.env.localhost` - Local development
- `frontend/.env.example` - Example configuration

### Using Custom Environment
```bash
# Backend
export ENV_FILE=.env.localhost
source .venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
cp .env.localhost .env.local
npm run dev
```

## 🌐 Development URLs

| Service | HTTP | HTTPS |
|---------|------|-------|
| Frontend | http://localhost:5173 | http://localhost:5173 |
| Backend API | http://localhost:8000 | https://localhost:8000 |
| API Documentation | http://localhost:8000/docs | https://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc | https://localhost:8000/redoc |

## 🔒 HTTPS Setup

For HTTPS development:
```bash
# Setup SSL certificates
./scripts/setup-localhost-ssl.sh

# Start with HTTPS
./scripts/start-dev-https.sh
```

**Note**: You'll need to trust the self-signed certificate in your browser or system keychain.

## 📊 Service Status

### Check Services
```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Redis
redis-cli ping

# Both services
./scripts/start-dev.sh  # This will check and start if needed
```

### Service Management
```bash
# Start/Stop PostgreSQL
brew services start postgresql@14
brew services stop postgresql@14

# Start/Stop Redis
brew services start redis
brew services stop redis
```

## 🧪 Development Workflow

### 1. Daily Development
```bash
# Start services (they may already be running)
./scripts/start-full-dev.sh

# Work on your code...
# The backend and frontend will auto-reload on changes
```

### 2. Database Changes
```bash
# After making model changes, create migration
./scripts/db-manage.sh migration
# Enter migration description when prompted

# Apply migrations
./scripts/db-manage.sh migrate
```

### 3. Testing
```bash
# Backend tests
cd /path/to/psychsync
source .venv/bin/activate
pytest tests/ -v

# Frontend tests
cd frontend
npm run test
```

### 4. Code Quality
```bash
# Backend type checking
cd /path/to/psychsync
source .venv/bin/activate
mypy app/

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

## 🛠️ Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@14

# Check database exists
psql -U psychsync_user -d psychsync_db -c "SELECT 1;"
```

#### Redis Connection Issues
```bash
# Check Redis status
brew services list | grep redis

# Restart Redis
brew services restart redis

# Test connection
redis-cli ping
```

#### Backend Won't Start
```bash
# Check virtual environment
source .venv/bin/activate
pip install -r requirements.txt

# Check database migrations
alembic upgrade head

# Check environment variables
cat .env.localhost
```

### Log Files
- Backend logs: Console output when running `uvicorn`
- Frontend logs: Browser developer tools console
- Database logs: `brew services list` shows log file locations

## 🔍 Debug Mode

### Enable Debug Logging
```bash
# Backend
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload

# Frontend
cd frontend
echo "VITE_ENABLE_DEBUG_MODE=true" >> .env.local
npm run dev
```

### SQL Query Debugging
In `.env.localhost`:
```
DB_ECHO=True
SQL_ECHO=True
```

## 📚 Development Resources

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database Schema
```bash
# Connect to database
./scripts/db-manage.sh connect

# List tables
\dt

# Describe table
\d users
```

### Frontend Development
- React Developer Tools (Chrome extension)
- Redux DevTools (if using Redux)
- Network tab in browser for API debugging

## 🚀 Production Deployment

While this setup is for development, the same configuration can be adapted for production by:

1. Using production environment files (`.env.prod`)
2. Setting up proper SSL certificates
3. Configuring production database
4. Setting up production Redis
5. Using a process manager like `systemd` or `pm2`

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Look at the logs for error messages
3. Ensure all services are running
4. Verify environment configuration
5. Check that ports are not already in use