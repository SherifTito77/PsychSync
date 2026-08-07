/**
 * AUDIT - Alcohol Use Disorders Identification Test
 *
 * World Health Organization screening tool for hazardous and harmful alcohol use
 *
 * Reliability: α = 0.92
 * Items: 10 questions with mixed scoring
 * Developed by WHO
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface AUDITResponse {
  q1_frequency: number;
  q2_amount: number;
  q3_binge_frequency: number;
  q4_loss_control: number;
  q5_failure_meet: number;
  q6_morning_drinking: number;
  q7_guilt: number;
  q8_memory_loss: number;
  q9_injury: number;
  q10_concern: number;
}

interface ScreeningResult {
  id: string;
  total_score: number;
  risk_level: string;
  risk_category: string;
  interpretation: string;
  recommendations: string[];
  risk_flags: string[];
}

const QUESTIONS = [
  {
    id: 'q1_frequency',
    text: 'How often do you have a drink containing alcohol?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Monthly or less' },
      { value: 2, label: '2 to 4 times a month' },
      { value: 3, label: '2 to 3 times a week' },
      { value: 4, label: '4 or more times a week' },
    ],
  },
  {
    id: 'q2_amount',
    text: 'How many standard drinks containing alcohol do you have on a typical day?',
    options: [
      { value: 0, label: '1 or 2' },
      { value: 1, label: '3 or 4' },
      { value: 2, label: '5 or 6' },
      { value: 3, label: '7 to 9' },
      { value: 4, label: '10 or more' },
    ],
  },
  {
    id: 'q3_binge_frequency',
    text: 'How often do you have six or more drinks on one occasion?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Less than monthly' },
      { value: 2, label: 'Monthly' },
      { value: 3, label: 'Weekly' },
      { value: 4, label: 'Daily or almost daily' },
    ],
  },
  {
    id: 'q4_loss_control',
    text: 'How often during the last year have you found that you were not able to stop drinking once you had started?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Less than monthly' },
      { value: 2, label: 'Monthly' },
      { value: 3, label: 'Weekly' },
      { value: 4, label: 'Daily or almost daily' },
    ],
  },
  {
    id: 'q5_failure_meet',
    text: 'How often during the last year have you failed to do what was normally expected from you because of drinking?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Less than monthly' },
      { value: 2, label: 'Monthly' },
      { value: 3, label: 'Weekly' },
      { value: 4, label: 'Daily or almost daily' },
    ],
  },
  {
    id: 'q6_morning_drinking',
    text: 'How often during the last year have you needed a first drink in the morning to get yourself going after a heavy drinking session?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Less than monthly' },
      { value: 2, label: 'Monthly' },
      { value: 3, label: 'Weekly' },
      { value: 4, label: 'Daily or almost daily' },
    ],
  },
  {
    id: 'q7_guilt',
    text: 'How often during the last year have you had a feeling of guilt or remorse after drinking?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Less than monthly' },
      { value: 2, label: 'Monthly' },
      { value: 3, label: 'Weekly' },
      { value: 4, label: 'Daily or almost daily' },
    ],
  },
  {
    id: 'q8_memory_loss',
    text: 'How often during the last year have you been unable to remember what happened the night before because you had been drinking?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Less than monthly' },
      { value: 2, label: 'Monthly' },
      { value: 3, label: 'Weekly' },
      { value: 4, label: 'Daily or almost daily' },
    ],
  },
  {
    id: 'q9_injury',
    text: 'Have you or someone else been injured as a result of your drinking?',
    options: [
      { value: 0, label: 'No' },
      { value: 2, label: 'Yes, but not in the last year' },
      { value: 4, label: 'Yes, during the last year' },
    ],
  },
  {
    id: 'q10_concern',
    text: 'Has a relative or friend, or a doctor or other health worker been concerned about your drinking or suggested you cut down?',
    options: [
      { value: 0, label: 'No' },
      { value: 2, label: 'Yes, but not in the last year' },
      { value: 4, label: 'Yes, during the last year' },
    ],
  },
];

const AUDITScreening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<AUDITResponse>>({});
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = QUESTIONS[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / QUESTIONS.length) * 100;

  const handleResponse = (value: number) => {
    const newResponses = {
      ...responses,
      [currentQuestion.id]: value,
    };
    setResponses(newResponses);

    // Move to next question or submit
    if (currentQuestionIndex < QUESTIONS.length - 1) {
      setTimeout(() => {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }, 300);
    } else {
      handleSubmit(newResponses as AUDITResponse);
    }
  };

  const handleSubmit = async (finalResponses: AUDITResponse) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'audit',
        responses: responses
      }
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
      console.error('AUDIT submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentQuestionIndex(0);
    setResponses({});
    setResult(null);
    setError(null);
  };

  if (result) {
    const scoreColor =
      result.total_score >= 20 ? 'text-red-600' :
      result.total_score >= 16 ? 'text-orange-600' :
      result.total_score >= 8 ? 'text-yellow-600' :
      'text-green-600';

    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">AUDIT Assessment Results</CardTitle>
            <CardDescription>Alcohol Use Disorders Identification Test (WHO)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Total Score</h3>
              <div className={`text-4xl font-bold ${scoreColor}`}>
                {result.total_score} / 40
              </div>
              <div className={`text-xl font-medium mt-2 ${scoreColor}`}>
                {result.risk_category}
              </div>
            </div>

            {result.interpretation && (
              <Alert>
                <AlertDescription className="text-base">
                  {result.interpretation}
                </AlertDescription>
              </Alert>
            )}

            {result.recommendations && result.recommendations.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Recommendations:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm">{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            <Button onClick={handleReset} className="w-full">
              Take Assessment Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">AUDIT Assessment</CardTitle>
          <CardDescription>
            Alcohol Use Disorders Identification Test - 10 questions
          </CardDescription>
          <Progress value={progress} className="mt-4" />
          <p className="text-sm text-gray-500 mt-2">
            Question {currentQuestionIndex + 1} of {QUESTIONS.length}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="error">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-gray-600">Analyzing your responses...</p>
            </div>
          ) : (
            <>
              <div>
                <Label className="text-lg font-medium">{currentQuestion.text}</Label>
              </div>

              <RadioGroup
                value={(responses[currentQuestion.id as keyof AUDITResponse] || 0).toString()}
                onChange={(value) => handleResponse(parseInt(value))}
                className="space-y-3"
              >
                {currentQuestion.options.map((option) => (
                  <div key={option.value} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                    <RadioGroupItem value={option.value.toString()} id={`${currentQuestion.id}-${option.value}`} />
                    <Label
                      htmlFor={`${currentQuestion.id}-${option.value}`}
                      className="flex-1 cursor-pointer"
                    >
                      {option.label}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AUDITScreening;
