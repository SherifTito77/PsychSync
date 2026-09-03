import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';

interface SocialStylesQuestion {
  id: number;
  question_text: string;
  style: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface SocialStylesAssessment {
  id: string;
  title: string;
  description: string;
  questions: SocialStylesQuestion[];
}

interface SocialStylesResult {
  social_style_type: string;
  type_info: {
    title: string;
    description: string;
    strengths: string[];
    challenges: string[];
    growth_path: string;
  };
  all_scores: Record<string, number>;
  dominant_score: number;
  confidence: number;
  style_breakdown: {
    analytical: number;
    driver: number;
    amiable: number;
    expressive: number;
  };
  responses_count: number;
  submitted_at: string;
}

const SocialStylesPage: React.FC = () => {
  const [assessment, setAssessment] = useState<SocialStylesAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<SocialStylesResult | null>(null);
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

      const response = await apiClient.get('/assessments/assessment-questions/social-styles');

      if (response.data && (response.data as any).success) {
        const backendAssessment = (response.data as any).assessment;
        const socialStylesAssessment: SocialStylesAssessment = {
          id: backendAssessment.id,
          title: backendAssessment.title,
          description: backendAssessment.description,
          questions: backendAssessment.questions.map((q: any) => ({
            id: q.id,
            question_text: q.question_text,
            style: q.style,
            options: q.options.map((opt: any) => ({
              text: opt.text,
              value: opt.value
            }))
          }))
        };
        setAssessment(socialStylesAssessment);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Failed to load Social Styles assessment:', error);
      setError('Failed to load assessment. Please refresh the page.');
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

  const handleSubmit = async () => {
    if (!assessment) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // Calculate Social Styles results based on answers
      const styleCounts: Record<string, number> = {
        'Analytical': 0,
        'Driver': 0,
        'Amiable': 0,
        'Expressive': 0
      };

      // Count answers for each style
      Object.values(answers).forEach(answer => {
        if (styleCounts.hasOwnProperty(answer)) {
          styleCounts[answer]++;
        }
      });

      // Determine dominant style
      const dominantStyle = Object.entries(styleCounts).reduce((a, b) =>
        styleCounts[a[0] as keyof typeof styleCounts] > styleCounts[b[0] as keyof typeof styleCounts] ? a : b
      )[0];

      const totalQuestions = assessment.questions.length;
      const confidence = (styleCounts[dominantStyle] / totalQuestions) * 100;

      const results: SocialStylesResult = {
        social_style_type: dominantStyle,
        type_info: {
          title: `${dominantStyle} Style`,
          description: getStyleDescription(dominantStyle),
          strengths: getStyleStrengths(dominantStyle),
          challenges: getStyleChallenges(dominantStyle),
          growth_path: getStyleGrowthPath(dominantStyle)
        },
        all_scores: styleCounts,
        dominant_score: styleCounts[dominantStyle],
        confidence: Math.round(confidence),
        style_breakdown: {
          analytical: styleCounts['Analytical'] || 0,
          driver: styleCounts['Driver'] || 0,
          amiable: styleCounts['Amiable'] || 0,
          expressive: styleCounts['Expressive'] || 0
        },
        responses_count: totalQuestions,
        submitted_at: new Date().toISOString()
      };

      setResults(results);
    } catch (error) {
      console.error('❌ Failed to submit assessment:', error);
      setError('Failed to submit assessment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStyleDescription = (style: string): string => {
    const descriptions: Record<string, string> = {
      'Analytical': 'Logical, systematic thinkers who focus on data and facts to make decisions.',
      'Driver': 'Results-oriented leaders who focus on efficiency and getting things done quickly.',
      'Amiable': 'Supportive team players who prioritize relationships and harmony.',
      'Expressive': 'Enthusiastic communicators who focus on people and possibilities.'
    };
    return descriptions[style] || '';
  };

  const getStyleStrengths = (style: string): string[] => {
    const strengths: Record<string, string[]> = {
      'Analytical': ['Systematic thinking', 'Attention to detail', 'Objective analysis', 'Problem-solving'],
      'Driver': ['Decision making', 'Leadership', 'Efficiency', 'Goal orientation'],
      'Amiable': ['Team building', 'Empathy', 'Collaboration', 'Relationship management'],
      'Expressive': ['Communication', 'Creativity', 'Persuasion', 'Motivation']
    };
    return strengths[style] || [];
  };

  const getStyleChallenges = (style: string): string[] => {
    const challenges: Record<string, string[]> = {
      'Analytical': ['Analysis paralysis', 'Overly critical', 'Slow decision making', 'Perfectionism'],
      'Driver': ['Impatience', 'Insensitivity to others', 'Work-life imbalance', 'Risk-taking'],
      'Amiable': ['Conflict avoidance', 'Difficulty saying no', 'Over-commitment', 'Resistance to change'],
      'Expressive': ['Disorganization', 'Impulsiveness', 'Attention seeking', 'Lack of follow-through']
    };
    return challenges[style] || [];
  };

  const getStyleGrowthPath = (style: string): string => {
    const paths: Record<string, string> = {
      'Analytical': 'Focus on balancing analysis with timely action and developing emotional intelligence.',
      'Driver': 'Work on patience, active listening, and considering the human impact of decisions.',
      'Amiable': 'Practice assertiveness, conflict resolution, and embracing constructive feedback.',
      'Expressive': 'Develop organization skills, follow-through, and active listening habits.'
    };
    return paths[style] || '';
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Loading Social Styles Assessment...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-700">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  if (results) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-center mb-8">🎯 Your Social Style Results</h2>

          <div className="text-center mb-8">
            <div className="text-2xl font-semibold text-blue-600 mb-2">{results.social_style_type}</div>
            <div className="text-gray-600">{results.type_info.title}</div>
            <div className="text-sm text-gray-500 mt-1">Confidence: {results.confidence}%</div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="font-semibold mb-3">Style Breakdown</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Analytical:</span>
                  <span>{results.style_breakdown.analytical}</span>
                </div>
                <div className="flex justify-between">
                  <span>Driver:</span>
                  <span>{results.style_breakdown.driver}</span>
                </div>
                <div className="flex justify-between">
                  <span>Amiable:</span>
                  <span>{results.style_breakdown.amiable}</span>
                </div>
                <div className="flex justify-between">
                  <span>Expressive:</span>
                  <span>{results.style_breakdown.expressive}</span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-6 rounded-lg">
              <h3 className="font-semibold mb-3">Description</h3>
              <p className="text-gray-700">{results.type_info.description}</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-green-50 p-6 rounded-lg">
              <h3 className="font-semibold mb-3">💪 Strengths</h3>
              <ul className="list-disc list-inside space-y-1">
                {results.type_info.strengths.map((strength, index) => (
                  <li key={index} className="text-gray-700">{strength}</li>
                ))}
              </ul>
            </div>

            <div className="bg-yellow-50 p-6 rounded-lg">
              <h3 className="font-semibold mb-3">⚠️ Growth Areas</h3>
              <ul className="list-disc list-inside space-y-1">
                {results.type_info.challenges.map((challenge, index) => (
                  <li key={index} className="text-gray-700">{challenge}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-purple-50 p-6 rounded-lg mb-8">
            <h3 className="font-semibold mb-3">🌱 Growth Path</h3>
            <p className="text-gray-700">{results.type_info.growth_path}</p>
          </div>

          {/* Social Styles Educational Content */}
          <div className="mb-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="text-xl font-semibold text-blue-800 mb-4">Understanding Your Social Style Results</h3>
            <p className="text-gray-700 mb-4">
              Social Styles is a behavioral model developed by David Merrill and Roger Reid that categorizes
              workplace communication and behavior patterns. The model uses two axes: Assertiveness (telling
              vs. asking) and Responsiveness (task vs. people focus) to create four distinct styles.
            </p>

            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-blue-800 mb-2">The Social Styles Framework:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-4 rounded-lg border">
                    <h5 className="font-semibold text-gray-800 mb-2">The Two Dimensions:</h5>
                    <div className="space-y-3 text-sm">
                      <div>
                        <strong className="text-blue-700">Assertiveness (Horizontal Axis):</strong>
                        <p className="text-gray-600">How people influence others and express opinions</p>
                        <ul className="list-disc list-inside ml-4 text-gray-500">
                          <li><strong>Tell</strong> (Less Responsive): Direct, forceful</li>
                          <li><strong>Ask</strong> (More Responsive): Cooperative, moderate</li>
                        </ul>
                      </div>
                      <div>
                        <strong className="text-blue-700">Responsiveness (Vertical Axis):</strong>
                        <p className="text-gray-600">How people express emotions and react to others</p>
                        <ul className="list-disc list-inside ml-4 text-gray-500">
                          <li><strong>Task</strong> (Less Responsive): Controlled, analytical</li>
                          <li><strong>People</strong> (More Responsive): Emotional, expressive</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <h5 className="font-semibold text-gray-800 mb-2">The Four Social Styles:</h5>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-center p-2 bg-red-50 rounded">
                        <div className="font-semibold text-red-700">Driver</div>
                        <div className="text-gray-600">Tell + Task</div>
                      </div>
                      <div className="text-center p-2 bg-yellow-50 rounded">
                        <div className="font-semibold text-yellow-700">Expressive</div>
                        <div className="text-gray-600">Tell + People</div>
                      </div>
                      <div className="text-center p-2 bg-green-50 rounded">
                        <div className="font-semibold text-green-700">Amiable</div>
                        <div className="text-gray-600">Ask + People</div>
                      </div>
                      <div className="text-center p-2 bg-blue-50 rounded">
                        <div className="font-semibold text-blue-700">Analytical</div>
                        <div className="text-gray-600">Ask + Task</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Style-Specific Deep Dive */}
          <div className="mb-8 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
            <h3 className="text-xl font-semibold text-indigo-800 mb-4">Your {results.social_style_type} Style Deep Dive</h3>

            {/* Driver Style Analysis */}
            {results.social_style_type === 'Driver' && (
              <div className="space-y-4">
                <div className="bg-red-100 p-4 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-2">Driver Style Characteristics</h4>
                  <p className="text-gray-700 mb-3">
                    As a Driver, you're results-oriented and decisive. You prefer direct communication and focus on
                    achieving goals efficiently. You naturally take charge and have a strong sense of urgency.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-red-700 mb-1">Communication Preferences:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Direct, brief, and to the point</li>
                        <li>Focus on results and outcomes</li>
                        <li>Prefer data over emotions</li>
                        <li>Speed over thoroughness when necessary</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-red-700 mb-1">Workplace Behaviors:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Takes initiative and makes decisions</li>
                        <li>Comfortable with conflict when necessary</li>
                        <li>Delegates effectively</li>
                        <li>Focuses on efficiency and results</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Expressive Style Analysis */}
            {results.social_style_type === 'Expressive' && (
              <div className="space-y-4">
                <div className="bg-yellow-100 p-4 rounded-lg">
                  <h4 className="font-semibold text-yellow-800 mb-2">Expressive Style Characteristics</h4>
                  <p className="text-gray-700 mb-3">
                    As an Expressive, you're enthusiastic and people-oriented. You excel at inspiring others and
                    thrive in social environments. You communicate openly and are comfortable taking risks.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-yellow-700 mb-1">Communication Preferences:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Enthusiastic and expressive</li>
                        <li>Focus on people and relationships</li>
                        <li>Enjoy brainstorming and new ideas</li>
                        <li>Use stories and examples</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-yellow-700 mb-1">Workplace Behaviors:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Build networks and relationships</li>
                        <li>Motivate and inspire others</li>
                        <li>Generate creative solutions</li>
                        <li>Thrive in collaborative environments</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Amiable Style Analysis */}
            {results.social_style_type === 'Amiable' && (
              <div className="space-y-4">
                <div className="bg-green-100 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">Amiable Style Characteristics</h4>
                  <p className="text-gray-700 mb-3">
                    As an Amiable, you're supportive and relationship-focused. You excel at creating harmony
                    and building consensus. You're reliable and prioritize people's feelings and security.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-green-700 mb-1">Communication Preferences:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Cooperative and supportive</li>
                        <li>Focus on feelings and relationships</li>
                        <li>Ask questions and listen actively</li>
                        <li>Provide reassurance and support</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-green-700 mb-1">Workplace Behaviors:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Build team cohesion and trust</li>
                        <li>Support and develop others</li>
                        <li>Mediate conflicts effectively</li>
                        <li>Create stable, secure environments</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Analytical Style Analysis */}
            {results.social_style_type === 'Analytical' && (
              <div className="space-y-4">
                <div className="bg-blue-100 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">Analytical Style Characteristics</h4>
                  <p className="text-gray-700 mb-3">
                    As an Analytical, you're logical and detail-oriented. You excel at analysis and systematic thinking.
                    You prefer objective data and make decisions based on careful consideration of facts.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-blue-700 mb-1">Communication Preferences:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Precise and logical</li>
                        <li>Focus on data and facts</li>
                        <li>Provide detailed explanations</li>
                        <li>Ask clarifying questions</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-blue-700 mb-1">Workplace Behaviors:</h5>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
                        <li>Analyze problems systematically</li>
                        <li>Ensure quality and accuracy</li>
                        <li>Plan carefully and minimize risks</li>
                        <li>Follow established procedures</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Style Interaction Patterns */}
          <div className="mb-8 p-6 bg-emerald-50 rounded-lg border border-emerald-200">
            <h3 className="text-xl font-semibold text-emerald-800 mb-4">Working with Different Styles</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-emerald-700 mb-3">Your Communication Strategy:</h4>
                <div className="space-y-3 text-sm">
                  {results.social_style_type === 'Driver' && (
                    <div className="bg-red-50 p-3 rounded">
                      <p className="text-gray-700"><strong>When communicating with others:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>With Drivers: Be direct and focus on results</li>
                        <li>With Expressives: Listen more, acknowledge their ideas</li>
                        <li>With Amiables: Show empathy, ask about their concerns</li>
                        <li>With Analytics: Provide data, but respect their process</li>
                      </ul>
                    </div>
                  )}
                  {results.social_style_type === 'Expressive' && (
                    <div className="bg-yellow-50 p-3 rounded">
                      <p className="text-gray-700"><strong>When communicating with others:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>With Drivers: Be more concise and results-focused</li>
                        <li>With Expressives: Match their energy, share vision</li>
                        <li>With Amiables: Be supportive, avoid overwhelming them</li>
                        <li>With Analytics: Provide data, but make it engaging</li>
                      </ul>
                    </div>
                  )}
                  {results.social_style_type === 'Amiable' && (
                    <div className="bg-green-50 p-3 rounded">
                      <p className="text-gray-700"><strong>When communicating with others:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>With Drivers: Be more direct and assertive</li>
                        <li>With Expressives: Show enthusiasm, support their ideas</li>
                        <li>With Amiables: Build on common ground and trust</li>
                        <li>With Analytics: Provide clear, organized information</li>
                      </ul>
                    </div>
                  )}
                  {results.social_style_type === 'Analytical' && (
                    <div className="bg-blue-50 p-3 rounded">
                      <p className="text-gray-700"><strong>When communicating with others:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>With Drivers: Get to the point, focus on bottom line</li>
                        <li>With Expressives: Show some enthusiasm, be flexible</li>
                        <li>With Amiables: Consider feelings, build relationships</li>
                        <li>With Analytics: Share data, respect their thoroughness</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-emerald-700 mb-3">Adaptation Strategies:</h4>
                <div className="space-y-3 text-sm">
                  {results.social_style_type === 'Driver' && (
                    <div>
                      <p className="text-gray-700"><strong>To be more effective:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Practice active listening and patience</li>
                        <li>Consider emotional impact of decisions</li>
                        <li>Build relationships, not just results</li>
                        <li>Allow time for others to process</li>
                      </ul>
                    </div>
                  )}
                  {results.social_style_type === 'Expressive' && (
                    <div>
                      <p className="text-gray-700"><strong>To be more effective:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Develop better organization and follow-through</li>
                        <li>Balance optimism with realistic assessment</li>
                        <li>Practice active listening</li>
                        <li>Focus on details when needed</li>
                      </ul>
                    </div>
                  )}
                  {results.social_style_type === 'Amiable' && (
                    <div>
                      <p className="text-gray-700"><strong>To be more effective:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Practice assertiveness and saying "no"</li>
                        <li>Embrace constructive conflict</li>
                        <li>Take initiative and make decisions</li>
                        <li>Be more comfortable with change</li>
                      </ul>
                    </div>
                  )}
                  {results.social_style_type === 'Analytical' && (
                    <div>
                      <p className="text-gray-700"><strong>To be more effective:</strong></p>
                      <ul className="list-disc list-inside space-y-1 text-gray-600 ml-4">
                        <li>Balance analysis with timely decisions</li>
                        <li>Develop interpersonal skills</li>
                        <li>Be more flexible with procedures</li>
                        <li>Accept "good enough" when appropriate</li>
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            <Button
              onClick={() => navigate('/personality-assessments')}
              className="px-6 py-3"
            >
              Back to Assessments
            </Button>
            <Button
              onClick={() => navigate('/dashboard')}
              variant="outline"
              className="px-6 py-3"
            >
              Go to Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-center">
          <div className="text-lg text-gray-600">Assessment data not available</div>
        </div>
      </div>
    );
  }

  const currentQ = assessment.questions[currentQuestion];
  const hasAnswer = answers[currentQ?.id] !== undefined;
  const isLastQuestion = currentQuestion === assessment.questions.length - 1;
  const progress = ((currentQuestion + 1) / assessment.questions.length) * 100;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-center mb-2">
            🤝 {assessment.title}
          </h1>
          <p className="text-center text-gray-600 mb-4">{assessment.description}</p>

          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">
              Question {currentQuestion + 1} of {assessment.questions.length}
            </span>
            <span className="text-sm text-gray-500">
              Progress: {Math.round(progress)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-center mb-8">
              {currentQ.question_text}
            </h3>
            <div className="text-center text-sm text-gray-500 mb-6">
              Style: {currentQ.style}
            </div>
          </div>

          <div className="space-y-4 mb-8">
            {currentQ.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleAnswer(currentQ.id, option.value)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-colors ${
                  answers[currentQ.id] === option.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <span className="font-medium">{option.value}</span>
                <p className="text-gray-600 mt-1">{option.text}</p>
              </button>
            ))}
          </div>

          <div className="flex justify-between">
            <Button
              onClick={handlePrevious}
              disabled={currentQuestion === 0}
              variant="outline"
              className="px-6 py-3"
            >
              Previous
            </Button>

            {isLastQuestion ? (
              <Button
                onClick={handleSubmit}
                disabled={!hasAnswer || isSubmitting}
                className="px-6 py-3 bg-green-600 hover:bg-green-700"
              >
                {isSubmitting ? 'Submitting...' : 'Complete Assessment'}
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                disabled={!hasAnswer}
                className="px-6 py-3"
              >
                Next
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SocialStylesPage;
