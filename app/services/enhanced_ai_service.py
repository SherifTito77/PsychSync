"""
Enhanced AI Service with Advanced Personality Insights
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import random

class EnhancedAIProcessor:
    """Advanced AI processor for detailed personality analysis"""

    def __init__(self):
        self.personality_descriptions = self._load_descriptions()
        self.workplace_insights = self._load_workplace_insights()
        self.development_recommendations = self._load_development_recommendations()

    def process_enhanced_assessment(self, framework: str, data: Dict[str, Any], user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process assessment with enhanced AI insights"""

        base_result = self._get_base_personality_data(framework, data)

        # Enhanced insights
        enhanced_result = {
            **base_result,
            'detailed_analysis': self._get_detailed_analysis(framework, data),
            'workplace_compatibility': self._get_workplace_compatibility(framework, data),
            'development_areas': self._get_development_areas(framework, data),
            'strengths': self._get_strengths(framework, data),
            'growth_opportunities': self._get_growth_opportunities(framework, data),
            'team_dynamics': self._get_team_dynamics(framework, data),
            'leadership_potential': self._assess_leadership_potential(framework, data),
            'communication_style': self._analyze_communication_style(framework, data),
            'decision_making': self._analyze_decision_making(framework, data),
            'stress_management': self._analyze_stress_management(framework, data),
            'personalized_recommendations': self._get_personalized_recommendations(framework, data, user_context)
        }

        return enhanced_result

    def _get_base_personality_data(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get base personality data"""
        personality_type = data.get('type', 'Unknown')
        confidence = data.get('confidence', 0.8)

        descriptions = {
            'mbti': {
                'INTJ': 'The Architect - Imaginative and strategic thinkers, with a plan for everything.',
                'ENFP': 'The Campaigner - Enthusiastic, creative and sociable free spirits.',
                'ISTJ': 'The Logistician - Practical and fact-oriented individuals, reliable and dutiful.',
                'ESFJ': 'The Consul - Extraordinary caring, social and popular people, always eager to help.',
                'INFJ': 'The Advocate - Quiet and mystical, yet very inspiring and tireless idealists.',
                'ESTP': 'The Entrepreneur - Smart, energetic and very perceptive people, who truly enjoy living on the edge.',
                'INFP': 'The Mediator - Poetic, kind and altruistic people, always eager to help a good cause.',
                'ESTJ': 'The Executive - Excellent administrators, unsurpassed at managing things or people.',
                'ISFJ': 'The Defender - Very dedicated and warm protectors, always ready to defend loved ones.',
                'ENTP': 'The Debater - Smart and curious thinkers who cannot resist an intellectual challenge.',
                'ISTP': 'The Virtuoso - Bold and practical experimenters, masters of all kinds of tools.',
                'ISFP': 'The Adventurer - Flexible and charming artists, always ready to explore.',
                'ENTJ': 'The Commander - Bold, imaginative and strong-willed leaders, always finding a way.',
                'INTP': 'The Logician - Innovative inventors with an unquenchable thirst for knowledge.',
                'ESFP': 'The Entertainer - Spontaneous, energetic and enthusiastic entertainers.',
                'ENFJ': 'The Protagonist - Charismatic and inspiring leaders, able to mesmerize their listeners.'
            },
            'enneagram': {
                'Type 1': 'The Reformer - Rational and idealistic with strong principles.',
                'Type 2': 'The Helper - Caring and interpersonal with generous spirit.',
                'Type 3': 'The Achiever - Success-oriented and pragmatic with image-conscious drive.',
                'Type 4': 'The Individualist - Sensitive and expressive with deep self-awareness.',
                'Type 5': 'The Investigator - Perceptive and innovative with intense cerebral focus.',
                'Type 6': 'The Loyalist - Committed and security-oriented with engaging responsibility.',
                'Type 7': 'The Enthusiast - Busy and fun-loving with spontaneous versatility.',
                'Type 8': 'The Challenger': 'Self-confident and decisive with powerful will.',
                'Type 9': 'The Peacemaker - Easygoing and self-effacing with receptive stability.'
            }
        }

        framework_descriptions = descriptions.get(framework, {})
        description = framework_descriptions.get(personality_type, f'{personality_type} personality analysis for {framework} framework.')

        return {
            'type': personality_type,
            'framework': framework,
            'confidence': confidence,
            'description': description,
            'processed_at': datetime.now().isoformat(),
            'processed_by': 'PsychSync Enhanced AI Engine'
        }

    def _get_detailed_analysis(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed personality analysis"""
        personality_type = data.get('type', 'Unknown')

        detailed_analyses = {
            'INTJ': {
                'core_traits': ['Strategic thinking', 'Independence', 'Perfectionism', 'Innovation'],
                'cognitive_style': 'Analytical and systems-oriented thinking',
                'motivational_drivers': ['Competence', 'Achievement', 'Knowledge'],
                'potential_challenges': ['Perfectionism', 'Impatience with inefficiency', 'Difficulty with small talk'],
                'ideal_environment': 'Structured environment with autonomy and intellectual challenges'
            },
            'ENFP': {
                'core_traits': ['Creativity', 'Empathy', 'Enthusiasm', 'Adaptability'],
                'cognitive_style': 'Creative and people-oriented thinking',
                'motivational_drivers': ['Connection', 'Creativity', 'Freedom'],
                'potential_challenges': ['Difficulty with routine', 'Over-commitment', 'Emotional sensitivity'],
                'ideal_environment': 'Dynamic, collaborative environment with diverse interactions'
            }
        }

        return detailed_analyses.get(personality_type, {
            'core_traits': ['Adaptability', 'Learning capability'],
            'cognitive_style': 'Flexible thinking approach',
            'motivational_drivers': ['Growth', 'Achievement'],
            'potential_challenges': ['Context-specific challenges'],
            'ideal_environment': 'Supportive and challenging environment'
        })

    def _get_workplace_compatibility(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workplace compatibility"""
        personality_type = data.get('type', 'Unknown')

        compatibility_map = {
            'INTJ': {
                'best_fit_roles': ['Strategic Planner', 'Systems Analyst', 'Research Director', 'Software Architect'],
                'collaboration_style': 'Prefers working independently on complex problems',
                'management_approach': 'Values competence and autonomy, minimal supervision',
                'team_contribution': 'Strategic insights and long-term planning'
            },
            'ENFP': {
                'best_fit_roles': ['Creative Director', 'HR Manager', 'Marketing Specialist', 'Team Builder'],
                'collaboration_style': 'Thrives in collaborative, people-oriented environments',
                'management_approach': 'Values encouragement, inspiration, and flexibility',
                'team_contribution': 'Creative solutions and team morale'
            }
        }

        return compatibility_map.get(personality_type, {
            'best_fit_roles': ['Consultant', 'Specialist', 'Coordinator'],
            'collaboration_style': 'Adaptable to various team dynamics',
            'management_approach': 'Values clear communication and respect',
            'team_contribution': 'Reliable and adaptable contributions'
        })

    def _get_development_areas(self, framework: str, data: Dict[str, Any]) -> List[str]:
        """Identify development areas"""
        personality_type = data.get('type', 'Unknown')

        development_map = {
            'INTJ': ['Interpersonal communication', 'Patience with process', 'Emotional expression', 'Delegating effectively'],
            'ENFP': ['Time management', 'Attention to detail', 'Conflict resolution', 'Maintaining focus'],
            'ISTJ': ['Adaptability to change', 'Creative thinking', 'Risk tolerance', 'Expressing appreciation'],
            'ESFJ': ['Setting boundaries', 'Critical thinking', 'Giving constructive feedback', 'Self-care']
        }

        return development_map.get(personality_type, ['Self-awareness', 'Communication skills', 'Emotional intelligence', 'Adaptability'])

    def _get_strengths(self, framework: str, data: Dict[str, Any]) -> List[str]:
        """Identify key strengths"""
        personality_type = data.get('type', 'Unknown')

        strengths_map = {
            'INTJ': ['Strategic thinking', 'Problem-solving', 'Independence', 'Innovation', 'Long-term planning'],
            'ENFP': ['Creativity', 'Empathy', 'Communication', 'Adaptability', 'Inspiring others'],
            'ISTJ': ['Reliability', 'Organization', 'Attention to detail', 'Loyalty', 'Practicality'],
            'ESFJ': ['Supportiveness', 'Organization', 'Empathy', 'Loyalty', 'Harmony maintenance']
        }

        return strengths_map.get(personality_type, ['Adaptability', 'Learning capability', 'Problem-solving', 'Teamwork'])

    def _get_growth_opportunities(self, framework: str, data: Dict[str, Any]) -> List[str]:
        """Identify growth opportunities"""
        return [
            'Develop emotional intelligence for better relationships',
            'Practice flexibility in thinking and approach',
            'Enhance communication across different personality types',
            'Build resilience through stress management techniques',
            'Develop leadership skills regardless of personality type'
        ]

    def _get_team_dynamics(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team dynamics contribution"""
        personality_type = data.get('type', 'Unknown')

        return {
            'role_in_team': self._determine_team_role(personality_type),
            'conflict_resolution_style': self._get_conflict_style(personality_type),
            'communication_preferences': self._get_communication_preferences(personality_type),
            'decision_making_contribution': self._get_decision_contribution(personality_type)
        }

    def _assess_leadership_potential(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess leadership potential and style"""
        personality_type = data.get('type', 'Unknown')

        leadership_map = {
            'INTJ': {
                'style': 'Strategic/Transformational',
                'strengths': ['Vision setting', 'Strategic planning', 'Problem-solving'],
                'development_areas': ['People skills', 'Patience', 'Communication clarity']
            },
            'ENFP': {
                'style': 'Inspirational/Participative',
                'strengths': ['Team motivation', 'Creative problem-solving', 'Communication'],
                'development_areas': ['Follow-through', 'Conflict management', 'Structured planning']
            }
        }

        return leadership_map.get(personality_type, {
            'style': 'Adaptive leadership',
            'strengths': ['Flexibility', 'Learning orientation', 'Team building'],
            'development_areas': ['Consistency', 'Strategic thinking', 'Decision speed']
        })

    def _analyze_communication_style(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze communication preferences"""
        personality_type = data.get('type', 'Unknown')

        return {
            'preferred_medium': self._get_communication_medium(personality_type),
            'communication_style': self._get_communication_approach(personality_type),
            'feedback_reception': self._get_feedback_style(personality_type),
            'presentation_style': self._get_presentation_style(personality_type)
        }

    def _analyze_decision_making(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze decision-making style"""
        return {
            'approach': 'Analytical and systematic',
            'speed': 'Moderate to fast',
            'factors_considered': ['Data analysis', 'Long-term impact', 'Stakeholder needs', 'Risk assessment'],
            'decision_confidence': 'High with sufficient information',
            'stress_response': 'Becomes more analytical under pressure'
        }

    def _analyze_stress_management(self, framework: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze stress management tendencies"""
        return {
            'stress_triggers': ['Uncertainty', 'Time pressure', 'Interpersonal conflict', 'Resource constraints'],
            'stress_response': 'Increased analytical thinking and withdrawal',
            'coping_mechanisms': ['Problem analysis', 'Structured planning', 'Seeking information'],
            'recovery_needs': ['Quiet time', 'Autonomy', 'Logical solutions'],
            'prevention_strategies': ['Advance planning', 'Skill development', 'Boundary setting']
        }

    def _get_personalized_recommendations(self, framework: str, data: Dict[str, Any], user_context: Optional[Dict] = None) -> List[str]:
        """Generate personalized recommendations"""
        base_recommendations = [
            "Focus on developing complementary skills to your natural strengths",
            "Seek mentors or colleagues with different personality types for balanced perspective",
            "Practice self-awareness through regular reflection and feedback",
            "Set challenging but achievable goals that leverage your natural talents"
        ]

        # Add context-specific recommendations
        if user_context:
            if user_context.get('role') == 'manager':
                base_recommendations.extend([
                    "Develop adaptive leadership approaches for different team members",
                    "Create environments that accommodate diverse working styles"
                ])
            elif user_context.get('role') == 'team_member':
                base_recommendations.extend([
                    "Proactively communicate your working preferences",
                    "Seek roles and projects that align with your natural strengths"
                ])

        return base_recommendations

    # Helper methods
    def _determine_team_role(self, personality_type: str) -> str:
        roles = {
            'INTJ': 'Strategic Visionary',
            'ENFP': 'Creative Catalyst',
            'ISTJ': 'Reliable Executor',
            'ESFJ': 'Team Harmonizer'
        }
        return roles.get(personality_type, 'Versatile Contributor')

    def _get_conflict_style(self, personality_type: str) -> str:
        styles = {
            'INTJ': 'Analytical problem-solving',
            'ENFP': 'Collaborative resolution',
            'ISTJ': 'Rule-based approach',
            'ESFJ': 'Harmony restoration'
        }
        return styles.get(personality_type, 'Adaptive approach')

    def _get_communication_preferences(self, personality_type: str) -> Dict[str, str]:
        preferences = {
            'INTJ': {'style': 'Direct and concise', 'frequency': 'As needed'},
            'ENFP': {'style': 'Expressive and enthusiastic', 'frequency': 'Regular'},
            'ISTJ': {'style': 'Clear and factual', 'frequency': 'Structured'},
            'ESFJ': {'style': 'Warm and personal', 'frequency': 'Frequent'}
        }
        return preferences.get(personality_type, {'style': 'Adaptable', 'frequency': 'Moderate'})

    def _get_decision_contribution(self, personality_type: str) -> str:
        contributions = {
            'INTJ': 'Strategic analysis and long-term planning',
            'ENFP': 'Creative solutions and stakeholder consideration',
            'ISTJ': 'Risk assessment and practical implementation',
            'ESFJ': 'Team impact and relationship considerations'
        }
        return contributions.get(personality_type, 'Balanced perspective')

    def _get_communication_medium(self, personality_type: str) -> str:
        mediums = {
            'INTJ': 'Written and data-driven',
            'ENFP': 'Verbal and interactive',
            'ISTJ': 'Clear, structured communication',
            'ESFJ': 'Personal and face-to-face'
        }
        return mediums.get(personality_type, 'Flexible adaptation')

    def _get_communication_approach(self, personality_type: str) -> str:
        approaches = {
            'INTJ': 'Direct and logical',
            'ENFP': 'Expressive and inspiring',
            'ISTJ': 'Factual and systematic',
            'ESFJ': 'Supportive and encouraging'
        }
        return approaches.get(personality_type, 'Balanced and adaptable')

    def _get_feedback_style(self, personality_type: str) -> str:
        styles = {
            'INTJ': 'Prefers constructive, solution-focused feedback',
            'ENFP': 'Appreciates personal and encouraging feedback',
            'ISTJ': 'Values specific, actionable feedback',
            'ESFJ': 'Responds well to supportive, collaborative feedback'
        }
        return styles.get(personality_type, 'Open to various feedback styles')

    def _get_presentation_style(self, personality_type: str) -> str:
        styles = {
            'INTJ': 'Structured and data-driven',
            'ENFP': 'Engaging and story-focused',
            'ISTJ': 'Organized and fact-based',
            'ESFJ': 'Interactive and relationship-focused'
        }
        return styles.get(personality_type, 'Adaptable presentation style')

# Initialize the enhanced AI processor
enhanced_ai_processor = EnhancedAIProcessor()