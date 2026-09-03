/**
 * EAT-26 (Eating Attitudes Test) Screening Component
 *
 * 26-item assessment for eating disorder screening
 * 6-point scale (Always to Never)
 * Includes behavioral questions for referral determination
 *
 * Reliability: α = 0.83
 * Clinical utility: High - widely used eating disorder screening tool
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Progress from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Apple, AlertTriangle, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import api from '@/services/api';

interface EAT26Response {
  [key: number]: number; // Item 1-26, scale 0-5
}

interface BehavioralQuestions {
  weight_loss_6months: boolean;
  binge_eating: string;
  vomiting: string;
  laxatives: string;
  exercise: string;
  bmi_concern: boolean;
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
  subscale_scores: {
    dieting: number;
    bulimia: number;
    oral_control: number;
  };
}

const EAT26_QUESTIONS = [
  {
    id: 1,
    text: 'Am terrified about being overweight',
    category: 'Dieting',
  },
  {
    id: 2,
    text: 'Avoid eating when I am hungry',
    category: 'Oral Control',
  },
  {
    id: 3,
    text: 'Find myself preoccupied with food',
    category: 'Bulimia',
  },
  {
    id: 4,
    text: 'Have gone on eating binges where I feel that I may not be able to stop',
    category: 'Bulimia',
  },
  {
    id: 5,
    text: 'Cut my food into small pieces',
    category: 'Oral Control',
  },
  {
    id: 6,
    text: 'Aware of the calorie content of foods that I eat',
    category: 'Dieting',
  },
  {
    id: 7,
    text: 'Particularly avoid food with a high carbohydrate content',
    category: 'Dieting',
  },
  {
    id: 8,
    text: 'Feel that others would prefer if I ate more',
    category: 'Oral Control',
  },
  {
    id: 9,
    text: 'Vomit after I have eaten',
    category: 'Bulimia',
  },
  {
    id: 10,
    text: 'Feel extremely guilty after eating',
    category: 'Dieting',
  },
  {
    id: 11,
    text: 'Am preoccupied with a desire to be thinner',
    category: 'Dieting',
  },
  {
    id: 12,
    text: 'Think about burning up calories when I exercise',
    category: 'Dieting',
  },
  {
    id: 13,
    text: 'Other people think that I am too thin',
    category: 'Oral Control',
  },
  {
    id: 14,
    text: 'Am preoccupied with the thought of having fat on my body',
    category: 'Dieting',
  },
  {
    id: 15,
    text: 'Take longer than others to eat my meals',
    category: 'Oral Control',
  },
  {
    id: 16,
    text: 'Avoid foods with sugar in them',
    category: 'Dieting',
  },
  {
    id: 17,
    text: 'Eat diet foods',
    category: 'Dieting',
  },
  {
    id: 18,
    text: 'Feel that food controls my life',
    category: 'Bulimia',
  },
  {
    id: 19,
    text: 'Display self-control around food',
    category: 'Oral Control',
  },
  {
    id: 20,
    text: 'Feel that others pressure me to eat',
    category: 'Oral Control',
  },
  {
    id: 21,
    text: 'Give too much time and thought to food',
    category: 'Bulimia',
  },
  {
    id: 22,
    text: 'Feel uncomfortable after eating sweets',
    category: 'Dieting',
  },
  {
    id: 23,
    text: 'Engage in dieting behavior',
    category: 'Dieting',
  },
  {
    id: 24,
    text: 'Like my stomach to be empty',
    category: 'Dieting',
  },
  {
    id: 25,
    text: 'Have the impulse to vomit after meals',
    category: 'Bulimia',
  },
  {
    id: 26,
    text: 'Enjoy trying new rich foods',
    category: 'Oral Control',
    reverse: true, // Reverse scored
  },
];

const RESPONSE_OPTIONS = [
  { value: 3, label: 'Always', description: 'Applies to me always' },
  { value: 2, label: 'Usually', description: 'Applies to me usually' },
  { value: 1, label: 'Often', description: 'Applies to me often' },
  { value: 0, label: 'Sometimes', description: 'Applies to me sometimes' },
  { value: 0, label: 'Rarely', description: 'Applies to me rarely' },
  { value: 0, label: 'Never', description: 'Applies to me never' },
];

const BINGE_EATING_OPTIONS = [
  'Never',
  'Less than once a month',
  '1-3 times per month',
  'Once a week',
  '2-6 times per week',
  'Daily or more',
];

const EXERCISE_OPTIONS = [
  'Never',
  'Less than once a week',
  '1-2 times per week',
  '3-5 times per week',
  'Daily',
  'More than once a day',
];

function EAT26Screening() {
  const [responses, setResponses] = useState<EAT26Response>({});
  const [behavioralQuestions, setBehavioralQuestions] = useState<BehavioralQuestions>({
    weight_loss_6months: false,
    binge_eating: 'Never',
    vomiting: 'Never',
    laxatives: 'Never',
    exercise: 'Never',
    bmi_concern: false,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const progress = (Object.keys(responses).length / EAT26_QUESTIONS.length) * 100;
  const currentQuestionComplete = responses[EAT26_QUESTIONS[currentQuestion]?.id] !== undefined;
  const allQuestionsComplete = EAT26_QUESTIONS.every((q) => responses[q.id] !== undefined);

  const handleResponse = (questionId: number, value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }));
    setError(null);
  };

  const handleNext = () => {
    if (currentQuestion < EAT26_QUESTIONS.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    if (!allQuestionsComplete) {
      setError('Please complete all questions before submitting.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        responses: responses,
        behavioral_questions: behavioralQuestions,
      };

      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'eat26',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to submit assessment. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResponses({});
    setBehavioralQuestions({
      weight_loss_6months: false,
      binge_eating: 'Never',
      vomiting: 'Never',
      laxatives: 'Never',
      exercise: 'Never',
      bmi_concern: false,
    });
    setResult(null);
    setError(null);
    setCurrentQuestion(0);
  };

  // Results view
  if (result) {
    const referralThreshold = 20;
    const requiresReferral = result.total_score >= referralThreshold || result.crisis_alert;

    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Header */}
        <Card className={`border-2 ${
          result.crisis_alert ? 'border-red-500 bg-red-50' : 'border-green-500 bg-green-50'
        }`}>
          <CardHeader>
            <div className="flex items-center gap-3">
              {result.crisis_alert ? (
                <AlertTriangle className="h-8 w-8 text-red-600" />
              ) : (
                <CheckCircle className="h-8 w-8 text-green-600" />
              )}
              <div>
                <CardTitle className="text-2xl">
                  {result.crisis_alert ? 'Crisis Alert' : 'Assessment Complete'}
                </CardTitle>
                <CardDescription className="text-base">
                  Eating Attitudes Test (EAT-26)
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center py-4">
                <p className="text-sm text-gray-600 mb-2">Total Score (0-78)</p>
                <p className="text-5xl font-bold text-gray-900">{result.total_score}</p>
                <p className="text-sm text-gray-600 mt-2">
                  Referral Threshold: {referralThreshold}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-sm text-gray-600">Severity</p>
                  <p className="text-xl font-semibold capitalize">{result.severity_level.replace('_', ' ')}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-sm text-gray-600">Risk Level</p>
                  <p className="text-xl font-semibold capitalize">{result.risk_level}</p>
                </div>
              </div>

              {/* Crisis Alert Banner */}
              {result.crisis_alert && (
                <Alert className="border-red-500 bg-red-100">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-900">
                    <strong>⚠️ Immediate Attention Required:</strong> Your responses indicate significant eating disorder
                    concerns. This may include life-threatening behaviors. Please seek medical and psychological
                    evaluation immediately.
                  </AlertDescription>
                </Alert>
              )}

              {/* Referral Recommendation */}
              {requiresReferral && !result.crisis_alert && (
                <Alert className="border-orange-500 bg-orange-50">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <AlertDescription className="text-orange-900">
                    <strong>Professional Evaluation Recommended:</strong> Your score suggests you may benefit from
                    consultation with an eating disorder specialist. Early intervention leads to better outcomes.
                  </AlertDescription>
                </Alert>
              )}

              {/* Risk Flags */}
              {result.risk_flags && result.risk_flags.length > 0 && (
                <Alert className="border-red-500 bg-red-50">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-900">
                    <strong>Risk Indicators:</strong>
                    <ul className="list-disc list-inside mt-2">
                      {result.risk_flags.map((flag, idx) => (
                        <li key={idx} className="capitalize">{flag.replace(/_/g, ' ')}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Interpretation */}
        <Card>
          <CardHeader>
            <CardTitle>Understanding Your Results</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">{result.interpretation}</p>
          </CardContent>
        </Card>

        {/* Subscale Scores */}
        <Card>
          <CardHeader>
            <CardTitle>Detailed Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2 text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-600">Dieting</p>
                <p className="text-3xl font-bold">{result.subscale_scores?.dieting || 0}</p>
                <p className="text-xs text-gray-500">Preoccupation with food/weight</p>
              </div>
              <div className="space-y-2 text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-600">Bulimia</p>
                <p className="text-3xl font-bold">{result.subscale_scores?.bulimia || 0}</p>
                <p className="text-xs text-gray-500">Binge eating & vomiting</p>
              </div>
              <div className="space-y-2 text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-600">Oral Control</p>
                <p className="text-3xl font-bold">{result.subscale_scores?.oral_control || 0}</p>
                <p className="text-xs text-gray-500">Eating control issues</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {result.recommendations.map((rec, idx) => (
                <li key={idx} className="flex gap-3">
                  <Apple className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Crisis Resources */}
        <Card className="border-red-500 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900">Eating Disorder Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <strong className="text-red-900">National Eating Disorders Association (NEDA)</strong>
                <p className="text-red-800">Helpline: (800) 931-2237</p>
                <p className="text-sm text-red-700">Available Monday-Thursday 11AM-9PM, Friday 11AM-5PM</p>
              </div>
              <div>
                <strong className="text-red-900">988 Suicide & Crisis Lifeline</strong>
                <p className="text-red-800">Call or text 988 (24/7)</p>
              </div>
              <div>
                <strong className="text-red-900">Emergency Services</strong>
                <p className="text-red-800">Call 911 if in immediate danger</p>
              </div>
              <div className="mt-4 p-3 bg-red-100 rounded-lg">
                <p className="text-sm text-red-900">
                  <strong>Medical Attention Needed:</strong> If you've lost significant weight, are purging,
                  or experiencing irregular heartbeats, seek immediate medical evaluation. Eating disorders
                  can cause serious medical complications.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex gap-4">
          <Button onClick={handleReset} variant="outline" size="sm">
            Take Assessment Again
          </Button>
          <Button onClick={() => window.print()} size="sm">
            Save Results
          </Button>
        </div>
      </div>
    );
  }

  // Behavioral Questions (shown after main questions)
  if (allQuestionsComplete && !result) {
    return (
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Apple className="h-8 w-8 text-green-600" />
              <div>
                <CardTitle className="text-2xl">Additional Information</CardTitle>
                <CardDescription>
                  These questions help us provide the most appropriate recommendations
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-8">
            {/* Weight Loss */}
            <div className="flex items-start space-x-3 p-4 border rounded-lg">
              <Checkbox
                id="weight_loss"
                checked={behavioralQuestions.weight_loss_6months}
                onCheckedChange={(checked) =>
                  setBehavioralQuestions((prev) => ({ ...prev, weight_loss_6months: checked as boolean }))
                }
              />
              <div className="flex-1">
                <Label htmlFor="weight_loss" className="text-base font-semibold cursor-pointer">
                  Have you lost 20 pounds or more in the past 6 months?
                </Label>
                <p className="text-sm text-gray-600 mt-1">This helps us understand recent changes</p>
              </div>
            </div>

            {/* Binge Eating */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">
                How often do you experience episodes of binge eating?
              </Label>
              <RadioGroup
                value={behavioralQuestions.binge_eating}
                onChange={(value) =>
                  setBehavioralQuestions((prev) => ({ ...prev, binge_eating: value }))
                }
              >
                {BINGE_EATING_OPTIONS.map((option) => (
                  <div key={option} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value={option} id={`binge-${option}`} />
                    <Label htmlFor={`binge-${option}`} className="cursor-pointer flex-1">
                      {option}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {/* Vomiting */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">
                How often do you self-induce vomiting?
              </Label>
              <RadioGroup
                value={behavioralQuestions.vomiting}
                onChange={(value) =>
                  setBehavioralQuestions((prev) => ({ ...prev, vomiting: value }))
                }
              >
                {BINGE_EATING_OPTIONS.map((option) => (
                  <div key={option} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value={option} id={`vomit-${option}`} />
                    <Label htmlFor={`vomit-${option}`} className="cursor-pointer flex-1">
                      {option}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {/* Laxatives */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">
                How often do you use laxatives for weight control?
              </Label>
              <RadioGroup
                value={behavioralQuestions.laxatives}
                onChange={(value) =>
                  setBehavioralQuestions((prev) => ({ ...prev, laxatives: value }))
                }
              >
                {BINGE_EATING_OPTIONS.map((option) => (
                  <div key={option} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value={option} id={`laxative-${option}`} />
                    <Label htmlFor={`laxative-${option}`} className="cursor-pointer flex-1">
                      {option}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {/* Exercise */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">
                How often do you exercise specifically to burn calories?
              </Label>
              <RadioGroup
                value={behavioralQuestions.exercise}
                onChange={(value) =>
                  setBehavioralQuestions((prev) => ({ ...prev, exercise: value }))
                }
              >
                {EXERCISE_OPTIONS.map((option) => (
                  <div key={option} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value={option} id={`exercise-${option}`} />
                    <Label htmlFor={`exercise-${option}`} className="cursor-pointer flex-1">
                      {option}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </div>

            {/* BMI Concern */}
            <div className="flex items-start space-x-3 p-4 border rounded-lg">
              <Checkbox
                id="bmi_concern"
                checked={behavioralQuestions.bmi_concern}
                onCheckedChange={(checked) =>
                  setBehavioralQuestions((prev) => ({ ...prev, bmi_concern: checked as boolean }))
                }
              />
              <div className="flex-1">
                <Label htmlFor="bmi_concern" className="text-base font-semibold cursor-pointer">
                  Are you currently concerned about your BMI or weight?
                </Label>
                <p className="text-sm text-gray-600 mt-1">This helps us understand your concerns</p>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleSubmit}
              disabled={loading}
              size="sm"
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit Assessment'
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main assessment view
  const question = EAT26_QUESTIONS[currentQuestion];

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Apple className="h-8 w-8 text-green-600" />
            <div>
              <CardTitle className="text-2xl">Eating Attitudes Assessment</CardTitle>
              <CardDescription>
                Eating Attitudes Test (EAT-26) • Question {currentQuestion + 1} of {EAT26_QUESTIONS.length}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-gray-600 mt-2 text-center">
            {Math.round(progress)}% Complete
          </p>
        </CardContent>
      </Card>

      {/* Question Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xl mb-2">
                {question.text}
              </CardTitle>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                question.category === 'Dieting'
                  ? 'bg-orange-100 text-orange-800'
                  : question.category === 'Bulimia'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-purple-100 text-purple-800'
              }`}>
                {question.category}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioGroup
            value={responses[question.id]?.toString()}
            onChange={(value) => handleResponse(question.id, parseInt(value))}
          >
            {RESPONSE_OPTIONS.map((option, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 border cursor-pointer"
              >
                <RadioGroupItem value={option.value.toString()} id={`option-${idx}`} />
                <div className="flex-1">
                  <Label htmlFor={`option-${idx}`} className="font-medium cursor-pointer">
                    {option.label}
                  </Label>
                  <p className="text-sm text-gray-600">{option.description}</p>
                </div>
              </div>
            ))}
          </RadioGroup>

          {/* Error Message */}
          {error && (
            <Alert variant="error">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <Button
          onClick={handlePrevious}
          disabled={currentQuestion === 0}
          variant="outline"
          size="sm"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>

        {currentQuestion < EAT26_QUESTIONS.length - 1 ? (
          <Button
            onClick={handleNext}
            disabled={!currentQuestionComplete}
            size="sm"
          >
            Next
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        ) : (
          <Button
            onClick={() => {}}
            disabled={!allQuestionsComplete}
            size="sm"
            className="bg-green-600 hover:bg-green-700"
          >
            Continue to Additional Questions
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>

      {/* Quick Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Navigation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-2">
            {EAT26_QUESTIONS.map((q, idx) => {
              const isComplete = responses[q.id] !== undefined;
              const isCurrent = idx === currentQuestion;

              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(idx)}
                  className={`w-10 h-10 rounded-lg font-medium text-sm transition-all ${
                    isCurrent
                      ? 'bg-green-600 text-white scale-110'
                      : isComplete
                      ? 'bg-green-100 text-green-800 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
export default EAT26Screening;
