/**
 * IAT Internet Addiction Test Component
 *
 * Internet Addiction Test - 20 Items
 * Evidence-based internet addiction screening tool
 *
 * Reliability: α = 0.90
 * Items: 20 questions, 0-5 scale
 * Measures problematic internet use patterns
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface IATResponse {
  q1_preoccupied: number;
  q2_dissatisfied: number;
  q3_feel_good: number;
  q4_cant_stop: number;
  q5_loss_time: number;
  q6_life_stable: number;
  q7_others_complain: number;
  q8_grades_suffer: number;
  q9_check_before: number;
  q10_job_performance: number;
  q11_defensive: number;
  q12_avoid_problems: number;
  q13_isolation: number;
  q14_depressed_offline: number;
  q15_euphoric_online: number;
  q16_check_during: number;
  q17_offline_preoccupied: number;
  q18_sleep_disrupted: number;
  q19_secret_online: number;
  q20_life_revolve: number;
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
    id: 'q1_preoccupied',
    text: 'Do you feel preoccupied with the Internet (think about previous online activity or anticipate next online session)?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q2_dissatisfied',
    text: 'Do you feel the need to use the Internet with increasing amounts of time in order to achieve satisfaction?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q3_feel_good',
    text: 'Do you repeatedly feel the need to cut back on Internet use?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q4_cant_stop',
    text: 'Do you feel restless, moody, depressed, or irritable when attempting to cut down or stop Internet use?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q5_loss_time',
    text: 'Do you stay online longer than originally intended?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q6_life_stable',
    text: 'Have you jeopardized or risked the loss of a significant relationship, job, educational, or career opportunity because of the Internet?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q7_others_complain',
    text: 'Have you lied to family members, a therapist, or others to conceal the extent of your involvement with the Internet?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q8_grades_suffer',
    text: 'Do you use the Internet as a way of escaping from problems or of relieving a dysphoric mood (e.g., feelings of helplessness, guilt, anxiety, depression)?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q9_check_before',
    text: 'How often do you find that you stay online longer than you intended?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q10_job_performance',
    text: 'How often do you neglect household chores to spend more time online?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q11_defensive',
    text: 'How often do you prefer the excitement of the Internet to intimacy with your partner?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q12_avoid_problems',
    text: 'How often do you form new relationships with fellow online users?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q13_isolation',
    text: 'How often do others in your life complain to you about the amount of time you spend online?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q14_depressed_offline',
    text: 'How often do your grades or school work suffer because of the amount of time you spend online?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q15_euphoric_online',
    text: 'How often do you check your e-mail before doing something else that you need to do?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q16_check_during',
    text: 'How often does your job performance or productivity suffer because of the Internet?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q17_offline_preoccupied',
    text: 'How often do you become defensive or secretive when anyone asks you what you do online?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q18_sleep_disrupted',
    text: 'How often do you block out disturbing thoughts about your life with soothing thoughts of the Internet?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q19_secret_online',
    text: 'How often do you find yourself anticipating when you will go online again?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
  {
    id: 'q20_life_revolve',
    text: 'How often do you fear that life without the Internet would be boring, empty, and joyless?',
    options: [
      { value: 0, label: 'Does Not Apply' },
      { value: 1, label: 'Rarely' },
      { value: 2, label: 'Occasionally' },
      { value: 3, label: 'Frequently' },
      { value: 4, label: 'Often' },
      { value: 5, label: 'Always' },
    ],
  },
];

export function IATScreening() {
  const [responses, setResponses] = useState<Partial<IATResponse>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const allQuestionsAnswered = QUESTIONS.every((q) =>
    responses[q.id as keyof IATResponse] !== undefined
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
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'iat',
        responses: responses
      });
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
          <CardTitle>IAT Results</CardTitle>
          <CardDescription>
            Your internet addiction screening results are ready
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Score Display */}
          <div className="text-center p-6 bg-secondary rounded-lg">
            <div className="text-4xl font-bold mb-2">
              {result.total_score} / 100
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
              instrument. The IAT measures patterns of internet use that may be
              problematic. A high score suggests you may benefit from speaking
              with a mental health professional for proper evaluation. Only a
              licensed healthcare provider can diagnose internet addiction disorder.
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
        <CardTitle>IAT Internet Addiction Test</CardTitle>
        <CardDescription>
          Internet Addiction Test - 20 Items
          <br />
          <span className="text-xs text-muted-foreground">
            To assess your level of internet use, please think about your online behavior over the past year and answer the following questions.
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

        {/* Progress indicator for answered questions */}
        <div className="flex flex-wrap gap-2">
          {QUESTIONS.map((_, idx) => (
            <div
              key={idx}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${
                responses[QUESTIONS[idx].id as keyof IATResponse] !== undefined
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
            value={String(responses[QUESTIONS[currentQuestion].id as keyof IATResponse] || 0)}
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
              disabled={responses[QUESTIONS[currentQuestion].id as keyof IATResponse] === undefined}
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
export default IATScreening;
