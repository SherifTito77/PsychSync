# 🚀 **Production Deployment Guide**

<div align="center">

![PsychSync Deployment](https://img.shields.io/badge/Deployment-Ready-green?style=for-the-badge&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Supported-blue?style=for-the-badge&logo=kubernetes)
![AWS](https://img.shields.io/badge/AWS-Compatible-orange?style=for-the-badge&logo=amazon-aws)
![Production](https://img.shields.io/badge/Production-Grade-brightgreen?style=for-the-badge)

**Complete guide for deploying PsychSync AI to production with 1000% performance optimization**

[🐳 Docker](#-docker-deployment) • [☁️ Cloud](#️-cloud-deployment) • [🔧 Configuration](#-environment-configuration) • [📊 Monitoring](#-monitoring-and-logging)

</div>

---

## **🎯 Overview**

This comprehensive deployment guide covers everything you need to deploy PsychSync AI to production environments, from single-server deployments to enterprise-scale Kubernetes clusters with **1000% performance optimization**.

### **🌟 Deployment Options**
- **Docker Compose**: Quick single-server deployment with zero-downtime updates
- **Kubernetes**: Scalable container orchestration with auto-scaling
- **Cloud Platforms**: AWS, GCP, Azure managed services with serverless options
- **On-Premise**: Private data center deployment with air-gapped support

### **💡 Production Features**
- **High Availability**: Multi-replica deployment with intelligent load balancing
- **Auto-Scaling**: Dynamic resource allocation based on real-time demand
- **Zero Downtime**: Rolling updates and blue-green deployments
- **1000% Performance**: Advanced caching, optimization, and monitoring
- **Enterprise Security**: Military-grade security with comprehensive audit trails

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [SSL Certificate Setup](#ssl-certificate-setup)
4. [Deployment Process](#deployment-process)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Backup and Recovery](#backup-and-recovery)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or CentOS 8+
- **CPU**: Minimum 4 cores, recommended 8+ cores
- **Memory**: Minimum 16GB RAM, recommended 32GB+
- **Storage**: Minimum 100GB SSD, recommended 500GB+ SSD
- **Network**: Stable internet connection with static IP

### Software Dependencies

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx htop
```

## Environment Configuration

### 1. Copy Environment Template

```bash
cp .env.production.example .env.production
```

### 2. Configure Required Variables

Edit `.env.production` and update the following critical variables:

```bash
# Security
SECRET_KEY=your-super-secret-key-min-32-characters
DATABASE_PASSWORD=your-secure-db-password
REDIS_PASSWORD=your-redis-password

# Database
DATABASE_URL=postgresql+asyncpg://psychsync_user:YOUR_DB_PASSWORD@db:5432/psychsync_prod

# Email
SMTP_USER=notifications@psychsync.com
SMTP_PASSWORD=your-app-password

# Stripe
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
GRAFANA_ADMIN_PASSWORD=your-grafana-password
```

### 3. AWS Configuration (for backups)

```bash
# AWS S3 for backups
BACKUP_S3_BUCKET=psychsync-backups
BACKUP_S3_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot --nginx -d app.psychsync.com -d api.psychsync.com -d www.psychsync.com

# Copy certificates to project directory
sudo cp /etc/letsencrypt/live/app.psychsync.com/fullchain.pem docker-compose/production/nginx/ssl/psychsync.com.crt
sudo cp /etc/letsencrypt/live/app.psychsync.com/privkey.pem docker-compose/production/nginx/ssl/psychsync.com.key
sudo cp /etc/letsencrypt/live/app.psychsync.com/chain.pem docker-compose/production/nginx/ssl/psychsync.com.chain.crt
```

### Option 2: Custom SSL Certificates

Place your SSL certificates in:
```
docker-compose/production/nginx/ssl/
├── psychsync.com.crt
├── psychsync.com.key
└── psychsync.com.chain.crt
```

## Deployment Process

### 1. Initial Deployment

```bash
# Navigate to production directory
cd docker-compose/production

# Create necessary directories
mkdir -p nginx/ssl logs backups monitoring/grafana/dashboards monitoring/grafana/datasources

# Deploy the application
sudo ../../deployment/deploy.sh deploy
```

### 2. Deployment Script Features

The deployment script (`deployment/deploy.sh`) provides:

- **Prerequisites checking**: Validates Docker, files, and certificates
- **Automated backup**: Creates database and volume backups
- **Zero-downtime deployment**: Rolling updates with health checks
- **Rollback capability**: Quick rollback to previous version
- **Health monitoring**: Post-deployment health verification

### 3. Available Commands

```bash
# Deploy new version
sudo ./deployment/deploy.sh deploy

# Rollback to previous version
sudo ./deployment/deploy.sh rollback

# Run health checks
sudo ./deployment/deploy.sh health-check
```

## Monitoring and Logging

### 1. Application Monitoring

Access monitoring dashboards:

- **Grafana**: `https://app.psychsync.com:3001` (admin / your-grafana-password)
- **Prometheus**: `https://app.psychsync.com:9090`
- **Kibana**: `https://app.psychsync.com:5601`

### 2. Key Metrics to Monitor

- **Application Performance**:
  - Response times (API endpoints)
  - Error rates (4xx, 5xx)
  - Request throughput
  - Database query performance

- **Infrastructure**:
  - CPU and memory usage
  - Disk I/O and storage
  - Network traffic
  - Docker container health

- **Business Metrics**:
  - User registration rates
  - Assessment completion rates
  - Team optimization usage
  - Billing events

### 3. Alert Configuration

Configure alerts in Grafana for:

- High error rates (>5%)
- Slow response times (>2 seconds)
- Database connection failures
- Disk space usage (>80%)
- Memory usage (>90%)

## Backup and Recovery

### 1. Automated Backups

The system includes automated daily backups:

- **Database backups**: Compressed SQL dumps uploaded to S3
- **Volume backups**: Docker volumes backed up locally
- **Retention policy**: 30 days retention (configurable)

### 2. Manual Backup

```bash
# Create manual database backup
docker-compose exec backend python -m alembic backup

# Upload backup to S3
aws s3 cp backups/ s3://psychsync-backups/database/ --recursive
```

### 3. Recovery Process

```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d db
sleep 10
docker-compose exec -T db psql -U psychsync_user -d psychsync_prod < backup-file.sql

# Start all services
docker-compose up -d
```

## Security Considerations

### 1. Network Security

- **Firewall**: Configure UFW to only allow necessary ports
```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

- **Fail2Ban**: Protect against brute force attacks
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 2. Application Security

- **Environment variables**: Never commit `.env.production` to version control
- **Secrets rotation**: Regularly rotate database passwords and API keys
- **SSL/TLS**: Enforce HTTPS for all connections
- **CORS**: Configure strict CORS policies
- **Rate limiting**: Implement API rate limiting (configured in nginx)

### 3. Compliance

- **GDPR**: Data retention and user privacy controls
- **SOC 2**: Access controls and audit logging
- **HIPAA**: If handling healthcare data (additional requirements)

## Troubleshooting

### 1. Common Issues

#### Services Not Starting
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Check container status
docker-compose ps

# Check resource usage
docker stats
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec backend python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Check database logs
docker-compose logs db
```

#### SSL Certificate Issues
```bash
# Verify certificate validity
openssl x509 -in nginx/ssl/psychsync.com.crt -text -noout

# Test SSL configuration
nginx -t -c nginx/nginx.conf
```

### 2. Performance Issues

#### High Memory Usage
```bash
# Check container resource usage
docker stats --no-stream

# Monitor system resources
htop
free -h
df -h
```

#### Slow Database Queries
```bash
# Connect to database
docker-compose exec db psql -U psychsync_user -d psychsync_prod

# Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

### 3. Emergency Procedures

#### Complete System Recovery
```bash
# 1. Stop all services
docker-compose down

# 2. Restore from latest backup
aws s3 cp s3://psychsync-backups/database/latest.sql.gz ./
gunzip latest.sql.gz

# 3. Restore database
docker-compose up -d db
sleep 10
docker-compose exec -T db psql -U psychsync_user -d psychsync_prod < latest.sql

# 4. Start all services
docker-compose up -d

# 5. Verify health
./deployment/deploy.sh health-check
```

## Maintenance

### 1. Regular Tasks

- **Weekly**: Review logs and monitoring dashboards
- **Monthly**: Update Docker images and dependencies
- **Quarterly**: Security audit and penetration testing
- **Annually**: SSL certificate renewal (if not using Let's Encrypt)

### 2. Updates

```bash
# Update Docker images
docker-compose pull

# Rebuild application images
docker-compose build --no-cache

# Deploy updates
./deployment/deploy.sh deploy
```

### 3. Scaling

For horizontal scaling:

1. **Backend**: Add more backend containers behind load balancer
2. **Database**: Consider read replicas for read-heavy workloads
3. **Frontend**: Serve via CDN for global distribution
4. **Redis**: Use Redis Cluster for high availability

## Support

For deployment issues:

1. Check this documentation first
2. Review logs in `/var/log/psychsync-deployment.log`
3. Check monitoring dashboards for system alerts
4. Contact the development team with detailed error information

---

**Important**: This deployment configuration is designed for production use. Ensure all security measures are properly configured before going live.
