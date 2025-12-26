import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';

interface DISCQuestion {
  id: number;
  question_text: string;
  dimension: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface DISCAssessment {
  id: string;
  title: string;
  description: string;
  questions: DISCQuestion[];
}

interface DISCResult {
  disc_type: string;
  disc_description: string;
  scores: Record<string, number>;
  responses_count: number;
  submitted_at: string;
}

const DISCAssessmentPage: React.FC = () => {
  const [assessment, setAssessment] = useState<DISCAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<DISCResult | null>(null);
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

      const response = await apiClient.get('/assessment-questions/disc');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;
        const discAssessment: DISCAssessment = {
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
        setAssessment(discAssessment);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Failed to load DISC assessment:', error);
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
      const response = await apiClient.post('/disc-test-submit', {
        assessment_type: 'disc',
        responses: answers,
        raw_type: 'DISC'
      });

      if (response.data && response.data.success) {
        setResults(response.data.result);
        console.log('✅ DISC assessment submitted successfully');
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading DISC Assessment...</p>
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
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Your DISC Profile</h2>
              <div className="inline-block px-6 py-3 bg-purple-100 text-purple-800 rounded-full text-lg font-semibold">
                {results.disc_type}
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-700 mb-4">Behavioral Style</h3>
              <p className="text-gray-600 mb-6">{results.disc_description}</p>
            </div>

            {/* DISC Educational Content */}
            <div className="mb-8 p-6 bg-purple-50 rounded-lg border border-purple-200">
              <h3 className="text-xl font-semibold text-purple-800 mb-4">Understanding Your DISC Results</h3>
              <p className="text-gray-700 mb-4">
                DISC is a behavioral assessment tool based on the work of psychologist William Moulton Marston.
                It measures four primary behavioral styles that predict how people approach problems, interact with others,
                respond to pace, and respond to rules and procedures.
              </p>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-purple-800 mb-2">The Four DISC Behavioral Styles:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-red-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-red-800 mb-2">D - Dominance (Red)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Focus:</strong> Problems & Challenges
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Traits:</strong> Direct, decisive, results-oriented, competitive, strong-willed
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Motivation:</strong> Overcoming challenges and achieving results
                      </p>
                    </div>
                    <div className="bg-yellow-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-yellow-800 mb-2">I - Influence (Yellow)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Focus:</strong> People & Communication
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Traits:</strong> Enthusiastic, optimistic, collaborative, persuasive, talkative
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Motivation:</strong> Social recognition and building relationships
                      </p>
                    </div>
                    <div className="bg-green-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-green-800 mb-2">S - Steadiness (Green)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Focus:</strong> Pace & Consistency
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Traits:</strong> Patient, supportive, stable, reliable, team-oriented
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Motivation:</strong> Security and helping others
                      </p>
                    </div>
                    <div className="bg-blue-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-blue-800 mb-2">C - Conscientiousness (Blue)</h5>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Focus:</strong> Rules & Procedures
                      </p>
                      <p className="text-gray-700 text-sm mb-2">
                        <strong>Traits:</strong> Analytical, precise, private, quality-focused, systematic
                      </p>
                      <p className="text-gray-700 text-sm">
                        <strong>Motivation:</strong> Accuracy and following established standards
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Type-Specific Deep Dive */}
            <div className="mb-8 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
              <h3 className="text-xl font-semibold text-indigo-800 mb-4">Your DISC Type Deep Dive</h3>

              {/* D Type Analysis */}
              {results.disc_type === 'D' && (
                <div className="space-y-4">
                  <div className="bg-red-100 p-4 rounded-lg">
                    <h4 className="font-semibold text-red-800 mb-2">High Dominance Profile</h4>
                    <p className="text-gray-700 mb-3">
                      You're driven by results and aren't afraid to take charge of situations. You prefer direct communication
                      and thrive in environments where you can make independent decisions and see tangible outcomes.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-red-700 mb-1">Natural Strengths:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Quick decision-making under pressure</li>
                          <li>Strong leadership and initiative</li>
                          <li>Goal-oriented and competitive drive</li>
                          <li>Willingness to take calculated risks</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-red-700 mb-1">Growth Opportunities:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Practice active listening to understand others' perspectives</li>
                          <li>Consider the impact on team morale and relationships</li>
                          <li>Balance speed with thoughtful planning</li>
                          <li>Develop patience with less decisive team members</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* I Type Analysis */}
              {results.disc_type === 'I' && (
                <div className="space-y-4">
                  <div className="bg-yellow-100 p-4 rounded-lg">
                    <h4 className="font-semibold text-yellow-800 mb-2">High Influence Profile</h4>
                    <p className="text-gray-700 mb-3">
                      You thrive on social interaction and bring energy and enthusiasm to your environment. You're skilled at
                      inspiring and persuading others, often acting as the catalyst for team cohesion and positive atmosphere.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-yellow-700 mb-1">Natural Strengths:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Excellent communication and presentation skills</li>
                          <li>Building and maintaining professional relationships</li>
                          <li>Positive attitude that motivates others</li>
                          <li>Creative problem-solving and brainstorming</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-yellow-700 mb-1">Growth Opportunities:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Develop better time management and follow-through</li>
                          <li>Balance optimism with realistic assessment</li>
                          <li>Practice active listening vs. being the primary speaker</li>
                          <li>Focus on details and task completion</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* S Type Analysis */}
              {results.disc_type === 'S' && (
                <div className="space-y-4">
                  <div className="bg-green-100 p-4 rounded-lg">
                    <h4 className="font-semibold text-green-800 mb-2">High Steadiness Profile</h4>
                    <p className="text-gray-700 mb-3">
                      You bring stability and reliability to your environment. You excel at creating harmony and supporting
                      team members, preferring predictable environments where you can build long-term relationships and maintain consistency.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-green-700 mb-1">Natural Strengths:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Exceptional reliability and dependability</li>
                          <li>Patience and ability to support others</li>
                          <li>Strong listening and empathy skills</li>
                          <li>Consistency and attention to routine details</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-green-700 mb-1">Growth Opportunities:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Embrace change and be more adaptable</li>
                          <li>Practice assertiveness in expressing opinions</li>
                          <li>Take initiative in new situations</li>
                          <li>Balance supporting others with self-advocacy</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* C Type Analysis */}
              {results.disc_type === 'C' && (
                <div className="space-y-4">
                  <div className="bg-blue-100 p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2">High Conscientiousness Profile</h4>
                    <p className="text-gray-700 mb-3">
                      You excel at analysis and ensuring quality and accuracy. You prefer to work systematically,
                      following established procedures and maintaining high standards in everything you do.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-blue-700 mb-1">Natural Strengths:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Exceptional attention to detail and quality</li>
                          <li>Analytical and systematic problem-solving</li>
                          <li>Thorough planning and risk assessment</li>
                          <li>High standards and ethical conduct</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-blue-700 mb-1">Growth Opportunities:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li>Accept good enough vs. perfect when deadlines loom</li>
                          <li>Improve interpersonal communication and relationships</li>
                          <li>Be more flexible with changing priorities</li>
                          <li>Balance analysis with timely decision-making</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Practical Applications */}
            <div className="mb-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
              <h3 className="text-xl font-semibold text-emerald-800 mb-4">Practical Applications</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-emerald-700 mb-2">Communication Tips:</h4>
                  <div className="space-y-3 text-sm">
                    {results.disc_type === 'D' && (
                      <div>
                        <p className="text-gray-700"><strong>For others communicating with you:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Be direct and to the point</li>
                          <li>Focus on results and outcomes</li>
                          <li>Avoid excessive small talk</li>
                          <li>Present logical arguments</li>
                        </ul>
                      </div>
                    )}
                    {results.disc_type === 'I' && (
                      <div>
                        <p className="text-gray-700"><strong>For others communicating with you:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Allow time for social interaction</li>
                          <li>Use enthusiastic and positive language</li>
                          <li>Focus on people and relationships</li>
                          <li>Avoid being too critical or negative</li>
                        </ul>
                      </div>
                    )}
                    {results.disc_type === 'S' && (
                      <div>
                        <p className="text-gray-700"><strong>For others communicating with you:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Take time to build rapport</li>
                          <li>Be sincere and genuine</li>
                          <li>Provide reassurance and support</li>
                          <li>Avoid sudden changes or pressure</li>
                        </ul>
                      </div>
                    )}
                    {results.disc_type === 'C' && (
                      <div>
                        <p className="text-gray-700"><strong>For others communicating with you:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Provide facts and evidence</li>
                          <li>Be thorough and precise</li>
                          <li>Respect privacy and personal space</li>
                          <li>Avoid emotional appeals</li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-700 mb-2">Work Environment Preferences:</h4>
                  <div className="space-y-3 text-sm">
                    {results.disc_type === 'D' && (
                      <div>
                        <p className="text-gray-700"><strong>Ideal environments:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Leadership roles with autonomy</li>
                          <li>Results-driven cultures</li>
                          <li>Competitive environments</li>
                          <li>Clear goals and measurable outcomes</li>
                        </ul>
                      </div>
                    )}
                    {results.disc_type === 'I' && (
                      <div>
                        <p className="text-gray-700"><strong>Ideal environments:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Collaborative team settings</li>
                          <li>Public-facing or client-interaction roles</li>
                          <li>Creative and innovative workplaces</li>
                          <li>Environments that recognize achievement</li>
                        </ul>
                      </div>
                    )}
                    {results.disc_type === 'S' && (
                      <div>
                        <p className="text-gray-700"><strong>Ideal environments:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Stable, secure organizations</li>
                          <li>Supportive team cultures</li>
                          <li>Roles helping others achieve goals</li>
                          <li>Predictable work patterns</li>
                        </ul>
                      </div>
                    )}
                    {results.disc_type === 'C' && (
                      <div>
                        <p className="text-gray-700"><strong>Ideal environments:</strong></p>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                          <li>Quality-focused organizations</li>
                          <li>Research and analytical roles</li>
                          <li>Environments with clear procedures</li>
                          <li>Technical or specialized fields</li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">DISC Scores</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    results.disc_type === 'D' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {results.scores.D}
                  </div>
                  <div className="text-sm text-gray-600">Dominance</div>
                  <div className="text-xs text-gray-500">Direct & Decisive</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    results.disc_type === 'I' ? 'text-yellow-600' : 'text-gray-600'
                  }`}>
                    {results.scores.I}
                  </div>
                  <div className="text-sm text-gray-600">Influence</div>
                  <div className="text-xs text-gray-500">Outgoing & Optimistic</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    results.disc_type === 'S' ? 'text-green-600' : 'text-gray-600'
                  }`}>
                    {results.scores.S}
                  </div>
                  <div className="text-sm text-gray-600">Steadiness</div>
                  <div className="text-xs text-gray-500">Patient & Supportive</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    results.disc_type === 'C' ? 'text-blue-600' : 'text-gray-600'
                  }`}>
                    {results.scores.C}
                  </div>
                  <div className="text-sm text-gray-600">Conscientiousness</div>
                  <div className="text-xs text-gray-500">Analytical & Precise</div>
                </div>
              </div>
            </div>

            <div className="mb-8 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-3">Understanding Your DISC Type</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start">
                  <span className="text-red-600 font-semibold mr-2">D:</span>
                  <span className="text-gray-600">Dominance - Direct, results-oriented, strong-willed, fast-paced</span>
                </div>
                <div className="flex items-start">
                  <span className="text-yellow-600 font-semibold mr-2">I:</span>
                  <span className="text-gray-600">Influence - Enthusiastic, optimistic, collaborative, people-oriented</span>
                </div>
                <div className="flex items-start">
                  <span className="text-green-600 font-semibold mr-2">S:</span>
                  <span className="text-gray-600">Steadiness - Calm, methodical, patient, team-oriented</span>
                </div>
                <div className="flex items-start">
                  <span className="text-blue-600 font-semibold mr-2">C:</span>
                  <span className="text-gray-600">Conscientiousness - Analytical, precise, private, quality-focused</span>
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
                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <p className="text-gray-600 mb-8">{assessment.description}</p>
          </div>

          <div className="mb-8">
            <div className="mb-2">
              <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 text-sm font-medium rounded-full">
                {question.dimension}
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
                      ? 'border-purple-500 bg-purple-50'
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
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isSubmitting ? 'Submitting...' : 'Get Your DISC Profile'}
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

export default DISCAssessmentPage;
