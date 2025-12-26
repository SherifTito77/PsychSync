import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';

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

const BigFiveAssessmentPage: React.FC = () => {
  const [assessment, setAssessment] = useState<BigFiveAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<BigFiveResult | null>(null);
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

      const response = await apiClient.get('/assessment-questions/big-five');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;
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
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Failed to load Big Five assessment:', error);
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
      const response = await apiClient.post('/big-five-test-submit', {
        assessment_type: 'big_five',
        responses: answers,
        raw_type: 'Big Five'
      });

      if (response.data && response.data.success) {
        setResults(response.data.result);
        console.log('✅ Big Five assessment submitted successfully');
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Big Five Assessment...</p>
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
            <h2 className="text-3xl font-bold text-gray-800 mb-6">Your Big Five Results</h2>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-700 mb-4">Personality Profile</h3>
              <p className="text-gray-600 mb-6">{results.summary}</p>
            </div>

            {/* Big Five Educational Content */}
            <div className="mb-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="text-xl font-semibold text-blue-800 mb-4">Understanding Your Big Five Results</h3>
              <p className="text-gray-700 mb-4">
                The Big Five model (OCEAN) is the most scientifically validated personality framework, measuring five core dimensions
                of personality that remain relatively stable throughout your life. Your scores represent where you fall on each spectrum
                compared to the general population.
              </p>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-blue-800 mb-2">The OCEAN Model Explained:</h4>
                  <ul className="list-disc list-inside space-y-2 text-gray-700">
                    <li><strong>O - Openness:</strong> Your preference for novelty, creativity, and intellectual curiosity vs. preference for routine and familiarity</li>
                    <li><strong>C - Conscientiousness:</strong> Your tendency toward organization, responsibility, and self-discipline vs. spontaneity and flexibility</li>
                    <li><strong>E - Extraversion:</strong> Your orientation toward external stimulation, social interaction, and assertiveness vs. need for solitude and quiet</li>
                    <li><strong>A - Agreeableness:</strong> Your inclination toward cooperation, compassion, and social harmony vs. skepticism and independence</li>
                    <li><strong>N - Neuroticism:</strong> Your propensity for emotional instability, anxiety, and mood swings vs. emotional stability and resilience</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Detailed Trait Analysis */}
            <div className="mb-8 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
              <h3 className="text-xl font-semibold text-indigo-800 mb-4">Your Personality Insights</h3>

              {/* Openness Section */}
              {results.descriptions.Openness && (
                <div className="mb-6">
                  <h4 className="font-semibold text-indigo-700 mb-2">Openness to Experience: {results.descriptions.Openness.level}</h4>
                  <p className="text-gray-700 mb-3">{results.descriptions.Openness.description}</p>

                  {results.descriptions.Openness.level === 'High' && (
                    <div className="p-4 bg-indigo-100 rounded-lg">
                      <h5 className="font-medium text-indigo-800 mb-2">Your High Openness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely enjoy creative pursuits, artistic expression, and intellectual exploration</li>
                        <li>You may be comfortable with ambiguity and enjoy considering multiple perspectives</li>
                        <li>You might prefer careers that offer variety, innovation, and continuous learning</li>
                        <li>Your growth areas: Ensure creative exploration doesn't lead to unfinished projects or impractical decisions</li>
                      </ul>
                    </div>
                  )}

                  {results.descriptions.Openness.level === 'Moderate' && (
                    <div className="p-4 bg-gray-100 rounded-lg">
                      <h5 className="font-medium text-gray-800 mb-2">Your Moderate Openness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You balance practical thinking with creative exploration when needed</li>
                        <li>You can adapt to both traditional and innovative approaches</li>
                        <li>You're open to new ideas but also value proven methods</li>
                      </ul>
                    </div>
                  )}

                  {results.descriptions.Openness.level === 'Low' && (
                    <div className="p-4 bg-indigo-100 rounded-lg">
                      <h5 className="font-medium text-indigo-800 mb-2">Your Lower Openness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely prefer practical, down-to-earth approaches to problem-solving</li>
                        <li>You may excel at implementing established methods and maintaining consistency</li>
                        <li>You might prefer careers with clear structures and predictable routines</li>
                        <li>Your growth areas: Consider exploring new perspectives and occasionally trying unfamiliar approaches</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Conscientiousness Section */}
              {results.descriptions.Conscientiousness && (
                <div className="mb-6">
                  <h4 className="font-semibold text-indigo-700 mb-2">Conscientiousness: {results.descriptions.Conscientiousness.level}</h4>
                  <p className="text-gray-700 mb-3">{results.descriptions.Conscientiousness.description}</p>

                  {results.descriptions.Conscientiousness.level === 'High' && (
                    <div className="p-4 bg-green-100 rounded-lg">
                      <h5 className="font-medium text-green-800 mb-2">Your High Conscientiousness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely excel at planning, organizing, and following through on commitments</li>
                        <li>You may have strong self-discipline and attention to detail</li>
                        <li>Others probably see you as reliable, responsible, and dependable</li>
                        <li>Your growth areas: Balance perfectionism with flexibility and avoid over-scheduling</li>
                      </ul>
                    </div>
                  )}

                  {results.descriptions.Conscientiousness.level === 'Low' && (
                    <div className="p-4 bg-green-100 rounded-lg">
                      <h5 className="font-medium text-green-800 mb-2">Your Lower Conscientiousness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely prefer spontaneity and adaptability over strict planning</li>
                        <li>You may be flexible and able to pivot quickly when circumstances change</li>
                        <li>You might excel in dynamic environments that require rapid response</li>
                        <li>Your growth areas: Consider developing basic planning systems and accountability structures</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Extraversion Section */}
              {results.descriptions.Extraversion && (
                <div className="mb-6">
                  <h4 className="font-semibold text-indigo-700 mb-2">Extraversion: {results.descriptions.Extraversion.level}</h4>
                  <p className="text-gray-700 mb-3">{results.descriptions.Extraversion.description}</p>

                  {results.descriptions.Extraversion.level === 'High' && (
                    <div className="p-4 bg-yellow-100 rounded-lg">
                      <h5 className="font-medium text-yellow-800 mb-2">Your High Extraversion Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely gain energy from social interaction and external stimulation</li>
                        <li>You may be outgoing, assertive, and comfortable in group settings</li>
                        <li>You might prefer collaborative work environments and team-based projects</li>
                        <li>Your growth areas: Balance social time with adequate rest and reflection</li>
                      </ul>
                    </div>
                  )}

                  {results.descriptions.Extraversion.level === 'Low' && (
                    <div className="p-4 bg-yellow-100 rounded-lg">
                      <h5 className="font-medium text-yellow-800 mb-2">Your Lower Extraversion (Introversion) Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely gain energy from solitude and quiet reflection</li>
                        <li>You may prefer deeper one-on-one relationships over large group interactions</li>
                        <li>You might excel at focused, independent work and detailed analysis</li>
                        <li>Your growth areas: Recognize the value of your reflective nature while developing social comfort</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Agreeableness Section */}
              {results.descriptions.Agreeableness && (
                <div className="mb-6">
                  <h4 className="font-semibold text-indigo-700 mb-2">Agreeableness: {results.descriptions.Agreeableness.level}</h4>
                  <p className="text-gray-700 mb-3">{results.descriptions.Agreeableness.description}</p>

                  {results.descriptions.Agreeableness.level === 'High' && (
                    <div className="p-4 bg-purple-100 rounded-lg">
                      <h5 className="font-medium text-purple-800 mb-2">Your High Agreeableness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely prioritize cooperation, harmony, and helping others</li>
                        <li>You may be empathetic, patient, and skilled at building relationships</li>
                        <li>Others probably see you as warm, trusting, and supportive</li>
                        <li>Your growth areas: Develop assertiveness skills and learn to say "no" when necessary</li>
                      </ul>
                    </div>
                  )}

                  {results.descriptions.Agreeableness.level === 'Low' && (
                    <div className="p-4 bg-purple-100 rounded-lg">
                      <h5 className="font-medium text-purple-800 mb-2">Your Lower Agreeableness Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely value directness, competition, and objective decision-making</li>
                        <li>You may be more skeptical and willing to challenge others' viewpoints</li>
                        <li>You might excel at negotiations and making tough decisions</li>
                        <li>Your growth areas: Consider others' perspectives and develop collaborative skills</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Neuroticism Section */}
              {results.descriptions.Neuroticism && (
                <div className="mb-6">
                  <h4 className="font-semibold text-indigo-700 mb-2">Neuroticism: {results.descriptions.Neuroticism.level}</h4>
                  <p className="text-gray-700 mb-3">{results.descriptions.Neuroticism.description}</p>

                  {results.descriptions.Neuroticism.level === 'High' && (
                    <div className="p-4 bg-red-100 rounded-lg">
                      <h5 className="font-medium text-red-800 mb-2">Your Higher Neuroticism Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You may experience emotions more intensely and be more sensitive to stress</li>
                        <li>You might worry more about potential problems and negative outcomes</li>
                        <li>You could be more attuned to emotional nuances in yourself and others</li>
                        <li>Your growth areas: Develop stress management techniques and cognitive reframing skills</li>
                      </ul>
                    </div>
                  )}

                  {results.descriptions.Neuroticism.level === 'Low' && (
                    <div className="p-4 bg-green-100 rounded-lg">
                      <h5 className="font-medium text-green-800 mb-2">Your Lower Neuroticism (Emotional Stability) Suggests:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>You likely remain calm and composed under pressure</li>
                        <li>You may be resilient in the face of setbacks and stressors</li>
                        <li>You might have an optimistic outlook and handle challenges with confidence</li>
                        <li>Your growth areas: Stay aware of others' emotional needs while maintaining your stability</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Practical Applications */}
            <div className="mb-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
              <h3 className="text-xl font-semibold text-emerald-800 mb-4">Practical Applications</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-emerald-700 mb-2">Career Considerations:</h4>
                  <p className="text-gray-700 mb-3">
                    Your Big Five profile can guide career choices that align with your natural tendencies:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                    <li><strong>High Openness:</strong> Creative fields, research, innovation, arts, consulting</li>
                    <li><strong>High Conscientiousness:</strong> Management, accounting, engineering, healthcare, law</li>
                    <li><strong>High Extraversion:</strong> Sales, leadership, public relations, event planning</li>
                    <li><strong>High Agreeableness:</strong> Counseling, teaching, social work, customer service</li>
                    <li><strong>High Emotional Stability:</strong> Emergency services, finance, high-pressure roles</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-emerald-700 mb-2">Relationship Insights:</h4>
                  <p className="text-gray-700 mb-3">
                    Understanding your personality helps in building and maintaining relationships:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                    <li>Recognize your natural communication style and needs</li>
                    <li>Understand how others may perceive your behavior</li>
                    <li>Identify potential conflicts with different personality types</li>
                    <li>Develop strategies for bridging personality differences</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {Object.entries(results.descriptions).map(([dimension, desc]) => (
                <div key={dimension} className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-800 mb-2">{dimension}</h4>
                  <div className="mb-2">
                    <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                      desc.level === 'High' ? 'bg-green-100 text-green-800' :
                      desc.level === 'Moderate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {desc.level}
                    </span>
                    <span className="ml-2 text-gray-600">
                      Score: {results.scores[dimension]?.toFixed(1)}/5.0
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{desc.description}</p>
                </div>
              ))}
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
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <p className="text-gray-600 mb-8">{assessment.description}</p>
          </div>

          <div className="mb-8">
            <div className="mb-2">
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                {question.trait}
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
                      ? 'border-indigo-500 bg-indigo-50'
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
                className="bg-green-600 hover:bg-green-700"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Assessment'}
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

export default BigFiveAssessmentPage;
