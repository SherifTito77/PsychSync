#!/usr/bin/env python3
"""
Comprehensive Bug Tracking and Monitoring Dashboard
===============================================

Real-time bug tracking dashboard with metrics, trend analysis, and
quality assurance insights for the PsychSync platform.

Author: Claude Code Assistant
Date: December 13, 2025
Version: 1.0
"""

import datetime
import json
import random
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class BugStatus(Enum):
    NEW = "New"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    TESTING = "Testing"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REOPENED = "Reopened"


class BugTrend(Enum):
    INCREASING = "Increasing"
    DECREASING = "Decreasing"
    STABLE = "Stable"
    FLUCTUATING = "Fluctuating"


@dataclass
class BugMetrics:
    """Bug tracking metrics"""

    total_bugs: int
    new_bugs: int
    resolved_bugs: int
    critical_bugs: int
    high_priority_bugs: int
    avg_resolution_time: float
    bug_trend: BugTrend
    quality_score: float


@dataclass
class BugReport:
    """Individual bug report with tracking information"""

    id: str
    title: str
    severity: str
    priority: str
    status: BugStatus
    assignee: str
    reporter: str
    created_date: str
    updated_date: str
    resolved_date: Optional[str]
    tags: List[str]
    module: str
    assessment_type: Optional[str]


class BugTrackingDashboard:
    """Comprehensive bug tracking and monitoring dashboard"""

    def __init__(self):
        self.bugs = []
        self.metrics_history = []
        self.init_sample_data()

    def init_sample_data(self):
        """Initialize with sample PsychSync bug data"""
        sample_bugs = [
            {
                "id": "BUG-2025-001",
                "title": "MBTI assessment report fails for large teams",
                "severity": "Critical",
                "priority": "Immediate",
                "status": BugStatus.IN_PROGRESS,
                "assignee": "John Smith",
                "reporter": "QA Team",
                "created_date": "2025-12-01T10:30:00",
                "updated_date": "2025-12-13T14:20:00",
                "resolved_date": None,
                "tags": ["assessment", "report", "MBTI"],
                "module": "Assessment Engine",
                "assessment_type": "MBTI",
            },
            {
                "id": "BUG-2025-002",
                "title": "Login timeout for users with slow connections",
                "severity": "High",
                "priority": "High",
                "status": BugStatus.RESOLVED,
                "assignee": "Sarah Johnson",
                "reporter": "Customer Support",
                "created_date": "2025-12-02T09:15:00",
                "updated_date": "2025-12-10T16:45:00",
                "resolved_date": "2025-12-10T16:45:00",
                "tags": ["authentication", "performance"],
                "module": "Authentication Service",
                "assessment_type": None,
            },
            {
                "id": "BUG-2025-003",
                "title": "Big Five assessment results not saving properly",
                "severity": "High",
                "priority": "High",
                "status": BugStatus.TESTING,
                "assignee": "Mike Chen",
                "reporter": "QA Team",
                "created_date": "2025-12-03T11:20:00",
                "updated_date": "2025-12-12T13:30:00",
                "resolved_date": None,
                "tags": ["assessment", "data", "Big Five"],
                "module": "Data Storage",
                "assessment_type": "Big Five",
            },
            {
                "id": "BUG-2025-004",
                "title": "Team dashboard loading slowly with multiple assessments",
                "severity": "Medium",
                "priority": "Medium",
                "status": BugStatus.NEW,
                "assignee": "Unassigned",
                "reporter": "Team Leader",
                "created_date": "2025-12-11T14:45:00",
                "updated_date": "2025-12-11T14:45:00",
                "resolved_date": None,
                "tags": ["performance", "dashboard"],
                "module": "Frontend",
                "assessment_type": None,
            },
            {
                "id": "BUG-2025-005",
                "title": "Email notifications not sent for completed assessments",
                "severity": "Medium",
                "priority": "Medium",
                "status": BugStatus.ASSIGNED,
                "assignee": "Emily Davis",
                "reporter": "HR Manager",
                "created_date": "2025-12-05T16:30:00",
                "updated_date": "2025-12-13T09:15:00",
                "resolved_date": None,
                "tags": ["notification", "email"],
                "module": "Notification Service",
                "assessment_type": None,
            },
        ]

        self.bugs = [BugReport(**bug) for bug in sample_bugs]

    def calculate_current_metrics(self) -> BugMetrics:
        """Calculate current bug tracking metrics"""

        total_bugs = len(self.bugs)
        new_bugs = len([b for b in self.bugs if b.status == BugStatus.NEW])
        resolved_bugs = len([b for b in self.bugs if b.status == BugStatus.RESOLVED])
        critical_bugs = len([b for b in self.bugs if b.severity == "Critical"])
        high_priority_bugs = len(
            [b for b in self.bugs if b.priority in ["Immediate", "High"]]
        )

        # Calculate average resolution time
        resolved_bugs_list = [
            b for b in self.bugs if b.status == BugStatus.RESOLVED and b.resolved_date
        ]
        if resolved_bugs_list:
            total_resolution_time = 0
            for bug in resolved_bugs_list:
                created = datetime.datetime.fromisoformat(
                    bug.created_date.replace("Z", "+00:00")
                )
                resolved = datetime.datetime.fromisoformat(
                    bug.resolved_date.replace("Z", "+00:00")
                )
                total_resolution_time += (
                    resolved - created
                ).total_seconds() / 3600  # Convert to hours
            avg_resolution_time = total_resolution_time / len(resolved_bugs_list)
        else:
            avg_resolution_time = 0

        # Determine bug trend
        bug_trend = self._calculate_bug_trend()

        # Calculate quality score
        quality_score = self._calculate_quality_score()

        return BugMetrics(
            total_bugs=total_bugs,
            new_bugs=new_bugs,
            resolved_bugs=resolved_bugs,
            critical_bugs=critical_bugs,
            high_priority_bugs=high_priority_bugs,
            avg_resolution_time=avg_resolution_time,
            bug_trend=bug_trend,
            quality_score=quality_score,
        )

    def _calculate_bug_trend(self) -> BugTrend:
        """Calculate bug trend based on recent activity"""
        today = datetime.datetime.now()
        week_ago = today - datetime.timedelta(days=7)

        recent_bugs = [
            b
            for b in self.bugs
            if datetime.datetime.fromisoformat(b.created_date.replace("Z", "+00:00"))
            > week_ago
        ]
        recent_resolved = [
            b
            for b in self.bugs
            if b.resolved_date
            and datetime.datetime.fromisoformat(b.resolved_date.replace("Z", "+00:00"))
            > week_ago
        ]

        if len(recent_bugs) > len(recent_resolved) + 2:
            return BugTrend.INCREASING
        elif len(recent_resolved) > len(recent_bugs) + 2:
            return BugTrend.DECREASING
        elif abs(len(recent_bugs) - len(recent_resolved)) <= 2:
            return BugTrend.STABLE
        else:
            return BugTrend.FLUCTUATING

    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score based on bug metrics"""
        total_bugs = len(self.bugs)
        critical_bugs = len([b for b in self.bugs if b.severity == "Critical"])
        high_priority_bugs = len(
            [b for b in self.bugs if b.priority in ["Immediate", "High"]]
        )
        resolved_bugs = len([b for b in self.bugs if b.status == BugStatus.RESOLVED])

        # Calculate average resolution time
        resolved_bugs_list = [
            b for b in self.bugs if b.status == BugStatus.RESOLVED and b.resolved_date
        ]
        if resolved_bugs_list:
            total_resolution_time = 0
            for bug in resolved_bugs_list:
                created = datetime.datetime.fromisoformat(
                    bug.created_date.replace("Z", "+00:00")
                )
                resolved = datetime.datetime.fromisoformat(
                    bug.resolved_date.replace("Z", "+00:00")
                )
                total_resolution_time += (resolved - created).total_seconds() / 3600
            avg_resolution_time = total_resolution_time / len(resolved_bugs_list)
        else:
            avg_resolution_time = 0

        # Base score starts at 100
        score = 100.0

        # Deduct points for critical and high-priority bugs
        score -= critical_bugs * 15
        score -= high_priority_bugs * 5

        # Add points for resolved bugs
        score += resolved_bugs * 3

        # Deduct points for long resolution times
        if avg_resolution_time > 72:  # More than 3 days
            score -= 10
        elif avg_resolution_time > 48:  # More than 2 days
            score -= 5

        # Ensure score stays within 0-100 range
        return max(0, min(100, score))

    def get_module_breakdown(self) -> Dict[str, Dict[str, int]]:
        """Get bug breakdown by module"""
        module_stats = {}

        for bug in self.bugs:
            module = bug.module
            if module not in module_stats:
                module_stats[module] = {
                    "total": 0,
                    "critical": 0,
                    "high": 0,
                    "new": 0,
                    "resolved": 0,
                }

            module_stats[module]["total"] += 1
            if bug.severity == "Critical":
                module_stats[module]["critical"] += 1
            if bug.priority in ["Immediate", "High"]:
                module_stats[module]["high"] += 1
            if bug.status == BugStatus.NEW:
                module_stats[module]["new"] += 1
            if bug.status == BugStatus.RESOLVED:
                module_stats[module]["resolved"] += 1

        return module_stats

    def get_assessment_type_breakdown(self) -> Dict[str, int]:
        """Get bug breakdown by assessment type"""
        assessment_stats = {}

        for bug in self.bugs:
            if bug.assessment_type:
                assessment_type = bug.assessment_type
                assessment_stats[assessment_type] = (
                    assessment_stats.get(assessment_type, 0) + 1
                )

        return assessment_stats

    def get_team_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics by team member"""
        team_stats = {}

        for bug in self.bugs:
            assignee = bug.assignee
            if assignee not in team_stats:
                team_stats[assignee] = {
                    "total_assigned": 0,
                    "resolved": 0,
                    "in_progress": 0,
                    "avg_resolution_time": 0,
                    "resolution_times": [],
                }

            team_stats[assignee]["total_assigned"] += 1

            if bug.status == BugStatus.RESOLVED and bug.resolved_date:
                team_stats[assignee]["resolved"] += 1
                created = datetime.datetime.fromisoformat(
                    bug.created_date.replace("Z", "+00:00")
                )
                resolved = datetime.datetime.fromisoformat(
                    bug.resolved_date.replace("Z", "+00:00")
                )
                resolution_time = (resolved - created).total_seconds() / 3600
                team_stats[assignee]["resolution_times"].append(resolution_time)

            elif bug.status == BugStatus.IN_PROGRESS:
                team_stats[assignee]["in_progress"] += 1

        # Calculate average resolution times
        for member, stats in team_stats.items():
            if stats["resolution_times"]:
                stats["avg_resolution_time"] = sum(stats["resolution_times"]) / len(
                    stats["resolution_times"]
                )
            del stats["resolution_times"]  # Remove temporary data

        return team_stats

    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""

        metrics = self.calculate_current_metrics()
        module_breakdown = self.get_module_breakdown()
        assessment_breakdown = self.get_assessment_type_breakdown()
        team_performance = self.get_team_performance()

        report = {
            "report_metadata": {
                "generated_date": datetime.datetime.now().isoformat(),
                "report_period": "Current Status",
                "total_bugs_analyzed": len(self.bugs),
            },
            "executive_summary": {
                "overall_quality_score": metrics.quality_score,
                "bug_trend": metrics.bug_trend.value,
                "critical_issues": metrics.critical_bugs,
                "resolution_efficiency": (
                    "Good" if metrics.avg_resolution_time < 48 else "Needs Improvement"
                ),
            },
            "key_metrics": asdict(metrics),
            "module_analysis": module_breakdown,
            "assessment_type_analysis": assessment_breakdown,
            "team_performance": team_performance,
            "recommendations": self._generate_recommendations(metrics),
            "action_items": self._generate_action_items(metrics, module_breakdown),
        }

        return report

    def _generate_recommendations(self, metrics: BugMetrics) -> List[str]:
        """Generate quality improvement recommendations"""

        recommendations = []

        if metrics.critical_bugs > 0:
            recommendations.append(
                f"URGENT: Address {metrics.critical_bugs} critical bugs immediately"
            )

        if metrics.high_priority_bugs > 5:
            recommendations.append(
                f"High priority bug count ({metrics.high_priority_bugs}) requires attention"
            )

        if metrics.avg_resolution_time > 72:
            recommendations.append(
                "Average resolution time exceeds 3 days - review development process"
            )

        if metrics.new_bugs > 3:
            recommendations.append(
                "Growing backlog of new bugs - allocate more QA resources"
            )

        if metrics.bug_trend == BugTrend.INCREASING:
            recommendations.append(
                "Bug trend is increasing - review code quality practices"
            )

        if metrics.quality_score < 70:
            recommendations.append(
                "Overall quality score is below 70 - implement quality improvement initiatives"
            )

        if not recommendations:
            recommendations.append(
                "Quality metrics look good - maintain current practices"
            )

        return recommendations

    def _generate_action_items(
        self, metrics: BugMetrics, module_breakdown: Dict[str, Dict[str, int]]
    ) -> List[str]:
        """Generate specific action items"""

        action_items = []

        # Module-specific actions
        high_risk_modules = [
            module
            for module, stats in module_breakdown.items()
            if stats["critical"] > 0 or stats["high"] > 2
        ]

        for module in high_risk_modules:
            action_items.append(f"Conduct comprehensive code review for {module}")

        # Process improvements
        if metrics.avg_resolution_time > 48:
            action_items.append("Implement daily bug triage meetings")

        if metrics.new_bugs > metrics.resolved_bugs:
            action_items.append("Schedule bug fixing sprint")

        # Quality initiatives
        action_items.append("Update automated test coverage for high-bug modules")
        action_items.append("Review and update development guidelines")

        return action_items

    def display_dashboard(self):
        """Display comprehensive bug tracking dashboard"""

        metrics = self.calculate_current_metrics()
        module_breakdown = self.get_module_breakdown()
        assessment_breakdown = self.get_assessment_type_breakdown()
        team_performance = self.get_team_performance()

        print("📊 PSYCHSYNC BUG TRACKING DASHBOARD")
        print("=" * 100)
        print(f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        print()

        # Executive Summary
        print("📈 EXECUTIVE SUMMARY")
        print("-" * 60)
        quality_icon = (
            "🟢"
            if metrics.quality_score >= 80
            else "🟡" if metrics.quality_score >= 60 else "🔴"
        )
        trend_icon = (
            "📈"
            if metrics.bug_trend == BugTrend.DECREASING
            else "📉" if metrics.bug_trend == BugTrend.INCREASING else "➡️"
        )

        print(f"{quality_icon} Quality Score: {metrics.quality_score}/100")
        print(f"{trend_icon} Bug Trend: {metrics.bug_trend.value}")
        print(f"🔴 Critical Issues: {metrics.critical_bugs}")
        print(f"📊 Total Bugs: {metrics.total_bugs}")
        print(f"✅ Resolved: {metrics.resolved_bugs}")
        print(f"🆕 New: {metrics.new_bugs}")
        print(f"⏱️  Avg Resolution Time: {metrics.avg_resolution_time:.1f} hours")
        print()

        # Module Breakdown
        print("🏗️  MODULE BREAKDOWN")
        print("-" * 60)
        for module, stats in module_breakdown.items():
            status_icon = (
                "🔴" if stats["critical"] > 0 else "🟡" if stats["high"] > 2 else "🟢"
            )
            print(f"{status_icon} {module}:")
            print(
                f"   Total: {stats['total']} | Critical: {stats['critical']} | High: {stats['high']}"
            )
            print(f"   New: {stats['new']} | Resolved: {stats['resolved']}")
            print()

        # Assessment Type Impact
        if assessment_breakdown:
            print("📋 ASSESSMENT TYPE IMPACT")
            print("-" * 60)
            for assessment_type, count in assessment_breakdown.items():
                print(f"📝 {assessment_type}: {count} bugs")
            print()

        # Team Performance
        print("👥 TEAM PERFORMANCE")
        print("-" * 60)
        for member, stats in team_performance.items():
            if member != "Unassigned":
                efficiency = (
                    (stats["resolved"] / stats["total_assigned"] * 100)
                    if stats["total_assigned"] > 0
                    else 0
                )
                efficiency_icon = (
                    "🟢" if efficiency >= 70 else "🟡" if efficiency >= 50 else "🔴"
                )
                print(f"{efficiency_icon} {member}:")
                print(
                    f"   Assigned: {stats['total_assigned']} | Resolved: {stats['resolved']}"
                )
                print(
                    f"   Efficiency: {efficiency:.1f}% | Avg Resolution: {stats['avg_resolution_time']:.1f}h"
                )
                print()

        # Active Critical Bugs
        critical_bugs = [
            b
            for b in self.bugs
            if b.severity == "Critical" and b.status != BugStatus.RESOLVED
        ]
        if critical_bugs:
            print("🚨 ACTIVE CRITICAL BUGS")
            print("-" * 60)
            for bug in critical_bugs:
                print(f"🔴 {bug.id}: {bug.title}")
                print(f"   Assignee: {bug.assignee} | Status: {bug.status.value}")
                print(f"   Module: {bug.module} | Created: {bug.created_date[:10]}")
                print()

        # Recent Activity
        print("🔄 RECENT ACTIVITY")
        print("-" * 60)
        today = datetime.datetime.now()
        recent_bugs = [
            b
            for b in self.bugs
            if datetime.datetime.fromisoformat(b.updated_date.replace("Z", "+00:00"))
            > today - datetime.timedelta(days=7)
        ]

        for bug in recent_bugs[-5:]:  # Show last 5 recent bugs
            status_icon = (
                "🆕"
                if bug.status == BugStatus.NEW
                else "🔧" if bug.status == BugStatus.IN_PROGRESS else "✅"
            )
            print(f"{status_icon} {bug.id}: {bug.title[:50]}...")
            print(f"   Status: {bug.status.value} | Updated: {bug.updated_date[:10]}")
            print()

    def export_report(self, filename: str = None) -> str:
        """Export comprehensive quality report"""

        if filename is None:
            filename = f"psychsync_quality_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = self.generate_quality_report()

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return filename


def main():
    """Main execution function"""
    dashboard = BugTrackingDashboard()

    # Display dashboard
    dashboard.display_dashboard()

    # Generate and export comprehensive report
    report_file = dashboard.export_report()
    print(f"📄 Quality report exported to: {report_file}")

    # Display recommendations
    metrics = dashboard.calculate_current_metrics()
    recommendations = dashboard._generate_recommendations(metrics)

    print("\n💡 QUALITY RECOMMENDATIONS")
    print("-" * 60)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    print("\n🎯 DASHBOARD REFRESH COMPLETE!")


if __name__ == "__main__":
    main()
