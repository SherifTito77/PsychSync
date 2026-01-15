/**
 * PSS-10 - Perceived Stress Scale
 *
 * Measures the degree to which situations in one's life are appraised as stressful
 *
 * Reliability: α = 0.78
 * Items: 10 questions, 0-4 scale
 * Scoring: Items 4, 5, 7, 8 are reverse-scored
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

interface PSS10Response {
  q1_upset: number;
  q2_control: number;
  q3_confident: number;
  q4_coped: number;
  q5_on_top: number;
  q6_cannot_cope: number;
  q7_control_events: number;
  q8_not_control: number;
  q9_angry: number;
  q10_difficulties_piled: number;
}

interface ScreeningResult {
  id: string;
  total_score: number;
  perceived_stress: string;
  interpretation: string;
  recommendations: string[];
}

const QUESTIONS = [
  {
    id: 'q1_upset',
    reverse: false,
    text: 'In the last month, how often have you been upset because of something that happened unexpectedly?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q2_control',
    reverse: false,
    text: 'In the last month, how often have you felt that you were unable to control the important things in your life?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q3_confident',
    reverse: false,
    text: 'In the last month, how often have you felt nervous and stressed?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q4_coped',
    reverse: true,
    text: 'In the last month, how often have you felt confident about your ability to handle your personal problems?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q5_on_top',
    reverse: true,
    text: 'In the last month, how often have you felt that things were going your way?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q6_cannot_cope',
    reverse: false,
    text: 'In the last month, how often have you found that you could not cope with all the things that you had to do?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q7_control_events',
    reverse: true,
    text: 'In the last month, how often have you been able to control irritations in your life?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q8_not_control',
    reverse: true,
    text: 'In the last month, how often have you felt that you were on top of things?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q9_angry',
    reverse: false,
    text: 'In the last month, how often have you been angered because of things that were outside of your control?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
  {
    id: 'q10_difficulties_piled',
    reverse: false,
    text: 'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Almost never' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Fairly often' },
      { value: 4, label: 'Very often' },
    ],
  },
];

const PSS10Screening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<PSS10Response>>({});
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

    if (currentQuestionIndex < QUESTIONS.length - 1) {
      setTimeout(() => {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }, 300);
    } else {
      handleSubmit(newResponses as PSS10Response);
    }
  };

  const handleSubmit = async (finalResponses: PSS10Response) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/screening/pss10', finalResponses);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
      console.error('PSS-10 submission error:', err);
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
      result.total_score >= 27 ? 'text-red-600' :
      result.total_score >= 14 ? 'text-yellow-600' :
      'text-green-600';

    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">PSS-10 Assessment Results</CardTitle>
            <CardDescription>Perceived Stress Scale</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Perceived Stress Score</h3>
              <div className={`text-4xl font-bold ${scoreColor}`}>
                {result.total_score} / 40
              </div>
              <div className={`text-xl font-medium mt-2 ${scoreColor}`}>
                {result.perceived_stress}
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
          <CardTitle className="text-2xl">PSS-10 Assessment</CardTitle>
          <CardDescription>
            Perceived Stress Scale - 10 questions
          </CardDescription>
          <Progress value={progress} className="mt-4" />
          <p className="text-sm text-gray-500 mt-2">
            Question {currentQuestionIndex + 1} of {QUESTIONS.length}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
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
                onValueChange={(value) => handleResponse(parseInt(value))}
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

export default PSS10Screening;
