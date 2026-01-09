import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '@/services/api';

/**
 * AssessmentContext - Shared state management for all assessment types
 *
 * This context eliminates duplicate state logic across MBTI, Big Five, Enneagram, etc.
 * Provides a unified interface for assessment navigation, answer tracking, and submission.
 */

// Generic interfaces for assessment data
interface AssessmentQuestion {
  id: number;
  question_text: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface Assessment<T extends AssessmentQuestion> {
  id: string;
  title: string;
  description: string;
  questions: T[];
}

interface AssessmentContextValue<T extends AssessmentQuestion> {
  // State
  assessment: Assessment<T> | null;
  currentQuestion: number;
  answers: Record<number, string>;
  isLoading: boolean;
  isSubmitting: boolean;
  results: any;
  error: string | null;

  // Actions
  setAssessment: (assessment: Assessment<T> | null) => void;
  setCurrentQuestion: (index: number) => void;
  handleAnswer: (questionId: number, value: string) => void;
  handleNext: () => void;
  handlePrevious: () => void;
  handleSubmit: (endpoint: string, transformData?: (answers: Record<number, string>) => any) => Promise<void>;
  clearError: () => void;
  resetAssessment: () => void;
}

const AssessmentContext = createContext<AssessmentContextValue<any> | undefined>(undefined);

interface AssessmentProviderProps {
  children: ReactNode;
}

export function AssessmentProvider<T extends AssessmentQuestion>({ children }: AssessmentProviderProps) {
  const navigate = useNavigate();

  // Core assessment state - identical across all assessment types
  const [assessment, setAssessment] = useState<Assessment<T> | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Record an answer for a specific question
   * Uses functional update for optimal re-rendering
   */
  const handleAnswer = useCallback((questionId: number, value: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  }, []);

  /**
   * Navigate to next question
   * Validates that there is a next question before advancing
   */
  const handleNext = useCallback(() => {
    if (assessment && currentQuestion < assessment.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  }, [assessment, currentQuestion]);

  /**
   * Navigate to previous question
   * Validates that there is a previous question before going back
   */
  const handlePrevious = useCallback(() => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  }, [currentQuestion]);

  /**
   * Submit assessment answers to backend
   *
   * @param endpoint - API endpoint to submit to (e.g., '/assessments/mbti/submit')
   * @param transformData - Optional function to transform answers before submission
   *
   * TODO(human): Implement the submission logic below
   *
   * Requirements:
   * 1. Set isSubmitting to true before calling API
   * 2. Call apiClient.post(endpoint, transformedData)
   * 3. On success: set results data and navigate to results page
   * 4. On error: set error message and set isSubmitting to false
   * 5. Handle different response formats for different assessment types
   *
   * Guidance:
   * - The transformData function allows each assessment type to format answers differently
   * - Some assessments might need answers grouped by dimension/trait
   * - Consider saving results to localStorage for persistence
   * - Error messages should be user-friendly, not technical
   * - The navigate function is available from useNavigate() hook
   */
  const handleSubmit = async (
    endpoint: string,
    transformData?: (answers: Record<number, string>) => any
  ): Promise<void> => {
    try {
      setIsSubmitting(true);
      setError(null);

      // Transform answers if transform function provided
      const submissionData = transformData ? transformData(answers) : { answers };

      // Make API call with submission data
      const response = await apiClient.post(endpoint, submissionData);

      // Handle success response
      if (response.data && response.data.success) {
        const resultsData = response.data.results || response.data.data;

        // Set results state
        setResults(resultsData);

        // Persist results to localStorage for page refresh capability
        try {
          localStorage.setItem(
            `assessment_${assessment?.id || 'latest'}_results`,
            JSON.stringify({
              results: resultsData,
              timestamp: new Date().toISOString(),
              assessmentId: assessment?.id
            })
          );
        } catch (storageError) {
          // Non-blocking: localStorage might be disabled or full
          console.warn('Could not save results to localStorage:', storageError);
        }

        // Navigate to results page
        // The component can override this by handling navigation itself
        if (assessment?.id) {
          navigate(`/assessments/${assessment.id}/results`, { replace: true });
        }
      } else {
        // Handle API success = false case
        const errorMessage = response.data?.message || 'Submission failed. Please try again.';
        setError(errorMessage);
      }
    } catch (err: any) {
      // Handle API errors
      console.error('Assessment submission error:', err);

      // Determine user-friendly error message
      let errorMessage = 'Failed to submit assessment. Please try again.';

      if (err.response) {
        // Server responded with error status
        if (err.response.status === 401) {
          errorMessage = 'Your session has expired. Please log in again.';
        } else if (err.response.status === 429) {
          errorMessage = 'Too many attempts. Please wait a moment and try again.';
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message;
        }
      } else if (err.request) {
        // Request made but no response (network error)
        errorMessage = 'Network error. Please check your connection and try again.';
      }

      setError(errorMessage);

      // TODO: Add toast notification for better UX
      // Example: toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Clear the current error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Reset assessment to initial state
   * Useful for restarting assessment or cleanup
   */
  const resetAssessment = useCallback(() => {
    setAssessment(null);
    setCurrentQuestion(0);
    setAnswers({});
    setIsLoading(false);
    setIsSubmitting(false);
    setResults(null);
    setError(null);
  }, []);

  const value: AssessmentContextValue<T> = {
    // State
    assessment,
    currentQuestion,
    answers,
    isLoading,
    isSubmitting,
    results,
    error,

    // Actions
    setAssessment,
    setCurrentQuestion,
    handleAnswer,
    handleNext,
    handlePrevious,
    handleSubmit,
    clearError,
    resetAssessment,
  };

  return (
    <AssessmentContext.Provider value={value}>
      {children}
    </AssessmentContext.Provider>
  );
}

/**
 * Hook to use assessment context
 * Throws error if used outside of AssessmentProvider
 */
export function useAssessment<T extends AssessmentQuestion>() {
  const context = useContext(AssessmentContext);
  if (context === undefined) {
    throw new Error('useAssessment must be used within an AssessmentProvider');
  }
  return context as AssessmentContextValue<T>;
}
