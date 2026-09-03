// AI Service - Connects frontend to AI engine endpoints
import { apiClient } from './api';
import axios from 'axios';
import { safeJSONParse } from '../utils/safeJSON';

// Create a separate axios instance for AI requests that don't require authentication
const aiApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/v1` : (import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1'),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Enhanced AI client that supports both authenticated and non-authenticated requests
const createAuthenticatedAIClient = (token?: string) => {
  return axios.create({
    baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/v1` : (import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1'),
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });
};

export interface AIProcessingRequest {
  framework: string;
  data: Record<string, any>;
}

export interface AIProcessingResponse {
  success: boolean;
  framework: string;
  processed_at: string;
  confidence: number;
  results: Record<string, any>;
  processed_by: string;
  error?: string;
  fallback?: boolean;
}

export interface PersonalityFramework {
  id: string;
  name: string;
  description: string;
  icon: string;
  duration?: number;
  questions?: number;
}

class AIService {
  private baseUrl = '/personality-assessments';

  /**
   * Process personality assessment data using AI engine
   */
  async processAssessment(request: AIProcessingRequest): Promise<AIProcessingResponse> {
    try {
      // Try the public endpoint first (no authentication required)
      const response = await aiApiClient.post(`${this.baseUrl}/process-public`, request);
      console.log('✅ AI Processing successful using public endpoint');
      return response.data as any;
    } catch (error: any) {
      console.log('⚠️ Public endpoint failed, trying authenticated endpoint...');
      try {
        // Fallback to authenticated endpoint if public fails
        const response = await apiClient.post(`${this.baseUrl}/process-public`, request);
        console.log('✅ AI Processing successful using authenticated endpoint');
        return response.data as any;
      } catch (authError: any) {
        console.error('❌ Both AI endpoints failed:', authError);
        throw new Error(authError.response?.data?.detail || 'Failed to process assessment');
      }
    }
  }

  /**
   * Get available personality frameworks
   */
  async getAvailableFrameworks(): Promise<PersonalityFramework[]> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/frameworks`);
      return response.data as any;
    } catch (error: any) {
      console.error('Error fetching frameworks:', error);
      // Return fallback frameworks
      return this.getFallbackFrameworks();
    }
  }

  /**
   * Test AI engine availability with simple error handling
   */
  async testAIEngine(retryCount: number = 0): Promise<boolean> {
    try {
      const testData: AIProcessingRequest = {
        framework: 'mbti',
        data: { type: 'INTJ', confidence: 0.9 }
      };

      const response = await aiApiClient.post(`${this.baseUrl}/process-public`, testData);

      // Cache successful result
      if (response.data.success) {
        localStorage.setItem('ai_last_result', JSON.stringify(response.data));
      }

      return response.data.success === true;
    } catch (error) {
      console.error('AI engine test failed:', error);
      return false;
    }
  }

  /**
   * Get AI-powered insights for MBTI type with simple error handling
   */
  async getMBTIInsights(type: string): Promise<Record<string, any>> {
    try {
      const testData: AIProcessingRequest = {
        framework: 'mbti',
        data: { type: type.toUpperCase(), confidence: 1.0 }
      };

      const response = await aiApiClient.post(`${this.baseUrl}/process-public`, testData);

      if (response.data.success) {
        return response.data.results;
      } else {
        throw new Error(response.data.error || 'Failed to get MBTI insights');
      }
    } catch (error) {
      console.error('Error getting MBTI insights:', error);
      return {
        type: type.toUpperCase(),
        description: this.getBasicMBTIDescription(type.toUpperCase()),
        confidence: 0.7,
        fallback: true,
        basic_insights: ['Basic MBTI analysis available']
      };
    }
  }

  /**
   * Get AI-powered insights for Enneagram type
   */
  async getEnneagramInsights(type: string): Promise<Record<string, any>> {
    try {
      const testData: AIProcessingRequest = {
        framework: 'enneagram',
        data: { type: type, confidence: 1.0 }
      };

      // Use the non-authenticated client for AI processing
      const response = await aiApiClient.post(`${this.baseUrl}/process-public`, testData);

      if (response.data.success) {
        return response.data.results;
      } else {
        throw new Error(response.data.error || 'Failed to get Enneagram insights');
      }
    } catch (error) {
      console.error('Error getting Enneagram insights:', error);
      throw error;
    }
  }

  /**
   * Process AI with user context (authenticated)
   */
  async processUserAssessment(request: AIProcessingRequest, userContext?: any): Promise<AIProcessingResponse> {
    try {
      const token = localStorage.getItem('access_token');
      const client = token ? createAuthenticatedAIClient(token) : aiApiClient;

      const enhancedRequest = {
        ...request,
        user_context: userContext || this.getUserContext(),
        timestamp: new Date().toISOString()
      };

      const response = await client.post(`${this.baseUrl}/process-user`, enhancedRequest);
      return response.data as any;
    } catch (error: any) {
      console.error('User assessment processing error:', error);
      // Fallback to non-authenticated processing
      return this.processAssessment(request);
    }
  }

  /**
   * Get personalized AI insights based on user history
   */
  async getPersonalizedInsights(framework: string, userType: string): Promise<Record<string, any>> {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        // Fallback to non-personalized insights
        return this.getFrameworkInsights(framework, userType);
      }

      const client = createAuthenticatedAIClient(token);
      const response = await client.post(`${this.baseUrl}/personalized-insights`, {
        framework,
        user_type: userType,
        user_context: this.getUserContext()
      });

      return response.data as any;
    } catch (error) {
      console.error('Error getting personalized insights:', error);
      // Fallback to standard insights
      return this.getFrameworkInsights(framework, userType);
    }
  }

  /**
   * Get user context from localStorage
   */
  private getUserContext(): any {
    try {
      const user = safeJSONParse<any>(localStorage.getItem('user'), {});
      return {
        user_id: user.id,
        email: user.email,
        role: user.role,
        organization: user.organization_id
      };
    } catch {
      return {};
    }
  }

  /**
   * Generic framework insights method
   */
  private async getFrameworkInsights(framework: string, userType: string): Promise<Record<string, any>> {
    const testData: AIProcessingRequest = {
      framework,
      data: { type: userType, confidence: 1.0 }
    };

    const response = await aiApiClient.post(`${this.baseUrl}/process-public`, testData);
    return response.data.results;
  }

  /**
   * Process team personality profile with simple error handling
   */
  async processTeamProfile(teamData: Record<string, any>): Promise<Record<string, any>> {
    try {
      const response = await aiApiClient.post(`${this.baseUrl}/process-public`, {
        framework: 'mbti',
        data: {
          team_composition: teamData,
          analysis_type: 'team_profile'
        }
      });

      if (response.data.success) {
        return response.data.results;
      } else {
        throw new Error(response.data.error || 'Failed to process team profile');
      }
    } catch (error) {
      console.error('Error processing team profile:', error);
      return {
        team_analysis: 'Basic team analysis available',
        success: false,
        fallback: true
      };
    }
  }

  /**
   * Get basic MBTI description for fallback
   */
  private getBasicMBTIDescription(type: string): string {
    const descriptions = {
      'INTJ': 'The Architect - Imaginative and strategic thinkers, with a plan for everything.',
      'ENFP': 'The Campaigner - Enthusiastic, creative and sociable free spirits.',
      'ISTJ': 'The Logistician - Practical and fact-oriented individuals, reliable and dutiful.',
      'ESFJ': 'The Consul - Extraordinary caring, social and popular people, always eager to help.'
    };
    return descriptions[type] || `${type} personality type analysis`;
  }


  /**
   * Fallback frameworks if API fails
   */
  private getFallbackFrameworks(): PersonalityFramework[] {
    return [
      { id: 'mbti', name: 'MBTI', description: 'Myers-Briggs Type Indicator', icon: '🧠', duration: 20, questions: 93 },
      { id: 'enneagram', name: 'Enneagram', description: 'Nine personality types', icon: '⭐', duration: 25, questions: 144 },
      { id: 'bigfive', name: 'Big Five', description: 'Five-factor personality model', icon: '🌟', duration: 15, questions: 44 },
      { id: 'predictive', name: 'Predictive Index', description: 'Behavioral assessment', icon: '📊', duration: 10, questions: 86 }
    ];
  }
}

export const aiService = new AIService();
export default aiService;
