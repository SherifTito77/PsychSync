# PsychSync Development Setup

This guide will help you set up PsychSync for local development on your machine.

## 🚀 Quick Start

### Option 1: Using the Automated Scripts (Recommended)

1. **Using Docker (if you have Docker installed):**
   ```bash
   ./start_dev.sh
   ```

2. **Using Local Services (if you have PostgreSQL and Redis installed locally):**
   ```bash
   ./start_dev_local.sh
   ```

3. **To stop all services:**
   ```bash
   ./stop_dev.sh
   ```

### Option 2: Manual Setup

## 📋 Prerequisites

- **Python 3.12+** with pip
- **Node.js 18+** with npm
- **PostgreSQL 15+** OR Docker
- **Redis** OR Docker
- **Git**

## 🗄️ Database Setup

### Using Docker (Easiest)

1. Start database services:
   ```bash
   docker compose up -d db redis
   ```

2. Wait for services to be ready (10-15 seconds)

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Using Local PostgreSQL/Redis

1. **Start PostgreSQL:**
   ```bash
   # macOS
   brew services start postgresql

   # Ubuntu
   sudo systemctl start postgresql
   ```

2. **Start Redis:**
   ```bash
   # macOS
   brew services start redis

   # Ubuntu
   sudo systemctl start redis
   ```

3. **Create database:**
   ```bash
   createdb -h localhost -p 5432 -U postgres psychsync_db
   ```

4. **Create database user:**
   ```bash
   psql -h localhost -p 5432 -U postgres -d psychsync_db -c "CREATE USER psychsync_user WITH PASSWORD 'password';"
   psql -h localhost -p 5432 -U postgres -d psychsync_db -c "GRANT ALL PRIVILEGES ON DATABASE psychsync_db TO psychsync_user;"
   psql -h localhost -p 5432 -U postgres -d psychsync_db -c "ALTER USER psychsync_user CREATEDB;"
   ```

5. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

## 🔧 Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.dev .env.local
   # Edit .env.local with your database credentials if needed
   ```

3. **Start the backend server:**
   ```bash
   PYTHONPATH=. python app/main.py
   ```

   Or with hot reload:
   ```bash
   PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🎨 Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   ```

4. **Start the frontend development server:**
   ```bash
   npm run dev
   ```

## 🌐 Accessing the Application

Once both servers are running:

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **ReDoc Documentation:** http://localhost:8000/redoc

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/api/test_auth.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui
```

## 🔍 Database Management

### Connecting to Database
```bash
# Using psql
psql -h localhost -p 5432 -U psychsync_user -d psychsync_db

# Using connection string
postgresql://psychsync_user:password@localhost:5432/psychsync_db
```

### Running Migrations
```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Rollback to previous migration
alembic downgrade -1
```

## 🛠️ Common Issues

### Backend Issues

1. **Database connection error:**
   - Ensure PostgreSQL is running
   - Check database credentials in .env file
   - Verify database was created

2. **Import errors:**
   ```bash
   export PYTHONPATH=.
   ```

3. **Port already in use:**
   ```bash
   # Kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

### Frontend Issues

1. **Port already in use:**
   ```bash
   # Kill process using port 5173
   lsof -ti:5173 | xargs kill -9
   ```

2. **Node modules issues:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

## 📁 Project Structure

```
psychsync/
├── app/                    # Backend application
│   ├── api/               # API routes
│   ├── core/              # Core configuration
│   ├── db/                # Database models
│   ├── services/          # Business logic
│   └── main.py           # FastAPI entry point
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── contexts/     # React contexts
│   └── package.json
├── alembic/               # Database migrations
├── docker-compose.yml     # Docker configuration
└── requirements.txt      # Python dependencies
```

## 🔄 Development Workflow

1. **Create a new feature branch**
2. **Make your changes**
3. **Run tests to ensure everything works**
4. **Commit your changes**
5. **Push to your branch and create a PR**

## 🚨 Security Notes

- Never commit secrets or API keys to git
- Use environment variables for sensitive configuration
- Change default passwords in production
- Review security best practices before deployment

## 📞 Getting Help

If you encounter issues:

1. Check the [Common Issues](#-common-issues) section above
2. Review the logs for error messages
3. Check the API documentation at `/docs`
4. Create an issue in the project repository

## 🎯 Next Steps

Once everything is running, you can:

1. Create a user account at http://localhost:5173/register
2. Log in and explore the dashboard
3. Check out the API documentation at http://localhost:8000/docs
4. Start building new features!