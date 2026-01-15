/**
 * AQ-10 Autism Spectrum Screening Component
 *
 * Autism Spectrum Quotient - 10 Item Version
 * Evidence-based autism screening tool
 *
 * Reliability: α = 0.85
 * Items: 10 questions, agree/disagree format
 * Sensitivity: 0.88, Specificity: 0.91
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface AQ10Response {
  q1_social: number;
  q2_routine: number;
  q3_interests: number;
  q4_numbers: number;
  q5_parties: number;
  q6_people: number;
  q7_reading: number;
  q8_imagination: number;
  q9_dates: number;
  q10_hobbies: number;
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
    id: 'q1_social',
    text: 'I often notice small sounds when others do not',
    options: [
      { value: 0, label: 'Disagree' },
      { value: 1, label: 'Agree' },
    ],
  },
  {
    id: 'q2_routine',
    text: 'I usually concentrate more on the whole picture, rather than the small details',
    options: [
      { value: 0, label: 'Agree' },
      { value: 1, label: 'Disagree' },
    ],
  },
  {
    id: 'q3_interests',
    text: 'I find it easy to do more than one thing at once',
    options: [
      { value: 0, label: 'Agree' },
      { value: 1, label: 'Disagree' },
    ],
  },
  {
    id: 'q4_numbers',
    text: 'If there is an interruption, I can switch back to what I was doing very quickly',
    options: [
      { value: 0, label: 'Agree' },
      { value: 1, label: 'Disagree' },
    ],
  },
  {
    id: 'q5_parties',
    text: 'I find it easy to "read between the lines" when someone is talking to me',
    options: [
      { value: 0, label: 'Agree' },
      { value: 1, label: 'Disagree' },
    ],
  },
  {
    id: 'q6_people',
    text: 'I know how to tell if someone listening to me is getting bored',
    options: [
      { value: 0, label: 'Agree' },
      { value: 1, label: 'Disagree' },
    ],
  },
  {
    id: 'q7_reading',
    text: 'When I am reading a story, I find it difficult to work out the characters\' intentions',
    options: [
      { value: 0, label: 'Disagree' },
      { value: 1, label: 'Agree' },
    ],
  },
  {
    id: 'q8_imagination',
    text: 'I like to collect information about categories of things (e.g., types of cars, types of birds, types of trains, etc.)',
    options: [
      { value: 0, label: 'Disagree' },
      { value: 1, label: 'Agree' },
    ],
  },
  {
    id: 'q9_dates',
    text: 'I find it difficult to work out people\'s intentions',
    options: [
      { value: 0, label: 'Disagree' },
      { value: 1, label: 'Agree' },
    ],
  },
  {
    id: 'q10_hobbies',
    text: 'I find it easy to imagine what it would be like to be someone else',
    options: [
      { value: 0, label: 'Agree' },
      { value: 1, label: 'Disagree' },
    ],
  },
];

export function AQ10Screening() {
  const [responses, setResponses] = useState<Partial<AQ10Response>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const allQuestionsAnswered = QUESTIONS.every((q) =>
    responses[q.id as keyof AQ10Response] !== undefined
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
      const response = await api.post('/api/v1/screening/aq10', responses);
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
          <CardTitle>AQ-10 Results</CardTitle>
          <CardDescription>
            Your autism spectrum screening results are ready
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Score Display */}
          <div className="text-center p-6 bg-secondary rounded-lg">
            <div className="text-4xl font-bold mb-2">
              {result.total_score} / 10
            </div>
            <div className="text-lg text-muted-foreground capitalize">
              {result.severity_level.replace('_', ' ')}
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
              instrument. The AQ-10 is a brief screening measure that identifies
              individuals who may benefit from a comprehensive diagnostic evaluation
              for autism spectrum conditions. Only a qualified healthcare professional
              can diagnose autism spectrum disorder.
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
        <CardTitle>AQ-10 Autism Spectrum Screening</CardTitle>
        <CardDescription>
          Autism Spectrum Quotient - 10 Items
          <br />
          <span className="text-xs text-muted-foreground">
            Please indicate how strongly you agree or disagree with each statement.
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
                responses[QUESTIONS[idx].id as keyof AQ10Response] !== undefined
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
            value={responses[QUESTIONS[currentQuestion].id as keyof AQ10Response]}
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
              disabled={responses[QUESTIONS[currentQuestion].id as keyof AQ10Response] === undefined}
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
export default AQ10Screening;
