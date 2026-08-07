// frontend/src/pages/TakeAssessment.tsx
import React, { useEffect, useReducer, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  assessmentService,
  AssessmentWithSections,
  Section,
  Question,
} from '../services/assessmentService';
import {
  responseService,
  ResponseSession,
} from '../services/responseService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import QuestionRenderer from '../components/assessments/QuestionRenderer';
import { useAnalytics } from '../services/analytics/tracker';

// ✅ PERFORMANCE FIX: Type for cached assessment metrics
interface AssessmentMetrics {
  total_questions: number;
  total_sections: number;
}

/**
 * ✅ CONSOLIDATED STATE: Using reducer to prevent multiple re-renders
 *
 * All related state updates now happen in a single render cycle
 * instead of causing 11 separate re-renders for each update.
 */

// Define state shape
interface AssessmentState {
  assessment: AssessmentWithSections | null;
  responseSession: ResponseSession | null;
  currentSectionIndex: number;
  answers: Record<string, any>;
  isLoading: boolean;
  isSaving: boolean;
  isSubmitting: boolean;
  error: string;
  startTime: number;
  autoSaveTimer: NodeJS.Timeout | null;
}

// Define action types
type AssessmentAction =
  | { type: 'SET_ASSESSMENT'; payload: AssessmentWithSections }
  | { type: 'SET_RESPONSE_SESSION'; payload: ResponseSession }
  | { type: 'SET_CURRENT_SECTION'; payload: number }
  | { type: 'SET_ANSWERS'; payload: Record<string, any> }
  | { type: 'UPDATE_ANSWER'; questionId: number; value: any }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SAVING'; payload: boolean }
  | { type: 'SET_SUBMITTING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SET_AUTO_SAVE_TIMER'; payload: NodeJS.Timeout | null }
  | { type: 'RESET' };

// Initial state
const initialState: AssessmentState = {
  assessment: null,
  responseSession: null,
  currentSectionIndex: 0,
  answers: {},
  isLoading: true,
  isSaving: false,
  isSubmitting: false,
  error: '',
  startTime: Date.now(),
  autoSaveTimer: null,
};

// Reducer function
function assessmentReducer(state: AssessmentState, action: AssessmentAction): AssessmentState {
  switch (action.type) {
    case 'SET_ASSESSMENT':
      return { ...state, assessment: action.payload };

    case 'SET_RESPONSE_SESSION':
      return { ...state, responseSession: action.payload };

    case 'SET_CURRENT_SECTION':
      return { ...state, currentSectionIndex: action.payload };

    case 'SET_ANSWERS':
      return { ...state, answers: action.payload };

    case 'UPDATE_ANSWER':
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.questionId.toString()]: action.value,
        },
      };

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_SAVING':
      return { ...state, isSaving: action.payload };

    case 'SET_SUBMITTING':
      return { ...state, isSubmitting: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'SET_AUTO_SAVE_TIMER':
      // Clear existing timer if setting new one
      if (state.autoSaveTimer) {
        clearTimeout(state.autoSaveTimer);
      }
      return { ...state, autoSaveTimer: action.payload };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

const TakeAssessment: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const { track, trackFunnel, trackPage } = useAnalytics();

  // ✅ CONSOLIDATED: Single reducer instead of 11 useState calls
  const [state, dispatch] = useReducer(assessmentReducer, initialState);
  // ✅ PERFORMANCE FIX: Cache expensive assessment metrics calculation
  // Prevents O(n) reduce computation on every render/tracking call
  const assessmentMetrics = useMemo((): AssessmentMetrics | null => {
    if (!state.assessment) return null;

    const totalQuestions = state.assessment.sections.reduce(
      (sum, section) => sum + section.questions.length,
      0
    );

    return {
      total_questions: totalQuestions,
      total_sections: state.assessment.sections.length,
    };
  }, [state.assessment]);

  // ✅ MEMOIZED: Load function only recreated when assessmentId changes
  const loadAssessmentAndStartSession = useCallback(async () => {
    if (!assessmentId) return;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: '' });

    try {
      // Load assessment
      const assessmentData = await assessmentService.getAssessment(
        assessmentId
      );
      dispatch({ type: 'SET_ASSESSMENT', payload: assessmentData });

      // ✅ PERFORMANCE FIX: Compute metrics once instead of on every tracking call
      const totalQuestions = assessmentData.sections.reduce((sum, s) => sum + s.questions.length, 0);
      const totalSections = assessmentData.sections.length;

      // Track page view and funnel start
      trackPage('take_assessment', {
        assessment_id: assessmentId,
        assessment_title: assessmentData.title,
        assessment_category: assessmentData.category
      });

      // Start response session
      const session = await responseService.startResponse({
        assessment_id: assessmentId,
      });
      dispatch({ type: 'SET_RESPONSE_SESSION', payload: session });

      // Track assessment funnel start
      const isResuming = !!session.responses;
      trackFunnel('assessment', 'started', {
        assessment_id: assessmentId,
        assessment_title: assessmentData.title,
        assessment_category: assessmentData.category,
        is_resuming: isResuming,
        total_sections: totalSections,
        total_questions: totalQuestions
      });

      // Load existing answers if resuming
      if (session.responses) {
        dispatch({ type: 'SET_ANSWERS', payload: session.responses });
        dispatch({ type: 'SET_CURRENT_SECTION', payload: session.current_section || 0 });
      }
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.response?.data?.detail || 'Failed to load assessment' });
      // Track error
      track('system_error_occurred', {
        error_type: 'assessment_load_failed',
        error_message: error.response?.data?.detail || 'Failed to load assessment',
        assessment_id: assessmentId
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [assessmentId, track, trackFunnel, trackPage]);

  // ✅ MEMOIZED: Auto-save uses reducer state
  const handleAutoSave = useCallback(async () => {
    if (!state.responseSession || state.responseSession.is_complete) return;
    try {
      await responseService.saveProgress(state.responseSession.id, {
        responses: state.answers,
        current_section: state.currentSectionIndex,
      });
    } catch (error) {
      console.error('Auto-save failed:', error);
    }
  }, [state.responseSession, state.answers, state.currentSectionIndex]);

  // ✅ MEMOIZED: Answer change uses reducer action
  const handleAnswerChange = useCallback((questionId: number, value: any) => {
    dispatch({ type: 'UPDATE_ANSWER', questionId, value });
  }, []);  // No dependencies - dispatch is stable

  // ✅ MEMOIZED: Save progress uses reducer state
  const handleSaveProgress = useCallback(async () => {
    if (!state.responseSession) return;
    dispatch({ type: 'SET_SAVING', payload: true });

    try {
      const updated = await responseService.saveProgress(state.responseSession.id, {
        responses: state.answers,
        current_section: state.currentSectionIndex,
      });
      dispatch({ type: 'SET_RESPONSE_SESSION', payload: updated });
      alert('Progress saved successfully!');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to save progress');
    } finally {
      dispatch({ type: 'SET_SAVING', payload: false });
    }
  }, [state.responseSession, state.answers, state.currentSectionIndex]);

  // ✅ MEMOIZED: Next section uses reducer state
  const handleNextSection = useCallback(() => {
    if (state.assessment && state.currentSectionIndex < state.assessment.sections.length - 1) {
      const nextSectionIndex = state.currentSectionIndex + 1;
      dispatch({ type: 'SET_CURRENT_SECTION', payload: nextSectionIndex });

      // Track section navigation
      track('user_button_clicked', {
        button_id: 'next_section',
        page: 'take_assessment',
        from_section: state.currentSectionIndex,
        to_section: nextSectionIndex,
        assessment_id: assessmentId
      });
    }
  }, [state.assessment, state.currentSectionIndex, track, assessmentId]);

  // ✅ MEMOIZED: Previous section uses reducer state
  const handlePreviousSection = useCallback(() => {
    if (state.currentSectionIndex > 0) {
      const prevSectionIndex = state.currentSectionIndex - 1;
      dispatch({ type: 'SET_CURRENT_SECTION', payload: prevSectionIndex });

      // Track section navigation
      track('user_button_clicked', {
        button_id: 'previous_section',
        page: 'take_assessment',
        from_section: state.currentSectionIndex,
        to_section: prevSectionIndex,
        assessment_id: assessmentId
      });
    }
  }, [state.currentSectionIndex, track, assessmentId]);

  // ✅ MEMOIZED: Validate uses reducer state
  const validateCurrentSection = useCallback((): boolean => {
    if (!state.assessment) return false;
    const currentSection = state.assessment.sections[state.currentSectionIndex];
    const requiredQuestions = currentSection.questions.filter((q) => q.is_required);
    for (const question of requiredQuestions) {
      const answer = state.answers[question.id.toString()];
      if (answer === undefined || answer === null || answer === '') {
        alert(`Please answer the required question: ${question.question_text}`);
        return false;
      }
    }
    return true;
  }, [state.assessment, state.currentSectionIndex, state.answers]);

  // ✅ MEMOIZED: Submit uses reducer state
  const handleSubmit = useCallback(async () => {
    if (!state.assessment || !state.responseSession) return;

    // Validate all sections
    for (let i = 0; i < state.assessment.sections.length; i++) {
      const section = state.assessment.sections[i];
      const requiredQuestions = section.questions.filter((q) => q.is_required);
      for (const question of requiredQuestions) {
        const answer = state.answers[question.id.toString()];
        if (answer === undefined || answer === null || answer === '') {
          alert(`Please complete all required questions in section: ${section.title}`);
          dispatch({ type: 'SET_CURRENT_SECTION', payload: i });
          return;
        }
      }
    }

    if (!confirm('Are you sure you want to submit? You cannot change your answers after submission.')) {
      // Track cancellation
      track('user_button_clicked', {
        button_id: 'submit_cancelled',
        page: 'take_assessment',
        assessment_id: assessmentId
      });
      return;
    }

    // Track submit button click
    track('user_button_clicked', {
      button_id: 'submit_assessment',
      page: 'take_assessment',
      assessment_id: assessmentId,
      total_questions_answered: Object.keys(state.answers).length
    });

    dispatch({ type: 'SET_SUBMITTING', payload: true });

    try {
      const timeTaken = Math.floor((Date.now() - state.startTime) / 1000);
      const result = await responseService.submitResponse(state.responseSession.id, {
        responses: state.answers,
        time_taken: timeTaken,
      });

      // Track successful assessment completion
      trackFunnel('assessment', 'completed', {
        assessment_id: assessmentId,
        assessment_title: state.assessment.title,
        assessment_category: state.assessment.category,
        time_taken_seconds: timeTaken,
        time_taken_minutes: Math.round(timeTaken / 60),
        total_questions: assessmentMetrics?.total_questions ?? 0,
        questions_answered: Object.keys(state.answers).length,
        completion_percentage: assessmentMetrics
          ? Math.round((Object.keys(state.answers).length / assessmentMetrics.total_questions) * 100)
          : 0
      });

      // Navigate to results page
      navigate(`/responses/${result.id}/results`);
    } catch (error: any) {
      // Track submission error
      track('system_error_occurred', {
        error_type: 'assessment_submit_failed',
        error_message: error.response?.data?.detail || 'Failed to submit response',
        assessment_id: assessmentId
      });
      alert(error.response?.data?.detail || 'Failed to submit response');
    } finally {
      dispatch({ type: 'SET_SUBMITTING', payload: false });
    }
  }, [state.assessment, state.responseSession, state.answers, state.startTime, navigate, track, trackFunnel, assessmentId]);

  // ✅ MEMOIZED: Calculate progress uses cached assessment metrics
  const calculateProgress = useCallback((): number => {
    if (!state.assessment || !assessmentMetrics) return 0;

    const answeredQuestions = Object.keys(state.answers).filter(
      (key) => state.answers[key] !== undefined && state.answers[key] !== null && state.answers[key] !== ''
    ).length;
    return assessmentMetrics.total_questions > 0
      ? (answeredQuestions / assessmentMetrics.total_questions) * 100
      : 0;
  }, [state.assessment, state.answers, assessmentMetrics]);

  // ✅ EFFECT: Only runs when assessmentId changes
  useEffect(() => {
    loadAssessmentAndStartSession();

    // Cleanup auto-save timer on unmount
    return () => {
      if (state.autoSaveTimer) {
        clearTimeout(state.autoSaveTimer);
      }
    };
  }, [assessmentId]);  // ✅ Only assessmentId dependency

  // ✅ EFFECT: Auto-save timer only recreates when dependencies change
  useEffect(() => {
    // Auto-save every 30 seconds
    let timerId: NodeJS.Timeout | undefined;
    if (state.responseSession && !state.responseSession.is_complete) {
      timerId = setTimeout(() => {
        handleAutoSave();
      }, 30000);
      dispatch({ type: 'SET_AUTO_SAVE_TIMER', payload: timerId });
    }

    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [state.answers, state.currentSectionIndex, state.responseSession, handleAutoSave]);

  // Loading state
  if (state.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // ✅ Use reducer state
  if (state.error || !state.assessment || !state.responseSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
        <div className="max-w-md w-full">
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{state.error || 'Assessment not found'}</p>
          </div>
          <button
            onClick={() => navigate('/assessments')}
            className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  // ✅ Use reducer state
  const currentSection = state.assessment.sections[state.currentSectionIndex];
  const isFirstSection = state.currentSectionIndex === 0;
  const isLastSection = state.currentSectionIndex === state.assessment.sections.length - 1;
  const progress = calculateProgress();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">{state.assessment.title}</h1>
            {state.assessment.description && (
              <p className="mt-2 text-sm text-gray-500">{state.assessment.description}</p>
            )}
          </div>
          {/* Progress Bar */}
          {state.assessment.show_progress && (
            <div className="px-6 py-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Progress</span>
                <span className="text-sm font-medium text-gray-700">
                  {Math.round(progress)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
          {/* Instructions */}
          {state.assessment.instructions && state.currentSectionIndex === 0 && (
            <div className="px-6 py-4 bg-blue-50 border-t border-blue-100">
              <h3 className="text-sm font-medium text-blue-900 mb-2">Instructions</h3>
              <p className="text-sm text-blue-800 whitespace-pre-wrap">
                {state.assessment.instructions}
              </p>
            </div>
          )}
        </div>
        {/* Current Section */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                {currentSection.title}
              </h2>
              <span className="text-sm text-gray-500">
                Section {state.currentSectionIndex + 1} of {state.assessment.sections.length}
              </span>
            </div>
            {currentSection.description && (
              <p className="mt-2 text-sm text-gray-500">{currentSection.description}</p>
            )}
          </div>
          {/* Questions */}
          <div className="px-6 py-6 space-y-8">
            {currentSection.questions.map((question, index) => (
              <QuestionRenderer
                key={question.id}
                question={question}
                questionNumber={`${state.currentSectionIndex + 1}.${index + 1}`}
                value={state.answers[question.id.toString()]}
                onChange={(value) => handleAnswerChange(question.id, value)}
              />
            ))}
          </div>
        </div>
        {/* Navigation */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex space-x-3">
              <button
                onClick={handlePreviousSection}
                disabled={isFirstSection}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={handleSaveProgress}
                disabled={state.isSaving}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {state.isSaving ? 'Saving...' : 'Save Progress'}
              </button>
            </div>
            <div className="flex space-x-3">
              {!isLastSection ? (
                <button
                  onClick={() => {
                    if (validateCurrentSection()) {
                      handleNextSection();
                    }
                  }}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Next Section
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={state.isSubmitting}
                  className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {state.isSubmitting ? (
                    <>
                      <LoadingSpinner size="small" className="inline mr-2" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Assessment'
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
        {/* Auto-save indicator */}
        <div className="mt-4 text-center text-sm text-gray-500">
          Last saved: {new Date(state.responseSession.last_saved_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
export default TakeAssessment;
