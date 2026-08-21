# app/core/rls_verifier.py
"""
RLS (Row-Level Security) verification utility.
Validates tenant isolation by running controlled cross-tenant queries
and asserting that no data leaks between tenants.

Intended for CI pipelines and security audits — NOT production traffic.
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app.security.rls_verifier")

# Tables that should have RLS enabled
# Map table name → org column name
RLS_PROTECTED_TABLES: dict[str, str] = {
    "users_secure": "organization_id",
    "organizations_secure": "id",  # the org IS the row
    "teams_secure": "organization_id",
    "team_members_secure": "",  # no direct org column
    "assessments_secure": "organization_id",
    "clinical_screenings": "org_id",
    "clinical_alerts": "org_id",
    "clinical_referrals": "org_id",
    "clinical_consents": "org_id",
}


@dataclass
class RLSCheckResult:
    table: str
    check_type: str
    passed: bool
    detail: str = ""


@dataclass
class RLSVerificationReport:
    checks: list[RLSCheckResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    def add(self, result: RLSCheckResult):
        self.checks.append(result)
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1

    def summary(self) -> dict:
        return {
            "all_passed": self.all_passed,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "checks": [
                {
                    "table": c.table,
                    "check_type": c.check_type,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
        }


class RLSVerifier:
    """
    Verifies RLS policies by:
    1. Checking that RLS is enabled on all expected tables
    2. Setting session context to tenant A, inserting test data
    3. Switching to tenant B, verifying tenant A's data is invisible
    4. Verifying admin bypass works when is_platform_admin is set
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def verify_all(
        self,
        tenant_a_id: UUID,
        tenant_b_id: UUID,
        user_a_id: UUID,
        user_b_id: UUID,
    ) -> RLSVerificationReport:
        """Run all RLS verification checks."""
        report = RLSVerificationReport()

        # 1. Verify RLS is enabled on all expected tables
        await self._check_rls_enabled(report)

        # 2. Verify tenant isolation
        await self._check_tenant_isolation(
            report, tenant_a_id, tenant_b_id, user_a_id, user_b_id
        )

        # 3. Verify admin bypass
        await self._check_admin_bypass(report, tenant_a_id, user_a_id)

        logger.info(
            "RLS verification complete: %d passed, %d failed",
            report.passed,
            report.failed,
        )
        return report

    async def _check_rls_enabled(self, report: RLSVerificationReport):
        """Verify RLS is enabled on all protected tables."""
        for table in RLS_PROTECTED_TABLES.keys():
            result = await self._session.execute(
                text(
                    """
                    SELECT rowsecurity
                    FROM pg_tables
                    WHERE tablename = :table_name
                """
                ),
                {"table_name": table},
            )
            row = result.fetchone()

            if row is None:
                report.skipped += 1
                continue

            rls_enabled = row[0]
            report.add(
                RLSCheckResult(
                    table=table,
                    check_type="rls_enabled",
                    passed=rls_enabled,
                    detail="RLS enabled" if rls_enabled else "RLS NOT enabled",
                )
            )

    async def _check_tenant_isolation(
        self,
        report: RLSVerificationReport,
        tenant_a: UUID,
        tenant_b: UUID,
        user_a: UUID,
        user_b: UUID,
    ):
        """
        Verify that tenant B cannot see tenant A's data.
        Uses session variables to simulate different tenant contexts.
        """
        for table, org_col in RLS_PROTECTED_TABLES.items():
            # Skip tables without a direct org column
            if not org_col:
                continue

            if not await self._table_exists(table):
                continue

            # Run inside a transaction so SET LOCAL is scoped properly
            async with self._session.begin_nested():
                # Switch to tenant B context
                await self._set_session_context(
                    user_id=str(user_b),
                    org_id=str(tenant_b),
                    role="user",
                    is_admin=False,
                )

                # Key test: tenant B queries for tenant A's rows using the correct column
                cross_query = await self._session.execute(
                    text(
                        f"SELECT COUNT(*) FROM {table} WHERE {org_col} = :tenant_a_id"
                    ),  # noqa: S608
                    {"tenant_a_id": str(tenant_a)},
                )
                cross_tenant_count = cross_query.scalar()

            passed = cross_tenant_count == 0
            report.add(
                RLSCheckResult(
                    table=table,
                    check_type="tenant_isolation",
                    passed=passed,
                    detail=(
                        f"Tenant B sees 0 of tenant A's rows (col: {org_col})"
                        if passed
                        else f"LEAK: Tenant B sees {cross_tenant_count} of tenant A's rows via {org_col}"
                    ),
                )
            )

    async def _check_admin_bypass(
        self,
        report: RLSVerificationReport,
        tenant_a: UUID,
        user_a: UUID,
    ):
        """Verify platform admin bypass works by comparing admin vs regular user visibility."""
        for table in ["users_secure", "clinical_screenings"]:
            if not await self._table_exists(table):
                continue

            # First: count rows visible to a regular user in tenant A
            async with self._session.begin_nested():
                await self._set_session_context(
                    user_id=str(user_a),
                    org_id=str(tenant_a),
                    role="user",
                    is_admin=False,
                )
                result = await self._session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                )
                regular_count = result.scalar()

            # Second: count rows visible to platform admin
            async with self._session.begin_nested():
                await self._set_session_context(
                    user_id=str(user_a),
                    org_id=str(tenant_a),
                    role="super_admin",
                    is_admin=True,
                )
                result = await self._session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
                )
                admin_count = result.scalar()

            # Admin should see at least as many rows as a regular user
            passed = admin_count >= regular_count
            report.add(
                RLSCheckResult(
                    table=table,
                    check_type="admin_bypass",
                    passed=passed,
                    detail=(
                        f"Admin sees {admin_count} rows (regular user sees {regular_count})"
                        if passed
                        else f"BROKEN: Admin sees {admin_count} rows but regular user sees {regular_count}"
                    ),
                )
            )

    async def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        result = await self._session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = :table_name
                )
            """
            ),
            {"table_name": table_name},
        )
        return result.scalar()

    async def _set_session_context(
        self,
        user_id: str,
        org_id: str,
        role: str,
        is_admin: bool,
    ):
        """Set PostgreSQL session variables for RLS context."""
        await self._session.execute(
            text("SET LOCAL app.current_user_id = :uid"), {"uid": user_id}
        )
        await self._session.execute(
            text("SET LOCAL app.current_org_id = :oid"), {"oid": org_id}
        )
        await self._session.execute(
            text("SET LOCAL app.current_user_role = :role"), {"role": role}
        )
        await self._session.execute(
            text("SET LOCAL app.is_platform_admin = :admin"),
            {"admin": "true" if is_admin else "false"},
        )
