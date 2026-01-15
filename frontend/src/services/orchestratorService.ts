// src/services/orchestratorService.ts
// AI Assessment Orchestrator - Intelligent assessment recommendation engine
import {
  UserContext,
  Recommendation,
  OrchestratorResponse,
  OrchestratorInsight,
  AssessmentPath,
  OrchestratorConfig,
  AssessmentCategory,
  AssessmentFramework,
} from '../types/orchestrator';

/**
 * Team composition analysis for balanced team recommendations
 */
interface TeamComposition {
  personality: {
    dominant: string[];
    missing: string[];
    balanced: boolean;
  };
  diversity: number; // 0-1 score
  gaps: string[];
}

/**
 * AI Assessment Orchestrator Service
 * Uses rule-based ML to recommend personalized assessments
 * TODO: Integrate with actual AI/ML backend
 */
class OrchestratorService {
  private assessmentDatabase: Map<string, Recommendation>;

  constructor() {
    this.assessmentDatabase = this.initializeAssessmentDatabase();
  }

  /**
   * Get personalized assessment recommendations
   */
  async getRecommendations(
    userContext: UserContext,
    config: OrchestratorConfig = { maxRecommendations: 5 }
  ): Promise<OrchestratorResponse> {
    const recommendations = this.generateRecommendations(userContext, config);
    const insights = this.generateInsights(userContext);
    const personalizedPath = this.generatePersonalizedPath(userContext);

    return {
      topRecommendations: recommendations.slice(0, config.maxRecommendations),
      personalizedPath,
      insights,
      alternatives: recommendations.slice(config.maxRecommendations),
      totalOptions: recommendations.length,
      generatedAt: new Date().toISOString(),
    };
  }

  /**
   * Analyze team composition for balanced recommendations
   */
  private analyzeTeamComposition(userContext: UserContext): TeamComposition | null {
    if (!userContext.teamSize || userContext.teamSize < 2) return null;

    // Mock team composition analysis
    // In production, this would aggregate actual team assessment data
    const composition: TeamComposition = {
      personality: {
        dominant: ['Conscientiousness', 'Agreeableness'], // Mock dominant traits
        missing: ['Openness to Experience'], // Mock missing trait
        balanced: false,
      },
      diversity: 0.65, // Mock diversity score (0-1)
      gaps: ['Creative thinking', 'Risk tolerance'], // Mock capability gaps
    };

    return composition;
  }

  /**
   * Get seasonal/temporal recommendations
   */
  private getTemporalRecommendations(
    userContext: UserContext,
    recommendations: Recommendation[]
  ): Recommendation[] {
    const currentMonth = new Date().getMonth();
    const seasonalRecs: Recommendation[] = [];

    // Winter (Dec-Feb): New Year, self-reflection
    if (currentMonth >= 11 || currentMonth <= 1) {
      if (!userContext.previousAssessments.some(a => a.framework === 'enneagram')) {
        seasonalRecs.push(this.assessmentDatabase.get('enneagram')!);
      }
    }

    // Spring (Mar-May): Growth, development
    if (currentMonth >= 2 && currentMonth <= 4) {
      if (!userContext.previousAssessments.some(a => a.framework === 'strengthsfinder')) {
        seasonalRecs.push(this.assessmentDatabase.get('strengthsfinder')!);
      }
    }

    // Summer (Jun-Aug): Team building, leadership
    if (currentMonth >= 5 && currentMonth <= 7) {
      if (userContext.role === 'team_lead' || userContext.role === 'hr_manager') {
        if (!userContext.previousAssessments.some(a => a.framework === 'disc')) {
          seasonalRecs.push(this.assessmentDatabase.get('disc')!);
        }
      }
    }

    // Fall (Sep-Nov): Planning, strategy
    if (currentMonth >= 8 && currentMonth <= 10) {
      if (!userContext.previousAssessments.some(a => a.framework === 'predictive_index')) {
        seasonalRecs.push(this.assessmentDatabase.get('predictive_index')!);
      }
    }

    return seasonalRecs;
  }

  /**
   * Generate team-balanced recommendations
   */
  private getTeamBalancedRecommendations(
    userContext: UserContext,
    teamComp: TeamComposition
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // If team lacks diversity, recommend varied assessments
    if (teamComp.diversity < 0.5) {
      recommendations.push(this.assessmentDatabase.get('big_five')!);
      recommendations.push(this.assessmentDatabase.get('mbti')!);
    }

    // If team has personality gaps, recommend specific assessments
    if (teamComp.personality.missing.includes('Openness to Experience')) {
      const rec = this.assessmentDatabase.get('big_five');
      if (rec) {
        recommendations.push({
          ...rec,
          reasoning: [
            'Your team lacks creative and innovative thinkers',
            'Big Five can help identify openness to experience',
            'Balanced teams perform better on complex tasks',
          ],
        });
      }
    }

    return recommendations;
  }

  /**
   * Generate personalized assessment path
   */
  private generatePersonalizedPath(userContext: UserContext): AssessmentPath | undefined {
    const { role, goals, previousAssessments } = userContext;

    // If user is new, start with basics
    if (previousAssessments.length === 0) {
      return {
        pathId: 'onboarding',
        name: 'PsychSync Discovery Journey',
        description: 'Start your self-discovery with our foundational assessments',
        duration: 45,
        assessments: [
          this.assessmentDatabase.get('big_five')!,
          this.assessmentDatabase.get('mbti')!,
          this.assessmentDatabase.get('strengthsfinder')!,
        ],
        expectedOutcome: 'Comprehensive understanding of your personality, work style, and strengths',
        difficulty: 'beginner',
        targetAudience: ['everyone'],
      };
    }

    // If user has completed basics, suggest intermediate
    if (previousAssessments.length >= 3 && previousAssessments.length < 7) {
      return {
        pathId: 'growth',
        name: 'Growth & Development Path',
        description: 'Deepen your understanding and unlock advanced insights',
        duration: 60,
        assessments: [
          this.assessmentDatabase.get('enneagram')!,
          this.assessmentDatabase.get('disc')!,
          this.assessmentDatabase.get('predictive_index')!,
        ],
        expectedOutcome: 'Advanced behavioral insights and team dynamics understanding',
        difficulty: 'intermediate',
        targetAudience: ['professionals', 'team_leads'],
      };
    }

    return undefined;
  }

  /**
   * Generate actionable insights based on user context
   */
  private generateInsights(userContext: UserContext): OrchestratorInsight[] {
    const insights: OrchestratorInsight[] = [];
    const { previousAssessments, completionRate, timeSinceLastAssessment, goals, teamSize } = userContext;

    // Insight: Completion rate opportunity
    if (completionRate < 70) {
      insights.push({
        type: 'opportunity',
        title: 'Improve Completion Rate',
        description: `Your completion rate is ${completionRate}%. Shorter assessments might help you finish more.`,
        actionable: true,
        recommendations: [
          'Start with PHQ-9 (5 min)',
          'Try GAD-7 (3 min)',
          'Complete Big Five (10 min) over multiple sessions',
        ],
      });
    }

    // Insight: Team composition gap
    const teamComp = this.analyzeTeamComposition(userContext);
    if (teamComp && !teamComp.personality.balanced) {
      insights.push({
        type: 'gap',
        title: 'Balance Your Team',
        description: `Your team lacks diversity in ${teamComp.personality.missing.join(' and ')}. Consider assessments that identify these traits during hiring.`,
        actionable: true,
        recommendations: [
          'Use Predictive Index for hiring',
          'Assess candidates for missing traits',
          'Build complementary teams',
        ],
      });
    }

    // Insight: Assessment category gap
    const completedCategories = new Set(previousAssessments.map(a => a.category));
    if (!completedCategories.has('clinical') && !completedCategories.has('strengths')) {
      insights.push({
        type: 'gap',
        title: 'Explore New Areas',
        description: 'You haven\'t tried clinical tools or strengths assessments yet',
        actionable: true,
        recommendations: [
          'Discover your strengths with CliftonStrengths',
          'Check your wellbeing with our clinical screening',
        ],
      });
    }

    // Insight: Time to reassess
    if (timeSinceLastAssessment > 90) {
      insights.push({
        type: 'next_step',
        title: 'Track Your Progress',
        description: 'It\'s been 90+ days since your last assessment. Time to check your progress!',
        actionable: true,
        recommendations: [
          'Retake Big Five to see personality evolution',
          'Compare your stress levels over time',
          'Update your team profile',
        ],
      });
    }

    // Insight: Goal alignment
    if (goals.includes('leadership_development') && !completedCategories.has('behavioral')) {
      insights.push({
        type: 'opportunity',
        title: 'Leadership Development Opportunity',
        description: 'Behavioral assessments can accelerate your leadership growth',
        actionable: true,
        recommendations: [
          'Take Predictive Index for leadership insights',
          'Complete Social Styles for communication mastery',
        ],
      });
    }

    // Insight: Seasonal opportunity
    const currentMonth = new Date().getMonth();
    if (currentMonth >= 11 || currentMonth <= 1) {
      insights.push({
        type: 'trend',
        title: 'New Year, New You',
        description: 'Start the year with deeper self-awareness. Enneagram is perfect for New Year reflections.',
        actionable: true,
        recommendations: [
          'Take Enneagram for self-discovery',
          'Set development goals based on results',
          'Share with your team for better understanding',
        ],
      });
    }

    return insights;
  }

  /**
   * Generate recommendations using enhanced rule-based logic
   * Includes team composition and temporal rules
   */
  private generateRecommendations(
    userContext: UserContext,
    config: OrchestratorConfig
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];
    const { role, previousAssessments, goals, completionRate } = userContext;

    const completedFrameworks = new Set(
      previousAssessments.map(a => a.framework)
    );

    // Helper to add recommendation
    const addRec = (assessment: Recommendation, priority: 'high' | 'medium' | 'low') => {
      if (
        !config.excludeFrameworks?.includes(assessment.framework) &&
        (!config.maxTimeAvailable || assessment.estimatedTime <= config.maxTimeAvailable) &&
        (!config.categories || config.categories.includes(assessment.category))
      ) {
        recommendations.push({ ...assessment, priority });
      }
    };

    // Rule 1: If completion rate is low, prioritize short assessments
    if (completionRate < 60) {
      addRec(this.assessmentDatabase.get('gad7')!, 'high');
      addRec(this.assessmentDatabase.get('phq9')!, 'high');
    }

    // Rule 2: If new user, start with foundational
    if (previousAssessments.length === 0) {
      addRec(this.assessmentDatabase.get('big_five')!, 'high');
      addRec(this.assessmentDatabase.get('mbti')!, 'high');
      addRec(this.assessmentDatabase.get('strengthsfinder')!, 'medium');
    }

    // Rule 3: HR/Team role → prioritize team assessments
    if (role === 'hr_manager' || role === 'team_lead') {
      if (!completedFrameworks.has('predictive_index')) {
        addRec(this.assessmentDatabase.get('predictive_index')!, 'high');
      }
      if (!completedFrameworks.has('disc')) {
        addRec(this.assessmentDatabase.get('disc')!, 'high');
      }
    }

    // Rule 4: Clinical interest → suggest clinical tools
    if (config.includeClinicalTools && !completedFrameworks.has('phq9')) {
      addRec(this.assessmentDatabase.get('phq9')!, 'medium');
      addRec(this.assessmentDatabase.get('gad7')!, 'medium');
    }

    // Rule 5: Goal-based recommendations
    if (goals.includes('self_awareness') && !completedFrameworks.has('enneagram')) {
      addRec(this.assessmentDatabase.get('enneagram')!, 'medium');
    }

    if (goals.includes('team_optimization') && !completedFrameworks.has('social_styles')) {
      addRec(this.assessmentDatabase.get('social_styles')!, 'medium');
    }

    // Rule 6: Team composition-based recommendations
    const teamComp = this.analyzeTeamComposition(userContext);
    if (teamComp && !teamComp.personality.balanced) {
      const teamRecs = this.getTeamBalancedRecommendations(userContext, teamComp);
      teamRecs.forEach(rec => {
        if (!completedFrameworks.has(rec.framework)) {
          addRec(rec, 'high');
        }
      });
    }

    // Rule 7: Temporal/seasonal recommendations
    const seasonalRecs = this.getTemporalRecommendations(userContext, recommendations);
    seasonalRecs.forEach(rec => {
      if (!completedFrameworks.has(rec.framework)) {
        const seasonalReasoning = [...(rec.reasoning || []), `Perfect for this time of year!`];
        addRec({ ...rec, reasoning: seasonalReasoning }, 'medium');
      }
    });

    // Rule 8: Add complementary assessments
    if (completedFrameworks.has('big_five') && !completedFrameworks.has('mbti')) {
      addRec(this.assessmentDatabase.get('mbti')!, 'medium');
    }

    if (completedFrameworks.has('mbti') && !completedFrameworks.has('enneagram')) {
      addRec(this.assessmentDatabase.get('enneagram')!, 'low');
    }

    // Rule 9: Time-based diversification (reassessment)
    if (userContext.timeSinceLastAssessment > 60 && completedFrameworks.has('big_five')) {
      const reassessment = {
        ...this.assessmentDatabase.get('big_five')!,
        reasoning: [
          'It\'s been 60+ days since your last assessment',
          'Personalities evolve over time',
          'Track your growth and changes',
        ],
      };
      addRec(reassessment, 'medium'); // Re-take
    }

    // Rule 10: Adaptive difficulty based on completion
    const completedCount = previousAssessments.filter(a => !a.incomplete && !a.skipped).length;
    if (completedCount >= 5 && completedCount < 10) {
      // Suggest intermediate assessments
      if (!completedFrameworks.has('disc') && !completedFrameworks.has('social_styles')) {
        addRec(this.assessmentDatabase.get('social_styles')!, 'medium');
      }
    }

    if (completedCount >= 10) {
      // Suggest advanced assessments
      if (!completedFrameworks.has('enneagram')) {
        addRec(this.assessmentDatabase.get('enneagram')!, 'low');
      }
    }

    // Sort by priority and confidence
    recommendations.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority] || b.confidence - a.confidence;
    });

    return recommendations;
  }

  /**
   * Initialize the assessment knowledge base
   */
  private initializeAssessmentDatabase(): Map<string, Recommendation> {
    return new Map([
      [
        'big_five',
        {
          assessmentId: 'big_five',
          framework: 'big_five',
          category: 'personality',
          name: 'Big Five Personality Test',
          description: 'Discover your personality across 5 key traits: Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism',
          estimatedTime: 15,
          priority: 'high',
          confidence: 0.95,
          reasoning: ['Most scientifically validated personality framework', 'Foundation for all other assessments'],
          benefits: [
            'Understand your core personality traits',
            'Compare with population norms',
            'Foundation for personal development',
          ],
          relatedAssessments: ['mbti', 'enneagram', 'disc'],
        },
      ],
      [
        'mbti',
        {
          assessmentId: 'mbti',
          framework: 'mbti',
          category: 'personality',
          name: 'Myers-Briggs Type Indicator',
          description: 'Discover your 4-letter personality type and how it influences your work style, relationships, and decision-making',
          estimatedTime: 20,
          priority: 'high',
          confidence: 0.92,
          reasoning: ['Popular and widely used in organizations', 'Easy to understand and apply'],
          benefits: [
            'Learn your natural preferences',
            'Improve communication',
            'Better career fit',
          ],
          relatedAssessments: ['big_five', 'enneagram'],
        },
      ],
      [
        'enneagram',
        {
          assessmentId: 'enneagram',
          framework: 'enneagram',
          category: 'personality',
          name: 'Enneagram Personality Type',
          description: 'Explore your core motivations and fears through the ancient Enneagram system',
          estimatedTime: 25,
          priority: 'medium',
          confidence: 0.88,
          reasoning: ['Deep insight into motivations', 'Popular for personal growth'],
          benefits: [
            'Understand your core motivations',
            'Identify growth opportunities',
            'Improve relationships',
          ],
          prerequisites: ['Basic self-awareness helpful'],
          relatedAssessments: ['mbti', 'big_five'],
        },
      ],
      [
        'disc',
        {
          assessmentId: 'disc',
          framework: 'disc',
          category: 'behavioral',
          name: 'DISC Assessment',
          description: 'Understand your behavioral style across four dimensions: Dominance, Influence, Steadiness, and Conscientiousness',
          estimatedTime: 15,
          priority: 'high',
          confidence: 0.90,
          reasoning: ['Excellent for team dynamics', 'Simple to apply in workplace'],
          benefits: [
            'Improve team communication',
            'Understand conflict styles',
            'Better leadership approach',
          ],
          relatedAssessments: ['predictive_index', 'social_styles'],
        },
      ],
      [
        'predictive_index',
        {
          assessmentId: 'predictive_index',
          framework: 'predictive_index',
          category: 'behavioral',
          name: 'Predictive Index',
          description: 'Science-based behavioral assessment for hiring and team optimization',
          estimatedTime: 10,
          priority: 'high',
          confidence: 0.93,
          reasoning: ['Validated for workplace use', 'Great for hiring decisions'],
          benefits: [
            'Build better teams',
            'Improve hiring accuracy',
            'Reduce turnover',
          ],
          relatedAssessments: ['disc', 'big_five'],
        },
      ],
      [
        'strengthsfinder',
        {
          assessmentId: 'strengthsfinder',
          framework: 'clifton_strengths',
          category: 'strengths',
          name: 'CliftonStrengths Assessment',
          description: 'Discover your top 5 talents and learn to develop them into strengths',
          estimatedTime: 45,
          priority: 'medium',
          confidence: 0.89,
          reasoning: ['Focus on what you do best', 'Positive psychology approach'],
          benefits: [
            'Identify your natural talents',
            'Increase engagement',
            'Boost performance',
          ],
          relatedAssessments: ['big_five', 'enneagram'],
        },
      ],
      [
        'social_styles',
        {
          assessmentId: 'social_styles',
          framework: 'social_styles',
          category: 'behavioral',
          name: 'Social Styles Assessment',
          description: 'Learn your interpersonal style and how to adapt to others',
          estimatedTime: 12,
          priority: 'medium',
          confidence: 0.85,
          reasoning: ['Practical for workplace relationships', 'Quick to complete'],
          benefits: [
            'Improve communication',
            'Better teamwork',
            'Sales effectiveness',
          ],
          relatedAssessments: ['disc', 'predictive_index'],
        },
      ],
      [
        'phq9',
        {
          assessmentId: 'phq9',
          framework: 'phq9',
          category: 'clinical',
          name: 'PHQ-9 Depression Screening',
          description: 'Validated screening tool for depression symptoms',
          estimatedTime: 5,
          priority: 'medium',
          confidence: 0.95,
          reasoning: ['Quick and validated', 'Clinical grade tool'],
          benefits: [
            'Screen for depression',
            'Track symptoms over time',
            'Inform healthcare decisions',
          ],
          relatedAssessments: ['gad7'],
        },
      ],
      [
        'gad7',
        {
          assessmentId: 'gad7',
          framework: 'gad7',
          category: 'clinical',
          name: 'GAD-7 Anxiety Screening',
          description: 'Validated screening tool for anxiety symptoms',
          estimatedTime: 3,
          priority: 'medium',
          confidence: 0.94,
          reasoning: ['Very quick', 'Clinically validated'],
          benefits: [
            'Screen for anxiety',
            'Monitor treatment progress',
            'Quick check-in tool',
          ],
          relatedAssessments: ['phq9'],
        },
      ],
    ]);
  }
}

export const orchestratorService = new OrchestratorService();
