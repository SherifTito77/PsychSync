"""
Health Monitoring Services Package

Provides comprehensive health monitoring, stress detection, and automated interventions
to prevent work-related health issues and burnout.

Services:
- StressMonitoringService: Analyzes health risks from multiple data sources
- HealthInterventionSystem: Creates and manages automated interventions
"""

from app.services.health.stress_monitoring_service import (
    StressMonitoringService,
    HealthRiskIndicators,
    BiometricData,
    StressLevel,
    BurnoutStage
)

from app.services.health.intervention_system import (
    HealthInterventionSystem,
    InterventionAction,
    InterventionType,
    InterventionUrgency
)

__all__ = [
    # Stress Monitoring
    'StressMonitoringService',
    'HealthRiskIndicators',
    'BiometricData',
    'StressLevel',
    'BurnoutStage',

    # Interventions
    'HealthInterventionSystem',
    'InterventionAction',
    'InterventionType',
    'InterventionUrgency',
]
