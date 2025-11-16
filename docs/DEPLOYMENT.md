# PsychSync Deployment Guide

## Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis (optional, for caching)
- Domain name
- SSL certificate

## Production Backend Setup

### 1. Server Preparation (Ubuntu 20.04+)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Database Setup
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE psychsync;
CREATE USER psychsync_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE psychsync TO psychsync_user;
\q
```

### 3. Backend Deployment
```bash
# Clone repository
git clone https://github.com/yourusername/psychsync.git
cd psychsync/app

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create production .env
cp .env.example .env.production
nano .env.production
```

**Production .env:**
```env
DATABASE_URL=postgresql://psychsync_user:your_secure_password@localhost/psychsync
JWT_SECRET_KEY=generate-a-secure-random-key-here
CORS_ORIGINS=["https://yourdomain.com"]
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
FRONTEND_URL=https://yourdomain.com
```
```bash
# Run migrations
python create_team_tables.py
python create_assessment_tables.py
python update_response_tables.py
python create_template_tables.py
python seed_templates.py

# Test gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Systemd Service

Create `/etc/systemd/system/psychsync.service`:
```ini
[Unit]
Description=PsychSync FastAPI Application
After=network.target

[Service]
User=your_user
Group=your_group
WorkingDirectory=/path/to/psychsync/app
Environment="PATH=/path/to/psychsync/app/.venv/bin"
ExecStart=/path/to/psychsync/app/.venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind unix:/tmp/psychsync.sock

[Install]
WantedBy=multi-user.target
```
```bash
# Enable and start service
sudo systemctl enable psychsync
sudo systemctl start psychsync
sudo systemctl status psychsync
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/psychsync`:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://unix:/tmp/psychsync.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/psychsync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

## Production Frontend Setup

### 1. Build Frontend
```bash
cd /path/to/psychsync/frontend

# Update environment
cp .env.example .env.production
nano .env.production
```

**Production .env:**
```env
VITE_API_URL=https://api.yourdomain.com/api/v1
```
```bash
# Install dependencies
npm install

# Build for production
npm run build
```

### 2. Deploy Static Files
```bash
# Copy build to web server
sudo cp -r dist/* /var/www/psychsync/
sudo chown -R www-data:www-data /var/www/psychsync
```

### 3. Nginx Configuration for Frontend

Create `/etc/nginx/sites-available/psychsync-frontend`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    root /var/www/psychsync;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/psychsync-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

## Docker Deployment (Alternative)

### 1. Backend Dockerfile

**File:** `app/Dockerfile`
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. Frontend Dockerfile

**File:** `frontend/Dockerfile`
```dockerfile
FROM node:16-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3. Docker Compose

**File:** `docker-compose.prod.yml`
```yaml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: psychsync
      POSTGRES_USER: psychsync_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./app
    environment:
      DATABASE_URL: postgresql://psychsync_user:${DB_PASSWORD}@db:5432/psychsync
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    depends_on:
      - db
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```
```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
