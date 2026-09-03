# PsychSync Assessment Engine Requirements
**Technical Specification for Multi-Framework Personality Assessment System**

**Version:** 1.0
**Last Updated:** 2025-01-12
**Owner:** Engineering Team (Backend + AI)
**Reviewers:** Product, Data Science, QA

---

## Executive Summary

The PsychSync Assessment Engine is a **multi-framework, adaptive, validated personality assessment system** that processes user responses through scientifically-backed algorithms to generate personality profiles, team insights, and predictive analytics.

**Key Requirements:**
- Support 5 frameworks: Big Five (OCEAN), MBTI, Enneagram, Predictive Index, DISC
- Adaptive questioning: Reduce completion time by 40% while maintaining validity
- Real-time scoring: Sub-200ms response time for results delivery
- Cross-framework validation: Consistency checks across frameworks
- Team analytics: Multi-user composition analysis and compatibility scoring

---

## Part 1: System Architecture Overview

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Assessment   │  │ Progress     │  │ Results      │          │
│  │ Question UI  │  │ Tracker      │  │ Dashboard    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────────┐
│                      API Gateway (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Assessment   │  │ Results      │  │ Team         │          │
│  │ Endpoints    │  │ Endpoints    │  │ Analytics    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    Assessment Engine Service                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Framework    │  │ Scoring      │  │ Validation   │          │
│  │ Processors   │  │ Engine       │  │ Layer        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Adaptive     │  │ Cross-       │  │ Team         │          │
│  │ Questioning  │  │ Framework    │  │ Composition  │          │
│  │ Engine       │  │ Mapper       │  │ Analyzer     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │ Redis        │  │ S3           │          │
│  │ (Assessments,│  │ (Cache,      │  (Question     │          │
│  │ Responses)   │  │ Sessions)    │  │ Banks)       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| Backend API | FastAPI | 0.104+ | Async, auto-validation, high performance |
| Database | PostgreSQL | 15+ | JSONB for flexible schema, ACID compliance |
| Cache | Redis | 7+ | Session management, real-time scoring cache |
| ML/Scoring | Python (scikit-learn) | 1.3+ | Proven ML algorithms, rich ecosystem |
| Frontend | React + TypeScript | 18+ | Type safety, component reusability |
| State Management | React Context | - | Lightweight, sufficient for assessment flow |

---

## Part 2: Framework Specifications

### Framework 1: Big Five (OCEAN)

**Scientific Basis:** Five-factor model of personality (Goldberg, 1990)

**Dimensions:**
1. **Openness to Experience** (Curious, Creative vs. Consistent, Cautious)
2. **Conscientiousness** (Organized, Efficient vs. Easy-going, Careless)
3. **Extraversion** (Outgoing, Energetic vs. Solitary, Reserved)
4. **Agreeableness** (Friendly, Compassionate vs. Challenging, Detached)
5. **Neuroticism** (Sensitive, Anxious vs. Secure, Confident)

**Question Bank:**
- Total questions: 50 (10 per dimension)
- Question type: 5-point Likert scale (Strongly Disagree to Strongly Agree)
- Sample questions:
  - "I have a rich vocabulary" (Openness)
  - "I am always prepared" (Conscientiousness)
  - "I feel comfortable around people" (Extraversion)
  - "I insult people" (Reverse-coded, Agreeableness)
  - "I worry about things" (Neuroticism)

**Scoring Algorithm:**
```python
def score_big_five(responses: List[Response]) -> BigFiveResult:
    """
    Score Big Five assessment using IRT (Item Response Theory)

    Args:
        responses: List of question responses (1-5 scale)

    Returns:
        BigFiveResult with percentile scores for each dimension
    """
    # Reverse-code negative items
    # Sum scores per dimension
    # Convert to percentiles (norm-referenced)
    # Validate: Consistency checks, social desirability bias
    pass
```

**Output Format:**
```json
{
  "framework": "big_five",
  "scores": {
    "openness": 78,
    "conscientiousness": 85,
    "extraversion": 42,
    "agreeableness": 65,
    "neuroticism": 35
  },
  "percentiles": {
    "openness": "78th percentile",
    "conscientiousness": "85th percentile"
  },
  "personality_summary": "You are highly organized and creative, with a calm and steady demeanor. You prefer deep thinking over social interaction.",
  "validity_metrics": {
    "consistency_score": 0.89,
    "social_desirability_bias": 0.12,
    "completion_time_seconds": 420
  }
}
```

**Psychometric Properties:**
- Cronbach's alpha: 0.85-0.90 (excellent reliability)
- Test-retest reliability: 0.85 (6-week interval)
- Convergent validity: Correlates 0.70+ with other Big Five measures

---

### Framework 2: MBTI (Myers-Briggs Type Indicator)

**Scientific Basis:** Jungian cognitive functions (simplification for business use)

**Dimensions:**
1. **Extraversion (E) vs. Introversion (I)** - Energy direction
2. **Sensing (S) vs. Intuition (N)** - Information gathering
3. **Thinking (T) vs. Feeling (F)** - Decision making
4. **Judging (J) vs. Perceiving (P)** - Lifestyle structure

**Question Bank:**
- Total questions: 93 (standard MBTI Form M)
- Question type: Forced choice dichotomous (A vs. B)
- Sample questions:
  - "At a party, do you: (A) Interact with many people, including strangers (B) Interact with a few people, known to you"
  - "Do you prefer: (A) Practical matters (B) Theoretical matters"

**Scoring Algorithm:**
```python
def score_mbti(responses: List[Response]) -> MBTIResult:
    """
    Score MBTI assessment using weighted preference clarity

    Args:
        responses: List of dichotomous choices (A/B)

    Returns:
        MBTIResult with 4-letter type and preference clarity
    """
    # Count E vs. I responses
    # Count S vs. N responses
    # Count T vs. F responses
    # Count J vs. P responses
    # Determine type based on majority
    # Calculate preference clarity (slight, moderate, clear, very clear)
    pass
```

**Output Format:**
```json
{
  "framework": "mbti",
  "type": "INTJ",
  "preferences": {
    "EI": "Introversion (78%)",
    "SN": "Intuition (82%)",
    "TF": "Thinking (65%)",
    "JP": "Judging (71%)"
  },
  "cognitive_stack": ["Ni", "Te", "Fi", "Se"],
  "type_description": "The Architect: Strategic, independent, and determined. You see the big picture and create long-term plans.",
  "strengths": ["Strategic thinking", "Independence", "High standards"],
  "blind_spots": ["Dismissive of emotions", "Overly critical", "Resistance to change"],
  "validity_metrics": {
    "preference_clarity": "clear",
    "response_consistency": 0.76,
    "completion_time_seconds": 720
  }
}
```

**Psychometric Properties:**
- Test-retest reliability: 0.70-0.80 (varies by type)
- Split-half reliability: 0.75-0.85
- **Note:** MBTI has lower scientific validity than Big Five, but high business adoption

---

### Framework 3: Enneagram

**Scientific Basis:** 9 personality types based on core motivations (controversial, limited peer review)

**Types:**
1. **The Reformer** - Principled, purposeful, perfectionistic
2. **The Helper** - Generous, people-pleasing, possessive
3. **The Achiever** - Adaptive, ambitious, image-conscious
4. **The Individualist** - Expressive, dramatic, self-absorbed
5. **The Investigator** - Perceptive, innovative, secretive
6. **The Loyalist** - Engaging, responsible, anxious
7. **The Enthusiast** - Spontaneous, versatile, scattered
8. **The Challenger** - Self-confident, decisive, confrontational
9. **The Peacemaker** - Receptive, reassuring, complacent

**Question Bank:**
- Total questions: 144 (Riso-Hudson Enneagram Type Indicator)
- Question type: Likert scale (Disagree to Agree) paired statements
- Sample question pairs:
  - "I have been romantic and imaginative" (Type 4)
  - "I have been pragmatic and down to earth" (Type 6)

**Scoring Algorithm:**
```python
def score_enneagram(responses: List[Response]) -> EnneagramResult:
    """
    Score Enneagram assessment using RHETI algorithm

    Args:
        responses: List of Likert scale responses

    Returns:
        EnneagramResult with dominant type and wing
    """
    # Calculate scores for all 9 types
    # Identify dominant type (highest score)
    # Identify wing (adjacent type with 2nd highest score)
    # Determine instinctual variant (self-preservation, social, sexual)
    pass
```

**Output Format:**
```json
{
  "framework": "enneagram",
  "dominant_type": 5,
  "wing": "5w6",
  "instinctual_variant": "social",
  "type_description": "Type 5 - The Investigator: Perceptive, innovative, and secretive. You seek knowledge and fear being useless or incompetent.",
  "core_desire": "To be capable and competent",
  "core_fear": "Being useless or helpless",
  "growth_path": "Move to Type 8 (become more decisive and action-oriented)",
  "stress_path": "Move to Type 7 (become scattered and unfocused)",
  "type_scores": {
    "1": 12,
    "2": 8,
    "3": 15,
    "4": 18,
    "5": 28,
    "6": 22,
    "7": 14,
    "8": 11,
    "9": 10
  },
  "validity_metrics": {
    "type_certainty": "high",
    "wing_certainty": "moderate",
    "completion_time_seconds": 900
  }
}
```

**Psychometric Properties:**
- **Caution:** Limited scientific validation, mixed psychometric evidence
- Internal consistency: 0.70-0.80 (acceptable)
- Test-retest reliability: 0.65-0.75 (moderate)

---

### Framework 4: Predictive Index (PI)

**Scientific Basis:** Four-factor behavioral assessment (PRF study)

**Dimensions:**
1. **A (Dominance)** - High: Independent, assertive | Low: Cooperative, accommodating
2. **B (Extraversion)** - High: Social, outgoing | Low: Reserved, private
3. **C (Patience)** - High: Patient, steady | Low: Fast-paced, urgent
4. **D (Formality)** - High: Disciplined, precise | Low: Informal, flexible

**Question Bank:**
- Total questions: 2 pages of adjectives (standard PI)
- Question type: Select adjectives that describe you (vs. don't describe)
- Sample adjectives:
  - Dominance: "Assertive", "Bold", "Dominant", "Forceful"
  - Extraversion: "Sociable", "Talkative", "Warm", "Responsive"
  - Patience: "Patient", "Steady", "Consistent", "Peaceful"
  - Formality: "Precise", "Conforming", "Detail-conscious", "Structured"

**Scoring Algorithm:**
```python
def score_pi(responses: List[Response]) -> PIResult:
    """
    Score Predictive Index assessment

    Args:
        responses: Selected adjectives (self-concept)

    Returns:
        PIResult with 4-factor scores
    """
    # Count adjectives per dimension
    # Calculate raw scores
    # Convert to percentile (norm-referenced)
    # Generate behavioral profile
    pass
```

**Output Format:**
```json
{
  "framework": "predictive_index",
  "scores": {
    "A_dominance": 72,
    "B_extraversion": 45,
    "C_patience": 38,
    "D_formality": 81
  },
  "behavioral_profile": "Analytical and precise, you prefer working independently with detailed plans. You're structured and disciplined, but can be impatient with slow processes.",
  "work_style": "Works best independently, values accuracy over speed, prefers clear rules and procedures",
  "management_needs": "Give autonomy, provide detailed specs, avoid micromanagement",
  "motivators": ["Achievement", "Expertise", "Efficiency"],
  "demotivators": ["Inefficiency", "Lack of clarity", "Social demands"],
  "validity_metrics": {
    "adjective_count": 42,
    "response_time_seconds": 480
  }
}
```

**Psychometric Properties:**
- Construct validity: Moderate (correlates with Big Five)
- Test-retest reliability: 0.80-0.85
- **Note:** PRF (Psychological Research Foundation) proprietary, limited independent validation

---

### Framework 5: DISC

**Scientific Basis:** Marston's DISC theory (1928) - limited scientific validation

**Dimensions:**
1. **Dominance (D)** - Direct, firm, strong-willed
2. **Influence (I)** - Outgoing, enthusiastic, optimistic
3. **Steadiness (S)** - Even-tempered, accommodating, patient
4. **Conscientiousness (C)** - Analytical, reserved, precise

**Question Bank:**
- Total questions: 24-28 (varies by vendor)
- Question type: Most/Least like me (4 adjectives per question)
- Sample question:
  - [Most like me] [Least like me] from: "Bold", "Cheerful", "Patient", "Precise"

**Scoring Algorithm:**
```python
def score_disc(responses: List[Response]) -> DISCResult:
    """
    Score DISC assessment

    Args:
        responses: Most/Least selections

    Returns:
        DISCResult with 4-quadrant profile
    """
    # Count D, I, S, C selections
    # Calculate relative percentages
    # Determine dominant style (highest %)
    # Generate behavioral insights
    pass
```

**Output Format:**
```json
{
  "framework": "disc",
  "scores": {
    "D": 35,
    "I": 20,
    "S": 25,
    "C": 20
  },
  "dominant_style": "D - Dominance",
  "style_description": "Direct and decisive, you prefer taking action and driving results. You're confident and willing to take risks.",
  "priorities": ["Results", "Action", "Challenge"],
  "fears": ["Being taken advantage of", "Losing control", "Failure"],
  "ideal_environment": "Fast-paced, autonomous, outcome-focused",
  "communication_style": "Direct, brief, to the point",
  "blind_spots": ["Impatient", "Insensitive to others", "Argumentative"],
  "validity_metrics": {
    "style_certainty": "moderate",
    "response_consistency": 0.68,
    "completion_time_seconds": 360
  }
}
```

**Psychometric Properties:**
- **Caution:** Limited scientific validation, oversimplified
- Test-retest reliability: 0.60-0.75 (fair to moderate)
- Correlation with Big Five: 0.50-0.65 (moderate)

---

## Part 3: Adaptive Questioning Engine

### Purpose
Reduce assessment completion time by 40% while maintaining psychometric validity through **Computerized Adaptive Testing (CAT)**.

### Algorithm

```python
class AdaptiveQuestioningEngine:
    """
    Implements Computerized Adaptive Testing (CAT) for personality assessments

    Algorithm:
    1. Start with medium-difficulty questions
    2. After each response, update trait estimate (theta) using IRT
    3. Select next question based on information gain (Fisher information)
    4. Stop when standard error < threshold or max questions reached
    """

    def __init__(self, framework: str):
        self.framework = framework
        self.theta_estimates = {}  # Trait estimates (e.g., O, C, E, A, N)
        self.standard_errors = {}
        self.questions_asked = []
        self.confidence_threshold = 0.80  # Stop when SE < 0.20

    def select_next_question(self) -> Question:
        """
        Select the next question that maximizes information gain

        Returns:
            Question to display next
        """
        # Calculate Fisher information for all remaining questions
        # Select question with highest information for current theta
        # Ensure content balance (don't ask 20 questions on one trait)
        pass

    def update_theta(self, response: Response):
        """
        Update trait estimate using IRT (3-parameter logistic model)

        Args:
            response: User's response to last question
        """
        # Apply IRT formula: P(theta) = c + (1-c) / (1 + exp(-a(theta - b)))
        # where: a = discrimination, b = difficulty, c = guessing
        # Update theta using maximum likelihood estimation
        pass

    def should_stop(self) -> bool:
        """
        Determine if assessment should terminate

        Returns:
            True if confidence threshold reached or max questions asked
        """
        # Stop if SE < threshold for all traits
        # Stop if max questions reached
        # Ensure minimum questions per trait (e.g., 5)
        pass
```

### Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Completion time reduction | 40% | 35% | ⚠️ In development |
| Validity correlation (vs. full) | ≥0.90 | 0.87 | ⚠️ Needs improvement |
| User satisfaction | ≥4.5/5 | 4.2/5 | ✅ On track |
| Questions per assessment | 30-40 (down from 50-93) | 38 | ✅ On track |

---

## Part 4: Cross-Framework Validation

### Purpose
Ensure consistency across frameworks and detect inconsistent responses.

### Validation Rules

1. **Expected Correlations:**
   - Big Five Extraversion ↔ MBTI E: r = 0.70+
   - Big Five Openness ↔ MBTI N: r = 0.65+
   - Big Five Conscientiousness ↔ MBTI J: r = 0.60+
   - Big Five Agreeableness ↔ DISC S: r = 0.55+

2. **Red Flags (Investigate):**
   - Correlation < 0.30 between expected mappings
   - High social desirability bias (>0.80)
   - Response time < 2 seconds per question (possible random responding)
   - Straight-lining (same answer for 10+ consecutive questions)

3. **Validation Actions:**
   - Warn user: "Your responses seem inconsistent. Please answer carefully."
   - Prompt re-take: "We couldn't score your assessment. Please try again."
   - Flag for review (for team assessments): "This user's results may not be accurate"

### Implementation

```python
class CrossFrameworkValidator:
    """
    Validates consistency across multiple personality frameworks
    """

    def validate_consistency(self, results: List[AssessmentResult]) -> ValidationResult:
        """
        Check if results from different frameworks are consistent

        Args:
            results: List of assessment results (e.g., Big Five + MBTI)

        Returns:
            ValidationResult with consistency score and flags
        """
        # Calculate cross-framework correlations
        # Compare to expected correlations
        # Flag inconsistencies
        # Generate recommendations
        pass

    def detect_invalid_responses(self, responses: List[Response]) -> List[Flag]:
        """
        Detect response patterns that indicate invalid data

        Flags:
        - Straight-lining (same answer repeatedly)
        - Random responding (response time too fast)
        - Social desirability bias (all answers in positive direction)
        - Inconsistent responses (similar questions answered differently)
        """
        pass
```

---

## Part 5: Team Composition Analysis

### Purpose
Analyze multi-user team composition and generate insights about team dynamics, compatibility, and blind spots.

### Data Requirements

- Minimum team size: 3 users
- All users must complete the same framework (e.g., all Big Five)
- Optional: Include demographic data (role, tenure, department) for subgroup analysis

### Analysis Types

1. **Team Constellation Map**
   - Visual representation of team's personality distribution
   - Identify clusters (e.g., 60% Introverted, 40% Extraverted)
   - Highlight gaps (e.g., "No one in team scores high on Agreeableness")

2. **Dyadic Compatibility**
   - Pairwise analysis of all team members
   - For 5-person team: 10 unique pairs (5 choose 2)
   - Compatibility score based on complementary vs. conflicting traits

3. **Team-Level Metrics**
   - Diversity score: How varied is the team?
   - Consensus score: How aligned is the team?
   - Risk score: Probability of conflict (from ML model)

4. **Blind Spots**
   - Traits underrepresented in the team
   - "Your team has low Agreeableness - expect direct debates"
   - "No one scores high on Openness - may struggle with innovation"

### Implementation

```python
class TeamCompositionAnalyzer:
    """
    Analyzes team composition and generates insights
    """

    def analyze_team(self, team_id: str) -> TeamInsights:
        """
        Generate team-level insights from individual assessments

        Args:
            team_id: Team to analyze

        Returns:
            TeamInsights with constellation map, compatibility, risks
        """
        # Fetch all team members' assessment results
        # Calculate team-level averages and distributions
        # Generate dyadic compatibility matrix
        # Identify blind spots and risks
        pass

    def calculate_compatibility(self, user1: AssessmentResult, user2: AssessmentResult) -> CompatibilityScore:
        """
        Calculate personality compatibility between two users

        Args:
            user1, user2: Individual assessment results

        Returns:
            CompatibilityScore (0-100) with explanation
        """
        # Compare personality dimensions
        # Calculate complementarity (opposites attract)
        # Calculate similarity (birds of feather)
        # Weight by context (e.g., communication style vs. work style)
        pass

    def predict_team_conflict(self, team_insights: TeamInsights) -> ConflictPrediction:
        """
        Predict team conflict probability using ML model

        Args:
            team_insights: Team composition data

        Returns:
            ConflictPrediction with probability and risk factors
        """
        # Load trained ML model (Random Forest)
        # Extract features: diversity, consensus, trait extremes
        # Predict conflict probability
        # Identify top risk factors
        pass
```

### Output Format

```json
{
  "team_id": "team_123",
  "framework": "big_five",
  "team_size": 8,
  "constellation_map": {
    "openness": {
      "mean": 65,
      "distribution": [45, 52, 58, 65, 72, 78, 85, 90],
      "description": "Moderately high openness - team is curious and creative"
    },
    "conscientiousness": {
      "mean": 78,
      "distribution": [70, 72, 75, 78, 80, 82, 85, 88],
      "description": "High conscientiousness - team is organized and disciplined"
    },
    "extraversion": {
      "mean": 42,
      "distribution": [25, 30, 35, 40, 45, 50, 55, 60],
      "description": "Introverted majority - team prefers focused work"
    },
    "agreeableness": {
      "mean": 55,
      "distribution": [35, 40, 45, 55, 65, 70, 75, 80],
      "description": "Balanced agreeableness - mix of direct and diplomatic styles"
    },
    "neuroticism": {
      "mean": 38,
      "distribution": [20, 25, 30, 35, 40, 45, 50, 55],
      "description": "Low neuroticism - team is calm and resilient"
    }
  },
  "blind_spots": [
    "Low Agreeableness (mean 55) - may struggle with customer-facing roles",
    "Low Extraversion (mean 42) - limited natural networkers or promoters"
  ],
  "strengths": [
    "High Conscientiousness (mean 78) - strong execution and reliability",
    "Low Neuroticism (mean 38) - resilient under pressure"
  ],
  "dyadic_compatibility": {
    "user_1_user_2": {
      "score": 78,
      "description": "Highly compatible - complementary work styles"
    },
    "user_1_user_3": {
      "score": 45,
      "description": "Moderate compatibility - may clash on decision-making speed"
    }
  },
  "conflict_prediction": {
    "probability": 0.22,
    "risk_level": "low",
    "risk_factors": [
      "Low Agreeableness + High Conscientiousness = potential rigidity"
    ]
  },
  "recommendations": [
    "Assign customer-facing roles to high-Agreeableness members (users 6, 7, 8)",
    "Encourage brainstorming sessions to leverage team's Openness",
    "Use structured decision frameworks to accommodate diverse thinking styles"
  ]
}
```

---

## Part 6: Performance Requirements

### Response Time Targets

| Operation | Target | P95 | P99 |
|-----------|--------|-----|-----|
| Single question submission | <100ms | <200ms | <500ms |
| Assessment scoring | <200ms | <400ms | <1s |
| Team composition analysis | <500ms | <1s | <2s |
| ML conflict prediction | <1s | <2s | <5s |
| Results retrieval | <100ms | <200ms | <500ms |

### Scalability Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Concurrent assessments | 10,000 | Peak usage (Monday mornings) |
| Assessments per day | 100,000 | Growth projection (Month 12) |
| Database size | 1TB assessments + responses | 1M users × 100 responses × 10KB |
| Cache hit rate | >80% | Reduce DB load, improve latency |

### Reliability Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Assessment completion rate | >95% | 92% | ⚠️ Improve error handling |
| Scoring accuracy | >99.9% | 99.95% | ✅ On track |
| Data loss rate | <0.01% | 0% | ✅ On track |
| Uptime | 99.9% (8.7 hours downtime/year) | 99.95% | ✅ Exceeding |

---

## Part 7: Data Models

### Database Schema

```sql
-- Assessments table
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework VARCHAR(50) NOT NULL, -- 'big_five', 'mbti', etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    question_count INT NOT NULL,
    estimated_duration_minutes INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Questions table
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL, -- 'likert_5', 'dichotomous', 'adjective'
    dimension VARCHAR(50), -- 'openness', 'EI', etc.
    is_reverse_coded BOOLEAN DEFAULT FALSE,
    display_order INT NOT NULL,
    irt_discrimination FLOAT, -- IRT 'a' parameter
    irt_difficulty FLOAT, -- IRT 'b' parameter
    irt_guessing FLOAT DEFAULT 0.0, -- IRT 'c' parameter
    created_at TIMESTAMP DEFAULT NOW()
);

-- Responses table (user answers)
CREATE TABLE assessment_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
    responses JSONB NOT NULL, -- [{question_id: uuid, answer: value}]
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    time_spent_seconds INT,
    ip_address INET,
    user_agent TEXT,
    validity_flags JSONB, -- {straight_lining: bool, random_responding: bool, ...}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Results table (computed scores)
CREATE TABLE assessment_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID REFERENCES assessment_responses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
    framework VARCHAR(50) NOT NULL,
    scores JSONB NOT NULL, -- Framework-specific scores
    percentiles JSONB,
    personality_summary TEXT,
    validity_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(response_id, framework)
);

-- Team insights table (cached team analytics)
CREATE TABLE team_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    framework VARCHAR(50) NOT NULL,
    constellation_map JSONB NOT NULL,
    blind_spots JSONB,
    strengths JSONB,
    dyadic_compatibility JSONB,
    conflict_prediction JSONB,
    recommendations JSONB,
    last_member_assessment_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(team_id, framework)
);

-- Create indexes for performance
CREATE INDEX idx_responses_user_id ON assessment_responses(user_id);
CREATE INDEX idx_responses_team_id ON assessment_responses(team_id);
CREATE INDEX idx_results_user_id ON assessment_results(user_id);
CREATE INDEX idx_results_team_id ON assessment_results(team_id);
CREATE INDEX idx_insights_team_id ON team_insights(team_id);
```

### API Response Models (Pydantic)

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuestionResponse(BaseModel):
    id: str
    assessment_id: str
    question_text: str
    question_type: str
    dimension: Optional[str]
    display_order: int

class AssessmentSubmitRequest(BaseModel):
    assessment_id: str
    responses: List[Dict[str, Any]]  # [{question_id: str, answer: Any}]

class BigFiveScores(BaseModel):
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int

class AssessmentResultResponse(BaseModel):
    id: str
    user_id: str
    framework: str
    scores: Dict[str, Any]
    personality_summary: str
    validity_metrics: Dict[str, Any]
    created_at: datetime

class TeamInsightsResponse(BaseModel):
    team_id: str
    framework: str
    constellation_map: Dict[str, Any]
    blind_spots: List[str]
    strengths: List[str]
    dyadic_compatibility: Dict[str, Dict[str, Any]]
    conflict_prediction: Dict[str, Any]
    recommendations: List[str]
```

---

## Part 8: Security & Privacy

### Data Protection

1. **Encryption at Rest:**
   - All assessment responses encrypted (AES-256)
   - Results encrypted with customer-specific keys
   - Database encryption enabled (PostgreSQL TDE)

2. **Encryption in Transit:**
   - TLS 1.3 for all API communications
   - Certificate pinning for mobile apps

3. **Access Controls:**
   - Role-based access (RBAC) enforced at API level
   - Users can only see their own results (and team results if authorized)
   - Audit logging for all data access

4. **Data Retention:**
   - Raw responses: Retain for 2 years, then archive
   - Aggregated results: Retain indefinitely
   - User deletion: Full data purge within 30 days (GDPR/CCPA)

5. **Anonymization:**
   - ML training data anonymized (remove PII)
   - Research data scrubbed of identifying information
   - Team insights don't expose individual scores without consent

### Compliance

- **SOC 2 Type II:** Certified (security, availability, confidentiality)
- **GDPR:** Compliant (data portability, right to erasure)
- **CCPA:** Compliant (opt-out, data deletion)
- **ISO 27001:** In progress (target Q3 2025)

---

## Part 9: Testing Strategy

### Unit Tests

- Scoring algorithms: Test against known outputs (validated datasets)
- Adaptive questioning: Mock responses, verify question selection
- Cross-framework validation: Test consistency checks

### Integration Tests

- Full assessment flow: Submit → Score → Results
- Team composition: Simulate 5-user team, verify insights
- ML predictions: Test conflict prediction accuracy

### Psychometric Validation

- **Test-Retest Reliability:** Subset of users retake assessment (2-week interval)
- **Internal Consistency:** Calculate Cronbach's alpha per dimension
- **Convergent Validity:** Compare with established measures (e.g., IPIP-NEO)
- **Known-Groups Validity:** Verify differences between known groups (e.g., artists vs. accountants on Openness)

### Performance Tests

- Load test: 10,000 concurrent assessments
- Stress test: Find breaking point (target: >20,000 concurrent)
- Latency test: Verify P95/P99 targets under load

---

## Part 10: Implementation Roadmap

### Phase 1: Core Frameworks (Weeks 1-8)

**Deliverables:**
- [ ] Big Five processor (complete ✅)
- [ ] MBTI processor (complete ✅)
- [ ] Enneagram processor (complete ✅)
- [ ] Basic scoring algorithms
- [ ] API endpoints for assessments and results

**Success Criteria:**
- All 3 frameworks pass psychometric validation
- API response times <200ms (P95)
- Unit test coverage >80%

---

### Phase 2: Team Analytics (Weeks 9-12)

**Deliverables:**
- [ ] Team composition analyzer
- [ ] Dyadic compatibility scoring
- [ ] Constellation map visualization
- [ ] Blind spot detection

**Success Criteria:**
- Support teams up to 100 users
- Team insights generated in <500ms
- Customer feedback >4.0/5 on usefulness

---

### Phase 3: Adaptive Questioning (Weeks 13-16)

**Deliverables:**
- [ ] IRT parameter estimation for all questions
- [ ] CAT implementation for Big Five
- [ ] Validation study (adaptive vs. full assessment)
- [ ] Performance optimization

**Success Criteria:**
- 40% reduction in completion time
- Validity correlation ≥0.90 with full assessment
- User satisfaction >4.5/5

---

### Phase 4: ML Predictions (Weeks 17-20)

**Deliverables:**
- [ ] Conflict prediction model (Random Forest)
- [ ] Training dataset (10K teams)
- [ ] Model validation (accuracy >75%)
- [ ] API endpoint for predictions

**Success Criteria:**
- Conflict prediction accuracy >75%
- False positive rate <20%
- Customer adoption >60% (teams use insights)

---

### Phase 5: Additional Frameworks (Weeks 21-24)

**Deliverables:**
- [ ] Predictive Index processor
- [ ] DISC processor
- [ ] Cross-framework validation
- [ ] Custom assessment builder

**Success Criteria:**
- All 5 frameworks validated
- Cross-framework consistency checks operational
- Custom assessments available in self-serve

---

**Next Steps:**
1. Review and approve technical requirements
2. Assign engineering resources (2 backend + 1 data scientist)
3. Set up development environment and database
4. Begin Phase 1 implementation (Big Five, MBTI, Enneagram)
5. Schedule bi-weekly requirement review meetings

---

*For questions or feedback, contact: engineering@psychsync.io*
