/**
 * C-SSRS Suicide Risk Screening Component
 *
 * Columbia-Suicide Severity Rating Scale
 * Evidence-based suicide risk assessment tool
 *
 * Reliability: AUC = 0.83
 * Items: 6 questions assessing suicidal ideation and behavior
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface CSSRSResponse {
  wish_dead: number;
  suicidal_ideation: number;
  ideation_frequency: number;
  ideation_duration: number;
  ideation_controll: number;
  suicide_attempts: number;
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
    id: 'wish_dead',
    text: 'Have you wished you were dead or wished you could go to sleep and not wake up?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
    warning: true,
  },
  {
    id: 'suicidal_ideation',
    text: 'Have you actually had any thoughts about killing yourself?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
    warning: true,
  },
  {
    id: 'ideation_frequency',
    text: 'Have you had these thoughts about killing yourself more than once?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes - Once' },
      { value: 2, label: 'Yes - Multiple times' },
    ],
  },
  {
    id: 'ideation_duration',
    text: 'How long have you had these thoughts about killing yourself?',
    options: [
      { value: 0, label: 'Briefly' },
      { value: 1, label: 'Several hours' },
      { value: 2, label: 'One or more days' },
      { value: 3, label: 'One week or more' },
    ],
  },
  {
    id: 'ideation_controll',
    text: 'Have you done anything to try to stop these thoughts or make them less frequent?',
    options: [
      { value: 0, label: 'Yes, I can control them' },
      { value: 1, label: 'I try but cannot stop them' },
      { value: 2, label: 'No, I cannot control them' },
    ],
  },
  {
    id: 'suicide_attempts',
    text: 'Have you ever tried to kill yourself or made a suicide attempt?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes, once' },
      { value: 2, label: 'Yes, multiple times' },
    ],
    warning: true,
  },
];

export function CSSRSScreening() {
  const [responses, setResponses] = useState<Partial<CSSRSResponse>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const allQuestionsAnswered = QUESTIONS.every((q) =>
    responses[q.id as keyof CSSRSResponse] !== undefined
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
      const response = await api.post('/api/v1/screening/cssrs', responses);
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
          <CardTitle>C-SSRS Results</CardTitle>
          <CardDescription>
            Columbia-Suicide Severity Rating Scale Assessment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Crisis Alert */}
          {result.crisis_alert && (
            <Alert variant="destructive">
              <AlertDescription>
                <div className="space-y-4">
                  <div className="font-semibold text-lg">
                    🚨 Immediate Support Available
                  </div>
                  <p>{result.interpretation}</p>
                  <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
                    <div className="font-semibold mb-2">Crisis Resources:</div>
                    <ul className="space-y-1 text-sm">
                      <li>• 📞 Call 988 Suicide & Crisis Lifeline (24/7)</li>
                      <li>• 💬 Text "HOME" to 741741 (Crisis Text Line)</li>
                      <li>• 🚨 Call 911 or go to nearest emergency room</li>
                    </ul>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Risk Level Display */}
          <div className="text-center p-6 bg-secondary rounded-lg">
            <div className="text-2xl font-bold mb-2">
              Risk Level: {result.risk_level.toUpperCase()}
            </div>
            <div className="text-lg text-muted-foreground capitalize">
              {result.severity_level.replace('_', ' ')}
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

          {/* Immediate Crisis Resources */}
          <Alert variant="destructive">
            <AlertDescription>
              <div className="space-y-2">
                <div className="font-semibold">If you're in crisis right now:</div>
                <ul className="text-sm space-y-1">
                  <li>• Call 988 (Suicide & Crisis Lifeline)</li>
                  <li>• Text "HOME" to 741741</li>
                  <li>• Go to your nearest emergency room</li>
                  <li>• Contact a trusted friend or family member</li>
                </ul>
              </div>
            </AlertDescription>
          </Alert>

          {/* Disclaimer */}
          <Alert>
            <AlertDescription className="text-xs">
              <strong>Important:</strong> This screening tool is NOT a diagnostic
              instrument. If you're experiencing thoughts of self-harm, please
              contact emergency services immediately or call 988. Help is
              available 24/7 and you are not alone.
            </AlertDescription>
          </Alert>

          <div className="flex gap-2">
            <Button onClick={handleStartOver} variant="outline">
              Start Over
            </Button>
            <Button
              onClick={() => window.location.href = '/screening/crisis-resources'}
            >
              View Crisis Resources
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show questions
  return (
    <Card className="max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>C-SSRS Suicide Risk Screening</CardTitle>
        <CardDescription>
          Columbia-Suicide Severity Rating Scale
          <br />
          <span className="text-xs text-muted-foreground">
            Please answer honestly. Your responses help us provide appropriate support.
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
        {/* Crisis Banner */}
        <Alert variant="destructive">
          <AlertDescription className="text-sm">
            <strong>Need immediate help?</strong> Call 988 or 911, or text "HOME" to 741741.
            Help is available 24/7.
          </AlertDescription>
        </Alert>

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
                responses[QUESTIONS[idx].id as keyof CSSRSResponse] !== undefined
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

          {/* Warning for sensitive questions */}
          {QUESTIONS[currentQuestion].warning && (
            <Alert>
              <AlertDescription className="text-sm">
                Your honest answer helps us provide the best support.
                If you are in crisis, please call 988 immediately.
              </AlertDescription>
            </Alert>
          )}

          {/* Response options */}
          <RadioGroup
            value={responses[QUESTIONS[currentQuestion].id as keyof CSSRSResponse]}
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
              disabled={responses[QUESTIONS[currentQuestion].id as keyof CSSRSResponse] === undefined}
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
            evaluated by mental health professionals. Your data is
            protected under HIPAA. If you indicate immediate risk,
            we will connect you with crisis resources.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}

// Default export for React.lazy()
export default CSSRSScreening;
