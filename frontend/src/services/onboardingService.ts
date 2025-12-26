// src/services/onboardingService.ts
// Frontend service for value-first onboarding API calls
import { apiClient } from './api';

export interface QuickAssessmentRequest {
  role: 'manager' | 'hr' | 'lead' | 'member' | 'executive';
  challenge: 'communication' | 'productivity' | 'turnover' | 'collaboration' | 'conflict';
  team_size?: string;
  industry?: string;
  session_id?: string;
  referrer?: string;
}

export interface Recommendation {
  title: string;
  description: string;
  priority: 'High' | 'Medium' | 'Low';
  effort: 'Low' | 'Medium' | 'High';
  expected_outcome: string;
}

export interface QuickInsights {
  primary_benefit: string;
  risk_areas: string[];
  strengths: string[];
  opportunities: string[];
  recommendations: Recommendation[];
  conversion_probability: number;
  estimated_time_to_value: string;
}

export interface QuickAssessmentResponse {
  success: boolean;
  insights: QuickInsights;
  next_steps: string[];
  value_proposition: string;
  estimated_time_to_value: string;
}

export interface ConversionEvent {
  event_type: string;
  session_id: string;
  data?: Record<string, any>;
}

class OnboardingService {
  private sessionId: string;

  constructor() {
    // Generate or retrieve session ID for tracking
    this.sessionId = this.getOrCreateSessionId();
  }

  private getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('psychsync_session_id');
    if (!sessionId) {
      sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      sessionStorage.setItem('psychsync_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Generate instant team insights from role and challenge
   * This is the core of the value-first onboarding experience
   */
  async generateQuickInsights(request: Omit<QuickAssessmentRequest, 'session_id'>): Promise<QuickAssessmentResponse> {
    try {
      const response = await apiClient.post('/onboarding/quick-assessment', {
        ...request,
        session_id: this.sessionId
      });

      // Track conversion event
      await this.trackConversionEvent('quick_assessment_completed', {
        role: request.role,
        challenge: request.challenge,
        conversion_probability: response.data.insights.conversion_probability
      });

      return response.data;
    } catch (error) {
      console.error('Failed to generate quick insights:', error);

      // Fallback to client-side insights if API fails
      return this.generateFallbackInsights(request.role, request.challenge);
    }
  }

  /**
   * Get user's onboarding status and recommended next steps
   */
  async getOnboardingStatus(): Promise<any> {
    try {
      const response = await apiClient.get('/onboarding/onboarding-status');
      return response.data;
    } catch (error) {
      console.error('Failed to get onboarding status:', error);
      return this.getFallbackOnboardingStatus();
    }
  }

  /**
   * Handle progressive setup wizard steps
   */
  async processSetupStep(step: string, data: Record<string, any>): Promise<any> {
    try {
      const response = await apiClient.post('/onboarding/setup-wizard', {
        step,
        data,
        session_id: this.sessionId
      });

      // Track step completion
      await this.trackConversionEvent('setup_step_completed', {
        step,
        success: response.data.success
      });

      return response.data;
    } catch (error) {
      console.error('Failed to process setup step:', error);
      throw error;
    }
  }

  /**
   * Track conversion events for analytics and optimization
   */
  async trackConversionEvent(eventType: string, data?: Record<string, any>): Promise<void> {
    try {
      await apiClient.post('/onboarding/track-conversion', {
        event_type: eventType,
        session_id: this.sessionId,
        data,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      // Don't fail the user experience for analytics tracking
      console.warn('Failed to track conversion event:', error);
    }
  }

  /**
   * Get real-time value metrics for the user's team
   */
  async getValueMetrics(): Promise<any> {
    try {
      const response = await apiClient.get('/onboarding/value-metrics');
      return response.data;
    } catch (error) {
      console.error('Failed to get value metrics:', error);
      return this.getFallbackValueMetrics();
    }
  }

  /**
   * Generate detailed team insights for registered users
   */
  async getDetailedTeamInsights(teamId?: string, assessmentData?: any): Promise<any> {
    try {
      const response = await apiClient.post('/onboarding/team-insights', {
        team_id: teamId,
        assessment_data: assessmentData,
        session_id: this.sessionId
      });

      // Track team insights generation
      await this.trackConversionEvent('team_insights_generated', {
        team_id: teamId,
        insights_count: response.data.detailed_insights?.length || 0
      });

      return response.data;
    } catch (error) {
      console.error('Failed to get detailed team insights:', error);
      throw error;
    }
  }

  /**
   * Fallback insights generation for offline/API failure scenarios
   */
  private generateFallbackInsights(role: string, challenge: string): QuickAssessmentResponse {
    const fallbackData: Record<string, any> = {
      manager: {
        communication: {
          primary_benefit: "Reduce team misunderstandings by 60% and save 8+ hours of productivity monthly",
          risk_areas: ["Information silos", "Misaligned expectations"],
          strengths: ["Natural leadership", "Goal-oriented"],
          opportunities: ["Improved meeting efficiency", "Better documentation"],
          conversion_probability: 0.75,
          estimated_time_to_value: "2 weeks"
        },
        productivity: {
          primary_benefit: "Increase team output by 25% through better role alignment",
          risk_areas: ["Role misalignment", "Low engagement"],
          strengths: ["Process optimization", "Resource management"],
          opportunities: ["Automation opportunities", "Skill development"],
          conversion_probability: 0.72,
          estimated_time_to_value: "1 month"
        }
      },
      hr: {
        turnover: {
          primary_benefit: "Identify turnover risk 6 months early and reduce replacement costs by $500K+",
          risk_areas: ["High performers at risk", "Poor culture fit"],
          strengths: ["Retention strategies", "Culture assessment"],
          opportunities: ["Retention programs", "Culture initiatives"],
          conversion_probability: 0.80,
          estimated_time_to_value: "6 months"
        }
      }
    };

    const roleData = fallbackData[role]?.[challenge] || fallbackData.manager.communication;

    return {
      success: true,
      insights: {
        ...roleData,
        recommendations: [
          {
            title: "Schedule team assessment",
            description: "Complete comprehensive team behavioral analysis",
            priority: "High" as const,
            effort: "Low" as const,
            expected_outcome: "Get personalized insights for team optimization"
          }
        ]
      },
      next_steps: [
        "Create your account to save these insights",
        "Set up your team for detailed analysis"
      ],
      value_proposition: `As a ${role}, you can improve team performance`,
      estimated_time_to_value: roleData.estimated_time_to_value
    };
  }

  /**
   * Fallback onboarding status
   */
  private getFallbackOnboardingStatus() {
    const hasStartedQuickAssessment = sessionStorage.getItem('quick_assessment_started');
    const hasCompletedQuickAssessment = sessionStorage.getItem('quick_assessment_completed');

    return {
      is_authenticated: false,
      onboarding_complete: false,
      current_step: hasCompletedQuickAssessment ? 'signup_prompt' : 'quick_assessment',
      completed_steps: hasCompletedQuickAssessment ? ['quick_assessment'] : [],
      recommended_actions: hasCompletedQuickAssessment
        ? ['Create account to save insights', 'Set up your team']
        : ['Try the 2-minute assessment to see instant value'],
      progress_percentage: hasCompletedQuickAssessment ? 0.5 : 0.1,
      estimated_remaining_time: hasCompletedQuickAssessment ? '3 minutes' : '2 minutes'
    };
  }

  /**
   * Fallback value metrics
   */
  private getFallbackValueMetrics() {
    return {
      productivity_improvement: 0.23,
      communication_efficiency: 0.45,
      conflict_reduction: 0.60,
      turnover_risk_reduction: 0.35,
      team_satisfaction_score: 0.78,
      roi_estimate: 3.2,
      time_to_value: "6 weeks",
      monthly_value_created: 12500.0
    };
  }

  /**
   * Get role display name
   */
  getRoleDisplayName(role: string): string {
    const roleNames: Record<string, string> = {
      'manager': 'Team Manager',
      'hr': 'HR Professional',
      'lead': 'Team Lead',
      'member': 'Team Member',
      'executive': 'Executive'
    };
    return roleNames[role] || role;
  }

  /**
   * Get challenge display name
   */
  getChallengeDisplayName(challenge: string): string {
    const challengeNames: Record<string, string> = {
      'communication': 'Communication Issues',
      'productivity': 'Low Productivity',
      'turnover': 'High Turnover',
      'collaboration': 'Poor Collaboration',
      'conflict': 'Team Conflict'
    };
    return challengeNames[challenge] || challenge;
  }

  /**
   * Format conversion probability for display
   */
  formatConversionProbability(probability: number): string {
    return `${Math.round(probability * 100)}%`;
  }

  /**
   * Estimate time savings based on role and challenge
   */
  estimateTimeSavings(role: string, challenge: string): string {
    const timeSavings: Record<string, Record<string, string>> = {
      manager: {
        communication: '8+ hours saved per week',
        productivity: '20% increase in output',
        turnover: '$200K+ saved annually',
        collaboration: '30% faster project completion'
      },
      hr: {
        turnover: '$500K+ saved in replacement costs',
        communication: '50% improvement in cross-department collaboration',
        productivity: '15% increase in organizational productivity'
      }
    };

    return timeSavings[role]?.[challenge] || 'Significant team improvements';
  }
}

// Export singleton instance
export const onboardingService = new OnboardingService();
export default onboardingService;