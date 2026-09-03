/**
 * PCL-5 PTSD Checklist for DSM-5
 *
 * 20-item assessment screening for PTSD symptoms
 * Based on DSM-5 diagnostic criteria
 *
 * Reliability: α = 0.94
 * Items: 20 questions, 0-4 scale
 * Cutoff score: ≥ 33 indicates probable PTSD
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Loader2, AlertTriangle } from 'lucide-react';
import api from '@/services/api';

interface PCL5Response {
  q1_intrusive_thoughts: number;
  q2_nightmares: number;
  q3_flashbacks: number;
  q4_emotional_distress: number;
  q5_physical_reactions: number;
  q6_avoid_thoughts: number;
  q7_avoid_reminders: number;
  q8_amnesia: number;
  q9_loss_of_interest: number;
  q10_detachment: number;
  q11_numbness: number;
  q12_distant_future: number;
  q13_sleep_disturbance: number;
  q14_irritability: number;
  q15_concentration_problems: number;
  q16_hyper_vigilance: number;
  q17_exaggerated_startle: number;
  q18_difficulty_concentrating: number;
  q19_sleep_problems: number;
  q20_hypervigilant: number;
}

interface ScreeningResult {
  id: string;
  total_score: number;
  severity_level: string;
  risk_level: string;
  interpretation: string;
  symptom_clusters: {
    re_experiencing: number;
    avoidance: number;
    negative_alt: number;
    arousal: number;
  };
  recommendations: string[];
  crisis_alert: boolean;
}

const QUESTIONS = [
  {
    id: 'q1_intrusive_thoughts',
    cluster: 're_experiencing',
    text: 'Repeated, disturbing, and unwanted memories of the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q2_nightmares',
    cluster: 're_experiencing',
    text: 'Repeated, disturbing dreams of the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q3_flashbacks',
    cluster: 're_experiencing',
    text: 'Suddenly feeling as if the stressful experience were happening again (as if you were reliving it)?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q4_emotional_distress',
    cluster: 're_experiencing',
    text: 'Feeling very upset when something reminded you of the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q5_physical_reactions',
    cluster: 're_experiencing',
    text: 'Having physical reactions (e.g., heart pounding, trouble breathing, or sweating) when reminded of the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q6_avoid_thoughts',
    cluster: 'avoidance',
    text: 'Avoiding memories, thoughts, or feelings related to the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q7_avoid_reminders',
    cluster: 'avoidance',
    text: 'Avoiding external reminders (e.g., people, places, conversations, activities, objects, or situations) that arouse memories of the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q8_amnesia',
    cluster: 'negative_alt',
    text: 'Trouble remembering important parts of the stressful experience?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q9_loss_of_interest',
    cluster: 'negative_alt',
    text: 'Having strong negative beliefs about yourself, others, or the world (e.g., "I am bad," "No one can be trusted," "The world is completely dangerous")?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q10_detachment',
    cluster: 'negative_alt',
    text: 'Blaming yourself or someone else for the stressful experience or what happened after it?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q11_numbness',
    cluster: 'negative_alt',
    text: 'Having strong negative feelings such as fear, horror, anger, guilt, or shame?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q12_distant_future',
    cluster: 'negative_alt',
    text: 'Loss of interest in activities that you used to enjoy?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q13_sleep_disturbance',
    cluster: 'negative_alt',
    text: 'Feeling distant or cut off from other people?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q14_irritability',
    cluster: 'arousal',
    text: 'Trouble experiencing positive feelings (e.g., being unable to feel happiness or satisfaction with things)?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q15_concentration_problems',
    cluster: 'arousal',
    text: 'Irritable behavior, angry outbursts, or acting aggressively?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q16_hyper_vigilance',
    cluster: 'arousal',
    text: 'Taking too many risks or doing things that could cause you harm?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q17_exaggerated_startle',
    cluster: 'arousal',
    text: 'Being "super alert" or watchful on guard?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q18_difficulty_concentrating',
    cluster: 'arousal',
    text: 'Feeling jumpy or easily startled?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q19_sleep_problems',
    cluster: 'arousal',
    text: 'Difficulty concentrating?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
  {
    id: 'q20_hypervigilant',
    cluster: 'arousal',
    text: 'Trouble falling or staying asleep?',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'A little bit' },
      { value: 2, label: 'Moderately' },
      { value: 3, label: 'Quite a bit' },
      { value: 4, label: 'Extremely' },
    ],
  },
];

const PCL5Screening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<PCL5Response>>({});
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
      handleSubmit(newResponses as PCL5Response);
    }
  };

  const handleSubmit = async (finalResponses: PCL5Response) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'pcl5',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
      console.error('PCL-5 submission error:', err);
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
      result.total_score >= 50 ? 'text-red-600' :
      result.total_score >= 33 ? 'text-orange-600' :
      result.total_score >= 20 ? 'text-yellow-600' :
      'text-green-600';

    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {result.crisis_alert && (
          <Alert variant="error" className="border-red-600">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Important:</strong> Your responses indicate significant distress. Please consider
              speaking with a mental health professional or contacting crisis support services.
            </AlertDescription>
          </Alert>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">PCL-5 Assessment Results</CardTitle>
            <CardDescription>PTSD Checklist for DSM-5</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">Total Score</h3>
              <div className={`text-4xl font-bold ${scoreColor}`}>
                {result.total_score} / 80
              </div>
              <div className={`text-xl font-medium mt-2 ${scoreColor}`}>
                {result.severity_level}
              </div>
            </div>

            {/* Symptom Clusters */}
            <div className="border-t pt-4">
              <h4 className="font-semibold mb-3">Symptom Clusters:</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-600">Re-experiencing (5 items)</div>
                  <div className="text-2xl font-bold">{result.symptom_clusters.re_experiencing}/20</div>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-600">Avoidance (2 items)</div>
                  <div className="text-2xl font-bold">{result.symptom_clusters.avoidance}/8</div>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-600">Negative Alterations (7 items)</div>
                  <div className="text-2xl font-bold">{result.symptom_clusters.negative_alt}/28</div>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-600">Arousal (6 items)</div>
                  <div className="text-2xl font-bold">{result.symptom_clusters.arousal}/24</div>
                </div>
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
          <CardTitle className="text-2xl">PCL-5 Assessment</CardTitle>
          <CardDescription>
            PTSD Checklist for DSM-5 - 20 questions
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
                <p className="text-sm text-gray-500 mb-2">In the past month, how much were you bothered by:</p>
                <Label className="text-lg font-medium">{currentQuestion.text}</Label>
              </div>

              <RadioGroup
                value={String(responses[currentQuestion.id as keyof PCL5Response] || 0)}
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

export default PCL5Screening;
