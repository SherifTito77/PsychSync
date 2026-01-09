# app/services/optimized_queries.py
"""
Optimized Database Queries for PsychSync
Demonstrates application of query optimization patterns
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache_strategy import CacheStrategy, intelligent_cache
from app.core.query_monitor import query_monitor
from app.core.structured_logging import EventType, get_logger
from app.db.models.team import Team
from app.db.models.user import User

logger = get_logger(__name__)


class OptimizedQueryService:
    """
    Service demonstrating optimized database queries with monitoring
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    async def get_users_with_teams_optimized(
        self,
        db: AsyncSession,
        organization_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """
        Optimized query to get users with their teams
        Uses eager loading to prevent N+1 queries
        """
        query_str = """
        SELECT u.*, t.id as team_id, t.name as team_name
        FROM users u
        LEFT JOIN team_members tm ON u.id = tm.user_id
        LEFT JOIN teams t ON tm.team_id = t.id
        WHERE u.is_active = true
        """

        params = {"limit": limit, "offset": offset}
        if organization_id:
            query_str += " AND u.organization_id = :org_id"
            params["org_id"] = str(organization_id)

        query_str += " ORDER BY u.full_name LIMIT :limit OFFSET :offset"

        async with query_monitor.monitor_query(
            query_str, operation_name="get_users_with_teams_optimized", db=db, params=params
        ):
            # Use optimized query with eager loading
            query = (
                select(User)
                .options(
                    selectinload(User.teams).selectinload(Team.members),
                    selectinload(User.organization),
                )
                .where(User.is_active == True)
            )

            if organization_id:
                query = query.where(User.organization_id == organization_id)

            query = query.order_by(User.full_name).limit(limit).offset(offset)

            result = await db.execute(query)
            users = result.scalars().all()

            # Cache the results
            cache_key = f"users_with_teams_{organization_id}_{limit}_{offset}"
            await intelligent_cache.set(
                CacheStrategy.USER_PROFILE,
                cache_key,
                users,
                ttl=300,  # 5 minutes
            )

            self.logger.info(
                EventType.DATABASE_OPERATION,
                f"Retrieved {len(users)} users with teams (optimized)",
                operation_name="get_users_with_teams_optimized",
                user_count=len(users),
                organization_id=str(organization_id) if organization_id else None,
            )

            return users

    async def get_team_analytics_optimized(
        self, db: AsyncSession, team_id: UUID, days: int = 30
    ) -> dict[str, Any]:
        """
        Optimized query for team analytics with minimal database calls
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query_str = """
        WITH member_activity AS (
            SELECT
                COUNT(DISTINCT ar.user_id) as active_members,
                COUNT(ar.id) as total_responses,
                AVG(ar.completion_time_seconds) as avg_completion_time
            FROM assessment_responses ar
            JOIN users u ON ar.user_id = u.id
            JOIN team_members tm ON u.id = tm.user_id
            WHERE tm.team_id = :team_id
            AND ar.created_at >= :cutoff_date
        ),
        team_growth AS (
            SELECT
                COUNT(DISTINCT u.id) as total_members,
                COUNT(DISTINCT CASE WHEN tm.created_at >= :cutoff_date THEN u.id END) as new_members
            FROM team_members tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.team_id = :team_id
        )
        SELECT
            ma.active_members,
            ma.total_responses,
            ma.avg_completion_time,
            tg.total_members,
            tg.new_members
        FROM member_activity ma, team_growth tg
        """

        params = {"team_id": str(team_id), "cutoff_date": cutoff_date}

        async with query_monitor.monitor_query(
            query_str, operation_name="get_team_analytics_optimized", db=db, params=params
        ):
            # Execute optimized analytics query
            result = await db.execute(text(query_str), params)
            analytics_data = result.fetchone()

            if not analytics_data:
                return {
                    "team_id": str(team_id),
                    "period_days": days,
                    "active_members": 0,
                    "total_responses": 0,
                    "avg_completion_time": 0,
                    "total_members": 0,
                    "new_members": 0,
                }

            analytics = {
                "team_id": str(team_id),
                "period_days": days,
                "active_members": analytics_data.active_members or 0,
                "total_responses": analytics_data.total_responses or 0,
                "avg_completion_time": float(analytics_data.avg_completion_time or 0),
                "total_members": analytics_data.total_members or 0,
                "new_members": analytics_data.new_members or 0,
            }

            # Cache analytics for shorter period due to time sensitivity
            cache_key = f"team_analytics_{team_id}_{days}"
            await intelligent_cache.set(
                CacheStrategy.TEAM_DATA,
                cache_key,
                analytics,
                ttl=180,  # 3 minutes
            )

            return analytics

    async def get_assessment_completion_rates_optimized(
        self, db: AsyncSession, organization_id: UUID | None = None, days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Optimized query for assessment completion rates using window functions
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query_str = """
        SELECT
            a.id,
            a.title,
            a.created_at,
            COUNT(DISTINCT ar.user_id) as participants,
            COUNT(ar.id) as total_responses,
            COUNT(DISTINCT CASE WHEN ar.status = 'completed' THEN ar.user_id END) as completed_users,
            AVG(
                CASE
                    WHEN ar.status = 'completed' THEN
                        EXTRACT(EPOCH FROM (ar.completed_at - ar.started_at)) / 60
                    ELSE NULL
                END
            ) as avg_completion_minutes
        FROM assessments a
        LEFT JOIN assessment_responses ar ON a.id = ar.assessment_id
            AND ar.created_at >= :cutoff_date
        """

        params = {"cutoff_date": cutoff_date}
        if organization_id:
            query_str += " WHERE a.organization_id = :org_id"
            params["org_id"] = str(organization_id)

        query_str += """
        GROUP BY a.id, a.title, a.created_at
        HAVING COUNT(ar.user_id) > 0
        ORDER BY participants DESC
        """

        async with query_monitor.monitor_query(
            query_str,
            operation_name="get_assessment_completion_rates_optimized",
            db=db,
            params=params,
        ):
            result = await db.execute(text(query_str), params)
            rows = result.fetchall()

            completion_data = []
            for row in rows:
                completion_rate = (
                    (row.completed_users / row.participants * 100) if row.participants > 0 else 0
                )

                completion_data.append(
                    {
                        "assessment_id": str(row.id),
                        "title": row.title,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "participants": row.participants,
                        "total_responses": row.total_responses,
                        "completed_users": row.completed_users,
                        "completion_rate": round(completion_rate, 2),
                        "avg_completion_minutes": round(float(row.avg_completion_minutes or 0), 2),
                    }
                )

            # Cache completion rates
            cache_key = f"assessment_completion_rates_{organization_id}_{days}"
            await intelligent_cache.set(
                CacheStrategy.ASSESSMENT_DATA,
                cache_key,
                completion_data,
                ttl=600,  # 10 minutes
            )

            return completion_data

    async def search_users_optimized(
        self,
        db: AsyncSession,
        search_term: str,
        organization_id: UUID | None = None,
        limit: int = 20,
        include_teams: bool = True,
    ) -> list[User]:
        """
        Optimized user search using full-text search and efficient pagination
        """
        # Add wildcards for partial matching
        search_pattern = f"%{search_term.lower()}%"

        query_str = """
        SELECT DISTINCT u.* FROM users u
        WHERE (
            LOWER(u.full_name) LIKE :search_pattern OR
            LOWER(u.email) LIKE :search_pattern
        )
        AND u.is_active = true
        """

        params = {"search_pattern": search_pattern, "limit": limit}
        if organization_id:
            query_str += " AND u.organization_id = :org_id"
            params["org_id"] = str(organization_id)

        query_str += " ORDER BY u.full_name LIMIT :limit"

        async with query_monitor.monitor_query(
            query_str, operation_name="search_users_optimized", db=db, params=params
        ):
            # Build optimized query
            query = (
                select(User)
                .options(
                    selectinload(User.organization),
                    selectinload(User.teams) if include_teams else None,
                )
                .where(
                    and_(
                        User.is_active == True,
                        or_(User.full_name.ilike(search_pattern), User.email.ilike(search_pattern)),
                    )
                )
            )

            if organization_id:
                query = query.where(User.organization_id == organization_id)

            query = query.order_by(User.full_name).limit(limit)

            result = await db.execute(query)
            users = result.scalars().all()

            self.logger.info(
                EventType.DATABASE_OPERATION,
                f"User search returned {len(users)} results",
                operation_name="search_users_optimized",
                search_term=search_term,
                result_count=len(users),
                organization_id=str(organization_id) if organization_id else None,
            )

            return users

    async def get_organization_metrics_optimized(
        self, db: AsyncSession, organization_id: UUID, days: int = 30
    ) -> dict[str, Any]:
        """
        Comprehensive organization metrics with optimized queries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query_str = """
        WITH org_metrics AS (
            SELECT
                (SELECT COUNT(*) FROM users WHERE organization_id = :org_id AND is_active = true) as total_users,
                (SELECT COUNT(DISTINCT tm.user_id)
                 FROM team_members tm
                 JOIN users u ON tm.user_id = u.id
                 WHERE u.organization_id = :org_id) as active_team_members,
                (SELECT COUNT(*) FROM teams WHERE organization_id = :org_id) as total_teams,
                (SELECT COUNT(*) FROM assessments WHERE organization_id = :org_id) as total_assessments,
                (SELECT COUNT(ar.id)
                 FROM assessment_responses ar
                 JOIN assessments a ON ar.assessment_id = a.id
                 WHERE a.organization_id = :org_id
                 AND ar.created_at >= :cutoff_date) as recent_responses
        )
        SELECT * FROM org_metrics
        """

        params = {"org_id": str(organization_id), "cutoff_date": cutoff_date}

        async with query_monitor.monitor_query(
            query_str, operation_name="get_organization_metrics_optimized", db=db, params=params
        ):
            result = await db.execute(text(query_str), params)
            metrics_data = result.fetchone()

            metrics = {
                "organization_id": str(organization_id),
                "period_days": days,
                "total_users": metrics_data.total_users if metrics_data else 0,
                "active_team_members": metrics_data.active_team_members if metrics_data else 0,
                "total_teams": metrics_data.total_teams if metrics_data else 0,
                "total_assessments": metrics_data.total_assessments if metrics_data else 0,
                "recent_responses": metrics_data.recent_responses if metrics_data else 0,
            }

            # Calculate derived metrics
            if metrics["total_users"] > 0:
                metrics["team_participation_rate"] = (
                    metrics["active_team_members"] / metrics["total_users"]
                ) * 100
            else:
                metrics["team_participation_rate"] = 0

            if metrics["total_assessments"] > 0:
                metrics["response_rate"] = (
                    metrics["recent_responses"] / metrics["total_assessments"]
                ) * 100
            else:
                metrics["response_rate"] = 0

            # Cache organization metrics
            cache_key = f"org_metrics_{organization_id}_{days}"
            await intelligent_cache.set(
                CacheStrategy.ORGANIZATION_DATA,
                cache_key,
                metrics,
                ttl=300,  # 5 minutes
            )

            return metrics

    async def get_popular_assessments_optimized(
        self, db: AsyncSession, organization_id: UUID | None = None, days: int = 30, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get most popular assessments based on completion rates and participation
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query_str = """
        SELECT
            a.id,
            a.title,
            a.created_at,
            COUNT(DISTINCT ar.user_id) as participants,
            COUNT(ar.id) as total_responses,
            COUNT(DISTINCT CASE WHEN ar.status = 'completed' THEN ar.user_id END) as completed_users,
            (COUNT(DISTINCT CASE WHEN ar.status = 'completed' THEN ar.user_id END) * 100.0 /
             NULLIF(COUNT(DISTINCT ar.user_id), 0)) as completion_rate
        FROM assessments a
        LEFT JOIN assessment_responses ar ON a.id = ar.assessment_id
            AND ar.created_at >= :cutoff_date
        """

        params = {"cutoff_date": cutoff_date, "limit": limit}
        if organization_id:
            query_str += " WHERE a.organization_id = :org_id"
            params["org_id"] = str(organization_id)

        query_str += """
        GROUP BY a.id, a.title, a.created_at
        HAVING COUNT(DISTINCT ar.user_id) >= 3
        ORDER BY (participants * completion_rate) DESC
        LIMIT :limit
        """

        async with query_monitor.monitor_query(
            query_str, operation_name="get_popular_assessments_optimized", db=db, params=params
        ):
            result = await db.execute(text(query_str), params)
            rows = result.fetchall()

            popular_assessments = []
            for row in rows:
                popular_assessments.append(
                    {
                        "assessment_id": str(row.id),
                        "title": row.title,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "participants": row.participants,
                        "total_responses": row.total_responses,
                        "completed_users": row.completed_users,
                        "completion_rate": round(float(row.completion_rate or 0), 2),
                        "popularity_score": row.participants * (row.completion_rate or 0),
                    }
                )

            # Cache popular assessments
            cache_key = f"popular_assessments_{organization_id}_{days}_{limit}"
            await intelligent_cache.set(
                CacheStrategy.ASSESSMENT_DATA,
                cache_key,
                popular_assessments,
                ttl=600,  # 10 minutes
            )

            return popular_assessments


# TODO(human): Implement query optimization recommendations
# This should analyze query patterns and suggest specific optimizations
# for common operations, with the ability to apply them automatically


class QueryOptimizationRecommender:
    """
    Recommends specific optimizations for common query patterns
    """

    def __init__(self):
        self.logger = get_logger(__name__)

    def analyze_common_patterns(self, query_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze common query patterns and provide optimization recommendations"""
        recommendations = []

        # Group similar queries
        pattern_groups = self._group_similar_queries(query_history)

        for pattern, queries in pattern_groups.items():
            if len(queries) >= 5:  # Pattern that appears frequently
                avg_time = sum(q["execution_time_ms"] for q in queries) / len(queries)
                max_time = max(q["execution_time_ms"] for q in queries)

                if avg_time > 200:  # Slow pattern
                    recommendation = {
                        "pattern": pattern,
                        "frequency": len(queries),
                        "avg_execution_time": avg_time,
                        "max_execution_time": max_time,
                        "optimizations": self._recommend_optimizations_for_pattern(pattern),
                        "impact_score": len(queries) * avg_time,
                    }
                    recommendations.append(recommendation)

        # Sort by impact score
        recommendations.sort(key=lambda x: x["impact_score"], reverse=True)

        return recommendations[:10]  # Top 10 recommendations

    def _group_similar_queries(
        self, queries: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group similar queries for analysis"""
        import re

        groups = {}
        for query in queries:
            # Create a normalized pattern
            pattern = query["query"].lower()
            pattern = re.sub(r"\d+", "N", pattern)  # Replace numbers
            pattern = re.sub(r":\w+", ":param", pattern)  # Replace parameters
            pattern = re.sub(r"'[^']*'", "'value'", pattern)  # Replace string literals

            if pattern not in groups:
                groups[pattern] = []
            groups[pattern].append(query)

        return groups

    def _recommend_optimizations_for_pattern(self, pattern: str) -> list[str]:
        """Recommend specific optimizations for a query pattern"""
        optimizations = []

        if "users" in pattern and "join" in pattern:
            optimizations.append("Add composite index on (organization_id, is_active, created_at)")
            optimizations.append("Use eager loading with selectinload for teams")
            optimizations.append("Consider filtering users before join operations")

        if "count(" in pattern and "group by" in pattern:
            optimizations.append("Create materialized view for expensive aggregates")
            optimizations.append("Add indexes on GROUP BY columns")
            optimizations.append("Cache count results for frequent queries")

        if "order by" in pattern and "created_at" in pattern:
            optimizations.append("Create index on created_at DESC for sorting")
            optimizations.append("Consider using index with ORDER BY clause")

        if "assessment_responses" in pattern:
            optimizations.append("Add index on (assessment_id, user_id, status)")
            optimizations.append("Consider partitioning by date for large tables")
            optimizations.append("Implement result caching for analytics queries")

        if "like" in pattern or "ilike" in pattern:
            optimizations.append("Consider full-text search for pattern matching")
            optimizations.add("Add trigram indexes for fuzzy matching")
            optimizations.append("Limit search results with early filtering")

        return list(set(optimizations))  # Remove duplicates


# Global optimized query service
optimized_query_service = OptimizedQueryService()
query_recommender = QueryOptimizationRecommender()
