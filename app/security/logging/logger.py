"""
Security Logger - Main Integration Point

Provides unified interface for security logging with:
- Automatic redaction of sensitive data
- Hash-chain integrity verification
- SIEM streaming
- Real-time threat detection
- Multiple log schemas (auth, privilege, tool, data, model)

Usage:
    from app.security.logging import security_logger

    # Log authentication event
    await security_logger.log_auth_event(
        event_type="login_success",
        user_id="user_123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0..."
    )
"""

from typing import Any

from app.security.logging.detection import SecurityEventDetector, get_detector
from app.security.logging.integrity import LogIntegrityManager
from app.security.logging.redaction import DataRedactor
from app.security.logging.schemas import (
    AuthEvent,
    DataAccessEvent,
    EventSeverity,
    EventType,
    ModelEvent,
    PrivilegeChangeEvent,
    SecurityEvent,
    ToolInvocationEvent,
)
from app.security.logging.siem import SIEMStreamer


class SecurityLogger:
    """
    Main security logger with integrated redaction, integrity, SIEM, and detection.

    Thread-safe, async, production-ready implementation.
    """

    def __init__(
        self,
        redactor: DataRedactor | None = None,
        integrity_manager: LogIntegrityManager | None = None,
        siem_streamer: SIEMStreamer | None = None,
        detector: SecurityEventDetector | None = None,
        enable_redaction: bool = True,
        enable_integrity: bool = True,
        enable_siem: bool = False,
        enable_detection: bool = True,
    ):
        self.redactor = redactor or DataRedactor()
        self.integrity_manager = integrity_manager
        self.siem_streamer = siem_streamer or SIEMStreamer()
        self.detector = detector or get_detector()

        self.enable_redaction = enable_redaction
        self.enable_integrity = enable_integrity
        self.enable_siem = enable_siem
        self.enable_detection = enable_detection

        # Statistics
        self._stats = {
            "events_logged": 0,
            "events_redacted": 0,
            "alerts_generated": 0,
            "siem_errors": 0,
        }

    async def log_event(self, event: SecurityEvent) -> SecurityEvent:
        """
        Log a generic security event with full processing pipeline.

        Pipeline:
        1. Redact sensitive data
        2. Add to hash chain (integrity)
        3. Write ahead to staging
        4. Run detection rules
        5. Stream to SIEMs
        6. Promote to production

        Args:
            event: Event to log

        Returns:
            Processed event with hashes and detection flags
        """
        try:
            # Step 1: Redact sensitive data
            if self.enable_redaction:
                event = self._redact_event(event)
                self._stats["events_redacted"] += 1

            # Step 2: Add to hash chain
            if self.enable_integrity and self.integrity_manager:
                event = self.integrity_manager.chain_event(event)

            # Step 3: Write ahead to staging
            if self.enable_integrity and self.integrity_manager:
                staging_path = self.integrity_manager.write_ahead(event)
                # Immediately promote to production (in production, do this async)
                if staging_path:
                    self.integrity_manager.promote_to_production(staging_path)

            # Step 4: Run detection rules
            if self.enable_detection:
                alerts = self.detector.analyze_event(event)
                if alerts:
                    self._stats["alerts_generated"] += len(alerts)
                    # Mark event as suspicious if alerts generated
                    event.is_suspicious = True
                    event.detection_rules_matched = [alert.rule_id for alert in alerts]

                    # TODO: Send alerts to notification system (Slack, PagerDuty, etc.)

            # Step 5: Stream to SIEM
            if self.enable_siem:
                try:
                    await self.siem_streamer.send_event(event)
                except Exception as e:
                    logger.error(f"Error sending to SIEM: {e}")
                    self._stats["siem_errors"] += 1

            # Update stats
            self._stats["events_logged"] += 1

            return event

        except Exception as e:
            logger.error(f"Error logging event: {e}")
            # Don't raise - logging failures shouldn't break application
            return event

    def _redact_event(self, event: SecurityEvent) -> SecurityEvent:
        """Redact sensitive data from event"""
        # Redact description
        if event.description:
            event.description = self.redactor.redact_string(event.description)

        # Redact metadata
        if event.metadata:
            event.metadata = self.redactor.redact_dict(event.metadata)

        # Redactor-specific fields based on event type
        if isinstance(event, ToolInvocationEvent):
            # Redact parameters
            if event.parameters:
                event.parameters = self.redactor.redact_dict(event.parameters)

            # Redact error messages (may contain paths or credentials)
            if event.error_message:
                event.error_message = self.redactor.redact_string(event.error_message)

        elif isinstance(event, ModelEvent):
            # Create safe previews (already redacted in ModelEvent creation)
            # But double-redact here
            if event.prompt_preview:
                event.prompt_preview = self.redactor.redact_string(event.prompt_preview)
            if event.response_preview:
                event.response_preview = self.redactor.redact_string(
                    event.response_preview
                )

        elif isinstance(event, DataAccessEvent):
            # Redact filters
            if event.filters:
                event.filters = self.redactor.redact_dict(event.filters)

        return event

    async def log_auth_event(
        self,
        event_type: EventType,
        user_id: str | None = None,
        username: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        auth_method: str | None = None,
        mfa_verified: bool = False,
        failure_reason: str | None = None,
        is_anomalous: bool = False,
        risk_score: float = 0.0,
        **kwargs,
    ) -> AuthEvent:
        """
        Log authentication event.

        Args:
            event_type: Type of auth event
            user_id: User ID
            username: Username
            ip_address: IP address
            user_agent: User agent string
            session_id: Session ID
            auth_method: Authentication method (password, oauth, etc.)
            mfa_verified: Whether MFA was verified
            failure_reason: Reason for failure (if applicable)
            is_anomalous: Whether event is anomalous
            risk_score: Risk score (0-100)
            **kwargs: Additional fields

        Returns:
            Logged AuthEvent
        """
        # Map event type to severity
        severity = self._get_auth_severity(event_type)

        event = AuthEvent(
            event_type=event_type,
            severity=severity,
            actor_user_id=user_id,
            actor_username=username,
            actor_ip_address=ip_address,
            actor_user_agent=user_agent,
            actor_session_id=session_id,
            auth_method=auth_method,
            mfa_verified=mfa_verified,
            failure_reason=failure_reason,
            is_anomalous=is_anomalous,
            risk_score=risk_score,
            description=f"Authentication event: {event_type.value}",
            metadata=kwargs,
        )

        return await self.log_event(event)

    async def log_privilege_change(
        self,
        user_id: str,
        action: str,
        target_user_id: str,
        target_username: str | None = None,
        old_role: str | None = None,
        new_role: str | None = None,
        permission_name: str | None = None,
        permission_resource: str | None = None,
        permission_action: str | None = None,
        reason: str | None = None,
        approval_ticket: str | None = None,
        approved_by: str | None = None,
        scope: str = "user",
        organization_id: str | None = None,
        team_id: str | None = None,
        **kwargs,
    ) -> PrivilegeChangeEvent:
        """
        Log privilege change event.

        Args:
            user_id: ID of user making the change
            action: Action taken (role_granted, role_revoked, etc.)
            target_user_id: ID of user whose privileges are being changed
            target_username: Username of target user
            old_role: Previous role
            new_role: New role
            permission_name: Permission name (if permission change)
            permission_resource: Resource permission applies to
            permission_action: Action (grant, revoke, modify)
            reason: Reason for change
            approval_ticket: Approval ticket reference
            approved_by: Who approved the change
            scope: Scope of change (user, team, organization, global)
            organization_id: Organization ID
            team_id: Team ID
            **kwargs: Additional fields

        Returns:
            Logged PrivilegeChangeEvent
        """
        # Map action to event type
        event_type_map = {
            "role_granted": EventType.PRIV_ROLE_GRANTED,
            "role_revoked": EventType.PRIV_ROLE_REVOKED,
            "permission_granted": EventType.PRIV_PERMISSION_GRANTED,
            "permission_revoked": EventType.PRIV_PERMISSION_REVOKED,
        }
        event_type = event_type_map.get(action, EventType.PRIV_ROLE_GRANTED)

        event = PrivilegeChangeEvent(
            event_type=event_type,
            severity=EventSeverity.HIGH,  # Privilege changes are always high severity
            actor_user_id=user_id,
            target_user_id=target_user_id,
            target_username=target_username,
            target_old_role=old_role,
            target_new_role=new_role,
            permission_name=permission_name,
            permission_resource=permission_resource,
            permission_action=permission_action,
            reason=reason,
            approval_ticket=approval_ticket,
            approved_by=approved_by,
            scope=scope,
            organization_id=organization_id,
            team_id=team_id,
            description=f"Privilege change: {action} on {target_user_id}",
            metadata=kwargs,
        )

        return await self.log_event(event)

    async def log_tool_invocation(
        self,
        tool_name: str,
        user_id: str | None = None,
        parameters: dict[str, Any] | None = None,
        execution_time_ms: int | None = None,
        result_count: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        agent_id: str | None = None,
        agent_type: str | None = None,
        conversation_id: str | None = None,
        is_abnormal: bool = False,
        abnormality_reason: str | None = None,
        **kwargs,
    ) -> ToolInvocationEvent:
        """
        Log tool/agent invocation event.

        Args:
            tool_name: Name of tool being invoked
            user_id: User ID invoking the tool
            parameters: Tool parameters (will be redacted)
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
            error_type: Type of error (if failed)
            error_message: Error message
            agent_id: Agent ID (if invoked by agent)
            agent_type: Agent type (claude, gpt, custom)
            conversation_id: Conversation ID
            is_abnormal: Whether invocation is abnormal
            abnormality_reason: Reason if abnormal
            **kwargs: Additional fields

        Returns:
            Logged ToolInvocationEvent
        """
        # Determine event type and severity
        if error_type:
            event_type = EventType.TOOL_INVOCATION_FAILED
            severity = EventSeverity.MEDIUM
        elif is_abnormal:
            event_type = EventType.TOOL_INVOCATION_BLOCKED
            severity = EventSeverity.HIGH
        else:
            event_type = EventType.TOOL_INVOCATION
            severity = EventSeverity.INFO

        event = ToolInvocationEvent(
            event_type=event_type,
            severity=severity,
            actor_user_id=user_id,
            tool_name=tool_name,
            parameters=parameters or {},
            execution_time_ms=execution_time_ms,
            result_count=result_count,
            error_type=error_type,
            error_message=error_message,
            agent_id=agent_id,
            agent_type=agent_type,
            conversation_id=conversation_id,
            is_abnormal=is_abnormal,
            abnormality_reason=abnormality_reason,
            description=f"Tool invocation: {tool_name}",
            metadata=kwargs,
        )

        return await self.log_event(event)

    async def log_data_access(
        self,
        user_id: str | None = None,
        data_type: str = "unknown",
        data_classification: str = "internal",
        access_method: str = "api",
        query_type: str | None = None,
        query_pattern: str | None = None,
        record_count: int | None = None,
        filters: dict[str, Any] | None = None,
        fields_accessed: list[str] | None = None,
        is_bulk_access: bool = False,
        export_format: str | None = None,
        export_destination: str | None = None,
        export_size_bytes: int | None = None,
        export_record_count: int | None = None,
        **kwargs,
    ) -> DataAccessEvent:
        """
        Log data access event.

        Args:
            user_id: User ID accessing data
            data_type: Type of data (user_profile, assessment_results, etc.)
            data_classification: Classification (public, internal, confidential, restricted)
            access_method: Method of access (api, webui, cli, integration)
            query_type: Type of query (select, insert, update, delete)
            query_pattern: Query pattern (for detection)
            record_count: Number of records accessed
            filters: Filters applied
            fields_accessed: List of fields accessed
            is_bulk_access: Whether this is bulk access
            export_format: Format of export (if export)
            export_destination: Destination of export
            export_size_bytes: Size of export in bytes
            export_record_count: Number of records in export
            **kwargs: Additional fields

        Returns:
            Logged DataAccessEvent
        """
        # Determine event type
        if export_format:
            event_type = EventType.DATA_EXPORT
            severity = EventSeverity.MEDIUM
        elif is_bulk_access:
            event_type = EventType.DATA_BULK_ACCESS
            severity = EventSeverity.HIGH
        elif query_type == "delete":
            event_type = EventType.DATA_ACCESS_DELETE
            severity = EventSeverity.HIGH
        elif query_type in ["insert", "update"]:
            event_type = EventType.DATA_ACCESS_WRITE
            severity = EventSeverity.MEDIUM
        else:
            event_type = EventType.DATA_ACCESS_READ
            severity = EventSeverity.LOW

        event = DataAccessEvent(
            event_type=event_type,
            severity=severity,
            actor_user_id=user_id,
            data_type=data_type,
            data_classification=data_classification,
            access_method=access_method,
            query_type=query_type,
            query_pattern=query_pattern,
            record_count=record_count,
            filters=filters or {},
            fields_accessed=fields_accessed or [],
            is_bulk_access=is_bulk_access,
            export_format=export_format,
            export_destination=export_destination,
            export_size_bytes=export_size_bytes,
            export_record_count=export_record_count,
            description=f"Data access: {query_type} on {data_type}",
            metadata=kwargs,
        )

        return await self.log_event(event)

    async def log_model_event(
        self,
        model_name: str,
        user_id: str | None = None,
        prompt: str | None = None,
        response: str | None = None,
        prompt_tokens: int | None = None,
        response_tokens: int | None = None,
        tools_used: list[str] | None = None,
        latency_ms: int | None = None,
        safety_score: float | None = None,
        flagged_content: list[str] | None = None,
        injection_indicators: list[str] | None = None,
        cache_hit: bool = False,
        **kwargs,
    ) -> ModelEvent:
        """
        Log model/AI event with automatic redaction.

        Args:
            model_name: Name of model
            user_id: User ID
            prompt: Model prompt (will be redacted and hashed)
            response: Model response (will be redacted and hashed)
            prompt_tokens: Number of prompt tokens
            response_tokens: Number of response tokens
            tools_used: List of tools used
            latency_ms: Latency in milliseconds
            safety_score: Safety score (0-1)
            flagged_content: List of flagged content
            injection_indicators: List of injection indicators found
            cache_hit: Whether response was cached
            **kwargs: Additional fields

        Returns:
            Logged ModelEvent
        """
        import hashlib

        # Redact and hash prompt for integrity
        prompt_preview = None
        prompt_hash = None
        prompt_length = 0

        if prompt:
            prompt_length = len(prompt)
            prompt_preview = self.redactor.create_safe_preview(prompt, max_length=100)
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

        # Redact and hash response
        response_preview = None
        response_hash = None
        response_length = 0

        if response:
            response_length = len(response)
            response_preview = self.redactor.create_safe_preview(
                response, max_length=100
            )
            response_hash = hashlib.sha256(response.encode()).hexdigest()

        # Determine event type and severity
        if injection_indicators:
            event_type = EventType.MODEL_INJECTION_ATTEMPT
            severity = EventSeverity.CRITICAL
        elif flagged_content:
            event_type = EventType.MODEL_SAFETY_VIOLATION
            severity = EventSeverity.HIGH
        else:
            event_type = EventType.MODEL_PROMPT
            severity = EventSeverity.INFO

        event = ModelEvent(
            event_type=event_type,
            severity=severity,
            actor_user_id=user_id,
            model_name=model_name,
            prompt_length=prompt_length,
            prompt_tokens=prompt_tokens,
            prompt_hash=prompt_hash,
            prompt_preview=prompt_preview,
            response_length=response_length,
            response_tokens=response_tokens,
            response_hash=response_hash,
            response_preview=response_preview,
            tools_used=tools_used or [],
            tool_results_count=len(tools_used) if tools_used else 0,
            latency_ms=latency_ms,
            safety_score=safety_score,
            flagged_content=flagged_content or [],
            injection_indicators=injection_indicators or [],
            cache_hit=cache_hit,
            description=f"Model event: {model_name}",
            metadata=kwargs,
        )

        return await self.log_event(event)

    def _get_auth_severity(self, event_type: EventType) -> EventSeverity:
        """Map auth event type to severity"""
        high_severity = [
            EventType.AUTH_LOGIN_FAILURE,
            EventType.AUTH_MFA_DISABLED,
        ]

        medium_severity = [
            EventType.AUTH_PASSWORD_CHANGE,
            EventType.AUTH_TOKEN_REFRESH,
        ]

        if event_type in high_severity:
            return EventSeverity.HIGH
        if event_type in medium_severity:
            return EventSeverity.MEDIUM
        return EventSeverity.INFO

    async def get_alerts(
        self, severity: EventSeverity | None = None, limit: int = 100
    ) -> list[Any]:
        """Get detection alerts"""
        return self.detector.get_alerts(severity=severity, limit=limit)

    def get_stats(self) -> dict[str, Any]:
        """Get logging statistics"""
        stats = {
            **self._stats,
            "integrity": (
                self.integrity_manager.get_integrity_report()
                if self.integrity_manager
                else {}
            ),
            "detection": self.detector.get_stats(),
            "siem": self.siem_streamer.get_stats() if self.enable_siem else {},
        }
        return stats

    async def shutdown(self):
        """Cleanup resources"""
        if self.siem_streamer:
            await self.siem_streamer.flush_all()
            await self.siem_streamer.close()


# Singleton instance
_default_logger = None


def get_security_logger() -> SecurityLogger:
    """Get default security logger instance"""
    global _default_logger
    if _default_logger is None:
        _default_logger = SecurityLogger()
    return _default_logger


# Global instance for easy import
security_logger = get_security_logger()


# Helper functions for quick logging
async def log_auth(event_type: EventType, user_id: str, **kwargs) -> AuthEvent:
    """Quick auth logging"""
    return await security_logger.log_auth_event(event_type, user_id, **kwargs)


async def log_privilege_change(
    user_id: str, target_user_id: str, action: str, **kwargs
) -> PrivilegeChangeEvent:
    """Quick privilege change logging"""
    return await security_logger.log_privilege_change(
        user_id=user_id, target_user_id=target_user_id, action=action, **kwargs
    )


async def log_tool_invocation(
    tool_name: str, user_id: str | None = None, **kwargs
) -> ToolInvocationEvent:
    """Quick tool invocation logging"""
    return await security_logger.log_tool_invocation(
        tool_name=tool_name, user_id=user_id, **kwargs
    )


async def log_data_access(
    user_id: str | None = None, data_type: str = "unknown", **kwargs
) -> DataAccessEvent:
    """Quick data access logging"""
    return await security_logger.log_data_access(
        user_id=user_id, data_type=data_type, **kwargs
    )


async def log_model_event(
    model_name: str, prompt: str | None = None, **kwargs
) -> ModelEvent:
    """Quick model event logging"""
    return await security_logger.log_model_event(
        model_name=model_name, prompt=prompt, **kwargs
    )
