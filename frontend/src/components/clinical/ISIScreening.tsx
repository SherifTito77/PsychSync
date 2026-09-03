/**
 * ISI - Insomnia Severity Index
 *
 * Measures perceived severity of insomnia symptoms
 *
 * Reliability: α = 0.91
 * Items: 7 questions, 0-4 scale
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

interface ISIResponse {
  q1_falling_asleep: number;
  q2_staying_asleep: number;
  q3_early_wakening: number;
  q4_sleep_pattern: number;
  q5_dissatisfied: number;
  q6_noticeable: number;
  q7_worried: number;
}

interface ScreeningResult {
  id: string;
  total_score: number;
  severity: string;
  interpretation: string;
  recommendations: string[];
}

const QUESTIONS = [
  {
    id: 'q1_falling_asleep',
    text: 'Please rate the severity of your sleep problem (difficulty falling asleep):',
    options: [
      { value: 0, label: 'No problem' },
      { value: 1, label: 'Mild' },
      { value: 2, label: 'Moderate' },
      { value: 3, label: 'Severe' },
      { value: 4, label: 'Very severe' },
    ],
  },
  {
    id: 'q2_staying_asleep',
    text: 'Please rate the severity of your sleep problem (difficulty staying asleep):',
    options: [
      { value: 0, label: 'No problem' },
      { value: 1, label: 'Mild' },
      { value: 2, label: 'Moderate' },
      { value: 3, label: 'Severe' },
      { value: 4, label: 'Very severe' },
    ],
  },
  {
    id: 'q3_early_wakening',
    text: 'Please rate the severity of your sleep problem (problems waking up too early):',
    options: [
      { value: 0, label: 'No problem' },
      { value: 1, label: 'Mild' },
      { value: 2, label: 'Moderate' },
      { value: 3, label: 'Severe' },
      { value: 4, label: 'Very severe' },
    ],
  },
  {
    id: 'q4_sleep_pattern',
    text: 'How satisfied/dissatisfied are you with your current sleep pattern?',
    options: [
      { value: 0, label: 'Very satisfied' },
      { value: 1, label: 'Satisfied' },
      { value: 2, label: 'Neutral' },
      { value: 3, label: 'Dissatisfied' },
      { value: 4, label: 'Very dissatisfied' },
    ],
  },
  {
    id: 'q5_dissatisfied',
    text: 'To what extent do you consider your sleep problem to interfere with your daily functioning?',
    options: [
      { value: 0, label: 'Not at all interfering' },
      { value: 1, label: 'A little' },
      { value: 2, label: 'Somewhat' },
      { value: 3, label: 'Much' },
      { value: 4, label: 'Very much interfering' },
    ],
  },
  {
    id: 'q6_noticeable',
    text: 'How noticeable to others do you think your sleep problem is in terms of impairing the quality of your life?',
    options: [
      { value: 0, label: 'Not at all noticeable' },
      { value: 1, label: 'A little' },
      { value: 2, label: 'Somewhat' },
      { value: 3, label: 'Much' },
      { value: 4, label: 'Very much noticeable' },
    ],
  },
  {
    id: 'q7_worried',
    text: 'How worried/distressed are you about your current sleep problem?',
    options: [
      { value: 0, label: 'Not at all worried' },
      { value: 1, label: 'A little' },
      { value: 2, label: 'Somewhat' },
      { value: 3, label: 'Much' },
      { value: 4, label: 'Very much worried' },
    ],
  },
];

const ISIScreening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<ISIResponse>>({});
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = QUESTIONS[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / QUESTIONS.length) * 100;

  const handleResponse = (value: number) => {
    const newResponses = { ...responses, [currentQuestion.id]: value };
    setResponses(newResponses);

    if (currentQuestionIndex < QUESTIONS.length - 1) {
      setTimeout(() => setCurrentQuestionIndex(currentQuestionIndex + 1), 300);
    } else {
      handleSubmit(newResponses as ISIResponse);
    }
  };

  const handleSubmit = async (finalResponses: ISIResponse) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'isi',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
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
      result.total_score >= 22 ? 'text-red-600' :
      result.total_score >= 15 ? 'text-orange-600' :
      result.total_score >= 8 ? 'text-yellow-600' :
      'text-green-600';

    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">ISI Assessment Results</CardTitle>
            <CardDescription>Insomnia Severity Index</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Insomnia Severity</h3>
              <div className={`text-4xl font-bold ${scoreColor}`}>
                {result.total_score} / 28
              </div>
              <div className={`text-xl font-medium mt-2 ${scoreColor}`}>
                {result.severity}
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

            <Button onClick={handleReset} className="w-full">Take Assessment Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">ISI Assessment</CardTitle>
          <CardDescription>Insomnia Severity Index - 7 questions</CardDescription>
          <Progress value={progress} className="mt-4" />
          <p className="text-sm text-gray-500 mt-2">Question {currentQuestionIndex + 1} of {QUESTIONS.length}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && <Alert variant="error"><AlertDescription>{error}</AlertDescription></Alert>}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-gray-600">Analyzing your responses...</p>
            </div>
          ) : (
            <>
              <Label className="text-lg font-medium">{currentQuestion.text}</Label>
              <RadioGroup
                value={String(responses[currentQuestion.id as keyof ISIResponse] || 0)}
                onChange={(value) => handleResponse(parseInt(value))}
                className="space-y-3"
              >
                {currentQuestion.options.map((option) => (
                  <div key={option.value} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                    <RadioGroupItem value={option.value.toString()} id={`${currentQuestion.id}-${option.value}`} />
                    <Label htmlFor={`${currentQuestion.id}-${option.value}`} className="flex-1 cursor-pointer">{option.label}</Label>
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

export default ISIScreening;
