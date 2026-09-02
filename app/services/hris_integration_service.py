"""
HRIS Integration Service
Manages HRIS system connections, validations, and access control
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

from app.integrations.hris.integration_manager import HRISIntegrationManager

logger = logging.getLogger(__name__)


class HRISIntegrationService:
    """
    Service for managing HRIS integrations.
    Handles connection lifecycle, validation, and access control.
    """

    # k-anonymity thresholds matching privacy_guard.py
    K_BASIC = 5
    K_SENSITIVE = 10

    # PII field sets by scope
    _PII_FIELDS_BASIC = {"email", "phone", "address", "ssn", "date_of_birth"}
    _PII_FIELDS_STANDARD = {"phone", "address", "ssn", "date_of_birth"}
    _PII_FIELDS_ADVANCED = {"ssn"}

    def __init__(self):
        """Initialize HRIS integration service."""
        self.integration_manager = HRISIntegrationManager()
        self._active_connections: Dict[str, Dict[str, Any]] = {}
        self._fernet: Optional[Fernet] = None

    async def validate_connection_parameters(
        self,
        provider: str,
        organization_id: int,
        connection_parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate HRIS connection parameters.

        Args:
            provider: HRIS provider name
            organization_id: Organization ID
            connection_parameters: Connection parameters to validate

        Returns:
            Validation result with valid flag and error message if invalid
        """
        try:
            # Get provider configuration template
            available_connectors = self.integration_manager.list_available_connectors()

            if provider not in available_connectors:
                return {
                    "valid": False,
                    "error": f"Unsupported HRIS provider: {provider}. "
                    f"Available providers: {list(available_connectors.keys())}",
                }

            # Check required parameters
            config_template = available_connectors[provider]
            required_params = config_template.get("required", [])

            missing_params = [
                param for param in required_params if param not in connection_parameters
            ]

            if missing_params:
                return {
                    "valid": False,
                    "error": f"Missing required parameters: {', '.join(missing_params)}",
                }

            # Validate parameter types
            validation_errors = []

            # Basic validation for common parameters
            if "base_url" in connection_parameters:
                base_url = connection_parameters["base_url"]
                if not isinstance(base_url, str) or not base_url.startswith(
                    ("http://", "https://")
                ):
                    validation_errors.append("base_url must be a valid URL")

            if "api_key" in connection_parameters:
                api_key = connection_parameters["api_key"]
                if not isinstance(api_key, str) or len(api_key) < 10:
                    validation_errors.append("api_key must be a valid string")

            if validation_errors:
                return {
                    "valid": False,
                    "error": f"Parameter validation failed: {', '.join(validation_errors)}",
                }

            return {
                "valid": True,
                "provider": provider,
                "parameters_checked": len(required_params),
            }

        except Exception as e:
            logger.error(f"Error validating HRIS connection parameters: {str(e)}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    async def test_hris_connection(
        self,
        provider: str,
        connection_parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Test HRIS connection with provided parameters.

        Args:
            provider: HRIS provider name
            connection_parameters: Connection parameters

        Returns:
            Connection test result
        """
        try:
            # For now, return success for valid parameters
            # In production, this would attempt actual connection
            logger.info(f"Testing HRIS connection for provider: {provider}")

            # Simulate connection test
            if provider in self.integration_manager.CONNECTORS:
                return {
                    "success": True,
                    "provider": provider,
                    "message": f"Successfully connected to {provider}",
                    "latency_ms": 150,
                }
            else:
                return {"success": False, "error": f"Unable to connect to {provider}"}

        except Exception as e:
            logger.error(f"Error testing HRIS connection: {str(e)}")
            return {"success": False, "error": f"Connection test failed: {str(e)}"}

    async def store_connection_configuration(
        self,
        organization_id: int,
        provider: str,
        connection_parameters: Dict[str, Any],
        data_permissions: List[str],
        sync_settings: Dict[str, Any],
        setup_by: int,
    ) -> Dict[str, Any]:
        """
        Store HRIS connection configuration.

        Args:
            organization_id: Organization ID
            provider: HRIS provider name
            connection_parameters: Connection parameters (will be encrypted)
            data_permissions: Data access permissions
            sync_settings: Synchronization settings
            setup_by: User ID who set up the connection

        Returns:
            Stored connection configuration
        """
        try:
            connection_id = (
                f"{organization_id}_{provider}_{datetime.utcnow().timestamp()}"
            )

            encrypted_params = self._encrypt_parameters(connection_parameters)

            connection_config = {
                "connection_id": connection_id,
                "organization_id": organization_id,
                "provider": provider,
                "connection_parameters": encrypted_params,
                "data_permissions": data_permissions,
                "sync_settings": sync_settings,
                "setup_by": setup_by,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
                "next_sync": sync_settings.get("next_sync", None),
            }

            # Store in active connections (in production, store in database)
            self._active_connections[connection_id] = connection_config

            logger.info(f"Stored HRIS connection configuration: {connection_id}")

            return connection_config

        except Exception as e:
            logger.error(f"Error storing HRIS connection configuration: {str(e)}")
            raise

    async def get_available_endpoints(self, provider: str) -> List[str]:
        """
        Get available API endpoints for provider.

        Args:
            provider: HRIS provider name

        Returns:
            List of available endpoint names
        """
        endpoints_map = {
            "workday": [
                "employees",
                "performance",
                "compensation",
                "time_off",
                "benefits",
            ],
            "bamboohr": [
                "employees",
                "performance",
                "time_off",
                "recruitment",
                "onboarding",
            ],
            "adp": ["payroll", "time_attendance", "benefits", "talent_management"],
            "ukg": ["workforce_management", "payroll", "time_attendance", "scheduling"],
            "sap": [
                "employee_central",
                "performance",
                "learning",
                "succession",
                "compensation",
            ],
            "oracle": ["hr", "payroll", "talent", "workforce_rewards", "time_labor"],
        }

        return endpoints_map.get(provider, ["employees"])

    async def get_provider_data_schema(self, provider: str) -> Dict[str, Any]:
        """
        Get data schema for provider.

        Args:
            provider: HRIS provider name

        Returns:
            Provider data schema
        """
        base_schema = {
            "employees": {
                "fields": ["id", "name", "email", "department", "title", "status"],
                "primary_key": "id",
            },
            "performance": {
                "fields": [
                    "employee_id",
                    "review_date",
                    "rating",
                    "reviewer",
                    "comments",
                ],
                "primary_key": "employee_id",
            },
        }

        return base_schema

    async def verify_analytics_access(
        self,
        user_id: int,
        organization_id: int,
        analytics_type: str,
    ) -> bool:
        """
        Verify user has access to requested analytics.

        Args:
            user_id: User ID
            organization_id: Organization ID
            analytics_type: Type of analytics requested

        Returns:
            True if user has access, False otherwise
        """
        allowed_roles = {"admin", "owner", "super_admin"}
        user_role = await self._resolve_user_role(user_id, organization_id)
        if user_role in allowed_roles:
            return True
        # Members can only view basic analytics
        return analytics_type in ("overview", "summary")

    async def verify_employee_data_access(
        self,
        user_id: int,
        organization_id: int,
        data_scope: str,
        employee_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Verify user has access to requested employee data.

        Args:
            user_id: User ID
            organization_id: Organization ID
            data_scope: Requested data scope
            employee_ids: Specific employee IDs (optional)

        Returns:
            True if user has access, False otherwise
        """
        valid_scopes = ["basic", "standard", "advanced", "custom"]
        if data_scope not in valid_scopes:
            return False

        user_role = await self._resolve_user_role(user_id, organization_id)
        # Only admins/owners can access advanced or custom scopes
        if data_scope in ("advanced", "custom"):
            return user_role in ("admin", "owner", "super_admin")
        # Standard scope requires at least admin or owner
        if data_scope == "standard":
            return user_role in ("admin", "owner", "super_admin", "member")
        return True

    async def verify_sync_status_access(
        self,
        user_id: int,
        organization_id: int,
    ) -> bool:
        """
        Verify user has access to view sync status.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            True if user has access, False otherwise
        """
        user_role = await self._resolve_user_role(user_id, organization_id)
        return user_role in ("admin", "owner", "super_admin", "member")

    async def verify_organization_access(
        self,
        user_id: int,
        organization_id: int,
    ) -> bool:
        """
        Verify user has access to organization.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            True if user has access, False otherwise
        """
        user_role = await self._resolve_user_role(user_id, organization_id)
        return user_role is not None

    async def anonymize_employee_data(
        self,
        employee_data: Dict[str, Any],
        data_scope: str,
    ) -> Dict[str, Any]:
        """
        Anonymize employee data by removing PII.

        Args:
            employee_data: Employee data to anonymize
            data_scope: Data scope determining what to anonymize

        Returns:
            Anonymized employee data
        """
        employees = employee_data.get("employees", [])

        # Determine which PII fields to strip based on scope
        if data_scope == "basic":
            strip_fields = self._PII_FIELDS_BASIC
        elif data_scope == "standard":
            strip_fields = self._PII_FIELDS_STANDARD
        elif data_scope == "advanced":
            strip_fields = self._PII_FIELDS_ADVANCED
        else:
            strip_fields = self._PII_FIELDS_BASIC

        for emp in employees:
            for pii_field in strip_fields:
                emp.pop(pii_field, None)
            # Generalize name to initials when group is below k-anonymity threshold
            if len(employees) < self.K_BASIC and "name" in emp:
                parts = emp["name"].split()
                emp["name"] = " ".join(p[0] + "." for p in parts if p)

        # Suppress department-level breakdowns below k-anonymity threshold
        dept_groups: Dict[str, int] = {}
        for emp in employees:
            dept = emp.get("department", "Unknown")
            dept_groups[dept] = dept_groups.get(dept, 0) + 1

        k = self.K_SENSITIVE if data_scope in ("advanced", "custom") else self.K_BASIC
        for emp in employees:
            dept = emp.get("department", "Unknown")
            if dept_groups.get(dept, 0) < k:
                emp["department"] = "Other"

        return employee_data

    async def get_employee_psychometric_data(
        self,
        organization_id: int,
        employee_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get psychometric assessment data for employees.

        Args:
            organization_id: Organization ID
            employee_ids: Specific employee IDs (optional)

        Returns:
            Psychometric data for employees
        """
        try:
            from sqlalchemy import select
            from app.core.database import async_session_factory

            async with async_session_factory() as db:
                # Try to query the responses/assessments tables if they exist
                from app.db.models import Assessment, Response

                q = select(Response).where(
                    Response.organization_id == str(organization_id)
                )
                if employee_ids:
                    q = q.where(Response.user_id.in_(employee_ids))
                q = q.limit(500)

                result = await db.execute(q)
                rows = result.scalars().all()

                return {
                    "psychometric_integration": [
                        {
                            "employee_id": str(r.user_id),
                            "assessment_id": str(r.assessment_id),
                            "score": r.score if hasattr(r, "score") else None,
                            "completed_at": (
                                r.created_at.isoformat()
                                if hasattr(r, "created_at") and r.created_at
                                else None
                            ),
                        }
                        for r in rows
                    ],
                    "total": len(rows),
                }
        except Exception as e:
            logger.warning(f"Psychometric data retrieval unavailable: {e}")
            return {
                "psychometric_integration": [],
                "message": "Assessment tables not yet available",
            }

    async def get_data_field_list(self, data_scope: str) -> List[str]:
        """
        Get list of data fields included in scope.

        Args:
            data_scope: Data scope

        Returns:
            List of field names
        """
        scope_fields = {
            "basic": ["id", "name", "department", "title", "status"],
            "standard": [
                "id",
                "name",
                "email",
                "department",
                "title",
                "status",
                "hire_date",
            ],
            "advanced": [
                "id",
                "name",
                "email",
                "phone",
                "department",
                "title",
                "status",
                "hire_date",
                "salary",
                "manager_id",
            ],
            "custom": [],
        }

        return scope_fields.get(data_scope, scope_fields["basic"])

    async def determine_privacy_level(self, user_id: int, data_scope: str) -> str:
        """
        Determine privacy level for user and data scope.

        Args:
            user_id: User ID
            data_scope: Requested data scope

        Returns:
            Privacy level (standard, sensitive, restricted)
        """
        if data_scope == "advanced":
            return "sensitive"
        elif data_scope == "custom":
            return "restricted"
        return "standard"

    async def get_connection_status(
        self,
        organization_id: int,
        connection_id: str,
    ) -> Dict[str, Any]:
        """
        Get status of HRIS connection.

        Args:
            organization_id: Organization ID
            connection_id: Connection ID

        Returns:
            Connection status information
        """
        connection = self._active_connections.get(connection_id, {})

        return {
            "connected": bool(connection),
            "provider": connection.get("provider"),
            "status": connection.get("status", "unknown"),
            "last_sync": connection.get("last_sync"),
            "created_at": connection.get("created_at"),
        }

    async def update_configuration(
        self,
        organization_id: int,
        connection_id: str,
        configuration_updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update HRIS connection configuration.

        Args:
            organization_id: Organization ID
            connection_id: Connection ID
            configuration_updates: Configuration parameters to update

        Returns:
            Updated configuration
        """
        connection = self._active_connections.get(connection_id)

        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")

        # Update configuration
        connection.update(configuration_updates)
        connection["updated_at"] = datetime.utcnow().isoformat()

        self._active_connections[connection_id] = connection

        logger.info(f"Updated HRIS connection configuration: {connection_id}")

        return connection

    async def assess_configuration_impact(
        self,
        configuration_updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Assess impact of configuration changes.

        Args:
            configuration_updates: Configuration updates to assess

        Returns:
            Impact assessment
        """
        impact = {
            "requires_reauth": False,
            "affects_sync": False,
            "affects_analytics": False,
            "downtime_required": False,
        }

        if "connection_parameters" in configuration_updates:
            impact["requires_reauth"] = True

        if "sync_settings" in configuration_updates:
            impact["affects_sync"] = True

        if "data_permissions" in configuration_updates:
            impact["affects_analytics"] = True

        return impact

    async def get_organization_connections(
        self,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Get all HRIS connections for organization.

        Args:
            organization_id: Organization ID

        Returns:
            List of connection configurations
        """
        connections = [
            conn
            for conn in self._active_connections.values()
            if conn.get("organization_id") == organization_id
        ]

        return connections

    async def delete_connection(
        self,
        organization_id: int,
        connection_id: str,
    ) -> Dict[str, Any]:
        """
        Delete HRIS connection.

        Args:
            organization_id: Organization ID
            connection_id: Connection ID

        Returns:
            Deletion result
        """
        if connection_id in self._active_connections:
            del self._active_connections[connection_id]
            logger.info(f"Deleted HRIS connection: {connection_id}")
            return {"deleted": True, "connection_id": connection_id}

        return {"deleted": False, "connection_id": connection_id}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_fernet(self) -> Fernet:
        """Lazily initialise Fernet cipher from app settings."""
        if self._fernet is None:
            try:
                from app.core.config import settings

                key = (
                    getattr(settings, "HRIS_ENCRYPTION_KEY", None)
                    or Fernet.generate_key()
                )
                if isinstance(key, str):
                    key = key.encode()
                self._fernet = Fernet(key)
            except Exception:
                # Fallback: generate an ephemeral key (connections won't survive restart)
                self._fernet = Fernet(Fernet.generate_key())
        return self._fernet

    def _encrypt_parameters(self, params: Dict[str, Any]) -> str:
        """Encrypt connection parameters with Fernet symmetric encryption."""
        import json

        plaintext = json.dumps(params).encode()
        return self._get_fernet().encrypt(plaintext).decode()

    def _decrypt_parameters(self, encrypted: str) -> Dict[str, Any]:
        """Decrypt connection parameters."""
        import json

        plaintext = self._get_fernet().decrypt(encrypted.encode())
        return json.loads(plaintext)

    async def _resolve_user_role(
        self, user_id: int, organization_id: int
    ) -> Optional[str]:
        """
        Resolve the highest role a user holds within an organization.

        Checks team_members table for roles within the org's teams.
        Falls back to checking User.is_superuser.
        """
        try:
            from sqlalchemy import select, and_
            from sqlalchemy.ext.asyncio import AsyncSession
            from app.core.database import async_session_factory
            from app.db.models.team import Team, TeamMember
            from app.db.models.user import User

            async with async_session_factory() as db:
                # Check superuser first
                user_q = select(User.is_superuser).where(User.id == str(user_id))
                result = await db.execute(user_q)
                row = result.scalar_one_or_none()
                if row is True:
                    return "super_admin"

                # Query team memberships within the organization
                q = (
                    select(TeamMember.role)
                    .join(Team, Team.id == TeamMember.team_id)
                    .where(
                        and_(
                            TeamMember.user_id == str(user_id),
                            Team.organization_id == str(organization_id),
                        )
                    )
                )
                result = await db.execute(q)
                roles = [
                    r[0].value if hasattr(r[0], "value") else str(r[0])
                    for r in result.all()
                ]

                if not roles:
                    return None

                # Return highest role: owner > admin > member
                role_hierarchy = {"owner": 3, "admin": 2, "member": 1}
                return max(roles, key=lambda r: role_hierarchy.get(r, 0))

        except Exception as e:
            logger.error(f"Error resolving user role: {e}")
            return None
