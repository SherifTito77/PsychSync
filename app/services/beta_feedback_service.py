"""
Beta User Feedback Collection Service
Comprehensive system for collecting, analyzing, and managing beta user feedback
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
from pathlib import Path
import json
import uuid
from statistics import mean, median

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.core.config import settings

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback that can be collected"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY_ISSUE = "usability_issue"
    GENERAL_FEEDBACK = "general_feedback"
    SATISFACTION_RATING = "satisfaction_rating"
    PERFORMANCE_ISSUE = "performance_issue"
    UI_UX_FEEDBACK = "ui_ux_feedback"
    ERROR_REPORT = "error_report"


class FeedbackCategory(Enum):
    """Categories for organizing feedback"""
    USER_INTERFACE = "user_interface"
    USER_EXPERIENCE = "user_experience"
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    RELIABILITY = "reliability"
    ACCESSIBILITY = "accessibility"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"
    SECURITY = "security"
    DATA_MANAGEMENT = "data_management"


class FeedbackPriority(Enum):
    """Priority levels for feedback items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserSegment(Enum):
    """User segments for targeted feedback analysis"""
    NEW_USERS = "new_users"
    POWER_USERS = "power_users"
    TEAM_ADMINS = "team_admins"
    REGULAR_USERS = "regular_users"
    MOBILE_USERS = "mobile_users"
    DESKTOP_USERS = "desktop_users"
    BETA_TESTERS = "beta_testers"


class SatisfactionScale(Enum):
    """Satisfaction rating scales"""
    VERY_DISSATISFIED = 1
    DISSATISFIED = 2
    NEUTRAL = 3
    SATISFIED = 4
    VERY_SATISFIED = 5


@dataclass
class FeedbackSubmission:
    """Individual feedback submission from beta user"""
    id: str
    user_id: str
    user_segment: UserSegment
    feedback_type: FeedbackType
    category: FeedbackCategory
    title: str
    description: str
    priority: FeedbackPriority
    satisfaction_rating: Optional[int] = None
    feature_context: Optional[str] = None  # Where in the app the feedback was submitted
    device_info: Optional[Dict[str, Any]] = None
    browser_info: Optional[Dict[str, Any]] = None
    session_context: Optional[Dict[str, Any]] = None
    attachments: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "new"  # new, reviewed, in_progress, resolved, closed


@dataclass
class FeedbackSession:
    """Context for a feedback collection session"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    current_page: Optional[str] = None
    user_actions: List[Dict[str, Any]] = field(default_factory=list)
    feedback_prompted: bool = False
    session_duration: Optional[float] = None


@dataclass
class FeedbackPattern:
    """Identified patterns in feedback data"""
    pattern_type: str  # "frequent_issue", "feature_request_cluster", "sentiment_trend"
    description: str
    affected_users: List[str]
    frequency: int
    confidence_score: float
    recommended_action: str
    related_feedback: List[str] = field(default_factory=list)


@dataclass
class FeedbackAnalysis:
    """Analysis of collected feedback data"""
    analysis_period: Dict[str, datetime]
    total_submissions: int
    unique_users: int
    satisfaction_score: float
    top_categories: List[Dict[str, Any]]
    sentiment_trends: Dict[str, float]
    priority_distribution: Dict[str, int]
    identified_patterns: List[FeedbackPattern]
    recommendations: List[str]


@dataclass
class BetaCohort:
    """Beta testing cohort management"""
    cohort_id: str
    name: str
    description: str
    user_ids: List[str]
    target_features: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    engagement_goals: Dict[str, float] = field(default_factory=dict)
    feedback_targets: Dict[str, int] = field(default_factory=dict)


class BetaFeedbackService:
    """Comprehensive beta feedback management service"""

    def __init__(self):
        self.feedback_storage: Dict[str, FeedbackSubmission] = {}
        self.feedback_sessions: Dict[str, FeedbackSession] = {}
        self.beta_cohorts: Dict[str, BetaCohort] = {}
        self.feedback_patterns: Dict[str, FeedbackPattern] = {}

        # Initialize default cohorts
        self._initialize_default_cohorts()

    def _initialize_default_cohorts(self):
        """Initialize default beta testing cohorts"""
        current_time = datetime.utcnow()

        self.beta_cohorts["early_adopters"] = BetaCohort(
            cohort_id="early_adopters",
            name="Early Adopters",
            description="First users testing new features",
            user_ids=[],
            target_features=["team_optimization", "advanced_analytics", "integrations"],
            start_date=current_time,
            engagement_goals={
                "weekly_active_days": 3,
                "feature_usage_rate": 0.7,
                "feedback_submissions_per_week": 2
            },
            feedback_targets={
                "total_submissions": 50,
                "bug_reports": 15,
                "feature_requests": 20,
                "usability_issues": 10
            }
        )

        self.beta_cohorts["power_users"] = BetaCohort(
            cohort_id="power_users",
            name="Power Users",
            description="Experienced users testing advanced features",
            user_ids=[],
            target_features=["api_access", "custom_assessments", "enterprise_features"],
            start_date=current_time,
            engagement_goals={
                "weekly_active_days": 5,
                "feature_usage_rate": 0.9,
                "feedback_submissions_per_week": 3
            },
            feedback_targets={
                "total_submissions": 40,
                "feature_requests": 25,
                "performance_issues": 8,
                "integration_issues": 5
            }
        )

    async def submit_feedback(
        self,
        user_id: str,
        feedback_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> FeedbackSubmission:
        """Submit new feedback from beta user"""
        try:
            # Determine user segment
            user_segment = await self._determine_user_segment(user_id)

            # Create feedback submission
            submission = FeedbackSubmission(
                id=str(uuid.uuid4()),
                user_id=user_id,
                user_segment=user_segment,
                feedback_type=FeedbackType(feedback_data.get("feedback_type", "general_feedback")),
                category=FeedbackCategory(feedback_data.get("category", "functionality")),
                title=feedback_data.get("title", ""),
                description=feedback_data.get("description", ""),
                priority=FeedbackPriority(feedback_data.get("priority", "medium")),
                satisfaction_rating=feedback_data.get("satisfaction_rating"),
                feature_context=feedback_data.get("feature_context"),
                device_info=feedback_data.get("device_info"),
                browser_info=feedback_data.get("browser_info"),
                session_context=feedback_data.get("session_context"),
                attachments=feedback_data.get("attachments", []),
                tags=feedback_data.get("tags", [])
            )

            # Store feedback
            self.feedback_storage[submission.id] = submission

            # Update session if provided
            if session_id and session_id in self.feedback_sessions:
                self.feedback_sessions[session_id].feedback_prompted = True

            # Analyze for patterns
            await self._analyze_feedback_patterns(submission)

            logger.info(f"Feedback submitted: {submission.id} from user {user_id}")
            return submission

        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise

    async def _determine_user_segment(self, user_id: str) -> UserSegment:
        """Determine user segment based on user behavior and characteristics"""
        # This would integrate with user analytics to determine segment
        # For now, returning a default segment
        return UserSegment.BETA_TESTERS

    async def start_feedback_session(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new feedback tracking session"""
        session_id = str(uuid.uuid4())

        session = FeedbackSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            current_page=context.get("current_page") if context else None,
            user_actions=context.get("user_actions", []) if context else []
        )

        self.feedback_sessions[session_id] = session
        logger.info(f"Started feedback session: {session_id} for user {user_id}")

        return session_id

    async def end_feedback_session(self, session_id: str) -> Optional[FeedbackSession]:
        """End feedback tracking session and calculate duration"""
        if session_id not in self.feedback_sessions:
            return None

        session = self.feedback_sessions[session_id]
        session.end_time = datetime.utcnow()
        session.session_duration = (session.end_time - session.start_time).total_seconds()

        logger.info(f"Ended feedback session: {session_id} (duration: {session.session_duration}s)")
        return session

    async def get_user_feedback(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        feedback_type: Optional[FeedbackType] = None
    ) -> List[FeedbackSubmission]:
        """Get feedback submissions for a specific user"""
        feedback_list = []

        for feedback in self.feedback_storage.values():
            if feedback.user_id != user_id:
                continue

            # Filter by date range
            if start_date and feedback.timestamp < start_date:
                continue
            if end_date and feedback.timestamp > end_date:
                continue

            # Filter by feedback type
            if feedback_type and feedback.feedback_type != feedback_type:
                continue

            feedback_list.append(feedback)

        return sorted(feedback_list, key=lambda x: x.timestamp, reverse=True)

    async def get_feedback_by_category(
        self,
        category: FeedbackCategory,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FeedbackSubmission]:
        """Get feedback submissions by category"""
        feedback_list = []

        for feedback in self.feedback_storage.values():
            if feedback.category != category:
                continue

            # Filter by date range
            if start_date and feedback.timestamp < start_date:
                continue
            if end_date and feedback.timestamp > end_date:
                continue

            feedback_list.append(feedback)

        return sorted(feedback_list, key=lambda x: x.timestamp, reverse=True)

    async def get_high_priority_feedback(
        self,
        priority_threshold: FeedbackPriority = FeedbackPriority.HIGH
    ) -> List[FeedbackSubmission]:
        """Get high-priority feedback items"""
        priority_order = {
            FeedbackPriority.CRITICAL: 4,
            FeedbackPriority.HIGH: 3,
            FeedbackPriority.MEDIUM: 2,
            FeedbackPriority.LOW: 1
        }

        threshold_value = priority_order[priority_threshold]

        high_priority = [
            feedback for feedback in self.feedback_storage.values()
            if priority_order[feedback.priority] >= threshold_value
        ]

        return sorted(
            high_priority,
            key=lambda x: (priority_order[x.priority], x.timestamp),
            reverse=True
        )

    async def analyze_feedback_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_segment: Optional[UserSegment] = None
    ) -> FeedbackAnalysis:
        """Analyze collected feedback data and generate insights"""
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Filter feedback based on criteria
        filtered_feedback = []
        for feedback in self.feedback_storage.values():
            if feedback.timestamp < start_date or feedback.timestamp > end_date:
                continue
            if user_segment and feedback.user_segment != user_segment:
                continue
            filtered_feedback.append(feedback)

        if not filtered_feedback:
            return FeedbackAnalysis(
                analysis_period={"start": start_date, "end": end_date},
                total_submissions=0,
                unique_users=0,
                satisfaction_score=0.0,
                top_categories=[],
                sentiment_trends={},
                priority_distribution={},
                identified_patterns=[],
                recommendations=[]
            )

        # Calculate metrics
        unique_users = len(set(f.user_id for f in filtered_feedback))
        satisfaction_scores = [f.satisfaction_rating for f in filtered_feedback if f.satisfaction_rating]
        avg_satisfaction = mean(satisfaction_scores) if satisfaction_scores else 0.0

        # Category analysis
        category_counts = {}
        for feedback in filtered_feedback:
            category_counts[feedback.category.value] = category_counts.get(feedback.category.value, 0) + 1

        top_categories = sorted(
            [{"category": cat, "count": count} for cat, count in category_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # Priority distribution
        priority_dist = {}
        for feedback in filtered_feedback:
            priority_dist[feedback.priority.value] = priority_dist.get(feedback.priority.value, 0) + 1

        # Sentiment trends (simplified)
        sentiment_trends = {
            "positive": len([f for f in filtered_feedback if f.satisfaction_rating and f.satisfaction_rating >= 4]),
            "neutral": len([f for f in filtered_feedback if f.satisfaction_rating == 3]),
            "negative": len([f for f in filtered_feedback if f.satisfaction_rating and f.satisfaction_rating <= 2])
        }

        # Identify patterns
        patterns = await self._identify_feedback_patterns(filtered_feedback)

        # Generate recommendations
        recommendations = await self._generate_recommendations(filtered_feedback, patterns)

        return FeedbackAnalysis(
            analysis_period={"start": start_date, "end": end_date},
            total_submissions=len(filtered_feedback),
            unique_users=unique_users,
            satisfaction_score=avg_satisfaction,
            top_categories=top_categories,
            sentiment_trends=sentiment_trends,
            priority_distribution=priority_dist,
            identified_patterns=patterns,
            recommendations=recommendations
        )

    async def _identify_feedback_patterns(
        self,
        feedback_list: List[FeedbackSubmission]
    ) -> List[FeedbackPattern]:
        """Identify patterns in feedback data"""
        patterns = []

        # Check for frequent issues
        issue_clusters = {}
        for feedback in feedback_list:
            key_words = self._extract_key_words(feedback.description)
            for word in key_words:
                if word in issue_clusters:
                    issue_clusters[word].append(feedback)
                else:
                    issue_clusters[word] = [feedback]

        # Create patterns for frequent issues
        for issue, related_feedback in issue_clusters.items():
            if len(related_feedback) >= 3:  # Threshold for pattern detection
                pattern = FeedbackPattern(
                    pattern_type="frequent_issue",
                    description=f"Multiple users reporting issues related to '{issue}'",
                    affected_users=list(set(f.user_id for f in related_feedback)),
                    frequency=len(related_feedback),
                    confidence_score=min(1.0, len(related_feedback) / 10.0),
                    recommended_action=f"Investigate and address issues related to {issue}",
                    related_feedback=[f.id for f in related_feedback]
                )
                patterns.append(pattern)

        # Check for feature request clusters
        feature_requests = [f for f in feedback_list if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        if feature_requests:
            feature_clusters = {}
            for feedback in feature_requests:
                key_words = self._extract_key_words(feedback.description + " " + feedback.title)
                for word in key_words:
                    if word in feature_clusters:
                        feature_clusters[word].append(feedback)
                    else:
                        feature_clusters[word] = [feedback]

            for feature, related_requests in feature_clusters.items():
                if len(related_requests) >= 2:
                    pattern = FeedbackPattern(
                        pattern_type="feature_request_cluster",
                        description=f"Multiple users requesting features related to '{feature}'",
                        affected_users=list(set(f.user_id for f in related_requests)),
                        frequency=len(related_requests),
                        confidence_score=min(1.0, len(related_requests) / 8.0),
                        recommended_action=f"Consider developing features related to {feature}",
                        related_feedback=[f.id for f in related_requests]
                    )
                    patterns.append(pattern)

        return patterns

    def _extract_key_words(self, text: str) -> List[str]:
        """Extract key words from text for pattern analysis"""
        # Simple keyword extraction (in production, would use NLP)
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must"}

        words = text.lower().replace("-", " ").replace("_", " ").split()
        key_words = [word.strip(".,!?;:") for word in words if len(word) > 3 and word not in common_words]

        return list(set(key_words))  # Remove duplicates

    async def _generate_recommendations(
        self,
        feedback_list: List[FeedbackSubmission],
        patterns: List[FeedbackPattern]
    ) -> List[str]:
        """Generate recommendations based on feedback analysis"""
        recommendations = []

        # High-priority issues
        critical_issues = [f for f in feedback_list if f.priority == FeedbackPriority.CRITICAL]
        if critical_issues:
            recommendations.append(
                f"URGENT: Address {len(critical_issues)} critical issues reported by users. "
                "These issues significantly impact user experience and should be prioritized."
            )

        # Low satisfaction
        satisfaction_scores = [f.satisfaction_rating for f in feedback_list if f.satisfaction_rating]
        if satisfaction_scores and mean(satisfaction_scores) < 3.0:
            recommendations.append(
                f"User satisfaction is low ({mean(satisfaction_scores):.1f}/5.0). "
                "Review user feedback and implement improvements to address common pain points."
            )

        # Frequent bugs
        bug_reports = [f for f in feedback_list if f.feedback_type == FeedbackType.BUG_REPORT]
        if len(bug_reports) > len(feedback_list) * 0.4:  # More than 40% bug reports
            recommendations.append(
                f"High number of bug reports ({len(bug_reports)}). "
                "Consider dedicating resources to quality assurance and bug fixing."
            )

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.confidence_score > 0.7:
                recommendations.append(pattern.recommended_action)

        # Feature requests
        feature_requests = [f for f in feedback_list if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        if feature_requests:
            top_requested = {}
            for feedback in feature_requests:
                key_words = self._extract_key_words(feedback.description + " " + feedback.title)
                for word in key_words:
                    if word in top_requested:
                        top_requested[word] += 1
                    else:
                        top_requested[word] = 1

            if top_requested:
                most_requested = max(top_requested.items(), key=lambda x: x[1])
                if most_requested[1] >= 3:
                    recommendations.append(
                        f"Consider prioritizing development of '{most_requested[0]}' features "
                        f"as they have been requested {most_requested[1]} times."
                    )

        return recommendations

    async def _analyze_feedback_patterns(self, new_feedback: FeedbackSubmission):
        """Analyze new feedback for patterns and update stored patterns"""
        # This would integrate with machine learning for pattern detection
        # For now, using simple keyword-based clustering
        pass

    async def get_feedback_summary(
        self,
        days: int = 7,
        user_segment: Optional[UserSegment] = None
    ) -> Dict[str, Any]:
        """Get summary of recent feedback"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        filtered_feedback = []
        for feedback in self.feedback_storage.values():
            if feedback.timestamp < start_date or feedback.timestamp > end_date:
                continue
            if user_segment and feedback.user_segment != user_segment:
                continue
            filtered_feedback.append(feedback)

        summary = {
            "period": f"Last {days} days",
            "total_submissions": len(filtered_feedback),
            "unique_users": len(set(f.user_id for f in filtered_feedback)),
            "by_type": {},
            "by_priority": {},
            "by_category": {},
            "average_satisfaction": 0.0,
            "trending_issues": []
        }

        # Type breakdown
        for feedback in filtered_feedback:
            feedback_type = feedback.feedback_type.value
            summary["by_type"][feedback_type] = summary["by_type"].get(feedback_type, 0) + 1

        # Priority breakdown
        for feedback in filtered_feedback:
            priority = feedback.priority.value
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1

        # Category breakdown
        for feedback in filtered_feedback:
            category = feedback.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1

        # Average satisfaction
        satisfaction_scores = [f.satisfaction_rating for f in filtered_feedback if f.satisfaction_rating]
        if satisfaction_scores:
            summary["average_satisfaction"] = mean(satisfaction_scores)

        # Trending issues (simplified)
        recent_issues = [f for f in filtered_feedback if f.feedback_type in [FeedbackType.BUG_REPORT, FeedbackType.USABILITY_ISSUE]]
        if recent_issues:
            issue_words = {}
            for feedback in recent_issues:
                words = self._extract_key_words(feedback.description + " " + feedback.title)
                for word in words:
                    issue_words[word] = issue_words.get(word, 0) + 1

            summary["trending_issues"] = sorted(
                [{"issue": word, "count": count} for word, count in issue_words.items() if count >= 2],
                key=lambda x: x["count"],
                reverse=True
            )[:5]

        return summary

    async def manage_beta_cohort(
        self,
        cohort_id: str,
        action: str,
        user_ids: Optional[List[str]] = None,
        updates: Optional[Dict[str, Any]] = None
    ) -> Optional[BetaCohort]:
        """Manage beta testing cohorts"""
        if cohort_id not in self.beta_cohorts:
            return None

        cohort = self.beta_cohorts[cohort_id]

        if action == "add_users" and user_ids:
            cohort.user_ids.extend(user_ids)
            cohort.user_ids = list(set(cohort.user_ids))  # Remove duplicates

        elif action == "remove_users" and user_ids:
            cohort.user_ids = [uid for uid in cohort.user_ids if uid not in user_ids]

        elif action == "update" and updates:
            if "end_date" in updates:
                cohort.end_date = updates["end_date"]
            if "engagement_goals" in updates:
                cohort.engagement_goals.update(updates["engagement_goals"])
            if "feedback_targets" in updates:
                cohort.feedback_targets.update(updates["feedback_targets"])

        elif action == "end":
            cohort.end_date = datetime.utcnow()

        return cohort

    async def get_cohort_feedback(
        self,
        cohort_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[FeedbackSubmission]:
        """Get feedback from specific beta cohort"""
        if cohort_id not in self.beta_cohorts:
            return []

        cohort = self.beta_cohorts[cohort_id]
        cohort_feedback = []

        for feedback in self.feedback_storage.values():
            if feedback.user_id not in cohort.user_ids:
                continue

            # Filter by date range
            if start_date and feedback.timestamp < start_date:
                continue
            if end_date and feedback.timestamp > end_date:
                continue

            cohort_feedback.append(feedback)

        return sorted(cohort_feedback, key=lambda x: x.timestamp, reverse=True)

    async def generate_feedback_report(
        self,
        report_type: str = "comprehensive",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive feedback report"""
        filters = filters or {}

        # Get analysis data
        analysis = await self.analyze_feedback_data(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            user_segment=filters.get("user_segment")
        )

        report = {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "filters_applied": filters,
            "executive_summary": {
                "total_feedback": analysis.total_submissions,
                "unique_contributors": analysis.unique_users,
                "overall_satisfaction": analysis.satisfaction_score,
                "critical_issues": len([f for f in self.feedback_storage.values() if f.priority == FeedbackPriority.CRITICAL])
            },
            "detailed_analysis": {
                "feedback_by_category": analysis.top_categories,
                "priority_distribution": analysis.priority_distribution,
                "sentiment_breakdown": analysis.sentiment_trends
            },
            "identified_patterns": [
                {
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "affected_users": len(pattern.affected_users),
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence_score,
                    "recommended_action": pattern.recommended_action
                }
                for pattern in analysis.identified_patterns
            ],
            "recommendations": analysis.recommendations,
            "action_items": await self._generate_action_items(analysis)
        }

        if report_type == "cohort_specific" and filters.get("cohort_id"):
            cohort_id = filters["cohort_id"]
            if cohort_id in self.beta_cohorts:
                cohort = self.beta_cohorts[cohort_id]
                cohort_feedback = await self.get_cohort_feedback(cohort_id)

                report["cohort_analysis"] = {
                    "cohort_name": cohort.name,
                    "cohort_size": len(cohort.user_ids),
                    "feedback_from_cohort": len(cohort_feedback),
                    "engagement_metrics": {
                        "active_users": len(set(f.user_id for f in cohort_feedback)),
                        "average_feedback_per_user": len(cohort_feedback) / len(set(f.user_id for f in cohort_feedback)) if cohort_feedback else 0
                    },
                    "target_progress": {
                        "total_feedback_progress": len(cohort_feedback) / cohort.feedback_targets.get("total_submissions", 1),
                        "bug_report_progress": len([f for f in cohort_feedback if f.feedback_type == FeedbackType.BUG_REPORT]) / cohort.feedback_targets.get("bug_reports", 1)
                    }
                }

        return report

    async def _generate_action_items(self, analysis: FeedbackAnalysis) -> List[Dict[str, Any]]:
        """Generate specific action items based on feedback analysis"""
        action_items = []

        # Critical issues
        critical_feedback = [f for f in self.feedback_storage.values() if f.priority == FeedbackPriority.CRITICAL]
        for feedback in critical_feedback[:5]:  # Top 5 critical issues
            action_items.append({
                "type": "urgent_fix",
                "title": f"Fix critical issue: {feedback.title}",
                "description": feedback.description,
                "priority": "critical",
                "affected_users": 1,  # Would be calculated based on actual impact
                "estimated_effort": "high",
                "feedback_id": feedback.id
            })

        # Feature requests with high demand
        feature_requests = [f for f in self.feedback_storage.values() if f.feedback_type == FeedbackType.FEATURE_REQUEST]
        feature_demand = {}
        for feedback in feature_requests:
            key_words = self._extract_key_words(feedback.description + " " + feedback.title)
            for word in key_words:
                if word not in feature_demand:
                    feature_demand[word] = []
                feature_demand[word].append(feedback)

        for feature, requests in feature_demand.items():
            if len(requests) >= 3:
                action_items.append({
                    "type": "feature_development",
                    "title": f"Develop '{feature}' feature",
                    "description": f"Feature requested by {len(requests)} users",
                    "priority": "medium",
                    "affected_users": len(set(r.user_id for r in requests)),
                    "estimated_effort": "medium",
                    "related_feedback": [r.id for r in requests]
                })

        # Usability improvements
        usability_issues = [f for f in self.feedback_storage.values() if f.feedback_type == FeedbackType.USABILITY_ISSUE]
        if len(usability_issues) > 5:
            action_items.append({
                "type": "usability_improvement",
                "title": "Improve user experience based on feedback",
                "description": f"Address {len(usability_issues)} usability issues reported by users",
                "priority": "medium",
                "affected_users": len(set(u.user_id for u in usability_issues)),
                "estimated_effort": "medium",
                "related_feedback": [u.id for u in usability_issues]
            })

        return action_items


# Initialize the beta feedback service
beta_feedback_service = BetaFeedbackService()