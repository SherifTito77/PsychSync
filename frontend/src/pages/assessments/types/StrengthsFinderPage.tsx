import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';

interface StrengthsFinderQuestion {
  id: number;
  question_text: string;
  dimension: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface StrengthsFinderAssessment {
  id: string;
  title: string;
  description: string;
  questions: StrengthsFinderQuestion[];
}

interface StrengthsFinderResult {
  top_strengths: Array<{
    strength: string;
    score: number;
    description: string;
    applications: string[];
  }>;
  all_scores: Record<string, number>;
  summary: string;
  responses_count: number;
  submitted_at: string;
}

const StrengthsFinderPage: React.FC = () => {
  const [assessment, setAssessment] = useState<StrengthsFinderAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<StrengthsFinderResult | null>(null);
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

      const response = await apiClient.get('/assessment-questions/strengthsfinder');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;
        const strengthsFinderAssessment: StrengthsFinderAssessment = {
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
        setAssessment(strengthsFinderAssessment);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Failed to load StrengthsFinder assessment:', error);
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
      const response = await apiClient.post('/strengthsfinder-test-submit', {
        assessment_type: 'strengthsfinder',
        responses: answers,
        raw_type: 'StrengthsFinder'
      });

      if (response.data && response.data.success) {
        setResults(response.data.result);
        console.log('✅ StrengthsFinder assessment submitted successfully');
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading StrengthsFinder Assessment...</p>
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
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Your Top 5 Strengths</h2>
              <div className="inline-block px-6 py-3 bg-green-100 text-green-800 rounded-full text-lg font-semibold">
                StrengthsFinder Results
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-700 mb-4">Summary</h3>
              <p className="text-gray-600 mb-6">{results.summary}</p>
            </div>

            {/* StrengthsFinder Educational Content */}
            <div className="mb-8 p-6 bg-green-50 rounded-lg border border-green-200">
              <h3 className="text-xl font-semibold text-green-800 mb-4">Understanding Your StrengthsFinder Results</h3>
              <p className="text-gray-700 mb-4">
                StrengthsFinder is a scientifically developed assessment that identifies your natural talents and recurring
                patterns of thought, feeling, or behavior. These are your innate abilities that, when invested in and
                developed, become your most powerful strengths for personal and professional success.
              </p>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-green-800 mb-2">The Philosophy Behind Strengths:</h4>
                  <div className="bg-white p-4 rounded-lg border">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-2">Core Principles:</h5>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                          <li><strong>Talent × Investment = Strength:</strong> Natural talent developed through practice</li>
                          <li><strong>Focus on Strengths:</strong> More growth comes from building strengths than fixing weaknesses</li>
                          <li><strong>Natural Patterns:</strong> Your strengths feel effortless and energizing</li>
                          <li><strong>Consistent Performance:</strong> You deliver near-perfect performance in strength areas</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-semibold text-gray-800 mb-2">The Research:</h5>
                        <p className="text-gray-700 text-sm mb-2">
                          Based on 40+ years of research by Dr. Donald Clifton and Gallup studying success
                          patterns across millions of people worldwide.
                        </p>
                        <p className="text-gray-700 text-sm">
                          The assessment identifies talents across 34 distinct themes, with your top 5 representing
                          your greatest potential for excellence.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-green-800 mb-2">Why Focus on Strengths?</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <h5 className="font-medium text-blue-700 mb-1">Performance</h5>
                      <p className="text-gray-700 text-sm">
                        People who use their strengths every day are 6x more likely to be engaged
                        in their work and 3x more likely to report excellent quality of life.
                      </p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <h5 className="font-medium text-purple-700 mb-1">Energy</h5>
                      <p className="text-gray-700 text-sm">
                        Working in your strength areas feels energizing rather than draining.
                        You can work longer and more effectively when using natural talents.
                      </p>
                    </div>
                    <div className="bg-yellow-50 p-3 rounded-lg">
                      <h5 className="font-medium text-yellow-700 mb-1">Growth</h5>
                      <p className="text-gray-700 text-sm">
                        You can achieve orders of magnitude more growth in areas of talent than
                        in areas of weakness. Focus where you have natural advantage.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Strength Development Strategies */}
            <div className="mb-8 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
              <h3 className="text-xl font-semibold text-indigo-800 mb-4">Living and Leading with Your Strengths</h3>
              <p className="text-gray-700 mb-4">
                Understanding your strengths is just the beginning. The real power comes from intentionally
                applying and developing these talents in your daily life, work, and relationships.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-indigo-700 mb-3">Daily Strength Application:</h4>
                  <div className="space-y-3 text-sm">
                    <div className="bg-white p-3 rounded-lg">
                      <h5 className="font-medium text-gray-800 mb-1">Name, Claim, Aim:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li><strong>Name:</strong> Acknowledge and own your talents</li>
                        <li><strong>Claim:</strong> Take pride in what makes you unique</li>
                        <li><strong>Aim:</strong> Intentionally use strengths to achieve goals</li>
                      </ul>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <h5 className="font-medium text-gray-800 mb-1">Strength Integration:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Look for opportunities to use top 5 strengths daily</li>
                        <li>Volunteer for projects that leverage your talents</li>
                        <li>Teach others about using their strengths</li>
                        <li>Build work and life around your natural talents</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-indigo-700 mb-3">Partnerships and Teams:</h4>
                  <div className="space-y-3 text-sm">
                    <div className="bg-white p-3 rounded-lg">
                      <h5 className="font-medium text-gray-800 mb-1">Complementary Strengths:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Partner with people who have different strengths</li>
                        <li>Respect and value different talent perspectives</li>
                        <li>Build teams with diverse strength profiles</li>
                        <li>Create strength-based role assignments</li>
                      </ul>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <h5 className="font-medium text-gray-800 mb-1">Strength-Based Leadership:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Help others discover and use their strengths</li>
                        <li>Delegate tasks based on team members' talents</li>
                        <li>Recognize and praise strength applications</li>
                        <li>Create environments where strengths can flourish</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Common Strength Themes Overview */}
            <div className="mb-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
              <h3 className="text-xl font-semibold text-emerald-800 mb-4">The 34 Strength Themes</h3>
              <p className="text-gray-700 mb-4">
                Your top 5 strengths are highlighted below, but understanding all 34 themes helps you recognize
                strengths in others and appreciate the full spectrum of human talent.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-white p-3 rounded-lg border">
                  <h5 className="font-semibold text-red-700 mb-1">Executing Themes (9)</h5>
                  <p className="text-gray-700 text-sm mb-2">Making things happen:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Achiever, Activator, Arranger, Belief, Consistency</li>
                    <li>• Deliberative, Discipline, Focus, Responsibility, Restorative</li>
                  </ul>
                </div>
                <div className="bg-white p-3 rounded-lg border">
                  <h5 className="font-semibold text-blue-700 mb-1">Influencing Themes (8)</h5>
                  <p className="text-gray-700 text-sm mb-2">Taking command, selling ideas:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Command, Communication, Competition, Maximizer</li>
                    <li>• Self-Assurance, Significance, Woo</li>
                  </ul>
                </div>
                <div className="bg-white p-3 rounded-lg border">
                  <h5 className="font-semibold text-green-700 mb-1">Relationship Building Themes (9)</h5>
                  <p className="text-gray-700 text-sm mb-2">Connecting with others:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Adaptability, Connectedness, Developer, Empathy</li>
                    <li>• Harmony, Includer, Individualization, Positivity, Relator</li>
                  </ul>
                </div>
                <div className="bg-white p-3 rounded-lg border">
                  <h5 className="font-semibold text-yellow-700 mb-1">Strategic Thinking Themes (8)</h5>
                  <p className="text-gray-700 text-sm mb-2">Analyzing, thinking about the future:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li>• Analytical, Context, Futuristic, Ideation</li>
                    <li>• Input, Intellection, Learner, Strategic</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="space-y-6 mb-8">
              {results.top_strengths.map((strength, index) => (
                <div key={strength.strength} className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 border border-green-200">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-lg font-bold text-gray-800">
                      {index + 1}. {strength.strength}
                    </h4>
                    <div className="text-2xl font-bold text-green-600">
                      {strength.score.toFixed(1)}
                    </div>
                  </div>
                  <p className="text-gray-700 mb-4">{strength.description}</p>
                  <div>
                    <h5 className="font-semibold text-gray-700 mb-2">Practical Applications:</h5>
                    <ul className="list-disc list-inside space-y-1">
                      {strength.applications.map((app, appIndex) => (
                        <li key={appIndex} className="text-gray-600 text-sm">{app}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">All Strengths Scores</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {Object.entries(results.all_scores)
                  .sort(([,a], [,b]) => b - a)
                  .map(([strength, score]) => (
                    <div key={strength} className="bg-gray-50 rounded-lg p-3 text-center">
                      <div className="font-semibold text-gray-800 text-sm">{strength}</div>
                      <div className="text-xl font-bold text-green-600">{score.toFixed(1)}</div>
                    </div>
                  ))}
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
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <p className="text-gray-600 mb-8">{assessment.description}</p>
          </div>

          <div className="mb-8">
            <div className="mb-2">
              <span className="inline-block px-3 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
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
                      ? 'border-green-500 bg-green-50'
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
                {isSubmitting ? 'Submitting...' : 'Discover Your Strengths'}
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

export default StrengthsFinderPage;
