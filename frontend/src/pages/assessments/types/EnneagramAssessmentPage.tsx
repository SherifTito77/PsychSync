import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../../components/common/Button';
import apiClient from '../../../services/api';

interface EnneagramQuestion {
  id: number;
  question_text: string;
  type: string;
  options: Array<{
    text: string;
    value: string;
  }>;
}

interface EnneagramAssessment {
  id: string;
  title: string;
  description: string;
  questions: EnneagramQuestion[];
}

interface EnneagramResult {
  enneagram_type: string;
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
  center_grouping: {
    head_center: number;
    heart_center: number;
    gut_center: number;
  };
  responses_count: number;
  submitted_at: string;
}

const EnneagramAssessmentPage: React.FC = () => {
  const [assessment, setAssessment] = useState<EnneagramAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<EnneagramResult | null>(null);
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

      const response = await apiClient.get('/assessment-questions/enneagram');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;
        const enneagramAssessment: EnneagramAssessment = {
          id: backendAssessment.id,
          title: backendAssessment.title,
          description: backendAssessment.description,
          questions: backendAssessment.questions.map((q: any) => ({
            id: q.id,
            question_text: q.question_text,
            type: q.type,
            options: q.options.map((opt: any) => ({
              text: opt.text,
              value: opt.value
            }))
          }))
        };
        setAssessment(enneagramAssessment);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('❌ Failed to load Enneagram assessment:', error);
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
      const response = await apiClient.post('/enneagram-test-submit', {
        assessment_type: 'enneagram',
        responses: answers,
        raw_type: 'Enneagram'
      });

      if (response.data && response.data.success) {
        setResults(response.data.result);
        console.log('✅ Enneagram assessment submitted successfully');
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
          <p className="text-gray-600">Loading Enneagram Assessment...</p>
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
              <h2 className="text-3xl font-bold text-gray-800 mb-2">Your Enneagram Type</h2>
              <div className="inline-block px-6 py-3 bg-purple-100 text-purple-800 rounded-full text-lg font-semibold">
                {results.enneagram_type}: {results.type_info.title}
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-700 mb-4">About Your Type</h3>
              <p className="text-gray-600 mb-6">{results.type_info.description}</p>
            </div>

            {/* Enneagram Educational Content */}
            <div className="mb-8 p-6 bg-purple-50 rounded-lg border border-purple-200">
              <h3 className="text-xl font-semibold text-purple-800 mb-4">Understanding Your Enneagram Results</h3>
              <p className="text-gray-700 mb-4">
                The Enneagram is a powerful personality system that describes nine distinct personality types and their
                patterns of thinking, feeling, and behaving. Your type represents your core motivation and worldview,
                shaped by both nature and nurture throughout your life.
              </p>

              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-purple-800 mb-2">The Nine Enneagram Types:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 1 - The Perfectionist:</strong> Rational, idealistic, principled
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 2 - The Helper:</strong> Caring, generous, people-pleasing
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 3 - The Achiever:</strong> Success-oriented, practical, image-conscious
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 4 - The Individualist:</strong> Sensitive, expressive, dramatic
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 5 - The Investigator:</strong> Perceptive, innovative, secretive
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 6 - The Loyalist:</strong> Committed, security-oriented, anxious
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 7 - The Enthusiast:</strong> Busy, fun-loving, scattered
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 8 - The Challenger:</strong> Powerful, decisive, confrontational
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <strong className="text-purple-700">Type 9 - The Peacemaker:</strong> Easygoing, self-effacing, complacent
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-purple-800 mb-2">The Three Intelligence Centers:</h4>
                  <p className="text-gray-700 mb-3">
                    Your center grouping shows which intelligence center you primarily use:
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-blue-800 mb-2">Head Center (Types 5,6,7)</h5>
                      <p className="text-gray-700 text-sm">
                        Mental intelligence: thinking, analyzing, planning, and imagining. You lead with your mind
                        and may overthink or disconnect from emotions.
                      </p>
                    </div>
                    <div className="bg-green-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-green-800 mb-2">Heart Center (Types 2,3,4)</h5>
                      <p className="text-gray-700 text-sm">
                        Emotional intelligence: feeling, relating, and connecting with others. You lead with your heart
                        and may be highly attuned to others' emotions.
                      </p>
                    </div>
                    <div className="bg-red-100 p-4 rounded-lg">
                      <h5 className="font-semibold text-red-800 mb-2">Gut Center (Types 8,9,1)</h5>
                      <p className="text-gray-700 text-sm">
                        Instinctual intelligence: doing, acting, and responding from your gut. You lead with instinct
                        and may be action-oriented or struggle with anger.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Type-Specific Educational Content */}
            <div className="mb-8 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
              <h3 className="text-xl font-semibold text-indigo-800 mb-4">Your Enneagram Type {results.enneagram_type} Deep Dive</h3>

              {/* Core Fear and Desire */}
              <div className="mb-6">
                <h4 className="font-semibold text-indigo-700 mb-2">Core Motivations:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-red-100 p-4 rounded-lg">
                    <h5 className="font-medium text-red-800 mb-1">Core Fear:</h5>
                    <p className="text-gray-700 text-sm">
                      {results.enneagram_type === '1' && 'Being corrupt, evil, defective, or making mistakes'}
                      {results.enneagram_type === '2' && 'Being unloved or unwanted for being worthless'}
                      {results.enneagram_type === '3' && 'Being worthless, a failure, or fundamentally incapable'}
                      {results.enneagram_type === '4' && 'Having no identity or personal significance'}
                      {results.enneagram_type === '5' && 'Being useless, helpless, or incapable'}
                      {results.enneagram_type === '6' && 'Being without support, guidance, or security'}
                      {results.enneagram_type === '7' && 'Being trapped in pain and deprivation'}
                      {results.enneagram_type === '8' && 'Being harmed or controlled by others'}
                      {results.enneagram_type === '9' && 'Loss, separation, or fragmentation'}
                    </p>
                  </div>
                  <div className="bg-green-100 p-4 rounded-lg">
                    <h5 className="font-medium text-green-800 mb-1">Core Desire:</h5>
                    <p className="text-gray-700 text-sm">
                      {results.enneagram_type === '1' && 'To have integrity, to be good, to have balance, to be certain'}
                      {results.enneagram_type === '2' && 'To feel loved and wanted'}
                      {results.enneagram_type === '3' && 'To have value, worth, and respect'}
                      {results.enneagram_type === '4' && 'To find themselves and their significance, to create identity'}
                      {results.enneagram_type === '5' && 'To be capable and competent'}
                      {results.enneagram_type === '6' && 'To have security, support, and guidance'}
                      {results.enneagram_type === '7' && 'To be satisfied and content, to have their needs fulfilled'}
                      {results.enneagram_type === '8' && 'To protect themselves and control their own life'}
                      {results.enneagram_type === '9' && 'To have stability, peace of mind, and inner wholeness'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Wings and Paths */}
              <div className="mb-6">
                <h4 className="font-semibold text-indigo-700 mb-2">Growth and Stress Paths:</h4>
                <p className="text-gray-700 mb-3">
                  Each type has integrated (growth) and disintegrated (stress) paths that show how you change under different conditions:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-emerald-100 p-4 rounded-lg">
                    <h5 className="font-medium text-emerald-800 mb-1">Integration (Growth) Path:</h5>
                    <p className="text-gray-700 text-sm">
                      {results.enneagram_type === '1' && 'Move toward Type 7: Become more spontaneous, joyful, and relaxed'}
                      {results.enneagram_type === '2' && 'Move toward Type 4: Develop self-awareness and emotional authenticity'}
                      {results.enneagram_type === '3' && 'Move toward Type 6: Learn cooperation and commitment to others'}
                      {results.enneagram_type === '4' && 'Move toward Type 1: Develop practicality and objective thinking'}
                      {results.enneagram_type === '5' && 'Move toward Type 8: Become more confident, decisive, and engaged with world'}
                      {results.enneagram_type === '6' && 'Move toward Type 9: Develop inner peace and trust in yourself'}
                      {results.enneagram_type === '7' && 'Move toward Type 5: Develop depth, focus, and appreciation for silence'}
                      {results.enneagram_type === '8' && 'Move toward Type 2: Develop vulnerability, compassion, and gentleness'}
                      {results.enneagram_type === '9' && 'Move toward Type 3: Develop ambition, energy, and self-assertion'}
                    </p>
                  </div>
                  <div className="bg-orange-100 p-4 rounded-lg">
                    <h5 className="font-medium text-orange-800 mb-1">Disintegration (Stress) Path:</h5>
                    <p className="text-gray-700 text-sm">
                      {results.enneagram_type === '1' && 'Move toward Type 4: Become moody, irrational, and self-absorbed'}
                      {results.enneagram_type === '2' && 'Move toward Type 8: Become aggressive, dominating, and controlling'}
                      {results.enneagram_type === '3' && 'Move toward Type 9: Become disengaged, apathetic, and stagnant'}
                      {results.enneagram_type === '4' && 'Move toward Type 2: Become dependent, manipulative, and demanding'}
                      {results.enneagram_type === '5' && 'Move toward Type 7: Become scattered, hyperactive, and impulsive'}
                      {results.enneagram_type === '6' && 'Move toward Type 3: Become competitive, arrogant, and image-conscious'}
                      {results.enneagram_type === '7' && 'Move toward Type 1: Become critical, perfectionistic, and rigid'}
                      {results.enneagram_type === '8' && 'Move toward Type 5: Become withdrawn, secretive, and fearful'}
                      {results.enneagram_type === '9' && 'Move toward Type 6: Become anxious, indecisive, and suspicious'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Practical Applications */}
              <div className="mb-6">
                <h4 className="font-semibold text-indigo-700 mb-2">Practical Applications:</h4>
                <div className="bg-white p-4 rounded-lg">
                  <ul className="list-disc list-inside space-y-2 text-gray-700 text-sm">
                    <li><strong>Self-Awareness:</strong> Use your Enneagram knowledge to recognize your automatic patterns and reactions</li>
                    <li><strong>Personal Growth:</strong> Work on integrating positive qualities from your growth path</li>
                    <li><strong>Relationships:</strong> Understand how others' types differ from yours and improve communication</li>
                    <li><strong>Stress Management:</strong> Recognize your stress patterns and develop healthy coping mechanisms</li>
                    <li><strong>Career Development:</strong> Choose roles that align with your natural motivations and gifts</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-700 mb-4 text-green-600">Strengths</h3>
                <ul className="space-y-2">
                  {results.type_info.strengths.map((strength, index) => (
                    <li key={index} className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-700 mb-4 text-orange-600">Challenges</h3>
                <ul className="space-y-2">
                  {results.type_info.challenges.map((challenge, index) => (
                    <li key={index} className="flex items-center">
                      <span className="text-orange-500 mr-2">!</span>
                      {challenge}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mb-8 bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-3 text-blue-600">Growth Path</h3>
              <p className="text-gray-700">{results.type_info.growth_path}</p>
            </div>

            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-700 mb-4">Center Grouping</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {results.center_grouping.head_center.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Head Center</div>
                  <div className="text-xs text-gray-500">(Types 5,6,7)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {results.center_grouping.heart_center.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Heart Center</div>
                  <div className="text-xs text-gray-500">(Types 2,3,4)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {results.center_grouping.gut_center.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Gut Center</div>
                  <div className="text-xs text-gray-500">(Types 8,9,1)</div>
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
                className="bg-green-600 hover:bg-green-700"
              >
                {isSubmitting ? 'Submitting...' : 'Get Your Results'}
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

export default EnneagramAssessmentPage;
