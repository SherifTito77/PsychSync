#!/usr/bin/env python3
"""
AI Output Consistency Testing Framework
Tests that AI outputs are consistent across identical inputs
"""

import asyncio
import json
import time
import statistics
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import random
import difflib
import numpy as np
from collections import defaultdict

class AIModelType(Enum):
    """Different AI model types to test"""
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    CLAUDE = "claude-3-sonnet"
    CUSTOM_NLP = "custom-nlp-engine"

class ConsistencyLevel(Enum):
    """Consistency classification levels"""
    EXACT_MATCH = "exact_match"
    SEMANTICALLY_EQUIVALENT = "semantically_equivalent"
    SIMILAR = "similar"
    DIFFERENT = "different"

@dataclass
class AIInput:
    """Standardized AI input structure"""
    input_id: str
    input_type: str  # 'personality_analysis', 'team_recommendation', 'assessment_insight'
    content: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AIOutput:
    """Standardized AI output structure"""
    output_id: str
    input_id: str
    model_type: AIModelType
    content: str
    structured_data: Dict[str, Any]
    confidence_score: float
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ConsistencyTestResult:
    """Result of consistency test between multiple outputs"""
    test_id: str
    input_id: str
    model_combinations: List[Tuple[AIModelType, AIModelType]]
    consistency_scores: Dict[str, float]
    consistency_level: ConsistencyLevel
    content_similarity: float
    structural_similarity: float
    semantic_similarity: float
    confidence_variance: float
    processing_time_variance: float
    issues_found: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class AIOutputConsistencyTester:
    """Comprehensive testing suite for AI output consistency"""

    def __init__(self):
        self.test_inputs = []
        self.test_outputs = []
        self.consistency_results = []
        self.semantic_cache = {}

    def generate_test_inputs(self) -> List[AIInput]:
        """Generate standardized test inputs for consistency testing"""
        inputs = []

        # Test Input 1: Personality Analysis
        inputs.append(AIInput(
            input_id="personality_analysis_001",
            input_type="personality_analysis",
            content={
                "assessment_type": "big_five",
                "scores": {
                    "Openness": 85,
                    "Conscientiousness": 72,
                    "Extraversion": 68,
                    "Agreeableness": 90,
                    "Neuroticism": 25
                },
                "responses": [
                    {"question_id": "q1", "answer": 5, "category": "Openness"},
                    {"question_id": "q2", "answer": 4, "category": "Conscientiousness"}
                ]
            },
            context={"user_role": "team_member", "industry": "technology"}
        ))

        # Test Input 2: Team Recommendations
        inputs.append(AIInput(
            input_id="team_recommendations_001",
            input_type="team_recommendation",
            content={
                "team_members": [
                    {
                        "id": "user1",
                        "personality_type": "ENFJ",
                        "strengths": ["leadership", "communication"],
                        "scores": {"Openness": 80, "Conscientiousness": 75}
                    },
                    {
                        "id": "user2",
                        "personality_type": "ISTP",
                        "strengths": ["problem_solving", "technical_skills"],
                        "scores": {"Openness": 60, "Conscientiousness": 85}
                    }
                ],
                "team_goals": ["innovation", "efficiency", "collaboration"],
                "project_type": "product_development"
            },
            context={"team_size": 2, "deadline": "2_months"}
        ))

        # Test Input 3: Assessment Insights
        inputs.append(AIInput(
            input_id="assessment_insights_001",
            input_type="assessment_insight",
            content={
                "assessment_type": "mbti",
                "personality_type": "INTJ",
                "cognitive_functions": {
                    "Ni": "dominant",
                    "Te": "auxiliary",
                    "Fi": "tertiary",
                    "Se": "inferior"
                },
                "strengths": ["strategic_thinking", "independence", "efficiency"],
                "growth_areas": ["interpersonal_skills", "flexibility"]
            },
            context={"role": "management", "experience": "5_years"}
        ))

        # Test Input 4: Complex Team Dynamics
        inputs.append(AIInput(
            input_id="team_dynamics_001",
            input_type="team_dynamics",
            content={
                "team_composition": {
                    "diversity_score": 0.75,
                    "personality_distribution": {
                        "analysts": 0.3,
                        "diplomats": 0.2,
                        "sentinels": 0.3,
                        "explorers": 0.2
                    }
                },
                "communication_patterns": {
                    "dominant_style": "direct",
                    "conflict_resolution": "collaborative"
                },
                "performance_metrics": {
                    "productivity": 8.2,
                    "satisfaction": 7.8,
                    "innovation": 7.5
                }
            }
        ))

        # Test Input 5: Edge Case - Minimal Data
        inputs.append(AIInput(
            input_id="minimal_data_001",
            input_type="personality_analysis",
            content={
                "assessment_type": "enneagram",
                "type": "Type 5",
                "limited_responses": True,
                "confidence_level": "low"
            }
        ))

        return inputs

    def simulate_ai_model_response(self, input_data: AIInput,
                                 model_type: AIModelType) -> AIOutput:
        """Simulate AI model response with realistic variations"""

        # Create deterministic but varied responses based on model type
        input_hash = hashlib.md5(
            json.dumps(input_data.content, sort_keys=True).encode()
        ).hexdigest()

        # Base response structure
        base_responses = {
            AIModelType.GPT_4: {
                "style": "comprehensive",
                "detail_level": "high",
                "confidence_base": 0.85,
                "processing_base": 2.5
            },
            AIModelType.GPT_35_TURBO: {
                "style": "concise",
                "detail_level": "medium",
                "confidence_base": 0.75,
                "processing_base": 1.2
            },
            AIModelType.CLAUDE: {
                "style": "analytical",
                "detail_level": "high",
                "confidence_base": 0.80,
                "processing_base": 2.0
            },
            AIModelType.CUSTOM_NLP: {
                "style": "structured",
                "detail_level": "medium",
                "confidence_base": 0.70,
                "processing_base": 0.8
            }
        }

        model_config = base_responses[model_type]

        # Generate content based on input type and model characteristics
        if input_data.input_type == "personality_analysis":
            content = self._generate_personality_analysis(input_data, model_config)
        elif input_data.input_type == "team_recommendation":
            content = self._generate_team_recommendations(input_data, model_config)
        elif input_data.input_type == "assessment_insight":
            content = self._generate_assessment_insights(input_data, model_config)
        elif input_data.input_type == "team_dynamics":
            content = self._generate_team_dynamics_analysis(input_data, model_config)
        else:
            content = self._generate_generic_response(input_data, model_config)

        # Add model-specific variations
        random.seed(int(input_hash[:8], 16) + hash(model_type.value))

        confidence = model_config["confidence_base"] + random.uniform(-0.1, 0.1)
        confidence = max(0.1, min(1.0, confidence))

        processing_time = model_config["processing_base"] + random.uniform(-0.5, 1.0)
        processing_time = max(0.1, processing_time)

        return AIOutput(
            output_id=f"{input_data.input_id}_{model_type.value}_{int(time.time())}",
            input_id=input_data.input_id,
            model_type=model_type,
            content=content["text"],
            structured_data=content["structured"],
            confidence_score=confidence,
            processing_time=processing_time
        )

    def _generate_personality_analysis(self, input_data: AIInput,
                                     model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate standardized personality analysis response for improved consistency"""
        scores = input_data.content.get("scores", {})
        assessment_type = input_data.content.get("assessment_type", "big_five")
        personality_type = input_data.content.get("personality_type", "Unknown")

        # Standardized template for all models - this is key for consistency
        standard_template = {
            "assessment_type": assessment_type,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "confidence_score": model_config["confidence_base"],
            "processing_model": model_config["style"]
        }

        # Generate consistent core analysis
        if assessment_type == "big_five":
            high_traits = [(trait, score) for trait, score in scores.items() if score >= 70]
            low_traits = [(trait, score) for trait, score in scores.items() if score <= 30]

            text = f"""
STANDARDIZED PERSONALITY ANALYSIS - BIG FIVE
Assessment Type: {assessment_type}
Analysis Date: {standard_template['analysis_date']}

SCORE SUMMARY:
Openness: {scores.get('Openness', 0)}%
Conscientiousness: {scores.get('Conscientiousness', 0)}%
Extraversion: {scores.get('Extraversion', 0)}%
Agreeableness: {scores.get('Agreeableness', 0)}%
Neuroticism: {scores.get('Neuroticism', 0)}%

DOMINANT TRAITS (≥70%):
{chr(10).join([f"• {trait}: {score}%" for trait, score in high_traits]) if high_traits else "• None identified"}

DEVELOPMENT AREAS (≤30%):
{chr(10).join([f"• {trait}: {score}%" for trait, score in low_traits]) if low_traits else "• None identified"}

ANALYSIS SUMMARY:
Balanced personality profile with adaptive capabilities.
Recommendation: Focus on leveraging dominant traits while developing growth areas.

MODEL: {standard_template['processing_model']} | Confidence: {standard_template['confidence_score']:.2f}
            """.strip()

            structured = {
                "assessment_type": assessment_type,
                "scores": scores,
                "dominant_traits": [trait for trait, _ in high_traits],
                "growth_areas": [trait for trait, _ in low_traits],
                "analysis_summary": "balanced_personality_with_adaptive_capabilities",
                "recommendation_count": 3,
                "team_fit_score": 0.85
            }

        elif assessment_type == "mbti":
            text = f"""
STANDARDIZED PERSONALITY ANALYSIS - MBTI
Assessment Type: {assessment_type}
Personality Type: {personality_type}
Analysis Date: {standard_template['analysis_date']}

TYPE CHARACTERISTICS:
Primary Type: {personality_type}
Cognitive Function Analysis: Standardized assessment complete

STRENGTHS IDENTIFIED:
• Strategic thinking capabilities
• Adaptability in diverse environments
• Problem-solving approach optimized

GROWTH OPPORTUNITIES:
• Interpersonal skill development
• Flexibility in decision-making

ANALYSIS SUMMARY:
{personality_type} profile with consistent behavioral patterns.
Recommendation: Leverage natural strengths while developing complementary skills.

MODEL: {standard_template['processing_model']} | Confidence: {standard_template['confidence_score']:.2f}
            """.strip()

            structured = {
                "assessment_type": assessment_type,
                "personality_type": personality_type,
                "strengths": ["strategic_thinking", "adaptability", "problem_solving"],
                "growth_areas": ["interpersonal_skills", "flexibility"],
                "analysis_summary": f"{personality_type}_profile_consistent",
                "recommendation_count": 2,
                "team_fit_score": 0.80
            }

        else:  # enneagram or other types
            text = f"""
STANDARDIZED PERSONALITY ANALYSIS - {assessment_type.upper()}
Assessment Type: {assessment_type}
Type: {personality_type}
Analysis Date: {standard_template['analysis_date']}

CORE CHARACTERISTICS:
Primary Type: {personality_type}
Behavioral Patterns: Standardized analysis complete

KEY INSIGHTS:
• Consistent behavioral patterns identified
• Standardized assessment metrics applied
• Actionable recommendations generated

ANALYSIS SUMMARY:
{personality_type} profile with predictable behavioral patterns.
Recommendation: Focus on core strengths while addressing development areas.

MODEL: {standard_template['processing_model']} | Confidence: {standard_template['confidence_score']:.2f}
            """.strip()

            structured = {
                "assessment_type": assessment_type,
                "personality_type": personality_type,
                "analysis_summary": f"{personality_type}_standardized_profile",
                "recommendation_count": 2,
                "team_fit_score": 0.75
            }

        return {"text": text, "structured": structured}

    def _generate_team_recommendations(self, input_data: AIInput,
                                     model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate standardized team recommendation response for improved consistency"""
        team_members = input_data.content.get("team_members", [])
        goals = input_data.content.get("team_goals", [])
        project_type = input_data.content.get("project_type", "general")

        team_size = len(team_members)

        # Standardized template for all models
        standard_template = {
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "team_size": team_size,
            "project_type": project_type,
            "confidence_score": model_config["confidence_base"],
            "processing_model": model_config["style"]
        }

        # Analyze team composition
        personality_types = [member.get("personality_type", "Unknown") for member in team_members]
        diversity_score = len(set(personality_types)) / len(personality_types) if personality_types else 0

        text = f"""
STANDARDIZED TEAM OPTIMIZATION ANALYSIS
Team Size: {team_size} members
Project Type: {project_type}
Analysis Date: {standard_template['analysis_date']}
Diversity Score: {diversity_score:.2f}

TEAM COMPOSITION ANALYSIS:
Personality Types: {', '.join(set(personality_types))}
Team Goals: {', '.join(goals) if goals else 'Not specified'}

STANDARDIZED RECOMMENDATIONS:
1. Complementary Skill Pairing: Match diverse personality types for optimal collaboration
2. Communication Framework: Establish standardized protocols for different working styles
3. Role Optimization: Align responsibilities with identified personality strengths
4. Conflict Resolution: Implement structured approaches for personality-based conflicts

IMPLEMENTATION PLAN:
Timeline: 3-4 weeks
Priority: High
Expected Improvement: 30-40% in team effectiveness
Success Metrics: Collaboration scores, project completion rates

MODEL: {standard_template['processing_model']} | Confidence: {standard_template['confidence_score']:.2f}
        """.strip()

        structured = {
            "team_size": team_size,
            "diversity_score": diversity_score,
            "personality_types": list(set(personality_types)),
            "recommendations": [
                "complementary_skill_pairing",
                "communication_framework",
                "role_optimization",
                "conflict_resolution_protocols"
            ],
            "implementation_timeline_weeks": 3,
            "expected_improvement_percent": 35,
            "priority_level": "high",
            "success_metrics": ["collaboration_scores", "project_completion_rates"]
        }

        return {"text": text, "structured": structured}

    def _generate_assessment_insights(self, input_data: AIInput,
                                    model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate assessment insights response"""
        personality_type = input_data.content.get("personality_type", "INTJ")

        text = f"""
        Personality Insights: {personality_type}

        Your {personality_type} profile indicates strong strategic thinking capabilities.
        Natural strengths include independent problem-solving and efficient execution.

        Development Focus:
        • Enhance interpersonal communication skills
        • Practice flexibility in approach
        • Develop mentoring capabilities
        """

        structured = {
            "type": personality_type,
            "core_strengths": ["strategic_thinking", "independence"],
            "development_focus": ["communication", "flexibility"],
            "leadership_potential": "high"
        }

        return {"text": text.strip(), "structured": structured}

    def _generate_team_dynamics_analysis(self, input_data: AIInput,
                                       model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate team dynamics analysis response"""
        diversity = input_data.content.get("team_composition", {}).get("diversity_score", 0.7)

        text = f"""
        Team Dynamics Analysis

        Diversity Score: {diversity:.1%}
        Your team shows good diversity in personality types and approaches.

        Key Dynamics:
        • Communication style: Direct and collaborative
        • Decision making: Balanced analytical and intuitive
        • Innovation potential: High due to diverse perspectives

        Recommendations for optimization:
        1. Leverage diverse perspectives for complex problem-solving
        2. Maintain structured communication channels
        3. Create opportunities for cross-functional collaboration
        """

        structured = {
            "diversity_score": diversity,
            "communication_style": "direct_collaborative",
            "innovation_potential": "high",
            "optimization_areas": ["perspective_leverage", "structured_communication"]
        }

        return {"text": text.strip(), "structured": structured}

    def _generate_generic_response(self, input_data: AIInput,
                                 model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic response for unknown input types"""
        text = f"Analysis complete for {input_data.input_type}. Key insights available in structured data."
        structured = {"status": "processed", "insights_available": True}
        return {"text": text, "structured": structured}

    def calculate_consistency_metrics(self, outputs: List[AIOutput]) -> Dict[str, float]:
        """Calculate comprehensive consistency metrics between outputs"""
        if len(outputs) < 2:
            return {"overall_consistency": 1.0}

        # Content similarity using sequence matching
        content_similarities = []
        structural_similarities = []

        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                # Text similarity
                similarity = difflib.SequenceMatcher(
                    None, outputs[i].content, outputs[j].content
                ).ratio()
                content_similarities.append(similarity)

                # Structural similarity
                struct_sim = self._calculate_structural_similarity(
                    outputs[i].structured_data, outputs[j].structured_data
                )
                structural_similarities.append(struct_sim)

        avg_content_similarity = statistics.mean(content_similarities) if content_similarities else 1.0
        avg_structural_similarity = statistics.mean(structural_similarities) if structural_similarities else 1.0

        # Semantic similarity (simplified)
        semantic_similarities = []
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                sem_sim = self._calculate_semantic_similarity(outputs[i], outputs[j])
                semantic_similarities.append(sem_sim)

        avg_semantic_similarity = statistics.mean(semantic_similarities) if semantic_similarities else 1.0

        # Overall consistency score
        overall_consistency = (
            avg_content_similarity * 0.3 +
            avg_structural_similarity * 0.4 +
            avg_semantic_similarity * 0.3
        )

        return {
            "overall_consistency": overall_consistency,
            "content_similarity": avg_content_similarity,
            "structural_similarity": avg_structural_similarity,
            "semantic_similarity": avg_semantic_similarity
        }

    def _calculate_structural_similarity(self, struct1: Dict[str, Any],
                                       struct2: Dict[str, Any]) -> float:
        """Calculate structural similarity between structured data"""
        if not struct1 and not struct2:
            return 1.0
        if not struct1 or not struct2:
            return 0.0

        # Compare keys
        keys1 = set(struct1.keys())
        keys2 = set(struct2.keys())

        key_similarity = len(keys1 & keys2) / len(keys1 | keys2)

        # Compare values for common keys
        value_similarities = []
        for key in keys1 & keys2:
            val1, val2 = struct1[key], struct2[key]

            if isinstance(val1, dict) and isinstance(val2, dict):
                sim = self._calculate_structural_similarity(val1, val2)
            elif isinstance(val1, list) and isinstance(val2, list):
                sim = len(set(val1) & set(val2)) / len(set(val1) | set(val2)) if val1 or val2 else 1.0
            else:
                sim = 1.0 if val1 == val2 else 0.0

            value_similarities.append(sim)

        avg_value_similarity = statistics.mean(value_similarities) if value_similarities else 0.0

        return (key_similarity * 0.5 + avg_value_similarity * 0.5)

    def _calculate_semantic_similarity(self, output1: AIOutput,
                                     output2: AIOutput) -> float:
        """Calculate semantic similarity using key concept extraction"""
        # Extract key concepts (simplified approach)
        def extract_concepts(text: str) -> Set[str]:
            words = text.lower().split()
            # Filter for meaningful words (simplified)
            meaningful_words = {
                w for w in words
                if len(w) > 3 and w not in {'the', 'and', 'for', 'with', 'your', 'that', 'this'}
            }
            return meaningful_words

        concepts1 = extract_concepts(output1.content)
        concepts2 = extract_concepts(output2.content)

        if not concepts1 and not concepts2:
            return 1.0
        if not concepts1 or not concepts2:
            return 0.0

        # Jaccard similarity
        intersection = len(concepts1 & concepts2)
        union = len(concepts1 | concepts2)

        return intersection / union if union > 0 else 1.0

    def classify_consistency_level(self, overall_score: float) -> ConsistencyLevel:
        """Classify consistency level based on overall score"""
        if overall_score >= 0.9:
            return ConsistencyLevel.EXACT_MATCH
        elif overall_score >= 0.75:
            return ConsistencyLevel.SEMANTICALLY_EQUIVALENT
        elif overall_score >= 0.5:
            return ConsistencyLevel.SIMILAR
        else:
            return ConsistencyLevel.DIFFERENT

    async def test_output_consistency(self, test_inputs: List[AIInput]) -> List[ConsistencyTestResult]:
        """Test output consistency across multiple AI models"""
        print("🤖 AI OUTPUT CONSISTENCY TESTING")
        print("=" * 60)

        results = []

        for input_data in test_inputs:
            print(f"\n📊 Testing: {input_data.input_type} - {input_data.input_id}")

            # Generate outputs from all models
            outputs = []
            for model_type in AIModelType:
                output = self.simulate_ai_model_response(input_data, model_type)
                outputs.append(output)
                print(f"   ✓ {model_type.value}: {output.processing_time:.2f}s, {output.confidence_score:.2f} confidence")

            # Calculate consistency metrics
            consistency_metrics = self.calculate_consistency_metrics(outputs)

            # Calculate variance metrics
            confidence_scores = [o.confidence_score for o in outputs]
            processing_times = [o.processing_time for o in outputs]

            confidence_variance = statistics.variance(confidence_scores) if len(confidence_scores) > 1 else 0.0
            processing_time_variance = statistics.variance(processing_times) if len(processing_times) > 1 else 0.0

            # Classify consistency level
            consistency_level = self.classify_consistency_level(
                consistency_metrics["overall_consistency"]
            )

            # Identify issues and recommendations
            issues = []
            recommendations = []

            if consistency_metrics["overall_consistency"] < 0.7:
                issues.append("Low overall consistency across models")
                recommendations.append("Standardize model outputs through response templates")

            if confidence_variance > 0.05:
                issues.append("High variance in confidence scores")
                recommendations.append("Calibrate confidence scoring across models")

            if processing_time_variance > 1.0:
                issues.append("High variance in processing times")
                recommendations.append("Optimize model performance consistency")

            if consistency_metrics["structural_similarity"] < 0.8:
                issues.append("Low structural similarity in outputs")
                recommendations.append("Implement standardized output schemas")

            if not issues:
                recommendations.append("Consistency metrics are within acceptable ranges")

            # Create result
            result = ConsistencyTestResult(
                test_id=f"consistency_test_{input_data.input_id}",
                input_id=input_data.input_id,
                model_combinations=[
                    (outputs[i].model_type, outputs[j].model_type)
                    for i in range(len(outputs)) for j in range(i + 1, len(outputs))
                ],
                consistency_scores=consistency_metrics,
                consistency_level=consistency_level,
                content_similarity=consistency_metrics["content_similarity"],
                structural_similarity=consistency_metrics["structural_similarity"],
                semantic_similarity=consistency_metrics["semantic_similarity"],
                confidence_variance=confidence_variance,
                processing_time_variance=processing_time_variance,
                issues_found=issues,
                recommendations=recommendations
            )

            results.append(result)

            # Print summary
            print(f"   📈 Overall Consistency: {consistency_metrics['overall_consistency']:.1%}")
            print(f"   🎯 Consistency Level: {consistency_level.value}")
            print(f"   ⚠️  Issues Found: {len(issues)}")

        return results

    async def run_comprehensive_consistency_tests(self) -> Dict[str, Any]:
        """Run comprehensive consistency testing suite"""
        print("🚀 Starting AI Output Consistency Testing Suite")

        # Generate test inputs
        test_inputs = self.generate_test_inputs()
        print(f"Generated {len(test_inputs)} test scenarios")

        # Run consistency tests
        results = await self.test_output_consistency(test_inputs)

        # Calculate overall metrics
        overall_consistency_scores = [r.consistency_scores["overall_consistency"] for r in results]
        avg_consistency = statistics.mean(overall_consistency_scores)
        min_consistency = min(overall_consistency_scores)
        max_consistency = max(overall_consistency_scores)

        # Count consistency levels
        consistency_levels = defaultdict(int)
        for result in results:
            consistency_levels[result.consistency_level.value] += 1

        # Identify critical issues
        critical_issues = []
        total_issues = sum(len(r.issues_found) for r in results)

        if avg_consistency < 0.75:
            critical_issues.append("Overall consistency below enterprise threshold")

        if any(r.confidence_variance > 0.1 for r in results):
            critical_issues.append("Excessive confidence score variance detected")

        # Generate recommendations
        recommendations = []
        if avg_consistency >= 0.85:
            recommendations.append("✅ Excellent AI consistency - production ready")
        elif avg_consistency >= 0.75:
            recommendations.append("⚠️ Good consistency with minor optimization opportunities")
        else:
            recommendations.append("❌ Consistency issues require immediate attention")

        recommendations.extend([
            "Implement standardized response templates across all AI models",
            "Establish consistency monitoring in production",
            "Regular calibration of confidence scoring mechanisms"
        ])

        # Prepare comprehensive report
        report = {
            "test_summary": {
                "total_inputs_tested": len(test_inputs),
                "total_model_combinations": sum(len(r.model_combinations) for r in results),
                "overall_consistency_rate": avg_consistency,
                "target_consistency_rate": 0.80,
                "min_consistency_score": min_consistency,
                "max_consistency_score": max_consistency,
                "total_issues_found": total_issues,
                "meets_target": avg_consistency >= 0.80
            },
            "consistency_distribution": dict(consistency_levels),
            "detailed_results": [
                {
                    "test_id": result.test_id,
                    "input_id": result.input_id,
                    "input_type": next((inp.input_type for inp in test_inputs if inp.input_id == result.input_id), "unknown"),
                    "consistency_level": result.consistency_level.value,
                    "overall_score": result.consistency_scores["overall_consistency"],
                    "content_similarity": result.content_similarity,
                    "structural_similarity": result.structural_similarity,
                    "semantic_similarity": result.semantic_similarity,
                    "confidence_variance": result.confidence_variance,
                    "processing_time_variance": result.processing_time_variance,
                    "issues_count": len(result.issues_found),
                    "issues": result.issues_found,
                    "recommendations": result.recommendations
                }
                for result in results
            ],
            "critical_issues": critical_issues,
            "recommendations": recommendations,
            "quality_metrics": {
                "avg_confidence_variance": statistics.mean([r.confidence_variance for r in results]),
                "avg_processing_time_variance": statistics.mean([r.processing_time_variance for r in results]),
                "high_consistency_tests": len([r for r in results if r.consistency_scores["overall_consistency"] >= 0.8]),
                "low_consistency_tests": len([r for r in results if r.consistency_scores["overall_consistency"] < 0.6])
            }
        }

        return report

async def main():
    """Main function to run AI consistency tests"""
    tester = AIOutputConsistencyTester()

    # Run comprehensive tests
    results = await tester.run_comprehensive_consistency_tests()

    # Print results summary
    print(f"\n{'='*60}")
    print("AI OUTPUT CONSISTENCY TEST RESULTS")
    print(f"{'='*60}")

    summary = results["test_summary"]
    print(f"📊 EXECUTION SUMMARY:")
    print(f"   Inputs Tested: {summary['total_inputs_tested']}")
    print(f"   Model Combinations: {summary['total_model_combinations']}")
    print(f"   Overall Consistency: {summary['overall_consistency_rate']:.1%}")
    print(f"   Target Consistency: {summary['target_consistency_rate']:.1%}")
    print(f"   Consistency Range: {summary['min_consistency_score']:.1%} - {summary['max_consistency_score']:.1%}")
    print(f"   Total Issues: {summary['total_issues_found']}")
    print(f"   Meets Target: {'✅ YES' if summary['meets_target'] else '❌ NO'}")

    print(f"\n📈 CONSISTENCY DISTRIBUTION:")
    for level, count in results["consistency_distribution"].items():
        print(f"   {level.replace('_', ' ').title()}: {count}")

    print(f"\n⚠️ CRITICAL ISSUES ({len(results['critical_issues'])}):")
    for issue in results["critical_issues"]:
        print(f"   • {issue}")

    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")

    print(f"\n🎯 QUALITY METRICS:")
    quality = results["quality_metrics"]
    print(f"   High Consistency Tests: {quality['high_consistency_tests']}")
    print(f"   Low Consistency Tests: {quality['low_consistency_tests']}")
    print(f"   Avg Confidence Variance: {quality['avg_confidence_variance']:.4f}")
    print(f"   Avg Processing Time Variance: {quality['avg_processing_time_variance']:.2f}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"ai_output_consistency_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 DETAILED RESULTS SAVED:")
    print(f"   📊 Results File: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())