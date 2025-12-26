import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '@/services/api';
import assessmentResultsService from '@/services/assessmentResultsService';

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

export default function MBTIAssessmentPage() {
  const [assessment, setAssessment] = useState<MBTIAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  useEffect(() => {
    // Prevent multiple loads once assessment is loaded
    if (assessment) return;

    loadMBTIAssessment();
  }, [assessmentId]); // Only depend on assessmentId

  const loadMBTIAssessment = async () => {
    try {
      console.log('🚀 Loading MBTI Assessment...');
      console.log('📍 Assessment ID:', assessmentId);
      setIsLoading(true);
      setError(null);

      // Clear any cached results to ensure fresh start
      setResults(null);
      setAnswers({});
      setCurrentQuestion(0);

      console.log('📡 Fetching MBTI questions from API...');
      // Load MBTI assessment from backend API
      const response = await apiClient.get('/assessment-questions/mbti');

      if (response.data && response.data.success) {
        const backendAssessment = response.data.assessment;

        // Transform backend data to frontend format
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

        console.log('✅ MBTI Assessment loaded successfully:', mbtiAssessment.title, `(${mbtiAssessment.questions.length} questions)`);
        setAssessment(mbtiAssessment);
        setIsLoading(false);
      } else {
        throw new Error('Failed to load assessment from backend');
      }

    } catch (error) {
      console.error('❌ Failed to load MBTI assessment from backend:', error);

      // Fallback to mock MBTI assessment if backend fails
      console.log('⚠️ Using fallback mock data...');
      const mockMBTI: MBTIAssessment = {
        id: assessmentId || 'mbti-default',
        title: 'Myers-Briggs Type Indicator (MBTI) Assessment',
        description: 'Discover your personality type based on the four MBTI dimensions',
        questions: [
          {
            id: 1,
            question_text: 'At parties, do you:',
            dimension: 'E-I',
            options: [
              { text: 'Talk to many people, including strangers', value: 'E' },
              { text: 'Talk to a few people you know well', value: 'I' }
            ]
          },
          {
            id: 2,
            question_text: 'Do you prefer to:',
            dimension: 'S-N',
            options: [
              { text: 'Focus on the real world and practical matters', value: 'S' },
              { text: 'Imagine the possibilities and think about abstract concepts', value: 'N' }
            ]
          },
          {
            id: 3,
            question_text: 'When making decisions, do you:',
            dimension: 'T-F',
            options: [
              { text: 'Rely on logic and objective analysis', value: 'T' },
              { text: 'Consider how it will affect people involved', value: 'F' }
            ]
          },
          {
            id: 4,
            question_text: 'Do you prefer to:',
            dimension: 'J-P',
            options: [
              { text: 'Plan things in advance and stick to the plan', value: 'J' },
              { text: 'Be spontaneous and adapt to new situations', value: 'P' }
            ]
          },
          {
            id: 5,
            question_text: 'At work, do you:',
            dimension: 'E-I',
            options: [
              { text: 'Enjoy working in teams and brainstorming with others', value: 'E' },
              { text: 'Prefer working independently and concentrating deeply', value: 'I' }
            ]
          },
          {
            id: 6,
            question_text: 'When learning something new, do you:',
            dimension: 'S-N',
            options: [
              { text: 'Prefer step-by-step instructions with concrete examples', value: 'S' },
              { text: 'Like to understand the overall concept first', value: 'N' }
            ]
          },
          {
            id: 7,
            question_text: 'When giving feedback, do you:',
            dimension: 'T-F',
            options: [
              { text: 'Focus on facts and logical improvements', value: 'T' },
              { text: 'Consider feelings and how to deliver it gently', value: 'F' }
            ]
          },
          {
            id: 8,
            question_text: 'For weekends, do you:',
            dimension: 'J-P',
            options: [
              { text: 'Plan activities and have a schedule', value: 'J' },
              { text: 'Leave options open and decide spontaneously', value: 'P' }
            ]
          }
        ]
      };

      console.log('✅ Fallback MBTI Assessment ready:', mockMBTI.title, `(${mockMBTI.questions.length} questions)`);
      setAssessment(mockMBTI);
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

    // Count answers for each dimension
    assessment?.questions.forEach(question => {
      const answer = answers[question.id];
      if (answer && dimensions[question.dimension]) {
        (dimensions[question.dimension] as any)[answer]++;
      }
    });

    // Determine type based on majority in each dimension
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

      // NEW: Submit using the comprehensive assessment results service
      const resultResponse = await assessmentResultsService.submitMBTIAssessment(
        assessment.id,
        answers,
        mbtiType
      );

      // Format the result for display
      const formattedResult = assessmentResultsService.formatMBTIResult(resultResponse.result);
      setResults(formattedResult);

    } catch (error) {
      console.error('Failed to submit assessment:', error);

      // Fallback: Try the old method for backward compatibility
      try {
        const response = await apiClient.post('/mbti-test-submit', {
          assessment_id: assessment.id,
          assessment_type: 'mbti',
          responses: answers,
          raw_type: calculateMBTIType(answers)
        });
        setResults(response.data);
      } catch (fallbackError) {
        console.error('Fallback submission also failed:', fallbackError);
        // Final fallback: client-side calculation only
        const mbtiType = calculateMBTIType(answers);
        setResults({
          type: mbtiType,
          confidence: 0.8,
          description: `Your MBTI type is ${mbtiType}`,
          submitted_at: new Date().toISOString()
        });
      }
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
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading MBTI Assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-4">
            {error}
          </div>
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
              {/* MBTI Educational Content */}
              <div className="mb-8 bg-blue-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Understanding Your MBTI Type: {results.type}</h3>
                <div className="space-y-4 text-gray-700">
                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">What Your Type Means:</h4>
                    <p className="text-sm leading-relaxed">
                      Your MBTI type reveals your natural preferences for how you direct and receive energy, process information, make decisions, and approach the outer world.
                      These preferences influence your communication style, work environment preferences, stress triggers, and natural strengths. Understanding your type helps you work with your preferences rather than against them.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Your Four Preference Pairs:</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className={`p-3 rounded ${results.dimensions?.['E'] > results.dimensions?.['I'] ? 'bg-blue-100 border-blue-300' : 'bg-gray-50'}`}>
                        <strong>Energy Direction: {results.dimensions?.['E'] > results.dimensions?.['I'] ? 'Extraversion (E)' : 'Introversion (I)'}</strong>
                        <p>{results.dimensions?.['E'] > results.dimensions?.I'] ?
                          'You gain energy from social interaction and external activities' :
                          'You gain energy from solitude and internal reflection'}</p>
                      </div>
                      <div className={`p-3 rounded ${results.dimensions?.['S'] > results.dimensions?.['N'] ? 'bg-green-100 border-green-300' : 'bg-gray-50'}`}>
                        <strong>Information Processing: {results.dimensions?.['S'] > results.dimensions?.['N'] ? 'Sensing (S)' : 'Intuition (N)'}</strong>
                        <p>{results.dimensions?.['S'] > results.dimensions?.N'] ?
                          'You focus on concrete facts and practical details' :
                          'You focus on patterns, possibilities, and future implications'}</p>
                      </div>
                      <div className={`p-3 rounded ${results.dimensions?.['T'] > results.dimensions?.['F'] ? 'bg-purple-100 border-purple-300' : 'bg-gray-50'}`}>
                        <strong>Decision Making: {results.dimensions?.['T'] > results.dimensions?.['F'] ? 'Thinking (T)' : 'Feeling (F)'}</strong>
                        <p>{results?.dimensions?.['T'] > results?.dimensions?.F'] ?
                          'You make decisions based on logical analysis and objective criteria' :
                          'You make decisions based on values and impact on people'}</p>
                      </div>
                      <div className={`p-3 rounded ${results?.dimensions?.['J'] > results?.['P'] ? 'bg-orange-100 border-orange-300' : 'bg-gray-50'}`}>
                        <strong>Lifestyle Approach: {results?.dimensions?.['J'] > results?.['P'] ? 'Judging (J)' : 'Perceiving (P)'}</strong>
                        <p>{results?.dimensions?.['J'] > results?.dimensions?.P'] ?
                          'You prefer structure, plans, and closure' :
                          'You prefer flexibility, spontaneity, and keeping options open'}</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Your Natural Strengths:</h4>
                    <ul className="text-sm space-y-2">
                      {results.type.includes('E') && <li>• Excellent at building networks and motivating others through social interaction</li>}
                      {results.type.includes('I') && <li>• Deep concentration and thoughtful analysis when working independently</li>}
                      {results.type.includes('S') && <li>• Practical problem-solving with attention to concrete details and realistic applications</li>}
                      {results.type.includes('N') && <li>• Creative thinking with ability to see patterns and future possibilities</li>}
                      {results.type.includes('T') && <li>• Objective analysis and logical decision-making with attention to accuracy</li>}
                      {results.type.includes('F') && <li>• Harmony-seeking with sensitivity to others' needs and emotional dynamics</li>}
                      {results.type.includes('J') && <li>• Organized planning with ability to structure environments and achieve goals efficiently</li>}
                      {results.type.includes('P') && <li>• Adaptability and spontaneity with openness to new information and experiences</li>}
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Potential Growth Areas:</h4>
                    <ul className="text-sm space-y-2">
                      {results.type.includes('E') && <li>• Develop quiet reflection time and working independently on focused tasks</li>}
                      {results.type.includes('I') && <li>• Practice networking and sharing your insights with others more regularly</li>}
                      {results.type.includes('S') && <li>• Explore abstract concepts and theoretical frameworks beyond concrete applications</li>}
                      {results.type.includes('N') && <li>• Focus on practical details and step-by-step implementation of your ideas</li>}
                      {results.type.includes('T') && <li>• Consider others' feelings and values when making group decisions</li>}
                      {results.type.includes('F') && <li>• Develop objective analysis skills and consider logical implications alongside emotional factors</li>}
                      {results.type.includes('J') && <li>• Practice flexibility and keep options open when plans change</li>}
                      {results.type.includes('P') && <li>• Develop organizational skills and create structured approaches to complex projects</li>}
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Work Environment Preferences:</h4>
                    <p className="text-sm leading-relaxed">
                      You're likely to thrive in environments that align with your natural preferences. Consider these factors when choosing roles, teams, or work arrangements:
                      <ul className="mt-2 space-y-1">
                        {results.type.includes('E') && <li>• Social interaction and collaborative projects</li>}
                        {results.type.includes('I') && <li>• Quiet, focused work with minimal interruptions</li>}
                        {results.type.includes('S') && <li>• Clear instructions and practical, tangible outcomes</li>}
                        {results.type.includes('N') && <li>• Innovation, strategic planning, and creative problem-solving</li>}
                        {results.type.includes('T') && <li>• Analytical tasks, data-driven decision making, and objective evaluation</li>}
                        {results.type.includes('F') && <li>• Harmonious teams, helping roles, and people-centered initiatives</li>}
                        {results.includes('STJ') && <li>• Structured environments with clear expectations and efficient systems</li>}
                        {results.includes('NFP') && <li>• Flexible environments with creative freedom and supportive relationships</li>}
                      </ul>
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Communication and Relationships:</h4>
                    <p className="text-sm leading-relaxed">
                      Understanding your type can improve your relationships by recognizing natural differences in communication styles:
                      <ul className="mt-2 space-y-1">
                        {results.type.includes('E') && <li>• You tend to think out loud and process through conversation</li>}
                        {results.type.includes('I') && <li>• You prefer to think before speaking and may need time to process your thoughts</li>}
                        {results.type.includes('S') && <li>• You communicate about concrete facts and practical experiences</li>}
                        {results.type.includes('N') && <li>• You communicate about concepts, patterns, and future possibilities</li>}
                        {results.type.includes('T') && <li>• You prioritize direct, factual communication</li>}
                        {result.type.includes('F') && <li>• You prioritize harmony and consider how others might feel</li>}
                      </ul>
                    </p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-blue-900 mb-2">Important MBTI Reminders:</h4>
                    <ul className="text-sm space-y-1 text-blue-800 bg-blue-50 p-4 rounded">
                      <li>• MBTI indicates preferences, not abilities - all types can develop all preferences</li>
                      <li>• Your type may change over time as you grow and have different life experiences</li>
                        • Results reflect your current state, not fixed identity</li>
                      <li>• Use MBTI as a tool for self-understanding, not for limiting your potential</li>
                      <li>• Every type brings valuable perspectives and strengths to teams and relationships</li>
                      <li>• The goal is self-awareness and growth, not stereotyping yourself or others</li>
                    </ul>
                  </div>
                </div>
              </div>

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
    return <div>No assessment data available</div>;
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
