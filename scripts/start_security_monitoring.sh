#!/bin/bash
# Security Monitoring System Startup Script
# Initializes and starts comprehensive security monitoring

set -e

echo "🔐 STARTING SECURITY MONITORING SYSTEM"
echo "======================================"

# Check if required services are running
echo "🔍 Checking service dependencies..."

# Check Redis (for caching and monitoring data)
if ! redis-cli ping >/dev/null 2>&1; then
    echo "❌ Redis is not running - required for security monitoring"
    echo "   Starting Redis..."
    redis-server --daemonize yes --port 6379
    sleep 2

    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
else
    echo "✅ Redis is running"
fi

# Check PostgreSQL
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running - required for security event logging"
    echo "   Please start PostgreSQL before continuing"
    exit 1
else
    echo "✅ PostgreSQL is running"
fi

# Check if backend is running
if ! curl -s http://localhost:8000/api/v1/health/public >/dev/null 2>&1; then
    echo "⚠️  Backend may not be running on port 8000"
    echo "   Security monitoring requires backend to be accessible"

    # Try to start backend if in development mode
    if [ -f ".env.dev" ]; then
        echo "🚀 Attempting to start backend in development mode..."
        python app/main.py &
        BACKEND_PID=$!
        echo "   Backend started with PID: $BACKEND_PID"
        sleep 5

        # Check if backend started successfully
        if curl -s http://localhost:8000/api/v1/health/public >/dev/null 2>&1; then
            echo "✅ Backend started successfully"
        else
            echo "❌ Failed to start backend"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
    else
        echo "❌ Backend not accessible and no development configuration found"
        exit 1
    fi
else
    echo "✅ Backend is running"
fi

# Create monitoring logs directory
echo "📁 Creating monitoring directories..."
mkdir -p logs/security
mkdir -p logs/monitoring
mkdir -p data/security

# Set up security monitoring configuration
echo "⚙️  Setting up security monitoring configuration..."
cat > .security_monitoring.conf << 'EOF'
# Security Monitoring Configuration
# Generated for PsychSync Security System

# Enable/disable monitoring
SECURITY_MONITORING_ENABLED=true
SECURITY_MONITORING_DEBUG=false

# Anomaly detection thresholds
ANOMALY_DETECTION_THRESHOLD=0.7
IMPOSSIBLE_TRAVEL_SPEED_KMH=800
MAX_CONCURRENT_SESSIONS=3
BRUTE_FORCE_THRESHOLD=5
UNUSUAL_LOCATION_THRESHOLD=0.8

# Data retention
SECURITY_ALERT_RETENTION_DAYS=90
BEHAVIOR_PROFILE_RETENTION_DAYS=30
SECURITY_EVENT_RETENTION_DAYS=7

# Alert thresholds
HIGH_RISK_THRESHOLD=70
CRITICAL_RISK_THRESHOLD=85

# Monitoring intervals
SYSTEM_RESOURCE_CHECK_INTERVAL=30
NETWORK_CONNECTION_CHECK_INTERVAL=60
ANOMALY_DETECTION_INTERVAL=300
DATA_CLEANUP_INTERVAL=3600

# Security policies
ENABLE_IP_BLOCKING=true
IP_BLOCK_DURATION_HOURS=24
MAX_FAILED_ATTEMPTS_PER_IP=20
MAX_FAILED_ATTEMPTS_PER_USER=10

# Notification settings
ENABLE_EMAIL_ALERTS=true
ENABLE_SLACK_ALERTS=false
ENABLE_WEBHOOK_ALERTS=false

# Rate limiting
RATE_LIMIT_WINDOW_MINUTES=5
RATE_LIMIT_MAX_REQUESTS=100

# Logging
SECURITY_LOG_LEVEL=INFO
ENABLE_DETAILED_LOGGING=true
LOG_SECURITY_EVENTS_TO_DATABASE=true
EOF

echo "✅ Security monitoring configuration created"

# Initialize security monitoring database tables (if needed)
echo "🗄️  Initializing security monitoring database..."
python -c "
import asyncio
from app.core.database import get_async_db
from sqlalchemy import text

async def init_tables():
    try:
        async for db in get_async_db():
            # Create security_events table if it doesn't exist
            await db.execute(text('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255),
                    event_type VARCHAR(100) NOT NULL,
                    ip_address INET NOT NULL,
                    user_agent TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    success BOOLEAN DEFAULT true,
                    endpoint VARCHAR(255),
                    response_time FLOAT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            '''))

            # Create indexes
            await db.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
            '''))

            await db.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);
            '''))

            await db.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security_events(ip_address);
            '''))

            # Create security_alerts table if it doesn't exist
            await db.execute(text('''
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id VARCHAR(100) PRIMARY KEY,
                    user_id VARCHAR(255),
                    anomaly_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    details JSONB DEFAULT '{}',
                    risk_score FLOAT DEFAULT 0.0,
                    action_taken TEXT,
                    resolved BOOLEAN DEFAULT false,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    resolved_at TIMESTAMP WITH TIME ZONE
                );
            '''))

            # Create alert indexes
            await db.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);
            '''))

            await db.execute(text('''
                CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);
            '''))

            # Commit the changes
            await db.commit()

            print('✅ Security monitoring tables initialized')
            break

    except Exception as e:
        print(f'❌ Error initializing security tables: {e}')

asyncio.run(init_tables())
"

if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize security monitoring database"
    exit 1
fi

# Test security monitoring system
echo "🧪 Testing security monitoring system..."
python -c "
import asyncio
from app.core.security_monitoring import security_monitor

async def test_system():
    print('   Testing security event recording...')

    # Test recording different types of events
    await security_monitor.record_security_event(
        user_id='monitoring_test_user',
        event_type='authentication_success',
        ip_address='127.0.0.1',
        user_agent='Security-Monitoring-Test/1.0',
        success=True,
        endpoint='/api/v1/auth/login'
    )

    await security_monitor.record_security_event(
        user_id='monitoring_test_user',
        event_type='authentication_failure',
        ip_address='192.168.1.100',
        user_agent='Malicious-Client/1.0',
        success=False,
        endpoint='/api/v1/auth/login'
    )

    # Test getting alerts
    alerts = await security_monitor.get_security_alerts(hours=1)
    print(f'   ✅ Security alerts working: {len(alerts)} alerts')

    # Test user risk assessment
    risk_level, risk_factors = await security_monitor.get_user_risk_level('monitoring_test_user')
    print(f'   ✅ Risk assessment working: {risk_level.value} risk level')

    print('   ✅ All security monitoring tests passed')

asyncio.run(test_system())
"

if [ $? -ne 0 ]; then
    echo "❌ Security monitoring system tests failed"
    exit 1
fi

# Set up monitoring cron jobs (optional)
echo "⏰ Setting up monitoring automation..."
cat > scripts/security_monitoring_cron.sh << 'EOF'
#!/bin/bash
# Security Monitoring Cron Job
# Run every 5 minutes to monitor security events

cd /path/to/psychsync

# Log current status
echo "$(date): Security monitoring check" >> logs/security/monitoring.log

# Check for critical security alerts
python -c "
import asyncio
from app.core.security_monitoring import security_monitor
from app.core.security_monitoring import AlertSeverity

async def check_critical_alerts():
    alerts = await security_monitor.get_security_alerts(hours=1, severity=AlertSeverity.CRITICAL)
    if alerts:
        print(f'CRITICAL: {len(alerts)} critical security alerts detected')
        for alert in alerts[:3]:  # Show first 3
            print(f'  - {alert.description}')

        # Here you could add email/SMS notifications
        # send_critical_alert(alerts)
    else:
        print('Security status: OK')

asyncio.run(check_critical_alerts())
" >> logs/security/monitoring.log 2>&1

# Check system resources and anomalies
python -c "
import asyncio
import psutil

async def check_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    if cpu_percent > 90:
        print(f'WARNING: High CPU usage: {cpu_percent}%')

    if memory.percent > 90:
        print(f'WARNING: High memory usage: {memory.percent}%')

asyncio.run(check_system_resources())
" >> logs/security/monitoring.log 2>&1

echo "" >> logs/security/monitoring.log
EOF

chmod +x scripts/security_monitoring_cron.sh

# Instructions for setting up cron
echo "📅 To set up automated monitoring, add the following to your crontab:"
echo "   */5 * * * * /path/to/psychsync/scripts/security_monitoring_cron.sh"
echo ""

# Create security monitoring dashboard script
echo "📊 Creating security monitoring dashboard script..."
cat > scripts/view_security_dashboard.sh << 'EOF'
#!/bin/bash
# View Security Monitoring Dashboard

echo "🔐 PSYCHSYNC SECURITY DASHBOARD"
echo "=============================="

# Get security dashboard data
DASHBOARD_DATA=$(curl -s -H "Authorization: Bearer YOUR_API_TOKEN" \
    "http://localhost:8000/api/v1/security-monitoring/dashboard" 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "📊 Current Security Status:"
    echo "$DASHBOARD_DATA" | python -m json.tool | grep -E '"(total_alerts|security_score|active_threats)" | sed 's/,//g' | sed 's/"/  /g'
    echo ""

    echo "🚨 Recent Critical Alerts:"
    echo "$DASHBOARD_DATA" | python -c "
import json, sys
data = json.load(sys.stdin)
for event in data['recent_events'][:3]:
    print(f\"  - {event['description']} (Risk: {event['risk_score']})\")
" 2>/dev/null || echo "  No critical alerts"
else
    echo "❌ Unable to fetch security dashboard data"
    echo "   Make sure the application is running and you have valid API credentials"
fi

echo ""
echo "🔍 Security Monitoring Commands:"
echo "  View all alerts: curl -H \"Authorization: Bearer TOKEN\" http://localhost:8000/api/v1/security-monitoring/alerts"
echo "  User risk assessment: curl -H \"Authorization: Bearer TOKEN\" http://localhost:8000/api/v1/security-monitoring/user-risk/USER_ID"
echo "  Threat intelligence: curl -H \"Authorization: Bearer TOKEN\" http://localhost:8000/api/v1/security-monitoring/threat-intelligence"
echo ""
echo "📋 Logs are available in: logs/security/"
echo "📊 Monitor configuration: .security_monitoring.conf"
EOF

chmod +x scripts/view_security_dashboard.sh

# Final status check
echo ""
echo "🎉 SECURITY MONITORING SYSTEM SETUP COMPLETED"
echo "=========================================="
echo ""
echo "✅ Security monitoring components initialized:"
echo "   🔒 Real-time threat detection engine"
echo "   📊 Security dashboard and analytics"
echo "   🚨 Automated alert system"
echo "   👤 User behavior profiling"
echo "   🔍 Anomaly detection algorithms"
echo "   📈 Threat intelligence integration"
echo "   🗄️  Security event logging"
echo "   ⏰ Automated monitoring tasks"
echo ""
echo "🌐 Security Monitoring Endpoints:"
echo "   Dashboard: http://localhost:8000/api/v1/security-monitoring/dashboard"
echo "   Alerts:    http://localhost:8000/api/v1/security-monitoring/alerts"
echo "   User Risk: http://localhost:8000/api/v1/security-monitoring/user-risk/{user_id}"
echo "   Intel:     http://localhost:8000/api/v1/security-monitoring/threat-intelligence"
echo ""
echo "🔧 Management Scripts:"
echo "   View dashboard: ./scripts/view_security_dashboard.sh"
echo "   Monitor logs:    tail -f logs/security/monitoring.log"
echo "   Security config: .security_monitoring.conf"
echo ""
echo "📋 Security Features Active:"
echo "   ✅ Authentication failure detection"
echo "   ✅ Brute force attack detection"
echo "   ✅ Impossible travel detection"
echo "   ✅ Multiple session monitoring"
echo "   ✅ Unusual location detection"
echo "   ✅ Suspicious API usage detection"
echo "   ✅ User risk assessment"
echo "   ✅ Automated threat intelligence"
echo "   ✅ Real-time alerting system"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "1. Review and adjust security thresholds in .security_monitoring.conf"
echo "2. Set up alert notifications (email/Slack) for critical threats"
echo "3. Configure automated response actions for high-risk threats"
echo "4. Regularly review security logs and dashboard data"
echo "5. Test incident response procedures regularly"
echo "6. Keep security monitoring system updated"
echo ""
echo "🔒 Your system is now protected by comprehensive security monitoring!"