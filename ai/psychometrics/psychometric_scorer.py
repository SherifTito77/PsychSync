
# ============================================================================
# FILE 6: /ai/psychometrics/psychometric_scorer.py
# Score and validate psychometric assessments
# ============================================================================

from typing import Dict, List, Optional
import numpy as np
from datetime import datetime

class PsychometricScorer:
    """Score and validate psychometric assessments"""
    
    def __init__(self):
        self.scoring_methods = {
            "big_five": self._score_big_five,
            "mbti": self._score_mbti,
            "enneagram": self._score_enneagram,
            "disc": self._score_disc
        }
    
    def score_assessment(
        self,
        assessment_type: str,
        responses: List[Dict],
        framework_config: Dict
    ) -> Dict:
        """
        Score an assessment based on type and responses
        
        Args:
            assessment_type: Type of assessment (big_five, mbti, etc.)
            responses: List of question-answer pairs
            framework_config: Configuration for scoring
            
        Returns:
            Scored results with interpretation
        """
        if assessment_type not in self.scoring_methods:
            raise ValueError(f"Unknown assessment type: {assessment_type}")
        
        # Validate responses
        validation = self._validate_responses(responses, framework_config)
        if not validation["valid"]:
            return {"error": "Invalid responses", "details": validation["errors"]}
        
        # Score using appropriate method
        scores = self.scoring_methods[assessment_type](responses, framework_config)
        
        # Add metadata
        scores["metadata"] = {
            "assessment_type": assessment_type,
            "completed_at": datetime.utcnow().isoformat(),
            "response_count": len(responses),
            "completion_time_seconds": self._calculate_completion_time(responses)
        }
        
        return scores
    
    def _score_big_five(self, responses: List[Dict], config: Dict) -> Dict:
        """Score Big Five personality assessment"""
        dimensions = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        scores = {dim: [] for dim in dimensions}
        
        # Map responses to dimensions
        for response in responses:
            question_id = response["question_id"]
            answer_value = response["answer_value"]
            
            # Get dimension and reverse scoring flag
            dimension = config["questions"][question_id]["dimension"]
            reverse_score = config["questions"][question_id].get("reverse_score", False)
            
            # Apply reverse scoring if needed
            if reverse_score:
                answer_value = config["max_value"] - answer_value + config["min_value"]
            
            scores[dimension].append(answer_value)
        
        # Calculate dimension scores (normalized 0-1)
        results = {}
        for dimension, values in scores.items():
            if values:
                raw_score = np.mean(values)
                normalized = (raw_score - config["min_value"]) / (config["max_value"] - config["min_value"])
                results[dimension] = {
                    "score": float(normalized),
                    "percentile": self._score_to_percentile(normalized),
                    "interpretation": self._interpret_big_five_score(dimension, normalized)
                }
        
        return {"dimensions": results, "type": "big_five"}
    
    def _score_mbti(self, responses: List[Dict], config: Dict) -> Dict:
        """Score MBTI assessment"""
        dimensions = {
            "E_I": {"E": 0, "I": 0},  # Extraversion vs Introversion
            "S_N": {"S": 0, "N": 0},  # Sensing vs Intuition
            "T_F": {"T": 0, "F": 0},  # Thinking vs Feeling
            "J_P": {"J": 0, "P": 0}   # Judging vs Perceiving
        }
        
        for response in responses:
            question_id = response["question_id"]
            answer = response["answer_value"]
            
            dimension = config["questions"][question_id]["dimension"]
            preference = config["questions"][question_id]["preference"]
            
            dimensions[dimension][preference] += answer
        
        # Determine type
        mbti_type = ""
        preferences = {}
        
        for dimension, scores in dimensions.items():
            options = list(scores.keys())
            if scores[options[0]] > scores[options[1]]:
                mbti_type += options[0]
                preference = options[0]
                strength = scores[options[0]] / (scores[options[0]] + scores[options[1]])
            else:
                mbti_type += options[1]
                preference = options[1]
                strength = scores[options[1]] / (scores[options[0]] + scores[options[1]])
            
            preferences[dimension] = {
                "preference": preference,
                "strength": float(strength),
                "clarity": "clear" if strength > 0.65 else "moderate" if strength > 0.55 else "slight"
            }
        
        return {
            "type": mbti_type,
            "preferences": preferences,
            "description": self._get_mbti_description(mbti_type)
        }
    
    def _score_enneagram(self, responses: List[Dict], config: Dict) -> Dict:
        """Score Enneagram assessment"""
        type_scores = {i: 0 for i in range(1, 10)}
        
        for response in responses:
            question_id = response["question_id"]
            answer_value = response["answer_value"]
            
            # Each question may map to multiple types with weights
            type_mappings = config["questions"][question_id]["types"]
            
            for enneagram_type, weight in type_mappings.items():
                type_scores[int(enneagram_type)] += answer_value * weight
        
        # Normalize scores
        max_score = max(type_scores.values())
        normalized_scores = {k: v/max_score for k, v in type_scores.items()}
        
        # Get primary type and wing
        primary_type = max(type_scores, key=type_scores.get)
        
        # Determine wing (adjacent type with highest score)
        adjacent = [(primary_type - 1) if primary_type > 1 else 9, 
                    (primary_type + 1) if primary_type < 9 else 1]
        wing = max(adjacent, key=lambda x: type_scores[x])
        
        return {
            "primary_type": primary_type,
            "wing": wing,
            "type_string": f"{primary_type}w{wing}",
            "scores": {str(k): float(v) for k, v in normalized_scores.items()},
            "description": self._get_enneagram_description(primary_type)
        }
    
    def _score_disc(self, responses: List[Dict], config: Dict) -> Dict:
        """Score DISC assessment"""
        dimensions = {"D": 0, "I": 0, "S": 0, "C": 0}
        
        for response in responses:
            question_id = response["question_id"]
            
            # DISC typically uses ranking
            rankings = response["rankings"]  # e.g., {"D": 1, "I": 3, "S": 2, "C": 4}
            
            # Convert rankings to scores (lower rank = higher score)
            for dimension, rank in rankings.items():
                dimensions[dimension] += (5 - rank)  # Invert ranking
        
        # Normalize
        total = sum(dimensions.values())
        normalized = {k: (v/total)*100 for k, v in dimensions.items()}
        
        # Determine primary and secondary styles
        sorted_dims = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "dimensions": {k: float(v) for k, v in normalized.items()},
            "primary_style": sorted_dims[0][0],
            "secondary_style": sorted_dims[1][0],
            "profile_type": sorted_dims[0][0] + sorted_dims[1][0],
            "interpretation": self._get_disc_interpretation(sorted_dims[0][0])
        }
    
    def _validate_responses(self, responses: List[Dict], config: Dict) -> Dict:
        """Validate assessment responses"""
        errors = []
        
        # Check all required questions answered
        required_questions = set(config.get("required_questions", []))
        answered_questions = set(r["question_id"] for r in responses)
        
        missing = required_questions - answered_questions
        if missing:
            errors.append(f"Missing responses for questions: {missing}")
        
        # Check response values are valid
        for response in responses:
            if "answer_value" in response:
                value = response["answer_value"]
                if not (config["min_value"] <= value <= config["max_value"]):
                    errors.append(f"Invalid value {value} for question {response['question_id']}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _score_to_percentile(self, normalized_score: float) -> int:
        """Convert normalized score to percentile"""
        return int(normalized_score * 100)
    
    def _interpret_big_five_score(self, dimension: str, score: float) -> str:
        """Interpret Big Five score"""
        level = "high" if score > 0.65 else "moderate" if score > 0.35 else "low"
        
        interpretations = {
            "openness": {
                "high": "Creative, curious, and open to new experiences",
                "moderate": "Balanced between traditional and novel approaches",
                "low": "Practical, conventional, and prefers routine"
            },
            "conscientiousness": {
                "high": "Organized, responsible, and goal-oriented",
                "moderate": "Flexible with reasonable level of organization",
                "low": "Spontaneous and adaptable"
            },
            "extraversion": {
                "high": "Outgoing, energetic, and socially confident",
                "moderate": "Comfortable in both social and solitary settings",
                "low": "Reserved, reflective, and prefers smaller groups"
            },
            "agreeableness": {
                "high": "Compassionate, cooperative, and trusting",
                "moderate": "Balanced between cooperation and assertion",
                "low": "Direct, competitive, and skeptical"
            },
            "neuroticism": {
                "high": "Sensitive to stress and prone to worry",
                "moderate": "Generally stable with occasional emotional sensitivity",
                "low": "Emotionally stable and resilient"
            }
        }
        
        return interpretations[dimension][level]
    
    def _get_mbti_description(self, mbti_type: str) -> str:
        """Get MBTI type description"""
        descriptions = {
            "INTJ": "Strategic, analytical, and independent thinker",
            "INTP": "Logical, innovative, and adaptable problem-solver",
            "ENTJ": "Bold, decisive, and natural leader",
            "ENTP": "Quick-witted, enthusiastic debater and innovator",
            # Add all 16 types...
        }
        return descriptions.get(mbti_type, "Unique personality type")
    
    def _get_enneagram_description(self, type_num: int) -> str:
        """Get Enneagram type description"""
        descriptions = {
            1: "The Perfectionist - Principled and purposeful",
            2: "The Helper - Generous and people-pleasing",
            3: "The Achiever - Success-oriented and driven",
            4: "The Individualist - Sensitive and creative",
            5: "The Investigator - Intense and cerebral",
            6: "The Loyalist - Committed and security-oriented",
            7: "The Enthusiast - Spontaneous and versatile",
            8: "The Challenger - Powerful and dominating",
            9: "The Peacemaker - Receptive and agreeable"
        }
        return descriptions.get(type_num, "Unknown type")
    
    def _get_disc_interpretation(self, primary: str) -> str:
        """Get DISC interpretation"""
        interpretations = {
            "D": "Dominant - Direct, results-oriented, and decisive",
            "I": "Influential - Outgoing, enthusiastic, and persuasive",
            "S": "Steady - Patient, reliable, and team-oriented",
            "C": "Conscientious - Analytical, precise, and systematic"
        }
        return interpretations.get(primary, "Balanced profile")
    
    def _calculate_completion_time(self, responses: List[Dict]) -> int:
        """Calculate assessment completion time in seconds"""
        if not responses or "timestamp" not in responses[0]:
            return 0
        
        timestamps = [datetime.fromisoformat(r["timestamp"]) for r in responses if "timestamp" in r]
        if len(timestamps) < 2:
            return 0
        
        duration = (max(timestamps) - min(timestamps)).total_seconds()
        return int(duration)

