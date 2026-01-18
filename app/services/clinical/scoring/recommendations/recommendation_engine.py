"""
Recommendation engine module.

This module is SOLELY responsible for generating clinical recommendations
based on assessment severity and crisis indicators.

Single Responsibility Principle: Only generate recommendations.
"""

from typing import Dict, List
from abc import ABC, abstractmethod
from ..config import SeverityLevel


class RecommendationStrategy(ABC):
    """Base strategy for recommendation generation"""

    @abstractmethod
    def get_recommendations(self, severity: str, is_crisis: bool) -> List[str]:
        """Generate recommendations based on severity and crisis status"""
        pass


class DepressionRecommendations(RecommendationStrategy):
    """Recommendations for depression screening (PHQ-9)"""

    RECOMMENDATIONS = {
        SeverityLevel.MINIMAL.value: [
            "Continue regular monitoring",
            "Maintain healthy lifestyle habits (sleep, exercise, nutrition)",
            "Reassess in 2-4 weeks if symptoms persist",
            "Reach out for support if symptoms worsen"
        ],
        SeverityLevel.MILD.value: [
            "Consider self-help strategies",
            "Monitor symptoms for worsening",
            "Consult healthcare provider if symptoms persist beyond 2 weeks",
            "Practice stress management techniques"
        ],
        SeverityLevel.MODERATE.value: [
            "Clinical evaluation recommended",
            "Consider psychotherapy (CBT, IPT)",
            "Consider pharmacotherapy if appropriate",
            "Engage social support network"
        ],
        SeverityLevel.MODERATELY_SEVERE.value: [
            "Clinical evaluation strongly recommended",
            "Psychotherapy indicated",
            "Pharmacotherapy likely beneficial",
            "Weekly monitoring required"
        ],
        SeverityLevel.SEVERE.value: [
            "Immediate clinical evaluation required",
            "Combination therapy (psychotherapy + pharmacotherapy)",
            "Consider intensive outpatient or partial hospitalization",
            "Daily monitoring until stabilized",
            "Possible inpatient treatment if safety concerns"
        ]
    }

    CRISIS_RECOMMENDATIONS = [
        "🚨 IMMEDIATE: Contact crisis hotline (988 Suicide & Crisis Lifeline)",
        "🚨 IMMEDIATE: Seek emergency mental health evaluation",
        "Do not be alone if possible",
        "Remove access to means of self-harm",
        "Contact emergency services (911) if imminent danger"
    ]

    def get_recommendations(self, severity: str, is_crisis: bool) -> List[str]:
        """Get PHQ-9 specific recommendations"""
        base_recommendations = self.RECOMMENDATIONS.get(
            severity,
            self.RECOMMENDATIONS[SeverityLevel.MODERATE.value]
        )

        if is_crisis:
            return self.CRISIS_RECOMMENDATIONS + base_recommendations

        return base_recommendations


class AnxietyRecommendations(RecommendationStrategy):
    """Recommendations for anxiety screening (GAD-7)"""

    RECOMMENDATIONS = {
        SeverityLevel.MINIMAL.value: [
            "Continue regular monitoring",
            "Practice relaxation techniques",
            "Maintain healthy lifestyle habits",
        ],
        SeverityLevel.MILD.value: [
            "Consider self-help strategies (mindfulness, relaxation)",
            "Monitor symptoms for worsening",
            "Consult healthcare provider if symptoms persist",
        ],
        SeverityLevel.MODERATE.value: [
            "Clinical evaluation recommended",
            "Consider CBT for anxiety",
            "Stress management techniques",
        ],
        SeverityLevel.SEVERE.value: [
            "Clinical evaluation strongly recommended",
            "CBT indicated",
            "Consider pharmacotherapy if appropriate",
            "Regular monitoring required",
        ]
    }

    def get_recommendations(self, severity: str, is_crisis: bool) -> List[str]:
        """Get GAD-7 specific recommendations"""
        return self.RECOMMENDATIONS.get(
            severity,
            self.RECOMMENDATIONS[SeverityLevel.MODERATE.value]
        )


class ADHDRecommendations(RecommendationStrategy):
    """Recommendations for ADHD screening (ASRS)"""

    RECOMMENDATIONS = {
        "minimal_symptoms": [
            "Continue monitoring symptoms",
            "Maintain healthy lifestyle habits",
            "Seek evaluation if symptoms worsen or impact daily life"
        ],
        "some_symptoms": [
            "Monitor symptoms and consider evaluation if worsening",
            "Self-help strategies: time management, organization, stress reduction",
            "Lifestyle optimization: sleep hygiene, regular exercise, balanced nutrition"
        ],
        "symptoms_present": [
            "Monitor symptoms and consider evaluation if worsening",
            "Self-help strategies: time management, organization, stress reduction",
            "Lifestyle optimization: sleep hygiene, regular exercise, balanced nutrition"
        ],
        "inattentive_type": [
            "Clinical evaluation recommended for inattentive ADHD",
            "Focus strategies: time management, minimizing distractions, organizational tools",
            "Consider cognitive-behavioral therapy for ADHD",
            "Explore workplace/school accommodations if needed"
        ],
        "hyperactive_type": [
            "Clinical evaluation recommended for hyperactive-impulsive ADHD",
            "Impulse control strategies: mindfulness, pause-think-act techniques",
            "Channel energy constructively: regular exercise, movement breaks",
            "Consider behavioral coaching and organizational systems"
        ],
        "combined_type": [
            "Comprehensive clinical evaluation with ADHD specialist recommended",
            "Consider neuropsychological testing to confirm diagnosis",
            "Explore evidence-based treatments: behavioral therapy, medication coaching, skills training",
            "Implement structure: routines, reminders, organizational systems",
            "Schedule follow-up with healthcare provider to discuss treatment options"
        ]
    }

    def get_recommendations(self, severity: str, is_crisis: bool) -> List[str]:
        """Get ASRS specific recommendations"""
        return self.RECOMMENDATIONS.get(
            severity,
            self.RECOMMENDATIONS["minimal_symptoms"]
        )


class RecommendationEngine:
    """
    Main recommendation engine that delegates to specific strategies.

    This provides a clean interface for getting recommendations while
    allowing instrument-specific customization.
    """

    def __init__(self, strategy: RecommendationStrategy):
        self.strategy = strategy

    def generate(self, severity: str, crisis_alert: bool) -> List[str]:
        """
        Generate recommendations using the configured strategy.

        Args:
            severity: Severity level string
            crisis_alert: Whether crisis is detected

        Returns:
            List of recommendation strings
        """
        return self.strategy.get_recommendations(severity, crisis_alert)

    @classmethod
    def for_phq9(cls) -> 'RecommendationEngine':
        """Factory method for PHQ-9 recommendations"""
        return cls(strategy=DepressionRecommendations())

    @classmethod
    def for_gad7(cls) -> 'RecommendationEngine':
        """Factory method for GAD-7 recommendations"""
        return cls(strategy=AnxietyRecommendations())

    @classmethod
    def for_asrs(cls) -> 'RecommendationEngine':
        """Factory method for ASRS recommendations"""
        return cls(strategy=ADHDRecommendations())
