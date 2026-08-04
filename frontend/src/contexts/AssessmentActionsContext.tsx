import React, { createContext, useContext, useCallback, useMemo, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '@/services/api';
import { useAssessmentData } from './AssessmentDataContext';
import { useAssessmentUI } from './AssessmentUIContext';

/**
 * AssessmentActionsContext - Business logic actions for assessments
 */

interface AssessmentActionsContextValue {
  handleAnswer: (questionId: number, value: string) => void;
  handleNext: () => void;
  handlePrevious: () => void;
  handleSubmit: (endpoint: string, transformData?: (answers: Record<number, string>) => any) => Promise<void>;
  resetAssessment: () => void;
}

const AssessmentActionsContext = createContext<AssessmentActionsContextValue | undefined>(undefined);

interface AssessmentActionsProviderProps {
  children: ReactNode;
}

export function AssessmentActionsProvider({ children }: AssessmentActionsProviderProps) {
  const navigate = useNavigate();

  // Get data state
  const { assessment, currentQuestion, answers, setAssessment, setCurrentQuestion, setAnswers, setResults } = useAssessmentData();

  // Get UI state
  const { setIsLoading, setIsSubmitting, setError } = useAssessmentUI();

  /**
   * Record an answer for a specific question
   */
  const handleAnswer = useCallback((questionId: number, value: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  }, [setAnswers]);

  /**
   * Navigate to next question
   */
  const handleNext = useCallback(() => {
    if (assessment && currentQuestion < assessment.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  }, [assessment, currentQuestion, setCurrentQuestion]);

  /**
   * Navigate to previous question
   */
  const handlePrevious = useCallback(() => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  }, [currentQuestion, setCurrentQuestion]);

  /**
   * Submit assessment answers to backend
   */
  const handleSubmit = useCallback(async (
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
      const responseData = response.data as { success?: boolean; results?: any; data?: any; message?: string };
      if (responseData && responseData.success) {
        const resultsData = responseData.results || responseData.data;

        // Set results state
        setResults(resultsData);

        // Navigate to results page
        if (assessment?.id) {
          navigate(`/assessments/${assessment.id}/results`, { replace: true });
        }
      } else {
        // Handle API success = false case
        const errorMessage = responseData?.message || 'Submission failed. Please try again.';
        setError(errorMessage);
      }
    } catch (err: any) {
      // Handle API errors
      console.error('Assessment submission error:', err);

      let errorMessage = 'Failed to submit assessment. Please try again.';

      if (err.response) {
        if (err.response.status === 401) {
          errorMessage = 'Your session has expired. Please log in again.';
        } else if (err.response.status === 429) {
          errorMessage = 'Too many attempts. Please wait a moment and try again.';
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message;
        }
      } else if (err.request) {
        errorMessage = 'Network error. Please check your connection and try again.';
      }

      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  }, [answers, assessment, navigate, setResults, setIsSubmitting, setError]);

  /**
   * Reset assessment to initial state
   */
  const resetAssessment = useCallback(() => {
    setAssessment(null);
    setCurrentQuestion(0);
    setAnswers({});
    setIsSubmitting(false);
    setResults(null);
    setError(null);
  }, [setAssessment, setCurrentQuestion, setAnswers, setIsSubmitting, setResults, setError]);

  // Memoized context value
  const value: AssessmentActionsContextValue = useMemo(() => ({
    handleAnswer,
    handleNext,
    handlePrevious,
    handleSubmit,
    resetAssessment,
  }), [
    handleAnswer,
    handleNext,
    handlePrevious,
    handleSubmit,
    resetAssessment,
  ]);

  return (
    <AssessmentActionsContext.Provider value={value}>
      {children}
    </AssessmentActionsContext.Provider>
  );
}

/**
 * Hook to use assessment actions context
 */
export function useAssessmentActions() {
  const context = useContext(AssessmentActionsContext);
  if (context === undefined) {
    throw new Error('useAssessmentActions must be used within an AssessmentActionsProvider');
  }
  return context;
}
