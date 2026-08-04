"""
Clinical Screening Scoring Algorithm Tests

Tests all scoring algorithms for accuracy and edge cases
Run with: pytest tests/test_clinical_scoring.py -v
"""

import pytest

from app.services.clinical.scoring_algorithms import (
    score_ace,
    score_aq10,
    score_asrs,
    score_cssrs,
    score_dast10,
    score_gad7,
    score_isi,
    score_mdq,
    score_phq9,
    score_pss10,
)


class TestPHQ9Scoring:
    """Test PHQ-9 depression scoring"""

    def test_minimal_depression(self):
        """Score: 0-4 = Minimal depression"""
        result = score_phq9(
            {
                "q1_interest": 0,
                "q2_depressed": 0,
                "q3_sleep": 0,
                "q4_energy": 1,
                "q5_appetite": 0,
                "q6_self_worth": 0,
                "q7_concentration": 1,
                "q8_motor": 0,
                "q9_suicide": 0,
            }
        )

        assert result["total_score"] == 2
        assert result["severity_level"] == "minimal"
        assert result["risk_level"] == "low"
        assert result["crisis_alert"] == False

    def test_moderate_depression(self):
        """Score: 10-14 = Moderate depression"""
        result = score_phq9(
            {
                "q1_interest": 2,
                "q2_depressed": 2,
                "q3_sleep": 1,
                "q4_energy": 2,
                "q5_appetite": 1,
                "q6_self_worth": 1,
                "q7_concentration": 2,
                "q8_motor": 1,
                "q9_suicide": 0,
            }
        )

        assert result["total_score"] == 12
        assert result["severity_level"] == "moderate"
        assert result["risk_level"] == "moderate"
        assert result["crisis_alert"] == False

    def test_severe_depression(self):
        """Score: 20-27 = Severe depression"""
        result = score_phq9(
            {
                "q1_interest": 3,
                "q2_depressed": 3,
                "q3_sleep": 3,
                "q4_energy": 3,
                "q5_appetite": 2,
                "q6_self_worth": 3,
                "q7_concentration": 2,
                "q8_motor": 3,
                "q9_suicide": 0,
            }
        )

        assert result["total_score"] == 22
        assert result["severity_level"] == "severe"
        assert result["risk_level"] == "critical"
        assert result["crisis_alert"] == False

    def test_suicide_ideation_triggers_crisis(self):
        """Item 9 >= 1 should trigger crisis alert regardless of total score"""
        result = score_phq9(
            {
                "q1_interest": 0,
                "q2_depressed": 0,
                "q3_sleep": 0,
                "q4_energy": 0,
                "q5_appetite": 0,
                "q6_self_worth": 0,
                "q7_concentration": 0,
                "q8_motor": 0,
                "q9_suicide": 2,  # Triggers crisis
            }
        )

        assert result["total_score"] == 2
        assert result["crisis_alert"] == True
        assert result["risk_level"] == "critical"
        # The actual implementation returns specific severity flags
        assert any("suicide" in flag.lower() for flag in result["risk_flags"])


class TestGAD7Scoring:
    """Test GAD-7 anxiety scoring"""

    def test_minimal_anxiety(self):
        """Score: 0-4 = Minimal anxiety"""
        result = score_gad7(
            {
                "q1_nervous": 0,
                "q2_control_worry": 1,
                "q3_worry_too_much": 0,
                "q4_trouble_relaxing": 1,
                "q5_restless": 0,
                "q6_irritable": 0,
                "q7_afraid": 0,
            }
        )

        assert result["total_score"] == 2
        assert result["severity_level"] == "minimal"
        assert result["risk_level"] == "low"

    def test_severe_anxiety(self):
        """Score: 15-21 = Severe anxiety"""
        result = score_gad7(
            {
                "q1_nervous": 3,
                "q2_control_worry": 3,
                "q3_worry_too_much": 2,
                "q4_trouble_relaxing": 2,
                "q5_restless": 2,
                "q6_irritable": 2,
                "q7_afraid": 2,
            }
        )

        assert result["total_score"] == 16
        assert result["severity_level"] == "severe"
        assert result["risk_level"] == "critical"


class TestCSSRSScoring:
    """Test C-SSRS suicide risk scoring"""

    def test_no_ideation_low_risk(self):
        """No suicidal ideation = LOW risk"""
        result = score_cssrs(
            {
                "wish_dead": False,
                "suicidal_thoughts": False,
                "suicidal_intent": 0,
                "suicidal_plan": False,
                "suicidal_attempts": 0,
                "lifetime_attempts": 0,
            }
        )

        assert result["severity_level"] == "no_ideation"
        assert result["risk_level"] == "low"
        assert result["crisis_alert"] == False

    def test_active_ideation_high_risk(self):
        """Active suicidal thoughts = HIGH risk"""
        result = score_cssrs(
            {
                "wish_dead": True,
                "suicidal_thoughts": True,
                "suicidal_intent": 3,  # Strong intent
                "suicidal_plan": False,
                "suicidal_attempts": 0,
                "lifetime_attempts": 0,
            }
        )

        assert result["risk_level"] == "high"
        assert result["crisis_alert"] == True

    def test_recent_attempt_critical_risk(self):
        """Recent attempt = CRITICAL risk (highest level)"""
        result = score_cssrs(
            {
                "wish_dead": True,
                "suicidal_thoughts": True,
                "suicidal_intent": 3,
                "suicidal_plan": True,
                "suicidal_attempts": 1,  # Recent attempt
                "lifetime_attempts": 2,
            }
        )

        assert result["severity_level"] == "recent_attempt"
        assert result["risk_level"] == "critical"
        assert result["crisis_alert"] == True
        assert "recent_attempt" in result["risk_flags"]


class TestMDQScoring:
    """Test MDQ bipolar disorder scoring"""

    def test_negative_screen(self):
        """Few symptoms, not clustered, no impairment = Negative"""
        result = score_mdq(
            {
                "q1": True,
                "q2": False,
                "q3": False,
                "q4": True,
                "q5": False,
                "q6": False,
                "q7": True,
                "q8": False,
                "q9": False,
                "q10": False,
                "q11": False,
                "q12": False,
                "q13": False,
                "q14_clustered": False,
                "q15_impairment": 0,
            }
        )

        assert result["positive_screen"] == False
        assert result["risk_level"] == "low"

    def test_positive_screen(self):
        """7+ symptoms, clustered, with impairment = Positive"""
        result = score_mdq(
            {
                "q1": True,
                "q2": True,
                "q3": True,
                "q4": True,
                "q5": True,
                "q6": True,
                "q7": True,  # 7 symptoms
                "q8": False,
                "q9": False,
                "q10": False,
                "q11": False,
                "q12": False,
                "q13": False,
                "q14_clustered": True,  # Clustered
                "q15_impairment": 2,  # Moderate impairment
            }
        )

        assert result["positive_screen"] == True
        assert result["symptom_count"] == 7
        assert result["risk_level"] == "high"


class TestDAST10Scoring:
    """Test DAST-10 substance use scoring"""

    def test_no_substance_use(self):
        """Score 0-2 = Low risk"""
        result = score_dast10(
            {
                "q1": False,
                "q2": False,
                "q3": False,
                "q4": False,
                "q5": False,
                "q6": False,
                "q7": False,
                "q8": False,
                "q9": False,
                "q10": False,
            }
        )

        assert result["total_score"] == 0
        assert result["severity_level"] == "no_use"
        assert result["risk_level"] == "low"

    def test_severe_substance_use(self):
        """Score 9-10 = Severe (CRITICAL)"""
        result = score_dast10(
            {
                "q1": True,
                "q2": True,
                "q3": True,
                "q4": True,
                "q5": True,
                "q6": True,
                "q7": True,
                "q8": True,
                "q9": True,
                "q10": True,
            }
        )

        assert result["total_score"] == 10
        assert result["severity_level"] == "severe"
        assert result["risk_level"] == "critical"
        assert result["crisis_alert"] == True


class TestAQ10Scoring:
    """Test AQ-10 autism spectrum scoring"""

    def test_no_autism_traits(self):
        """Score < 6 = Negative screen"""
        result = score_aq10(
            {
                "1": 1,  # Disagree
                "2": 1,
                "3": 2,  # Reverse-scored (agree = 0)
                "4": 2,
                "5": 2,
                "6": 2,  # Reverse-scored
                "7": 2,
                "8": 2,  # Reverse-scored
                "9": 2,
                "10": 2,
            }
        )

        assert result["total_score"] == 3
        assert result["positive_screen"] == False
        assert result["risk_level"] == "low"

    def test_autism_traits_detected(self):
        """Score >= 6 = Positive screen"""
        result = score_aq10(
            {
                "1": 4,  # Agree
                "2": 4,
                "3": 1,  # Reverse-scored
                "4": 3,
                "5": 4,
                "6": 1,  # Reverse-scored
                "7": 3,
                "8": 1,  # Reverse-scored
                "9": 4,
                "10": 3,
            }
        )

        assert result["total_score"] == 7
        assert result["positive_screen"] == True
        assert result["risk_level"] == "moderate"


class TestACEScoring:
    """Test ACE childhood trauma scoring"""

    def test_no_adversity(self):
        """Score 0 = No adversity"""
        result = score_ace(
            {
                "1": False,
                "2": False,
                "3": False,
                "4": False,
                "5": False,
                "6": False,
                "7": False,
                "8": False,
                "9": False,
                "10": False,
            }
        )

        assert result["total_score"] == 0
        assert result["risk_level"] == "low"

    def test_high_adversity(self):
        """Score 4+ = High adversity (HIGH risk)"""
        result = score_ace(
            {
                "1": True,
                "2": True,
                "3": True,
                "4": True,
                "5": True,
                "6": True,
                "7": True,
                "8": False,
                "9": False,
                "10": False,
            }
        )

        assert result["total_score"] == 7
        assert result["risk_level"] == "high"
        assert result["subcategories"]["abuse"] == 3
        assert result["subcategories"]["neglect"] == 2
        assert result["subcategories"]["household_dysfunction"] == 2


class TestPSS10Scoring:
    """Test PSS-10 perceived stress scoring"""

    def test_low_stress(self):
        """Score 0-13 = Low stress"""
        result = score_pss10(
            {
                "1": 0,
                "2": 1,
                "3": 0,
                "4": 4,  # Reverse-scored (4 -> 0)
                "5": 4,  # Reverse-scored (4 -> 0)
                "6": 1,
                "7": 3,  # Reverse-scored (3 -> 1)
                "8": 4,  # Reverse-scored (4 -> 0)
                "9": 0,
                "10": 1,
            }
        )

        assert result["total_score"] <= 13
        assert result["severity_level"] == "low_stress"
        assert result["risk_level"] == "low"
        assert result["crisis_alert"] == False

    def test_reverse_scoring(self):
        """Verify items 4, 5, 7, 8 are reverse-scored correctly"""
        # Items 4,5,7,8 = 4 should contribute 0 to total (reverse)
        result = score_pss10(
            {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 4,  # Reverse: 4 -> 0
                "5": 4,  # Reverse: 4 -> 0
                "6": 0,
                "7": 4,  # Reverse: 4 -> 0
                "8": 4,  # Reverse: 4 -> 0
                "9": 0,
                "10": 0,
            }
        )

        # Only reverse-scored items set to 4, others 0
        # Reverse scoring: 4 -> 0, so total should be 0
        assert result["total_score"] == 0

    def test_severe_stress_triggers_crisis(self):
        """Score 27+ = Severe (CRITICAL)"""
        result = score_pss10(
            {
                "1": 4,
                "2": 4,
                "3": 4,
                "4": 0,  # Reverse-scored (0 -> 4)
                "5": 0,  # Reverse-scored (0 -> 4)
                "6": 3,
                "7": 0,  # Reverse-scored (0 -> 4)
                "8": 0,  # Reverse-scored (0 -> 4)
                "9": 4,
                "10": 4,
            }
        )

        assert result["total_score"] >= 27
        assert result["severity_level"] == "severe_stress"
        assert result["risk_level"] == "critical"
        assert result["crisis_alert"] == True


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_missing_responses_default_to_zero(self):
        """Missing question responses should default to 0"""
        result = score_phq9(
            {
                "q1_interest": 1,
                "q2_depressed": 2,
                # All other questions missing
            }
        )

        # Should handle missing keys gracefully
        assert "total_score" in result
        assert result["total_score"] >= 0

    def test_invalid_scores_handled(self):
        """Out-of-range scores should be handled"""
        # This test ensures the algorithm doesn't crash with invalid input
        result = score_phq9(
            {
                "q1_interest": 5,  # Invalid (should be 0-3)
                "q2_depressed": -1,  # Invalid (should be 0-3)
            }
        )

        # Should still return a valid result structure
        assert "total_score" in result
        assert "severity_level" in result

    def test_all_zero_responses(self):
        """All responses = 0 (lowest possible score)"""
        result = score_phq9(
            {
                "q1_interest": 0,
                "q2_depressed": 0,
                "q3_sleep": 0,
                "q4_energy": 0,
                "q5_appetite": 0,
                "q6_self_worth": 0,
                "q7_concentration": 0,
                "q8_motor": 0,
                "q9_suicide": 0,
            }
        )

        assert result["total_score"] == 0
        assert result["severity_level"] == "minimal"

    def test_all_maximum_responses(self):
        """All responses = max value (highest possible score)"""
        result = score_phq9(
            {
                "q1_interest": 3,
                "q2_depressed": 3,
                "q3_sleep": 3,
                "q4_energy": 3,
                "q5_appetite": 3,
                "q6_self_worth": 3,
                "q7_concentration": 3,
                "q8_motor": 3,
                "q9_suicide": 3,
            }
        )

        assert result["total_score"] == 27
        assert result["severity_level"] == "severe"
        assert result["risk_level"] == "critical"


class TestOutputStructure:
    """Verify all scoring functions return consistent structure"""

    def test_phq9_output_structure(self):
        """PHQ-9 returns all required fields"""
        result = score_phq9(
            {
                "q1_interest": 1,
                "q2_depressed": 1,
                "q3_sleep": 1,
                "q4_energy": 1,
                "q5_appetite": 1,
                "q6_self_worth": 1,
                "q7_concentration": 1,
                "q8_motor": 1,
                "q9_suicide": 0,
            }
        )

        required_fields = [
            "screening_type",
            "total_score",
            "severity_level",
            "risk_level",
            "interpretation",
            "recommendations",
            "crisis_alert",
            "risk_flags",
            "completed_at",
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        assert isinstance(result["recommendations"], list)
        assert isinstance(result["risk_flags"], list)
        assert isinstance(result["crisis_alert"], bool)

    def test_all_screening_types_have_consistent_structure(self):
        """All screening tools return the same output structure"""
        screening_functions = [
            ("PHQ9", score_phq9, self.get_phq9_responses()),
            ("GAD7", score_gad7, self.get_gad7_responses()),
            ("PSS10", score_pss10, self.get_pss10_responses()),
        ]

        for name, func, responses in screening_functions:
            result = func(responses)

            # Verify core fields exist
            assert "screening_type" in result, f"{name} missing screening_type"
            assert "total_score" in result, f"{name} missing total_score"
            assert "severity_level" in result, f"{name} missing severity_level"
            assert "risk_level" in result, f"{name} missing risk_level"
            assert "crisis_alert" in result, f"{name} missing crisis_alert"

    def get_phq9_responses(self):
        return {
            "q1_interest": 1,
            "q2_depressed": 1,
            "q3_sleep": 1,
            "q4_energy": 1,
            "q5_appetite": 1,
            "q6_self_worth": 1,
            "q7_concentration": 1,
            "q8_motor": 1,
            "q9_suicide": 0,
        }

    def get_gad7_responses(self):
        return {
            "q1_nervous": 1,
            "q2_control_worry": 1,
            "q3_worry_too_much": 1,
            "q4_trouble_relaxing": 1,
            "q5_restless": 1,
            "q6_irritable": 1,
            "q7_afraid": 1,
        }

    def get_pss10_responses(self):
        return {
            "1": 2,
            "2": 2,
            "3": 2,
            "4": 2,
            "5": 2,
            "6": 2,
            "7": 2,
            "8": 2,
            "9": 2,
            "10": 2,
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


class TestASRSScoring:
    """Test ASRS v1.1 ADHD scoring"""

    def test_no_adhd_indicators(self):
        """No ADHD symptoms detected"""
        result = score_asrs(
            {
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
                "5": 0,
                "6": 0,
                "7": 0,
                "8": 0,
                "9": 0,  # Part A: Inattention
                "10": 0,
                "11": 0,
                "12": 0,
                "13": 0,
                "14": 0,
                "15": 0,
                "16": 0,
                "17": 0,
                "18": 0,  # Part B: Hyperactivity
            }
        )

        assert result["total_score"] == 0
        assert result["part_a_score"] == 0
        assert result["part_b_score"] == 0
        assert result["inattention_adhd"] == False
        assert result["hyperactive_adhd"] == False
        assert result["combined_adhd"] == False
        assert result["risk_level"] == "low"

    def test_inattentive_type_adhd(self):
        """Part A ≥ 24 suggests ADHD inattentive type"""
        result = score_asrs(
            {
                "1": 3,
                "2": 3,
                "3": 3,
                "4": 3,
                "5": 2,
                "6": 2,
                "7": 3,
                "8": 3,
                "9": 2,  # Part A: 24/36
                "10": 1,
                "11": 1,
                "12": 1,
                "13": 0,
                "14": 0,
                "15": 1,
                "16": 0,
                "17": 1,
                "18": 0,  # Part B: 5/36
            }
        )

        assert result["part_a_score"] == 24
        assert result["part_b_score"] == 5
        assert result["inattention_adhd"] == True
        assert result["hyperactive_adhd"] == False
        assert result["combined_adhd"] == False
        assert "inattentive" in result["interpretation"].lower()
        assert result["risk_level"] == "high"

    def test_hyperactive_impulsive_type(self):
        """Part B ≥ 24 suggests ADHD hyperactive-impulsive type"""
        result = score_asrs(
            {
                "1": 0,
                "2": 1,
                "3": 1,
                "4": 0,
                "5": 0,
                "6": 1,
                "7": 0,
                "8": 1,
                "9": 1,  # Part A: 5/36
                "10": 3,
                "11": 3,
                "12": 3,
                "13": 3,
                "14": 2,
                "15": 3,
                "16": 2,
                "17": 3,
                "18": 2,  # Part B: 24/36
            }
        )

        assert result["part_a_score"] == 5
        assert result["part_b_score"] == 24
        assert result["inattention_adhd"] == False
        assert result["hyperactive_adhd"] == True
        assert result["combined_adhd"] == False
        assert "hyperactive" in result["interpretation"].lower()
        assert result["risk_level"] == "high"

    def test_combined_type_adhd(self):
        """Both Part A and Part B ≥ 24 suggests ADHD combined type"""
        result = score_asrs(
            {
                "1": 3,
                "2": 3,
                "3": 3,
                "4": 3,
                "5": 3,
                "6": 3,
                "7": 3,
                "8": 3,
                "9": 3,  # Part A: 27/36
                "10": 3,
                "11": 3,
                "12": 3,
                "13": 3,
                "14": 3,
                "15": 3,
                "16": 3,
                "17": 3,
                "18": 3,  # Part B: 27/36
            }
        )

        assert result["part_a_score"] == 27
        assert result["part_b_score"] == 27
        assert result["inattention_adhd"] == True
        assert result["hyperactive_adhd"] == True
        assert result["combined_adhd"] == True
        assert "combined" in result["interpretation"].lower()
        assert result["risk_level"] == "high"

    def test_subscale_scores(self):
        """Verify subscale scores are correctly calculated and returned"""
        result = score_asrs(
            {
                "1": 2,
                "2": 2,
                "3": 1,
                "4": 2,
                "5": 1,
                "6": 2,
                "7": 1,
                "8": 2,
                "9": 1,  # Part A: 14/36
                "10": 1,
                "11": 2,
                "12": 1,
                "13": 2,
                "14": 1,
                "15": 2,
                "16": 1,
                "17": 2,
                "18": 2,  # Part B: 14/36
            }
        )

        assert "subscale_scores" in result
        assert "inattention" in result["subscale_scores"]
        assert "hyperactivity_impulsivity" in result["subscale_scores"]
        assert result["subscale_scores"]["inattention"] == 14
        assert result["subscale_scores"]["hyperactivity_impulsivity"] == 14

    def test_severe_symptoms_triggers_high_risk(self):
        """Severe symptoms (≥30 in either part) trigger high risk"""
        result = score_asrs(
            {
                "1": 4,
                "2": 4,
                "3": 4,
                "4": 4,
                "5": 3,
                "6": 3,
                "7": 4,
                "8": 4,
                "9": 4,  # Part A: 34/36
                "10": 0,
                "11": 0,
                "12": 0,
                "13": 0,
                "14": 0,
                "15": 0,
                "16": 0,
                "17": 0,
                "18": 0,  # Part B: 0/36
            }
        )

        assert result["part_a_score"] == 34
        assert result["risk_level"] == "high"
        assert "severe_inattention" in result["risk_flags"]


class TestISIScoring:
    """Test ISI Insomnia Severity Index scoring"""

    def test_no_insomnia(self):
        """Score 0-7 = No clinically significant insomnia"""
        result = score_isi({"1": 0, "2": 0, "3": 0, "4": 1, "5": 0, "6": 0, "7": 1})

        assert result["total_score"] == 2
        assert result["severity_level"] == "no_insomnia"
        assert result["risk_level"] == "low"
        assert result["crisis_alert"] == False

    def test_subthreshold_insomnia(self):
        """Score 8-14 = Subthreshold insomnia"""
        result = score_isi({"1": 1, "2": 1, "3": 1, "4": 2, "5": 1, "6": 1, "7": 2})

        assert result["total_score"] == 9
        assert result["severity_level"] == "subthreshold_insomnia"
        assert result["risk_level"] == "low"
        assert "sleep hygiene" in " ".join(result["recommendations"]).lower()

    def test_moderate_insomnia(self):
        """Score 15-21 = Clinical insomnia (moderate)"""
        result = score_isi({"1": 2, "2": 2, "3": 2, "4": 3, "5": 2, "6": 2, "7": 3})

        assert result["total_score"] == 16
        assert result["severity_level"] == "moderate_insomnia"
        assert result["risk_level"] == "moderate"
        assert (
            "CBT-I" in " ".join(result["recommendations"])
            or "cognitive" in " ".join(result["recommendations"]).lower()
        )

    def test_severe_insomnia(self):
        """Score 22-28 = Clinical insomnia (severe)"""
        result = score_isi({"1": 3, "2": 3, "3": 3, "4": 4, "5": 3, "6": 4, "7": 4})

        assert result["total_score"] == 24
        assert result["severity_level"] == "severe_insomnia"
        assert result["risk_level"] == "high"
        assert (
            "urgent" in " ".join(result["recommendations"]).lower()
            or "sleep specialist" in " ".join(result["recommendations"]).lower()
        )

    def test_risk_flags_severe_symptoms(self):
        """Severe individual symptoms trigger specific risk flags"""
        result = score_isi(
            {
                "1": 3,  # Severe sleep onset difficulty
                "2": 3,  # Severe sleep maintenance difficulty
                "3": 0,
                "4": 4,
                "5": 0,
                "6": 0,
                "7": 3,  # Severe daytime impairment
            }
        )

        assert "SEVERE_SLEEP_ONSET_DIFFICULTY" in result["risk_flags"]
        assert "SEVERE_SLEEP_MAINTENANCE_DIFFICULTY" in result["risk_flags"]
        assert "SEVERE_DAYTIME_IMPAIRMENT" in result["risk_flags"]

    def test_clinical_cutoff(self):
        """Score ≥ 15 indicates clinical insomnia"""
        result = score_isi({"1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 3})

        assert result["total_score"] == 15
        assert result["clinical_cutoff"] == 15
        assert result["risk_level"] in ["moderate", "high"]
        assert "clinical evaluation" in " ".join(result["recommendations"]).lower()
