/**
 * ACE Adverse Childhood Experiences Screening Component
 *
 * Adverse Childhood Experiences Questionnaire
 * Evidence-based trauma and adversity screening tool
 *
 * Reliability: α = 0.88
 * Items: 10 questions, yes/no format
 * Strong predictor of adult health outcomes
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface ACEResponse {
  q1_abuse: number;
  q2_neglect: number;
  q3_domestic_violence: number;
  q4_substance_abuse: number;
  q5_mental_illness: number;
  q6_separation: number;
  q7_abuse_mother: number;
  q8_emotional_neglect: number;
  q9_physical_neglect: number;
  q10_household_challenges: number;
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
    id: 'q1_abuse',
    text: 'Did a parent or other adult in the household often or very often swear at you, insult you, put you down, or humiliate you? Or act in a way that made you afraid that you might be physically hurt?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q2_neglect',
    text: 'Did a parent or other adult in the household often or very often push, grab, slap, or throw something at you? Or ever hit you so hard that you had marks or were injured?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q3_domestic_violence',
    text: 'Did an adult or person at least 5 years older than you ever touch or fondle you or have you touch their body in a sexual way? Or attempt or actually have oral, anal, or vaginal intercourse with you?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q4_substance_abuse',
    text: 'Did you often or very often feel that no one in your family loved you or thought you were important or special? Or your family didn\'t look out for each other, feel close to each other, or support each other?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q5_mental_illness',
    text: 'Did you often or very often feel that you didn\'t have enough to eat, had to wear dirty clothes, and had no one to protect you? Or your parents were too drunk or high to take care of you or take you to the doctor if you needed it?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q6_separation',
    text: 'Were your biological parents ever separated or divorced?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q7_abuse_mother',
    text: 'Was your mother or stepmother often or very often pushed, grabbed, slapped, or had something thrown at her? Or sometimes, often, or very often kicked, bitten, hit with a fist, or hit with something hard? Or ever repeatedly hit over at least a few minutes or threatened with a gun or knife?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q8_emotional_neglect',
    text: 'Did you live with anyone who was a problem drinker or alcoholic, or who used street drugs?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q9_physical_neglect',
    text: 'Was a household member depressed or mentally ill, or did a household member attempt suicide?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
  {
    id: 'q10_household_challenges',
    text: 'Did a household member go to prison?',
    options: [
      { value: 0, label: 'No' },
      { value: 1, label: 'Yes' },
    ],
  },
];

export function ACEScreening() {
  const [responses, setResponses] = useState<Partial<ACEResponse>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const allQuestionsAnswered = QUESTIONS.every((q) =>
    responses[q.id as keyof ACEResponse] !== undefined
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
      const response = await api.post(./clinical/screening/submit., { assessment_type: (w+), responses: };
      setResult(response.data as ScreeningResult);
    } catch (err) {
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
          <CardTitle>ACE Score Results</CardTitle>
          <CardDescription>
            Your adverse childhood experiences results are ready
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Crisis Alert */}
          {result.crisis_alert && (
            <Alert variant="error">
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
                      <li>• National Domestic Violence Hotline: 1-800-799-7233</li>
                    </ul>
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

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
              <strong>Important:</strong> This screening tool measures adverse childhood
              experiences and is NOT a diagnostic instrument. Higher ACE scores are
              associated with increased health risks, but having ACEs does not determine
              your future. Many people with high ACE scores live healthy, fulfilling lives.
              Healing is possible with proper support and interventions.
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
        <CardTitle>ACE Questionnaire</CardTitle>
        <CardDescription>
          Adverse Childhood Experiences - 10 Items
          <br />
          <span className="text-xs text-muted-foreground">
            Please answer the following questions about your first 18 years of life.
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
          <Alert variant="error">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Content warning */}
        {currentQuestion === 0 && (
          <Alert>
            <AlertDescription className="text-sm">
              <strong>Content Notice:</strong> This questionnaire asks about potentially
              sensitive childhood experiences. You may skip any question and stop at any time.
              Support resources are available if you need them.
            </AlertDescription>
          </Alert>
        )}

        {/* Progress indicator for answered questions */}
        <div className="flex flex-wrap gap-2">
          {QUESTIONS.map((_, idx) => (
            <div
              key={idx}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${
                responses[QUESTIONS[idx].id as keyof ACEResponse] !== undefined
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
            value={String(responses[QUESTIONS[currentQuestion].id as keyof ACEResponse] || 0)}
            onChange={(value) =>
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
              disabled={responses[QUESTIONS[currentQuestion].id as keyof ACEResponse] === undefined}
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
export default ACEScreening;
