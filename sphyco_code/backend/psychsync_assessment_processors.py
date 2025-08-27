            # Assign questions to dimensions cyclically
            dimension_index = i % 4
            
            if dimension_index == 0:  # E vs I
                if answer > 3:
                    scores['E'] += answer
                else:
                    scores['I'] += (6 - answer)
            elif dimension_index == 1:  # S vs N
                if answer > 3:
                    scores['S'] += answer
                else:
                    scores['N'] += (6 - answer)
            elif dimension_index == 2:  # T vs F
                if answer > 3:
                    scores['T'] += answer
                else:
                    scores['F'] += (6 - answer)
            else:  # J vs P
                if answer > 3:
                    scores['J'] += answer
                else:
                    scores['P'] += (6 - answer)
        
        # Normalize scores to percentages
        total_e_i = scores['E'] + scores['I']
        total_s_n = scores['S'] + scores['N']
        total_t_f = scores['T'] + scores['F']
        total_j_p = scores['J'] + scores['P']
        
        normalized_scores = {
            'E': scores['E'] / total_e_i if total_e_i > 0 else 0.5,
            'I': scores['I'] / total_e_i if total_e_i > 0 else 0.5,
            'S': scores['S'] / total_s_n if total_s_n > 0 else 0.5,
            'N': scores['N'] / total_s_n if total_s_n > 0 else 0.5,
            'T': scores['T'] / total_t_f if total_t_f > 0 else 0.5,
            'F': scores['F'] / total_t_f if total_t_f > 0 else 0.5,
            'J': scores['J'] / total_j_p if total_j_p > 0 else 0.5,
            'P': scores['P'] / total_j_p if total_j_p > 0 else 0.5
        }
        
        return normalized_scores
    
    def _determine_type(self, scores: Dict[str, float]) -> str:
        """Determine MBTI type from dimension scores"""
        type_letters = []
        
        # Extraversion vs Introversion
        type_letters.append('E' if scores['E'] > scores['I'] else 'I')
        
        # Sensing vs Intuition
        type_letters.append('S' if scores['S'] > scores['N'] else 'N')
        
        # Thinking vs Feeling
        type_letters.append('T' if scores['T'] > scores['F'] else 'F')
        
        # Judging vs Perceiving
        type_letters.append('J' if scores['J'] > scores['P'] else 'P')
        
        return ''.join(type_letters)
    
    def _calculate_mbti_confidence(self, scores: Dict[str, float], raw_data: Dict) -> float:
        """Calculate confidence in MBTI type determination"""
        base_confidence = self.calculate_confidence(raw_data)
        
        # Calculate clarity of preferences
        preferences_clarity = [
            abs(scores['E'] - scores['I']),
            abs(scores['S'] - scores['N']),
            abs(scores['T'] - scores['F']),
            abs(scores['J'] - scores['P'])
        ]
        
        avg_clarity = np.mean(preferences_clarity)
        clarity_bonus = min(0.3, avg_clarity)
        
        return min(1.0, base_confidence + clarity_bonus)
    
    def _get_type_strengths(self, mbti_type: str) -> List[str]:
        """Get strengths for MBTI type"""
        strengths_map = {
            'INTJ': ['Strategic thinking', 'Independent work', 'Long-term planning', 'System optimization'],
            'INTP': ['Logical analysis', 'Creative problem-solving', 'Theoretical thinking', 'Adaptability'],
            'ENTJ': ['Leadership', 'Strategic planning', 'Efficiency', 'Decision-making'],
            'ENTP': ['Innovation', 'Brainstorming', 'Networking', 'Adaptability'],
            'INFJ': ['Insight', 'Long-term vision', 'Empathy', 'Dedication'],
            'INFP': ['Creativity', 'Values-based decisions', 'Authenticity', 'Individual focus'],
            'ENFJ': ['Team leadership', 'Communication', 'Inspiration', 'Development of others'],
            'ENFP': ['Enthusiasm', 'Creativity', 'People skills', 'Adaptability'],
            'ISTJ': ['Reliability', 'Attention to detail', 'Organization', 'Thoroughness'],
            'ISFJ': ['Service orientation', 'Loyalty', 'Attention to others needs', 'Practical help'],
            'ESTJ': ['Management', 'Organization', 'Efficiency', 'Decisiveness'],
            'ESFJ': ['Team harmony', 'Service', 'Organization', 'Communication'],
            'ISTP': ['Problem-solving', 'Hands-on skills', 'Flexibility', 'Crisis management'],
            'ISFP': ['Artistic abilities', 'Flexibility', 'Service', 'Individual attention'],
            'ESTP': ['Action orientation', 'Adaptability', 'Practical problem-solving', 'People skills'],
            'ESFP': ['Enthusiasm', 'People skills', 'Flexibility', 'Team spirit']
        }
        return strengths_map.get(mbti_type, [])
    
    def _get_development_areas(self, mbti_type: str) -> List[str]:
        """Get development areas for MBTI type"""
        development_map = {
            'INTJ': ['Emotional expression', 'Team collaboration', 'Patience with details', 'Flexibility'],
            'INTP': ['Follow-through', 'Practical application', 'Emotional awareness', 'Time management'],
            'ENTJ': ['Patience', 'Emotional sensitivity', 'Listening skills', 'Work-life balance'],
            'ENTP': ['Follow-through', 'Attention to detail', 'Emotional sensitivity', 'Routine tasks'],
            # Add more types...
        }
        return development_map.get(mbti_type, [])
    
    def _get_communication_style(self, mbti_type: str) -> Dict[str, str]:
        """Get communication style for MBTI type"""
        # Simplified - would be more detailed in production
        if 'E' in mbti_type:
            energy = 'Outwardly expressive, thinks out loud'
        else:
            energy = 'Reflective, thinks before speaking'
        
        if 'N' in mbti_type:
            information = 'Big picture, conceptual'
        else:
            information = 'Specific, detailed, practical'
        
        return {
            'energy_style': energy,
            'information_style': information
        }
    
    def _get_leadership_style(self, mbti_type: str) -> str:
        """Get leadership style for MBTI type"""
        leadership_styles = {
            'ENTJ': 'Strategic and commanding',
            'ENFJ': 'Inspirational and developmental',
            'ESTJ': 'Traditional and organized',
            'ESFJ': 'Supportive and harmonious',
            'INTJ': 'Visionary and independent',
            'INFJ': 'Insightful and values-driven',
            'ISTJ': 'Reliable and methodical',
            'ISFJ': 'Caring and behind-the-scenes'
        }
        return leadership_styles.get(mbti_type, 'Situational leadership')
    
    def _get_team_contribution(self, mbti_type: str) -> List[str]:
        """Get team contributions for MBTI type"""
        contributions = {
            'INTJ': ['Strategic insights', 'System improvements', 'Long-term planning'],
            'ENFP': ['Creative ideas', 'Team motivation', 'Exploring possibilities'],
            'ISTJ': ['Process adherence', 'Quality control', 'Reliable execution'],
            'ESFJ': ['Team harmony', 'Coordination', 'Supporting others']
            # Add more types...
        }
        return contributions.get(mbti_type, ['Unique perspective', 'Dedicated contribution'])
    
    def _get_stress_indicators(self, mbti_type: str) -> List[str]:
        """Get stress indicators for MBTI type"""
        stress_indicators = {
            'INTJ': ['Micromanaging details', 'Becoming overly critical', 'Withdrawing from others'],
            'ENFP': ['Becoming scattered', 'Overcommitting', 'Neglecting details'],
            'ISTJ': ['Becoming inflexible', 'Worrying excessively', 'Avoiding change'],
            'ESFP': ['Becoming moody', 'Overreacting emotionally', 'Avoiding responsibilities']
            # Add more types...
        }
        return stress_indicators.get(mbti_type, ['Changes in normal behavior patterns'])


class BigFiveProcessor(AssessmentProcessor):
    """Process Big Five (OCEAN) personality assessments"""
    
    def __init__(self):
        self.dimensions = {
            'openness': 'Openness to Experience',
            'conscientiousness': 'Conscientiousness',
            'extraversion': 'Extraversion',
            'agreeableness': 'Agreeableness',
            'neuroticism': 'Neuroticism'
        }
        
        self.facets = self._create_facets_map()
    
    def _create_facets_map(self) -> Dict[str, List[str]]:
        """Create mapping of dimensions to their facets"""
        return {
            'openness': [
                'Ideas', 'Fantasy', 'Aesthetics', 'Actions', 'Feelings', 'Values'
            ],
            'conscientiousness': [
                'Competence', 'Order', 'Dutifulness', 'Achievement Striving',
                'Self-Discipline', 'Deliberation'
            ],
            'extraversion': [
                'Warmth', 'Gregariousness', 'Assertiveness', 'Activity',
                'Excitement Seeking', 'Positive Emotions'
            ],
            'agreeableness': [
                'Trust', 'Straightforwardness', 'Altruism', 'Compliance',
                'Modesty', 'Tender-Mindedness'
            ],
            'neuroticism': [
                'Anxiety', 'Angry Hostility', 'Depression', 'Self-Consciousness',
                'Impulsiveness', 'Vulnerability'
            ]
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate Big Five assessment input"""
        if not isinstance(raw_data, dict):
            return False
        
        # Need minimum questions for reliable assessment
        if len(raw_data) < 25:  # 5 per dimension minimum
            return False
        
        # Validate answer format (1-5 scale typically)
        for key, value in raw_data.items():
            if value is not None and not (1 <= value <= 5):
                return False
        
        return True
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Big Five assessment data"""
        if not self.validate_input(raw_data):
            raise ValueError("Invalid Big Five assessment data")
        
        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(raw_data)
        
        # Calculate facet scores
        facet_scores = self._calculate_facet_scores(raw_data)
        
        # Calculate confidence
        confidence = self.calculate_confidence(raw_data)
        
        # Generate interpretations
        interpretations = self._generate_interpretations(dimension_scores)
        
        result = {
            "openness": dimension_scores['openness'],
            "conscientiousness": dimension_scores['conscientiousness'],
            "extraversion": dimension_scores['extraversion'],
            "agreeableness": dimension_scores['agreeableness'],
            "neuroticism": dimension_scores['neuroticism'],
            "facet_scores": facet_scores,
            "confidence": confidence,
            "interpretations": interpretations,
            "percentiles": self._calculate_percentiles(dimension_scores),
            "profile_pattern": self._determine_profile_pattern(dimension_scores),
            "work_implications": self._get_work_implications(dimension_scores),
            "team_dynamics": self._get_team_dynamics_implications(dimension_scores),
            "development_suggestions": self._get_development_suggestions(dimension_scores),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _calculate_dimension_scores(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scores for each Big Five dimension"""
        # Distribute questions evenly across dimensions
        questions_per_dimension = len(raw_data) // 5
        
        scores = {dim: [] for dim in self.dimensions.keys()}
        
        for i, (question, answer) in enumerate(raw_data.items()):
            if answer is None:
                continue
                
            # Determine which dimension this question belongs to
            dimension_index = i % 5
            dimension_keys = list(self.dimensions.keys())
            dimension = dimension_keys[dimension_index]
            
            # Convert to 0-1 scale
            normalized_answer = (answer - 1) / 4.0
            scores[dimension].append(normalized_answer)
        
        # Calculate average scores
        dimension_averages = {}
        for dimension, values in scores.items():
            if values:
                dimension_averages[dimension] = np.mean(values)
            else:
                dimension_averages[dimension] = 0.5  # Neutral if no data
        
        return dimension_averages
    
    def _calculate_facet_scores(self, raw_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Calculate facet scores within each dimension"""
        # Simplified facet calculation
        facet_scores = {}
        
        for dimension, facets in self.facets.items():
            facet_scores[dimension] = {}
            for facet in facets:
                # Mock calculation - would use specific question mapping in production
                facet_scores[dimension][facet] = np.random.beta(2, 2)
        
        return facet_scores
    
    def _generate_interpretations(self, scores: Dict[str, float]) -> Dict[str, Dict[str, str]]:
        """Generate text interpretations for each dimension"""
        interpretations = {}
        
        for dimension, score in scores.items():
            if score > 0.7:
                level = "high"
            elif score > 0.3:
                level = "moderate"
            else:
                level = "low"
            
            interpretations[dimension] = {
                "level": level,
                "description": self._get_dimension_description(dimension, level),
                "behavioral_indicators": self._get_behavioral_indicators(dimension, level)
            }
        
        return interpretations
    
    def _get_dimension_description(self, dimension: str, level: str) -> str:
        """Get description for dimension at specific level"""
        descriptions = {
            'openness': {
                'high': 'Very creative, curious, and open to new experiences',
                'moderate': 'Balanced between tradition and innovation',
                'low': 'Prefers familiar routines and conventional approaches'
            },
            'conscientiousness': {
                'high': 'Highly organized, disciplined, and goal-oriented',
                'moderate': 'Generally reliable with some flexibility',
                'low': 'More spontaneous and less structured in approach'
            },
            'extraversion': {
                'high': 'Outgoing, energetic, and socially confident',
                'moderate': 'Comfortable in both social and solitary settings',
                'low': 'Prefers quiet environments and smaller social groups'
            },
            'agreeableness': {
                'high': 'Cooperative, trusting, and considerate of others',
                'moderate': 'Balanced between self-interest and cooperation',
                'low': 'More skeptical and competitive in relationships'
            },
            'neuroticism': {
                'high': 'Tends to experience stress and emotional instability',
                'moderate': 'Generally emotionally stable with occasional stress',
                'low': 'Very emotionally stable and resilient'
            }
        }
        return descriptions.get(dimension, {}).get(level, '')
    
    def _get_behavioral_indicators(self, dimension: str, level: str) -> List[str]:
        """Get behavioral indicators for dimension at specific level"""
        indicators = {
            'openness_high': ['Seeks variety', 'Enjoys abstract thinking', 'Appreciates art'],
            'openness_low': ['Prefers routine', 'Focuses on practical matters', 'Traditional values'],
            'conscientiousness_high': ['Plans ahead', 'Pays attention to details', 'Meets deadlines'],
            'conscientiousness_low': ['Flexible with plans', 'Comfortable with ambiguity', 'Spontaneous'],
            'extraversion_high': ['Talkative', 'Energetic in groups', 'Seeks social attention'],
            'extraversion_low': ['Reflective', 'Prefers written communication', 'Values privacy'],
            'agreeableness_high': ['Helpful', 'Avoids conflict', 'Trusting'],
            'agreeableness_low': ['Direct communication', 'Skeptical', 'Competitive'],
            'neuroticism_high': ['Worries frequently', 'Emotionally reactive', 'Stress-sensitive'],
            'neuroticism_low': ['Calm under pressure', 'Emotionally even', 'Resilient']
        }
        key = f"{dimension}_{level}"
        return indicators.get(key, [])
    
    def _calculate_percentiles(self, scores: Dict[str, float]) -> Dict[str, int]:
        """Calculate percentile ranks for each dimension"""
        # Mock percentile calculation - would use normative data in production
        percentiles = {}
        for dimension, score in scores.items():
            # Convert 0-1 score to percentile (simplified)
            percentile = int(score * 100)
            percentiles[dimension] = max(1, min(99, percentile))
        return percentiles
    
    def _determine_profile_pattern(self, scores: Dict[str, float]) -> str:
        """Determine overall personality profile pattern"""
        high_dims = [dim for dim, score in scores.items() if score > 0.7]
        low_dims = [dim for dim, score in scores.items() if score < 0.3]
        
        if len(high_dims) >= 3:
            return "high_functioning"
        elif 'neuroticism' in low_dims and 'conscientiousness' in high_dims:
            return "resilient_achiever"
        elif 'extraversion' in high_dims and 'openness' in high_dims:
            return "innovative_leader"
        elif 'agreeableness' in high_dims and 'conscientiousness' in high_dims:
            return "reliable_team_player"
        else:
            return "balanced_profile"
    
    def _get_work_implications(self, scores: Dict[str, float]) -> Dict[str, List[str]]:
        """Get work-related implications of personality profile"""
        implications = {
            "strengths": [],
            "challenges": [],
            "ideal_roles": [],
            "work_environment": []
        }
        
        # Conscientiousness implications
        if scores['conscientiousness'] > 0.7:
            implications["strengths"].extend(["Detail-oriented", "Reliable", "Goal-focused"])
            implications["ideal_roles"].extend(["Project manager", "Quality assurance"])
        
        # Extraversion implications
        if scores['extraversion'] > 0.7:
            implications["strengths"].extend(["Team collaboration", "Communication"])
            implications["ideal_roles"].extend(["Team lead", "Client-facing roles"])
            implications["work_environment"].append("Open, collaborative spaces")
        else:
            implications["work_environment"].append("Quiet, focused work areas")
        
        # Openness implications
        if scores['openness'] > 0.7:
            implications["strengths"].extend(["Innovation", "Adaptability"])
            implications["ideal_roles"].extend(["Research", "Creative roles"])
        
        return implications
    
    def _get_team_dynamics_implications(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Get team dynamics implications"""
        return {
            "collaboration_style": "cooperative" if scores['agreeableness'] > 0.6 else "independent",
            "communication_preference": "verbal" if scores['extraversion'] > 0.6 else "written",
            "conflict_approach": "avoiding" if scores['agreeableness'] > 0.7 else "direct",
            "stress_response": "resilient" if scores['neuroticism'] < 0.3 else "sensitive",
            "change_adaptation": "embracing" if scores['openness'] > 0.6 else "cautious"
        }
    
    def _get_development_suggestions(self, scores: Dict[str, float]) -> List[str]:
        """Get personalized development suggestions"""
        suggestions = []
        
        if scores['conscientiousness'] < 0.4:
            suggestions.append("Practice time management and goal-setting techniques")
        
        if scores['extraversion'] < 0.3:
            suggestions.append("Gradually increase participation in team discussions")
        
        if scores['neuroticism'] > 0.7:
            suggestions.append("Develop stress management and resilience strategies")
        
        if scores['agreeableness'] < 0.3:
            suggestions.append("Practice active listening and empathy in team interactions")
        
        return suggestions if suggestions else ["Continue leveraging your natural strengths"]


class PIProcessor(AssessmentProcessor):
    """Process Predictive Index assessments"""
    
    def __init__(self):
        self.dimensions = {
            'dominance': 'Drive to exert influence on people or events',
            'extraversion': 'Drive for social interaction',
            'patience': 'Drive for consistency and stability',
            'formality': 'Drive to conform to rules and structure'
        }
        
        self.behavioral_patterns = self._create_behavioral_patterns()
    
    def _create_behavioral_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Create behavioral pattern definitions"""
        return {
            'analyzer': {
                'description': 'Analytical, precise, and systematic',
                'traits': ['Detail-oriented', 'Cautious', 'Diplomatic'],
                'drives': {'dominance': 'low', 'extraversion': 'low', 'patience': 'high', 'formality': 'high'}
            },
            'controller': {
                'description': 'Independent, driving, and determined',
                'traits': ['Results-focused', 'Fast-paced', 'Self-confident'],
                'drives': {'dominance': 'high', 'extraversion': 'low', 'patience': 'low', 'formality': 'low'}
            },
            'promoter': {
                'description': 'Persuasive, outgoing, and optimistic',
                'traits': ['Enthusiastic', 'Trusting', 'Flexible'],
                'drives': {'dominance': 'high', 'extraversion': 'high', 'patience': 'low', 'formality': 'low'}
            },
            'supporter': {
                'description': 'Patient, reliable, and sincere',
                'traits': ['Stable', 'Team-oriented', 'Helpful'],
                'drives': {'dominance': 'low', 'extraversion': 'low', 'patience': 'high', 'formality': 'low'}
            }
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate PI assessment input"""
        if not isinstance(raw_data, dict):
            return False
        
        # PI typically uses forced-choice format
        if len(raw_data) < 12:  # Minimum questions
            return False
        
        return True
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process PI assessment data"""
        if not self.validate_input(raw_data):
            raise ValueError("Invalid PI assessment data")
        
        # Calculate dimension scores
        dimension_scores = self._calculate_pi_scores(raw_data)
        
        # Determine behavioral pattern
        pattern = self._determine_behavioral_pattern(dimension_scores)
        
        # Calculate confidence
        confidence = self.calculate_confidence(raw_data)
        
        result = {
            "dominance": dimension_scores['dominance'],
            "extraversion": dimension_scores['extraversion'],
            "patience": dimension_scores['patience'],
            "formality": dimension_scores['formality'],
            "behavioral_pattern": pattern,
            "pattern_description": self.behavioral_patterns[pattern]['description'],
            "key_traits": self.behavioral_patterns[pattern]['traits'],
            "confidence": confidence,
            "work_style": self._get_work_style_implications(dimension_scores),
            "management_style": self._get_management_implications(dimension_scores),
            "team_dynamics": self._get_team_implications(dimension_scores),
            "development_focus": self._get_development_focus(dimension_scores),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _calculate_pi_scores(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate PI dimension scores"""
        # Simplified calculation - distribute questions across dimensions
        scores = {'dominance': 0, 'extraversion': 0, 'patience': 0, 'formality': 0}
        counts = {'dominance': 0, 'extraversion': 0, 'patience': 0, 'formality': 0}
        
        dimensions = list(scores.keys())
        
        for i, (question, answer) in enumerate(raw_data.items()):
            if answer is None:
                continue
            
            dimension = dimensions[i % 4]
            
            # Convert answer to numeric score
            if isinstance(answer, str):
                numeric_answer = 1 if answer.lower() in ['yes', 'true', 'agree'] else 0
            else:
                numeric_answer = float(answer)
            
            scores[dimension] += numeric_answer
            counts[dimension] += 1
        
        # Normalize scores
        normalized_scores = {}
        for dim in dimensions:
            if counts[dim] > 0:
                normalized_scores[dim] = scores[dim] / counts[dim]
            else:
                normalized_scores[dim] = 0.5
        
        return normalized_scores
    
    def _determine_behavioral_pattern(self, scores: Dict[str, float]) -> str:
        """Determine primary behavioral pattern"""
        # Simplified pattern matching
        if scores['dominance'] > 0.6 and scores['extraversion'] > 0.6:
            return 'promoter'
        elif scores['dominance'] > 0.6:
            return 'controller'
        elif scores['formality'] > 0.6 and scores['patience'] > 0.6:
            return 'analyzer'
        else:
            return 'supporter'
    
    def _get_work_style_implications(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Get work style implications from PI scores"""
        return {
            "pace": "fast" if scores['patience'] < 0.4 else "steady",
            "decision_style": "quick" if scores['dominance'] > 0.6 else "deliberate",
            "communication": "direct" if scores['dominance'] > 0.6 else "diplomatic",
            "work_environment": "dynamic" if scores['extraversion'] > 0.6 else "focused",
            "structure_preference": "high" if scores['formality'] > 0.6 else "flexible"
        }
    
    def _get_management_implications(self, scores: Dict[str, float]) -> Dict[str, str]:
        """Get management style implications"""
        style = "directive" if scores['dominance'] > 0.6 else "collaborative"
        approach = "results-focused" if scores['dominance'] > 0.6 else "people-focused"
        
        return {
            "management_style": style,
            "approach": approach,
            "delegation": "outcomes" if scores['dominance'] > 0.6 else "process"
        }
    
    def _get_team_implications(self, scores: Dict[str, float]) -> Dict[str, str]:
        """Get team dynamics implications"""
        return {
            "role_preference": "leader" if scores['dominance'] > 0.7 else "contributor",
            "interaction_style": "collaborative" if scores['extraversion'] > 0.6 else "independent",
            "change_response": "embracing" if scores['patience'] < 0.4 else "cautious",
            "conflict_style": "direct" if scores['dominance'] > 0.6 else "harmonizing"
        }
    
    def _get_development_focus(self, scores: Dict[str, float]) -> List[str]:
        """Get development focus areas"""
        focus_areas = []
        
        if scores['dominance'] > 0.8:
            focus_areas.append("Develop listening and empathy skills")
        
        if scores['extraversion'] < 0.3:
            focus_areas.append("Practice public speaking and team participation")
        
        if scores['patience'] < 0.2:
            focus_areas.append("Work on patience and attention to detail")
        
        if scores['formality'] > 0.8:
            focus_areas.append("Increase flexibility and adaptability")
        
        return focus_areas if focus_areas else ["Continue leveraging natural strengths"]


class StrengthsProcessor(AssessmentProcessor):
    """Process StrengthsFinder/CliftonStrengths assessments"""
    
    def __init__(self):
        self.all_themes = [
            'Achiever', 'Activator', 'Adaptability', 'Analytical', 'Arranger', 'Belief',
            'Command', 'Communication', 'Competition', 'Connectedness', 'Consistency',
            'Context', 'Deliberative', 'Developer', 'Discipline', 'Empathy', 'Focus',
            'Futuristic', 'Harmony', 'Ideation', 'Includer', 'Individualization',
            'Input', 'Intellection', 'Learner', 'Maximizer', 'Positivity', 'Relator',
            'Responsibility', 'Restorative', 'Self-Assurance', 'Significance', 'Strategic', 'Woo'
        ]
        
        self.theme_domains = self._create_theme_domains()
        self.theme_descriptions = self._create_theme_descriptions()
    
    def _create_theme_domains(self) -> Dict[str, str]:
        """Map themes to their domains"""
        return {
            # Executing Domain
            'Achiever': 'Executing', 'Arranger': 'Executing', 'Belief': 'Executing',
            'Consistency': 'Executing', 'Deliberative': 'Executing', 'Discipline': 'Executing',
            'Focus': 'Executing', 'Responsibility': 'Executing', 'Restorative': 'Executing',
            
            # Influencing Domain
            'Activator': 'Influencing', 'Command': 'Influencing', 'Communication': 'Influencing',
            'Competition': 'Influencing', 'Maximizer': 'Influencing', 'Self-Assurance': 'Influencing',
            'Significance': 'Influencing', 'Woo': 'Influencing',
            
            # Relationship Building Domain
            'Adaptability': 'Relationship Building', 'Connectedness': 'Relationship Building',
            'Developer': 'Relationship Building', 'Empathy': 'Relationship Building',
            'Harmony': 'Relationship Building', 'Includer': 'Relationship Building',
            'Individualization': 'Relationship Building', 'Positivity': 'Relationship Building',
            'Relator': 'Relationship Building',
            
            # Strategic Thinking Domain
            'Analytical': 'Strategic Thinking', 'Context': 'Strategic Thinking',
            'Futuristic': 'Strategic Thinking', 'Ideation': 'Strategic Thinking',
            'Input': 'Strategic Thinking', 'Intellection': 'Strategic Thinking',
            'Learner': 'Strategic Thinking', 'Strategic': 'Strategic Thinking'
        }
    
    def _create_theme_descriptions(self) -> Dict[str, Dict[str, str]]:
        """Create descriptions for each strength theme"""
        return {
            'Achiever': {
                'description': 'People exceptionally talented in the Achiever theme work hard and possess great stamina.',
                'action_items': ['Set challenging goals', 'Track progress daily', 'Celebrate completions']
            },
            'Strategic': {
                'description': 'People exceptionally talented in the Strategic theme create alternative ways to proceed.',
                'action_items': ['Lead planning sessions', 'Analyze multiple scenarios', 'Share strategic insights']
            },
            'Learner': {
                'description': 'People exceptionally talented in the Learner theme have a great desire to learn.',
                'action_items': ['Pursue continuous education', 'Share knowledge with others', 'Explore new domains']
            },
            'Communication': {
                'description': 'People exceptionally talented in the Communication theme find it easy to put thoughts into words.',
                'action_items': ['Lead presentations', 'Facilitate meetings', 'Create compelling narratives']
            },
            'Empathy': {
                'description': 'People exceptionally talented in the Empathy theme can sense other peoples emotions.',
                'action_items': ['Provide emotional support', 'Mediate conflicts', 'Build inclusive environments']
            }
            # Add more themes as needed
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate StrengthsFinder assessment input"""
        if not isinstance(raw_data, dict):
            return False
        
        # Check for top themes or raw scores
        if 'top_themes' in raw_data:
            top_themes = raw_data['top_themes']
            if not isinstance(top_themes, list) or len(top_themes) < 1:
                return False
            
            # Validate theme names
            for theme in top_themes:
                if theme not in self.all_themes:
                    return False
        
        return True
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process StrengthsFinder assessment data"""
        if not self.validate_input(raw_data):
            raise ValueError("Invalid StrengthsFinder assessment data")
        
        # Extract top themes
        if 'top_themes' in raw_data:
            top_themes = raw_data['top_themes'][:5]  # Top 5
        else:
            # If raw scores provided, determine top themes
            top_themes = self._determine_top_themes(raw_data)
        
        # Calculate domain distribution
        domain_distribution = self._calculate_domain_distribution(top_themes)
        
        # Generate insights
        insights = self._generate_strengths_insights(top_themes, domain_distribution)
        
        result = {
            "top_themes": top_themes,
            "theme_descriptions": {theme: self.theme_descriptions.get(theme, {}) for theme in top_themes},
            "domain_distribution": domain_distribution,
            "dominant_domain": max(domain_distribution, key=domain_distribution.get),
            "insights": insights,
            "team_contributions": self._get_team_contributions(top_themes),
            "development_suggestions": self._get_development_suggestions(top_themes),
            "partnership_opportunities": self._get_partnership_opportunities(top_themes),
            "potential_blind_spots": self._identify_blind_spots(top_themes),
            "confidence": self.calculate_confidence(raw_data),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _determine_top_themes(self, raw_data: Dict[str, Any]) -> List[str]:
        """Determine top themes from raw assessment scores"""
        # Mock implementation - would use actual scoring algorithm
        theme_scores = {}
        
        for theme in self.all_themes:
            # Generate mock scores based on some questions
            theme_scores[theme] = np.random.beta(2, 3)  # Skewed toward lower scores
        
        # Sort by score and return top 5
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, score in sorted_themes[:5]]
    
    def _calculate_domain_distribution(self, top_themes: List[str]) -> Dict[str, int]:
        """Calculate distribution of themes across domains"""
        domain_counts = {
            'Executing': 0,
            'Influencing': 0,
            'Relationship Building': 0,
            'Strategic Thinking': 0
        }
        
        for theme in top_themes:
            domain = self.theme_domains.get(theme, 'Unknown')
            if domain in domain_counts:
                domain_counts[domain] += 1
        
        return domain_counts
    
    def _generate_strengths_insights(self, top_themes: List[str], domain_distribution: Dict[str, int]) -> List[str]:
        """Generate insights based on strengths profile"""
        insights = []
        
        # Domain-based insights
        dominant_domain = max(domain_distribution, key=domain_distribution.get)
        insights.append(f"Your strengths are primarily in {dominant_domain}, indicating natural talent in this area.")
        
        # Check for balance
        max_count = max(domain_distribution.values())
        if max_count >= 3:
            insights.append("Your strengths are concentrated in one domain, suggesting specialized expertise.")
        else:
            insights.append("Your strengths span multiple domains, indicating versatility.")
        
        # Specific theme combinations
        if 'Strategic' in top_themes and 'Achiever' in top_themes:
            insights.append("The combination of Strategic and Achiever makes you a powerful goal-oriented planner.")
        
        if 'Communication' in top_themes and 'Empathy' in top_themes:
            insights.append("Your Communication and Empathy strengths make you an exceptional team connector.")
        
        return insights
    
    def _get_team_contributions(self, top_themes: List[str]) -> List[str]:
        """Get specific team contributions based on strengths"""
        contributions = []
        
        theme_contributions = {
            'Achiever': 'Driving projects to completion',
            'Strategic': 'Providing strategic direction and planning',
            'Communication': 'Facilitating clear team communication',
            'Empathy': 'Understanding and supporting team members',
            'Learner': 'Bringing new knowledge and insights',
            'Analytical': 'Providing data-driven analysis',
            'Developer': 'Growing and mentoring team members',
            'Harmony': 'Maintaining team cohesion and reducing conflict',
            'Ideation': 'Generating creative solutions and ideas',
            'Responsibility': 'Ensuring follow-through and accountability'
        }
        
        for theme in top_themes:
            if theme in theme_contributions:
                contributions.append(theme_contributions[theme])
        
        return contributions
    
    def _get_development_suggestions(self, top_themes: List[str]) -> List[str]:
        """Get development suggestions based on top themes"""
        suggestions = []
        
        # Domain-specific suggestions
        domain_counts = self._calculate_domain_distribution(top_themes)
        
        if domain_counts.get('Executing', 0) >= 2:
            suggestions.append("Focus on leveraging your execution strengths in high-impact projects")
        
        if domain_counts.get('Influencing', 0) >= 2:
            suggestions.append("Seek leadership opportunities to utilize your influencing talents")
        
        if domain_counts.get('Relationship Building', 0) >= 2:
            suggestions.append("Take on mentoring or team development roles")
        
        if domain_counts.get('Strategic Thinking', 0) >= 2:
            suggestions.append("Contribute to strategic planning and analysis initiatives")
        
        # Theme-specific suggestions
        if 'Learner' in top_themes:
            suggestions.append("Pursue continuous learning opportunities and share knowledge with others")
        
        if 'Strategic' in top_themes:
            suggestions.append("Lead strategic planning sessions and scenario analysis")
        
        return suggestions
    
    def _get_partnership_opportunities(self, top_themes: List[str]) -> List[str]:
        """Identify partnership opportunities with complementary strengths"""
        partnerships = []
        
        domain_counts = self._calculate_domain_distribution(top_themes)
        
        # Identify missing or weak domains
        weak_domains = [domain for domain, count in domain_counts.items() if count == 0]
        
        for weak_domain in weak_domains:
            if weak_domain == 'Executing':
                partnerships.append("Partner with strong Executors like Achiever, Discipline, or Focus")
            elif weak_domain == 'Influencing':
                partnerships.append("Collaborate with Influencers like Command, Communication, or Woo")
            elif weak_domain == 'Relationship Building':
                partnerships.append("Work with Relationship Builders like Empathy, Harmony, or Developer")
            elif weak_domain == 'Strategic Thinking':
                partnerships.append("Team up with Strategic Thinkers like Analytical, Strategic, or Futuristic")
        
        return partnerships
    
    def _identify_blind_spots(self, top_themes: List[str]) -> List[str]:
        """Identify potential blind spots based on strengths profile"""
        blind_spots = []
        
        domain_counts = self._calculate_domain_distribution(top_themes)
        
        # Domain-based blind spots
        if domain_counts.get('Relationship Building', 0) == 0:
            blind_spots.append("May overlook team dynamics and individual needs")
        
        if domain_counts.get('Strategic Thinking', 0) == 0:
            blind_spots.append("Might miss long-term implications or alternative approaches")
        
        if domain_counts.get('Executing', 0) == 0:
            blind_spots.append("Could struggle with follow-through and implementation")
        
        if domain_counts.get('Influencing', 0) == 0:
            blind_spots.append("May have difficulty persuading others or driving change")
        
        # Theme-specific blind spots
        if 'Harmony' in top_themes and 'Command' not in top_themes:
            blind_spots.append("May avoid necessary conflicts or difficult conversations")
        
        return blind_spots


class SocialStylesProcessor(AssessmentProcessor):
    """Process Social Styles assessment"""
    
    def __init__(self):
        self.styles = {
            'analytical': {
                'name': 'Analytical',
                'description': 'Task-focused and introverted',
                'characteristics': ['Systematic', 'Logical', 'Thorough', 'Cautious']
            },
            'driver': {
                'name': 'Driver',
                'description': 'Task-focused and extroverted',
                'characteristics': ['Results-oriented', 'Fast-paced', 'Direct', 'Decisive']
            },
            'amiable': {
                'name': 'Amiable',
                'description': 'People-focused and introverted',
                'characteristics': ['Cooperative', 'Patient', 'Loyal', 'Supportive']
            },
            'expressive': {
                'name': 'Expressive',
                'description': 'People-focused and extroverted',
                'characteristics': ['Enthusiastic', 'Animated', 'Intuitive', 'Persuasive']
            }
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate Social Styles assessment input"""
        if not isinstance(raw_data, dict):
            return False
        
        # Need minimum questions for assessment
        if len(raw_data) < 8:
            return False
        
        return True
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Social Styles assessment data"""
        if not self.validate_input(raw_data):
            raise ValueError("Invalid Social Styles assessment data")
        
        # Calculate assertiveness and responsiveness scores
        assertiveness, responsiveness = self._calculate_dimensions(raw_data)
        
        # Determine social style
        social_style = self._determine_social_style(assertiveness, responsiveness)
        
        # Calculate confidence
        confidence = self.calculate_confidence(raw_data)
        
        result = {
            "social_style": social_style,
            "style_name": self.styles[social_style]['name'],
            "description": self.styles[social_style]['description'],
            "characteristics": self.styles[social_style]['characteristics'],
            "assertiveness": assertiveness,
            "responsiveness": responsiveness,
            "confidence": confidence,
            "communication_preferences": self._get_communication_preferences(social_style),
            "work_environment": self._get_work_environment_preferences(social_style),
            "team_dynamics": self._get_team_dynamics(social_style),
            "stress_behaviors": self._get_stress_behaviors(social_style),
            "development_tips": self._get_development_tips(social_style),
            "compatibility_matrix": self._get_compatibility_with_others(social_style),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _calculate_dimensions(self, raw_data: Dict[str, Any]) -> tuple:
        """Calculate assertiveness and responsiveness dimensions"""
        assertiveness_questions = []
        responsiveness_questions = []
        
        # Split questions between dimensions (simplified)
        for i, (question, answer) in enumerate(raw_data.items()):
            if answer is None:
                continue
            
            if i % 2 == 0:  # Even questions for assertiveness
                assertiveness_questions.append(answer)
            else:  # Odd questions for responsiveness
                responsiveness_questions.append(answer)
        
        # Calculate averages (normalize to 0-1 scale)
        assertiveness = np.mean(assertiveness_questions) / 5.0 if assertiveness_questions else 0.5
        responsiveness = np.mean(responsiveness_questions) / 5.0 if responsiveness_questions else 0.5
        
        return assertiveness, responsiveness
    
    def _determine_social_style(self, assertiveness: float, responsiveness: float) -> str:
        """Determine social style based on dimensions"""
        if assertiveness >= 0.5 and responsiveness >= 0.5:
            return 'expressive'
        elif assertiveness >= 0.5 and responsiveness < 0.5:
            return 'driver'
        elif assertiveness < 0.5 and responsiveness >= 0.5:
            return 'amiable'
        else:
            return 'analytical'
    
    def _get_communication_preferences(self, style: str) -> Dict[str, str]:
        """Get communication preferences for each style"""
        preferences = {
            'analytical': {
                'pace': 'Slower, thoughtful',
                'information': 'Detailed, factual',
                'decision_making': 'Data-driven, deliberate',
                'feedback': 'Specific, constructive'
            },
            'driver': {
                'pace': 'Fast, direct',
                'information': 'Bottom-line, efficient',
                'decision_making': 'Quick, results-focused',
                'feedback': 'Brief, action-oriented'
            },
            'amiable': {
                'pace': 'Steady, patient',
                'information': 'Personal, relational',
                'decision_making': 'Consensus-building',
                'feedback': 'Supportive, encouraging'
            },
            'expressive': {
                'pace': 'Enthusiastic, animated',
                'information': 'Big picture, inspiring',
                'decision_making': 'Intuitive, flexible',
                'feedback': 'Positive, motivational'
            }
        }
        return preferences.get(style, {})
    
    def _get_work_environment_preferences(self, style: str) -> List[str]:
        """Get work environment preferences"""
        environments = {
            'analytical': ['Organized workspace', 'Minimal interruptions', 'Access to information'],
            'driver': ['Efficient setup', 'Results-focused atmosphere', 'Authority and control'],
            'amiable': ['Collaborative space', 'Stable team environment', 'Supportive culture'],
            'expressive': ['Dynamic environment', 'Social interaction', 'Creative freedom']
        }
        return environments.get(style, [])
    
    def _get_team_dynamics(self, style: str) -> Dict[str, str]:
        """Get team dynamics information"""
        dynamics = {
            'analytical': {
                'role': 'Quality controller and analyst',
                'contribution': 'Thorough analysis and risk assessment',
                'needs': 'Time to process and detailed information'
            },
            'driver': {
                'role': 'Results-oriented leader',
                'contribution': 'Goal achievement and efficiency',
                'needs': 'Clear objectives and authority'
            },
            'amiable': {
                'role': 'Team harmonizer and supporter',
                'contribution': 'Stability and cooperation',
                'needs': 'Security and appreciation'
            },
            'expressive': {
                'role': 'Team motivator and innovator',
                'contribution': 'Energy and creative ideas',
                'needs': 'Recognition and variety'
            }
        }
        return dynamics.get(style, {})
    
    def _get_stress_behaviors(self, style: str) -> List[str]:
        """Get stress behaviors for each style"""
        stress_behaviors = {
            'analytical': ['Over-analyzing', 'Procrastination', 'Withdrawal', 'Criticism'],
            'driver': ['Impatience', 'Controlling behavior', 'Insensitivity', 'Autocratic decisions'],
            'amiable': ['Avoiding decisions', 'Submissiveness', 'Resentment', 'Passive-aggressive behavior'],
            'expressive': ['Disorganization', 'Impulsiveness', 'Emotional outbursts', 'Attacking others']
        }
        return stress_behaviors.get(style, [])
    
    def _get_development_tips(self, style: str) -> List[str]:
        """Get development tips for each style"""
        tips = {
            'analytical': [
                'Practice making decisions with incomplete information',
                'Work on expressing ideas more assertively',
                'Develop comfort with interpersonal relationships'
            ],
            'driver': [
                'Practice active listening and patience',
                'Consider impact on others when making decisions',
                'Develop empathy and relationship skills'
            ],
            'amiable': [
                'Practice assertiveness and saying no when appropriate',
                'Work on initiating change and expressing opinions',
                'Develop comfort with conflict resolution'
            ],
            'expressive': [
                'Focus on follow-through and attention to detail',
                'Practice organized planning and time management',
                'Work on listening skills and controlling emotions'
            ]
        }
        return tips.get(style, [])
    
    def _get_compatibility_with_others(self, style: str) -> Dict[str, str]:
        """Get compatibility information with other styles"""
        compatibility = {
            'analytical': {
                'analytical': 'High - Similar approaches to work and decisions',
                'driver': 'Medium - Appreciate efficiency but may clash on pace',
                'amiable': 'Medium - Both cautious but different focuses',
                'expressive': 'Low - Very different paces and approaches'
            },
            'driver': {
                'analytical': 'Medium - Value thoroughness but impatient with pace',
                'driver': 'Medium - Similar goals but may compete',
                'amiable': 'Medium - Complement each other but different paces',
                'expressive': 'High - Both assertive and action-oriented'
            },
            'amiable': {
                'analytical': 'Medium - Both thoughtful but different focuses',
                'driver': 'Medium - Complement skills but different paces',
                'amiable': 'High - Similar values and approaches',
                'expressive': 'Medium - Both people-focused but different energy'
            },
            'expressive': {
                'analytical': 'Low - Very different communication and decision styles',
                'driver': 'High - Both assertive and results-oriented',
                'amiable': 'Medium - Both people-focused but different assertiveness',
                'expressive': 'Medium - Similar energy but may compete for attention'
            }
        }
        return compatibility.get(style, {})# assessment_processors.py - Personality Assessment Processing
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AssessmentProcessor(ABC):
    """Base class for all personality assessment processors"""
    
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw assessment data into standardized results"""
        pass
    
    @abstractmethod
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate input data format and completeness"""
        pass
    
    def calculate_confidence(self, raw_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the assessment"""
        # Default implementation based on completion rate
        if not raw_data:
            return 0.0
        
        total_questions = len(raw_data)
        answered_questions = sum(1 for v in raw_data.values() if v is not None)
        
        completion_rate = answered_questions / total_questions if total_questions > 0 else 0
        return min(1.0, completion_rate * 0.9)  # Max 0.9 for complete answers


class EnneagramProcessor(AssessmentProcessor):
    """Process Enneagram personality assessments"""
    
    def __init__(self):
        self.type_descriptions = {
            1: {"name": "The Perfectionist", "motivation": "Integrity and improvement"},
            2: {"name": "The Helper", "motivation": "Love and connection"},
            3: {"name": "The Achiever", "motivation": "Success and admiration"},
            4: {"name": "The Individualist", "motivation": "Identity and significance"},
            5: {"name": "The Investigator", "motivation": "Knowledge and understanding"},
            6: {"name": "The Loyalist", "motivation": "Security and support"},
            7: {"name": "The Enthusiast", "motivation": "Satisfaction and freedom"},
            8: {"name": "The Challenger", "motivation": "Control and self-protection"},
            9: {"name": "The Peacemaker", "motivation": "Peace and harmony"}
        }
        
        # Mapping questions to types (simplified example)
        self.question_type_mapping = self._create_question_mapping()
    
    def _create_question_mapping(self) -> Dict[str, int]:
        """Create mapping between questions and Enneagram types"""
        # This would be based on validated Enneagram questionnaires
        return {
            "q1": 1, "q2": 2, "q3": 3, "q4": 4, "q5": 5,
            "q6": 6, "q7": 7, "q8": 8, "q9": 9,
            "q10": 1, "q11": 2, "q12": 3, "q13": 4, "q14": 5,
            "q15": 6, "q16": 7, "q17": 8, "q18": 9,
            # Add more questions for better accuracy
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate Enneagram assessment input"""
        if not isinstance(raw_data, dict):
            return False
        
        # Check for minimum number of questions
        if len(raw_data) < 18:  # Minimum for basic assessment
            logger.warning("Insufficient questions for reliable Enneagram assessment")
            return False
        
        # Validate answer format (should be 1-5 scale)
        for key, value in raw_data.items():
            if value is not None and not (1 <= value <= 5):
                logger.warning(f"Invalid answer value {value} for question {key}")
                return False
        
        return True
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Enneagram assessment data"""
        if not self.validate_input(raw_data):
            raise ValueError("Invalid Enneagram assessment data")
        
        # Calculate scores for each type
        type_scores = {i: 0.0 for i in range(1, 10)}
        question_count = {i: 0 for i in range(1, 10)}
        
        for question, answer in raw_data.items():
            if answer is not None and question in self.question_type_mapping:
                enneagram_type = self.question_type_mapping[question]
                type_scores[enneagram_type] += answer
                question_count[enneagram_type] += 1
        
        # Calculate average scores
        for etype in type_scores:
            if question_count[etype] > 0:
                type_scores[etype] = type_scores[etype] / question_count[etype]
        
        # Determine primary type
        primary_type = max(type_scores, key=type_scores.get)
        primary_score = type_scores[primary_type]
        
        # Determine wing (adjacent type with highest score)
        adjacent_types = self._get_adjacent_types(primary_type)
        wing_scores = {t: type_scores[t] for t in adjacent_types}
        wing_type = max(wing_scores, key=wing_scores.get) if wing_scores else None
        
        # Calculate confidence
        confidence = self.calculate_confidence(raw_data)
        
        # Adjust confidence based on score separation
        score_separation = primary_score - sorted(type_scores.values())[-2]
        if score_separation > 0.5:
            confidence = min(1.0, confidence + 0.1)
        elif score_separation < 0.2:
            confidence = max(0.3, confidence - 0.1)
        
        result = {
            "type": primary_type,
            "type_name": self.type_descriptions[primary_type]["name"],
            "motivation": self.type_descriptions[primary_type]["motivation"],
            "wing": f"{primary_type}w{wing_type}" if wing_type else None,
            "all_scores": type_scores,
            "confidence": confidence,
            "interpretation": self._generate_interpretation(primary_type, wing_type),
            "strengths": self._get_type_strengths(primary_type),
            "challenges": self._get_type_challenges(primary_type),
            "work_style": self._get_work_style(primary_type),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _get_adjacent_types(self, primary_type: int) -> List[int]:
        """Get adjacent types for wing determination"""
        if primary_type == 1:
            return [9, 2]
        elif primary_type == 9:
            return [8, 1]
        else:
            return [primary_type - 1, primary_type + 1]
    
    def _generate_interpretation(self, primary_type: int, wing_type: Optional[int]) -> str:
        """Generate interpretation text"""
        base_text = f"Primary type {primary_type} ({self.type_descriptions[primary_type]['name']})"
        if wing_type:
            base_text += f" with {wing_type} wing"
        return base_text
    
    def _get_type_strengths(self, etype: int) -> List[str]:
        """Get strengths for each type"""
        strengths_map = {
            1: ["Detail-oriented", "High standards", "Organized", "Principled"],
            2: ["Empathetic", "Supportive", "Interpersonally skilled", "Generous"],
            3: ["Goal-oriented", "Efficient", "Adaptable", "Confident"],
            4: ["Creative", "Emotionally aware", "Authentic", "Intuitive"],
            5: ["Analytical", "Independent", "Observant", "Innovative"],
            6: ["Loyal", "Responsible", "Trustworthy", "Prepared"],
            7: ["Enthusiastic", "Versatile", "Optimistic", "Quick thinking"],
            8: ["Decisive", "Self-confident", "Energetic", "Protective"],
            9: ["Peaceful", "Accepting", "Supportive", "Stable"]
        }
        return strengths_map.get(etype, [])
    
    def _get_type_challenges(self, etype: int) -> List[str]:
        """Get challenges for each type"""
        challenges_map = {
            1: ["Perfectionism", "Criticism", "Rigidity", "Resentment"],
            2: ["People-pleasing", "Neglecting own needs", "Manipulation", "Pride"],
            3: ["Image focus", "Workaholism", "Avoiding failure", "Superficiality"],
            4: ["Moodiness", "Self-absorption", "Envy", "Melancholy"],
            5: ["Isolation", "Detachment", "Hoarding resources", "Cynicism"],
            6: ["Anxiety", "Doubt", "Suspicion", "Reactivity"],
            7: ["Impulsiveness", "Avoiding pain", "Scattered focus", "Superficiality"],
            8: ["Intensity", "Controlling", "Impatience", "Confrontational"],
            9: ["Inaction", "Avoiding conflict", "Stubbornness", "Neglecting priorities"]
        }
        return challenges_map.get(etype, [])
    
    def _get_work_style(self, etype: int) -> Dict[str, Any]:
        """Get work style preferences for each type"""
        work_styles = {
            1: {
                "preferred_environment": "Structured and organized",
                "communication": "Direct and precise",
                "decision_making": "Thorough analysis",
                "team_role": "Quality assurance, process improvement"
            },
            2: {
                "preferred_environment": "Collaborative and supportive",
                "communication": "Warm and personal",
                "decision_making": "Considers impact on others",
                "team_role": "Team support, relationship building"
            },
            3: {
                "preferred_environment": "Goal-oriented and competitive",
                "communication": "Efficient and results-focused",
                "decision_making": "Quick and pragmatic",
                "team_role": "Project leadership, goal achievement"
            },
            # Add more types...
        }
        return work_styles.get(etype, {})


class MBTIProcessor(AssessmentProcessor):
    """Process MBTI personality assessments"""
    
    def __init__(self):
        self.dimensions = {
            'E_I': 'Extraversion vs Introversion',
            'S_N': 'Sensing vs Intuition',
            'T_F': 'Thinking vs Feeling',
            'J_P': 'Judging vs Perceiving'
        }
        
        self.type_descriptions = self._create_type_descriptions()
        self.cognitive_functions = self._create_cognitive_functions_map()
    
    def _create_type_descriptions(self) -> Dict[str, Dict[str, str]]:
        """Create detailed descriptions for all 16 MBTI types"""
        return {
            'INTJ': {
                'name': 'The Architect',
                'description': 'Imaginative and strategic thinkers, with a plan for everything.',
                'key_traits': ['Strategic', 'Independent', 'Determined', 'Insightful']
            },
            'INTP': {
                'name': 'The Thinker',
                'description': 'Innovative inventors with an unquenchable thirst for knowledge.',
                'key_traits': ['Logical', 'Flexible', 'Creative', 'Independent']
            },
            'ENTJ': {
                'name': 'The Commander',
                'description': 'Bold, imaginative and strong-willed leaders.',
                'key_traits': ['Efficient', 'Energetic', 'Self-confident', 'Strong-willed']
            },
            'ENTP': {
                'name': 'The Debater',
                'description': 'Smart and curious thinkers who cannot resist an intellectual challenge.',
                'key_traits': ['Quick', 'Ingenious', 'Stimulating', 'Alert']
            },
            # Add all 16 types...
        }
    
    def _create_cognitive_functions_map(self) -> Dict[str, List[str]]:
        """Map MBTI types to their cognitive function stacks"""
        return {
            'INTJ': ['Ni', 'Te', 'Fi', 'Se'],
            'INTP': ['Ti', 'Ne', 'Si', 'Fe'],
            'ENTJ': ['Te', 'Ni', 'Se', 'Fi'],
            'ENTP': ['Ne', 'Ti', 'Fe', 'Si'],
            'INFJ': ['Ni', 'Fe', 'Ti', 'Se'],
            'INFP': ['Fi', 'Ne', 'Si', 'Te'],
            'ENFJ': ['Fe', 'Ni', 'Se', 'Ti'],
            'ENFP': ['Ne', 'Fi', 'Te', 'Si'],
            'ISTJ': ['Si', 'Te', 'Fi', 'Ne'],
            'ISFJ': ['Si', 'Fe', 'Ti', 'Ne'],
            'ESTJ': ['Te', 'Si', 'Ne', 'Fi'],
            'ESFJ': ['Fe', 'Si', 'Ne', 'Ti'],
            'ISTP': ['Ti', 'Se', 'Ni', 'Fe'],
            'ISFP': ['Fi', 'Se', 'Ni', 'Te'],
            'ESTP': ['Se', 'Ti', 'Fe', 'Ni'],
            'ESFP': ['Se', 'Fi', 'Te', 'Ni']
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate MBTI assessment input"""
        if not isinstance(raw_data, dict):
            return False
        
        # Should have questions for all 4 dimensions
        required_questions = 20  # Minimum for basic MBTI
        if len(raw_data) < required_questions:
            return False
        
        # Validate answer format
        for key, value in raw_data.items():
            if value is not None and not isinstance(value, (int, float, str)):
                return False
        
        return True
    
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process MBTI assessment data"""
        if not self.validate_input(raw_data):
            raise ValueError("Invalid MBTI assessment data")
        
        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(raw_data)
        
        # Determine MBTI type
        mbti_type = self._determine_type(dimension_scores)
        
        # Calculate confidence
        confidence = self._calculate_mbti_confidence(dimension_scores, raw_data)
        
        # Get cognitive functions
        cognitive_functions = self.cognitive_functions.get(mbti_type, [])
        
        result = {
            "type": mbti_type,
            "type_name": self.type_descriptions.get(mbti_type, {}).get('name', ''),
            "description": self.type_descriptions.get(mbti_type, {}).get('description', ''),
            "key_traits": self.type_descriptions.get(mbti_type, {}).get('key_traits', []),
            "dimension_scores": dimension_scores,
            "cognitive_functions": cognitive_functions,
            "confidence": confidence,
            "strengths": self._get_type_strengths(mbti_type),
            "development_areas": self._get_development_areas(mbti_type),
            "communication_style": self._get_communication_style(mbti_type),
            "leadership_style": self._get_leadership_style(mbti_type),
            "team_contribution": self._get_team_contribution(mbti_type),
            "stress_indicators": self._get_stress_indicators(mbti_type),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    def _calculate_dimension_scores(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scores for each MBTI dimension"""
        # Simplified scoring - in production, use validated question mappings
        scores = {
            'E': 0, 'I': 0,  # Extraversion vs Introversion
            'S': 0, 'N': 0,  # Sensing vs Intuition
            'T': 0, 'F': 0,  # Thinking vs Feeling
            'J': 0, 'P': 0   # Judging vs Perceiving
        }
        
        question_count = len(raw_data)
        
        # Mock calculation - distribute questions across dimensions
        for i, (question, answer) in enumerate(raw_data.items()):
            if answer is None:
                continue
            
            # Convert answer to numeric if string
            if isinstance(answer, str):
                try:
                    answer = float(answer)
                except ValueError:
                    continue
            
            # Assign questions to dimensions cyclically
            dimension_index