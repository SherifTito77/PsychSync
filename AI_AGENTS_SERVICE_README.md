# 🤖 PsychSync AI Agents Service

**Standalone microservice for AI-powered automation**

**Port**: 5002
**Documentation**: http://localhost:5002/docs
**Status**: Operational

---

## 🚀 Quick Start

### Option 1: Using the startup script (Recommended)
```bash
./start-ai-agents.sh
```

### Option 2: Direct startup
```bash
python3 ai_agents_service.py
```

### Option 3: Custom port
```bash
PORT=8001 python3 ai_agents_service.py
```

The service will start at http://localhost:5002

---

## 📋 What This Service Does

The AI Agents Service provides **20 automated agents** for:

### 🛡️ Security (3 agents)
- **Security Headers Validator** - Checks OWASP compliance on all routes
- **Encryption Strategy Advisor** - Analyzes DB schema, recommends encryption
- **Unsafe Script Detector** - Scans frontend for vulnerabilities

### 💻 Development (8 agents)
- **Coding Style Enforcer** - Enforces code style standards
- **Performance Regression Detector** - Detects performance slowdowns
- **Localization Key Detector** - Finds missing i18n translations
- **Slow Endpoint Tracker** - Identifies slow API endpoints
- **Release Notes Generator** - Auto-generates changelogs
- **Permission Gap Detector** - Finds missing authentication
- **Test Coverage Reporter** - Grades test coverage
- **Refactoring Target Proposer** - Suggests code improvements

### 🔄 Operations (9 agents)
- **UX Telemetry Tracker** - Analyzes user experience friction
- **Environment Config Detector** - Validates environment variables
- **Incident Mitigation Planner** - Creates incident response plans
- **Dependency Updater** - Checks for outdated packages
- **PR-Jira Mapper** - Links pull requests to Jira tickets
- **Uptime Monitor** - Tracks system availability
- **Stability Score Calculator** - Calculates system health
- **Architecture Drift Detector** - Detects code quality issues
- **Bug Environment Creator** - Creates reproducible test environments

---

## 🔌 Endpoints

### Root Endpoints
- `GET /` - Service information
- `GET /health` - Health check

### Agent Endpoints
All agent endpoints are prefixed with `/api/v1/ai-agents/`

#### Security
- `POST /security-headers/validate` - Validate security headers
- `GET /security-headers/recommendations` - Get security recommendations
- `POST /encryption-strategy/analyze` - Analyze encryption needs
- `POST /unsafe-scripts/scan` - Scan for vulnerabilities
- `POST /security/permission-gaps` - Find permission gaps

#### Development
- `POST /coding-style/check` - Check code style
- `GET /coding-style/report` - Get style report
- `POST /performance/regression` - Detect regressions
- `POST /performance/slow-endpoints` - Track slow APIs
- `POST /release-notes/generate` - Generate release notes
- `GET /localization/check` - Check i18n coverage
- `POST /testing/coverage-report` - Get test coverage
- `POST /refactoring/propose-targets` - Get refactoring ideas

#### Operations
- `POST /ux/track-event` - Track UX event
- `GET /ux/friction-points` - Get friction analysis
- `POST /environment/validate` - Validate config
- `POST /incidents/mitigation-plan` - Get incident plan
- `GET /dependencies/check-outdated` - Check dependencies
- `POST /integrations/map-pr-to-jira` - Map PR to Jira
- `POST /monitoring/check-uptime` - Check uptime
- `GET /monitoring/daily-uptime-summary` - Get uptime summary
- `POST /monitoring/stability-score` - Calculate stability
- `POST /architecture/check-drift` - Check architecture
- `POST /debugging/create-bug-environment` - Create bug env

### Meta
- `GET /status` - List all agents and endpoints

---

## 🔐 Authentication

All endpoints require a JWT token. Include it in the Authorization header:

```bash
curl http://localhost:5002/api/v1/ai-agents/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Note**: In development mode, you can temporarily disable authentication by modifying the endpoint dependencies.

---

## 📚 Documentation

### Interactive API Documentation
- **Swagger UI**: http://localhost:5002/docs
- **ReDoc**: http://localhost:5002/redoc

### Usage Guide
See `docs/AI_AGENTS_USAGE_GUIDE.md` for detailed usage examples.

### Test Script
Run the demonstration script:
```bash
python3 test_ai_agents.py
```

---

## 🏗️ Architecture

```
AI Agents Service (Port 5002)
├── FastAPI Application
├── 20 AI Agents
│   ├── Security Layer (3)
│   ├── Development Layer (8)
│   └── Operations Layer (9)
├── 30 REST Endpoints
└── JWT Authentication
```

### Separation from Main App
- **Main App**: Port 8000 - Core PsychSync application
- **AI Agents Service**: Port 5002 - Automation agents
- **AI Engineering Prompts**: Port 5002 - Prompt management (if running)

This microservices architecture allows:
- Independent deployment
- Separate scaling
- Isolated failures
- Technology diversity

---

## 🧪 Testing

### Test the Service
```bash
# Health check
curl http://localhost:5002/health

# Agent status
curl http://localhost:5002/api/v1/ai-agents/status

# Run demo script
python3 test_ai_agents.py
```

### Expected Response
```json
{
  "total_agents": 20,
  "active_agents": 20,
  "agents": [...]
}
```

---

## 🔧 Configuration

### Environment Variables
- `PORT` - Port number (default: 5000)
- `HOST` - Host address (default: 0.0.0.0)
- `RELOAD` - Enable auto-reload (default: true)
- `DEBUG` - Debug mode

### Example
```bash
PORT=8001 HOST=127.0.0.1 python3 ai_agents_service.py
```

---

## 📊 Monitoring

### Logs
Logs are printed to stdout with format:
```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message
```

### Health Endpoint
```bash
curl http://localhost:5002/health
```

Returns:
```json
{
  "status": "healthy",
  "service": "ai-agents",
  "timestamp": "2024-01-17T12:00:00Z",
  "version": "1.0.0"
}
```

---

## 🚦 Production Deployment

### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "ai_agents_service.py"]
```

### Using Systemd
```ini
[Unit]
Description=PsychSync AI Agents Service
After=network.target

[Service]
Type=simple
User=psychsync
WorkingDirectory=/opt/psychsync
Environment="PORT=5000"
ExecStart=/usr/bin/python3 /opt/psychsync/ai_agents_service.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Using Supervisor
```ini
[program:ai-agents]
command=/usr/bin/python3 /opt/psychsync/ai_agents_service.py
directory=/opt/psychsync
user=psychsync
autostart=true
autorestart=true
environment=PORT="5000"
```

---

## 🔗 Integration

### With Main Application
The AI Agents Service can communicate with the main app:
- Database access (shared PostgreSQL)
- Redis (shared cache)
- File system (shared logs)

### Authentication
Uses the same JWT tokens as the main app. Tokens can be:
- Generated by main app (port 8000)
- Validated by shared secret key
- Passed in Authorization header

---

## 📝 Example Usage

### Check Security Headers
```bash
curl -X POST http://localhost:5002/api/v1/ai-agents/security-headers/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}'
```

### Generate Release Notes
```bash
curl -X POST "http://localhost:5002/api/v1/ai-agents/release-notes/generate?version=v2.1.0" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "commits": [
      {"message": "feat: Add dark mode support"},
      {"message": "fix: Resolve login bug"}
    ]
  }'
```

### Check System Stability
```bash
curl -X POST http://localhost:5002/api/v1/ai-agents/monitoring/stability-score \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "uptime_percent": 99.9,
    "error_rate": 0.05,
    "slow_request_rate": 1.5
  }'
```

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find process using port 5002
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
PORT=8001 python3 ai_agents_service.py
```

### Import Errors
```bash
# Ensure you're in project root
cd /path/to/psychsync

# Check Python path
echo $PYTHONPATH

# Add project root to path
export PYTHONPATH=/path/to/psychsync:$PYTHONPATH
```

### Agent Not Responding
```bash
# Check service health
curl http://localhost:5002/health

# Check logs
tail -f /var/log/ai-agents.log

# Restart service
./start-ai-agents.sh
```

---

## 📞 Support

For issues or questions:
- Check documentation: `docs/AI_AGENTS_USAGE_GUIDE.md`
- View test results: `AI_AGENTS_TEST_RESULTS.md`
- Run demo: `python3 test_ai_agents.py`
- Check logs: Console output

---

## 🎉 Summary

The AI Agents Service provides:
- ✅ 20 operational AI agents
- ✅ 30 REST endpoints
- ✅ JWT authentication
- ✅ Comprehensive documentation
- ✅ Health monitoring
- ✅ Error handling
- ✅ CORS support
- ✅ Production ready

**Access it now at: http://localhost:5002/docs**
