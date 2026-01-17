import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '@/services/api';

interface MBTIQuestion {
  id: number;
  question_text: string;
  dimension: 'E-I' | 'S-N' | 'T-F' | 'J-P';
  options: {
    text: string;
    value: string;
  }[];
}

interface MBTIAssessment {
  id: string;
  title: string;
  description: string;
  questions: MBTIQuestion[];
}

export default function MBTIAssessmentPageSimple() {
  const [assessment, setAssessment] = useState<MBTIAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Simple, clean loading without timeout complications
  useEffect(() => {
    loadAssessment();
  }, []);

  const loadAssessment = async () => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('🚀 Loading MBTI Assessment from API...');

      const response = await apiClient.get('/assessment-questions/mbti');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;

        const mbtiAssessment: MBTIAssessment = {
          id: backendAssessment.id,
          title: backendAssessment.title,
          description: backendAssessment.description,
          questions: backendAssessment.questions.map((q: any) => ({
            id: q.id,
            question_text: q.question_text,
            dimension: q.dimension,
            options: q.options.map((opt: any) => ({
              text: opt.text,
              value: opt.value
            }))
          }))
        };

        console.log('✅ Assessment loaded successfully:', mbtiAssessment.title);
        setAssessment(mbtiAssessment);
      } else {
        throw new Error('API returned unsuccessful response');
      }

    } catch (error) {
      console.error('❌ Failed to load assessment:', error);
      setError('Failed to load assessment. Please refresh the page.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswer = (questionId: number, value: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const calculateMBTIType = (answers: Record<number, string>): string => {
    const dimensions = {
      'E-I': { E: 0, I: 0 },
      'S-N': { S: 0, N: 0 },
      'T-F': { T: 0, F: 0 },
      'J-P': { J: 0, P: 0 }
    };

    assessment?.questions.forEach(question => {
      const answer = answers[question.id];
      if (answer && dimensions[question.dimension]) {
        (dimensions[question.dimension] as any)[answer]++;
      }
    });

    const type = [
      dimensions['E-I'].E >= dimensions['E-I'].I ? 'E' : 'I',
      dimensions['S-N'].S >= dimensions['S-N'].N ? 'S' : 'N',
      dimensions['T-F'].T >= dimensions['T-F'].F ? 'T' : 'F',
      dimensions['J-P'].J >= dimensions['J-P'].P ? 'J' : 'P'
    ].join('');

    return type;
  };

  const submitAssessment = async () => {
    if (!assessment) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const mbtiType = calculateMBTIType(answers);

      const response = await apiClient.post('/mbti-test-submit', {
        assessment_type: 'mbti',
        responses: answers,
        raw_type: mbtiType
      });

      if (response.data && response.data.success) {
        setResults(response.data.result);
        console.log('✅ Assessment submitted successfully');
      } else {
        throw new Error('Submission failed');
      }

    } catch (error) {
      console.error('❌ Submission failed:', error);
      setError('Failed to submit assessment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const nextQuestion = () => {
    if (currentQuestion < (assessment?.questions.length || 0) - 1) {
      setCurrentQuestion(prev => prev + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(prev => prev - 1);
    }
  };

  const restart = () => {
    setCurrentQuestion(0);
    setAnswers({});
    setResults(null);
    setError(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-4">
            {error}
          </div>
          <button
            onClick={loadAssessment}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 mr-2"
          >
            Try Again
          </button>
          <button
            onClick={() => navigate('/assessments')}
            className="text-blue-600 hover:text-blue-800 underline"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  if (results) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Your MBTI Type: {results.type}
              </h1>
              <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-white text-2xl font-bold">{results.type}</span>
              </div>
              <p className="text-gray-600 mb-4">{results.description}</p>
              <p className="text-sm text-gray-500">
                Confidence: {Math.round((results.confidence || 0.8) * 100)}%
              </p>
            </div>

            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4">Next Steps</h3>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/assessments')}
                  className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Back to Assessments
                </button>
                <button
                  onClick={restart}
                  className="w-full bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Retake Assessment
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No assessment data available</p>
          <button
            onClick={() => navigate('/assessments')}
            className="mt-4 text-blue-600 hover:text-blue-800 underline"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  const question = assessment.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / assessment.questions.length) * 100;
  const answeredCount = Object.keys(answers).length;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{assessment.title}</h1>
          <p className="text-gray-600 mb-4">{assessment.description}</p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-500">
            Question {currentQuestion + 1} of {assessment.questions.length}
          </p>
        </div>

        {/* Question Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-xl font-semibold mb-6 text-gray-900">
            {question.question_text}
          </h2>

          <div className="space-y-3">
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswer(question.id, option.value)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  answers[question.id] === option.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center">
                  <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                    answers[question.id] === option.value
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300'
                  }`}>
                    {answers[question.id] === option.value && (
                      <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                    )}
                  </div>
                  <span className="text-gray-800">{option.text}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <button
              onClick={prevQuestion}
              disabled={currentQuestion === 0}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>

            {currentQuestion < assessment.questions.length - 1 ? (
              <button
                onClick={nextQuestion}
                disabled={!answers[question.id]}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            ) : (
              <button
                onClick={submitAssessment}
                disabled={answeredCount < assessment.questions.length || isSubmitting}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
