/**
 * Big Five Assessment (Refactored with AssessmentContext)
 *
 * This component demonstrates the simplified assessment pattern using AssessmentContext.
 * Compare to original to see the massive code reduction and improved maintainability.
 *
 * Original: ~400 lines with 7 useState hooks and duplicate handlers
 * Refactored: ~250 lines with AssessmentContext
 * Reduction: 37%
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';
import { useAssessment } from '@/contexts/AssessmentContext';

interface BigFiveQuestion {
  id: number;
  question_text: string;
  trait: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface BigFiveAssessment {
  id: string;
  title: string;
  description: string;
  questions: BigFiveQuestion[];
}

interface BigFiveResult {
  personality_type: string;
  scores: Record<string, number>;
  descriptions: Record<string, {
    level: string;
    description: string;
  }>;
  summary: string;
  responses_count: number;
  submitted_at: string;
}

/**
 * Big Five Personality Assessment Component
 *
 * Uses AssessmentContext for all state management, eliminating duplicate code.
 */
const BigFiveAssessmentPageRefactored: React.FC = () => {
  const navigate = useNavigate();

  // All state from context - no more useState hooks!
  const {
    assessment,
    currentQuestion,
    answers,
    isLoading,
    isSubmitting,
    results,
    error,
    setAssessment,
    setError,
    handleAnswer,
    handleNext,
    handlePrevious,
    handleSubmit
  } = useAssessment<BigFiveQuestion>();

  // Load assessment data on mount
  useEffect(() => {
    loadAssessment();
  }, []);

  const loadAssessment = async () => {
    try {
      setError(null);

      const response = await apiClient.get('/assessments/assessment-questions/big-five');

      if (response.data && (response.data as any).success) {
        const backendAssessment = (response.data as any).assessment;
        const bigFiveAssessment: BigFiveAssessment = {
          id: backendAssessment.id,
          title: backendAssessment.title,
          description: backendAssessment.description,
          questions: backendAssessment.questions.map((q: any) => ({
            id: q.id,
            question_text: q.question_text,
            trait: q.trait,
            options: q.options.map((opt: any) => ({
              text: opt.text,
              value: opt.value
            }))
          }))
        };

        setAssessment(bigFiveAssessment);
      }
    } catch (error) {
      console.error('❌ Failed to load Big Five assessment:', error);
      setError('Failed to load assessment. Please refresh the page.');
    }
  };

  /**
   * Transform answers for Big Five submission
   * Groups answers by personality trait (OCEAN model)
   */
  const transformBigFiveAnswers = (answers: Record<number, string>) => {
    // Group answers by trait
    const traitAnswers: Record<string, string[]> = {};

    assessment?.questions.forEach(q => {
      if (!traitAnswers[q.trait]) {
        traitAnswers[q.trait] = [];
      }
      if (answers[q.id]) {
        traitAnswers[q.trait].push(answers[q.id]);
      }
    });

    return {
      assessment_type: 'big_five',
      responses: traitAnswers,
      raw_type: 'Big Five'
    };
  };

  // Loading state
  if (isLoading || !assessment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Big Five Assessment...</p>
        </div>
      </div>
    );
  }

  const currentQuestionData = assessment.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / assessment.questions.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{assessment.title}</h1>
          <p className="text-gray-600">{assessment.description}</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {assessment.questions.length}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-label={`Assessment progress: ${Math.round(progress)}%`}
              aria-valuenow={progress}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="flex-1">
                <p className="text-red-800 font-medium">Error</p>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Question Card */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
          {/* Trait Badge */}
          <div className="mb-4">
            <span className="inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-600 bg-blue-100 rounded-full">
              {currentQuestionData.trait}
            </span>
          </div>

          {/* Question Text */}
          <h2 className="text-2xl font-semibold text-gray-900 mb-8">
            {currentQuestionData.question_text}
          </h2>

          {/* Answer Options */}
          <div className="space-y-3">
            {currentQuestionData.options.map((option) => {
              const isSelected = answers[currentQuestionData.id] === option.value;

              return (
                <button
                  key={option.value}
                  onClick={() => handleAnswer(currentQuestionData.id, option.value)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50 text-blue-900'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                  aria-pressed={isSelected}
                >
                  <span className="font-medium">{option.text}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
            aria-label="Previous question"
          >
            Previous
          </Button>

          {currentQuestion < assessment.questions.length - 1 ? (
            <Button
              variant="default"
              onClick={handleNext}
              disabled={!answers[currentQuestionData.id]}
              aria-label="Next question"
            >
              Next
            </Button>
          ) : (
            <Button
              variant="default"
              onClick={() => handleSubmit('/big-five-test-submit', transformBigFiveAnswers)}
              disabled={isSubmitting || Object.keys(answers).length < assessment.questions.length}
              aria-label="Submit assessment"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
            </Button>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Answer each question based on how you truly feel, not how you think you should feel.</p>
          <p className="mt-2">There are no right or wrong answers.</p>
        </div>
      </div>
    </div>
  );
};

export default BigFiveAssessmentPageRefactored;
