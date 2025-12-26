import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface DASS21Question {
  id: number;
  text: string;
  category: 'depression' | 'anxiety' | 'stress';
}

const DASS21Assessment: React.FC = () => {
  const navigate = useNavigate();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<number, number>>({});

  // Standard DASS-21 questions with proper categories
  const dass21BaseQuestions: DASS21Question[] = [
    // Depression subscale (7 questions)
    { id: 3, text: "I couldn't seem to experience any positive feeling at all", category: 'depression' },
    { id: 5, text: "I found it difficult to work up the initiative to do things", category: 'depression' },
    { id: 10, text: "I felt that I had nothing to look forward to", category: 'depression' },
    { id: 13, text: "I felt sad and down", category: 'depression' },
    { id: 16, text: "I felt that I had lost interest in just about everything", category: 'depression' },
    { id: 17, text: "I felt that I wasn't worth much as a person", category: 'depression' },
    { id: 21, text: "I felt that life wasn't worthwhile", category: 'depression' },

    // Anxiety subscale (7 questions)
    { id: 1, text: "I found it hard to wind down", category: 'anxiety' },
    { id: 4, text: "I was aware of dryness of my mouth", category: 'anxiety' },
    { id: 7, text: "I experienced breathing difficulty (eg, unusually rapid breathing, breathlessness in the absence of physical exertion)", category: 'anxiety' },
    { id: 9, text: "I was worried about situations in which I might panic and make a fool of myself", category: 'anxiety' },
    { id: 15, text: "I felt I was close to panic", category: 'anxiety' },
    { id: 19, text: "I perspired noticeably (eg, hands sweating) in the absence of high temperatures or physical exertion", category: 'anxiety' },
    { id: 20, text: "I felt scared without any good reason", category: 'anxiety' },

    // Stress subscale (7 questions)
    { id: 2, text: "I tended to over-react to situations", category: 'stress' },
    { id: 6, text: "I found it difficult to relax", category: 'stress' },
    { id: 8, text: "I felt that I was using a lot of nervous energy", category: 'stress' },
    { id: 11, text: "I felt that I was rather touchy", category: 'stress' },
    { id: 12, text: "I found it hard to calm down after something upset me", category: 'stress' },
    { id: 14, text: "I was intolerant of anything that kept me from getting on with what I was doing", category: 'stress' },
    { id: 18, text: "I felt that I was rather touchy", category: 'stress' }
  ];

  // Add state for randomized questions
  const [randomizedQuestions, setRandomizedQuestions] = useState<DASS21Question[]>([]);

  // Shuffle and randomize questions on component mount
  useEffect(() => {
    const shuffleArray = (array: DASS21Question[]) => {
      const newArray = [...array];
      for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
      }
      return newArray;
    };

    // Shuffle questions while maintaining category balance
    const depressionQuestions = dass21BaseQuestions.filter(q => q.category === 'depression');
    const anxietyQuestions = dass21BaseQuestions.filter(q => q.category === 'anxiety');
    const stressQuestions = dass21BaseQuestions.filter(q => q.category === 'stress');

    // Shuffle within each category to maintain balance
    const shuffledDepression = shuffleArray(depressionQuestions);
    const shuffledAnxiety = shuffleArray(anxietyQuestions);
    const shuffledStress = shuffleArray(stressQuestions);

    // Interleave categories to avoid clustering
    const randomized: DASS21Question[] = [];
    for (let i = 0; i < 7; i++) {
      randomized.push(shuffledDepression[i]);
      randomized.push(shuffledAnxiety[i]);
      randomized.push(shuffledStress[i]);
    }

    // Final overall shuffle to randomize category order while maintaining balance
    setRandomizedQuestions(shuffleArray(randomized));
  }, []);

  const responseOptions = [
    { value: 0, text: "Did not apply to me at all" },
    { value: 1, text: "Applied to me to some degree, or some of the time" },
    { value: 2, text: "Applied to me to a considerable degree, or a good part of the time" },
    { value: 3, text: "Applied to me very much, or most of the time" },
  ];

  const handleResponse = (value: number) => {
    // Use the original question ID from randomized questions for scoring
    const questionId = randomizedQuestions[currentQuestion]?.id;
    if (questionId) {
      setResponses({ ...responses, [questionId]: value });
    }

    if (currentQuestion < randomizedQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Last question answered - directly submit assessment
      calculateAndShowResults();
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const validateScore = (score: any, questionId: number, category: string): number => {
    if (
      score === undefined ||
      score === null ||
      typeof score !== 'number' ||
      !isFinite(score) ||
      score === true ||
      score === false ||
      Number.isNaN(score)
    ) {
      console.warn(`Invalid DASS-21 score ${score} for question ${questionId} in ${category} category`);
      return 0;
    }
    return score;
  };

  const getSeverityLevel = (totalScore: number): string => {
    if (totalScore <= 21) return 'normal';
    if (totalScore <= 42) return 'mild';
    if (totalScore <= 63) return 'moderate';
    if (totalScore <= 84) return 'severe';
    return 'extremely severe';
  };

  const calculateAndShowResults = () => {
    try {
      // Calculate scores for each subscale with NaN protection
      const depressionIds = [1, 6, 8, 11, 12, 14, 17];
      const anxietyIds = [2, 4, 7, 9, 15, 19, 20];
      const stressIds = [3, 5, 10, 13, 16, 18, 21];

      const depressionScore = depressionIds.reduce((sum, id) => {
        const score = validateScore(responses[id], id, 'depression');
        return sum + score;
      }, 0) * 2;

      const anxietyScore = anxietyIds.reduce((sum, id) => {
        const score = validateScore(responses[id], id, 'anxiety');
        return sum + score;
      }, 0) * 2;

      const stressScore = stressIds.reduce((sum, id) => {
        const score = validateScore(responses[id], id, 'stress');
        return sum + score;
      }, 0) * 2;

      // Final validation of calculated scores
      const results = {
        depression: validateScore(depressionScore, 0, 'depression total'),
        anxiety: validateScore(anxietyScore, 0, 'anxiety total'),
        stress: validateScore(stressScore, 0, 'stress total'),
        totalScore: validateScore(depressionScore + anxietyScore + stressScore, 0, 'total')
      };

      // Additional validation - ensure all scores are reasonable
      if (results.totalScore > 126) { // Maximum possible score for DASS-21
        console.warn('DASS-21 total score exceeds maximum possible value', results);
        results.totalScore = 126;
      }

      navigate('/clinical/assessment/dass21/complete', { state: {
        assessmentType: 'dass21',
        result: {
          score: results.totalScore,
          severity_level: getSeverityLevel(results.totalScore),
          depression: results.depression,
          anxiety: results.anxiety,
          stress: results.stress
        }
      } });
    } catch (error) {
      console.error('Error calculating DASS-21 results:', error);
      navigate('/clinical/assessments');
    }
  };

  const question = randomizedQuestions[currentQuestion];

  // Show loading state while questions are being randomized
  if (randomizedQuestions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 flex items-center justify-center">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Preparing assessment...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            DASS-21 Assessment
          </h1>
          <div className="flex items-center justify-between mb-4">
            <p className="text-lg text-gray-600">
              Depression, Anxiety, and Stress Scales
            </p>
            <div className="text-sm text-gray-500">
              Question {currentQuestion + 1} of {randomizedQuestions.length}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / randomizedQuestions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm mr-3">
                {question.category.toUpperCase()}
              </span>
              Question {currentQuestion + 1}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg text-gray-800 mb-8 leading-relaxed">
              {question.text}
            </p>

            {/* Response Options */}
            <div className="space-y-3">
              {responseOptions.map((option) => (
                <Button
                  key={option.value}
                  variant="outline"
                  className="w-full text-left justify-start h-auto p-4 whitespace-normal"
                  onClick={() => handleResponse(option.value)}
                >
                  <div>
                    <span className="font-medium">{option.value}.</span> {option.text}
                  </div>
                </Button>
              ))}
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mt-8">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentQuestion === 0}
              >
                Previous
              </Button>

              <div className="text-center flex-1">
                <p className="text-sm text-gray-500">
                  Select the response that best describes how much the statement applied to you over the past week.
                </p>
                {currentQuestion === randomizedQuestions.length - 1 && (
                  <p className="text-sm font-semibold text-blue-600 mt-1">
                    🎯 This is the final question - selecting an answer will submit your assessment
                  </p>
                )}
              </div>

              {currentQuestion < randomizedQuestions.length - 1 && (
                <Button
                  variant="outline"
                  onClick={() => navigate('/clinical/assessments')}
                >
                  Exit Assessment
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">💡 About DASS-21</h3>
              <p className="text-sm text-gray-600">
                A 21-item questionnaire measuring symptoms of depression, anxiety, and stress.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">📊 Reliability</h3>
              <p className="text-sm text-gray-600">
                Good reliability (α = 0.84-0.91) across all three subscales.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">⏱️ Time</h3>
              <p className="text-sm text-gray-600">
                Takes approximately 5-10 minutes to complete.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Emergency Alert */}
        <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Need immediate help?</strong> If you're experiencing severe symptoms or thoughts of harm, please contact emergency services or a crisis hotline immediately.
              </p>
              <div className="mt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open('tel:988')}
                  className="text-yellow-700 border-yellow-300 hover:bg-yellow-100"
                >
                  Call 988 (Crisis Line)
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DASS21Assessment;