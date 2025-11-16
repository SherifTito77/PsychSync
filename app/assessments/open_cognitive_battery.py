
#app/assessments/open_cognitive_battery.py
"""
Open Cognitive Assessment Battery (OCAB) - Free Alternative to WAIS-IV
Brief cognitive screening assessing multiple cognitive domains.

File: app/assessments/open_cognitive_battery.py

Domains: Working Memory, Processing Speed, Verbal Reasoning, Visual-Spatial
Note: This is a SCREENING tool, not a full IQ test. For comprehensive 
cognitive assessment, refer to licensed neuropsychologist.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OCABScore:
    """Open Cognitive Assessment Battery Score Result."""
    domain_scores: Dict[str, int]
    domain_percentiles: Dict[str, int]
    composite_score: int
    estimated_ability_level: str
    strengths: List[str]
    weaknesses: List[str]
    interpretation: str
    recommendations: List[str]
    validity: str
    scored_at: str


class OpenCognitiveAssessmentBattery:
    """
    Open Cognitive Assessment Battery - Brief cognitive screening.
    Free, open-source alternative for cognitive screening.
    
    ⚠️ IMPORTANT: This is a SCREENING tool only. Not a replacement
    for comprehensive cognitive/IQ testing by qualified professionals.
    """
    
    def __init__(self):
        """Initialize OCAB."""
        # Domain definitions
        self.domains = {
            'working_memory': {
                'description': 'Ability to hold and manipulate information',
                'tasks': ['digit_span', 'letter_number'],
                'max_score': 20
            },
            'processing_speed': {
                'description': 'Speed of mental processing',
                'tasks': ['symbol_coding', 'cancellation'],
                'max_score': 20
            },
            'verbal_reasoning': {
                'description': 'Verbal comprehension and reasoning',
                'tasks': ['similarities', 'vocabulary'],
                'max_score': 20
            },
            'visual_spatial': {
                'description': 'Visual-spatial processing',
                'tasks': ['block_design', 'matrix_reasoning'],
                'max_score': 20
            }
        }
        
        # Normative percentiles (simplified)
        self.percentile_table = [
            (2, 1), (4, 5), (6, 10), (8, 16), (10, 25),
            (12, 50), (14, 75), (16, 84), (18, 95), (20, 99)
        ]
    
    def score_ocab(
        self,
        task_scores: Dict[str, int],
        age: int,
        education_years: int = 12,
        effort_valid: bool = True
    ) -> OCABScore:
        """
        Score the Open Cognitive Assessment Battery.
        
        Args:
            task_scores: Dictionary of task_name -> raw_score
            age: Participant age
            education_years: Years of education
            effort_valid: Whether effort testing indicates valid performance
            
        Returns:
            OCABScore with domain scores and interpretation
        """
        # Calculate domain scores
        domain_scores = {}
        domain_percentiles = {}
        
        domain_scores['working_memory'] = (
            task_scores.get('digit_span', 0) +
            task_scores.get('letter_number', 0)
        )
        
        domain_scores['processing_speed'] = (
            task_scores.get('symbol_coding', 0) +
            task_scores.get('cancellation', 0)
        )
        
        domain_scores['verbal_reasoning'] = (
            task_scores.get('similarities', 0) +
            task_scores.get('vocabulary', 0)
        )
        
        domain_scores['visual_spatial'] = (
            task_scores.get('block_design', 0) +
            task_scores.get('matrix_reasoning', 0)
        )
        
        # Convert to percentiles
        for domain, score in domain_scores.items():
            domain_percentiles[domain] = self._score_to_percentile(score)
        
        # Calculate composite (average of domains)
        composite_score = int(np.mean(list(domain_scores.values())))
        composite_percentile = self._score_to_percentile(composite_score)
        
        # Determine ability level
        ability_level = self._classify_ability(composite_percentile)
        
        # Identify strengths and weaknesses
        strengths, weaknesses = self._identify_profile(domain_percentiles)
        
        # Validity check
        validity = "Valid" if effort_valid else "Questionable - Poor Effort"
        
        # Generate interpretation
        interpretation = self._generate_interpretation(
            domain_scores,
            domain_percentiles,
            composite_percentile,
            ability_level,
            age,
            validity
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            domain_percentiles,
            weaknesses,
            validity
        )
        
        return OCABScore(
            domain_scores=domain_scores,
            domain_percentiles=domain_percentiles,
            composite_score=composite_score,
            estimated_ability_level=ability_level,
            strengths=strengths,
            weaknesses=weaknesses,
            interpretation=interpretation,
            recommendations=recommendations,
            validity=validity,
            scored_at=datetime.utcnow().isoformat()
        )
    
    def _score_to_percentile(self, score: int) -> int:
        """Convert raw score to percentile."""
        for threshold, percentile in self.percentile_table:
            if score <= threshold:
                return percentile
        return 99
    
    def _classify_ability(self, percentile: int) -> str:
        """Classify cognitive ability level."""
        if percentile >= 98:
            return "Very Superior"
        elif percentile >= 91:
            return "Superior"
        elif percentile >= 75:
            return "High Average"
        elif percentile >= 25:
            return "Average"
        elif percentile >= 9:
            return "Low Average"
        elif percentile >= 2:
            return "Borderline"
        else:
            return "Extremely Low"
    
    def _identify_profile(self, domain_percentiles: Dict) -> Tuple[List[str], List[str]]:
        """Identify cognitive strengths and weaknesses."""
        strengths = []
        weaknesses = []
        
        for domain, percentile in domain_percentiles.items():
            if percentile >= 75:
                strengths.append(domain.replace('_', ' ').title())
            elif percentile <= 25:
                weaknesses.append(domain.replace('_', ' ').title())
        
        return strengths, weaknesses
    
    def _generate_interpretation(
        self,
        domain_scores: Dict,
        domain_percentiles: Dict,
        composite_percentile: int,
        ability_level: str,
        age: int,
        validity: str
    ) -> str:
        """Generate narrative interpretation."""
        interp = "Open Cognitive Assessment Battery Results\n\n"
        
        if validity != "Valid":
            interp += f"⚠️ VALIDITY CONCERN: {validity}\n"
            interp += "Results should be interpreted with caution.\n\n"
        
        interp += f"Overall Cognitive Ability: {ability_level} ({composite_percentile}th percentile)\n\n"
        
        interp += "DOMAIN SCORES:\n"
        for domain, score in domain_scores.items():
            percentile = domain_percentiles[domain]
            max_score = self.domains[domain]['max_score']
            interp += f"  {domain.replace('_', ' ').title()}: {score}/{max_score} ({percentile}th percentile)\n"
        
        interp += "\n⚠️ IMPORTANT DISCLAIMER:\n"
        interp += "This is a brief cognitive SCREENING tool, not a comprehensive IQ test.\n"
        interp += "For diagnostic purposes or comprehensive assessment, refer to licensed\n"
        interp += "neuropsychologist for full battery (WAIS-IV, WISC-V, etc.).\n"
        
        return interp
    
    def _generate_recommendations(
        self,
        domain_percentiles: Dict,
        weaknesses: List[str],
        validity: str
    ) -> List[str]:
        """Generate recommendations."""
        recs = []
        
        if validity != "Valid":
            recs.append("⚠️ Re-test recommended due to validity concerns")
            recs.append("Ensure adequate sleep, motivation, and test-taking conditions")
            return recs
        
        # Domain-specific recommendations
        if domain_percentiles.get('working_memory', 50) <= 25:
            recs.append("Working memory deficits noted - consider strategies:")
            recs.append("  • Use external aids (calendars, reminders, notes)")
            recs.append("  • Break tasks into smaller steps")
            recs.append("  • Cognitive training exercises may help")
        
        if domain_percentiles.get('processing_speed', 50) <= 25:
            recs.append("Slow processing speed noted - accommodations:")
            recs.append("  • Extended time for tests/tasks")
            recs.append("  • Reduce timed pressures")
            recs.append("  • Allow frequent breaks")
        
        if domain_percentiles.get('verbal_reasoning', 50) <= 25:
            recs.append("Verbal reasoning challenges - supports:")
            recs.append("  • Visual aids and diagrams")
            recs.append("  • Simplified language")
            recs.append("  • Speech-language evaluation may be beneficial")
        
        if domain_percentiles.get('visual_spatial', 50) <= 25:
            recs.append("Visual-spatial difficulties - strategies:")
            recs.append("  • Use verbal descriptions alongside visuals")
            recs.append("  • Organize materials systematically")
            recs.append("  • Occupational therapy evaluation may help")
        
        # General recommendations
        if any(p <= 16 for p in domain_percentiles.values()):
            recs.append("⚠️ Significant cognitive concerns identified")
            recs.append("STRONGLY RECOMMEND: Comprehensive neuropsychological evaluation")
        
        if not recs:
            recs.append("Cognitive functioning within normal limits")
            recs.append("No specific interventions indicated")
        
        return recs


# Task descriptions for OCAB
def get_ocab_tasks() -> Dict:
    """Get descriptions of OCAB tasks."""
    return {
        "digit_span": {
            "name": "Digit Span",
            "domain": "Working Memory",
            "description": "Repeat sequences of numbers forward and backward",
            "administration": "Auditory presentation, verbal response",
            "scoring": "Longest sequence correctly repeated (max 10 points)"
        },
        "letter_number": {
            "name": "Letter-Number Sequencing",
            "domain": "Working Memory",
            "description": "Reorder mixed letters and numbers",
            "administration": "Auditory presentation, verbal response",
            "scoring": "Correct sequences (max 10 points)"
        },
        "symbol_coding": {
            "name": "Symbol Coding",
            "domain": "Processing Speed",
            "description": "Match symbols to numbers as quickly as possible",
            "administration": "Paper-and-pencil or digital, 90 seconds",
            "scoring": "Number correct in time limit (max 10 points)"
        },
        "cancellation": {
            "name": "Symbol Cancellation",
            "domain": "Processing Speed",
            "description": "Cross out target symbols among distractors",
            "administration": "Paper-and-pencil or digital, 60 seconds",
            "scoring": "Targets found minus errors (max 10 points)"
        },
        "similarities": {
            "name": "Similarities",
            "domain": "Verbal Reasoning",
            "description": "Explain how two things are alike",
            "administration": "Verbal question, verbal response",
            "scoring": "Quality of conceptual reasoning (max 10 points)"
        },
        "vocabulary": {
            "name": "Vocabulary",
            "domain": "Verbal Reasoning",
            "description": "Define words of increasing difficulty",
            "administration": "Verbal or written presentation",
            "scoring": "Accuracy of definitions (max 10 points)"
        },
        "block_design": {
            "name": "Block Design",
            "domain": "Visual-Spatial",
            "description": "Recreate patterns using colored blocks",
            "administration": "Physical blocks or digital simulation",
            "scoring": "Accuracy and speed (max 10 points)"
        },
        "matrix_reasoning": {
            "name": "Matrix Reasoning",
            "domain": "Visual-Spatial",
            "description": "Complete visual patterns/matrices",
            "administration": "Visual presentation, pointing or verbal response",
            "scoring": "Correct solutions (max 10 points)"
        }
    }


# Example usage
if __name__ == "__main__":
    print("Open Cognitive Assessment Battery (OCAB) Demo")
    print("=" * 60)
    
    ocab = OpenCognitiveAssessmentBattery()
    
    # Simulate task scores (normal performance)
    sample_scores = {
        'digit_span': 8,
        'letter_number': 7,
        'symbol_coding': 9,
        'cancellation': 8,
        'similarities': 9,
        'vocabulary': 10,
        'block_design': 7,
        'matrix_reasoning': 8
    }
    
    # Score
    result = ocab.score_ocab(
        task_scores=sample_scores,
        age=35,
        education_years=16,
        effort_valid=True
    )
    
    print("\nDomain Scores:")
    for domain, score in result.domain_scores.items():
        percentile = result.domain_percentiles[domain]
        print(f"  {domain.replace('_', ' ').title()}: {score}/20 ({percentile}th percentile)")
    
    print(f"\nComposite Score: {result.composite_score}/20")
    print(f"Estimated Ability: {result.estimated_ability_level}")
    print(f"Validity: {result.validity}")
    
    if result.strengths:
        print(f"\nStrengths: {', '.join(result.strengths)}")
    
    if result.weaknesses:
        print(f"Weaknesses: {', '.join(result.weaknesses)}")
    
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"  {rec}")
    
    print("\n" + "=" * 60)
    print("⚠️ DISCLAIMER: This is a screening tool only.")
    print("For comprehensive cognitive assessment, consult a licensed psychologist.")