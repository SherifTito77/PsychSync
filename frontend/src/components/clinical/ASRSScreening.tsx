/**
 * ASRS v1.1 - Adult ADHD Self-Report Scale
 *
 * World Health Organization screening tool for ADHD in adults
 *
 * Sensitivity: 0.687, Specificity: 0.721
 * Items: 18 questions
 * Part A (items 1-6) is the screening screener
 * Part B (items 7-18) provides additional symptom assessment
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

interface ASRSResponse {
  // Part A - Screening questions (most predictive)
  a1_careless: number;
  a2_difficulty_sustaining: number;
  a3_difficulty_listening: number;
  a4_distracted: number;
  a5_difficulty_organization: number;
  a6_forgetting_obligations: number;

  // Part B - Additional symptoms
  b7_avoid_tasks: number;
  b8_difficulty_finishing: number;
  b9_difficulty_concentrating: number;
  b10_losing_things: number;
  b11_distracted_activity: number;
  b12_difficultylistening: number;
  b13_fidgeting: number;
  b14_restless: number;
  b15_difficulty_relaxing: number;
  b16_active: number;
  b17_talking_excessively: number;
  b18_blurting_answers: number;
}

interface ScreeningResult {
  id: string;
  part_a_score: number;
  part_b_score: number;
  total_score: number;
  adhd_likelihood: string;
  interpretation: string;
  recommendations: string[];
  risk_flags: string[];
}

const QUESTIONS = [
  // Part A - Screening questions
  {
    id: 'a1_careless',
    part: 'A',
    text: 'How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'a2_difficulty_sustaining',
    part: 'A',
    text: 'How often do you have difficulty getting things in order when you have to do a task that requires organization?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'a3_difficulty_listening',
    part: 'A',
    text: 'When you have a task that requires a lot of thought, how often do you avoid or delay getting started?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'a4_distracted',
    part: 'A',
    text: 'How often do you have problems remembering appointments or obligations?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'a5_difficulty_organization',
    part: 'A',
    text: 'How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'a6_forgetting_obligations',
    part: 'A',
    text: 'How often do you feel overly active and compelled to do things, like you were driven by a motor?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  // Part B questions
  {
    id: 'b7_avoid_tasks',
    part: 'B',
    text: 'How often do you make careless mistakes when you have to work on a boring or difficult project?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b8_difficulty_finishing',
    part: 'B',
    text: 'How often do you have difficulty keeping your attention when you are doing boring or repetitive work?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b9_difficulty_concentrating',
    part: 'B',
    text: 'How often do you have difficulty concentrating on what people are saying to you, even when they are speaking to you directly?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b10_losing_things',
    part: 'B',
    text: 'How often do you have trouble wrapping up the final details of a project, once the challenging parts have been done?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b11_distracted_activity',
    part: 'B',
    text: 'How often do you have difficulty getting things in order when you have to do a task that requires organization?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b12_difficultylistening',
    part: 'B',
    text: 'When you have a task that requires a lot of thought, how often do you avoid or delay getting started?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b13_fidgeting',
    part: 'B',
    text: 'How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b14_restless',
    part: 'B',
    text: 'How often do you feel overly active and compelled to do things, like you were driven by a motor?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b15_difficulty_relaxing',
    part: 'B',
    text: 'How often do you leave your seat in meetings or other situations where you are expected to remain seated?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b16_active',
    part: 'B',
    text: 'How often do you feel restless or fidgety?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b17_talking_excessively',
    part: 'B',
    text: 'How often do you have difficulty unwinding and relaxing when you have time to yourself?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
  {
    id: 'b18_blurting_answers',
    part: 'B',
    text: 'How often do you find yourself talking too much when you are in social situations?',
    options: [
      { value: 0, label: 'Never' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Sometimes' },
      { value: 3, label: 'Often' },
      { value: 4, label: 'Very Often' },
    ],
  },
];

const ASRSScreening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<ASRSResponse>>({});
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
      handleSubmit(newResponses as ASRSResponse);
    }
  };

  const handleSubmit = async (finalResponses: ASRSResponse) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'asrs',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
      console.error('ASRS submission error:', err);
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
            <CardTitle className="text-2xl">ASRS v1.1 Assessment Results</CardTitle>
            <CardDescription>Adult ADHD Self-Report Scale</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="text-lg font-semibold mb-2">ADHD Screening</h3>
              <div className="text-2xl font-bold text-blue-900">
                {result.adhd_likelihood}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Part A Score (Screening)</div>
                <div className="text-2xl font-bold">{result.part_a_score}/24</div>
              </div>
              <div className="p-3 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Part B Score (Symptoms)</div>
                <div className="text-2xl font-bold">{result.part_b_score}/48</div>
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
          <CardTitle className="text-2xl">ASRS v1.1 Assessment</CardTitle>
          <CardDescription>
            Adult ADHD Self-Report Scale - 18 questions
          </CardDescription>
          <Progress value={progress} className="mt-4" />
          <p className="text-sm text-gray-500 mt-2">
            Question {currentQuestionIndex + 1} of {QUESTIONS.length} (Part {currentQuestion.part})
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
                value={(responses[currentQuestion.id as keyof ASRSResponse] || 0).toString()}
                onChange={(value) => handleResponse(parseInt(value))}
                className="space-y-3"
              >
                {currentQuestion.options.map((option) => (
                  <div key={option.value} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                    <RadioGroupItem value={option.value.toString()} id={`${currentQuestion.id}-${option.value}`} />
                    <Label htmlFor={`${currentQuestion.id}-${option.value}`} className="flex-1 cursor-pointer">
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

export default ASRSScreening;
