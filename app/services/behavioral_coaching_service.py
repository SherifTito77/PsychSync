# app/services/behavioral_coaching_service.py
"""
Behavioral Coaching and Intervention Service
Provides personalized coaching recommendations based on behavioral analysis
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func

from app.db.models.toxicity_detection import ToxicityPattern, BehavioralIntervention
from app.db.models.team_dynamics import TeamRoleAnalysis, TeamOptimization
from app.db.models.communication_patterns import CommunicationPatterns
from app.db.models.user import User
from app.core.logging_config import logger

@dataclass
class CoachingRecommendation:
    """Individual coaching recommendation"""
    category: str
    priority: str
    title: str
    description: str
    action_steps: List[str]
    expected_outcomes: List[str]
    timeline: str
    resources: List[str]

class BehavioralCoachingService:
    """
    Advanced behavioral coaching service
    Provides personalized recommendations for individuals and teams
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Coaching categories and focus areas
        self.coaching_categories = {
            'communication_excellence': {
                'description': 'Improve communication clarity, effectiveness, and impact',
                'focus_areas': ['clarity', 'listening', 'feedback', 'assertiveness', 'empathy'],
                'assessment_methods': ['sentiment_analysis', 'response_time', 'message_clarity', 'feedback_quality']
            },
            'leadership_development': {
                'description': 'Develop leadership skills and team influence',
                'focus_areas': ['vision', 'decision_making', 'delegation', 'motivation', 'conflict_resolution'],
                'assessment_methods': ['influence_scoring', 'decision_patterns', 'team_engagement', 'initiative_level']
            },
            'team_collaboration': {
                'description': 'Enhance teamwork and collaborative effectiveness',
                'focus_areas': ['trust_building', 'knowledge_sharing', 'psychological_safety', 'conflict_management'],
                'assessment_methods': ['network_analysis', 'collaboration_patterns', 'trust_indicators', 'safety_metrics']
            },
            'emotional_intelligence': {
                'description': 'Develop emotional awareness and regulation skills',
                'focus_areas': ['self_awareness', 'self_regulation', 'social_awareness', 'relationship_management'],
                'assessment_methods': ['sentiment_patterns', 'stress_indicators', 'empathy_scoring', 'relationship_quality']
            },
            'productivity_optimization': {
                'description': 'Improve personal and team productivity through behavioral optimization',
                'focus_areas': ['time_management', 'focus', 'prioritization', 'energy_management', 'workflow_optimization'],
                'assessment_methods': ['work_pattern_analysis', 'interruption_patterns', 'completion_rates', 'energy_levels']
            },
            'innovation_creativity': {
                'description': 'Foster innovative thinking and creative problem-solving',
                'focus_areas': ['creative_thinking', 'risk_taking', 'idea_generation', 'collaborative_innovation', 'psychological_safety'],
                'assessment_methods': ['idea_frequency', 'risk_assessment', 'innovation_participation', 'creative_collaboration']
            }
        }

        # Behavioral intervention strategies
        self.intervention_strategies = {
            'awareness_building': {
                'description': 'Build self-awareness through feedback and reflection',
                'techniques': ['360_feedback', 'behavioral_tracking', 'reflection_journals', 'coaching_conversations'],
                'timeline': '2-4 weeks',
                'success_indicators': ['increased_self_awareness', 'behavior_recognition', 'goal_setting']
            },
            'skill_development': {
                'description': 'Develop specific skills through training and practice',
                'techniques': ['targeted_training', 'practice_exercises', 'role_playing', 'mentoring'],
                'timeline': '4-8 weeks',
                'success_indicators': ['skill_mastery', 'behavior_change', 'confidence_increase']
            },
            'habit_formation': {
                'description': 'Form new positive habits through consistent practice',
                'techniques': ['habit_tracking', 'trigger_identification', 'environment_design', 'accountability_partners'],
                'timeline': '8-12 weeks',
                'success_indicators': ['habit_consistency', 'automatic_behavior', 'lasting_change']
            },
            'environmental_optimization': {
                'description': 'Optimize work environment to support desired behaviors',
                'techniques': ['workflow_redesign', 'tool_optimization', 'space_planning', 'process_improvement'],
                'timeline': '2-6 weeks',
                'success_indicators': ['reduced_barriers', 'increased_efficiency', 'behavior_support']
            }
        }

    async def generate_personalized_coaching_plan(
        self,
        db: Session,
        user_id: str,
        organization_id: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized coaching plan based on behavioral analysis
        """

        try:
            # Get user's behavioral data
            behavioral_data = await self._get_user_behavioral_data(
                db, user_id, organization_id
            )

            if not behavioral_data:
                return {
                    'error': 'Insufficient behavioral data for coaching recommendations',
                    'recommendations': []
                }

            # Analyze behavioral patterns and identify development areas
            development_areas = await self._analyze_development_areas(
                behavioral_data, focus_areas
            )

            # Generate specific coaching recommendations
            coaching_recommendations = await self._generate_coaching_recommendations(
                development_areas, behavioral_data
            )

            # Create personalized action plan
            action_plan = self._create_action_plan(coaching_recommendations)

            # Identify success metrics and tracking methods
            success_metrics = self._identify_success_metrics(
                development_areas, coaching_recommendations
            )

            # Get relevant resources and learning materials
            resources = await self._get_coaching_resources(
                development_areas, user_id
            )

            return {
                'user_id': user_id,
                'coaching_plan_generated': datetime.utcnow().isoformat(),
                'development_areas': development_areas,
                'coaching_recommendations': coaching_recommendations,
                'action_plan': action_plan,
                'success_metrics': success_metrics,
                'resources': resources,
                'coaching_duration': self._estimate_coaching_duration(coaching_recommendations),
                'expected_outcomes': self._predict_coaching_outcomes(coaching_recommendations)
            }

        except Exception as e:
            self.logger.error(f"Failed to generate coaching plan: {e}")
            return {
                'error': str(e),
                'recommendations': []
            }

    async def generate_team_coaching_plan(
        self,
        db: Session,
        team_id: str,
        organization_id: str,
        team_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate team-level coaching plan based on team dynamics analysis
        """

        try:
            # Get team behavioral data
            team_data = await self._get_team_behavioral_data(
                db, team_id, organization_id
            )

            if not team_data:
                return {
                    'error': 'Insufficient team data for coaching recommendations',
                    'recommendations': []
                }

            # Analyze team dynamics and identify improvement areas
            team_improvement_areas = await self._analyze_team_improvement_areas(
                team_data, team_focus
            )

            # Generate team coaching recommendations
            team_recommendations = await self._generate_team_coaching_recommendations(
                team_improvement_areas, team_data
            )

            # Create team action plan with individual roles
            team_action_plan = self._create_team_action_plan(
                team_recommendations, team_data.get('team_members', [])
            )

            # Identify team success metrics
            team_metrics = self._identify_team_success_metrics(
                team_improvement_areas, team_recommendations
            )

            # Get team resources and facilitation guides
            team_resources = await self._get_team_coaching_resources(
                team_improvement_areas
            )

            return {
                'team_id': team_id,
                'coaching_plan_generated': datetime.utcnow().isoformat(),
                'team_size': len(team_data.get('team_members', [])),
                'improvement_areas': team_improvement_areas,
                'team_recommendations': team_recommendations,
                'team_action_plan': team_action_plan,
                'success_metrics': team_metrics,
                'team_resources': team_resources,
                'facilitation_needs': self._identify_facilitation_needs(team_recommendations),
                'estimated_timeline': self._estimate_team_coaching_timeline(team_recommendations)
            }

        except Exception as e:
            self.logger.error(f"Failed to generate team coaching plan: {e}")
            return {
                'error': str(e),
                'recommendations': []
            }

    async def track_coaching_progress(
        self,
        db: Session,
        user_id: str,
        coaching_plan_id: str,
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track coaching progress and adjust recommendations
        """

        try:
            # Get original coaching plan
            coaching_plan = await self._get_coaching_plan(db, coaching_plan_id)

            if not coaching_plan:
                return {
                    'error': 'Coaching plan not found',
                    'progress_update': 'failed'
                }

            # Analyze progress data
            progress_analysis = self._analyze_coaching_progress(
                progress_data, coaching_plan
            )

            # Update recommendations based on progress
            updated_recommendations = await self._update_recommendations(
                coaching_plan, progress_analysis
            )

            # Generate progress report
            progress_report = self._generate_progress_report(
                coaching_plan, progress_analysis, updated_recommendations
            )

            # Store progress update
            await self._store_progress_update(
                db, user_id, coaching_plan_id, progress_data, progress_analysis
            )

            return {
                'progress_analysis': progress_analysis,
                'updated_recommendations': updated_recommendations,
                'progress_report': progress_report,
                'next_steps': self._generate_next_steps(progress_analysis),
                'motivation_message': self._generate_motivation_message(progress_analysis)
            }

        except Exception as e:
            self.logger.error(f"Failed to track coaching progress: {e}")
            return {
                'error': str(e),
                'progress_update': 'failed'
            }

    async def _get_user_behavioral_data(
        self,
        db: Session,
        user_id: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive behavioral data for user"""

        try:
            # Get user's role analysis
            role_analysis = db.query(TeamRoleAnalysis).filter(
                and_(
                    TeamRoleAnalysis.member_id == user_id,
                    TeamRoleAnalysis.organization_id == organization_id
                )
            ).all()

            # Get user's communication patterns
            comm_patterns = db.query(CommunicationPatterns).filter(
                and_(
                    CommunicationPatterns.user_id == user_id,
                    CommunicationPatterns.organization_id == organization_id
                )
            ).first()

            # Get any toxicity patterns involving user
            toxicity_patterns = db.query(ToxicityPattern).filter(
                and_(
                    ToxicityPattern.organization_id == organization_id,
                    ToxicityPattern.involved_anonymous_ids.contains([user_id])
                )
            ).all()

            # Get any interventions for user
            interventions = db.query(BehavioralIntervention).filter(
                and_(
                    BehavioralIntervention.assigned_to == user_id,
                    BehavioralIntervention.status.in_(['in_progress', 'planned'])
                )
            ).all()

            # Compile behavioral data
            behavioral_data = {
                'role_analyses': [self._serialize_role_analysis(ra) for ra in role_analysis],
                'communication_patterns': self._serialize_communication_patterns(comm_patterns),
                'toxicity_patterns': [self._serialize_toxicity_pattern(tp) for tp in toxicity_patterns],
                'interventions': [self._serialize_intervention(intervention) for intervention in interventions],
                'data_completeness': self._assess_data_completeness(role_analysis, comm_patterns)
            }

            return behavioral_data

        except Exception as e:
            self.logger.error(f"Failed to get user behavioral data: {e}")
            return {}

    async def _analyze_development_areas(
        self,
        behavioral_data: Dict[str, Any],
        focus_areas: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze behavioral data to identify development areas"""

        development_areas = []

        # Analyze communication patterns
        comm_patterns = behavioral_data.get('communication_patterns', {})
        if comm_patterns:
            # Check for communication issues
            avg_response_time = comm_patterns.get('avg_response_time', 0)
            sentiment_score = comm_patterns.get('avg_sentiment_score', 0)

            if avg_response_time > 480:  # > 8 hours
                development_areas.append({
                    'area': 'communication_responsiveness',
                    'severity': 'high',
                    'description': 'Slow response times affecting team collaboration',
                    'evidence': f'Average response time: {avg_response_time} minutes',
                    'impact_score': 0.7
                })

            if sentiment_score < -0.2:
                development_areas.append({
                    'area': 'communication_tone',
                    'severity': 'medium',
                    'description': 'Negative communication patterns detected',
                    'evidence': f'Average sentiment: {sentiment_score}',
                    'impact_score': 0.6
                })

        # Analyze role effectiveness
        role_analyses = behavioral_data.get('role_analyses', [])
        if role_analyses:
            latest_analysis = role_analyses[-1]  # Get most recent analysis
            role_effectiveness = latest_analysis.get('role_effectiveness_score', 0)
            influence_score = latest_analysis.get('influence_score', 0)

            if role_effectiveness < 3.0:
                development_areas.append({
                    'area': 'role_effectiveness',
                    'severity': 'high',
                    'description': 'Role effectiveness needs improvement',
                    'evidence': f'Role effectiveness score: {role_effectiveness}',
                    'impact_score': 0.8
                })

            if influence_score < 2.5:
                development_areas.append({
                    'area': 'leadership_influence',
                    'severity': 'medium',
                    'description': 'Limited influence on team decisions',
                    'evidence': f'Influence score: {influence_score}',
                    'impact_score': 0.6
                })

        # Analyze toxicity patterns
        toxicity_patterns = behavioral_data.get('toxicity_patterns', [])
        if toxicity_patterns:
            high_severity_patterns = [tp for tp in toxicity_patterns if tp.get('severity_level') in ['high', 'critical']]

            if high_severity_patterns:
                development_areas.append({
                    'area': 'behavioral_adjustment',
                    'severity': 'critical',
                    'description': 'Toxic behavior patterns detected requiring intervention',
                    'evidence': f'{len(high_severity_patterns)} high-severity patterns',
                    'impact_score': 0.9
                })

        # Filter by focus areas if specified
        if focus_areas:
            development_areas = [
                area for area in development_areas
                if any(focus in area['area'] for focus in focus_areas)
            ]

        # Sort by impact score
        development_areas.sort(key=lambda x: x['impact_score'], reverse=True)

        return development_areas

    async def _generate_coaching_recommendations(
        self,
        development_areas: List[Dict[str, Any]],
        behavioral_data: Dict[str, Any]
    ) -> List[CoachingRecommendation]:
        """Generate specific coaching recommendations"""

        recommendations = []

        for area in development_areas:
            area_name = area['area']
            severity = area['severity']

            # Generate specific recommendations based on area
            if area_name == 'communication_responsiveness':
                recommendations.append(CoachingRecommendation(
                    category='communication_excellence',
                    priority=severity,
                    title='Improve Response Time Management',
                    description='Develop better email and communication response habits',
                    action_steps=[
                        'Set specific times for checking and responding to messages',
                        'Use auto-responder for managing expectations',
                        'Prioritize messages by urgency and importance',
                        'Create templates for common responses'
                    ],
                    expected_outcomes=[
                        'Reduce average response time by 50%',
                        'Improve team collaboration efficiency',
                        'Reduce communication bottlenecks'
                    ],
                    timeline='4 weeks',
                    resources=[
                        'Time management training modules',
                        'Email productivity tools guide',
                        'Communication best practices checklist'
                    ]
                ))

            elif area_name == 'communication_tone':
                recommendations.append(CoachingRecommendation(
                    category='emotional_intelligence',
                    priority=severity,
                    title='Enhance Communication Tone and Emotional Intelligence',
                    description='Develop more positive and constructive communication patterns',
                    action_steps=[
                        'Practice constructive feedback techniques',
                        'Develop emotional awareness before responding',
                        'Use the "pause and reflect" method',
                        'Learn positive reframing techniques'
                    ],
                    expected_outcomes=[
                        'Improve sentiment scores by 30%',
                        'Reduce negative communication incidents',
                        'Enhance team psychological safety'
                    ],
                    timeline='6 weeks',
                    resources=[
                        'Emotional intelligence assessment',
                        'Constructive communication workshop',
                        'Positive psychology exercises'
                    ]
                ))

            elif area_name == 'role_effectiveness':
                recommendations.append(CoachingRecommendation(
                    category='leadership_development',
                    priority=severity,
                    title='Strengthen Role Performance and Impact',
                    description='Improve effectiveness in current role through skill development',
                    action_steps=[
                        'Identify key skills for role success',
                        'Create personal development plan',
                        'Seek mentorship from high-performers',
                        'Practice role-specific scenarios'
                    ],
                    expected_outcomes=[
                        'Increase role effectiveness score by 1.0 points',
                        'Improve team contribution visibility',
                        'Enhance career development prospects'
                    ],
                    timeline='8 weeks',
                    resources=[
                        'Role-specific competency framework',
                        'Skills assessment tools',
                        'Mentorship matching program'
                    ]
                ))

            elif area_name == 'leadership_influence':
                recommendations.append(CoachingRecommendation(
                    category='leadership_development',
                    priority=severity,
                    title='Develop Leadership Influence and Impact',
                    description='Build skills to influence team decisions and direction',
                    action_steps=[
                        'Study influence and persuasion techniques',
                        'Practice leading small projects',
                        'Develop strategic thinking skills',
                        'Build cross-functional relationships'
                    ],
                    expected_outcomes=[
                        'Increase influence score by 1.5 points',
                        'Successfully lead team initiatives',
                        'Improve decision-making contribution'
                    ],
                    timeline='10 weeks',
                    resources=[
                        'Leadership development program',
                        'Influence and persuasion workshops',
                        'Strategic thinking training'
                    ]
                ))

            elif area_name == 'behavioral_adjustment':
                recommendations.append(CoachingRecommendation(
                    category='emotional_intelligence',
                    priority=severity,
                    title='Behavioral Adjustment and Interpersonal Skills',
                    description='Address problematic behavioral patterns through targeted intervention',
                    action_steps=[
                        'Participate in behavioral coaching program',
                        'Develop self-awareness through feedback',
                        'Practice new communication patterns',
                        'Build empathy and perspective-taking skills'
                    ],
                    expected_outcomes=[
                        'Eliminate toxic behavior patterns',
                        'Improve interpersonal relationships',
                        'Enhance team collaboration'
                    ],
                    timeline='12 weeks',
                    resources=[
                        'Professional behavioral coaching',
                        'Conflict resolution training',
                        'Emotional intelligence intensive'
                    ]
                ))

        return recommendations

    def _create_action_plan(
        self,
        recommendations: List[CoachingRecommendation]
    ) -> Dict[str, Any]:
        """Create structured action plan from recommendations"""

        if not recommendations:
            return {}

        # Sort recommendations by priority and timeline
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_recommendations = sorted(
            recommendations,
            key=lambda r: (priority_order.get(r.priority, 3), r.timeline)
        )

        # Create weekly action plan
        action_plan = {
            'overall_timeline': self._calculate_overall_timeline(recommendations),
            'weekly_breakdown': [],
            'milestones': [],
            'checkpoints': []
        }

        current_week = 1
        for rec in sorted_recommendations:
            # Estimate duration in weeks
            duration_weeks = self._estimate_duration_in_weeks(rec.timeline)

            # Add weekly actions
            for week in range(duration_weeks):
                action_plan['weekly_breakdown'].append({
                    'week': current_week + week,
                    'recommendation': rec.title,
                    'category': rec.category,
                    'priority': rec.priority,
                    'actions': rec.action_steps[:2] if week == 0 else rec.action_steps[2:],
                    'focus_area': rec.description
                })

            # Add milestone
            action_plan['milestones'].append({
                'week': current_week + duration_weeks,
                'milestone': f"Complete {rec.title}",
                'category': rec.category,
                'expected_outcomes': rec.expected_outcomes
            })

            current_week += duration_weeks

        # Add regular checkpoints
        checkpoint_weeks = [2, 4, 8, 12]
        for week in checkpoint_weeks:
            if week <= current_week:
                action_plan['checkpoints'].append({
                    'week': week,
                    'activities': [
                        'Review progress against goals',
                        'Adjust action plan as needed',
                        'Gather feedback from stakeholders'
                    ]
                })

        return action_plan

    def _identify_success_metrics(
        self,
        development_areas: List[Dict[str, Any]],
        recommendations: List[CoachingRecommendation]
    ) -> List[Dict[str, Any]]:
        """Identify metrics to track coaching success"""

        success_metrics = []

        for area in development_areas:
            area_name = area['area']

            if area_name == 'communication_responsiveness':
                success_metrics.append({
                    'metric': 'Average Response Time',
                    'current_value': area.get('evidence', ''),
                    'target_value': '50% reduction',
                    'measurement_method': 'Communication pattern analysis',
                    'frequency': 'weekly',
                    'success_criteria': '< 4 hours average response time'
                })

            elif area_name == 'communication_tone':
                success_metrics.append({
                    'metric': 'Communication Sentiment Score',
                    'current_value': area.get('evidence', ''),
                    'target_value': '0.3 improvement',
                    'measurement_method': 'Sentiment analysis',
                    'frequency': 'weekly',
                    'success_criteria': 'Sentiment score > -0.1'
                })

            elif area_name == 'role_effectiveness':
                success_metrics.append({
                    'metric': 'Role Effectiveness Score',
                    'current_value': area.get('evidence', ''),
                    'target_value': '1.0 point improvement',
                    'measurement_method': 'Role analysis assessment',
                    'frequency': 'monthly',
                    'success_criteria': 'Score > 4.0'
                })

            elif area_name == 'leadership_influence':
                success_metrics.append({
                    'metric': 'Leadership Influence Score',
                    'current_value': area.get('evidence', ''),
                    'target_value': '1.5 point improvement',
                    'measurement_method': 'Network and influence analysis',
                    'frequency': 'monthly',
                    'success_criteria': 'Score > 4.0'
                })

        # Add qualitative metrics
        success_metrics.extend([
            {
                'metric': 'Peer Feedback Scores',
                'current_value': 'To be established',
                'target_value': '20% improvement',
                'measurement_method': '360-degree feedback',
                'frequency': 'quarterly',
                'success_criteria': 'Average rating > 4.0'
            },
            {
                'metric': 'Self-Reported Confidence',
                'current_value': 'To be established',
                'target_value': 'Significant increase',
                'measurement_method': 'Self-assessment surveys',
                'frequency': 'monthly',
                'success_criteria': 'Confidence level > 80%'
            }
        ])

        return success_metrics

    async def _get_coaching_resources(
        self,
        development_areas: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get relevant coaching resources and learning materials"""

        resources = []

        for area in development_areas:
            area_name = area['area']

            if area_name in ['communication_responsiveness', 'communication_tone']:
                resources.extend([
                    {
                        'type': 'online_course',
                        'title': 'Effective Communication in the Workplace',
                        'provider': 'LinkedIn Learning',
                        'duration': '3 hours',
                        'description': 'Master workplace communication skills',
                        'url': '#communication-course'
                    },
                    {
                        'type': 'article',
                        'title': '10 Ways to Improve Your Email Response Time',
                        'provider': 'Harvard Business Review',
                        'duration': '5 min read',
                        'description': 'Practical tips for faster email responses',
                        'url': '#email-tips'
                    }
                ])

            elif area_name in ['role_effectiveness', 'leadership_influence']:
                resources.extend([
                    {
                        'type': 'workshop',
                        'title': 'Leadership Excellence Program',
                        'provider': 'Internal L&D',
                        'duration': '2 days',
                        'description': 'Comprehensive leadership development',
                        'url': '#leadership-workshop'
                    },
                    {
                        'type': 'book',
                        'title': 'The 7 Habits of Highly Effective People',
                        'author': 'Stephen Covey',
                        'duration': '8-10 hours reading',
                        'description': 'Classic leadership and personal effectiveness',
                        'url': '#7habits'
                    }
                ])

            elif area_name == 'behavioral_adjustment':
                resources.extend([
                    {
                        'type': 'coaching_program',
                        'title': 'Behavioral Coaching Intensive',
                        'provider': 'Professional Coach Network',
                        'duration': '12 weeks',
                        'description': 'One-on-one behavioral coaching',
                        'url': '#behavioral-coaching'
                    },
                    {
                        'type': 'assessment',
                        'title': 'Emotional Intelligence Assessment',
                        'provider': 'PsychSync Platform',
                        'duration': '30 minutes',
                        'description': 'Comprehensive EQ evaluation',
                        'url': '#eq-assessment'
                    }
                ])

        # Add general resources
        resources.extend([
            {
                'type': 'podcast',
                'title': 'The Psychology of Performance',
                'provider': 'Various',
                'duration': 'Ongoing series',
                'description': 'Weekly insights on workplace psychology',
                'url': '#psychology-podcast'
            },
            {
                'type': 'tool',
                'title': 'Habit Tracking App',
                'provider': 'PsychSync Platform',
                'duration': 'Daily use',
                'description': 'Track progress on coaching goals',
                'url': '#habit-tracker'
            }
        ])

        return resources

    def _estimate_coaching_duration(self, recommendations: List[CoachingRecommendation]) -> str:
        """Estimate total coaching duration based on recommendations"""

        if not recommendations:
            return "Not applicable"

        total_weeks = 0
        for rec in recommendations:
            total_weeks += self._estimate_duration_in_weeks(rec.timeline)

        if total_weeks <= 4:
            return f"{total_weeks} weeks"
        elif total_weeks <= 12:
            return f"{total_weeks} weeks ({total_weeks//4} months)"
        else:
            months = total_weeks // 4
            return f"{months}+ months"

    def _predict_coaching_outcomes(self, recommendations: List[CoachingRecommendation]) -> List[str]:
        """Predict likely outcomes from coaching recommendations"""

        outcomes = []

        if any(rec.category == 'communication_excellence' for rec in recommendations):
            outcomes.append("Improved communication clarity and effectiveness")
            outcomes.append("Reduced misunderstandings and conflicts")

        if any(rec.category == 'leadership_development' for rec in recommendations):
            outcomes.append("Enhanced leadership capabilities and team influence")
            outcomes.append("Improved decision-making and strategic thinking")

        if any(rec.category == 'emotional_intelligence' for rec in recommendations):
            outcomes.append("Better emotional regulation and self-awareness")
            outcomes.append("Stronger interpersonal relationships")

        if any(rec.category == 'team_collaboration' for rec in recommendations):
            outcomes.append("More effective teamwork and collaboration")
            outcomes.append("Improved team psychological safety")

        # Add general outcomes
        outcomes.extend([
            "Increased self-awareness and personal growth",
            "Better performance and productivity",
            "Enhanced career development prospects"
        ])

        return list(set(outcomes))  # Remove duplicates

    def _serialize_role_analysis(self, role_analysis) -> Dict[str, Any]:
        """Serialize role analysis object for processing"""
        return {
            'primary_role': role_analysis.primary_role,
            'role_effectiveness_score': float(role_analysis.role_effectiveness_score or 0),
            'influence_score': float(role_analysis.influence_score or 0),
            'psychological_safety_contribution': float(role_analysis.psychological_safety_contribution or 0)
        }

    def _serialize_communication_patterns(self, comm_patterns) -> Dict[str, Any]:
        """Serialize communication patterns for processing"""
        if not comm_patterns:
            return {}

        return {
            'avg_response_time': float(comm_patterns.avg_response_time or 0),
            'avg_sentiment_score': float(comm_patterns.sentiment_score or 0),
            'communication_frequency': float(comm_patterns.communication_frequency or 0)
        }

    def _serialize_toxicity_pattern(self, toxicity_pattern) -> Dict[str, Any]:
        """Serialize toxicity pattern for processing"""
        return {
            'pattern_type': toxicity_pattern.pattern_type,
            'severity_level': toxicity_pattern.severity_level,
            'confidence_score': float(toxicity_pattern.confidence_score),
            'frequency_score': float(toxicity_pattern.frequency_score or 0)
        }

    def _serialize_intervention(self, intervention) -> Dict[str, Any]:
        """Serialize intervention for processing"""
        return {
            'intervention_type': intervention.intervention_type,
            'status': intervention.status,
            'effectiveness_rating': float(intervention.effectiveness_rating or 0)
        }

    def _assess_data_completeness(self, role_analyses, comm_patterns) -> str:
        """Assess completeness of available behavioral data"""
        has_role_data = len(role_analyses) > 0
        has_comm_data = comm_patterns is not None

        if has_role_data and has_comm_data:
            return "high"
        elif has_role_data or has_comm_data:
            return "medium"
        else:
            return "low"

    def _estimate_duration_in_weeks(self, timeline: str) -> int:
        """Convert timeline string to weeks"""
        timeline_lower = timeline.lower()

        if 'week' in timeline_lower:
            if '2-4' in timeline_lower or '4' in timeline_lower:
                return 4
            elif '4-8' in timeline_lower or '6' in timeline_lower:
                return 6
            elif '8-12' in timeline_lower or '10' in timeline_lower:
                return 10
            elif '12' in timeline_lower:
                return 12
            else:
                return 4
        elif 'month' in timeline_lower:
            if '1' in timeline_lower:
                return 4
            elif '2' in timeline_lower:
                return 8
            elif '3' in timeline_lower:
                return 12
            else:
                return 8
        else:
            return 4  # Default

    def _calculate_overall_timeline(self, recommendations: List[CoachingRecommendation]) -> str:
        """Calculate overall timeline for all recommendations"""
        total_weeks = sum(self._estimate_duration_in_weeks(rec.timeline) for rec in recommendations)

        if total_weeks <= 4:
            return f"{total_weeks} weeks"
        elif total_weeks <= 12:
            months = total_weeks // 4
            return f"{months} months"
        else:
            months = (total_weeks + 2) // 4  # Round up
            return f"{months}+ months"

# Singleton instance
behavioral_coaching_service = BehavioralCoachingService()