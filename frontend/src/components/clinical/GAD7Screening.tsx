/**
 * GAD-7 Anxiety Screening Component
 *
 * Generalized Anxiety Disorder-7 Item Scale
 * Evidence-based anxiety screening tool
 *
 * Reliability: α = 0.92
 * Items: 7 questions, 0-3 scale
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface GAD7Response {
  q1_nervous: number;
  q2_worrying: number;
  q3_worries: number;
  q4_relaxing: number;
  q5_restless: number;
  q6_annoyed: number;
  q7_afraid: number;
}

interface ScreeningResult {
  id: string;
  total_score: number;
  severity_level: string;
  risk_level: string;
  interpretation: string;
  recommendations: string[];
  crisis_alert: boolean;
  risk_flags: string[];
}

const QUESTIONS = [
  {
    id: 'q1_nervous',
    text: 'Feeling nervous, anxious, or on edge',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
  {
    id: 'q2_worrying',
    text: 'Not being able to stop or control worrying',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
  {
    id: 'q3_worries',
    text: 'Worrying too much about different things',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
  {
    id: 'q4_relaxing',
    text: 'Trouble relaxing',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
  {
    id: 'q5_restless',
    text: 'Being so restless that it is hard to sit still',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
  {
    id: 'q6_annoyed',
    text: 'Becoming easily annoyed or irritable',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
  {
    id: 'q7_afraid',
    text: 'Feeling afraid, as if something awful might happen',
    options: [
      { value: 0, label: 'Not at all' },
      { value: 1, label: 'Several days' },
      { value: 2, label: 'More than half the days' },
      { value: 3, label: 'Nearly every day' },
    ],
  },
];

export function GAD7Screening() {
  const [responses, setResponses] = useState<Partial<GAD7Response>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const allQuestionsAnswered = QUESTIONS.every((q) =>
    responses[q.id as keyof GAD7Response] !== undefined
  );

  const handleResponse = (questionId: string, value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }));

    // Auto-advance to next question
    if (currentQuestion < QUESTIONS.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handleSubmit = async () => {
    if (!allQuestionsAnswered) {
      setError('Please answer all questions before submitting');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/screening/gad7', responses);
      setResult(response.data);
    } catch (err: any) {
      console.error('Screening submission error:', err);
      const errorMessage = err?.response?.data?.detail || err?.response?.data?.message || 'Failed to submit screening. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleStartOver = () => {
    setResponses({});
    setResult(null);
    setError(null);
    setCurrentQuestion(0);
  };

  // Show results if available
  if (result) {
    return (
      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle>GAD-7 Results</CardTitle>
          <CardDescription>
            Your anxiety screening results are ready
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Crisis Alert */}
          {result.crisis_alert && (
            <Alert variant="destructive">
              <AlertDescription>
                <div className="space-y-4">
                  <div className="font-semibold text-lg">
                    ⚠️ Support Available
                  </div>
                  <p>{result.interpretation}</p>
                  <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
                    <div className="font-semibold mb-2">Immediate Resources:</div>
                    <ul className="space-y-1 text-sm">
                      <li>• 🚨 Call 988 Suicide & Crisis Lifeline</li>
                      <li>• Text "HOME" to 741741 (Crisis Text Line)</li>
                      <li>• Go to nearest emergency room or call 911</li>
                    </ul>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Score Display */}
          <div className="text-center p-6 bg-secondary rounded-lg">
            <div className="text-4xl font-bold mb-2">
              {result.total_score} / 21
            </div>
            <div className="text-lg text-muted-foreground capitalize">
              {result.severity_level.replace('_', ' ')} Anxiety
            </div>
            <div className="text-sm mt-2 capitalize">
              Risk Level: {result.risk_level}
            </div>
          </div>

          {/* Interpretation */}
          <div>
            <h3 className="font-semibold mb-2">Understanding Your Results</h3>
            <p className="text-sm text-muted-foreground">{result.interpretation}</p>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="font-semibold mb-2">Recommendations</h3>
            <ul className="space-y-2">
              {result.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm flex items-start">
                  <span className="mr-2">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Disclaimer */}
          <Alert>
            <AlertDescription className="text-xs">
              <strong>Important:</strong> This screening tool is NOT a diagnostic
              instrument. A positive screen suggests you may benefit from speaking
              with a mental health professional for proper evaluation. Only a
              licensed healthcare provider can diagnose anxiety disorders.
            </AlertDescription>
          </Alert>

          <Button onClick={handleStartOver} variant="outline">
            Start Over
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Show questions
  return (
    <Card className="max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>GAD-7 Anxiety Screening</CardTitle>
        <CardDescription>
          Generalized Anxiety Disorder-7 Item Scale
          <br />
          <span className="text-xs text-muted-foreground">
            Over the last 2 weeks, how often have you been bothered by the following problems?
          </span>
        </CardDescription>
        <div className="mt-4">
          <div className="flex justify-between text-sm text-muted-foreground mb-2">
            <span>Question {currentQuestion + 1} of {QUESTIONS.length}</span>
            <span>
              {Math.round(((currentQuestion + 1) / QUESTIONS.length) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{
                width: `${((currentQuestion + 1) / QUESTIONS.length) * 100}%`,
              }}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Progress indicator for answered questions */}
        <div className="flex flex-wrap gap-2">
          {QUESTIONS.map((_, idx) => (
            <div
              key={idx}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${
                responses[QUESTIONS[idx].id as keyof GAD7Response] !== undefined
                  ? 'bg-primary text-primary-foreground'
                  : idx === currentQuestion
                  ? 'bg-secondary border-2 border-primary'
                  : 'bg-muted'
              }`}
            >
              {idx + 1}
            </div>
          ))}
        </div>

        {/* Current question */}
        <div className="space-y-4">
          <div className="text-lg font-medium">
            {QUESTIONS[currentQuestion].text}
          </div>

          {/* Response options */}
          <RadioGroup
            value={responses[QUESTIONS[currentQuestion].id as keyof GAD7Response]}
            onValueChange={(value) =>
              handleResponse(QUESTIONS[currentQuestion].id, parseInt(value))
            }
          >
            {QUESTIONS[currentQuestion].options.map((option) => (
              <div key={option.value} className="flex items-center space-x-2 p-3 rounded-lg hover:bg-secondary">
                <RadioGroupItem value={option.value.toString()} id={`${QUESTIONS[currentQuestion].id}-${option.value}`} />
                <Label
                  htmlFor={`${QUESTIONS[currentQuestion].id}-${option.value}`}
                  className="flex-1 cursor-pointer"
                >
                  {option.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion((prev) => Math.max(0, prev - 1))}
            disabled={currentQuestion === 0}
          >
            Previous
          </Button>

          {currentQuestion < QUESTIONS.length - 1 ? (
            <Button
              onClick={() => setCurrentQuestion((prev) => Math.min(QUESTIONS.length - 1, prev + 1))}
              disabled={responses[QUESTIONS[currentQuestion].id as keyof GAD7Response] === undefined}
            >
              Next
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={!allQuestionsAnswered || loading}
            >
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Submit Screening
            </Button>
          )}
        </div>

        {/* Consent reminder */}
        <Alert>
          <AlertDescription className="text-xs">
            By submitting this screening, you consent to have your responses
            evaluated by licensed mental health professionals. Your data is
            protected under HIPAA. You can withdraw consent at any time.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}

// Default export for React.lazy()
export default GAD7Screening;
