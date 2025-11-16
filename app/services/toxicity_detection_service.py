# app/services/toxicity_detection_service.py
"""
Toxicity Detection and Behavioral Analysis Service
Uses AI and behavioral psychology to identify workplace toxicity patterns
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func

from app.db.models.toxicity_detection import ToxicityPattern, ToxicityType, ToxicityLevel
from app.db.models.communication_analysis import CommunicationAnalysis
from app.db.models.communication_patterns import CommunicationPatterns
from app.services.free_nlp_service import free_nlp_service
from app.core.logging_config import logger

@dataclass
class ToxicityIndicator:
    """Individual indicator of toxic behavior"""
    indicator_type: str
    description: str
    severity: float
    confidence: float
    evidence: List[str]

class ToxicityDetectionService:
    """Advanced toxicity detection using behavioral psychology and AI"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Toxicity patterns and keywords
        self.toxicity_patterns = {
            ToxicityType.VERBAL_ABUSE: {
                'keywords': ['stupid', 'idiot', 'useless', 'incompetent', 'worthless'],
                'patterns': [
                    r'you.*always.*negative',
                    r'you.*never.*positive',
                    r'what.*wrong.*with.*you'
                ],
                'behavioral_signs': ['personal_attacks', 'name_calling', 'belittling']
            },
            ToxicityType.BULLYING: {
                'keywords': ['bully', 'intimidate', 'threaten', 'pressure'],
                'patterns': [
                    r'if.*you.*don\'t.*will.*consequences',
                    r'everyone.*agrees.*with.*me',
                    r'no.*one.*likes.*you'
                ],
                'behavioral_signs': ['power_imbalance', 'social_exclusion', 'repeated_targeting']
            },
            ToxicityType.MICROMANAGEMENT: {
                'keywords': ['every.*step', 'constant.*check', 'supervise.*everything'],
                'patterns': [
                    r'need.*to.*approve.*everything',
                    r'can\'t.*trust.*you.*with.*this',
                    r'must.*copy.*me.*on.*everything'
                ],
                'behavioral_signs': ['excessive_control', 'lack_trust', 'detailed_monitoring']
            },
            ToxicityType.PASSIVE_AGGRESSIVE: {
                'keywords': ['fine', 'whatever', 'sure', 'interesting'],
                'patterns': [
                    r'as.*I.*said.*before',
                    r'if.*you.*think.*that\'s.*best',
                    r'interesting.*choice'
                ],
                'behavioral_signs': ['sarcasm', 'indirect_hostility', 'backhanded_compliments']
            },
            ToxicityType.EXCLUSION: {
                'keywords': ['not.*invited', 'left.*out', 'excluded', 'not.*part'],
                'patterns': [
                    r'we.*decided.*without.*you',
                    r'you.*weren\'t.*there',
                    r'team.*meeting.*you.*missed'
                ],
                'behavioral_signs': ['social_exclusion', 'information_withholding', 'deliberate_omission']
            }
        }

    async def analyze_team_toxicity(
        self,
        db: Session,
        organization_id: str,
        team_id: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Comprehensive toxicity analysis for team or organization"""

        try:
            # Get communication data for the period
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)

            # Fetch communication analyses
            communications = db.query(CommunicationAnalysis).filter(
                and_(
                    CommunicationAnalysis.organization_id == organization_id,
                    CommunicationAnalysis.analyzed_at >= cutoff_date
                )
            )

            if team_id:
                communications = communications.filter(
                    CommunicationAnalysis.team_id == team_id
                )

            communications = communications.all()

            if not communications:
                return {
                    'toxicity_level': ToxicityLevel.NONE,
                    'patterns_detected': [],
                    'risk_factors': [],
                    'recommendations': [],
                    'data_insufficient': True
                }

            # Analyze for toxicity patterns
            toxicity_analysis = await self._analyze_toxicity_patterns(communications)

            # Analyze behavioral indicators
            behavioral_analysis = self._analyze_behavioral_indicators(communications)

            # Calculate overall toxicity risk
            overall_risk = self._calculate_toxicity_risk(
                toxicity_analysis, behavioral_analysis
            )

            # Generate recommendations
            recommendations = self._generate_toxicity_recommendations(
                overall_risk, toxicity_analysis, behavioral_analysis
            )

            # Store toxicity patterns if high risk detected
            if overall_risk['risk_score'] > 0.3:
                await self._store_toxicity_patterns(
                    db, organization_id, team_id, toxicity_analysis, overall_risk
                )

            return {
                'toxicity_level': overall_risk['toxicity_level'],
                'risk_score': overall_risk['risk_score'],
                'patterns_detected': toxicity_analysis['patterns'],
                'behavioral_indicators': behavioral_analysis,
                'risk_factors': overall_risk['risk_factors'],
                'recommendations': recommendations,
                'data_insufficient': False,
                'analysis_period_days': period_days,
                'communications_analyzed': len(communications)
            }

        except Exception as e:
            self.logger.error(f"Toxicity analysis failed: {e}")
            return {
                'toxicity_level': ToxicityLevel.NONE,
                'error': str(e),
                'data_insufficient': True
            }

    async def _analyze_toxicity_patterns(
        self,
        communications: List[CommunicationAnalysis]
    ) -> Dict[str, Any]:
        """Analyze communications for specific toxicity patterns"""

        detected_patterns = []
        pattern_frequencies = defaultdict(int)

        for comm in communications:
            # Get text for analysis (subject and any preview text)
            text_to_analyze = comm.subject or ""

            # Add sentiment context
            if comm.sentiment_data:
                sentiment = comm.sentiment_data.get('sentiment', {})
                if sentiment.get('negative', 0) > 0.6:
                    # High negative sentiment - check for toxicity patterns
                    patterns = await self._detect_toxicity_in_text(text_to_analyze)
                    for pattern in patterns:
                        pattern_frequencies[pattern['type']] += 1
                        detected_patterns.append({
                            'communication_id': str(comm.id),
                            'pattern': pattern,
                            'confidence': pattern['confidence'],
                            'evidence': pattern['evidence']
                        })

        # Analyze patterns for frequency and severity
        significant_patterns = []
        for pattern_type, frequency in pattern_frequencies.items():
            if frequency >= 2:  # Pattern appears multiple times
                severity_score = min(frequency * 0.2, 1.0)  # Scale severity by frequency

                significant_patterns.append({
                    'type': pattern_type,
                    'frequency': frequency,
                    'severity_score': severity_score,
                    'pattern_definition': self.toxicity_patterns.get(pattern_type, {}),
                    'detection_confidence': min(frequency / len(communications), 1.0)
                })

        return {
            'patterns': significant_patterns,
            'total_patterns': len(significant_patterns),
            'pattern_diversity': len(set(p['type'] for p in significant_patterns)),
            'high_frequency_patterns': [p for p in significant_patterns if p['frequency'] >= 3]
        }

    async def _detect_toxicity_in_text(self, text: str) -> List[Dict[str, Any]]:
        """Detect specific toxicity patterns in text"""

        detected_patterns = []
        text_lower = text.lower()

        for toxicity_type, pattern_config in self.toxicity_patterns.items():
            # Check keywords
            keyword_matches = []
            for keyword in pattern_config['keywords']:
                if keyword in text_lower:
                    keyword_matches.append(keyword)

            # Check regex patterns
            pattern_matches = []
            for pattern in pattern_config['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    pattern_matches.append(pattern)

            # If matches found, create toxicity indicator
            if keyword_matches or pattern_matches:
                confidence = min(
                    (len(keyword_matches) * 0.3 + len(pattern_matches) * 0.7),
                    1.0
                )

                evidence = []
                if keyword_matches:
                    evidence.append(f"Keywords: {', '.join(keyword_matches)}")
                if pattern_matches:
                    evidence.append(f"Patterns: {', '.join(pattern_matches)}")

                detected_patterns.append({
                    'type': toxicity_type,
                    'confidence': confidence,
                    'evidence': evidence,
                    'keyword_matches': keyword_matches,
                    'pattern_matches': pattern_matches
                })

        return detected_patterns

    def _analyze_behavioral_indicators(
        self,
        communications: List[CommunicationAnalysis]
    ) -> Dict[str, Any]:
        """Analyze behavioral indicators of toxicity"""

        if not communications:
            return {}

        # Aggregate behavioral metrics
        total_sentiments = defaultdict(float)
        total_emotions = defaultdict(float)
        behavioral_metrics = defaultdict(list)

        negative_communications = 0
        high_stress_communications = 0
        conflict_indicators = 0

        for comm in communications:
            # Sentiment analysis
            if comm.sentiment_data:
                sentiment = comm.sentiment_data.get('sentiment', {})
                for key, value in sentiment.items():
                    total_sentiments[key] += value

                if sentiment.get('negative', 0) > 0.6:
                    negative_communications += 1

            # Emotion analysis
            if comm.emotion_data:
                emotions = comm.emotion_data.get('emotions', {})
                for key, value in emotions.items():
                    total_emotions[key] += value

            # Behavioral indicators
            if comm.behavioral_data:
                behavioral = comm.behavioral_data.get('behavioral_indicators', {})
                for key, value in behavioral.items():
                    behavioral_metrics[key].append(value)

                if behavioral.get('stress_level', 0) > 0.7:
                    high_stress_communications += 1

                if behavioral.get('conflict_probability', 0) > 0.6:
                    conflict_indicators += 1

        # Calculate averages and identify concerning patterns
        avg_sentiments = {k: v / len(communications) for k, v in total_sentiments.items()}
        avg_emotions = {k: v / len(communications) for k, v in total_emotions.items()}

        # Calculate behavioral averages
        avg_behavioral = {}
        for key, values in behavioral_metrics.items():
            if values:
                avg_behavioral[key] = sum(values) / len(values)

        # Identify concerning indicators
        concerning_indicators = []
        if avg_sentiments.get('negative', 0) > 0.3:
            concerning_indicators.append({
                'type': 'high_negativity',
                'description': 'Elevated negative sentiment in communications',
                'severity': avg_sentiments['negative']
            })

        if high_stress_communications / len(communications) > 0.2:
            concerning_indicators.append({
                'type': 'high_stress',
                'description': 'High stress levels detected in communications',
                'severity': high_stress_communications / len(communications)
            })

        if conflict_indicators / len(communications) > 0.15:
            concerning_indicators.append({
                'type': 'conflict_indicators',
                'description': 'Frequent conflict indicators in communication patterns',
                'severity': conflict_indicators / len(communications)
            })

        return {
            'average_sentiments': avg_sentiments,
            'average_emotions': avg_emotions,
            'behavioral_averages': avg_behavioral,
            'concerning_indicators': concerning_indicators,
            'negative_communication_ratio': negative_communications / len(communications),
            'high_stress_ratio': high_stress_communications / len(communications),
            'conflict_indicator_ratio': conflict_indicators / len(communications)
        }

    def _calculate_toxicity_risk(
        self,
        toxicity_analysis: Dict[str, Any],
        behavioral_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall toxicity risk score"""

        risk_factors = []
        risk_score = 0.0

        # Pattern-based risk
        if toxicity_analysis.get('patterns'):
            pattern_severity = sum(p['severity_score'] for p in toxicity_analysis['patterns'])
            pattern_risk = min(pattern_severity / len(toxicity_analysis['patterns']), 1.0)
            risk_score += pattern_risk * 0.4

            if pattern_risk > 0.3:
                risk_factors.append({
                    'type': 'toxicity_patterns',
                    'description': f"Detected {len(toxicity_analysis['patterns'])} toxicity patterns",
                    'severity': pattern_risk
                })

        # Behavioral risk
        if behavioral_analysis:
            neg_ratio = behavioral_analysis.get('negative_communication_ratio', 0)
            stress_ratio = behavioral_analysis.get('high_stress_ratio', 0)
            conflict_ratio = behavioral_analysis.get('conflict_indicator_ratio', 0)

            behavioral_risk = (neg_ratio + stress_ratio + conflict_ratio) / 3
            risk_score += behavioral_risk * 0.4

            if behavioral_risk > 0.3:
                risk_factors.append({
                    'type': 'behavioral_indicators',
                    'description': 'Elevated negative behavioral indicators',
                    'severity': behavioral_risk
                })

        # Communication quality risk
        concerning_indicators = behavioral_analysis.get('concerning_indicators', [])
        if concerning_indicators:
            indicator_risk = len(concerning_indicators) * 0.2
            risk_score += min(indicator_risk, 0.2) * 0.2

        # Normalize final risk score
        final_risk_score = min(risk_score, 1.0)

        # Determine toxicity level
        if final_risk_score >= 0.8:
            toxicity_level = ToxicityLevel.CRITICAL
        elif final_risk_score >= 0.6:
            toxicity_level = ToxicityLevel.HIGH
        elif final_risk_score >= 0.4:
            toxicity_level = ToxicityLevel.MEDIUM
        elif final_risk_score >= 0.2:
            toxicity_level = ToxicityLevel.LOW
        else:
            toxicity_level = ToxicityLevel.NONE

        return {
            'toxicity_level': toxicity_level,
            'risk_score': round(final_risk_score, 4),
            'risk_factors': risk_factors,
            'pattern_risk': pattern_risk if toxicity_analysis.get('patterns') else 0,
            'behavioral_risk': behavioral_risk if behavioral_analysis else 0
        }

    def _generate_toxicity_recommendations(
        self,
        overall_risk: Dict[str, Any],
        toxicity_analysis: Dict[str, Any],
        behavioral_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate specific recommendations based on toxicity analysis"""

        recommendations = []

        # Pattern-specific recommendations
        patterns = toxicity_analysis.get('patterns', [])
        pattern_types = set(p['type'] for p in patterns)

        if ToxicityType.VERBAL_ABUSE in pattern_types:
            recommendations.append({
                'priority': 'high',
                'category': 'communication_training',
                'title': 'Implement Professional Communication Training',
                'description': 'Address verbal abuse through targeted communication and conflict resolution training',
                'actions': [
                    'Conduct mandatory respectful workplace communication training',
                    'Implement clear communication guidelines',
                    'Establish zero-tolerance policy for verbal abuse'
                ],
                'timeline': '2-4 weeks'
            })

        if ToxicityType.BULLYING in pattern_types:
            recommendations.append({
                'priority': 'critical',
                'category': 'anti_bullying',
                'title': 'Immediate Anti-Bullying Intervention Required',
                'description': 'Bullying patterns detected - immediate intervention needed',
                'actions': [
                    'Launch formal investigation',
                    'Provide support to affected individuals',
                    'Implement comprehensive anti-bullying program',
                    'Consider temporary team restructuring'
                ],
                'timeline': '1-2 weeks'
            })

        if ToxicityType.MICROMANAGEMENT in pattern_types:
            recommendations.append({
                'priority': 'medium',
                'category': 'leadership_development',
                'title': 'Leadership and Trust Building Training',
                'description': 'Address micromanagement through leadership development',
                'actions': [
                    'Provide leadership training for managers',
                    'Implement clear delegation guidelines',
                    'Establish regular feedback mechanisms',
                    'Promote autonomy and trust culture'
                ],
                'timeline': '4-6 weeks'
            })

        # Behavioral indicator recommendations
        behavioral_risk = overall_risk.get('behavioral_risk', 0)
        if behavioral_risk > 0.4:
            recommendations.append({
                'priority': 'medium',
                'category': 'team_wellness',
                'title': 'Team Wellness and Stress Management',
                'description': 'High stress levels detected - implement wellness initiatives',
                'actions': [
                    'Conduct stress management workshops',
                    'Implement regular check-ins',
                    'Provide access to counseling resources',
                    'Review workload and deadlines'
                ],
                'timeline': '3-4 weeks'
            })

        # General recommendations based on overall risk
        if overall_risk['toxicity_level'] in [ToxicityLevel.HIGH, ToxicityLevel.CRITICAL]:
            recommendations.append({
                'priority': 'critical',
                'category': 'organizational_intervention',
                'title': 'Comprehensive Culture Intervention Required',
                'description': 'Critical toxicity level detected - immediate organizational intervention needed',
                'actions': [
                    'Engage external workplace culture consultants',
                    'Conduct anonymous climate survey',
                    'Implement temporary mediation processes',
                    'Consider leadership changes'
                ],
                'timeline': '1-3 weeks'
            })

        return recommendations

    async def _store_toxicity_patterns(
        self,
        db: Session,
        organization_id: str,
        team_id: Optional[str],
        toxicity_analysis: Dict[str, Any],
        overall_risk: Dict[str, Any]
    ) -> None:
        """Store detected toxicity patterns for tracking and intervention"""

        try:
            for pattern in toxicity_analysis.get('patterns', []):
                # Check if similar pattern already exists recently
                existing_pattern = db.query(ToxicityPattern).filter(
                    and_(
                        ToxicityPattern.organization_id == organization_id,
                        ToxicityPattern.team_id == team_id,
                        ToxicityPattern.pattern_type == pattern['type'],
                        ToxicityPattern.detection_date >= datetime.utcnow().date() - timedelta(days=7)
                    )
                ).first()

                if existing_pattern:
                    # Update existing pattern
                    existing_pattern.frequency_score = max(
                        existing_pattern.frequency_score, pattern['frequency']
                    )
                    existing_pattern.severity_level = max(
                        existing_pattern.severity_level,
                        self._severity_from_score(pattern['severity_score'])
                    )
                    existing_pattern.confidence_score = max(
                        existing_pattern.confidence_score,
                        pattern['detection_confidence']
                    )
                else:
                    # Create new pattern record
                    toxicity_pattern = ToxicityPattern(
                        organization_id=organization_id,
                        team_id=team_id,
                        pattern_type=pattern['type'],
                        severity_level=self._severity_from_score(pattern['severity_score']),
                        confidence_score=pattern['detection_confidence'],
                        behavioral_indicators=pattern.get('pattern_definition', {}).get('behavioral_signs', []),
                        frequency_score=pattern['frequency'],
                        detection_date=datetime.utcnow().date(),
                        status='detected',
                        intervention_required=overall_risk['risk_score'] > 0.5,
                        evidence_summary=f"Pattern detected {pattern['frequency']} times with {pattern['severity_score']:.2f} severity"
                    )

                    db.add(toxicity_pattern)
        await db.commit()

        except Exception as e:
            self.logger.error(f"Failed to store toxicity patterns: {e}")
            await db.rollback()

    def _severity_from_score(self, score: float) -> str:
        """Convert numeric severity score to severity level"""
        if score >= 0.8:
            return ToxicityLevel.CRITICAL
        elif score >= 0.6:
            return ToxicityLevel.HIGH
        elif score >= 0.4:
            return ToxicityLevel.MEDIUM
        elif score >= 0.2:
            return ToxicityLevel.LOW
        else:
            return ToxicityLevel.NONE

    def get_toxicity_trends(
        self,
        db: Session,
        organization_id: str,
        team_id: Optional[str] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Get toxicity trends and patterns over time"""

        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=days_back)

            query = db.query(ToxicityPattern).filter(
                and_(
                    ToxicityPattern.organization_id == organization_id,
                    ToxicityPattern.detection_date >= cutoff_date
                )
            )

            if team_id:
                query = query.filter(ToxicityPattern.team_id == team_id)

            patterns = query.order_by(ToxicityPattern.detection_date.desc()).all()

            if not patterns:
                return {
                    'trend_data': [],
                    'summary': {
                        'total_patterns': 0,
                        'current_risk_level': ToxicityLevel.NONE,
                        'trend_direction': 'stable'
                    }
                }

            # Group by date and severity
            daily_data = defaultdict(lambda: {'count': 0, 'severities': []})

            for pattern in patterns:
                date_key = pattern.detection_date.isoformat()
                daily_data[date_key]['count'] += 1
                daily_data[date_key]['severities'].append(pattern.severity_level)

            # Convert to trend data
            trend_data = []
            for date_str, data in sorted(daily_data.items()):
                severity_counts = Counter(data['severities'])
                trend_data.append({
                    'date': date_str,
                    'pattern_count': data['count'],
                    'severity_breakdown': dict(severity_counts),
                    'critical_patterns': severity_counts.get(ToxicityLevel.CRITICAL, 0),
                    'high_patterns': severity_counts.get(ToxicityLevel.HIGH, 0)
                })

            # Calculate trend direction
            if len(trend_data) >= 2:
                recent_avg = trend_data[-7:]['pattern_count'] if len(trend_data) >= 7 else [p['pattern_count'] for p in trend_data[-3:]]
                earlier_avg = trend_data[-14:-7]['pattern_count'] if len(trend_data) >= 14 else [p['pattern_count'] for p in trend_data[-8:-4]]

                recent_avg = sum(recent_avg) / len(recent_avg) if recent_avg else 0
                earlier_avg = sum(earlier_avg) / len(earlier_avg) if earlier_avg else 0

                if recent_avg > earlier_avg * 1.2:
                    trend_direction = 'increasing'
                elif recent_avg < earlier_avg * 0.8:
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'insufficient_data'

            # Determine current risk level
            recent_patterns = [p for p in patterns if (datetime.utcnow().date() - p.detection_date).days <= 7]
            if recent_patterns:
                max_severity = max(p.severity_level for p in recent_patterns)
                current_risk_level = max_severity
            else:
                current_risk_level = ToxicityLevel.NONE

            return {
                'trend_data': trend_data,
                'summary': {
                    'total_patterns': len(patterns),
                    'current_risk_level': current_risk_level,
                    'trend_direction': trend_direction,
                    'most_common_type': Counter([p.pattern_type for p in patterns]).most_common(1)[0] if patterns else None,
                    'patterns_requiring_intervention': len([p for p in patterns if p.intervention_required])
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get toxicity trends: {e}")
            return {
                'trend_data': [],
                'summary': {
                    'total_patterns': 0,
                    'current_risk_level': ToxicityLevel.NONE,
                    'trend_direction': 'stable',
                    'error': str(e)
                }
            }

# Singleton instance
toxicity_detection_service = ToxicityDetectionService()