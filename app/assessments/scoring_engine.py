#app/assessments/scoring_engine.py
"""
Scoring Engine for Clinical Assessments.
Calculates scores, interprets results, and provides clinical recommendations.

File: app/assessments/scoring_engine.py

Requirements:
    pip install numpy pandas
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AssessmentScore:
    """Results from assessment scoring."""
    assessment_id: str
    total_score: float
    subscale_scores: Dict[str, float]
    percentile: Optional[float]
    severity_level: str
    interpretation: str
    clinical_significance: str
    recommendations: List[str]
    scored_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ScoringEngine:
    """
    Main scoring engine for all clinical assessments.
    """
    
    def __init__(self):
        """Initialize scoring engine."""
        self.scoring_methods = {
            'phq9': self.score_phq9,
            'gad7': self.score_gad7,
            'dass21': self.score_dass21,
            'bdi': self.score_bdi,
            'audit': self.score_audit,
            'ace': self.score_ace,
            'mmpi2': self.score_mmpi2,
            'stai': self.score_stai,
            'pcl5': self.score_pcl5,
            'cbcl': self.score_cbcl,
            'msi': self.score_msi,
            'eq': self.score_eq,
            'iat': self.score_iat,
            'pcq': self.score_pcq
        }
    
    def score_assessment(
        self,
        assessment_id: str,
        responses: Dict[int, int],
        demographics: Optional[Dict] = None
    ) -> AssessmentScore:
        """
        Score any assessment.
        
        Args:
            assessment_id: Assessment identifier
            responses: Dictionary of item_number -> response_value
            demographics: Optional demographic info for normative comparison
            
        Returns:
            AssessmentScore object
        """
        if assessment_id not in self.scoring_methods:
            raise ValueError(f"Scoring not implemented for {assessment_id}")
        
        return self.scoring_methods[assessment_id](responses, demographics)
    
    # ========================================================================
    # Screening Tools
    # ========================================================================
    
    def score_phq9(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score PHQ-9 (Patient Health Questionnaire - Depression).
        
        Items 1-9: Each scored 0-3
        Total: 0-27
        """
        # Calculate total score
        total_score = sum(responses.values())
        
        # Item 9 is suicide risk (needs special attention)
        suicide_risk_score = responses.get(9, 0)
        
        # Determine severity
        if total_score < 5:
            severity = "None-Minimal"
            clinical_sig = "none"
            recommendations = ["Monitor if symptoms worsen"]
        elif total_score < 10:
            severity = "Mild"
            clinical_sig = "mild"
            recommendations = [
                "Watchful waiting",
                "Consider psychotherapy if symptoms persist",
                "Lifestyle modifications"
            ]
        elif total_score < 15:
            severity = "Moderate"
            clinical_sig = "moderate"
            recommendations = [
                "Psychotherapy recommended",
                "Consider medication evaluation",
                "Regular monitoring (every 2 weeks)"
            ]
        elif total_score < 20:
            severity = "Moderately Severe"
            clinical_sig = "severe"
            recommendations = [
                "Active treatment warranted",
                "Psychotherapy AND/OR medication",
                "Close monitoring (weekly)",
                "Consider psychiatric consultation"
            ]
        else:
            severity = "Severe"
            clinical_sig = "severe"
            recommendations = [
                "Immediate treatment required",
                "Psychiatric consultation recommended",
                "Consider intensive outpatient or inpatient care",
                "Weekly monitoring minimum"
            ]
        
        # Add suicide risk recommendations
        if suicide_risk_score > 0:
            recommendations.insert(0, "⚠️ SUICIDE RISK DETECTED - Conduct thorough risk assessment")
        
        interpretation = f"""
        PHQ-9 Score: {total_score}/27 - {severity}
        
        The client's responses indicate {severity.lower()} depression symptoms.
        """
        
        if suicide_risk_score > 0:
            interpretation += f"\n\n⚠️ ALERT: Client endorsed suicidal thoughts (Item 9 = {suicide_risk_score}). "
            interpretation += "Immediate safety assessment required."
        
        return AssessmentScore(
            assessment_id='phq9',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_gad7(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score GAD-7 (Generalized Anxiety Disorder).
        
        Items 1-7: Each scored 0-3
        Total: 0-21
        """
        total_score = sum(responses.values())
        
        # Determine severity
        if total_score < 5:
            severity = "Minimal"
            clinical_sig = "none"
            recommendations = ["No treatment needed", "Monitor if symptoms worsen"]
        elif total_score < 10:
            severity = "Mild"
            clinical_sig = "mild"
            recommendations = [
                "Psychoeducation about anxiety",
                "Self-help resources",
                "Consider brief counseling"
            ]
        elif total_score < 15:
            severity = "Moderate"
            clinical_sig = "moderate"
            recommendations = [
                "Probable anxiety disorder - treatment recommended",
                "Cognitive-behavioral therapy (CBT)",
                "Consider medication evaluation",
                "Regular monitoring"
            ]
        else:
            severity = "Severe"
            clinical_sig = "severe"
            recommendations = [
                "Active treatment required",
                "CBT and/or medication",
                "Consider psychiatric consultation",
                "Weekly monitoring"
            ]
        
        interpretation = f"""
        GAD-7 Score: {total_score}/21 - {severity} Anxiety
        
        Diagnostic utility: Score ≥10 has 89% sensitivity and 82% specificity for GAD.
        Also screens for panic disorder, social anxiety, and PTSD.
        """
        
        return AssessmentScore(
            assessment_id='gad7',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_dass21(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score DASS-21 (Depression, Anxiety, Stress Scale).
        
        Three subscales of 7 items each.
        Scores are multiplied by 2 to match DASS-42.
        """
        # Subscale item assignments
        depression_items = [3, 5, 10, 13, 16, 17, 21]
        anxiety_items = [2, 4, 7, 9, 15, 19, 20]
        stress_items = [1, 6, 8, 11, 12, 14, 18]
        
        # Calculate subscale scores
        depression = sum(responses.get(i, 0) for i in depression_items) * 2
        anxiety = sum(responses.get(i, 0) for i in anxiety_items) * 2
        stress = sum(responses.get(i, 0) for i in stress_items) * 2
        
        total_score = depression + anxiety + stress
        
        # Severity interpretation
        def interpret_depression(score):
            if score < 10: return "Normal"
            elif score < 14: return "Mild"
            elif score < 21: return "Moderate"
            elif score < 28: return "Severe"
            else: return "Extremely Severe"
        
        def interpret_anxiety(score):
            if score < 8: return "Normal"
            elif score < 10: return "Mild"
            elif score < 15: return "Moderate"
            elif score < 20: return "Severe"
            else: return "Extremely Severe"
        
        def interpret_stress(score):
            if score < 15: return "Normal"
            elif score < 19: return "Mild"
            elif score < 26: return "Moderate"
            elif score < 34: return "Severe"
            else: return "Extremely Severe"
        
        dep_level = interpret_depression(depression)
        anx_level = interpret_anxiety(anxiety)
        str_level = interpret_stress(stress)
        
        # Overall severity (highest subscale)
        max_subscale = max(depression, anxiety, stress)
        if max_subscale >= 28:
            overall_severity = "Severe"
            clinical_sig = "severe"
        elif max_subscale >= 20:
            overall_severity = "Moderate"
            clinical_sig = "moderate"
        elif max_subscale >= 10:
            overall_severity = "Mild"
            clinical_sig = "mild"
        else:
            overall_severity = "Normal"
            clinical_sig = "none"
        
        recommendations = []
        if dep_level != "Normal":
            recommendations.append(f"Address depression symptoms ({dep_level})")
        if anx_level != "Normal":
            recommendations.append(f"Address anxiety symptoms ({anx_level})")
        if str_level != "Normal":
            recommendations.append(f"Address stress symptoms ({str_level})")
        
        if not recommendations:
            recommendations = ["No clinical intervention required at this time"]
        
        interpretation = f"""
        DASS-21 Results:
        • Depression: {depression}/42 ({dep_level})
        • Anxiety: {anxiety}/42 ({anx_level})
        • Stress: {stress}/42 ({str_level})
        
        Overall: {overall_severity} emotional distress across domains.
        """
        
        return AssessmentScore(
            assessment_id='dass21',
            total_score=float(total_score),
            subscale_scores={
                'depression': float(depression),
                'anxiety': float(anxiety),
                'stress': float(stress)
            },
            percentile=None,
            severity_level=overall_severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_audit(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score AUDIT (Alcohol Use Disorders Identification Test).
        
        10 items: Items 1-8 scored 0-4, Items 9-10 scored 0,2,4
        Total: 0-40
        """
        # Items 1-8: Standard 0-4 scoring
        standard_items = sum(responses.get(i, 0) for i in range(1, 9))
        
        # Items 9-10: Special scoring (0, 2, 4 only)
        special_items = sum(responses.get(i, 0) for i in [9, 10])
        
        total_score = standard_items + special_items
        
        # Interpretation
        if total_score < 8:
            severity = "Low Risk"
            clinical_sig = "none"
            recommendations = [
                "No intervention needed",
                "Provide alcohol education materials"
            ]
        elif total_score < 16:
            severity = "Hazardous Drinking"
            clinical_sig = "moderate"
            recommendations = [
                "Brief intervention recommended",
                "Provide feedback about risks",
                "Motivational enhancement therapy",
                "Reassess in 3 months"
            ]
        elif total_score < 20:
            severity = "Harmful Drinking"
            clinical_sig = "severe"
            recommendations = [
                "Brief intervention + counseling",
                "Consider outpatient treatment program",
                "Monitor closely",
                "Assess for alcohol dependence"
            ]
        else:
            severity = "Alcohol Dependence"
            clinical_sig = "severe"
            recommendations = [
                "Comprehensive assessment needed",
                "Refer to addiction specialist",
                "Consider intensive outpatient or inpatient treatment",
                "Medical evaluation for withdrawal management",
                "Support group referral (AA, SMART Recovery)"
            ]
        
        interpretation = f"""
        AUDIT Score: {total_score}/40 - {severity}
        
        Interpretation:
        • Scores ≥8: Hazardous/harmful alcohol use
        • Scores ≥16: High likelihood of alcohol dependence
        • Scores ≥20: Probable alcohol dependence
        
        Consider conducting a more comprehensive substance use evaluation.
        """
        
        return AssessmentScore(
            assessment_id='audit',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_ace(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score ACE (Adverse Childhood Experiences).
        
        10 yes/no questions
        Score: Number of "yes" responses (0-10)
        """
        # Count yes responses (assuming yes=1, no=0)
        total_score = sum(1 for v in responses.values() if v == 1)
        
        # Interpretation
        if total_score == 0:
            severity = "No ACEs"
            clinical_sig = "none"
            recommendations = ["No specific trauma-informed interventions needed"]
        elif total_score <= 3:
            severity = "Moderate ACE Exposure"
            clinical_sig = "mild"
            recommendations = [
                "Acknowledge ACE history in treatment planning",
                "Consider trauma-informed care approach",
                "Assess current impact of early experiences"
            ]
        else:
            severity = "High ACE Exposure"
            clinical_sig = "severe"
            recommendations = [
                "High priority for trauma-informed care",
                "Consider trauma-focused therapy (EMDR, TF-CBT)",
                "Assess for complex trauma/PTSD",
                "Build safety and stabilization first",
                "Screen for dissociation"
            ]
        
        interpretation = f"""
        ACE Score: {total_score}/10 - {severity}
        
        Research indicates:
        • ACE Score ≥4: Significantly increased risk for:
          - Depression, anxiety, PTSD
          - Substance use disorders
          - Chronic health conditions
          - Interpersonal difficulties
        
        • ACE Score ≥6: Average lifespan reduced by 20 years
        
        Important: ACE score represents risk, not destiny. Resilience factors
        and therapeutic intervention can mitigate adverse effects.
        """
        
        return AssessmentScore(
            assessment_id='ace',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    # ========================================================================
    # Behavioral & Emotional Assessments
    # ========================================================================
    
    def score_bdi(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score BDI-II (Beck Depression Inventory).
        
        21 items, each scored 0-3
        Total: 0-63
        """
        total_score = sum(responses.values())
        
        if total_score < 14:
            severity = "Minimal"
            clinical_sig = "none"
            recommendations = ["No treatment indicated", "Monitor symptoms"]
        elif total_score < 20:
            severity = "Mild"
            clinical_sig = "mild"
            recommendations = [
                "Psychotherapy may be beneficial",
                "Self-help interventions",
                "Reassess in 2-4 weeks"
            ]
        elif total_score < 29:
            severity = "Moderate"
            clinical_sig = "moderate"
            recommendations = [
                "Psychotherapy recommended",
                "Consider medication evaluation",
                "Regular monitoring"
            ]
        else:
            severity = "Severe"
            clinical_sig = "severe"
            recommendations = [
                "Immediate treatment needed",
                "Psychotherapy AND medication likely needed",
                "Risk assessment for self-harm",
                "Consider intensive treatment"
            ]
        
        interpretation = f"BDI-II Score: {total_score}/63 - {severity} Depression"
        
        return AssessmentScore(
            assessment_id='bdi',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=severity,
            interpretation=interpretation,
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_stai(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score STAI (State-Trait Anxiety Inventory).
        
        Two scales: State (20 items) and Trait (20 items)
        Each scored 1-4
        """
        # Assuming items 1-20 are State, 21-40 are Trait
        state_items = list(range(1, 21))
        trait_items = list(range(21, 41))
        
        state_score = sum(responses.get(i, 0) for i in state_items)
        trait_score = sum(responses.get(i, 0) for i in trait_items)
        
        total_score = state_score + trait_score
        
        def interpret_score(score, scale_name):
            if score < 40:
                return f"{scale_name}: Low anxiety"
            elif score < 60:
                return f"{scale_name}: Moderate anxiety"
            else:
                return f"{scale_name}: High anxiety"
        
        state_interp = interpret_score(state_score, "State")
        trait_interp = interpret_score(trait_score, "Trait")
        
        if state_score >= 60 or trait_score >= 60:
            severity = "High Anxiety"
            clinical_sig = "severe"
            recommendations = [
                "Anxiety treatment recommended",
                "CBT or other evidence-based therapy",
                "Consider medication evaluation"
            ]
        elif state_score >= 40 or trait_score >= 40:
            severity = "Moderate Anxiety"
            clinical_sig = "moderate"
            recommendations = [
                "Monitor anxiety symptoms",
                "Stress management techniques",
                "Consider brief counseling"
            ]
        else:
            severity = "Low Anxiety"
            clinical_sig = "none"
            recommendations = ["No intervention needed"]
        
        interpretation = f"""
        STAI Results:
        • {state_interp} (Current anxiety: {state_score}/80)
        • {trait_interp} (General anxiety tendency: {trait_score}/80)
        """
        
        return AssessmentScore(
            assessment_id='stai',
            total_score=float(total_score),
            subscale_scores={
                'state_anxiety': float(state_score),
                'trait_anxiety': float(trait_score)
            },
            percentile=None,
            severity_level=severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    # ========================================================================
    # Trauma & Stress Tools
    # ========================================================================
    
    def score_pcl5(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """
        Score PCL-5 (PTSD Checklist for DSM-5).
        
        20 items, each scored 0-4
        Total: 0-80
        """
        # DSM-5 clusters
        cluster_b = [1, 2, 3, 4, 5]  # Intrusion
        cluster_c = [6, 7]  # Avoidance
        cluster_d = [8, 9, 10, 11, 12, 13, 14]  # Negative alterations
        cluster_e = [15, 16, 17, 18, 19, 20]  # Arousal/reactivity
        
        total_score = sum(responses.values())
        
        b_score = sum(responses.get(i, 0) for i in cluster_b)
        c_score = sum(responses.get(i, 0) for i in cluster_c)
        d_score = sum(responses.get(i, 0) for i in cluster_d)
        e_score = sum(responses.get(i, 0) for i in cluster_e)
        
        # Provisional PTSD diagnosis (DSM-5 criteria)
        criterion_b = any(responses.get(i, 0) >= 2 for i in cluster_b)
        criterion_c = any(responses.get(i, 0) >= 2 for i in cluster_c)
        criterion_d = sum(1 for i in cluster_d if responses.get(i, 0) >= 2) >= 2
        criterion_e = sum(1 for i in cluster_e if responses.get(i, 0) >= 2) >= 2
        
        meets_criteria = all([criterion_b, criterion_c, criterion_d, criterion_e])
        
        if total_score < 31:
            severity = "Below Cutoff"
            clinical_sig = "none" if total_score < 10 else "mild"
        elif total_score < 45:
            severity = "Probable PTSD"
            clinical_sig = "moderate"
        else:
            severity = "Severe PTSD Symptoms"
            clinical_sig = "severe"
        
        recommendations = []
        if meets_criteria or total_score >= 31:
            recommendations = [
                "Comprehensive PTSD assessment recommended",
                "Evidence-based trauma therapy (PE, CPT, EMDR)",
                "Consider medication consultation",
                "Safety and stabilization assessment"
            ]
        elif total_score >= 10:
            recommendations = [
                "Monitor trauma symptoms",
                "Psychoeducation about trauma",
                "Consider brief trauma-focused intervention"
            ]
        else:
            recommendations = ["No PTSD treatment indicated"]
        
        interpretation = f"""
        PCL-5 Score: {total_score}/80 - {severity}
        
        DSM-5 Cluster Scores:
        • Intrusion (B): {b_score}/20
        • Avoidance (C): {c_score}/8
        • Negative Alterations (D): {d_score}/28
        • Arousal/Reactivity (E): {e_score}/24
        
        Provisional PTSD: {"YES" if meets_criteria else "NO"}
        (Score ≥31-33 suggests probable PTSD)
        """
        
        return AssessmentScore(
            assessment_id='pcl5',
            total_score=float(total_score),
            subscale_scores={
                'intrusion': float(b_score),
                'avoidance': float(c_score),
                'negative_alterations': float(d_score),
                'arousal_reactivity': float(e_score)
            },
            percentile=None,
            severity_level=severity,
            interpretation=interpretation.strip(),
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    # ========================================================================
    # Specialized Tools
    # ========================================================================
    
    def score_eq(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """Score EQ (Empathy Quotient)."""
        # Simplified scoring
        total_score = sum(responses.values())
        
        if total_score < 30:
            level = "Low Empathy"
            recommendations = ["May benefit from social skills training"]
        elif total_score < 52:
            level = "Average Empathy"
            recommendations = ["Empathy within normal range"]
        else:
            level = "High Empathy"
            recommendations = ["Above average empathy"]
        
        return AssessmentScore(
            assessment_id='eq',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=level,
            interpretation=f"EQ Score: {total_score}/80 - {level}",
            clinical_significance="none",
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_iat(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """Score IAT (Internet Addiction Test)."""
        total_score = sum(responses.values())
        
        if total_score < 40:
            severity = "Average Online User"
            clinical_sig = "none"
            recommendations = ["No intervention needed"]
        elif total_score < 70:
            severity = "Frequent Problems"
            clinical_sig = "moderate"
            recommendations = [
                "Consider reducing internet use",
                "Set boundaries and schedules",
                "Brief counseling may help"
            ]
        else:
            severity = "Significant Problems"
            clinical_sig = "severe"
            recommendations = [
                "Internet use causing significant impairment",
                "Specialized treatment recommended",
                "CBT for internet addiction"
            ]
        
        return AssessmentScore(
            assessment_id='iat',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level=severity,
            interpretation=f"IAT Score: {total_score}/100 - {severity}",
            clinical_significance=clinical_sig,
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )
    
    # Placeholder methods for complex assessments
    def score_mmpi2(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """MMPI-2 scoring (complex, requires specialized software)."""
        return AssessmentScore(
            assessment_id='mmpi2',
            total_score=0.0,
            subscale_scores={},
            percentile=None,
            severity_level="Requires Professional Scoring",
            interpretation="MMPI-2 requires specialized scoring software and professional interpretation.",
            clinical_significance="unknown",
            recommendations=["Refer to qualified psychologist for MMPI-2 interpretation"],
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_cbcl(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """CBCL scoring placeholder."""
        return AssessmentScore(
            assessment_id='cbcl',
            total_score=0.0,
            subscale_scores={},
            percentile=None,
            severity_level="Requires Professional Scoring",
            interpretation="CBCL requires specialized scoring and age/gender norms.",
            clinical_significance="unknown",
            recommendations=["Professional scoring required"],
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_msi(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """MSI (Marital Satisfaction Inventory) placeholder."""
        total_score = sum(responses.values())
        return AssessmentScore(
            assessment_id='msi',
            total_score=float(total_score),
            subscale_scores={},
            percentile=None,
            severity_level="Variable",
            interpretation="MSI assesses relationship satisfaction across multiple domains.",
            clinical_significance="moderate",
            recommendations=["Couples therapy may be beneficial"],
            scored_at=datetime.utcnow().isoformat()
        )
    
    def score_pcq(self, responses: Dict, demographics: Dict = None) -> AssessmentScore:
        """PCQ (Psychological Capital) scoring."""
        # 4 subscales: Hope, Efficacy, Resilience, Optimism (6 items each)
        hope = sum(responses.get(i, 0) for i in range(1, 7))
        efficacy = sum(responses.get(i, 0) for i in range(7, 13))
        resilience = sum(responses.get(i, 0) for i in range(13, 19))
        optimism = sum(responses.get(i, 0) for i in range(19, 25))
        
        total_score = hope + efficacy + resilience + optimism
        
        if total_score < 72:
            level = "Low PsyCap"
            recommendations = ["May benefit from resilience-building interventions"]
        elif total_score < 108:
            level = "Moderate PsyCap"
            recommendations = ["Average psychological capital"]
        else:
            level = "High PsyCap"
            recommendations = ["Strong psychological resources"]
        
        return AssessmentScore(
            assessment_id='pcq',
            total_score=float(total_score),
            subscale_scores={
                'hope': float(hope),
                'efficacy': float(efficacy),
                'resilience': float(resilience),
                'optimism': float(optimism)
            },
            percentile=None,
            severity_level=level,
            interpretation=f"PCQ Score: {total_score}/144 - {level}",
            clinical_significance="none",
            recommendations=recommendations,
            scored_at=datetime.utcnow().isoformat()
        )


# Example usage
if __name__ == "__main__":
    print("Assessment Scoring Engine Demo")
    print("=" * 60)
    
    scorer = ScoringEngine()
    
    # Example: PHQ-9 responses
    phq9_responses = {
        1: 2,  # Little interest or pleasure
        2: 2,  # Feeling down, depressed
        3: 1,  # Sleep problems
        4: 2,  # Feeling tired
        5: 1,  # Poor appetite
        6: 1,  # Feeling bad about self
        7: 1,  # Trouble concentrating
        8: 0,  # Moving slowly
        9: 0   # Thoughts of self-harm
    }
    
    result = scorer.score_phq9(phq9_responses)
    
    print("\nPHQ-9 Scoring Results:")
    print(f"Total Score: {result.total_score}/27")
    print(f"Severity: {result.severity_level}")
    print(f"Clinical Significance: {result.clinical_significance}")
    print(f"\nInterpretation:\n{result.interpretation}")
    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")