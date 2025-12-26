import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface AUDITQuestion {
  id: number;
  text: string;
  scoringNotes?: string;
}

const AUDITAssessment: React.FC = () => {
  const navigate = useNavigate();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [responses, setResponses] = useState<Record<number, number>>({});

  const auditQuestions: AUDITQuestion[] = [
    {
      id: 1,
      text: "How often do you have a drink containing alcohol?",
    },
    {
      id: 2,
      text: "How many drinks containing alcohol do you have on a typical day when you are drinking?",
      scoringNotes: "1 drink = 1 can/bottle (330ml) beer, 1 glass (150ml) wine, 1 shot (40ml) spirits"
    },
    {
      id: 3,
      text: "How often do you have six or more drinks on one occasion?",
    },
    {
      id: 4,
      text: "During the past year, how often have you found that you were not able to stop drinking once you had started?",
    },
    {
      id: 5,
      text: "During the past year, how often have you failed to do what was normally expected from you because of drinking?",
    },
    {
      id: 6,
      text: "During the past year, how often have you needed a first drink in the morning to get yourself going after a heavy drinking session?",
    },
    {
      id: 7,
      text: "During the past year, how often have you had a feeling of guilt or remorse after drinking?",
    },
    {
      id: 8,
      text: "During the past year, have you been unable to remember what happened the night before because you had been drinking?",
    },
    {
      id: 9,
      text: "Have you or someone else been injured as a result of your drinking?",
    },
    {
      id: 10,
      text: "Has a relative or friend or a doctor or another health worker been concerned about your drinking or suggested you cut down?",
    },
  ];

  const getResponseOptions = (questionId: number) => {
    switch (questionId) {
      case 1: // How often
        return [
          { value: 0, text: "Never" },
          { value: 1, text: "Monthly or less" },
          { value: 2, text: "2 to 4 times a month" },
          { value: 3, text: "2 to 3 times a week" },
          { value: 4, text: "4 or more times a week" },
        ];
      case 2: // How many drinks
        return [
          { value: 0, text: "1 or 2" },
          { value: 1, text: "3 or 4" },
          { value: 2, text: "5 or 6" },
          { value: 3, text: "7, 8, or 9" },
          { value: 4, text: "10 or more" },
        ];
      case 3: // How often 6+ drinks
        return [
          { value: 0, text: "Never" },
          { value: 1, text: "Less than monthly" },
          { value: 2, text: "Monthly" },
          { value: 3, text: "Weekly" },
          { value: 4, text: "Daily or almost daily" },
        ];
      case 4:
      case 5:
      case 6:
      case 7: // Past year frequency
        return [
          { value: 0, text: "Never" },
          { value: 1, text: "Less than monthly" },
          { value: 2, text: "Monthly" },
          { value: 3, text: "Weekly" },
          { value: 4, text: "Daily or almost daily" },
        ];
      case 8: // Memory loss
        return [
          { value: 0, text: "No" },
          { value: 2, text: "Yes, but not in the past year" },
          { value: 3, text: "Yes, during the past year" },
        ];
      case 9: // Injury
        return [
          { value: 0, text: "No" },
          { value: 2, text: "Yes, but not in the past year" },
          { value: 4, text: "Yes, during the past year" },
        ];
      case 10: // Concern expressed
        return [
          { value: 0, text: "No" },
          { value: 2, text: "Yes, but not in the past year" },
          { value: 3, text: "Yes, during the past year" },
        ];
      default:
        return [];
    }
  };

  const handleResponse = (value: number) => {
    setResponses({ ...responses, [currentQuestion + 1]: value });

    if (currentQuestion < auditQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Calculate scores and show results
      calculateAndShowResults();
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const getAUDITSeverityLevel = (finalScore: number): string => {
    if (finalScore <= 7) return 'Minimal';
    if (finalScore <= 15) return 'Mild';
    if (finalScore <= 19) return 'Moderate';
    return 'Severe';
  };


  const validateScore = (score: any, questionId: number): number => {
    if (
      typeof score !== 'number' ||
      !isFinite(score) ||
      score === true ||
      score === false ||
      Number.isNaN(score)
    ) {
      console.warn(`Invalid AUDIT score ${score} for question ${questionId}`);
      return 0;
    }
    return score;
  };

  const calculateAndShowResults = () => {
    try {
      const totalScore = Object.entries(responses).reduce((sum, [qid, val]) => {
        const score = validateScore(val, parseInt(qid));
        return sum + score;
      }, 0);

      // Final validation of total score
      const validatedScore = validateScore(totalScore, 0);

      // Ensure score is within reasonable bounds (0-40 max for AUDIT)
      const finalScore = Math.min(validatedScore, 40);

      // Categorize risk levels based on WHO guidelines
      let riskLevel = '';
      let riskColor = '';
      if (finalScore <= 7) {
        riskLevel = 'Low Risk (Zone 1)';
        riskColor = 'green';
      } else if (finalScore <= 15) {
        riskLevel = 'Medium Risk (Zone 2)';
        riskColor = 'yellow';
      } else if (finalScore <= 19) {
        riskLevel = 'High Risk (Zone 3)';
        riskColor = 'orange';
      } else {
        riskLevel = 'High Risk (Zone 4)';
        riskColor = 'red';
      }

      const results = {
        score: finalScore,
        severity_level: getAUDITSeverityLevel(finalScore),
        riskLevel,
        riskColor,
        recommendation: getRecommendation(finalScore)
      };

      navigate('/clinical/assessment/audit/complete', { state: { assessmentType: 'audit', result: results } });
    } catch (error) {
      console.error('Error calculating AUDIT results:', error);
      navigate('/clinical/assessments');
    }
  };

  const getRecommendation = (score: number) => {
    if (score <= 7) {
      return 'Continue healthy drinking patterns or abstinence';
    } else if (score <= 15) {
      return 'Consider reducing alcohol consumption';
    } else if (score <= 19) {
      return 'Strongly recommend reducing drinking';
    } else {
      return 'Medical evaluation and treatment recommended';
    }
  };

  const question = auditQuestions[currentQuestion];
  const responseOptions = getResponseOptions(currentQuestion + 1);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            AUDIT Assessment
          </h1>
          <div className="flex items-center justify-between mb-4">
            <p className="text-lg text-gray-600">
              Alcohol Use Disorders Identification Test
            </p>
            <div className="text-sm text-gray-500">
              Question {currentQuestion + 1} of {auditQuestions.length}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / auditQuestions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm mr-3">
                ALCOHOL SCREENING
              </span>
              Question {currentQuestion + 1}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg text-gray-800 mb-2 leading-relaxed">
              {question.text}
            </p>
            {question.scoringNotes && (
              <p className="text-sm text-gray-500 mb-6 italic bg-blue-50 p-3 rounded">
                <strong>Note:</strong> {question.scoringNotes}
              </p>
            )}

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
                    {option.text}
                  </div>
                </Button>
              ))}
            </div>

            {/* Navigation */}
            <div className="flex justify-between mt-8">
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentQuestion === 0}
              >
                Previous
              </Button>
              <div className="text-sm text-gray-500">
                Please select the response that best describes your alcohol use over the past year.
              </div>
              <Button
                variant="outline"
                onClick={() => navigate('/clinical/assessments')}
              >
                Exit Assessment
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">🍺 About AUDIT</h3>
              <p className="text-sm text-gray-600">
                WHO-developed screening tool to assess harmful drinking patterns and alcohol dependence.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">📊 Reliability</h3>
              <p className="text-sm text-gray-600">
                Good reliability (α = 0.75-0.85) for alcohol use screening.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2">⏱️ Time</h3>
              <p className="text-sm text-gray-600">
                Takes approximately 5-8 minutes to complete.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Risk Level Information */}
        <Card className="mt-6 bg-blue-50 border-blue-200">
          <CardContent className="p-6">
            <h3 className="font-semibold text-gray-900 mb-4">🎯 Risk Level Categories</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-green-700">Zone 1 (0-7 points):</span>
                <span className="text-gray-600 ml-2">Low risk drinking</span>
              </div>
              <div>
                <span className="font-medium text-yellow-700">Zone 2 (8-15 points):</span>
                <span className="text-gray-600 ml-2">Medium risk drinking</span>
              </div>
              <div>
                <span className="font-medium text-orange-700">Zone 3 (16-19 points):</span>
                <span className="text-gray-600 ml-2">High risk drinking</span>
              </div>
              <div>
                <span className="font-medium text-red-700">Zone 4 (20+ points):</span>
                <span className="text-gray-600 ml-2">High risk - dependent drinking</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Confidential Assessment:</strong> Your responses are private and confidential. If you're concerned about your drinking patterns, consider speaking with a healthcare provider or counselor.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AUDITAssessment;