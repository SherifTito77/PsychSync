"""
Advanced clinical assessment scorers
LSAS (Social Anxiety), EAT-26 (Eating Disorders), Y-BOCS (OCD)

These scorers extend the existing clinical screening infrastructure
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


# Import from existing module to maintain consistency
from app.services.clinical.additional_scorers import (
    ScoringResult,
    RiskLevel,
    SeverityLevel
)


# ============================================================================
# LSAS - LIEBOWITZ SOCIAL ANXIETY SCALE
# ============================================================================

class LSASScorer:
    """
    Liebowitz Social Anxiety Scale
    Social anxiety disorder screening
    Reliability: α = 0.95
    24 items, each rated on fear (0-3) and avoidance (0-3)
    """

    NAME = "LSAS"
    ITEMS = 24

    SUBSCALES = {
        'performance': [1, 5, 6, 7, 9, 11, 13, 17, 19, 22, 23, 24],  # Speaking/performing
        'social': [2, 3, 4, 8, 10, 12, 14, 15, 16, 18, 20, 21]  # Social interaction
    }

    @staticmethod
    def score(responses: Dict[str, Dict[str, int]]) -> ScoringResult:
        """
        Score LSAS

        Args:
            responses: {
                'item_1': {'fear': 2, 'avoidance': 1},
                'item_2': {'fear': 3, 'avoidance': 2},
                ...
            }
        """

        total_fear = 0
        total_avoidance = 0
        performance_score = 0
        social_score = 0

        for item_num in range(1, LSASScorer.ITEMS + 1):
            item_key = f'item_{item_num}'
            if item_key in responses:
                fear = responses[item_key].get('fear', 0)
                avoidance = responses[item_key].get('avoidance', 0)

                total_fear += fear
                total_avoidance += avoidance

                if item_num in LSASScorer.SUBSCALES['performance']:
                    performance_score += fear + avoidance
                else:
                    social_score += fear + avoidance

        total_score = total_fear + total_avoidance

        # Severity categorization
        if total_score < 55:
            severity = SeverityLevel.MINIMAL.value
            risk_level = RiskLevel.LOW.value
            category = "Minimal to moderate social anxiety"
        elif total_score < 65:
            severity = SeverityLevel.MILD.value
            risk_level = RiskLevel.LOW.value
            category = "Marked social anxiety"
        elif total_score < 80:
            severity = SeverityLevel.MODERATE.value
            risk_level = RiskLevel.MODERATE.value
            category = "Severe social anxiety"
        elif total_score < 95:
            severity = SeverityLevel.MODERATELY_SEVERE.value
            risk_level = RiskLevel.HIGH.value
            category = "Very severe social anxiety"
        else:
            severity = SeverityLevel.SEVERE.value
            risk_level = RiskLevel.HIGH.value
            category = "Extremely severe social anxiety"

        # Crisis alert if avoidance is very high (isolation risk)
        crisis_alert = total_avoidance >= 50 and total_score >= 95

        risk_flags = []
        if total_score >= 80:
            risk_flags.append("SOCIAL_ANXIETY_DISORDER_LIKELY")
        if total_avoidance >= 50:
            risk_flags.append("SEVERE_AVOIDANCE_PATTERN")
        if performance_score > social_score * 1.5:
            risk_flags.append("PERFORMANCE_ANXIETY_DOMINANT")

        subscales = {
            'total_fear': total_fear,
            'total_avoidance': total_avoidance,
            'performance_anxiety': performance_score,
            'social_interaction_anxiety': social_score
        }

        interpretation = (
            f"LSAS Total Score: {total_score}. {category}. "
            f"Fear subscale: {total_fear}, Avoidance subscale: {total_avoidance}. "
            f"Performance situations: {performance_score}, Social situations: {social_score}."
        )

        recommendations = LSASScorer._get_recommendations(severity, total_score, subscales)

        return ScoringResult(
            total_score=total_score,
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores=subscales,
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            risk_flags=risk_flags
        )

    @staticmethod
    def _get_recommendations(severity: str, score: int, subscales: Dict) -> List[str]:
        if score >= 95:
            return [
                "URGENT: Psychiatric evaluation for severe social anxiety disorder",
                "Cognitive Behavioral Therapy (CBT) with exposure component",
                "Consider medication evaluation (SSRI/SNRI)",
                "Gradual exposure therapy to feared situations",
                "Social skills training may be beneficial",
                "Address isolation and avoidance patterns"
            ]
        elif score >= 80:
            return [
                "Mental health evaluation recommended",
                "CBT with exposure therapy highly effective",
                "Consider group therapy for social anxiety",
                "Medication evaluation may be helpful",
                "Practice relaxation techniques before social situations"
            ]
        elif score >= 55:
            return [
                "Consider therapy for social anxiety",
                "CBT techniques for anxiety management",
                "Gradual exposure to feared situations",
                "Mindfulness and relaxation practices",
                "Social skills development"
            ]
        else:
            return [
                "Mild symptoms detected",
                "Self-help resources for social confidence",
                "Continue monitoring symptoms",
                "Seek help if symptoms worsen"
            ]


# ============================================================================
# EAT-26 - EATING ATTITUDES TEST
# ============================================================================

class EAT26Scorer:
    """
    Eating Attitudes Test-26
    Eating disorder screening tool
    Reliability: α = 0.83
    26 items, 6-point scale (0-3 scoring)
    """

    NAME = "EAT-26"
    ITEMS = 26
    REFERRAL_THRESHOLD = 20

    # Items scored in reverse (items 26)
    REVERSE_ITEMS = [26]

    # Subscales
    SUBSCALES = {
        'dieting': [1, 6, 7, 10, 11, 12, 14, 16, 17, 22, 23, 24, 26],
        'bulimia': [3, 4, 9, 18, 21, 25],
        'oral_control': [2, 5, 8, 13, 15, 19, 20]
    }

    @staticmethod
    def score(responses: Dict[int, int], behavioral_questions: Optional[Dict[str, any]] = None) -> ScoringResult:
        """
        Score EAT-26

        Args:
            responses: Item responses (1-26), scale 0-5
            behavioral_questions: {
                'weight_loss_6months': bool,
                'binge_eating': str,  # 'never', 'less_than_once_month', etc.
                'vomiting': str,
                'laxatives': str,
                'exercise': str,
                'bmi_concern': bool
            }
        """

        # Score main items
        total_score = 0
        subscale_scores = {
            'dieting': 0,
            'bulimia': 0,
            'oral_control': 0
        }

        for item_num in range(1, EAT26Scorer.ITEMS + 1):
            if item_num in responses:
                response = responses[item_num]

                # Scoring: Always=3, Usually=2, Often=1, Sometimes/Rarely/Never=0
                # Except item 26 (reversed)
                if item_num in EAT26Scorer.REVERSE_ITEMS:
                    # For item 26, Never=3, Rarely=2, Sometimes=1
                    if response <= 2:  # Never, Rarely, Sometimes
                        score = 3 - response
                    else:
                        score = 0
                else:
                    # Normal scoring
                    if response >= 3:  # Often, Usually, Always
                        score = response - 2
                    else:
                        score = 0

                total_score += score

                # Add to subscales
                for subscale, items in EAT26Scorer.SUBSCALES.items():
                    if item_num in items:
                        subscale_scores[subscale] += score

        # Evaluate behavioral questions
        if behavioral_questions is None:
            behavioral_questions = {}

        behavioral_risk = EAT26Scorer._evaluate_behavioral_questions(behavioral_questions)

        # Determine referral need
        referral_indicated = (
            total_score >= EAT26Scorer.REFERRAL_THRESHOLD or
            behavioral_risk['high_risk']
        )

        if referral_indicated:
            severity = SeverityLevel.MODERATE.value
            risk_level = RiskLevel.HIGH.value
            crisis_alert = True
        elif total_score >= 15:
            severity = SeverityLevel.MILD.value
            risk_level = RiskLevel.MODERATE.value
            crisis_alert = False
        else:
            severity = SeverityLevel.MINIMAL.value
            risk_level = RiskLevel.LOW.value
            crisis_alert = False

        risk_flags = []
        if total_score >= EAT26Scorer.REFERRAL_THRESHOLD:
            risk_flags.append("EATING_DISORDER_LIKELY")
        if behavioral_risk['purging']:
            risk_flags.append("PURGING_BEHAVIORS")
            crisis_alert = True
        if behavioral_risk['severe_restriction']:
            risk_flags.append("SEVERE_DIETARY_RESTRICTION")

        interpretation = EAT26Scorer._generate_interpretation(
            total_score, subscale_scores, behavioral_risk, referral_indicated
        )

        recommendations = EAT26Scorer._get_recommendations(referral_indicated, behavioral_risk)

        return ScoringResult(
            total_score=total_score,
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores=subscale_scores,
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            risk_flags=risk_flags
        )

    @staticmethod
    def _evaluate_behavioral_questions(behavioral: Dict) -> Dict[str, bool]:
        """Evaluate behavioral risk factors"""

        purging = (
            behavioral.get('vomiting', 'never') != 'never' or
            behavioral.get('laxatives', 'never') != 'never'
        )

        binge_eating = behavioral.get('binge_eating', 'never') not in ['never', 'less_than_once_month']

        excessive_exercise = behavioral.get('exercise', 'never') in ['2-6_times_week', 'daily', 'more_than_daily']

        severe_restriction = behavioral.get('weight_loss_6months', False)

        high_risk = purging or (binge_eating and severe_restriction)

        return {
            'purging': purging,
            'binge_eating': binge_eating,
            'excessive_exercise': excessive_exercise,
            'severe_restriction': severe_restriction,
            'high_risk': high_risk
        }

    @staticmethod
    def _generate_interpretation(score: int, subscales: Dict, behavioral: Dict, referral: bool) -> str:
        interpretation = f"EAT-26 Score: {score}. "

        if referral:
            interpretation += (
                "Score indicates significant eating disorder risk. "
                "Professional evaluation strongly recommended. "
            )
        else:
            interpretation += "Score below clinical threshold. "

        # Subscale interpretation
        dominant = max(subscales, key=subscales.get)
        interpretation += f"Primary concerns: {dominant.replace('_', ' ')}. "

        # Behavioral flags
        if behavioral.get('purging'):
            interpretation += "⚠️ PURGING BEHAVIORS REPORTED - Medical evaluation urgent. "
        if behavioral.get('binge_eating'):
            interpretation += "Binge eating patterns detected. "

        return interpretation

    @staticmethod
    def _get_recommendations(referral: bool, behavioral: Dict) -> List[str]:
        if referral or behavioral.get('high_risk'):
            return [
                "URGENT: Eating disorder specialist evaluation required",
                "Medical assessment recommended (complications screening)",
                "Individual therapy focusing on eating behaviors",
                "Nutritional counseling with registered dietitian",
                "Consider family-based therapy if adolescent",
                "If purging: Immediate medical evaluation for electrolyte imbalance"
            ]
        else:
            return [
                "Monitor eating attitudes and behaviors",
                "Consider preventive counseling if concerns develop",
                "Maintain balanced approach to nutrition",
                "Seek help if symptoms worsen",
                "Body image work may be beneficial"
            ]


# ============================================================================
# Y-BOCS - YALE-BROWN OBSESSIVE COMPULSIVE SCALE
# ============================================================================

class YBOCSScorer:
    """
    Yale-Brown Obsessive Compulsive Scale (Severity Scale)
    OCD symptom severity assessment
    Reliability: Inter-rater α = 0.98
    10 items (5 obsessions, 5 compulsions), 0-4 scale each
    """

    NAME = "Y-BOCS"
    ITEMS = 10

    @staticmethod
    def score(responses: Dict[int, int]) -> ScoringResult:
        """
        Score Y-BOCS

        Items:
        1-5: Obsessions (time, interference, distress, resistance, control)
        6-10: Compulsions (time, interference, distress, resistance, control)

        Scale: 0 (none) to 4 (extreme)
        """

        # Calculate subscales
        obsessions_score = sum(responses.get(i, 0) for i in range(1, 6))
        compulsions_score = sum(responses.get(i, 0) for i in range(6, 11))
        total_score = obsessions_score + compulsions_score

        # Severity categories
        if total_score <= 7:
            severity = SeverityLevel.MINIMAL.value
            risk_level = RiskLevel.LOW.value
            category = "Subclinical"
        elif total_score <= 15:
            severity = SeverityLevel.MILD.value
            risk_level = RiskLevel.LOW.value
            category = "Mild OCD"
        elif total_score <= 23:
            severity = SeverityLevel.MODERATE.value
            risk_level = RiskLevel.MODERATE.value
            category = "Moderate OCD"
        elif total_score <= 31:
            severity = SeverityLevel.MODERATELY_SEVERE.value
            risk_level = RiskLevel.HIGH.value
            category = "Severe OCD"
        else:
            severity = SeverityLevel.SEVERE.value
            risk_level = RiskLevel.HIGH.value
            category = "Extreme OCD"

        # Crisis alert if severe functional impairment
        interference_score = responses.get(2, 0) + responses.get(7, 0)  # Interference items
        crisis_alert = total_score >= 32 or interference_score >= 7

        risk_flags = []
        if total_score >= 24:
            risk_flags.append("SEVERE_OCD_SYMPTOMS")
        if interference_score >= 6:
            risk_flags.append("SEVERE_FUNCTIONAL_IMPAIRMENT")
        if obsessions_score > compulsions_score * 1.5:
            risk_flags.append("OBSESSION_DOMINANT")
        elif compulsions_score > obsessions_score * 1.5:
            risk_flags.append("COMPULSION_DOMINANT")

        subscales = {
            'obsessions_severity': obsessions_score,
            'compulsions_severity': compulsions_score,
            'time_consumed': responses.get(1, 0) + responses.get(6, 0),
            'interference': interference_score,
            'distress': responses.get(3, 0) + responses.get(8, 0),
            'resistance': responses.get(4, 0) + responses.get(9, 0),
            'control': responses.get(5, 0) + responses.get(10, 0)
        }

        interpretation = (
            f"Y-BOCS Total Score: {total_score}/40. {category}. "
            f"Obsessions: {obsessions_score}/20, Compulsions: {compulsions_score}/20. "
        )

        if obsessions_score > compulsions_score * 1.3:
            interpretation += "Obsession-dominant presentation. "
        elif compulsions_score > obsessions_score * 1.3:
            interpretation += "Compulsion-dominant presentation. "
        else:
            interpretation += "Balanced obsessive-compulsive presentation. "

        recommendations = YBOCSScorer._get_recommendations(severity, total_score)

        return ScoringResult(
            total_score=total_score,
            severity_level=severity,
            risk_level=risk_level,
            subscale_scores=subscales,
            interpretation=interpretation,
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            risk_flags=risk_flags
        )

    @staticmethod
    def _get_recommendations(severity: str, score: int) -> List[str]:
        if score >= 32:
            return [
                "URGENT: OCD specialist evaluation required",
                "Intensive treatment recommended (ERP + medication)",
                "Exposure and Response Prevention (ERP) therapy - gold standard",
                "Psychiatric medication evaluation (SSRI at high doses)",
                "Consider intensive outpatient program (IOP)",
                "Family involvement in treatment beneficial",
                "Address functional impairment in daily activities"
            ]
        elif score >= 24:
            return [
                "OCD specialist evaluation strongly recommended",
                "Evidence-based treatment: ERP therapy",
                "Medication evaluation (SSRI/clomipramine)",
                "Weekly therapy sessions recommended",
                "Cognitive therapy for obsessional thoughts",
                "Address impact on work/school/relationships"
            ]
        elif score >= 16:
            return [
                "Mental health evaluation recommended for OCD",
                "ERP therapy effective for moderate symptoms",
                "Consider medication if therapy alone insufficient",
                "Self-help resources for OCD management",
                "Monitor symptom progression"
            ]
        elif score >= 8:
            return [
                "Consider evaluation if symptoms bothersome",
                "Self-help strategies for intrusive thoughts",
                "CBT techniques may be helpful",
                "Monitor for symptom worsening"
            ]
        else:
            return [
                "Subclinical symptoms",
                "No treatment needed at this time",
                "Practice stress management",
                "Seek help if symptoms increase"
            ]


# ============================================================================
# SCORER REGISTRY
# ============================================================================

ADVANCED_SCORER_REGISTRY = {
    'LSAS': LSASScorer,
    'EAT26': EAT26Scorer,
    'YBOCS': YBOCSScorer,
}


def get_advanced_scorer(screening_type: str):
    """Get advanced scorer class for screening type"""
    scorer = ADVANCED_SCORER_REGISTRY.get(screening_type)
    if not scorer:
        raise ValueError(f"Unknown advanced screening type: {screening_type}")
    return scorer
