/**
 * DASS-21 Depression, Anxiety, and Stress Scales
 *
 * 21-item assessment measuring three dimensions:
 * - Depression (7 items)
 * - Anxiety (7 items)
 * - Stress (7 items)
 *
 * Reliability: α = 0.84-0.91
 * Items: 21 questions, 0-3 scale
 * Scoring: Multiply each subscale by 2
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

interface DASS21Response {
  // Depression items
  d1_downhearted: number;
  d2_hopeless: number;
  d3_no_meaning: number;
  d4_crying: number;
  d5_trouble_starting: number;
  d6_down_depressed: number;
  d7_nothing_look_forward: number;

  // Anxiety items
  a1_trembling: number;
  a2_mouth_dry: number;
  a3_breathing_difficult: number;
  a4_heart_pounding: number;
  a5_panicky: number;
  a6_shaky: number;
  a7_worry: number;

  // Stress items
  s1_hard_to_calm: number;
  s2_mouth_dry_stress: number;
  s3_breathing_difficult_stress: number;
  s4_difficulty_swallowing: number;
  s5_cannot_control_worry: number;
  s6_overwhelmed: number;
  s7_difficulty_relaxing: number;
}

interface ScreeningResult {
  id: string;
  depression_score: number;
  anxiety_score: number;
  stress_score: number;
  depression_severity: string;
  anxiety_severity: string;
  stress_severity: string;
  interpretation: string;
  recommendations: string[];
  risk_flags: string[];
}

const QUESTIONS = [
  // Depression Items
  {
    id: 'd1_downhearted',
    category: 'depression',
    text: 'I found it hard to wind down',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a1_trembling',
    category: 'anxiety',
    text: 'I was aware of dryness of my mouth',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's1_hard_to_calm',
    category: 'stress',
    text: 'I couldn\'t seem to experience any positive feeling at all',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'd2_hopeless',
    category: 'depression',
    text: 'I experienced breathing difficulty (eg, excessively rapid breathing, breathlessness in the absence of physical exertion)',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a2_mouth_dry',
    category: 'anxiety',
    text: 'I found it difficult to work up the initiative to do things',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's2_mouth_dry_stress',
    category: 'stress',
    text: 'I tended to over-react to situations',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'd3_no_meaning',
    category: 'depression',
    text: 'I felt that I was using a lot of nervous energy',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a3_breathing_difficult',
    category: 'anxiety',
    text: 'I felt that I had nothing to look forward to',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's3_breathing_difficult_stress',
    category: 'stress',
    text: 'I found myself getting agitated',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'd4_crying',
    category: 'depression',
    text: 'I found it difficult to relax',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a4_heart_pounding',
    category: 'anxiety',
    text: 'I felt down-hearted and blue',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's4_difficulty_swallowing',
    category: 'stress',
    text: 'I was intolerant of anything that kept me from getting on with what I was doing',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'd5_trouble_starting',
    category: 'depression',
    text: 'I felt that I was rather touchy',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a5_panicky',
    category: 'anxiety',
    text: 'I was unable to become enthusiastic about anything',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's5_cannot_control_worry',
    category: 'stress',
    text: 'I felt I was pretty worthless',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'd6_down_depressed',
    category: 'depression',
    text: 'I felt that I was rather touchy',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a6_shaky',
    category: 'anxiety',
    text: 'I was aware of the action of my heart in the absence of physical exertion (eg, sense of heart rate increase, heart missing a beat)',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's6_overwhelmed',
    category: 'stress',
    text: 'I felt that I was rather touchy',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'd7_nothing_look_forward',
    category: 'depression',
    text: 'I felt scared without any good reason',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 'a7_worry',
    category: 'anxiety',
    text: 'I felt that life was meaningless',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
  {
    id: 's7_difficulty_relaxing',
    category: 'stress',
    text: 'I found it hard to wind down',
    options: [
      { value: 0, label: 'Did not apply to me at all' },
      { value: 1, label: 'Applied to me to some degree, or some of the time' },
      { value: 2, label: 'Applied to me to a considerable degree, or a good part of the time' },
      { value: 3, label: 'Applied to me very much, or most of the time' },
    ],
  },
];

const DASS21Screening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<DASS21Response>>({});
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
      handleSubmit(newResponses as DASS21Response);
    }
  };

  const handleSubmit = async (finalResponses: DASS21Response) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'dass21',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
      console.error('DASS-21 submission error:', err);
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
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">DASS-21 Assessment Results</CardTitle>
            <CardDescription>Depression, Anxiety, and Stress Scales</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Depression Score */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold mb-2">Depression: {result.depression_score}/42</h3>
              <div className={`text-lg font-medium ${
                result.depression_score <= 9 ? 'text-green-600' :
                result.depression_score <= 13 ? 'text-yellow-600' :
                result.depression_score <= 20 ? 'text-orange-600' :
                'text-red-600'
              }`}>
                {result.depression_severity}
              </div>
            </div>

            {/* Anxiety Score */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold mb-2">Anxiety: {result.anxiety_score}/42</h3>
              <div className={`text-lg font-medium ${
                result.anxiety_score <= 7 ? 'text-green-600' :
                result.anxiety_score <= 9 ? 'text-yellow-600' :
                result.anxiety_score <= 14 ? 'text-orange-600' :
                'text-red-600'
              }`}>
                {result.anxiety_severity}
              </div>
            </div>

            {/* Stress Score */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold mb-2">Stress: {result.stress_score}/42</h3>
              <div className={`text-lg font-medium ${
                result.stress_score <= 14 ? 'text-green-600' :
                result.stress_score <= 18 ? 'text-yellow-600' :
                result.stress_score <= 25 ? 'text-orange-600' :
                'text-red-600'
              }`}>
                {result.stress_severity}
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
          <CardTitle className="text-2xl">DASS-21 Assessment</CardTitle>
          <CardDescription>
            Depression, Anxiety, and Stress Scales - 21 questions
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
                value={String(responses[currentQuestion.id as keyof DASS21Response] || 0)}
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

export default DASS21Screening;
