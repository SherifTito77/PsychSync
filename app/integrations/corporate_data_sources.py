# app/integrations/corporate_data_sources.py
"""
Comprehensive Corporate Data Source Integration for PsychSync
Automated continuous behavioral analysis inputs
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of corporate data sources"""
    # Communication Platforms
    EMAIL_METADATA = "email_metadata"
    SLACK_MESSAGES = "slack_messages"
    TEAMS_MESSAGES = "teams_messages"
    ZOOM_TRANSCRIPTS = "zoom_transcripts"

    # Productivity & Collaboration
    CALENDAR_EVENTS = "calendar_events"
    JIRA_ACTIVITY = "jira_activity"
    GITHUB_COMMITS = "github_commits"
    CONFLUENCE_EDITS = "confluence_edits"
    ASANA_TASKS = "asana_tasks"
    MONDAY_PROJECTS = "monday_projects"

    # HR Systems
    WORKDAY_DATA = "workday_data"
    BAMBOO_HR = "bamboo_hr"
    ADP_ATTENDANCE = "adp_attendance"
    TIME_TRACKING = "time_tracking"
    PTO_REQUESTS = "pto_requests"
    PERFORMANCE_REVIEWS = "performance_reviews"

    # Surveys & Feedback
    PULSE_SURVEYS = "pulse_surveys"
    ENGAGEMENT_SURVEYS = "engagement_surveys"
    EXIT_INTERVIEWS = "exit_interviews"
    ONE_ON_ONE_NOTES = "one_on_one_notes"

    # Wellness & Biometrics
    WEARABLE_DATA = "wearable_data"
    WELLNESS_APP_DATA = "wellness_app_data"
    MENTAL_HEALTH_CHECKS = "mental_health_checks"

    # Systems & Access
    VPN_LOGS = "vpn_logs"
    BADGE_SWIPES = "badge_swipes"
    SYSTEM_LOGIN_TIMES = "system_login_times"
    APPLICATION_USAGE = "application_usage"

    # Financial & Compensation
    BONUS_DATA = "bonus_data"
    PROMOTION_DATA = "promotion_data"
    COMPENSATION_CHANGES = "compensation_changes"

    # Learning & Development
    TRAINING_COMPLETIONS = "training_completions"
    CERTIFICATION_DATA = "certification_data"
    SKILL_ASSESSMENTS = "skill_assessments"


@dataclass
class DataSourceConfig:
    """Configuration for a data source integration"""
    source_type: DataSourceType
    enabled: bool
    api_endpoint: Optional[str]
    authentication_method: str
    sync_frequency_hours: int
    data_retention_days: int
    privacy_level: str  # 'metadata_only', 'anonymized', 'full'
    behavioral_signals: List[str]
    requires_consent: bool


class CorporateDataSourceRegistry:
    """
    Registry of all possible corporate data sources with their capabilities
    """

    @staticmethod
    def get_all_sources() -> Dict[DataSourceType, DataSourceConfig]:
        """Get comprehensive list of all integratable data sources"""

        return {
            # ============================================
            # 1. COMMUNICATION PLATFORMS (Highest Value)
            # ============================================

            DataSourceType.EMAIL_METADATA: DataSourceConfig(
                source_type=DataSourceType.EMAIL_METADATA,
                enabled=True,
                api_endpoint="/api/integrations/email",
                authentication_method="oauth2",
                sync_frequency_hours=1,
                data_retention_days=90,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Communication frequency and patterns",
                    "Response time trends",
                    "After-hours work indicators",
                    "Email sentiment (subject lines)",
                    "Network mapping (who talks to whom)",
                    "Urgency keywords detection",
                    "Conflict language indicators",
                    "Thread length (back-and-forth)",
                    "CC/BCC patterns (inclusion/exclusion)",
                    "Meeting invite acceptance rates"
                ],
                requires_consent=True
            ),

            DataSourceType.SLACK_MESSAGES: DataSourceConfig(
                source_type=DataSourceType.SLACK_MESSAGES,
                enabled=True,
                api_endpoint="/api/integrations/slack",
                authentication_method="oauth2",
                sync_frequency_hours=1,
                data_retention_days=90,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Message frequency by time of day",
                    "Emoji usage patterns (emotional indicators)",
                    "Reaction patterns (team morale)",
                    "Thread participation rates",
                    "Response latency",
                    "Weekend/holiday activity",
                    "Channel participation diversity",
                    "Direct message frequency",
                    "Status updates (availability patterns)",
                    "Presence indicators (online/offline patterns)"
                ],
                requires_consent=True
            ),

            DataSourceType.TEAMS_MESSAGES: DataSourceConfig(
                source_type=DataSourceType.TEAMS_MESSAGES,
                enabled=True,
                api_endpoint="/api/integrations/teams",
                authentication_method="microsoft_oauth",
                sync_frequency_hours=1,
                data_retention_days=90,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Meeting participation rates",
                    "Chat activity patterns",
                    "Screen sharing frequency",
                    "Meeting duration trends",
                    "Late joins to meetings",
                    "Video on/off patterns",
                    "Background blur usage (privacy concerns?)",
                    "Breakout room participation",
                    "Hand-raising frequency",
                    "Reaction usage in meetings"
                ],
                requires_consent=True
            ),

            DataSourceType.ZOOM_TRANSCRIPTS: DataSourceConfig(
                source_type=DataSourceType.ZOOM_TRANSCRIPTS,
                enabled=True,
                api_endpoint="/api/integrations/zoom",
                authentication_method="oauth2",
                sync_frequency_hours=4,
                data_retention_days=30,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Speaking time distribution",
                    "Interruption frequency",
                    "Sentiment in speech",
                    "Dominant speakers",
                    "Silent participants",
                    "Meeting engagement scores",
                    "Question-asking frequency",
                    "Agreement/disagreement language",
                    "Confidence in speech patterns",
                    "Meeting length adherence"
                ],
                requires_consent=True
            ),

            # ============================================
            # 2. PRODUCTIVITY & COLLABORATION TOOLS
            # ============================================

            DataSourceType.CALENDAR_EVENTS: DataSourceConfig(
                source_type=DataSourceType.CALENDAR_EVENTS,
                enabled=True,
                api_endpoint="/api/integrations/calendar",
                authentication_method="oauth2",
                sync_frequency_hours=2,
                data_retention_days=180,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Meeting load (hours in meetings)",
                    "Back-to-back meeting frequency",
                    "Focus time availability",
                    "After-hours meetings",
                    "Weekend meetings",
                    "Recurring 1:1 patterns",
                    "Meeting acceptance/decline rates",
                    "Last-minute cancellations",
                    "Double-booked time slots",
                    "Time zone spread (global team stress)"
                ],
                requires_consent=False  # Calendar metadata is less sensitive
            ),

            DataSourceType.JIRA_ACTIVITY: DataSourceConfig(
                source_type=DataSourceType.JIRA_ACTIVITY,
                enabled=True,
                api_endpoint="/api/integrations/jira",
                authentication_method="api_token",
                sync_frequency_hours=4,
                data_retention_days=365,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Ticket volume per person",
                    "Ticket resolution time trends",
                    "Overdue task accumulation",
                    "Priority escalation patterns",
                    "Reassignment frequency",
                    "Comment activity (collaboration)",
                    "Blocker frequency",
                    "Sprint commitment vs completion",
                    "Story point velocity changes",
                    "Bug creation rate (quality stress)"
                ],
                requires_consent=False
            ),

            DataSourceType.GITHUB_COMMITS: DataSourceConfig(
                source_type=DataSourceType.GITHUB_COMMITS,
                enabled=True,
                api_endpoint="/api/integrations/github",
                authentication_method="oauth2",
                sync_frequency_hours=2,
                data_retention_days=365,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Commit frequency patterns",
                    "Code review turnaround time",
                    "PR comment tone analysis",
                    "Merge conflict frequency",
                    "Late-night commit patterns",
                    "Weekend coding activity",
                    "Branch lifecycle duration",
                    "Code churn (rewrites/deletions)",
                    "Review approval/rejection rates",
                    "Collaboration breadth (cross-team PRs)"
                ],
                requires_consent=False
            ),

            DataSourceType.CONFLUENCE_EDITS: DataSourceConfig(
                source_type=DataSourceType.CONFLUENCE_EDITS,
                enabled=True,
                api_endpoint="/api/integrations/confluence",
                authentication_method="api_token",
                sync_frequency_hours=4,
                data_retention_days=180,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Documentation contribution rates",
                    "Knowledge sharing frequency",
                    "Page view patterns",
                    "Comment/feedback engagement",
                    "Edit frequency (knowledge churn)",
                    "Cross-team documentation access",
                    "Search patterns (information seeking)",
                    "Outdated content indicators"
                ],
                requires_consent=False
            ),

            # ============================================
            # 3. HR SYSTEMS & EMPLOYEE DATA
            # ============================================

            DataSourceType.WORKDAY_DATA: DataSourceConfig(
                source_type=DataSourceType.WORKDAY_DATA,
                enabled=True,
                api_endpoint="/api/integrations/workday",
                authentication_method="oauth2",
                sync_frequency_hours=24,
                data_retention_days=730,
                privacy_level='full',
                behavioral_signals=[
                    "Tenure and turnover risk",
                    "Promotion history and cadence",
                    "Department transfers",
                    "Manager changes",
                    "Compensation adjustment patterns",
                    "Job level changes",
                    "Organization structure changes",
                    "Reporting line stability",
                    "Role changes frequency",
                    "Team size fluctuations"
                ],
                requires_consent=False  # HR data with proper governance
            ),

            DataSourceType.BAMBOO_HR: DataSourceConfig(
                source_type=DataSourceType.BAMBOO_HR,
                enabled=True,
                api_endpoint="/api/integrations/bamboohr",
                authentication_method="api_token",
                sync_frequency_hours=24,
                data_retention_days=730,
                privacy_level='full',
                behavioral_signals=[
                    "Time-off request patterns",
                    "Time-off approval/denial rates",
                    "Sick day frequency trends",
                    "Vacation day utilization",
                    "Emergency leave patterns",
                    "Benefits enrollment changes",
                    "Emergency contact updates",
                    "Address changes (life events)",
                    "Dependent changes",
                    "Direct deposit changes"
                ],
                requires_consent=False
            ),

            DataSourceType.TIME_TRACKING: DataSourceConfig(
                source_type=DataSourceType.TIME_TRACKING,
                enabled=True,
                api_endpoint="/api/integrations/timetracking",
                authentication_method="api_token",
                sync_frequency_hours=2,
                data_retention_days=365,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Actual hours worked vs expected",
                    "Overtime frequency",
                    "Weekend work patterns",
                    "Late-night work patterns",
                    "Project time allocation",
                    "Billable vs non-billable time",
                    "Task switching frequency",
                    "Break patterns",
                    "Continuous work stretches",
                    "Multi-project allocation stress"
                ],
                requires_consent=True
            ),

            DataSourceType.PERFORMANCE_REVIEWS: DataSourceConfig(
                source_type=DataSourceType.PERFORMANCE_REVIEWS,
                enabled=True,
                api_endpoint="/api/integrations/performance",
                authentication_method="api_token",
                sync_frequency_hours=168,  # Weekly
                data_retention_days=1095,  # 3 years
                privacy_level='anonymized',
                behavioral_signals=[
                    "Rating trends over time",
                    "Goal achievement rates",
                    "Peer feedback sentiment",
                    "Manager feedback patterns",
                    "Development plan progress",
                    "Skill gap identification",
                    "Career progression trajectory",
                    "Performance improvement plans",
                    "Recognition frequency",
                    "360 feedback consistency"
                ],
                requires_consent=True
            ),

            # ============================================
            # 4. SURVEYS & FEEDBACK MECHANISMS
            # ============================================

            DataSourceType.PULSE_SURVEYS: DataSourceConfig(
                source_type=DataSourceType.PULSE_SURVEYS,
                enabled=True,
                api_endpoint="/api/integrations/pulse-surveys",
                authentication_method="api_token",
                sync_frequency_hours=24,
                data_retention_days=365,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Employee satisfaction scores",
                    "Engagement levels",
                    "Team morale indicators",
                    "Manager effectiveness ratings",
                    "Workload perception",
                    "Work-life balance self-reports",
                    "Stress level self-assessments",
                    "Company culture sentiment",
                    "Career development satisfaction",
                    "Response rate patterns (engagement)"
                ],
                requires_consent=False  # Anonymous surveys
            ),

            DataSourceType.ENGAGEMENT_SURVEYS: DataSourceConfig(
                source_type=DataSourceType.ENGAGEMENT_SURVEYS,
                enabled=True,
                api_endpoint="/api/integrations/engagement",
                authentication_method="api_token",
                sync_frequency_hours=168,  # Weekly
                data_retention_days=730,
                privacy_level='anonymized',
                behavioral_signals=[
                    "eNPS (Employee Net Promoter Score)",
                    "Retention risk indicators",
                    "Pride in organization",
                    "Recommendation likelihood",
                    "Leadership trust scores",
                    "Team collaboration ratings",
                    "Resource availability",
                    "Professional growth opportunities",
                    "Psychological safety indicators",
                    "Inclusion and belonging scores"
                ],
                requires_consent=False
            ),

            DataSourceType.EXIT_INTERVIEWS: DataSourceConfig(
                source_type=DataSourceType.EXIT_INTERVIEWS,
                enabled=True,
                api_endpoint="/api/integrations/exit-interviews",
                authentication_method="api_token",
                sync_frequency_hours=168,
                data_retention_days=1095,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Departure reasons (categorized)",
                    "Manager relationship quality",
                    "Workload sustainability",
                    "Career growth concerns",
                    "Compensation competitiveness",
                    "Work environment issues",
                    "Team dynamics problems",
                    "Burnout indicators",
                    "Toxic behavior reports",
                    "Company culture misalignment"
                ],
                requires_consent=True
            ),

            DataSourceType.ONE_ON_ONE_NOTES: DataSourceConfig(
                source_type=DataSourceType.ONE_ON_ONE_NOTES,
                enabled=True,
                api_endpoint="/api/integrations/one-on-ones",
                authentication_method="api_token",
                sync_frequency_hours=24,
                data_retention_days=365,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Meeting frequency (manager attention)",
                    "Topic patterns (recurring issues)",
                    "Action item completion rates",
                    "Career conversation frequency",
                    "Feedback exchange patterns",
                    "Concern escalation",
                    "Development discussion frequency",
                    "Recognition mentions",
                    "Relationship quality indicators",
                    "Sentiment in notes"
                ],
                requires_consent=True
            ),

            # ============================================
            # 5. WELLNESS & BIOMETRIC DATA
            # ============================================

            DataSourceType.WEARABLE_DATA: DataSourceConfig(
                source_type=DataSourceType.WEARABLE_DATA,
                enabled=True,
                api_endpoint="/api/integrations/wearables",
                authentication_method="oauth2",
                sync_frequency_hours=2,
                data_retention_days=90,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Heart rate variability (stress)",
                    "Sleep quality and duration",
                    "Activity levels",
                    "Resting heart rate trends",
                    "Step counts (sedentary behavior)",
                    "Active minutes per day",
                    "Sleep disruption patterns",
                    "Recovery scores",
                    "Stress level estimates",
                    "Cardio fitness trends"
                ],
                requires_consent=True  # Highly sensitive
            ),

            DataSourceType.WELLNESS_APP_DATA: DataSourceConfig(
                source_type=DataSourceType.WELLNESS_APP_DATA,
                enabled=True,
                api_endpoint="/api/integrations/wellness-apps",
                authentication_method="oauth2",
                sync_frequency_hours=24,
                data_retention_days=180,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Meditation/mindfulness usage",
                    "Mental health check-in scores",
                    "Therapy session attendance",
                    "Wellness program participation",
                    "EAP utilization",
                    "Health coaching engagement",
                    "Fitness challenge participation",
                    "Nutrition tracking",
                    "Stress management tool usage",
                    "Sleep app usage patterns"
                ],
                requires_consent=True
            ),

            DataSourceType.MENTAL_HEALTH_CHECKS: DataSourceConfig(
                source_type=DataSourceType.MENTAL_HEALTH_CHECKS,
                enabled=True,
                api_endpoint="/api/integrations/mental-health",
                authentication_method="api_token",
                sync_frequency_hours=24,
                data_retention_days=365,
                privacy_level='anonymized',
                behavioral_signals=[
                    "PHQ-9 depression screening scores",
                    "GAD-7 anxiety scores",
                    "Burnout inventory results",
                    "Stress perception scales",
                    "Resilience assessments",
                    "Work-life balance ratings",
                    "Sleep quality self-reports",
                    "Energy level tracking",
                    "Mood tracking trends",
                    "Crisis support usage"
                ],
                requires_consent=True
            ),

            # ============================================
            # 6. SYSTEM & ACCESS LOGS
            # ============================================

            DataSourceType.VPN_LOGS: DataSourceConfig(
                source_type=DataSourceType.VPN_LOGS,
                enabled=True,
                api_endpoint="/api/integrations/vpn",
                authentication_method="api_token",
                sync_frequency_hours=1,
                data_retention_days=90,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Remote work patterns",
                    "Connection time distributions",
                    "After-hours access",
                    "Weekend work indicators",
                    "Geographic location patterns",
                    "Travel frequency",
                    "Continuous connection duration",
                    "Disconnection patterns",
                    "Multi-location work (nomadic)",
                    "Time zone challenges"
                ],
                requires_consent=False  # IT security logs
            ),

            DataSourceType.BADGE_SWIPES: DataSourceConfig(
                source_type=DataSourceType.BADGE_SWIPES,
                enabled=True,
                api_endpoint="/api/integrations/badge-access",
                authentication_method="api_token",
                sync_frequency_hours=2,
                data_retention_days=180,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Office presence patterns",
                    "Early arrival frequency",
                    "Late departure frequency",
                    "Weekend office access",
                    "Lunch break patterns",
                    "Conference room usage",
                    "Floor/area access patterns",
                    "Remote vs office balance",
                    "Commute consistency",
                    "After-hours building access"
                ],
                requires_consent=False
            ),

            DataSourceType.SYSTEM_LOGIN_TIMES: DataSourceConfig(
                source_type=DataSourceType.SYSTEM_LOGIN_TIMES,
                enabled=True,
                api_endpoint="/api/integrations/system-logs",
                authentication_method="api_token",
                sync_frequency_hours=1,
                data_retention_days=90,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "First login time distribution",
                    "Last logout time patterns",
                    "Total active hours per day",
                    "Idle time patterns",
                    "Multi-device usage",
                    "Continuous session duration",
                    "Lock/unlock frequency",
                    "Application switching patterns",
                    "Peak productivity hours",
                    "System usage volatility"
                ],
                requires_consent=False
            ),

            DataSourceType.APPLICATION_USAGE: DataSourceConfig(
                source_type=DataSourceType.APPLICATION_USAGE,
                enabled=True,
                api_endpoint="/api/integrations/app-usage",
                authentication_method="api_token",
                sync_frequency_hours=4,
                data_retention_days=90,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Communication tool usage patterns",
                    "Productivity tool engagement",
                    "Development tool usage",
                    "Focus time (deep work apps)",
                    "Context switching frequency",
                    "Multi-tasking indicators",
                    "Tool adoption rates",
                    "Collaboration tool balance",
                    "Learning platform usage",
                    "Distraction app usage"
                ],
                requires_consent=True
            ),

            # ============================================
            # 7. FINANCIAL & COMPENSATION
            # ============================================

            DataSourceType.COMPENSATION_CHANGES: DataSourceConfig(
                source_type=DataSourceType.COMPENSATION_CHANGES,
                enabled=True,
                api_endpoint="/api/integrations/compensation",
                authentication_method="api_token",
                sync_frequency_hours=168,
                data_retention_days=1095,
                privacy_level='anonymized',
                behavioral_signals=[
                    "Salary adjustment frequency",
                    "Promotion timing",
                    "Bonus achievement rates",
                    "Equity grant patterns",
                    "Pay parity indicators",
                    "Compensation satisfaction proxies",
                    "Market adjustment patterns",
                    "Performance-pay correlation",
                    "Retention bonus usage",
                    "Compensation review fairness"
                ],
                requires_consent=False
            ),

            # ============================================
            # 8. LEARNING & DEVELOPMENT
            # ============================================

            DataSourceType.TRAINING_COMPLETIONS: DataSourceConfig(
                source_type=DataSourceType.TRAINING_COMPLETIONS,
                enabled=True,
                api_endpoint="/api/integrations/training",
                authentication_method="api_token",
                sync_frequency_hours=24,
                data_retention_days=730,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Training participation rates",
                    "Course completion velocity",
                    "Learning path progress",
                    "Skill development investment",
                    "Mandatory training compliance",
                    "Self-directed learning",
                    "Cross-functional learning",
                    "Leadership development engagement",
                    "Certificate achievement",
                    "Learning time allocation"
                ],
                requires_consent=False
            ),

            DataSourceType.SKILL_ASSESSMENTS: DataSourceConfig(
                source_type=DataSourceType.SKILL_ASSESSMENTS,
                enabled=True,
                api_endpoint="/api/integrations/skill-assessments",
                authentication_method="api_token",
                sync_frequency_hours=168,
                data_retention_days=730,
                privacy_level='metadata_only',
                behavioral_signals=[
                    "Skill proficiency trends",
                    "Skill gap identification",
                    "Technical competency growth",
                    "Soft skill development",
                    "Assessment frequency",
                    "Peer skill endorsements",
                    "Certification preparation",
                    "Skill diversity",
                    "Role-skill alignment",
                    "Future skill readiness"
                ],
                requires_consent=False
            )
        }

    @staticmethod
    def get_recommended_sources_by_org_size(employee_count: int) -> List[DataSourceType]:
        """Get recommended data sources based on organization size"""

        # Core sources for all sizes
        core_sources = [
            DataSourceType.EMAIL_METADATA,
            DataSourceType.CALENDAR_EVENTS,
            DataSourceType.PULSE_SURVEYS,
            DataSourceType.TIME_TRACKING
        ]

        if employee_count < 50:
            # Small companies - focus on essentials
            return core_sources + [
                DataSourceType.SLACK_MESSAGES,
                DataSourceType.ONE_ON_ONE_NOTES
            ]

        elif employee_count < 500:
            # Mid-size - add collaboration tools
            return core_sources + [
                DataSourceType.SLACK_MESSAGES,
                DataSourceType.TEAMS_MESSAGES,
                DataSourceType.JIRA_ACTIVITY,
                DataSourceType.GITHUB_COMMITS,
                DataSourceType.PERFORMANCE_REVIEWS,
                DataSourceType.ENGAGEMENT_SURVEYS
            ]

        else:
            # Enterprise - comprehensive integration
            return core_sources + [
                DataSourceType.SLACK_MESSAGES,
                DataSourceType.TEAMS_MESSAGES,
                DataSourceType.ZOOM_TRANSCRIPTS,
                DataSourceType.JIRA_ACTIVITY,
                DataSourceType.GITHUB_COMMITS,
                DataSourceType.CONFLUENCE_EDITS,
                DataSourceType.WORKDAY_DATA,
                DataSourceType.PERFORMANCE_REVIEWS,
                DataSourceType.ENGAGEMENT_SURVEYS,
                DataSourceType.EXIT_INTERVIEWS,
                DataSourceType.VPN_LOGS,
                DataSourceType.BADGE_SWIPES,
                DataSourceType.WELLNESS_APP_DATA,
                DataSourceType.TRAINING_COMPLETIONS
            ]

    @staticmethod
    def get_privacy_compliant_sources() -> List[DataSourceType]:
        """Get sources that are most privacy-compliant (metadata only)"""

        all_sources = CorporateDataSourceRegistry.get_all_sources()

        return [
            source_type for source_type, config in all_sources.items()
            if config.privacy_level == 'metadata_only' and not config.requires_consent
        ]

    @staticmethod
    def get_high_value_signals() -> Dict[str, List[DataSourceType]]:
        """Get data sources grouped by high-value behavioral signals"""

        return {
            "Toxicity Detection": [
                DataSourceType.EMAIL_METADATA,
                DataSourceType.SLACK_MESSAGES,
                DataSourceType.ZOOM_TRANSCRIPTS,
                DataSourceType.EXIT_INTERVIEWS,
                DataSourceType.ONE_ON_ONE_NOTES,
                DataSourceType.PERFORMANCE_REVIEWS
            ],

            "Burnout Prevention": [
                DataSourceType.TIME_TRACKING,
                DataSourceType.CALENDAR_EVENTS,
                DataSourceType.VPN_LOGS,
                DataSourceType.SYSTEM_LOGIN_TIMES,
                DataSourceType.EMAIL_METADATA,
                DataSourceType.WEARABLE_DATA,
                DataSourceType.MENTAL_HEALTH_CHECKS
            ],

            "Team Health": [
                DataSourceType.PULSE_SURVEYS,
                DataSourceType.ENGAGEMENT_SURVEYS,
                DataSourceType.SLACK_MESSAGES,
                DataSourceType.JIRA_ACTIVITY,
                DataSourceType.GITHUB_COMMITS,
                DataSourceType.ONE_ON_ONE_NOTES
            ],

            "Leadership Effectiveness": [
                DataSourceType.ONE_ON_ONE_NOTES,
                DataSourceType.PERFORMANCE_REVIEWS,
                DataSourceType.ENGAGEMENT_SURVEYS,
                DataSourceType.EXIT_INTERVIEWS,
                DataSourceType.CALENDAR_EVENTS
            ],

            "Retention Risk": [
                DataSourceType.ENGAGEMENT_SURVEYS,
                DataSourceType.PERFORMANCE_REVIEWS,
                DataSourceType.COMPENSATION_CHANGES,
                DataSourceType.TRAINING_COMPLETIONS,
                DataSourceType.EMAIL_METADATA,
                DataSourceType.SLACK_MESSAGES
            ],

            "Work-Life Balance": [
                DataSourceType.TIME_TRACKING,
                DataSourceType.CALENDAR_EVENTS,
                DataSourceType.EMAIL_METADATA,
                DataSourceType.VPN_LOGS,
                DataSourceType.BADGE_SWIPES,
                DataSourceType.PTO_REQUESTS
            ],

            "Collaboration Quality": [
                DataSourceType.SLACK_MESSAGES,
                DataSourceType.TEAMS_MESSAGES,
                DataSourceType.GITHUB_COMMITS,
                DataSourceType.JIRA_ACTIVITY,
                DataSourceType.CONFLUENCE_EDITS,
                DataSourceType.CALENDAR_EVENTS
            ]
        }


# Integration priority matrix
INTEGRATION_PRIORITY = {
    "Must Have (MVP)": [
        DataSourceType.EMAIL_METADATA,
        DataSourceType.CALENDAR_EVENTS,
        DataSourceType.PULSE_SURVEYS
    ],

    "High Priority": [
        DataSourceType.SLACK_MESSAGES,
        DataSourceType.TEAMS_MESSAGES,
        DataSourceType.TIME_TRACKING,
        DataSourceType.ENGAGEMENT_SURVEYS
    ],

    "Medium Priority": [
        DataSourceType.JIRA_ACTIVITY,
        DataSourceType.GITHUB_COMMITS,
        DataSourceType.PERFORMANCE_REVIEWS,
        DataSourceType.ONE_ON_ONE_NOTES,
        DataSourceType.VPN_LOGS
    ],

    "Nice to Have": [
        DataSourceType.ZOOM_TRANSCRIPTS,
        DataSourceType.WEARABLE_DATA,
        DataSourceType.WELLNESS_APP_DATA,
        DataSourceType.BADGE_SWIPES,
        DataSourceType.TRAINING_COMPLETIONS
    ]
}
