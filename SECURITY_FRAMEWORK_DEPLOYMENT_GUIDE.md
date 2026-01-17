# PsychSync Security Framework Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying and managing the PsychSync Security Framework, which includes enterprise-grade security monitoring, infrastructure scanning, and real-time threat detection capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Framework                       │
├─────────────────────────────────────────────────────────────┤
│  Unified Security Dashboard (React UI)                      │
│  ├── Overall Security Status                                │
│  ├── Real-time Metrics                                      │
│  ├── Alert Management                                       │
│  └── Compliance Monitoring                                  │
├─────────────────────────────────────────────────────────────┤
│  Security Integration Manager (Python)                     │
│  ├── Alert Processing                                       │
│  ├── Metrics Collection                                     │
│  ├── Background Scanning                                    │
│  └── State Management                                       │
├─────────────────────────────────────────────────────────────┤
│  Core Security Components                                   │
│  ├── Enterprise Security Manager                            │
│  ├── Infrastructure Security Scanner                        │
│  ├── SSH Brute Force Tester                                │
│  └── API Security Tester                                    │
├─────────────────────────────────────────────────────────────┤
│  Data Storage                                               │
│  ├── Security State (JSON)                                  │
│  ├── Alert History                                          │
│  ├── Metrics History                                        │
│  └── Scan Results                                           │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: 3.8+ with pip
- **Node.js**: 16+ with npm
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB available space for logs and reports
- **Network**: Outbound HTTPS access required

### Python Dependencies

```bash
# Install security framework dependencies
pip install fastapi uvicorn sqlalchemy asyncpg redis pydantic pydantic-settings
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
pip install aiosmtpe jinja2 python-nmap paramiko requests
pip install pytest pytest-asyncio httpx python-dotenv
```

### Node.js Dependencies

```bash
# Frontend dependencies are already included in the main project
cd frontend/
npm install
```

## Installation

### 1. Clone and Setup

```bash
# Navigate to project root
cd /path/to/psychsync

# Ensure all files are present
ls scripts/security_integration_manager.py
ls scripts/infrastructure_security_scanner.py
ls scripts/ssh_brute_force_tester.py
ls frontend/src/components/security/UnifiedSecurityDashboard.tsx
```

### 2. Configuration

Create security configuration file:

```bash
# Security configuration
cat > security_config.json << 'EOF'
{
  "scan_interval_minutes": 60,
  "alert_thresholds": {
    "critical_cves": 5,
    "high_risk_ports": 3,
    "ssh_security_score": 70,
    "enterprise_security_score": 80
  },
  "infrastructure": {
    "target_host": "localhost",
    "ssh_host": "localhost",
    "ssh_port": 22
  },
  "background_scanning": true,
  "auto_resolve_alerts": false
}
EOF
```

### 3. Environment Setup

Add to your `.env.dev` file:

```bash
# Security Framework Configuration
SECURITY_ENABLED=true
SECURITY_SCAN_INTERVAL=60
SECURITY_ALERT_EMAIL=admin@psychsync.com
SECURITY_DATA_DIR=./security_data

# Background Monitoring
MONITORING_ENABLED=true
MONITORING_RETENTION_DAYS=30
```

### 4. Create Required Directories

```bash
mkdir -p security_data/reports
mkdir -p security_data/logs
mkdir -p security_data/state
chmod 755 security_data
```

## Deployment Options

### Option 1: Standalone Security Service

Deploy as a dedicated security monitoring service:

```bash
# Create systemd service file
sudo tee /etc/systemd/system/psychsync-security.service << 'EOF'
[Unit]
Description=PsychSync Security Framework
After=network.target

[Service]
Type=simple
User=psychsync
WorkingDirectory=/opt/psychsync
Environment=PATH=/opt/psychsync/venv/bin
ExecStart=/opt/psychsync/venv/bin/python scripts/security_integration_manager.py --monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable psychsync-security
sudo systemctl start psychsync-security
```

### Option 2: Integrated with Main Application

Run alongside your existing FastAPI application:

```bash
# Add to main application startup
python scripts/security_integration_manager.py --monitor &

# Or use process manager like PM2
pm2 start scripts/security_integration_manager.py --name security -- --monitor
```

### Option 3: Docker Deployment

```dockerfile
# Add to your Dockerfile
FROM python:3.9-slim

# Install security dependencies
RUN pip install python-nmap paramiko requests

# Copy security framework
COPY scripts/security_integration_manager.py /app/scripts/
COPY scripts/infrastructure_security_scanner.py /app/scripts/
COPY scripts/ssh_brute_force_tester.py /app/scripts/

# Create security data directory
RUN mkdir -p /app/security_data && \
    chown -R appuser:appuser /app/security_data

USER appuser
WORKDIR /app

# Start both main app and security monitoring
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & python scripts/security_integration_manager.py --monitor"]
```

## API Integration

### 1. Backend Integration

Add to your FastAPI application:

```python
# app/api/v1/routes/security.py
from fastapi import APIRouter, Depends
from scripts.security_integration_manager import SecurityIntegrationManager

router = APIRouter(prefix="/security/unified", tags=["security"])

security_manager = SecurityIntegrationManager()

@router.get("/status")
async def get_security_status():
    return security_manager.get_current_status()

@router.post("/scan")
async def run_security_scan():
    return await security_manager.run_comprehensive_scan()

@router.get("/alerts")
async def get_security_alerts():
    alerts = security_manager.get_alerts(limit=50)
    return {"alerts": [asdict(alert) for alert in alerts]}
```

### 2. Frontend Integration

Add to your main React application:

```typescript
// src/App.tsx
import { UnifiedSecurityDashboard } from './components/security/UnifiedSecurityDashboard';

function App() {
  return (
    <Routes>
      {/* Your existing routes */}
      <Route path="/security" element={<UnifiedSecurityDashboard />} />
    </Routes>
  );
}
```

### 3. Navigation Integration

Add to your navigation menu:

```typescript
// src/components/NavBar.tsx
import { Shield } from 'lucide-react';

const navigation = [
  // Your existing navigation items
  {
    name: 'Security',
    href: '/security',
    icon: Shield,
    current: false,
  },
];
```

## Configuration Management

### Production Configuration

```json
{
  "scan_interval_minutes": 30,
  "alert_thresholds": {
    "critical_cves": 0,
    "high_risk_ports": 1,
    "ssh_security_score": 90,
    "enterprise_security_score": 95
  },
  "infrastructure": {
    "target_host": "your-domain.com",
    "ssh_host": "your-domain.com",
    "ssh_port": 22
  },
  "background_scanning": true,
  "auto_resolve_alerts": false,
  "notifications": {
    "email_enabled": true,
    "slack_webhook": "https://hooks.slack.com/...",
    "email_recipients": ["admin@yourcompany.com"]
  }
}
```

### Staging Configuration

```json
{
  "scan_interval_minutes": 120,
  "alert_thresholds": {
    "critical_cves": 10,
    "high_risk_ports": 5,
    "ssh_security_score": 60,
    "enterprise_security_score": 70
  },
  "infrastructure": {
    "target_host": "staging.your-domain.com",
    "ssh_host": "staging.your-domain.com",
    "ssh_port": 22
  },
  "background_scanning": true,
  "auto_resolve_alerts": true
}
```

## Monitoring and Logging

### Log Rotation Setup

```bash
# Configure logrotate for security logs
sudo tee /etc/logrotate.d/psychsync-security << 'EOF'
/opt/psychsync/security_data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 psychsync psychsync
    postrotate
        systemctl reload psychsync-security
    endscript
}
EOF
```

### Monitoring Dashboard Integration

```bash
# Prometheus metrics endpoint (if using Prometheus)
cat > security_metrics.py << 'EOF'
from prometheus_client import Counter, Histogram, Gauge, start_http_server

SECURITY_SCANS_TOTAL = Counter('security_scans_total', 'Total security scans')
SECURITY_ALERTS_TOTAL = Counter('security_alerts_total', 'Total security alerts')
SECURITY_SCORE = Gauge('security_score', 'Overall security score')
SCAN_DURATION = Histogram('security_scan_duration_seconds', 'Security scan duration')
EOF
```

## Security Considerations

### 1. Access Control

```bash
# Restrict access to security data
chmod 700 security_data/
chmod 600 security_config.json

# Create dedicated security user
sudo useradd -r -s /bin/false security-user
sudo chown -R security-user:security-user security_data/
```

### 2. Network Security

```bash
# Firewall rules for security monitoring
sudo ufw allow from 10.0.0.0/8 to any port 22
sudo ufw allow from 127.0.0.1 to any port 8000
sudo ufw deny 22  # Block external SSH access
```

### 3. SSL/TLS Configuration

Ensure all API endpoints use HTTPS:

```python
# app/main.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="certs/key.pem",
        ssl_certfile="certs/cert.pem"
    )
```

## Testing the Deployment

### 1. Manual Testing

```bash
# Test security scanner
python scripts/security_integration_manager.py --scan

# Test status endpoint
python scripts/security_integration_manager.py --status

# Test alert system
python scripts/security_integration_manager.py --alerts
```

### 2. Automated Testing

```bash
# Create test script
cat > test_security_deployment.sh << 'EOF'
#!/bin/bash

echo "Testing Security Framework Deployment..."

# Test 1: Check if service is running
systemctl is-active psychsync-security || exit 1

# Test 2: Test API endpoints
curl -f http://localhost:8000/api/v1/security/unified/status || exit 1

# Test 3: Test scan functionality
curl -X POST http://localhost:8000/api/v1/security/unified/scan || exit 1

# Test 4: Check data directory
test -d security_data || exit 1

echo "✅ All tests passed!"
EOF

chmod +x test_security_deployment.sh
./test_security_deployment.sh
```

## Maintenance

### 1. Regular Updates

```bash
# Update security framework
git pull origin main
pip install -r requirements.txt
systemctl restart psychsync-security
```

### 2. Data Cleanup

```bash
# Cleanup old security data (run weekly)
find security_data/logs -name "*.log" -mtime +30 -delete
find security_data/reports -name "*.json" -mtime +90 -delete
```

### 3. Backup Configuration

```bash
# Backup security configuration
tar -czf security_backup_$(date +%Y%m%d).tar.gz \
    security_config.json \
    security_data/ \
    scripts/security_*.py
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   sudo chown -R $USER:$USER security_data/
   chmod 755 scripts/security_*.py
   ```

2. **Port Scanning Issues**
   ```bash
   # Install nmap if missing
   sudo apt-get install nmap

   # Check if running with sufficient privileges
   sudo python scripts/infrastructure_security_scanner.py
   ```

3. **Memory Usage**
   ```bash
   # Monitor memory usage
   ps aux | grep security_integration_manager

   # Adjust scan interval if needed
   # Edit security_config.json to increase scan_interval_minutes
   ```

### Log Analysis

```bash
# View recent security logs
tail -f security_integration.log

# Search for specific errors
grep "ERROR" security_integration.log | tail -20

# Monitor scan performance
grep "scan completed" security_integration.log
```

## Performance Optimization

### 1. Scan Optimization

```json
{
  "scan_interval_minutes": 120,
  "parallel_scans": true,
  "scan_timeout_seconds": 300,
  "cache_results_minutes": 30
}
```

### 2. Database Optimization

```python
# Configure database connection pooling
DATABASE_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

## Support and Documentation

### Additional Resources

- **Security Policies**: `/docs/security/`
- **API Documentation**: `http://localhost:8000/docs`
- **Monitoring Guides**: `/docs/monitoring/`
- **Troubleshooting**: `/docs/troubleshooting/`

### Getting Help

1. Check the logs: `security_integration.log`
2. Review configuration: `security_config.json`
3. Run diagnostic: `python scripts/security_integration_manager.py --status`
4. Check system resources: `htop`, `df -h`, `free -m`

---

**Note**: This security framework is designed for enterprise environments. Ensure proper change management and testing procedures when deploying to production systems.
