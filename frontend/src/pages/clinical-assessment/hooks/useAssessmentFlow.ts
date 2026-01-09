/**
 * Clinical Assessment Flow Hook
 *
 * Custom hook for managing clinical assessment flow and state.
 * Handles question progression, response tracking, and assessment completion.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AssessmentData, AssessmentResponse } from '../types';

interface UseAssessmentFlowOptions {
  assessmentData: AssessmentData;
  tool: string;
}

interface UseAssessmentFlowReturn {
  currentQuestion: number;
  responses: Record<string, string>;
  submitting: boolean;
  showCrisisWarning: boolean;
  handleResponseChange: (questionId: string, answer: string) => void;
  handleNext: () => void;
  handlePrevious: () => void;
  handleSubmit: () => void;
  canProgress: () => boolean;
  calculateScore: () => number;
  getSeverityLevel: (score: number) => any;
}

/**
 * Hook to manage clinical assessment flow
 *
 * @param options - Assessment data and tool type
 * @returns Assessment flow state and handlers
 *
 * @example
 * ```typescript
 * const {
 *   currentQuestion,
 *   responses,
 *   handleNext,
 *   handlePrevious,
 *   handleSubmit
 * } = useAssessmentFlow({ assessmentData, tool: 'phq9' });
 * ```
 */
export function useAssessmentFlow({
  assessmentData,
  tool,
}: UseAssessmentFlowOptions): UseAssessmentFlowReturn {
  const navigate = useNavigate();

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [showCrisisWarning, setShowCrisisWarning] = useState(false);

  const handleResponseChange = useCallback((questionId: string, answer: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: answer,
    }));
  }, []);

  const handleNext = useCallback(() => {
    if (currentQuestion < assessmentData.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  }, [currentQuestion, assessmentData.questions.length]);

  const handlePrevious = useCallback(() => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  }, [currentQuestion]);

  const calculateScore = useCallback((): number => {
    let totalScore = 0;

    assessmentData.questions.forEach((question) => {
      const answer = responses[question.id];
      if (!answer) return;

      // Score mapping based on answer options
      const scoreMap: Record<string, number> = {
        'Not at all': 0,
        'Never': 0,
        'Several days': 1,
        'Almost never': 1,
        'More than half the days': 2,
        'Sometimes': 2,
        'Nearly every day': 3,
        'Fairly often': 3,
        'Very often': 4,
      };

      totalScore += scoreMap[answer] || 0;
    });

    return totalScore;
  }, [assessmentData.questions, responses]);

  const getSeverityLevel = useCallback((score: number) => {
    return assessmentData.scoring.levels.find(
      (level) => score >= level.range[0] && score <= level.range[1]
    );
  }, [assessmentData.scoring.levels]);

  const handleSubmit = useCallback(async () => {
    setSubmitting(true);

    try {
      const score = calculateScore();
      const severityLevel = getSeverityLevel(score);

      // Check for crisis indicators
      const isCrisis = severityLevel?.label === 'Severe' ||
                       severityLevel?.label === 'Moderately Severe';

      if (isCrisis) {
        setShowCrisisWarning(true);
      }

      // Create response array
      const responseArray: AssessmentResponse[] = Object.entries(responses).map(
        ([questionId, answer]) => ({
          questionId,
          answer,
          timestamp: new Date(),
        })
      );

      // Submit to API
      const token = localStorage.getItem('access_token');
      const submitResponse = await fetch('/api/v1/clinical/screenings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          tool,
          responses: responseArray,
          score,
          severity_level: severityLevel?.label,
        }),
      });

      if (submitResponse.ok) {
        const result = await submitResponse.json();

        // Navigate to results page
        navigate(`/clinical/results/${tool}`, {
          state: {
            result: {
              score,
              severity_level: severityLevel?.label,
              severity: severityLevel,
              crisisAlert: isCrisis,
              responses: responseArray,
            },
            assessmentId: result.id,
            completedAt: new Date().toISOString(),
          },
        });
      } else {
        console.error('Failed to submit assessment');
        throw new Error('Submission failed');
      }
    } catch (error) {
      console.error('Error submitting assessment:', error);
      // Still navigate to results even if API fails
      const score = calculateScore();
      const severityLevel = getSeverityLevel(score);

      navigate(`/clinical/results/${tool}`, {
        state: {
          result: {
            score,
            severity_level: severityLevel?.label,
            severity: severityLevel,
            crisisAlert: false,
            responses: [],
          },
        },
      });
    } finally {
      setSubmitting(false);
    }
  }, [assessmentData, calculateScore, getSeverityLevel, navigate, responses, tool]);

  const canProgress = useCallback((): boolean => {
    const currentQuestionData = assessmentData.questions[currentQuestion];
    return !!currentQuestionData.required || !!responses[currentQuestionData.id];
  }, [assessmentData.questions, currentQuestion, responses]);

  return {
    currentQuestion,
    responses,
    submitting,
    showCrisisWarning,
    handleResponseChange,
    handleNext,
    handlePrevious,
    handleSubmit,
    canProgress,
    calculateScore,
    getSeverityLevel,
  };
}
