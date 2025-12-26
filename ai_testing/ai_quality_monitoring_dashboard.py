#!/usr/bin/env python3
"""
AI Quality Monitoring Dashboard
Real-time monitoring and visualization of AI system quality metrics
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import argparse

class QualityStatus(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class QualityMetric:
    """Individual quality metric with status and trend"""
    name: str
    current_value: float
    target_value: float
    status: QualityStatus
    trend: str  # "improving", "declining", "stable"
    description: str
    last_updated: datetime
    historical_values: List[float] = field(default_factory=list)

class AIQualityMonitor:
    """Comprehensive AI quality monitoring system"""

    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.historical_data = {}
        self.quality_targets = {
            "ai_consistency": 80.0,
            "hallucination_detection": 80.0,
            "personality_validation": 80.0,
            "recommendation_references": 75.0,
            "ai_bias_detection": 70.0,
            "overall_quality": 80.0
        }

    def load_latest_results(self, results_file: str = None):
        """Load latest AI testing results"""
        if results_file is None:
            # Find the most recent comprehensive report
            report_files = [f for f in os.listdir('.') if f.startswith('comprehensive_ai_testing_report_')]
            if not report_files:
                return self._generate_mock_data()

            latest_file = sorted(report_files)[-1]
            results_file = latest_file

        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
                return self._parse_comprehensive_results(data)
        except Exception as e:
            print(f"⚠️  Could not load results file: {e}")
            return self._generate_mock_data()

    def _parse_comprehensive_results(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Parse comprehensive AI testing results"""
        results = {}

        # Extract individual test results
        test_results = data.get("test_results", {})

        # AI Consistency
        consistency_result = test_results.get("ai_output_consistency", {})
        results["ai_consistency"] = consistency_result.get("overall_consistency", 0.0)

        # Hallucination Detection
        hallucination_result = test_results.get("ai_hallucination_detection", {})
        results["hallucination_detection"] = hallucination_result.get("detection_accuracy", 0.0)

        # Personality Validation
        personality_result = test_results.get("personality_analysis_validation", {})
        results["personality_validation"] = personality_result.get("average_validation_accuracy", 0.0)

        # Recommendation References
        recommendation_result = test_results.get("recommendation_data_reference", {})
        results["recommendation_references"] = recommendation_result.get("overall_verification_rate", 0.0) * 100

        # AI Bias Detection
        bias_result = test_results.get("ai_bias_detection", {})
        results["ai_bias_detection"] = bias_result.get("average_fairness_score", 0.0) * 100

        # Overall Quality
        results["overall_quality"] = data.get("overall_ai_quality_score", 0.0)

        return results

    def _generate_mock_data(self) -> Dict[str, float]:
        """Generate mock data for demonstration"""
        return {
            "ai_consistency": 98.2,
            "hallucination_detection": 90.0,
            "personality_validation": 74.4,
            "recommendation_references": 50.0,
            "ai_bias_detection": 90.2,
            "overall_quality": 75.0
        }

    def calculate_status(self, metric_name: str, value: float) -> QualityStatus:
        """Calculate quality status based on value and target"""
        target = self.quality_targets.get(metric_name, 80.0)

        if value >= target:
            return QualityStatus.EXCELLENT
        elif value >= target * 0.9:
            return QualityStatus.GOOD
        elif value >= target * 0.7:
            return QualityStatus.WARNING
        else:
            return QualityStatus.CRITICAL

    def initialize_metrics(self, results: Dict[str, float]):
        """Initialize quality metrics from test results"""
        metric_configs = {
            "ai_consistency": {
                "description": "Consistency of AI outputs across different models",
                "display_name": "AI Model Consistency"
            },
            "hallucination_detection": {
                "description": "Accuracy of hallucination detection in AI outputs",
                "display_name": "Hallucination Detection"
            },
            "personality_validation": {
                "description": "Accuracy of personality type analysis and validation",
                "display_name": "Personality Analysis Validation"
            },
            "recommendation_references": {
                "description": "Percentage of recommendations properly referencing assessment data",
                "display_name": "Data Grounding in Recommendations"
            },
            "ai_bias_detection": {
                "description": "Fairness and bias detection across demographic groups",
                "display_name": "AI Bias Detection"
            },
            "overall_quality": {
                "description": "Overall AI system quality score",
                "display_name": "Overall AI Quality"
            }
        }

        for metric_name, value in results.items():
            if metric_name in metric_configs:
                config = metric_configs[metric_name]
                status = self.calculate_status(metric_name, value)

                self.metrics[metric_name] = QualityMetric(
                    name=config["display_name"],
                    current_value=value,
                    target_value=self.quality_targets[metric_name],
                    status=status,
                    trend="stable",  # Would be calculated from historical data
                    description=config["description"],
                    last_updated=datetime.now(),
                    historical_values=[value]  # Single data point for now
                )

    def generate_dashboard(self, output_format: str = "text") -> str:
        """Generate AI quality monitoring dashboard"""
        if not self.metrics:
            return "❌ No metrics available. Please run AI testing first."

        dashboard = []

        # Header
        dashboard.append("🤖 PSYNSYNC AI QUALITY MONITORING DASHBOARD")
        dashboard.append("=" * 60)
        dashboard.append(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        dashboard.append(f"Overall Status: {self._get_overall_status()}")
        dashboard.append("")

        # Executive Summary
        dashboard.append("📊 EXECUTIVE SUMMARY")
        dashboard.append("-" * 30)
        overall_score = self.metrics.get("overall_quality")
        if overall_score:
            dashboard.append(f"Overall AI Quality: {overall_score.current_value:.1f}% (Target: {overall_score.target_value:.1f}%)")
            dashboard.append(f"Production Readiness: {'✅ READY' if overall_score.current_value >= 80 else '❌ NOT READY'}")
        else:
            dashboard.append("Overall AI Quality: Not available")
            dashboard.append("Production Readiness: ❌ NOT READY - No data available")
        dashboard.append("")

        # Key Metrics Grid
        dashboard.append("🎯 KEY QUALITY METRICS")
        dashboard.append("-" * 30)

        status_icons = {
            QualityStatus.EXCELLENT: "🟢",
            QualityStatus.GOOD: "🟡",
            QualityStatus.WARNING: "🟠",
            QualityStatus.CRITICAL: "🔴"
        }

        for metric_name, metric in self.metrics.items():
            if metric_name == "overall_quality":
                continue

            icon = status_icons[metric.status]
            trend_icon = "📈" if metric.trend == "improving" else "📉" if metric.trend == "declining" else "➡️"

            dashboard.append(f"{icon} {metric.name}: {metric.current_value:.1f}% (Target: {metric.target_value:.1f}%) {trend_icon}")

        dashboard.append("")

        # Detailed Metrics Analysis
        dashboard.append("📈 DETAILED ANALYSIS")
        dashboard.append("-" * 30)

        for metric_name, metric in self.metrics.items():
            if metric_name == "overall_quality":
                continue

            dashboard.append(f"\n🔍 {metric.name}")
            dashboard.append(f"   Current Performance: {metric.current_value:.1f}%")
            dashboard.append(f"   Target: {metric.target_value:.1f}%")
            dashboard.append(f"   Status: {metric.status.value.upper()}")
            dashboard.append(f"   Gap: {metric.target_value - metric.current_value:.1f}%")
            dashboard.append(f"   Description: {metric.description}")

        # Production Readiness Assessment
        dashboard.append("\n🚀 PRODUCTION READINESS ASSESSMENT")
        dashboard.append("-" * 40)

        ready_metrics = sum(1 for m in self.metrics.values() if m.status in [QualityStatus.EXCELLENT, QualityStatus.GOOD])
        total_metrics = len(self.metrics)
        readiness_percentage = (ready_metrics / total_metrics) * 100

        dashboard.append(f"Readiness Score: {readiness_percentage:.1f}% ({ready_metrics}/{total_metrics} metrics meeting targets)")

        if readiness_percentage >= 80:
            dashboard.append("✅ SYSTEM READY FOR PRODUCTION DEPLOYMENT")
        elif readiness_percentage >= 60:
            dashboard.append("⚠️  SYSTEM CONDITIONALLY READY - Address critical issues first")
        else:
            dashboard.append("❌ SYSTEM NOT READY - Significant improvements required")

        # Priority Recommendations
        dashboard.append("\n💡 PRIORITY RECOMMENDATIONS")
        dashboard.append("-" * 35)

        critical_metrics = [m for m in self.metrics.values() if m.status == QualityStatus.CRITICAL]
        if critical_metrics:
            dashboard.append("🔴 CRITICAL ACTIONS REQUIRED:")
            for metric in critical_metrics:
                gap = metric.target_value - metric.current_value
                dashboard.append(f"   • Improve {metric.name.lower()} by {gap:.1f}% to meet target")

        warning_metrics = [m for m in self.metrics.values() if m.status == QualityStatus.WARNING]
        if warning_metrics:
            dashboard.append("\n🟠 RECOMMENDED IMPROVEMENTS:")
            for metric in warning_metrics:
                gap = metric.target_value - metric.current_value
                dashboard.append(f"   • Optimize {metric.name.lower()} by {gap:.1f}%")

        return "\n".join(dashboard)

    def _get_overall_status(self) -> str:
        """Calculate overall system status"""
        if not self.metrics:
            return "❌ NO DATA"

        critical_count = sum(1 for m in self.metrics.values() if m.status == QualityStatus.CRITICAL)
        total_count = len(self.metrics)

        if critical_count > 0:
            return f"🔴 CRITICAL ({critical_count} critical issues)"
        elif all(m.status == QualityStatus.EXCELLENT for m in self.metrics.values()):
            return "🟢 EXCELLENT"
        else:
            return "🟡 GOOD - Some improvements needed"

    def save_dashboard(self, dashboard_text: str, filename: str = None):
        """Save dashboard to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_quality_dashboard_{timestamp}.txt"

        with open(filename, 'w') as f:
            f.write(dashboard_text)

        return filename

def main():
    """Main entry point for AI Quality Monitoring Dashboard"""
    parser = argparse.ArgumentParser(description="Generate AI Quality Monitoring Dashboard")
    parser.add_argument("--input", "-i", help="Input JSON file with AI testing results")
    parser.add_argument("--output", "-o", help="Output file for dashboard")
    parser.add_argument("--format", "-f", choices=["text", "html"], default="text", help="Output format")

    args = parser.parse_args()

    # Initialize monitoring system
    monitor = AIQualityMonitor()

    # Load latest test results
    results = monitor.load_latest_results(args.input)

    # Initialize metrics
    monitor.initialize_metrics(results)

    # Generate dashboard
    dashboard = monitor.generate_dashboard(args.format)

    # Output dashboard
    if args.output:
        filename = monitor.save_dashboard(dashboard, args.output)
        print(f"📊 Dashboard saved to: {filename}")
    else:
        print(dashboard)

    # Also save with timestamp for historical tracking
    timestamped_file = monitor.save_dashboard(dashboard)
    print(f"📄 Dashboard archived as: {timestamped_file}")

if __name__ == "__main__":
    main()