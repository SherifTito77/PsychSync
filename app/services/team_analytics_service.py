"""
Team Analytics Service
Provides aggregate email analytics for teams
"""

import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.organization import Organization
from app.db.models.team import Team
from app.db.models.user import User


class TeamAnalyticsService:
    """Service for analyzing team email patterns"""

    async def get_team_analytics(
        self, db: AsyncSession, team_id: int, days: int = 30, privacy_first: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a team

        Args:
            db: Database session
            team_id: Team ID
            days: Number of days to analyze
            privacy_first: If True, enforces strict k-anonymity (min 5 members) and hides individual identities.

        Returns:
            Team analytics data
        """
        # Get team members
        team_members = await self._get_team_members(db, team_id)

        if not team_members:
            return self._empty_team_analytics(team_id)

        # Enforce k-anonymity (minimum 5 members)
        if len(team_members) < 5:
            raise ValueError(
                f"Privacy Compliance Exception: Team size must be at least 5 to retrieve team-level analytics (k-anonymity constraint). Current size: {len(team_members)}."
            )

        # Collect individual analytics (mock data for now)
        member_analytics = []
        for idx, member in enumerate(team_members):
            analytics = await self._get_member_analytics(member["id"], days)
            if privacy_first:
                # Mask user details
                member_analytics.append(
                    {
                        "member_id": f"member_{idx + 1}",
                        "member_name": f"Team Member {chr(65 + idx)}",  # Team Member A, B, C...
                        "member_email": "redacted@psychsync.local",
                        "analytics": analytics,
                    }
                )
            else:
                member_analytics.append(
                    {
                        "member_id": member["id"],
                        "member_name": member["full_name"] or member["email"],
                        "member_email": member["email"],
                        "analytics": analytics,
                    }
                )

        # Aggregate team metrics
        team_metrics = self._aggregate_team_metrics(
            member_analytics, privacy_first=privacy_first
        )

        # Generate team insights
        insights = self._generate_team_insights(team_metrics, member_analytics)

        response = {
            "team_id": team_id,
            "period_days": days,
            "team_size": len(team_members),
            "team_metrics": team_metrics,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
        }

        if not privacy_first:
            response["member_analytics"] = member_analytics

        return response

    async def compare_teams(
        self, db: AsyncSession, team_ids: List[int], days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare analytics across multiple teams

        Args:
            db: Database session
            team_ids: List of team IDs to compare
            days: Number of days to analyze

        Returns:
            Comparison data
        """
        team_comparisons = []

        for team_id in team_ids:
            analytics = await self.get_team_analytics(db, team_id, days)
            team_comparisons.append(
                {"team_id": team_id, "metrics": analytics["team_metrics"]}
            )

        # Generate comparison insights
        rankings = self._rank_teams(team_comparisons)

        return {
            "period_days": days,
            "teams_compared": len(team_ids),
            "team_rankings": rankings,
            "best_performing": rankings[0] if rankings else None,
            "improvement_areas": self._identify_improvement_areas(team_comparisons),
        }

    async def get_organization_analytics(
        self, db: AsyncSession, organization_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics for entire organization

        Args:
            db: Database session
            organization_id: Organization ID
            days: Number of days to analyze

        Returns:
            Organization analytics
        """
        # Get all teams in organization
        teams = await self._get_organization_teams(db, organization_id)

        if not teams:
            return self._empty_org_analytics(organization_id)

        # Get analytics for each team
        team_analytics = []
        for team in teams:
            analytics = await self.get_team_analytics(db, team["id"], days)
            team_analytics.append(
                {
                    "team_id": team["id"],
                    "team_name": team["name"],
                    "analytics": analytics,
                }
            )

        # Aggregate organization metrics
        org_metrics = self._aggregate_organization_metrics(team_analytics)

        # Generate organization insights
        insights = self._generate_organization_insights(org_metrics, team_analytics)

        return {
            "organization_id": organization_id,
            "period_days": days,
            "total_teams": len(teams),
            "team_analytics": team_analytics,
            "organization_metrics": org_metrics,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _get_team_members(self, db: AsyncSession, team_id: int) -> List[Dict]:
        """Get all members of a team"""
        # TODO: Implement actual database query
        # For now, return mock data
        return [
            {"id": 1, "full_name": "John Doe", "email": "john@example.com"},
            {"id": 2, "full_name": "Jane Smith", "email": "jane@example.com"},
            {"id": 3, "full_name": "Bob Johnson", "email": "bob@example.com"},
            {"id": 4, "full_name": "Alice Williams", "email": "alice@example.com"},
            {"id": 5, "full_name": "Charlie Brown", "email": "charlie@example.com"},
        ]

    async def _get_member_analytics(self, member_id: int, days: int) -> Dict[str, Any]:
        """Get analytics for individual team member"""
        # TODO: Implement actual data fetching from email monitoring
        # For now, return mock data
        return {
            "total_emails": 1250,
            "emails_last_period": 87,
            "daily_average": 42,
            "categories": {
                "security": 35,
                "financial": 20,
                "professional": 18,
                "social": 8,
                "promotional": 4,
                "other": 2,
            },
            "response_time": {"avg_minutes": 45, "median_minutes": 30},
            "sentiment": {"positive": 65, "neutral": 25, "negative": 10},
            "stress_level": "moderate",
            "productivity_score": 78,
        }

    def _aggregate_team_metrics(
        self, member_analytics: List[Dict], privacy_first: bool = True
    ) -> Dict[str, Any]:
        """Aggregate individual analytics into team metrics"""
        total_emails = sum(m["analytics"]["total_emails"] for m in member_analytics)
        total_period_emails = sum(
            m["analytics"]["emails_last_period"] for m in member_analytics
        )

        # Aggregate categories
        category_totals = defaultdict(int)
        for member in member_analytics:
            for category, count in member["analytics"]["categories"].items():
                category_totals[category] += count

        # Calculate averages
        avg_daily_average = statistics.mean(
            m["analytics"]["daily_average"] for m in member_analytics
        )

        avg_response_time = statistics.mean(
            m["analytics"]["response_time"]["avg_minutes"] for m in member_analytics
        )

        # Aggregate sentiment
        sentiment_totals = defaultdict(int)
        for member in member_analytics:
            for sentiment, count in member["analytics"]["sentiment"].items():
                sentiment_totals[sentiment] += count

        # Stress distribution
        stress_distribution = Counter(
            m["analytics"]["stress_level"] for m in member_analytics
        )

        # Average productivity
        avg_productivity = statistics.mean(
            m["analytics"]["productivity_score"] for m in member_analytics
        )

        # Top performers
        top_performers = sorted(
            member_analytics,
            key=lambda x: x["analytics"]["productivity_score"],
            reverse=True,
        )[:3]

        return {
            "total_emails": total_emails,
            "emails_this_period": total_period_emails,
            "daily_average_per_member": round(avg_daily_average, 1),
            "category_breakdown": dict(category_totals),
            "average_response_time_minutes": round(avg_response_time, 1),
            "sentiment_distribution": dict(sentiment_totals),
            "stress_distribution": dict(stress_distribution),
            "average_productivity_score": round(avg_productivity, 1),
            "top_performers": [
                {
                    "name": m["member_name"],
                    "score": m["analytics"]["productivity_score"],
                }
                for m in top_performers
            ],
        }

    def _aggregate_organization_metrics(
        self, team_analytics: List[Dict]
    ) -> Dict[str, Any]:
        """Aggregate team analytics into organization metrics"""
        total_teams = len(team_analytics)
        total_members = sum(t["analytics"]["team_size"] for t in team_analytics)

        # Aggregate team metrics
        total_emails = sum(
            t["analytics"]["team_metrics"]["total_emails"] for t in team_analytics
        )

        avg_productivity = statistics.mean(
            t["analytics"]["team_metrics"]["average_productivity_score"]
            for t in team_analytics
        )

        # Best performing team
        best_team = max(
            team_analytics,
            key=lambda x: x["analytics"]["team_metrics"]["average_productivity_score"],
        )

        return {
            "total_teams": total_teams,
            "total_members": total_members,
            "total_emails": total_emails,
            "average_productivity_score": round(avg_productivity, 1),
            "best_performing_team": {
                "team_id": best_team["team_id"],
                "team_name": best_team["team_name"],
                "productivity_score": best_team["analytics"]["team_metrics"][
                    "average_productivity_score"
                ],
            },
        }

    def _generate_team_insights(
        self, metrics: Dict, member_analytics: List[Dict]
    ) -> List[str]:
        """Generate actionable insights for team"""
        insights = []

        # Productivity insight
        if metrics["average_productivity_score"] >= 80:
            insights.append(
                "Team productivity is excellent - maintain current practices"
            )
        elif metrics["average_productivity_score"] >= 60:
            insights.append("Team productivity is good - room for improvement")
        else:
            insights.append(
                "Team productivity needs attention - consider workflow optimization"
            )

        # Stress insight
        high_stress_count = metrics["stress_distribution"].get("high", 0)
        if high_stress_count > len(member_analytics) / 2:
            insights.append(
                "More than half the team shows high stress - consider workload rebalancing"
            )

        # Sentiment insight
        sentiment_dist = metrics["sentiment_distribution"]
        total = sum(sentiment_dist.values())
        if total > 0:
            positive_ratio = sentiment_dist.get("positive", 0) / total
            if positive_ratio > 0.7:
                insights.append("Team maintains highly positive communication tone")
            elif positive_ratio < 0.4:
                insights.append(
                    "Team communication tone is concerning - address team morale"
                )

        # Response time insight
        if metrics["average_response_time_minutes"] > 60:
            insights.append(
                "Average response time is over 1 hour - consider improving communication efficiency"
            )

        return insights

    def _generate_organization_insights(
        self, metrics: Dict, team_analytics: List[Dict]
    ) -> List[str]:
        """Generate insights for organization"""
        insights = []

        insights.append(
            f"Organization has {metrics['total_teams']} teams with {metrics['total_members']} total members"
        )
        insights.append(
            f"Best performing team: {metrics['best_performing_team']['team_name']}"
        )

        if metrics["average_productivity_score"] >= 75:
            insights.append("Organization-wide productivity is strong")
        elif metrics["average_productivity_score"] >= 60:
            insights.append(
                "Organization productivity is satisfactory with room for growth"
            )
        else:
            insights.append("Organization-wide productivity improvement needed")

        return insights

    def _rank_teams(self, team_comparisons: List[Dict]) -> List[Dict]:
        """Rank teams by performance"""
        ranked = sorted(
            team_comparisons,
            key=lambda x: x["metrics"]["average_productivity_score"],
            reverse=True,
        )

        return [
            {
                "rank": idx + 1,
                "team_id": t["team_id"],
                "productivity_score": t["metrics"]["average_productivity_score"],
                "total_emails": t["metrics"]["total_emails"],
                "avg_response_time": t["metrics"]["average_response_time_minutes"],
            }
            for idx, t in enumerate(ranked)
        ]

    def _identify_improvement_areas(self, team_comparisons: List[Dict]) -> List[str]:
        """Identify areas needing improvement across teams"""
        areas = []

        avg_response_time = statistics.mean(
            t["metrics"]["average_response_time_minutes"] for t in team_comparisons
        )

        if avg_response_time > 60:
            areas.append("Response times across all teams could be improved")

        avg_productivity = statistics.mean(
            t["metrics"]["average_productivity_score"] for t in team_comparisons
        )

        if avg_productivity < 70:
            areas.append(
                "Overall productivity below target - consider training programs"
            )

        return areas

    async def _get_organization_teams(
        self, db: AsyncSession, org_id: int
    ) -> List[Dict]:
        """Get all teams in an organization"""
        # TODO: Implement actual database query
        return [
            {"id": 1, "name": "Engineering"},
            {"id": 2, "name": "Sales"},
            {"id": 3, "name": "Marketing"},
        ]

    def _empty_team_analytics(self, team_id: int) -> Dict:
        """Return empty analytics for team with no members"""
        return {
            "team_id": team_id,
            "period_days": 30,
            "team_size": 0,
            "member_analytics": [],
            "team_metrics": {},
            "insights": ["No team members found"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _empty_org_analytics(self, org_id: int) -> Dict:
        """Return empty analytics for organization with no teams"""
        return {
            "organization_id": org_id,
            "period_days": 30,
            "total_teams": 0,
            "team_analytics": [],
            "organization_metrics": {},
            "insights": ["No teams found in organization"],
            "generated_at": datetime.utcnow().isoformat(),
        }


# Singleton instance
team_analytics_service = TeamAnalyticsService()
