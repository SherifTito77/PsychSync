/**
 * Mental Health Screening Form Component
 * Interactive form for PHQ-9, GAD-7, DASS-21 clinical assessments
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/common/Button';

interface ScreeningTool {
  id: string;
  name: string;
  description: string;
  questions: Question[];
  scoring: ScoringInfo;
}

interface Question {
  id: string;
  text: string;
  options: string[];
  type: 'likert' | 'multiple' | 'yesno';
  scoring?: number[]; // Optional scoring array for validation purposes
}

interface ScoringInfo {
  min: number;
  max: number;
  thresholds: {
    minimal: number;
    mild: number;
    moderate: number;
    severe: number;
  };
}

interface ScreeningResponse {
  question_id: string;
  answer: string | number;
  score: number;
}

interface ScreeningResult {
  tool_id: string;
  total_score: number;
  risk_level: 'minimal' | 'mild' | 'moderate' | 'severe';
  recommendations: string[];
  crisis_alert: boolean;
  next_recommended_action: string;
  timestamp: string;
}

// Helper function to calculate estimated completion time
const calculateMinutes = (tool: ScreeningTool): number => {
  const scoreRange = tool.scoring.max - tool.scoring.min;
  const averageTimePerQuestion = scoreRange / tool.questions.length;
  return Math.round(averageTimePerQuestion);
};

// Helper function to calculate minutes per question
const calculateMinutesPerQuestion = (tool: ScreeningTool): number => {
  const totalMinutes = calculateMinutes(tool);
  const minutesPerQuestion = totalMinutes / tool.questions.length;
  return Math.round(minutesPerQuestion * 10) / 10;
};

// Helper function for progress bar width calculation
const calculateProgressWidth = (current: number, total: number): number => {
  return ((current + 1) / total) * 100;
};

// Input validation functions to prevent NaN scores
const validateAnswerScore = (question: Question, answerIndex: number): number | null => {
  // Check if answer index is valid
  if (answerIndex < 0 || answerIndex >= question.options.length) {
    console.warn(`Invalid answer index ${answerIndex} for question ${question.id}`);
    return null;
  }

  // Check if scoring array exists and has the answer index
  if (!question.scoring || !Array.isArray(question.scoring)) {
    console.warn(`Missing scoring array for question ${question.id}`);
    return null;
  }

  if (answerIndex >= question.scoring.length) {
    console.warn(`Answer index ${answerIndex} out of bounds for scoring array of question ${question.id}`);
    return null;
  }

  const score = question.scoring[answerIndex];

  // Validate that score is a finite number and not a boolean
  // In JavaScript, typeof true === 'boolean', but typeof NaN === 'number'
  // We need to exclude boolean values explicitly
  if (
    typeof score !== 'number' ||
    !isFinite(score) ||
    // Additional check to ensure it's not a boolean (boolean values can be converted to numbers)
    score === 1 as any ||
    score === 0 as any ||
    // Explicit NaN check (isFinite already handles this, but keeping for clarity)
    Number.isNaN(score)
  ) {
    console.warn(`Invalid score ${score} for question ${question.id}, answer index ${answerIndex}`);
    return null;
  }

  return score;
};

const validateCompleteResponses = (toolQuestions: Question[], responses: ScreeningResponse[]): boolean => {
  // Check if all questions have been answered
  if (responses.length !== toolQuestions.length) {
    console.warn(`Incomplete responses: ${responses.length}/${toolQuestions.length} questions answered`);
    return false;
  }

  // Check if all responses have valid scores
  for (const response of responses) {
    // Enhanced score validation (same as validateAnswerScore but for existing scores)
    if (
      typeof response.score !== 'number' ||
      !isFinite(response.score) ||
      response.score === 1 as any ||
      response.score === 0 as any ||
      Number.isNaN(response.score)
    ) {
      console.warn(`Invalid score ${response.score} for response to question ${response.question_id}`);
      return false;
    }
  }

  return true;
};

const calculateSafeTotalScore = (responses: ScreeningResponse[]): { score: number; isValid: boolean; missingQuestions: string[] } => {
  const validScores: number[] = [];
  const missingQuestions: string[] = [];

  for (const response of responses) {
    // Enhanced validation to match other functions
    if (
      typeof response.score === 'number' &&
      isFinite(response.score) &&
      response.score !== 1 as any &&
      response.score !== 0 as any &&
      !Number.isNaN(response.score)
    ) {
      validScores.push(response.score);
    } else {
      missingQuestions.push(response.question_id);
    }
  }

  if (validScores.length === 0) {
    return { score: 0, isValid: false, missingQuestions };
  }

  // Use precise addition to avoid floating point precision issues
  const totalScore = validScores.reduce((sum, score) => sum + score, 0);
  const isValid = missingQuestions.length === 0;

  return { score: totalScore, isValid, missingQuestions };
};

const MentalHealthScreeningForm: React.FC = () => {
  const [selectedTool, setSelectedTool] = useState<string>('phq9');
  const [currentQuestion, setCurrentQuestion] = useState<number>(0);
  const [responses, setResponses] = useState<ScreeningResponse[]>([]);
  const [isStarted, setIsStarted] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [loading, setLoading] = useState(false);

  const screeningTools: ScreeningTool[] = [
    {
      id: 'phq9',
      name: 'PHQ-9',
      description: 'Patient Health Questionnaire - Depression Screening',
      questions: [
        {
          id: 'phq9_1',
          text: 'Over the last 2 weeks, how often have you been bothered by little interest or pleasure in doing things?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_2',
          text: 'Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_3',
          text: 'Over the last 2 weeks, how often have you been bothered by trouble falling or staying asleep, or sleeping too much?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_4',
          text: 'Over the last 2 weeks, how often have you been bothered by feeling tired or having little energy?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_5',
          text: 'Over the last 2 weeks, how often have you been bothered by poor appetite or overeating?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_6',
          text: 'Over the last 2 weeks, how often have you been bothered by feeling bad about yourself—or that you are a failure or have let yourself or your family down?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_7',
          text: 'Over the last 2 weeks, how often have you been bothered by trouble concentrating on things, such as reading the newspaper or watching television?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_8',
          text: 'Over the last 2 weeks, how often have you been bothered by moving or speaking so slowly that other people could have noticed? Or the opposite—being so fidgety or restless that you have been moving around a lot more than usual?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'phq9_9',
          text: 'Over the last 2 weeks, how often have you been bothered by thoughts that you would be better off dead or of hurting yourself in some way?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        }
      ],
      scoring: {
        min: 0,
        max: 27,
        thresholds: {
          minimal: 4,
          mild: 9,
          moderate: 14,
          severe: 19
        }
      }
    },
    {
      id: 'gad7',
      name: 'GAD-7',
      description: 'Generalized Anxiety Disorder Assessment',
      questions: [
        {
          id: 'gad7_1',
          text: 'Over the last 2 weeks, how often have you been bothered by feeling nervous, anxious, or on edge?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'gad7_2',
          text: 'Over the last 2 weeks, how often have you been bothered by not being able to stop or control worrying?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'gad7_3',
          text: 'Over the last 2 weeks, how often have you been bothered by worrying too much about different things?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'gad7_4',
          text: 'Over the last 2 weeks, how often have you been bothered by having trouble relaxing?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'gad7_5',
          text: 'Over the last 2 weeks, how often have you been bothered by being so restless that it is hard to sit still?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'gad7_6',
          text: 'Over the last 2 weeks, how often have you been bothered by becoming easily annoyed or irritable?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        },
        {
          id: 'gad7_7',
          text: 'Over the last 2 weeks, how often have you been bothered by feeling afraid, as if something awful might happen?',
          options: [
            'Not at all',
            'Several days',
            'More than half the days',
            'Nearly every day'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3]
        }
      ],
      scoring: {
        min: 0,
        max: 21,
        thresholds: {
          minimal: 4,
          mild: 9,
          moderate: 14,
          severe: 19
        }
      }
    },
    {
      id: 'stress',
      name: 'Perceived Stress Scale (PSS)',
      description: 'Perceived Stress Scale - Stress Assessment',
      questions: [
        {
          id: 'pss_1',
          text: 'In the last month, how often have you been upset because of something that happened unexpectedly?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3, 4]
        },
        {
          id: 'pss_2',
          text: 'In the last month, how often have you felt that you were unable to control the important things in your life?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3, 4]
        },
        {
          id: 'pss_3',
          text: 'In the last month, how often have you felt nervous and "stressed"?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3, 4]
        },
        {
          id: 'pss_4',
          text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [4, 3, 2, 1, 0] // Reverse scored
        },
        {
          id: 'pss_5',
          text: 'In the last month, how often have you felt that things were going your way?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [4, 3, 2, 1, 0] // Reverse scored
        },
        {
          id: 'pss_6',
          text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3, 4]
        },
        {
          id: 'pss_7',
          text: 'In the last month, how often have you been able to control irritations in your life?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [4, 3, 2, 1, 0] // Reverse scored
        },
        {
          id: 'pss_8',
          text: 'In the last month, how often have you felt that you were on top of things?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [4, 3, 2, 1, 0] // Reverse scored
        },
        {
          id: 'pss_9',
          text: 'In the last month, how often have you been angered because of things that were outside of your control?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3, 4]
        },
        {
          id: 'pss_10',
          text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?',
          options: [
            'Never',
            'Almost never',
            'Sometimes',
            'Fairly often',
            'Very often'
          ],
          type: 'likert',
          scoring: [0, 1, 2, 3, 4]
        }
      ],
      scoring: {
        min: 0,
        max: 40,
        thresholds: {
          minimal: 13,
          mild: 20,
          moderate: 27,
          severe: 34
        }
      }
    }
  ];

  const currentTool = screeningTools.find(tool => tool.id === selectedTool);

  const handleStartScreening = () => {
    setIsStarted(true);
    setCurrentQuestion(0);
    setResponses([]);
    setIsCompleted(false);
    setResult(null);
  };

  const handleAnswerSelect = (questionId: string, answerIndex: number) => {
    const question = currentTool?.questions.find(q => q.id === questionId);
    if (!question) return;

    // Validate the score before creating response
    const validatedScore = validateAnswerScore(question, answerIndex);
    if (validatedScore === null) {
      console.error(`Invalid score for question ${questionId} with answer index ${answerIndex}`);
      return;
    }

    const newResponse: ScreeningResponse = {
      question_id: questionId,
      answer: question.options[answerIndex],
      score: validatedScore
    };

    // Update or add response
    setResponses(prev => {
      const filtered = prev.filter(r => r.question_id !== questionId);
      return [...filtered, newResponse];
    });
  };

  const handleNext = () => {
    if (currentTool && currentQuestion < currentTool.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      handleSubmitScreening();
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmitScreening = async () => {
    if (!currentTool) return;

    // Validate that all required questions have been answered
    const isComplete = validateCompleteResponses(currentTool.questions, responses);
    if (!isComplete) {
      alert('Please answer all questions before submitting the screening.');
      return;
    }

    setLoading(true);
    try {
      // Calculate total score safely
      const { score: totalScore, isValid, missingQuestions } = calculateSafeTotalScore(responses);

      if (!isValid || isNaN(totalScore)) {
        alert(`There was an issue calculating your score. Please ensure all questions are answered properly. Missing questions: ${missingQuestions.join(', ')}`);
        return;
      }

      // Determine risk level based on thresholds
      const thresholds = currentTool.scoring.thresholds;
      let riskLevel: 'minimal' | 'mild' | 'moderate' | 'severe' = 'minimal';
      let recommendations: string[] = [];
      let crisisAlert = false;

      if (totalScore >= thresholds.severe) {
        riskLevel = 'severe';
        recommendations = [
          'Seek immediate professional help from a mental health provider',
          'Consider emergency services if having thoughts of self-harm',
          'Contact crisis hotlines for immediate support',
          'Inform trusted family members or friends about your situation'
        ];
        crisisAlert = true;
      } else if (totalScore >= thresholds.moderate) {
        riskLevel = 'moderate';
        recommendations = [
          'Schedule an appointment with a mental health professional',
          'Consider therapy or counseling options',
          'Practice stress reduction techniques',
          'Reach out to supportive friends or family members',
          'Monitor symptoms closely and seek help if they worsen'
        ];
      } else if (totalScore >= thresholds.mild) {
        riskLevel = 'mild';
        recommendations = [
          'Consider talking to a healthcare provider about your symptoms',
          'Practice self-care strategies like exercise and mindfulness',
          'Maintain regular sleep schedule',
          'Limit alcohol and caffeine',
          'Connect with supportive friends and family'
        ];
      } else {
        recommendations = [
          'Continue monitoring your mental health',
          'Practice regular self-care activities',
          'Maintain healthy lifestyle habits',
          'Stay connected with others'
        ];
      }

      // Add tool-specific recommendations
      if (selectedTool === 'phq9') {
        recommendations.push('Consider discussing results with your primary care physician');
      } else if (selectedTool === 'gad7') {
        recommendations.push('Explore relaxation techniques like deep breathing or meditation');
        recommendations.push('Consider regular physical exercise to reduce anxiety');
      } else if (selectedTool === 'stress') {
        recommendations.push('Practice time management and prioritize tasks');
        recommendations.push('Consider mindfulness-based stress reduction techniques');
        recommendations.push('Ensure adequate sleep and maintain a regular schedule');
      }

      const screeningResult: ScreeningResult = {
        tool_id: selectedTool,
        total_score: totalScore,
        risk_level: riskLevel,
        recommendations,
        crisis_alert: crisisAlert,
        next_recommended_action: riskLevel === 'severe' ? 'Seek immediate professional help' : 'Monitor and self-care',
        timestamp: new Date().toISOString()
      };

      setResult(screeningResult);
      setIsCompleted(true);

      // Log the screening result for monitoring (in production, this would go to a secure database)
      console.log('Screening completed:', screeningResult);

    } catch (error) {
      console.error('Error submitting screening:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = () => {
    handleStartScreening();
  };

  const getScoreColor = (score: number, maxScore: number) => {
    const percentage = (score / maxScore) * 100;
    if (percentage < 25) return 'text-green-600';
    if (percentage < 50) return 'text-yellow-600';
    if (percentage < 75) return 'text-orange-600';
    return 'text-red-600';
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'minimal': return 'text-green-600 bg-green-50';
      case 'mild': return 'text-yellow-600 bg-yellow-50';
      case 'moderate': return 'text-orange-600 bg-orange-50';
      case 'severe': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const currentQuestionData = currentTool?.questions[currentQuestion];

  if (!currentTool) {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500 mb-4">Loading screening tools...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {currentTool.name} Screening
        </h1>
        <p className="text-gray-600">{currentTool.description}</p>
        <div className="text-sm text-blue-600 mt-2">
          Validated clinical tool • {currentTool.questions.length} questions • {calculateMinutes(currentTool)} minutes
        </div>
      </div>

      {/* Progress Bar */}
      {isStarted && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">Progress</span>
            <span className="text-sm text-gray-600">
              Question {currentQuestion + 1} of {currentTool.questions.length}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${calculateProgressWidth(currentQuestion, currentTool.questions.length)}%` }}
            />
          </div>
        </div>
      )}

      {!isStarted && (
        /* Start Screen */
        <Card className="mb-6">
          <CardContent className="p-8 text-center">
            <div className="text-6xl mb-4">🩺</div>
            <h2 className="text-xl font-semibold mb-4">Ready to Start {currentTool.name}?</h2>
            <p className="text-gray-600 mb-6">
              This evidence-based screening tool will help assess your mental health.
              Your responses are confidential and used only to provide personalized recommendations.
            </p>
            <div className="space-y-3 text-left bg-yellow-50 p-4 rounded">
              <h3 className="font-medium text-yellow-800 mb-2">Important Notice:</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• This screening tool is for informational purposes only</li>
                <li>• It is not a substitute for professional medical diagnosis</li>
                <li>• If you're in crisis, please call 988 or 911 immediately</li>
                <li>• Consider consulting a healthcare provider for any concerns</li>
              </ul>
            </div>
            <Button onClick={handleStartScreening} className="w-full">
              Start Screening
            </Button>
          </CardContent>
        </Card>
      )}

      {isStarted && !isCompleted && (
        /* Question Screen */
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>
              Question {currentQuestion + 1} of {currentTool.questions.length}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-4">
                {currentQuestionData?.text}
              </h3>

              {currentQuestionData?.type === 'likert' && (
                <div className="space-y-2">
                  {currentQuestionData.options.map((option, index) => {
                    const isSelected = responses.find(r => r.question_id === currentQuestionData?.id && r.answer === option);
                    return (
                      <button
                        key={index}
                        onClick={() => handleAnswerSelect(currentQuestionData.id, index)}
                        className={`w-full text-left p-4 border-2 rounded-lg transition-colors ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center">
                          <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                            isSelected
                              ? 'bg-blue-500 border-blue-500'
                              : 'border-gray-300'
                          }`} />
                          <span>{option}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentQuestion === 0}
                className="flex items-center"
              >
                ← Previous
              </Button>
              <Button
                onClick={handleNext}
                className="flex items-center"
              >
                {currentQuestion === currentTool.questions.length - 1 ? 'Submit' : 'Next'} →
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isCompleted && result && (
        /* Results Screen */
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className={`flex items-center space-x-3 ${getRiskLevelColor(result.risk_level)}`}>
              <span className="text-2xl">
                {result.risk_level === 'severe' ? '🚨' :
                 result.risk_level === 'moderate' ? '⚠️' :
                 result.risk_level === 'mild' ? '📊' : '✅'}
              </span>
              <span>Screening Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="text-center mb-6">
              <div className={`text-4xl font-bold ${getScoreColor(result.total_score, currentTool.scoring.max)}`}>
                {result.total_score}
              </div>
              <div className="text-lg text-gray-600 capitalize">
                {result.risk_level} Risk Level
              </div>
              <div className="text-sm text-gray-500">
                Score: {result.total_score} / {currentTool.scoring.max}
              </div>
            </div>

            {result.crisis_alert && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="text-lg font-semibold text-red-800 mb-2">⚠️ Crisis Alert</h3>
                <p className="text-red-700">
                  Your screening results suggest immediate professional support is recommended.
                  Please contact emergency services if you're having thoughts of self-harm.
                </p>
                <div className="mt-4 space-x-2">
                  <Button className="bg-red-600 text-white">
                    Call 988
                  </Button>
                  <Button variant="outline" className="text-red-600 border-red-300">
                    Text HOME to 741741
                  </Button>
                </div>
              </div>
            )}

            <div className="mb-6">
              <h3 className="font-semibold mb-3">Recommendations:</h3>
              <ul className="space-y-2">
                {result.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-green-500 mr-2">•</span>
                    <span className="text-gray-700">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mb-6">
              <h3 className="font-semibold mb-2">Next Steps:</h3>
              <p className="text-gray-700">{result.next_recommended_action}</p>
            </div>

            <div className="flex space-x-4">
              <Button onClick={() => window.open('/mental-health-wellness', '_self')}>
                Return to Wellness Center
              </Button>
              <Button onClick={handleRestart}>
                Take Another Screening
              </Button>
              <Button variant="outline" onClick={() => console.log('Save results')}>
                Save Results
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading && (
        <div className="text-center py-8">
          <div className="text-2xl text-gray-500">Processing your results...</div>
        </div>
      )}
    </div>
  );
};

export default MentalHealthScreeningForm;
