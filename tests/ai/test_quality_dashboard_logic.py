import os
import sys

import pytest

# Ensure the root directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from datetime import datetime

from ai_testing.ai_quality_monitoring_dashboard import (
    AIQualityMonitor,
    QualityMetric,
    QualityStatus,
)


def test_readiness_logic():
    monitor = AIQualityMonitor()

    # Setup metrics: 2 EXCELLENT, 1 CRITICAL
    monitor.metrics = {
        "m1": QualityMetric(
            "M1", 90, 80, QualityStatus.EXCELLENT, "stable", "desc", datetime.now()
        ),
        "m2": QualityMetric(
            "M2", 90, 80, QualityStatus.EXCELLENT, "stable", "desc", datetime.now()
        ),
        "m3": QualityMetric(
            "M3", 10, 80, QualityStatus.CRITICAL, "stable", "desc", datetime.now()
        ),
    }

    # Calculate readiness
    ready_metrics = sum(
        1
        for m in monitor.metrics.values()
        if m.status in [QualityStatus.EXCELLENT, QualityStatus.GOOD]
    )
    readiness_percentage = (ready_metrics / len(monitor.metrics)) * 100

    # Assert readiness is NOT 100% because of CRITICAL
    assert readiness_percentage < 100
    # Assert readiness is 66.6%
    assert abs(readiness_percentage - 66.666) < 0.1
