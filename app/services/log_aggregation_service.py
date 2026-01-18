"""
Log Aggregation Service
Provides comprehensive log collection, processing, and analysis capabilities
for centralized logging across all application components.
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import gzip
import json
import logging
import re
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels following RFC 5424"""
    EMERGENCY = 0  # System is unusable
    ALERT = 1      # Action must be taken immediately
    CRITICAL = 2   # Critical conditions
    ERROR = 3      # Error conditions
    WARNING = 4    # Warning conditions
    NOTICE = 5     # Normal but significant condition
    INFO = 6       # Informational messages
    DEBUG = 7      # Debug-level messages


class LogSource(Enum):
    """Sources of log data"""
    APPLICATION = "application"
    WEB_SERVER = "web_server"
    DATABASE = "database"
    CACHE = "cache"
    SECURITY = "security"
    AUDIT = "audit"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"


class LogFormat(Enum):
    """Supported log formats"""
    JSON = "json"
    PLAIN_TEXT = "plain_text"
    STRUCTURED = "structured"
    SYSLOG = "syslog"
    CEF = "cef"  # Common Event Format
    LEEF = "leef"  # Log Event Extended Format


@dataclass
class LogEntry:
    """Individual log entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    level: LogLevel = LogLevel.INFO
    source: LogSource = LogSource.APPLICATION
    service: str = ""
    message: str = ""
    raw_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    trace_id: str | None = None
    span_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    environment: str = "production"
    hostname: str | None = None
    process_id: int | None = None
    thread_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert log entry to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "level_name": self.level.name,
            "source": self.source.value,
            "service": self.service,
            "message": self.message,
            "raw_message": self.raw_message,
            "metadata": self.metadata,
            "tags": self.tags,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "environment": self.environment,
            "hostname": self.hostname,
            "process_id": self.process_id,
            "thread_id": self.thread_id
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create log entry from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            level=LogLevel(data.get("level", LogLevel.INFO.value)),
            source=LogSource(data.get("source", LogSource.APPLICATION.value)),
            service=data.get("service", ""),
            message=data.get("message", ""),
            raw_message=data.get("raw_message", ""),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            correlation_id=data.get("correlation_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            environment=data.get("environment", "production"),
            hostname=data.get("hostname"),
            process_id=data.get("process_id"),
            thread_id=data.get("thread_id")
        )


@dataclass
class LogQuery:
    """Query parameters for log search"""
    search_term: str | None = None
    levels: list[LogLevel] | None = None
    sources: list[LogSource] | None = None
    services: list[str] | None = None
    tags: list[str] | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    user_id: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    metadata_filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 1000
    offset: int = 0
    sort_by: str = "timestamp"
    sort_order: str = "desc"

    def to_dict(self) -> dict[str, Any]:
        """Convert query to dictionary"""
        return {
            "search_term": self.search_term,
            "levels": [l.value for l in self.levels] if self.levels else None,
            "sources": [s.value for s in self.sources] if self.sources else None,
            "services": self.services,
            "tags": self.tags,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "user_id": self.user_id,
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "metadata_filters": self.metadata_filters,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order
        }


@dataclass
class LogStats:
    """Log statistics for a time period"""
    total_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0
    level_distribution: dict[str, int] = field(default_factory=dict)
    source_distribution: dict[str, int] = field(default_factory=dict)
    service_distribution: dict[str, int] = field(default_factory=dict)
    hourly_distribution: dict[str, int] = field(default_factory=dict)
    top_errors: list[dict[str, Any]] = field(default_factory=list)
    top_services: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "total_count": self.total_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "level_distribution": self.level_distribution,
            "source_distribution": self.source_distribution,
            "service_distribution": self.service_distribution,
            "hourly_distribution": self.hourly_distribution,
            "top_errors": self.top_errors,
            "top_services": self.top_services
        }


class LogAggregationService:
    """Comprehensive log aggregation service"""

    def __init__(self):
        # In-memory log storage (in production, this would be a dedicated log store)
        self._log_store = deque(maxlen=100000)  # Store last 100K logs
        self._log_index = defaultdict(set)  # Search indexes

        # Background processing
        self._processing_queue = asyncio.Queue()
        self._background_tasks = []
        self._running = False

        # Log parsers for different formats
        self._parsers = {
            LogFormat.JSON: self._parse_json_log,
            LogFormat.PLAIN_TEXT: self._parse_plain_text_log,
            LogFormat.STRUCTURED: self._parse_structured_log,
            LogFormat.SYSLOG: self._parse_syslog_log
        }

        # Log retention settings
        self._retention_days = 30
        self._cleanup_interval = 3600  # 1 hour

        # Statistics cache
        self._stats_cache = {}
        self._stats_cache_ttl = 300  # 5 minutes

        logger.info("Log aggregation service initialized")

    async def start(self) -> None:
        """Start the log aggregation service"""
        if self._running:
            return

        self._running = True

        # Start background processing tasks
        processor_task = asyncio.create_task(self._process_log_queue())
        cleaner_task = asyncio.create_task(self._cleanup_old_logs())

        self._background_tasks = [processor_task, cleaner_task]

        logger.info("Log aggregation service started")

    async def stop(self) -> None:
        """Stop the log aggregation service"""
        self._running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

        logger.info("Log aggregation service stopped")

    async def ingest_log(
        self,
        log_data: str | dict[str, Any],
        source: LogSource = LogSource.APPLICATION,
        format: LogFormat = LogFormat.JSON,
        service: str = "",
        metadata: dict[str, Any] | None = None
    ) -> str:
        """Ingest a log entry"""
        try:
            # Parse the log entry
            if format == LogFormat.JSON and isinstance(log_data, dict):
                log_entry = LogEntry.from_dict(log_data)
            else:
                log_entry = await self._parse_log_entry(log_data, format, source, service)

            # Apply metadata
            if metadata:
                log_entry.metadata.update(metadata)

            # Add to processing queue
            await self._processing_queue.put(log_entry)

            logger.debug(f"Ingested log: {log_entry.id}")
            return log_entry.id

        except Exception as e:
            logger.error(f"Failed to ingest log: {e!s}")
            raise

    async def ingest_logs_batch(
        self,
        logs: list[str | dict[str, Any]],
        source: LogSource = LogSource.APPLICATION,
        format: LogFormat = LogFormat.JSON,
        service: str = "",
        metadata: dict[str, Any] | None = None
    ) -> list[str]:
        """Ingest multiple log entries"""
        log_ids = []

        for log_data in logs:
            try:
                log_id = await self.ingest_log(log_data, source, format, service, metadata)
                log_ids.append(log_id)
            except Exception as e:
                logger.error(f"Failed to ingest log in batch: {e!s}")
                continue

        return log_ids

    async def search_logs(self, query: LogQuery) -> list[LogEntry]:
        """Search logs based on query parameters"""
        try:
            # Get logs from store (in production, query from log database)
            logs = list(self._log_store)

            # Apply filters
            filtered_logs = []

            for log in logs:
                if not self._matches_query(log, query):
                    continue

                filtered_logs.append(log)

            # Sort logs
            if query.sort_by == "timestamp":
                filtered_logs.sort(
                    key=lambda x: getattr(x, query.sort_by),
                    reverse=(query.sort_order == "desc")
                )
            elif query.sort_by == "level":
                filtered_logs.sort(
                    key=lambda x: x.level.value,
                    reverse=(query.sort_order == "desc")
                )

            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit

            return filtered_logs[start_idx:end_idx]

        except Exception as e:
            logger.error(f"Log search failed: {e!s}")
            return []

    async def get_log_by_id(self, log_id: str) -> LogEntry | None:
        """Get a specific log entry by ID"""
        # In production, query from log database
        for log in self._log_store:
            if log.id == log_id:
                return log

        return None

    async def get_logs_by_trace_id(self, trace_id: str) -> list[LogEntry]:
        """Get all logs for a specific trace"""
        query = LogQuery(trace_id=trace_id, limit=1000)
        return await self.search_logs(query)

    async def get_logs_by_user_id(self, user_id: str, limit: int = 1000) -> list[LogEntry]:
        """Get logs for a specific user"""
        query = LogQuery(user_id=user_id, limit=limit)
        return await self.search_logs(query)

    async def get_log_stats(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> LogStats:
        """Get log statistics for a time period"""
        try:
            # Check cache
            cache_key = f"stats:{start_time}_{end_time}"
            cached = self._stats_cache.get(cache_key)

            if cached and not self._is_stats_cache_expired(cache_key):
                return cached

            # Calculate statistics
            logs = list(self._log_store)
            if start_time:
                logs = [log for log in logs if log.timestamp >= start_time]
            if end_time:
                logs = [log for log in logs if log.timestamp <= end_time]

            stats = LogStats(total_count=len(logs))

            # Calculate distributions
            level_dist = defaultdict(int)
            source_dist = defaultdict(int)
            service_dist = defaultdict(int)
            hourly_dist = defaultdict(int)
            error_messages = defaultdict(int)
            service_errors = defaultdict(int)

            for log in logs:
                # Level distribution
                level_dist[log.level.name] += 1
                if log.level == LogLevel.ERROR:
                    stats.error_count += 1
                    error_messages[log.message[:100]] += 1
                elif log.level == LogLevel.WARNING:
                    stats.warning_count += 1
                elif log.level == LogLevel.INFO:
                    stats.info_count += 1
                elif log.level == LogLevel.DEBUG:
                    stats.debug_count += 1

                # Source distribution
                source_dist[log.source.value] += 1

                # Service distribution
                if log.service:
                    service_dist[log.service] += 1
                    if log.level == LogLevel.ERROR:
                        service_errors[log.service] += 1

                # Hourly distribution
                hour_key = log.timestamp.strftime("%Y-%m-%d %H:00")
                hourly_dist[hour_key] += 1

            # Convert to regular dicts
            stats.level_distribution = dict(level_dist)
            stats.source_distribution = dict(source_dist)
            stats.service_distribution = dict(service_dist)
            stats.hourly_distribution = dict(hourly_dist)

            # Top errors
            stats.top_errors = [
                {"message": msg, "count": count}
                for msg, count in sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Top services by error count
            stats.top_services = [
                {"service": service, "error_count": count}
                for service, count in sorted(service_errors.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Cache the result
            self._stats_cache[cache_key] = {
                "stats": stats,
                "timestamp": datetime.utcnow()
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get log statistics: {e!s}")
            return LogStats()

    async def export_logs(
        self,
        query: LogQuery,
        format: str = "json",
        compress: bool = True
    ) -> bytes:
        """Export logs to file"""
        try:
            # Get matching logs
            logs = await self.search_logs(query)

            # Convert to desired format
            if format == "json":
                export_data = [log.to_dict() for log in logs]
                content = json.dumps(export_data, indent=2).encode("utf-8")
            elif format == "csv":
                # Simple CSV export
                import csv
                import io

                output = io.StringIO()
                if logs:
                    fieldnames = logs[0].to_dict().keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    for log in logs:
                        writer.writerow(log.to_dict())

                content = output.getvalue().encode("utf-8")
            else:
                raise ValueError(f"Unsupported export format: {format}")

            # Compress if requested
            if compress:
                content = gzip.compress(content)

            return content

        except Exception as e:
            logger.error(f"Log export failed: {e!s}")
            raise

    async def create_log_alert(
        self,
        name: str,
        conditions: dict[str, Any],
        notification_channels: list[str],
        enabled: bool = True
    ) -> str:
        """Create a log-based alert rule"""
        # TODO: Implement log alert rules
        # This would integrate with the alerts service
        alert_id = str(uuid.uuid4())

        logger.info(f"Created log alert: {alert_id}")
        return alert_id

    async def _process_log_queue(self) -> None:
        """Background task to process incoming logs"""
        while self._running:
            try:
                # Wait for log entry with timeout
                log_entry = await asyncio.wait_for(
                    self._processing_queue.get(),
                    timeout=1.0
                )

                # Process the log entry
                await self._process_log_entry(log_entry)

            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing log queue: {e!s}")
                await asyncio.sleep(1)

    async def _process_log_entry(self, log_entry: LogEntry) -> None:
        """Process a single log entry"""
        try:
            # Add to store
            self._log_store.append(log_entry)

            # Update indexes
            self._update_indexes(log_entry)

            # Check for alerts
            await self._check_log_alerts(log_entry)

            logger.debug(f"Processed log entry: {log_entry.id}")

        except Exception as e:
            logger.error(f"Failed to process log entry {log_entry.id}: {e!s}")

    async def _parse_log_entry(
        self,
        log_data: str,
        format: LogFormat,
        source: LogSource,
        service: str
    ) -> LogEntry:
        """Parse log entry from string data"""
        parser = self._parsers.get(format)
        if not parser:
            raise ValueError(f"Unsupported log format: {format}")

        return await parser(log_data, source, service)

    async def _parse_json_log(
        self,
        log_data: str,
        source: LogSource,
        service: str
    ) -> LogEntry:
        """Parse JSON log entry"""
        try:
            data = json.loads(log_data)

            # Extract standard fields
            timestamp = data.get("timestamp")
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                timestamp = datetime.utcnow()

            level = LogLevel(data.get("level", LogLevel.INFO.value))
            message = data.get("message", "")

            # Create log entry
            log_entry = LogEntry(
                timestamp=timestamp,
                level=level,
                source=source,
                service=service,
                message=message,
                raw_message=log_data,
                metadata={k: v for k, v in data.items()
                         if k not in ["timestamp", "level", "message"]},
                tags=data.get("tags", []),
                trace_id=data.get("trace_id"),
                span_id=data.get("span_id"),
                user_id=data.get("user_id"),
                session_id=data.get("session_id"),
                request_id=data.get("request_id"),
                correlation_id=data.get("correlation_id"),
                ip_address=data.get("ip_address"),
                user_agent=data.get("user_agent"),
                environment=data.get("environment", "production"),
                hostname=data.get("hostname"),
                process_id=data.get("process_id"),
                thread_id=data.get("thread_id")
            )

            return log_entry

        except Exception as e:
            # Fallback to plain text parsing
            logger.warning(f"Failed to parse JSON log, falling back to plain text: {e!s}")
            return await self._parse_plain_text_log(log_data, source, service)

    async def _parse_plain_text_log(
        self,
        log_data: str,
        source: LogSource,
        service: str
    ) -> LogEntry:
        """Parse plain text log entry"""
        # Try to extract common log patterns
        timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})", log_data)
        level_match = re.search(r"\b(DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|CRITICAL|ALERT|EMERGENCY)\b", log_data, re.IGNORECASE)

        timestamp = None
        if timestamp_match:
            try:
                timestamp_str = timestamp_match.group(1).replace(" ", "T")
                if "T" in timestamp_str and "+" not in timestamp_str:
                    timestamp_str += "Z"
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception as e:
                pass

        level = LogLevel.INFO
        if level_match:
            level_str = level_match.group(1).upper()
            try:
                level = LogLevel[level_str]
            except KeyError:
                level = LogLevel.WARNING if level_str == "WARN" else LogLevel.ERROR if level_str == "CRITICAL" else LogLevel.INFO

        return LogEntry(
            timestamp=timestamp or datetime.utcnow(),
            level=level,
            source=source,
            service=service,
            message=log_data,
            raw_message=log_data,
            hostname="unknown"  # Could extract from log patterns
        )

    async def _parse_structured_log(
        self,
        log_data: str,
        source: LogSource,
        service: str
    ) -> LogEntry:
        """Parse structured log entry (key=value format)"""
        # Parse key=value pairs
        parts = log_data.split()
        metadata = {}
        message_parts = []

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                metadata[key] = value.strip('"\'')
            else:
                message_parts.append(part)

        message = " ".join(message_parts)

        # Try to extract timestamp and level from metadata
        timestamp = None
        if "timestamp" in metadata:
            try:
                timestamp = datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00"))
            except Exception as e:
                pass

        level = LogLevel.INFO
        if "level" in metadata:
            try:
                level = LogLevel[metadata["level"].upper()]
            except Exception as e:
                pass

        return LogEntry(
            timestamp=timestamp or datetime.utcnow(),
            level=level,
            source=source,
            service=service,
            message=message,
            raw_message=log_data,
            metadata=metadata,
            trace_id=metadata.get("trace_id"),
            span_id=metadata.get("span_id"),
            user_id=metadata.get("user_id"),
            request_id=metadata.get("request_id")
        )

    async def _parse_syslog_log(
        self,
        log_data: str,
        source: LogSource,
        service: str
    ) -> LogEntry:
        """Parse syslog format log entry"""
        # Basic syslog parsing (RFC 3164 format)
        # <priority>timestamp hostname tag: message
        priority_match = re.match(r"^<(\d+)>", log_data)

        if priority_match:
            priority = int(priority_match.group(1))
            facility = priority >> 3
            severity = priority & 0x07

            # Map syslog severity to our log levels
            level_mapping = {
                0: LogLevel.EMERGENCY,  # Emergency
                1: LogLevel.ALERT,      # Alert
                2: LogLevel.CRITICAL,   # Critical
                3: LogLevel.ERROR,      # Error
                4: LogLevel.WARNING,    # Warning
                5: LogLevel.NOTICE,     # Notice
                6: LogLevel.INFO,       # Informational
                7: LogLevel.DEBUG       # Debug
            }

            level = level_mapping.get(severity, LogLevel.INFO)

            # Remove priority from log_data for further parsing
            remaining_log = log_data[priority_match.end():]
        else:
            level = LogLevel.INFO
            remaining_log = log_data

        return LogEntry(
            timestamp=datetime.utcnow(),  # Could extract timestamp from syslog
            level=level,
            source=source,
            service=service,
            message=remaining_log,
            raw_message=log_data,
            metadata={"syslog_facility": facility if "priority_match" in locals() else None}
        )

    def _update_indexes(self, log_entry: LogEntry) -> None:
        """Update search indexes for log entry"""
        # Index by level
        self._log_index[f"level:{log_entry.level.value}"].add(log_entry.id)

        # Index by source
        self._log_index[f"source:{log_entry.source.value}"].add(log_entry.id)

        # Index by service
        if log_entry.service:
            self._log_index[f"service:{log_entry.service}"].add(log_entry.id)

        # Index by user
        if log_entry.user_id:
            self._log_index[f"user:{log_entry.user_id}"].add(log_entry.id)

        # Index by trace
        if log_entry.trace_id:
            self._log_index[f"trace:{log_entry.trace_id}"].add(log_entry.id)

        # Index by tags
        for tag in log_entry.tags:
            self._log_index[f"tag:{tag}"].add(log_entry.id)

    def _matches_query(self, log_entry: LogEntry, query: LogQuery) -> bool:
        """Check if log entry matches query criteria"""
        # Time range
        if query.start_time and log_entry.timestamp < query.start_time:
            return False
        if query.end_time and log_entry.timestamp > query.end_time:
            return False

        # Level filter
        if query.levels and log_entry.level not in query.levels:
            return False

        # Source filter
        if query.sources and log_entry.source not in query.sources:
            return False

        # Service filter
        if query.services and log_entry.service not in query.services:
            return False

        # Tags filter
        if query.tags:
            if not any(tag in log_entry.tags for tag in query.tags):
                return False

        # User filter
        if query.user_id and log_entry.user_id != query.user_id:
            return False

        # Trace filter
        if query.trace_id and log_entry.trace_id != query.trace_id:
            return False

        # Request filter
        if query.request_id and log_entry.request_id != query.request_id:
            return False

        # Search term
        if query.search_term:
            search_lower = query.search_term.lower()
            if (search_lower not in log_entry.message.lower() and
                search_lower not in log_entry.raw_message.lower()):
                return False

        # Metadata filters
        for key, value in query.metadata_filters.items():
            if log_entry.metadata.get(key) != value:
                return False

        return True

    async def _check_log_alerts(self, log_entry: LogEntry) -> None:
        """Check if log entry triggers any alerts"""
        # TODO: Implement log alert checking
        # This would evaluate log-based alert rules and trigger notifications

    async def _cleanup_old_logs(self) -> None:
        """Background task to clean up old logs"""
        while self._running:
            try:
                # Calculate cutoff time
                cutoff_time = datetime.utcnow() - timedelta(days=self._retention_days)

                # Remove old logs from store
                initial_count = len(self._log_store)
                while self._log_store and self._log_store[0].timestamp < cutoff_time:
                    old_log = self._log_store.popleft()
                    self._remove_from_indexes(old_log)

                removed_count = initial_count - len(self._log_store)

                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old log entries")

                # Clean up expired stats cache
                expired_keys = [
                    key for key, cached in self._stats_cache.items()
                    if self._is_stats_cache_expired(key)
                ]

                for key in expired_keys:
                    del self._stats_cache[key]

                # Wait for next cleanup
                await asyncio.sleep(self._cleanup_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during log cleanup: {e!s}")
                await asyncio.sleep(60)

    def _remove_from_indexes(self, log_entry: LogEntry) -> None:
        """Remove log entry from search indexes"""
        log_id = log_entry.id

        # Remove from all indexes
        keys_to_remove = [key for key, log_ids in self._log_index.items() if log_id in log_ids]
        for key in keys_to_remove:
            self._log_index[key].discard(log_id)
            if not self._log_index[key]:
                del self._log_index[key]

    def _is_stats_cache_expired(self, cache_key: str) -> bool:
        """Check if stats cache entry is expired"""
        cached = self._stats_cache.get(cache_key)
        if not cached:
            return True

        age = datetime.utcnow() - cached["timestamp"]
        return age.total_seconds() > self._stats_cache_ttl

    # Utility methods for external integration

    def get_default_log_config(self) -> dict[str, Any]:
        """Get default logging configuration for application integration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
                },
                "structured": {
                    "format": '%(asctime)s level=%(levelname)s logger=%(name)s message="%(message)s" pathname=%(pathname)s lineno=%(lineno)d'
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "level": "INFO",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "json",
                    "level": "DEBUG",
                    "filename": "logs/application.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file"]
            }
        }


# Export the main service class
__all__ = [
    "LogAggregationService",
    "LogEntry",
    "LogFormat",
    "LogLevel",
    "LogQuery",
    "LogSource",
    "LogStats"
]
