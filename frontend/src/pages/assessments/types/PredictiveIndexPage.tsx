import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';

interface PredictiveIndexQuestion {
  id: number;
  question_text: string;
  factor: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface PredictiveIndexAssessment {
  id: string;
  title: string;
  description: string;
  questions: PredictiveIndexQuestion[];
}

interface PredictiveIndexResult {
  primary_factor: string;
  secondary_factor: string;
  behavioral_pattern: string;
  factor_scores: Record<string, number>;
  description: string;
  strengths: string[];
  development_areas: string[];
  dominance_score: number;
  influence_score: number;
  steadiness_score: number;
  compliance_score: number;
  confidence: number;
  responses_count: number;
  submitted_at: string;
}

const PredictiveIndexPage: React.FC = () => {
  const [assessment, setAssessment] = useState<PredictiveIndexAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<PredictiveIndexResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Load assessment data
  useEffect(() => {
    loadAssessment();
  }, []);

  const loadAssessment = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiClient.get('/assessment-questions/predictive-index');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;
        const predictiveIndexAssessment: PredictiveIndexAssessment = {
          id: backendAssessment.id,
          title: backendAssessment.title,
          description: backendAssessment.description,
          questions: backendAssessment.questions.map((q: any) => ({
            id: q.id,
            question_text: q.question_text,
            factor: q.factor,
            options: q.options.map((opt: any) => ({
              text: opt.text,
              value: opt.value
            }))
          }))
        };
        setAssessment(predictiveIndexAssessment);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Failed to load Predictive Index assessment:', error);
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

  const handleNext = () => {
    if (currentQuestion < (assessment?.questions.length || 0) - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const submitAssessment = async () => {
    if (!assessment) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiClient.post('/predictive-index-test-submit', {
        assessment_type: 'predictive_index',
        responses: answers,
        raw_type: 'Predictive Index'
      });

      if (response.data && response.data.success) {
        setResults(response.data.result);
        console.log('✅ Predictive Index assessment submitted successfully');
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Predictive Index Assessment...</p>
        </div>
      </div>
    );
  }

  if (error && !assessment) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (results) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Your Behavioral Profile</h2>
              <div className="inline-block px-6 py-3 bg-blue-100 text-blue-800 rounded-full text-lg font-semibold">
                {results.behavioral_pattern}
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-700 mb-4">Profile Overview</h3>
              <p className="text-gray-600 mb-6">{results.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h4 className="font-semibold text-green-600 mb-3">Your Strengths</h4>
                  <ul className="space-y-2">
                    {results.strengths.map((strength, index) => (
                      <li key={index} className="flex items-center">
                        <span className="text-green-500 mr-2">✓</span>
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-orange-600 mb-3">Development Areas</h4>
                  <ul className="space-y-2">
                    {results.development_areas.map((area, index) => (
                      <li key={index} className="flex items-center">
                        <span className="text-orange-500 mr-2">!</span>
                        {area}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Predictive Index Educational Content */}
            <div className="mb-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="text-xl font-semibold text-blue-800 mb-4">Understanding Your Predictive Index Results</h3>
              <p className="text-gray-700 mb-4">
                The Predictive Index (PI) is a scientifically-validated behavioral assessment that measures workplace behavior
                and helps predict how people will perform in specific roles. It measures four core factors that determine
                your natural behavioral tendencies and how you interact with your work environment.
              </p>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-blue-800 mb-2">The Four PI Behavioral Factors:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-red-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-red-800 mb-2">Dominance (D)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Measures:</strong> Drive, control, and assertiveness
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>High D:</strong> Independent, competitive, decisive, results-driven
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Low D:</strong> Cooperative, collaborative, consensus-driven
                      </p>
                    </div>
                    <div className="bg-yellow-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-yellow-800 mb-2">Influence (I)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Measures:</strong> Social interaction, communication, and persuasion
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>High I:</strong> Outgoing, enthusiastic, persuasive, optimistic
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Low I:</strong> Reserved, factual, analytical, task-focused
                      </p>
                    </div>
                    <div className="bg-green-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-green-800 mb-2">Steadiness (S)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Measures:</strong> Patience, consistency, and persistence
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>High S:</strong> Patient, supportive, team-oriented, stable
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Low S:</strong> Fast-paced, active, flexible, adaptable
                      </p>
                    </div>
                    <div className="bg-blue-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-blue-800 mb-2">Compliance (C)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Measures:</strong> Structure, rules, and procedures
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>High C:</strong> Precise, analytical, rule-following, quality-focused
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Low C:</strong> Independent, flexible, informal, risk-tolerant
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Behavioral Pattern Analysis */}
            <div className="mb-8 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
              <h3 className="text-xl font-semibold text-indigo-800 mb-4">Your Behavioral Pattern Analysis</h3>
              <p className="text-gray-700 mb-4">
                Your behavioral pattern is defined by the combination of your dominant factors and how they interact.
                This creates a unique profile that predicts your workplace behaviors, motivations, and needs.
              </p>

              {/* Pattern-Specific Analysis */}
              {results.behavioral_pattern && (
                <div className="mb-6">
                  <h4 className="font-semibold text-indigo-700 mb-3">Pattern Type: {results.behavioral_pattern}</h4>

                  {/* Leadership Pattern */}
                  {(results.behavioral_pattern.includes('Leader') || results.behavioral_pattern.includes('Controller')) && (
                    <div className="bg-red-100 p-4 rounded-lg mb-4">
                      <h5 className="font-medium text-red-800 mb-2">Leadership Pattern Analysis</h5>
                      <p className="text-gray-700 mb-3">
                        You naturally take charge of situations and are comfortable making independent decisions.
                        Your drive for results and control makes you effective in leadership and management roles.
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h6 className="font-medium text-red-700 mb-1">Workplace Behaviors:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Quick decision-making and problem-solving</li>
                            <li>Direct communication style</li>
                            <li>Results-oriented approach</li>
                            <li>Comfortable with responsibility</li>
                          </ul>
                        </div>
                        <div>
                          <h6 className="font-medium text-red-700 mb-1">Development Focus:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Practice active listening</li>
                            <li>Consider team input before decisions</li>
                            <li>Develop patience with others</li>
                            <li>Balance speed with thoroughness</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Social Pattern */}
                  {(results.behavioral_pattern.includes('Persuader') || results.behavioral_pattern.includes('Influencer')) && (
                    <div className="bg-yellow-100 p-4 rounded-lg mb-4">
                      <h5 className="font-medium text-yellow-800 mb-2">Social Pattern Analysis</h5>
                      <p className="text-gray-700 mb-3">
                        You thrive on social interaction and excel at influencing and persuading others.
                        Your enthusiasm and communication skills make you effective in collaborative and people-oriented roles.
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h6 className="font-medium text-yellow-700 mb-1">Workplace Behaviors:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Excellent communication and presentation</li>
                            <li>Building relationships and networks</li>
                            <li>Enthusiastic and motivational</li>
                            <li>Creative problem-solving</li>
                          </ul>
                        </div>
                        <div>
                          <h6 className="font-medium text-yellow-700 mb-1">Development Focus:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Focus on task completion</li>
                            <li>Develop attention to detail</li>
                            <li>Balance social time with work output</li>
                            <li>Practice active listening</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Supportive Pattern */}
                  {(results.behavioral_pattern.includes('Supporter') || results.behavioral_pattern.includes('Stabilizer')) && (
                    <div className="bg-green-100 p-4 rounded-lg mb-4">
                      <h5 className="font-medium text-green-800 mb-2">Supportive Pattern Analysis</h5>
                      <p className="text-gray-700 mb-3">
                        You excel at creating harmony and supporting others in achieving their goals.
                        Your patient and steady approach makes you valuable in team-oriented and service roles.
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h6 className="font-medium text-green-700 mb-1">Workplace Behaviors:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Reliable and dependable</li>
                            <li>Strong listening skills</li>
                            <li>Team-oriented and collaborative</li>
                            <li>Consistent and thorough</li>
                          </ul>
                        </div>
                        <div>
                          <h6 className="font-medium text-green-700 mb-1">Development Focus:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Develop assertiveness skills</li>
                            <li>Embrace change and flexibility</li>
                            <li>Take initiative in new situations</li>
                            <li>Practice self-advocacy</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Analytical Pattern */}
                  {(results.behavioral_pattern.includes('Analyzer') || results.behavioral_pattern.includes('Perfectionist')) && (
                    <div className="bg-blue-100 p-4 rounded-lg mb-4">
                      <h5 className="font-medium text-blue-800 mb-2">Analytical Pattern Analysis</h5>
                      <p className="text-gray-700 mb-3">
                        You excel at analysis, precision, and ensuring quality and accuracy.
                        Your systematic approach and attention to detail make you valuable in technical and specialized roles.
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h6 className="font-medium text-blue-700 mb-1">Workplace Behaviors:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Exceptional attention to detail</li>
                            <li>Systematic problem-solving</li>
                            <li>High standards for quality</li>
                            <li>Thorough planning and analysis</li>
                          </ul>
                        </div>
                        <div>
                          <h6 className="font-medium text-blue-700 mb-1">Development Focus:</h6>
                          <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                            <li>Accept "good enough" when appropriate</li>
                            <li>Improve interpersonal communication</li>
                            <li>Be more flexible with changes</li>
                            <li>Balance analysis with action</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Workplace Applications */}
            <div className="mb-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
              <h3 className="text-xl font-semibold text-emerald-800 mb-4">Workplace Applications</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-emerald-700 mb-2">Performance Indicators:</h4>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-gray-700"><strong>How you perform best:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        {results.dominance_score > 6 && <li>In roles with autonomy and decision-making authority</li>}
                        {results.influence_score > 6 && <li>In collaborative, people-oriented environments</li>}
                        {results.steadiness_score > 6 && <li>In stable, supportive team settings</li>}
                        {results.compliance_score > 6 && <li>In structured environments with clear expectations</li>}
                      </ul>
                    </div>

                    <div>
                      <p className="text-gray-700"><strong>Stress indicators:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        {results.dominance_score < 4 && <li>Excessive control or micromanagement</li>}
                        {results.influence_score < 4 && <li>Lack of social interaction or recognition</li>}
                        {results.steadiness_score < 4 && <li>Rapid, unpredictable changes</li>}
                        {results.compliance_score < 4 && <li>Strict rules and excessive procedures</li>}
                      </ul>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-700 mb-2">Management and Motivation:</h4>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="text-gray-700"><strong>Ideal management style:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        {results.dominance_score > 6 && <li>Hands-off with clear goals and objectives</li>}
                        {results.influence_score > 6 && <li>Supportive with recognition and feedback</li>}
                        {results.steadiness_score > 6 && <li>Patient, consistent, and relationship-focused</li>}
                        {results.compliance_score > 6 && <li>Clear expectations and detailed instructions</li>}
                      </ul>
                    </div>

                    <div>
                      <p className="text-gray-700"><strong>Key motivators:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        {results.dominance_score > 6 && <li>Achievement, control, and results</li>}
                        {results.influence_score > 6 && <li>Social recognition and relationships</li>}
                        {results.steadiness_score > 6 && <li>Security, stability, and helping others</li>}
                        {results.compliance_score > 6 && <li>Quality, accuracy, and following procedures</li>}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">Behavioral Factor Scores</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {results.dominance_score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Dominance</div>
                  <div className="text-xs text-gray-500">Leadership & Control</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-600">
                    {results.influence_score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Influence</div>
                  <div className="text-xs text-gray-500">Social & Persuasive</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {results.steadiness_score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Steadiness</div>
                  <div className="text-xs text-gray-500">Patient & Supportive</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {results.compliance_score.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Compliance</div>
                  <div className="text-xs text-gray-500">Analytical & Precise</div>
                </div>
              </div>
            </div>

            <div className="mb-8 bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-3">Primary & Secondary Factors</h3>
              <div className="flex justify-center space-x-8">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-800">{results.primary_factor}</div>
                  <div className="text-sm text-gray-600">Primary Factor</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-800">{results.secondary_factor}</div>
                  <div className="text-sm text-gray-600">Secondary Factor</div>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={() => navigate('/assessments')}
              >
                Back to Assessments
              </Button>
              <Button
                onClick={() => {
                  setResults(null);
                  setCurrentQuestion(0);
                  setAnswers({});
                }}
              >
                Retake Assessment
              </Button>
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
          <p className="text-gray-600">Assessment not found</p>
          <Button onClick={() => navigate('/assessments')} className="mt-4">
            Back to Assessments
          </Button>
        </div>
      </div>
    );
  }

  const question = assessment.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / assessment.questions.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-800">{assessment.title}</h2>
              <span className="text-sm text-gray-500">
                Question {currentQuestion + 1} of {assessment.questions.length}
              </span>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <p className="text-gray-600 mb-8">{assessment.description}</p>
          </div>

          <div className="mb-8">
            <div className="mb-2">
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                {question.factor}
              </span>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-6">
              {question.question_text}
            </h3>

            <div className="space-y-3">
              {question.options.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleAnswer(question.id, option.value)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-200 ${
                    answers[question.id] === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-gray-800">{option.text}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentQuestion === 0}
            >
              Previous
            </Button>

            {currentQuestion === assessment.questions.length - 1 ? (
              <Button
                onClick={submitAssessment}
                disabled={!answers[question.id] || isSubmitting}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isSubmitting ? 'Submitting...' : 'Get Your Profile'}
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                disabled={!answers[question.id]}
              >
                Next
              </Button>
            )}
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PredictiveIndexPage;
