# app/crud/crud_code_quality.py

"""
CODE QUALITY CRUD OPERATIONS
Database operations for code quality monitoring

Author: Product Operations Team
Version: 1.0
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.code_quality import (
    CodeQualityIssue,
    CodeQualityMetric,
    PullRequestQuality,
)
from app.schemas.code_quality import (
    CodeQualityIssueCreate,
    CodeQualityMetricCreate,
    PullRequestQualityCreate,
)


class CRUDCodeQualityMetric:
    """CRUD operations for code quality metrics"""

    async def get(self, db: AsyncSession, id: str) -> Optional[CodeQualityMetric]:
        """Retrieve resource(s).

        Args:
            db: Database session
            **kwargs: Filter criteria

        Returns:
            Resource object or list of resources

        Raises:
            NotFoundError: If resource doesn't exist
        """
        """Get a single metric by ID"""
        result = await db.execute(
            select(CodeQualityMetric).where(CodeQualityMetric.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        module_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[CodeQualityMetric], int]:
        """Get multiple metrics with filtering."""
        query = select(CodeQualityMetric)

        # Apply filters
        filters = []
        if module_name is not None:
            filters = [CodeQualityMetric.module_name == module_name]
        if start_date is not None:
            filters.append(CodeQualityMetric.scan_date >= start_date)
        if end_date is not None:
            filters.append(CodeQualityMetric.scan_date <= end_date)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = (
            query.order_by(desc(CodeQualityMetric.scan_date)).offset(skip).limit(limit)
        )
        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def get_latest(
        self, db: AsyncSession, module_name: Optional[str] = None
    ) -> Optional[CodeQualityMetric]:
        """Retrieve resource(s).

        Args:
            db: Database session
            **kwargs: Filter criteria

        Returns:
            Resource object or list of resources

        Raises:
            NotFoundError: If resource doesn't exist
        """
        """Get the most recent metric"""
        query = (
            select(CodeQualityMetric)
            .order_by(desc(CodeQualityMetric.scan_date))
            .limit(1)
        )

        if module_name is not None:
            query = query.where(CodeQualityMetric.module_name == module_name)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_trend(
        self,
        db: AsyncSession,
        *,
        days: int = 30,
        module_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get quality trend over time."""
        start_date = datetime.utcnow() - timedelta(days=days)

        query = select(CodeQualityMetric).where(
            CodeQualityMetric.scan_date >= start_date
        )

        if module_name is not None:
            query = query.where(CodeQualityMetric.module_name == module_name)

        query = query.order_by(CodeQualityMetric.scan_date)

        result = await db.execute(query)
        metrics = result.scalars().all()

        return [
            {
                "date": m.scan_date,
                "quality_score": m.quality_score,
                "complexity_trend": m.complexity_trend or "stable",
                "coverage_trend": m.coverage_trend,
                "debt_trend": m.debt_trend or "stable",
                "critical_issues": m.security_hotspots_count + m.bugs_count,
                "major_issues": m.code_violations_count,
            }
            for m in metrics
        ]

    async def create(
        self, db: AsyncSession, *, obj_in: CodeQualityMetricCreate
    ) -> CodeQualityMetric:
        """Create a new resource.

        Args:
            db: Database session
            **kwargs: Resource attributes

        Returns:
            Created resource object

        Raises:
            ValidationError: If input data is invalid
        """
        """Create a new quality metric"""
        db_obj = CodeQualityMetric(**obj_in.model_dump())

        # Calculate quality score and grade
        db_obj.quality_score = self._calculate_quality_score(db_obj)
        db_obj.quality_grade = self._calculate_quality_grade(db_obj.quality_score)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_with_issues(
        self,
        db: AsyncSession,
        *,
        metric_in: CodeQualityMetricCreate,
        issues: list[dict[str, Any]],
    ) -> CodeQualityMetric:
        """Create a quality metric with associated issues."""
        db_obj = CodeQualityMetric(**metric_in.model_dump())

        # Calculate quality score and grade
        db_obj.quality_score = self._calculate_quality_score(db_obj)
        db_obj.quality_grade = self._calculate_quality_grade(db_obj.quality_score)

        db.add(db_obj)
        await db.flush()

        # Create issues
        for issue_data in issues:
            issue = CodeQualityIssue(**issue_data, metric_id=db_obj.id)
            db.add(issue)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_trends(
        self,
        db: AsyncSession,
        *,
        current_metric: CodeQualityMetric,
    ) -> CodeQualityMetric:
        """Update trend indicators by comparing with previous metric."""
        previous = await self.get_latest(db, module_name=current_metric.module_name)

        if previous and previous.id != current_metric.id:
            # Compare with previous scan
            current_metric.complexity_trend = self._calculate_trend(
                current_metric.cyclomatic_complexity,
                previous.cyclomatic_complexity,
            )
            current_metric.debt_trend = self._calculate_trend(
                previous.technical_debt_ratio,
                current_metric.technical_debt_ratio,
            )  # lower is better

            if (
                current_metric.test_coverage_percentage
                and previous.test_coverage_percentage
            ):
                current_metric.coverage_trend = self._calculate_trend(
                    current_metric.test_coverage_percentage,
                    previous.test_coverage_percentage,
                )

        await db.commit()
        await db.refresh(current_metric)
        return current_metric

    def _calculate_quality_score(self, metric: CodeQualityMetric) -> float:
        """Calculate overall quality score (0-100)"""
        score = 100.0

        # Deduct for complexity (>10 is bad)
        if metric.cyclomatic_complexity > 10:
            score -= min(20, (metric.cyclomatic_complexity - 10) * 2)

        # Deduct for duplication
        score -= min(25, metric.duplication_percentage * 0.5)

        # Deduct for low coverage
        if metric.test_coverage_percentage and metric.test_coverage_percentage < 80:
            score -= min(20, (80 - metric.test_coverage_percentage) * 0.5)

        # Deduct for technical debt (>5% is bad)
        if metric.technical_debt_ratio > 5:
            score -= min(20, (metric.technical_debt_ratio - 5) * 2)

        # Deduct for security hotspots and bugs
        score -= min(15, metric.security_hotspots_count * 3)
        score -= min(10, metric.bugs_count * 2)

        # Add bonus for good maintainability
        if metric.maintainability_index > 80:
            score += min(10, (metric.maintainability_index - 80) * 0.5)

        return max(0, min(100, score))

    def _calculate_quality_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 65:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _calculate_trend(
        self, current: float, previous: float, threshold: float = 0.05
    ) -> str:
        """Calculate trend direction"""
        if previous == 0:
            return "stable"

        change = (current - previous) / abs(previous)

        if change > threshold:
            return "improving"
        elif change < -threshold:
            return "declining"
        else:
            return "stable"


class CRUDCodeQualityIssue:
    """CRUD operations for code quality issues"""

    async def get(self, db: AsyncSession, id: str) -> Optional[CodeQualityIssue]:
        """Retrieve resource(s).

        Args:
            db: Database session
            **kwargs: Filter criteria

        Returns:
            Resource object or list of resources

        Raises:
            NotFoundError: If resource doesn't exist
        """
        """Get a single issue by ID"""
        result = await db.execute(
            select(CodeQualityIssue).where(CodeQualityIssue.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        issue_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: str = "open",
        metric_id: Optional[str] = None,
    ) -> tuple[list[CodeQualityIssue], int]:
        """Get multiple issues with filtering."""
        query = select(CodeQualityIssue)

        # Apply filters
        filters = []
        if issue_type is not None:
            filters.append(CodeQualityIssue.issue_type == issue_type)
        if severity is not None:
            filters.append(CodeQualityIssue.severity == severity)
        if status is not None:
            filters.append(CodeQualityIssue.status == status)
        if metric_id is not None:
            filters.append(CodeQualityIssue.metric_id == metric_id)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results - order by severity (critical first) then date
        severity_order = {
            "critical": 0,
            "major": 1,
            "minor": 2,
            "info": 3,
        }
        # Note: This is a simplified ordering. In production, use CASE expression in SQL
        query = (
            query.order_by(desc(CodeQualityIssue.last_detected))
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def get_hotspots(
        self,
        db: AsyncSession,
        *,
        limit: int = 20,
    ) -> list[CodeQualityIssue]:
        """Get the most critical issues."""
        result = await db.execute(
            select(CodeQualityIssue)
            .where(CodeQualityIssue.status == "open")
            .where(CodeQualityIssue.severity.in_(["critical", "major"]))
            .order_by(desc(CodeQualityIssue.last_detected))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, *, obj_in: CodeQualityIssueCreate
    ) -> CodeQualityIssue:
        """Create a new resource.

        Args:
            db: Database session
            **kwargs: Resource attributes

        Returns:
            Created resource object

        Raises:
            ValidationError: If input data is invalid
        """
        """Create a new quality issue"""
        db_obj = CodeQualityIssue(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDPullRequestQuality:
    """CRUD operations for pull request quality"""

    async def get(self, db: AsyncSession, id: str) -> Optional[PullRequestQuality]:
        """Retrieve resource(s).

        Args:
            db: Database session
            **kwargs: Filter criteria

        Returns:
            Resource object or list of resources

        Raises:
            NotFoundError: If resource doesn't exist
        """
        """Get a single PR quality record by ID"""
        result = await db.execute(
            select(PullRequestQuality).where(PullRequestQuality.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_pr_number(
        self, db: AsyncSession, *, pr_number: int
    ) -> Optional[PullRequestQuality]:
        """Retrieve resource(s).

        Args:
            db: Database session
            **kwargs: Filter criteria

        Returns:
            Resource object or list of resources

        Raises:
            NotFoundError: If resource doesn't exist
        """
        """Get PR quality by PR number"""
        result = await db.execute(
            select(PullRequestQuality).where(PullRequestQuality.pr_number == pr_number)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        risk_level: Optional[str] = None,
        author_id: Optional[str] = None,
        min_score: Optional[float] = None,
        is_merged: Optional[bool] = None,
    ) -> tuple[list[PullRequestQuality], int]:
        """Get multiple PR quality records with filtering."""
        query = select(PullRequestQuality)

        # Apply filters
        filters = []
        if risk_level is not None:
            filters.append(PullRequestQuality.risk_level == risk_level)
        if author_id is not None:
            filters.append(PullRequestQuality.author_id == author_id)
        if min_score is not None:
            filters.append(PullRequestQuality.overall_score >= min_score)
        if is_merged is not None:
            filters.append(PullRequestQuality.is_merged == is_merged)

        if filters:
            query = query.where(and_(*filters))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = (
            query.order_by(desc(PullRequestQuality.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def get_summary(
        self,
        db: AsyncSession,
        *,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get PR quality summary for recent period."""
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(PullRequestQuality).where(
                PullRequestQuality.created_at >= start_date
            )
        )
        prs = list(result.scalars().all())

        if not prs:
            return {
                "avg_quality_score": 0.0,
                "avg_review_time_hours": 0.0,
                "total_prs_analyzed": 0,
                "high_risk_prs": 0,
                "medium_risk_prs": 0,
                "low_risk_prs": 0,
                "avg_files_changed": 0.0,
                "avg_lines_added": 0.0,
                "total_tests_added": 0,
                "merge_rate": 0.0,
            }

        merged_prs = [pr for pr in prs if pr.is_merged]

        return {
            "avg_quality_score": sum(pr.overall_score for pr in prs) / len(prs),
            "avg_review_time_hours": (
                sum(pr.review_time_hours or 0 for pr in prs) / len(prs)
            ),
            "total_prs_analyzed": len(prs),
            "high_risk_prs": len([pr for pr in prs if pr.risk_level == "high"]),
            "medium_risk_prs": len([pr for pr in prs if pr.risk_level == "medium"]),
            "low_risk_prs": len([pr for pr in prs if pr.risk_level == "low"]),
            "avg_files_changed": sum(pr.files_changed for pr in prs) / len(prs),
            "avg_lines_added": sum(pr.lines_added for pr in prs) / len(prs),
            "total_tests_added": sum(pr.tests_added for pr in prs),
            "merge_rate": len(merged_prs) / len(prs) if prs else 0.0,
        }

    async def create(
        self, db: AsyncSession, *, obj_in: PullRequestQualityCreate
    ) -> PullRequestQuality:
        """Create a new resource.

        Args:
            db: Database session
            **kwargs: Resource attributes

        Returns:
            Created resource object

        Raises:
            ValidationError: If input data is invalid
        """
        """Create a new PR quality record"""
        db_obj = PullRequestQuality(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Create instances
code_quality_metric = CRUDCodeQualityMetric()
code_quality_issue = CRUDCodeQualityIssue()
pull_request_quality = CRUDPullRequestQuality()
