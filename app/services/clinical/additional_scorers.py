# app/services/clinical/additional_scorers.py
"""
Additional evidence-based screening tool scorers
Extends core clinical screening capabilities
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class ScoringResult:
    total_score: float
    severity_level: str
    risk_level: str
    subscale_scores: Dict[str, float]
    interpretation: str
    recommendations: List[str]
    crisis_alert: bool
    risk_flags: List[str]


class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SeverityLevel(Enum):
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


# ============================================================================
# MDQ - MOOD DISORDER QUESTIONNAIRE (BIPOLAR SCREENING)
# ============================================================================

class MDQScorer:
    """
    Mood Disorder Questionnaire
    Bipolar disorder screening
    Sensitivity: 0.73, Specificity: 0.90
    """

    NAME = "MDQ"
    ITEMS = 13

    @staticmethod
    def score(responses: Dict[str, any]) -> ScoringResult:
        """
        Score MDQ assessment

        Positive screen requires:
        - 7+ symptoms endorsed (Part 1)
        - Symptoms clustered together (Part 2)
        - Moderate/serious problems caused (Part 3)
        """

        # Part 1: 13 symptom items (yes/no)
        symptom_count = sum(
            1 for i in range(1, 14)
            if responses.get(f'q{i}', False)
        )

        # Part 2: Clustering (yes/no)
        clustered = responses.get('q14_clustered', False)

        # Part 3: Impairment level (0-3)
        impairment = responses.get('q15_impairment', 0)

        # Determine positive screen
        positive_screen = (
            symptom_count >= 7 and
            clustered and
            impairment >= 2  # Moderate or serious problems
        )

        if positive_screen:
            risk_level = RiskLevel.HIGH.value
            severity = SeverityLevel.MODERATE.value
            crisis_alert = True
            risk_flags = ["POSSIBLE_BIPOLAR_DISORDER"]
        elif symptom_count >= 7:
            risk_level = RiskLevel.MODERATE.value
            severity = SeverityLevel.MILD.value
            crisis_alert = False
            risk_flags = ["ELEVATED_MOOD_SYMPTOMS"]
        else:
            risk_level = RiskLevel.LOW.value
            severity = SeverityLevel.MINIMAL.value
            crisis_alert = False
            risk_flags = []

        interpretation = MDQScorer._get_interpretation(
            symptom_count, clustered, impairment, positive_screen
        )
        recommendations = MDQScorer._get_recommendations(positive_screen)

        return ScoringResult(
            total_score=float(symptom_count),
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores={
                'symptom_count': float(symptom_count),
                'impairment_level': float(impairment)
            },
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            risk_flags=risk_flags
        )

    @staticmethod
    def _get_interpretation(symptoms: int, clustered: bool, impairment: int, positive: bool) -> str:
        if positive:
            return (
                f"POSITIVE SCREEN for bipolar disorder ({symptoms} symptoms, "
                f"clustered together, causing moderate-serious impairment). "
                "Psychiatric evaluation strongly recommended."
            )
        elif symptoms >= 7:
            return (
                f"{symptoms} mood symptoms endorsed but did not meet full criteria. "
                "Consider monitoring or clinical evaluation."
            )
        else:
            return f"{symptoms} mood symptoms reported. Low likelihood of bipolar disorder."

    @staticmethod
    def _get_recommendations(positive: bool) -> List[str]:
        if positive:
            return [
                "URGENT: Psychiatric evaluation recommended",
                "Bipolar disorder requires specialized treatment",
                "Medication evaluation important",
                "Do not discontinue any current medications without MD consultation",
                "Avoid stimulants and excessive caffeine"
            ]
        else:
            return [
                "Continue monitoring mood changes",
                "Seek evaluation if symptoms worsen",
                "Maintain regular sleep schedule"
            ]


# ============================================================================
# DAST-10 - DRUG ABUSE SCREENING TEST
# ============================================================================

class DAST10Scorer:
    """
    Drug Abuse Screening Test (10-item version)
    Substance use disorder screening
    Reliability: α = 0.92
    """

    NAME = "DAST-10"
    ITEMS = 10

    @staticmethod
    def score(responses: Dict[str, bool]) -> ScoringResult:
        """Score DAST-10 (yes/no items)"""

        total_score = sum(1 for v in responses.values() if v)

        # Severity categories
        if total_score == 0:
            severity = SeverityLevel.MINIMAL.value
            risk_level = RiskLevel.LOW.value
        elif total_score <= 2:
            severity = SeverityLevel.MILD.value
            risk_level = RiskLevel.LOW.value
        elif total_score <= 5:
            severity = SeverityLevel.MODERATE.value
            risk_level = RiskLevel.MODERATE.value
        elif total_score <= 8:
            severity = SeverityLevel.MODERATELY_SEVERE.value
            risk_level = RiskLevel.HIGH.value
        else:
            severity = SeverityLevel.SEVERE.value
            risk_level = RiskLevel.HIGH.value

        crisis_alert = total_score >= 6
        risk_flags = []

        if total_score >= 6:
            risk_flags.append("SUBSTANCE_USE_DISORDER_LIKELY")
        if total_score >= 9:
            risk_flags.append("SEVERE_SUBSTANCE_USE")

        interpretation = DAST10Scorer._get_interpretation(total_score)
        recommendations = DAST10Scorer._get_recommendations(severity, total_score)

        return ScoringResult(
            total_score=float(total_score),
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores={},
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            risk_flags=risk_flags
        )

    @staticmethod
    def _get_interpretation(score: int) -> str:
        if score == 0:
            return "No drug use problems indicated."
        elif score <= 2:
            return "Low level of drug-related problems."
        elif score <= 5:
            return "Moderate level. Substance use evaluation recommended."
        elif score <= 8:
            return "Substantial drug problems. Treatment recommended."
        else:
            return "Severe drug use problems. Immediate intervention needed."

    @staticmethod
    def _get_recommendations(severity: str, score: int) -> List[str]:
        if score >= 6:
            return [
                "Seek substance use disorder evaluation",
                "Consider addiction treatment program",
                "Connect with support groups (NA, SMART Recovery)",
                "Medical detox may be necessary - consult physician",
                "Address co-occurring mental health conditions"
            ]
        elif score >= 3:
            return [
                "Evaluate substance use patterns",
                "Consider counseling or brief intervention",
                "Monitor for escalation",
                "Reduce harm where possible"
            ]
        else:
            return [
                "Continue healthy coping strategies",
                "Be aware of substance use risks"
            ]


# ============================================================================
# AQ-10 - AUTISM SPECTRUM QUOTIENT (SHORT VERSION)
# ============================================================================

class AQ10Scorer:
    """
    Autism Spectrum Quotient-10
    Adult autism screening
    Sensitivity: 0.88, Specificity: 0.91
    """

    NAME = "AQ-10"
    ITEMS = 10
    CUTOFF = 6  # Score ≥6 suggests autism spectrum

    @staticmethod
    def score(responses: Dict[int, int]) -> ScoringResult:
        """
        Score AQ-10
        Items scored 0 or 1 based on direction
        """

        # Items where "definitely agree" or "slightly agree" scores 1
        agree_scores_1 = [1, 2, 4, 5, 6, 7, 9, 10]

        total_score = 0
        for item, response in responses.items():
            if item in agree_scores_1:
                # Score 1 for "definitely/slightly agree"
                total_score += 1 if response in [3, 4] else 0
            else:
                # Score 1 for "definitely/slightly disagree"
                total_score += 1 if response in [1, 2] else 0

        positive_screen = total_score >= AQ10Scorer.CUTOFF

        if positive_screen:
            severity = SeverityLevel.MODERATE.value
            risk_level = RiskLevel.MODERATE.value
            risk_flags = ["POSSIBLE_AUTISM_SPECTRUM"]
        else:
            severity = SeverityLevel.MINIMAL.value
            risk_level = RiskLevel.LOW.value
            risk_flags = []

        interpretation = AQ10Scorer._get_interpretation(total_score, positive_screen)
        recommendations = AQ10Scorer._get_recommendations(positive_screen)

        return ScoringResult(
            total_score=float(total_score),
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores={},
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=False,
            risk_flags=risk_flags
        )

    @staticmethod
    def _get_interpretation(score: int, positive: bool) -> str:
        if positive:
            return (
                f"Score: {score}/10. Positive screen for autism spectrum traits. "
                "Comprehensive diagnostic evaluation recommended for formal assessment."
            )
        else:
            return f"Score: {score}/10. Below clinical threshold for autism spectrum."

    @staticmethod
    def _get_recommendations(positive: bool) -> List[str]:
        if positive:
            return [
                "Seek comprehensive autism diagnostic evaluation",
                "Consider neuropsychological testing",
                "Explore workplace accommodations if needed",
                "Connect with autism support communities",
                "Occupational therapy may be beneficial"
            ]
        else:
            return [
                "No specific follow-up indicated",
                "Neurodiversity awareness resources available"
            ]


# ============================================================================
# ACE - ADVERSE CHILDHOOD EXPERIENCES
# ============================================================================

class ACEScorer:
    """
    Adverse Childhood Experiences Questionnaire
    Childhood trauma screening
    Predictive validity for adult health outcomes
    """

    NAME = "ACE"
    ITEMS = 10
    CATEGORIES = ['abuse', 'neglect', 'household_dysfunction']

    @staticmethod
    def score(responses: Dict[int, bool]) -> ScoringResult:
        """
        Score ACE (10 yes/no items)
        Score is simple count of "yes" responses
        """

        total_score = sum(1 for v in responses.values() if v)

        # ACE score interpretation
        if total_score == 0:
            severity = SeverityLevel.MINIMAL.value
            risk_level = RiskLevel.LOW.value
        elif total_score <= 3:
            severity = SeverityLevel.MILD.value
            risk_level = RiskLevel.MODERATE.value
        else:  # 4+
            severity = SeverityLevel.MODERATE.value
            risk_level = RiskLevel.HIGH.value

        risk_flags = []
        if total_score >= 4:
            risk_flags.append("HIGH_ACE_SCORE")
            risk_flags.append("TRAUMA_INFORMED_CARE_RECOMMENDED")

        # Calculate subcategories
        subscales = {
            'abuse': float(sum(1 for i in [1, 2, 3] if responses.get(i, False))),
            'neglect': float(sum(1 for i in [4, 5] if responses.get(i, False))),
            'household_dysfunction': float(sum(1 for i in [6, 7, 8, 9, 10] if responses.get(i, False)))
        }

        interpretation = ACEScorer._get_interpretation(total_score, subscales)
        recommendations = ACEScorer._get_recommendations(total_score)

        return ScoringResult(
            total_score=float(total_score),
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores=subscales,
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=False,
            risk_flags=risk_flags
        )

    @staticmethod
    def _get_interpretation(score: int, subscales: Dict) -> str:
        interpretation = f"ACE Score: {score}/10. "

        if score == 0:
            interpretation += "No reported adverse childhood experiences."
        elif score <= 3:
            interpretation += (
                "Some childhood adversity reported. May benefit from "
                "trauma-informed therapeutic approaches."
            )
        else:
            interpretation += (
                "HIGH ACE Score. Significant childhood adversity reported. "
                "Strong predictor of adult health/mental health challenges. "
                "Trauma-focused therapy strongly recommended."
            )

        # Add subcategory details
        categories = []
        if subscales['abuse'] > 0:
            categories.append(f"Abuse: {int(subscales['abuse'])}")
        if subscales['neglect'] > 0:
            categories.append(f"Neglect: {int(subscales['neglect'])}")
        if subscales['household_dysfunction'] > 0:
            categories.append(f"Household dysfunction: {int(subscales['household_dysfunction'])}")

        if categories:
            interpretation += f" Categories: {', '.join(categories)}."

        return interpretation

    @staticmethod
    def _get_recommendations(score: int) -> List[str]:
        if score >= 4:
            return [
                "Trauma-focused therapy strongly recommended (EMDR, CPT, PE)",
                "Screen for PTSD and complex trauma",
                "Address co-occurring conditions (substance use, depression)",
                "Build resilience and coping skills",
                "Consider support groups for trauma survivors"
            ]
        elif score >= 1:
            return [
                "Consider trauma-informed therapy",
                "Monitor for trauma-related symptoms",
                "Build healthy coping mechanisms",
                "Resilience-building activities"
            ]
        else:
            return [
                "No specific trauma-focused interventions indicated",
                "Continue healthy development practices"
            ]


# ============================================================================
# SCORER REGISTRY
# ============================================================================

SCORER_REGISTRY = {
    'MDQ': MDQScorer,
    'DAST10': DAST10Scorer,
    'AQ10': AQ10Scorer,
    'ACE': ACEScorer,
}


def get_scorer(screening_type: str):
    """Get scorer class for screening type"""
    scorer_class = SCORER_REGISTRY.get(screening_type)
    if not scorer_class:
        raise ValueError(f"Unknown screening type: {screening_type}")
    return scorer_class
