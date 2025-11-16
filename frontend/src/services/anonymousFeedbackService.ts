// Anonymous Feedback Service
// Frontend service layer for anonymous feedback API calls with enhanced privacy features
import api from './api';
import type {
  AnonymousFeedbackSubmission,
  FeedbackSubmissionResponse,
  FeedbackStatusResponse,
  FeedbackStatisticsResponse,
  FeedbackItemForReview,
  AnonymousFeedbackCategoriesResponse
} from '../types/anonymousFeedback';
// For backward compatibility
type FeedbackSubmissionResult = FeedbackSubmissionResponse;
type AnonymousFeedbackStatus = FeedbackStatusResponse;
type FeedbackAnalytics = FeedbackStatisticsResponse;
type HRFeedbackItem = FeedbackItemForReview;
class AnonymousFeedbackService {
  private readonly baseUrl = '/anonymous-feedback';
  /**
   * Submit anonymous feedback with enhanced privacy protections
   */
  async submitFeedback(feedbackData: AnonymousFeedbackSubmission): Promise<FeedbackSubmissionResult> {
    try {
      const response = await api.post(`${this.baseUrl}/submit`, feedbackData);
      return response.data;
    } catch (error: any) {
      console.error('Error submitting anonymous feedback:', error);
      // Enhanced error handling with privacy-preserving fallbacks
      if (error.response?.status === 500) {
        throw new Error('Unable to submit feedback. Please try again or contact HR directly.');
      } else if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      } else {
        throw new Error('Failed to submit feedback. Please try again.');
      }
    }
  }
  /**
   * Check the status of submitted anonymous feedback
   */
  async checkFeedbackStatus(trackingId: string): Promise<AnonymousFeedbackStatus | null> {
    try {
      if (!trackingId.trim()) {
        throw new Error('Tracking ID is required');
      }
      const response = await api.get(`${this.baseUrl}/status/${encodeURIComponent(trackingId)}`);
      return response.data;
    } catch (error: any) {
      console.error('Error checking feedback status:', error);
      if (error.response?.status === 404) {
        return null; // Return null for not found instead of throwing
      } else if (error.response?.status === 500) {
        throw new Error('Unable to check status. Please try again later.');
      } else {
        throw new Error('Failed to check feedback status.');
      }
    }
  }
  /**
   * Submit follow-up to existing feedback
   */
  async submitFollowUp(trackingId: string, followUpData: FeedbackFollowUp): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post(`${this.baseUrl}/follow-up/${trackingId}`, followUpData);
      return response.data;
    } catch (error: any) {
      console.error('Error submitting follow-up:', error);
      throw new Error('Failed to submit follow-up. Please try again.');
    }
  }
  /**
   * Get feedback categories and guidelines
   */
  async getFeedbackCategories(): Promise<any> {
    try {
      const response = await api.get(`${this.baseUrl}/categories`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching feedback categories:', error);
      throw new Error('Unable to load feedback categories. Please refresh the page.');
    }
  }
  /**
   * Get feedback analytics for HR dashboard
   */
  async getFeedbackAnalytics(organizationId?: string): Promise<FeedbackAnalytics> {
    const params = organizationId ? `?organization_id=${organizationId}` : '';
    const response = await api.get(`/hr/anonymous-feedback/analytics${params}`);
    return response.data;
  }
  /**
   * Validate feedback form data
   */
  validateFeedbackForm(data: Partial<AnonymousFeedbackSubmission>): Record<string, string> {
    const errors: Record<string, string> = {};
    // Required field validation
    if (!data.feedback_type?.trim()) {
      errors.feedback_type = 'Feedback type is required';
    }
    if (!data.category?.trim()) {
      errors.category = 'Category is required';
    }
    if (!data.description?.trim()) {
      errors.description = 'Description is required';
    } else if (data.description.trim().length < 10) {
      errors.description = 'Description must be at least 10 characters';
    } else if (data.description.trim().length > 5000) {
      errors.description = 'Description must be less than 5000 characters';
    }
    if (!data.severity?.trim()) {
      errors.severity = 'Severity level is required';
    }
    if (!data.organization_id?.trim()) {
      errors.organization_id = 'Organization ID is required';
    }
    // Optional field validation
    if (data.evidence_urls && Array.isArray(data.evidence_urls)) {
      const invalidUrls = data.evidence_urls.filter(url => {
        try {
          new URL(url);
          return false;
        } catch {
          return true;
        }
      });
      if (invalidUrls.length > 0) {
        errors.evidence_urls = 'Some evidence URLs are invalid';
      }
    }
    if (data.incident_date) {
      const incidentDate = new Date(data.incident_date);
      const now = new Date();
      if (isNaN(incidentDate.getTime())) {
        errors.incident_date = 'Invalid incident date';
      } else if (incidentDate > now) {
        errors.incident_date = 'Incident date cannot be in the future';
      }
    }
    return errors;
  }
  /**
   * Format tracking ID for display (show first 8 chars with asterisks)
   */
  formatTrackingId(trackingId: string): string {
    if (!trackingId || trackingId.length < 8) {
      return trackingId;
    }
    return `${trackingId.substring(0, 8)}${'*'.repeat(trackingId.length - 8)}`;
  }
  /**
   * Get severity color for UI display
   */
  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'critical':
        return '#dc2626'; // red-600
      case 'high':
        return '#ea580c'; // orange-600
      case 'medium':
        return '#ca8a04'; // yellow-600
      case 'low':
        return '#16a34a'; // green-600
      default:
        return '#6b7280'; // gray-500
    }
  }
  /**
   * Get status color for UI display
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'critical':
      case 'escalated':
        return '#dc2626'; // red-600
      case 'investigating':
        return '#2563eb'; // blue-600
      case 'resolved':
        return '#16a34a'; // green-600
      case 'closed':
        return '#6b7280'; // gray-500
      case 'requires_more_info':
        return '#ca8a04'; // yellow-600
      case 'pending_review':
      default:
        return '#f59e0b'; // amber-500
    }
  }
  /**
   * Calculate days remaining based on estimated resolution time
   */
  calculateDaysRemaining(submittedAt: string, estimatedDays: number): number {
    const submitted = new Date(submittedAt);
    const now = new Date();
    const elapsed = Math.floor((now.getTime() - submitted.getTime()) / (1000 * 60 * 60 * 24));
    return Math.max(0, estimatedDays - elapsed);
  }
  /**
   * Format submission date for display
   */
  formatSubmissionDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  /**
   * Get feedback for HR review
   */
  async getFeedbackForReview(filters?: {
    status?: string;
    severity?: string;
    feedback_type?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<FeedbackReviewResponse> {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
      }
      const response = await api.get(`/hr/anonymous-feedback/review${params.toString() ? `?${params.toString()}` : ''}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching feedback for review:', error);
      throw new Error('Failed to fetch feedback for review.');
    }
  }
  /**
   * Get feedback statistics
   */
  async getFeedbackStatistics(organizationId?: string): Promise<FeedbackAnalytics> {
    try {
      const params = organizationId ? `?organization_id=${organizationId}` : '';
      const response = await api.get(`/hr/anonymous-feedback/analytics${params}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching feedback statistics:', error);
      throw new Error('Failed to fetch feedback statistics.');
    }
  }
  /**
   * Update feedback status
   */
  async updateFeedbackStatus(trackingId: string, updateData: {
    new_status: string;
    internal_notes?: string;
    public_notes?: string;
    actions_taken?: string;
  }): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.patch(`${this.baseUrl}/status/${trackingId}`, updateData);
      return response.data;
    } catch (error: any) {
      console.error('Error updating feedback status:', error);
      throw new Error('Failed to update feedback status.');
    }
  }
}
// Type for the review response
interface FeedbackReviewResponse {
  feedbacks: FeedbackItemForReview[];
  summary: any;
  total_count: number;
  reviewer_id: string;
  review_timestamp: string;
  privacy_guidelines: string[];
}
// Create singleton instance
export const anonymousFeedbackService = new AnonymousFeedbackService();
// Export the class for testing purposes
export { AnonymousFeedbackService };