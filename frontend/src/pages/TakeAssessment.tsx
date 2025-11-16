// frontend/src/pages/TakeAssessment.tsx
import React, { useEffect, useState } from 'react';
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
const TakeAssessment: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();
  const [assessment, setAssessment] = useState<AssessmentWithSections | null>(null);
  const [responseSession, setResponseSession] = useState<ResponseSession | null>(null);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [startTime] = useState(Date.now());
  const [autoSaveTimer, setAutoSaveTimer] = useState<NodeJS.Timeout | null>(null);
  useEffect(() => {
    loadAssessmentAndStartSession();
    // Cleanup auto-save timer on unmount
    return () => {
      if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
      }
    };
  }, [assessmentId]);
  useEffect(() => {
    // Auto-save every 30 seconds
    if (responseSession && !responseSession.is_complete) {
      const timer = setTimeout(() => {
        handleAutoSave();
      }, 30000);
      setAutoSaveTimer(timer);
      return () => clearTimeout(timer);
    }
  }, [answers, currentSectionIndex, responseSession]);
  const loadAssessmentAndStartSession = async () => {
    if (!assessmentId) return;
    setIsLoading(true);
    setError('');
    try {
      // Load assessment
      const assessmentData = await assessmentService.getAssessment(
        parseInt(assessmentId)
      );
      setAssessment(assessmentData);
      // Start response session
      const session = await responseService.startResponse({
        assessment_id: parseInt(assessmentId),
      });
      setResponseSession(session);
      // Load existing answers if resuming
      if (session.responses) {
        setAnswers(session.responses);
        setCurrentSectionIndex(session.current_section || 0);
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load assessment');
    } finally {
      setIsLoading(false);
    }
  };
  const handleAutoSave = async () => {
    if (!responseSession || responseSession.is_complete) return;
    try {
      await responseService.saveProgress(responseSession.id, {
        responses: answers,
        current_section: currentSectionIndex,
      });
    } catch (error) {
      console.error('Auto-save failed:', error);
    }
  };
  const handleAnswerChange = (questionId: number, value: any) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId.toString()]: value,
    }));
  };
  const handleSaveProgress = async () => {
    if (!responseSession) return;
    setIsSaving(true);
    try {
      const updated = await responseService.saveProgress(responseSession.id, {
        responses: answers,
        current_section: currentSectionIndex,
      });
      setResponseSession(updated);
      alert('Progress saved successfully!');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to save progress');
    } finally {
      setIsSaving(false);
    }
  };
  const handleNextSection = () => {
    if (assessment && currentSectionIndex < assessment.sections.length - 1) {
      setCurrentSectionIndex(currentSectionIndex + 1);
    }
  };
  const handlePreviousSection = () => {
    if (currentSectionIndex > 0) {
      setCurrentSectionIndex(currentSectionIndex - 1);
    }
  };
  const validateCurrentSection = (): boolean => {
    if (!assessment) return false;
    const currentSection = assessment.sections[currentSectionIndex];
    const requiredQuestions = currentSection.questions.filter((q) => q.is_required);
    for (const question of requiredQuestions) {
      const answer = answers[question.id.toString()];
      if (answer === undefined || answer === null || answer === '') {
        alert(`Please answer the required question: ${question.question_text}`);
        return false;
      }
    }
    return true;
  };
  const handleSubmit = async () => {
    if (!assessment || !responseSession) return;
    // Validate all sections
    for (let i = 0; i < assessment.sections.length; i++) {
      const section = assessment.sections[i];
      const requiredQuestions = section.questions.filter((q) => q.is_required);
      for (const question of requiredQuestions) {
        const answer = answers[question.id.toString()];
        if (answer === undefined || answer === null || answer === '') {
          alert(`Please complete all required questions in section: ${section.title}`);
          setCurrentSectionIndex(i);
          return;
        }
      }
    }
    if (!confirm('Are you sure you want to submit? You cannot change your answers after submission.')) {
      return;
    }
    setIsSubmitting(true);
    try {
      const timeTaken = Math.floor((Date.now() - startTime) / 1000);
      const result = await responseService.submitResponse(responseSession.id, {
        responses: answers,
        time_taken: timeTaken,
      });
      // Navigate to results page
      navigate(`/responses/${result.id}/results`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to submit response');
    } finally {
      setIsSubmitting(false);
    }
  };
  const calculateProgress = (): number => {
    if (!assessment) return 0;
    const totalQuestions = assessment.sections.reduce(
      (sum, section) => sum + section.questions.length,
      0
    );
    const answeredQuestions = Object.keys(answers).filter(
      (key) => answers[key] !== undefined && answers[key] !== null && answers[key] !== ''
    ).length;
    return totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
  };
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }
  if (error || !assessment || !responseSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
        <div className="max-w-md w-full">
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error || 'Assessment not found'}</p>
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
  const currentSection = assessment.sections[currentSectionIndex];
  const isFirstSection = currentSectionIndex === 0;
  const isLastSection = currentSectionIndex === assessment.sections.length - 1;
  const progress = calculateProgress();
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">{assessment.title}</h1>
            {assessment.description && (
              <p className="mt-2 text-sm text-gray-500">{assessment.description}</p>
            )}
          </div>
          {/* Progress Bar */}
          {assessment.show_progress && (
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
          {assessment.instructions && currentSectionIndex === 0 && (
            <div className="px-6 py-4 bg-blue-50 border-t border-blue-100">
              <h3 className="text-sm font-medium text-blue-900 mb-2">Instructions</h3>
              <p className="text-sm text-blue-800 whitespace-pre-wrap">
                {assessment.instructions}
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
                Section {currentSectionIndex + 1} of {assessment.sections.length}
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
                questionNumber={`${currentSectionIndex + 1}.${index + 1}`}
                value={answers[question.id.toString()]}
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
                disabled={isSaving}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Progress'}
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
                  disabled={isSubmitting}
                  className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {isSubmitting ? (
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
          Last saved: {new Date(responseSession.last_saved_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
export default TakeAssessment;
