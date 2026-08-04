# Time-Based Log Rotation Implementation
## Enhanced Log Management for PsychSync

**Date:** 2026-03-10
**Version:** 1.0.0
**Priority:** P2 (Medium Priority Enhancement)

---

## Executive Summary

This document provides a comprehensive design for implementing **time-based + size-based log rotation** for PsychSync's logging infrastructure. The solution addresses the current limitation of size-only rotation while providing flexible retention policies.

### Key Objectives

1. **Dual Trigger Rotation** - Rotate based on both size and time
2. **Flexible Retention Policies** - Configure retention by log type and severity
3. **Automatic Cleanup** - Remove expired log files automatically
4. **Backup Integration** - Support for compressed backups
5. **Monitoring Integration** - Track rotation events and disk usage
6. **Minimal Performance Impact** - Efficient rotation without disrupting logging

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Application Logging                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   API     │  │Security   │  │ Database  │  │  Error    │      │
│  │   Logs    │  │  Logs     │  │   Logs    │  │   Logs    │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
└─────────────────────────┼────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                 Log Rotation Manager                               │
│                  ┌─────────────┐                                │
│                  │   Rotation   │                                │
│                  │   Scheduler  │                                │
│                  │             │                                │
│                  │  - Timer     │                                │
│                  │  - Size Check│                                │
│                  │  - Trigger   │                                │
│                  └──────┬──────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
            ┌─────────────┐     ┌─────────────┐
            │  Time-Based  │     │ Size-Based  │
            │  Rotation    │     │ Rotation    │
            └──────┬──────┘     └──────┬──────┘
                   │                     │
                   └──────────┬──────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Post-Rotation Actions                            │
│                   ┌─────────────┐                                │
│                   │   Action     │                                │
│                   │   Handler    │                                │
│                  │             │                                │
│                  │  - Compress  │                                │
│                  │  - Archive   │                                │
│                  │  - Upload    │                                │
│                  │  - Notify   │                                │
│                  └──────┬──────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
            ┌─────────────┐     ┌─────────────┐
            │  Compressed  │     │   External  │
            │  Archives   │     │   Storage   │
            └─────────────┘     │  (S3, Azure)│
                                 └─────────────┘
```

---

## Component Specifications

### 1. Enhanced Logging Configuration

**File:** `app/core/logging_config.py` (Enhanced)

```python
"""
Enhanced Logging Configuration with Time-Based Rotation
Supports both time-based and size-based log rotation
"""

import logging
import logging.handlers
import os
import time
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from app.core.log_sanitizer import SensitiveDataFilter


@dataclass
class RotationConfig:
    """Configuration for log rotation"""
    log_file: str
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    time_rotation: str = None  # 'H', 'D', 'midnight', etc.
    compress_backups: bool = True
    retention_days: int = 30
    backup_path: str = None
    upload_to_cloud: bool = False
    cloud_bucket: str = None


class TimedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Enhanced rotating file handler with both time-based and size-based rotation
    """

    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        time_rotation: Optional[str] = None,
        compress: bool = True,
        retention_days: int = 30,
        backup_path: Optional[str] = None,
        **kwargs
    ):
        self.max_bytes = max_bytes
        self.time_rotation = time_rotation
        self.compress = compress
        self.retention_days = retention_days
        self.backup_path = backup_path or Path(filename).parent / "backups"

        # Track rotation time
        self.last_rotation_time = time.time()
        self.rotation_interval = self._parse_time_rotation(time_rotation)

        # Initialize base handler
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count, **kwargs)

        # Setup compression and retention
        self._setup_rotation_dir()

    def _parse_time_rotation(self, time_rotation: Optional[str]) -> Optional[timedelta]:
        """Parse time rotation string to timedelta"""
        if not time_rotation:
            return None

        rotation_map = {
            'H': timedelta(hours=1),
            '6H': timedelta(hours=6),
            '12H': timedelta(hours=12),
            'D': timedelta(days=1),
            'midnight': timedelta(days=1),
            'W': timedelta(weeks=1),
            'M': timedelta(days=30)
        }

        return rotation_map.get(time_rotation.upper())

    def _setup_rotation_dir(self):
        """Setup backup directory"""
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def shouldRollover(self, record: logging.LogRecord) -> bool:
        """
        Check if rotation should occur (time or size based)
        """
        # Check size-based rotation
        if self.stream is not None:
            try:
                self.stream.seek(0, 2)  # Seek to end
                if self.stream.tell() >= self.max_bytes:
                    return True
            except Exception:
                pass

        # Check time-based rotation
        if self.time_rotation:
            time_since_rotation = time.time() - self.last_rotation_time
            if time_since_rotation >= self.rotation_interval.total_seconds():
                return True

        return False

    def doRollover(self):
        """
        Perform log rotation with compression and retention cleanup
        """
        # Call base rotation
        super().doRollover()

        # Update rotation time
        self.last_rotation_time = time.time()

        # Compress old backups
        if self.compress:
            self._compress_backups()

        # Cleanup old logs
        self._cleanup_old_logs()

    def _compress_backups(self):
        """Compress log backup files"""
        log_dir = Path(self.baseFilename).parent
        log_base = Path(self.baseFilename).name

        # Find all backup files
        for backup_file in log_dir.glob(f"{log_base}.*"):
            # Skip already compressed files
            if backup_file.suffix == '.gz':
                continue

            # Skip the active log file
            if not self._is_backup_file(backup_file.name, log_base):
                continue

            # Compress the file
            try:
                compressed_file = backup_file.with_suffix(backup_file.suffix + '.gz')

                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove original file
                backup_file.unlink()

                print(f"Compressed: {backup_file.name} -> {compressed_file.name}")
            except Exception as e:
                print(f"Failed to compress {backup_file.name}: {e}")

    def _is_backup_file(self, filename: str, base_log: str) -> bool:
        """Check if file is a backup (not current log)"""
        return filename != base_log and filename.startswith(base_log)

    def _cleanup_old_logs(self):
        """Remove log files older than retention period"""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)

        log_dir = Path(self.baseFilename).parent
        backup_dir = self.backup_path

        # Cleanup main log directory
        self._cleanup_directory(log_dir, cutoff_time)

        # Cleanup backup directory
        self._cleanup_directory(backup_dir, cutoff_time)

    def _cleanup_directory(self, directory: Path, cutoff_time: datetime):
        """Remove files in directory older than cutoff"""
        if not directory.exists():
            return

        for file_path in directory.glob("*"):
            if file_path.is_file():
                # Get file modification time
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_time < cutoff_time:
                        file_path.unlink()
                        print(f"Removed old log: {file_path.name}")
                except Exception as e:
                    print(f"Failed to cleanup {file_path.name}: {e}")


class CloudUploadHandler:
    """Handler for uploading logs to cloud storage"""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('upload_to_cloud', False)
        self.bucket = config.get('cloud_bucket')

        if self.enabled:
            self._initialize_cloud_client()

    def _initialize_cloud_client(self):
        """Initialize cloud storage client"""
        import boto3

        self.s3_client = boto3.client('s3')

    async def upload_log(self, file_path: Path):
        """Upload log file to cloud storage"""
        if not self.enabled:
            return

        try:
            object_name = f"logs/{datetime.now().strftime('%Y/%m/%d')}/{file_path.name}"

            self.s3_client.upload_file(
                str(file_path),
                self.bucket,
                object_name
            )

            print(f"Uploaded {file_path.name} to {self.bucket}/{object_name}")
        except Exception as e:
            print(f"Failed to upload {file_path.name}: {e}")


class LogRotationMonitor:
    """Monitor log rotation events and disk usage"""

    def __init__(self, log_paths: List[str]):
        self.log_paths = log_paths
        self.rotation_events = []
        self.disk_usage = {}

    async def start_monitoring(self):
        """Start monitoring log rotation"""
        import asyncio

        while True:
            await self._check_disk_usage()
            await asyncio.sleep(300)  # Check every 5 minutes

    async def _check_disk_usage(self):
        """Check disk usage for log directories"""
        for log_path in self.log_paths:
            path = Path(log_path)
            if path.exists():
                # Get disk usage
                total, used, free = shutil.disk_usage(path.parent)

                usage_percent = (used / total) * 100

                self.disk_usage[log_path] = {
                    'total_bytes': total,
                    'used_bytes': used,
                    'free_bytes': free,
                    'usage_percent': usage_percent,
                    'timestamp': datetime.now()
                }

                # Alert if disk is nearly full
                if usage_percent > 90:
                    await self._send_disk_alert(log_path, usage_percent)

    async def _send_disk_alert(self, log_path: str, usage_percent: float):
        """Send alert for high disk usage"""
        # This would integrate with the alert system
        print(f"ALERT: Disk usage for {log_path} is {usage_percent:.1f}%")
```

### 2. Configuration File

**File:** `monitoring/logging_config_rotation.json`

```json
{
  "version": 2,
  "disable_existing_loggers": false,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
      "datefmt": "%Y-%m-%d %H:%M:%S"
    },
    "json": {
      "()": "app.core.logging_config.StructuredFormatter"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "detailed",
      "stream": "ext://sys.stdout"
    },
    "api_log_file": {
      "()": "app.core.logging_config.TimedRotatingFileHandler",
      "level": "INFO",
      "formatter": "json",
      "filename": "logs/api.log",
      "max_bytes": 52428800,
      "backup_count": 7,
      "time_rotation": "D",
      "compress": true,
      "retention_days": 30,
      "backup_path": "logs/backups/api"
    },
    "security_log_file": {
      "()": "app.core.logging_config.TimedRotatingFileHandler",
      "level": "INFO",
      "formatter": "json",
      "filename": "logs/security.log",
      "max_bytes": 52428800,
      "backup_count": 14,
      "time_rotation": "12H",
      "compress": true,
      "retention_days": 90,
      "backup_path": "logs/backups/security",
      "upload_to_cloud": true,
      "cloud_bucket": "psychsync-security-logs"
    },
    "error_log_file": {
      "()": "app.core.logging_config.TimedRotatingFileHandler",
      "level": "ERROR",
      "formatter": "json",
      "filename": "logs/errors.log",
      "max_bytes": 10485760,
      "backup_count": 14,
      "time_rotation": "6H",
      "compress": true,
      "retention_days": 180,
      "backup_path": "logs/backups/errors",
      "upload_to_cloud": true,
      "cloud_bucket": "psychsync-error-logs"
    },
    "database_log_file": {
      "()": "app.core.logging_config.TimedRotatingFileHandler",
      "level": "WARNING",
      "formatter": "detailed",
      "filename": "logs/database.log",
      "max_bytes": 104857600,
      "backup_count": 5,
      "time_rotation": "H",
      "compress": false,
      "retention_days": 14
    },
    "audit_log_file": {
      "()": "app.core.logging_config.TimedRotatingFileHandler",
      "level": "INFO",
      "formatter": "json",
      "filename": "logs/audit.log",
      "max_bytes": 10485760,
      "backup_count": 30,
      "time_rotation": "D",
      "compress": true,
      "retention_days": 365,
      "backup_path": "logs/backups/audit"
    }
  },
  "loggers": {
    "": {
      "level": "INFO",
      "handlers": ["console", "api_log_file"]
    },
    "app.security.logging": {
      "level": "INFO",
      "handlers": ["security_log_file"],
      "propagate": false
    },
    "app.core.database": {
      "level": "WARNING",
      "handlers": ["database_log_file"],
      "propagate": false
    },
    "app.security.audit": {
      "level": "INFO",
      "handlers": ["audit_log_file"],
      "propagate": false
    }
  }
}
```

### 3. Setup Script

**File:** `scripts/setup_log_rotation.sh`

```bash
#!/bin/bash
# Log Rotation Setup Script
# Initializes enhanced log rotation configuration

set -e

# Configuration
LOG_DIR="/var/log/psychsync"
BACKUP_DIR="/var/log/psychsync/backups"
PYTHON_CMD="${PYTHON_CMD:-python3}"

echo "🔧 Setting up PsychSync Log Rotation..."

# Create log directories
echo "Creating log directories..."
mkdir -p "${LOG_DIR}"
mkdir -p "${BACKUP_DIR}/api"
mkdir -p "${BACKUP_DIR}/security"
mkdir -p "${BACKUP_DIR}/errors"
mkdir -p "${BACKUP_DIR}/database"
mkdir -p "${BACKUP_DIR}/audit"

# Set permissions
echo "Setting permissions..."
chmod 755 "${LOG_DIR}"
chmod 700 "${BACKUP_DIR}"/*/  # Secure backup directories
chown -R app:app "${LOG_DIR}"

# Test configuration
echo "Testing logging configuration..."
${PYTHON_CMD} -c "
import logging.config
import json

with open('monitoring/logging_config_rotation.json') as f:
    config = json.load(f)
    logging.config.dictConfig(config)

    # Test logger creation
    logger = logging.getLogger('app.security.logging')
    logger.info('Log rotation setup successful')

    print('✅ Configuration loaded successfully')
"

# Install system timer for monitoring (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Setting up systemd timer for log monitoring..."

    sudo tee /etc/systemd/system/psychsync-log-monitor.service > /dev/null <<EOF
[Unit]
Description=PsychSync Log Monitor
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/app
ExecStart=${PYTHON_CMD} -m app.core.logging_config.monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo tee /etc/systemd/system/psychsync-log-monitor.timer > /dev/null <<EOF
[Unit]
Description=Run PsychSync Log Monitor every 5 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=1s

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable psychsync-log-monitor.timer
    sudo systemctl start psychsync-log-monitor.timer

    echo "✅ Systemd timer installed and started"
fi

# Create cron job for non-Linux systems
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Setting up cron job for log monitoring..."

    CRON_JOB="*/5 * * * * ${PYTHON_CMD} /app/scripts/monitor_logs.py >> /var/log/psychsync/monitor.log 2>&1"

    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "monitor_logs.py"; then
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo "✅ Cron job installed"
    else
        echo "✅ Cron job already exists"
    fi
fi

echo ""
echo "✨ Log rotation setup complete!"
echo ""
echo "📋 Summary:"
echo "  - Log directory: ${LOG_DIR}"
echo "  - Backup directory: ${BACKUP_DIR}"
echo "  - Monitoring: Enabled"
echo ""
echo "📝 Next steps:"
echo "  1. Update app/.env with LOG_ROTATION_CONFIG=monitoring/logging_config_rotation.json"
echo "  2. Restart the application"
echo "  3. Monitor log rotation in ${LOG_DIR}/monitor.log"
```

### 4. Monitoring Script

**File:** `scripts/monitor_logs.py`

```python
#!/usr/bin/env python3
"""
Log Rotation Monitoring Script
Monitors disk usage and rotation events
"""

import asyncio
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('log_monitor')


class LogMonitor:
    """Monitor log rotation and disk usage"""

    def __init__(self, config_file: str = 'monitoring/logging_config_rotation.json'):
        self.config_file = config_file
        self.config = self._load_config()
        self.log_paths = self._extract_log_paths()

    def _load_config(self) -> Dict[str, Any]:
        """Load logging configuration"""
        with open(self.config_file) as f:
            return json.load(f)

    def _extract_log_paths(self) -> list:
        """Extract log file paths from configuration"""
        paths = []

        handlers = self.config.get('handlers', {})
        for handler_name, handler_config in handlers.items():
            if 'filename' in handler_config:
                paths.append(handler_config['filename'])

        return paths

    async def monitor(self):
        """Main monitoring loop"""
        logger.info("Starting log rotation monitor...")

        while True:
            try:
                await self.check_disk_usage()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                logger.info("Monitor stopped")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def check_disk_usage(self):
        """Check disk usage for all log directories"""
        for log_path in self.log_paths:
            try:
                await self._check_single_path(log_path)
            except Exception as e:
                logger.error(f"Error checking {log_path}: {e}")

    async def _check_single_path(self, log_path: str):
        """Check disk usage for single log path"""
        path = Path(log_path)
        backup_path = path.parent / "backups" / path.stem

        # Check main log file
        if path.exists():
            file_size = path.stat().st_size

            # Get handler config
            handler_config = None
            for handler in self.config['handlers'].values():
                if handler.get('filename') == str(path):
                    handler_config = handler
                    break

            max_bytes = handler_config.get('max_bytes', 10 * 1024 * 1024)

            # Log if file is large
            if file_size > max_bytes * 0.8:  # 80% of max
                logger.warning(
                    f"Log file near rotation: {path.name} "
                    f"({file_size / 1024 / 1024:.1f}MB / {max_bytes / 1024 / 1024:.1f}MB)"
                )

        # Check backup directory
        if backup_path.exists():
            total_size = sum(
                f.stat().st_size
                for f in backup_path.rglob('*')
                if f.is_file()
            )

            retention_days = None
            for handler in self.config['handlers'].values():
                if handler.get('backup_path') == str(backup_path):
                    retention_days = handler.get('retention_days', 30)
                    break

            if retention_days:
                # Calculate expected size based on retention
                expected_max_size = total_size / retention_days * retention_days

                # Alert if backup size is growing unexpectedly
                if total_size > expected_max_size * 1.5:  # 50% over expected
                    logger.warning(
                        f"Backup directory large: {backup_path.name} "
                        f"({total_size / 1024 / 1024:.1f}MB)"
                    )

    async def generate_report(self):
        """Generate log rotation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'log_paths': [],
            'summary': {
                'total_files': 0,
                'total_size_bytes': 0,
                'compressed_files': 0,
                'rotation_events_today': 0
            }
        }

        for log_path in self.log_paths:
            path = Path(log_path)
            backup_path = path.parent / "backups" / path.stem

            path_info = {
                'name': path.name,
                'size_bytes': 0,
                'file_count': 0,
                'compressed_count': 0,
                'last_rotation': None
            }

            if path.exists():
                path_info['size_bytes'] += path.stat().st_size
                path_info['file_count'] += 1
                path_info['last_rotation'] = datetime.fromtimestamp(
                    path.stat().st_mtime
                ).isoformat()

            if backup_path.exists():
                for f in backup_path.rglob('*'):
                    if f.is_file():
                        path_info['size_bytes'] += f.stat().st_size
                        path_info['file_count'] += 1
                        if f.suffix == '.gz':
                            path_info['compressed_count'] += 1

            report['log_paths'].append(path_info)

            # Update summary
            report['summary']['total_files'] += path_info['file_count']
            report['summary']['total_size_bytes'] += path_info['size_bytes']
            report['summary']['compressed_files'] += path_info['compressed_count']

        # Save report
        report_path = Path('logs/backups/rotation_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Rotation report generated: {report_path}")

        return report


async def main():
    """Main entry point"""
    import sys

    monitor = LogMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        # Generate report
        report = await monitor.generate_report()
        print(json.dumps(report, indent=2, default=str))
    else:
        # Run continuous monitoring
        await monitor.monitor()


if __name__ == '__main__':
    asyncio.run(main())
```

---

## Implementation Roadmap

### Phase 1: Configuration (Week 1)
- [ ] Design rotation policies for each log type
- [ ] Create configuration file with dual triggers
- [ ] Set up retention schedules
- [ ] Configure cloud upload settings

### Phase 2: Implementation (Week 2)
- [ ] Implement TimedRotatingFileHandler
- [ ] Implement compression functionality
- [ ] Implement cleanup logic
- [ ] Add cloud upload support

### Phase 3: Integration (Week 3)
- [ ] Update application logging configuration
- [ ] Integrate with existing logging setup
- [ ] Test rotation triggers
- [ ] Verify compression and cleanup

### Phase 4: Monitoring (Week 4)
- [ ] Implement LogMonitor class
- [ ] Set up systemd/cron jobs
- [ ] Configure alerts for disk usage
- [ ] Create rotation reports

### Phase 5: Deployment (Week 5)
- [ ] Deploy to production environment
- [ ] Monitor rotation events
- [ ] Adjust retention policies as needed
- [ ] Document operational procedures

---

## Rotation Policies

### API Logs

| Parameter | Value |
|-----------|--------|
| Max File Size | 50MB |
| Time Rotation | Daily |
| Backup Count | 7 days |
| Retention | 30 days |
| Compression | Yes |
| Cloud Upload | No |

### Security Logs

| Parameter | Value |
|-----------|--------|
| Max File Size | 50MB |
| Time Rotation | Every 12 hours |
| Backup Count | 14 files |
| Retention | 90 days |
| Compression | Yes |
| Cloud Upload | Yes (separate bucket) |

### Error Logs

| Parameter | Value |
|-----------|--------|
| Max File Size | 10MB |
| Time Rotation | Every 6 hours |
| Backup Count | 14 files |
| Retention | 180 days |
| Compression | Yes |
| Cloud Upload | Yes (separate bucket) |

### Database Logs

| Parameter | Value |
|-----------|--------|
| Max File Size | 100MB |
| Time Rotation | Hourly |
| Backup Count | 5 files |
| Retention | 14 days |
| Compression | No |
| Cloud Upload | No |

### Audit Logs

| Parameter | Value |
|-----------|--------|
| Max File Size | 10MB |
| Time Rotation | Daily |
| Backup Count | 30 files |
| Retention | 365 days |
| Compression | Yes |
| Cloud Upload | No |

---

## Cost Estimate

| Component | Monthly Cost | Notes |
|-----------|--------------|--------|
| Local Disk Storage | $0 | Uses existing infrastructure |
| S3 Storage (backups) | $20 | 100GB for security and error logs |
| **Total** | **$20/month** | Production estimate |

---

## Troubleshooting Guide

### Common Issues

1. **Logs not rotating**
   ```bash
   # Check handler is using correct configuration
   python3 -c "
   import logging.config
   import json
   with open('monitoring/logging_config_rotation.json') as f:
       config = json.load(f)
       logging.config.dictConfig(config)
       print('Configuration loaded')
   "

   # Check file size
   ls -lh logs/

   # Check logs for rotation errors
   grep -i rotation logs/monitor.log
   ```

2. **Compression failing**
   ```bash
   # Check disk space
   df -h

   # Check file permissions
   ls -la logs/backups/

   # Manually test compression
   gzip -k logs/api.log.1
   ```

3. **Retention not cleaning up**
   ```bash
   # Check retention configuration
   python3 scripts/monitor_logs.py report

   # Manually trigger cleanup
   python3 -c "
   from app.core.logging_config import TimedRotatingFileHandler
   handler = TimedRotatingFileHandler('logs/api.log')
   handler._cleanup_old_logs()
   "
   ```

---

## Conclusion

Implementing time-based + size-based log rotation will significantly enhance PsychSync's log management capabilities by:

- ✅ Dual trigger rotation prevents both oversized and stale log files
- ✅ Flexible retention policies by log type and severity
- ✅ Automatic compression reduces storage costs
- ✅ Cloud upload provides off-site backup
- ✅ Monitoring ensures rotation is working correctly

The estimated implementation time is **5 weeks** with a monthly operational cost of **$20** for cloud backup storage.

---

**Next Steps:**
1. Review rotation policies with operations team
2. Obtain approval for cloud storage costs
3. Begin Phase 1: Configuration
4. Set up development environment for testing
