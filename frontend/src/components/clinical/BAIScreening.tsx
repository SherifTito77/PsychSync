/**
 * BAI (Beck Anxiety Inventory) Screening Component
 *
 * 21-item assessment for anxiety severity
 * Each item rated 0-3 based on symptom severity over past week
 *
 * Reliability: α = 0.92
 * Clinical utility: High - distinguishes anxiety from depression
 *
 * IMPORTANT: BAI measures SEVERITY of anxiety symptoms, not frequency
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Progress from '@/components/ui/progress';
import { Loader2, Brain, AlertTriangle, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import api from '@/services/api';

interface BAIResponse {
  [key: string]: number;
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
    cognitive_anxiety: number;
    somatic_anxiety: number;
    panic_severity: number;
  };
}

const BAI_QUESTIONS = [
  {
    id: '1',
    text: 'Numbness or tingling',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '2',
    text: 'Feeling hot',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '3',
    text: 'Wobbliness in legs',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '4',
    text: 'Unable to relax',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Cognitive',
  },
  {
    id: '5',
    text: 'Fear of worst happening',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '6',
    text: 'Dizzy or lightheaded',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '7',
    text: 'Heart pounding or racing',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '8',
    text: 'Unsteady',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '9',
    text: 'Terrified or afraid',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Cognitive',
  },
  {
    id: '10',
    text: 'Nervous',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Cognitive',
  },
  {
    id: '11',
    text: 'Feeling of choking',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '12',
    text: 'Hands trembling',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '13',
    text: 'Shaky / unsteady',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '14',
    text: 'Fear of losing control',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '15',
    text: 'Difficulty breathing',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '16',
    text: 'Fear of dying',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '17',
    text: 'Scared',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '18',
    text: 'Indigestion / discomfort in stomach',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '19',
    text: 'Faint / lightheaded',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
  {
    id: '20',
    text: 'Face flushed',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Panic',
  },
  {
    id: '21',
    text: 'Sweating (not due to heat)',
    options: [
      { value: 0, text: 'Not at all' },
      { value: 1, text: 'Mildly, it didn\'t bother me much' },
      { value: 2, text: 'Moderately - it wasn\'t pleasant at times' },
      { value: 3, text: 'Severely - it bothered me a lot' },
    ],
    category: 'Somatic',
  },
];

function BAIScreening() {
  const [responses, setResponses] = useState<BAIResponse>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const progress = (Object.keys(responses).length / BAI_QUESTIONS.length) * 100;

  const currentQuestionComplete = responses[BAI_QUESTIONS[currentQuestion]?.id] !== undefined;

  const allQuestionsComplete = BAI_QUESTIONS.every((q) => responses[q.id] !== undefined);

  const handleResponse = (questionId: string, value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }));
    setError(null);
  };

  const handleNext = () => {
    if (currentQuestion < BAI_QUESTIONS.length - 1) {
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
      const response = await api.post('/clinical/BAI/submit', responses);
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
    setResult(null);
    setError(null);
    setCurrentQuestion(0);
  };

  // Results view
  if (result) {
    return (
      <div className='max-w-4xl mx-auto p-6 space-y-6'>
        {/* Header */}
        <Card
          className={`border-2 ${
            result.crisis_alert
              ? 'border-red-500 bg-red-50'
              : 'border-green-500 bg-green-50'
          }`}
        >
          <CardHeader>
            <div className='flex items-center gap-3'>
              {result.crisis_alert ? (
                <AlertTriangle className='h-8 w-8 text-red-600' />
              ) : (
                <CheckCircle className='h-8 w-8 text-green-600' />
              )}
              <div>
                <CardTitle className='text-2xl'>
                  {result.crisis_alert ? '⚠️ Crisis Alert' : 'Assessment Complete'}
                </CardTitle>
                <CardDescription className='text-base'>
                  Beck Anxiety Inventory (BAI)
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className='space-y-4'>
              <div className='text-center py-4'>
                <p className='text-sm text-gray-600 mb-2'>Total Score (0-63)</p>
                <p className='text-5xl font-bold text-gray-900'>{result.total_score}</p>
              </div>

              <div className='grid grid-cols-2 gap-4 text-center'>
                <div className='bg-white p-4 rounded-lg shadow'>
                  <p className='text-sm text-gray-600'>Severity</p>
                  <p className='text-xl font-semibold capitalize'>
                    {result.severity_level.replace(/_/g, ' ')}
                  </p>
                </div>
                <div className='bg-white p-4 rounded-lg shadow'>
                  <p className='text-sm text-gray-600'>Risk Level</p>
                  <p className='text-xl font-semibold capitalize'>{result.risk_level}</p>
                </div>
              </div>

              {/* Crisis Alert Banner */}
              {result.crisis_alert && (
                <Alert className='border-red-500 bg-red-100'>
                  <AlertTriangle className='h-4 w-4 text-red-600' />
                  <AlertDescription className='text-red-900'>
                    <strong>⚠️ Crisis Alert:</strong> Your responses indicate severe anxiety with
                    potential panic symptoms. <strong
                      >Please seek immediate help from a mental health professional or crisis
                      service.</strong
                    >
                  </AlertDescription>
                </Alert>
              )}

              {/* Risk Flags */}
              {result.risk_flags && result.risk_flags.length > 0 && (
                <Alert className='border-orange-500 bg-orange-50'>
                  <AlertTriangle className='h-4 w-4 text-orange-600' />
                  <AlertDescription className='text-orange-900'>
                    <strong>Risk Indicators:</strong>
                    <ul className='list-disc list-inside mt-2'>
                      {result.risk_flags.map((flag, idx) => (
                        <li key={idx} className='capitalize'>
                          {flag.replace(/_/g, ' ')}
                        </li>
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
            <p className='text-gray-700 leading-relaxed'>{result.interpretation}</p>
          </CardContent>
        </Card>

        {/* Subscale Scores */}
        <Card>
          <CardHeader>
            <CardTitle>Anxiety Symptom Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='grid grid-cols-3 gap-4'>
              <div className='text-center p-4 bg-blue-50 rounded-lg'>
                <p className='text-sm font-medium text-gray-600 mb-2'>Cognitive Anxiety</p>
                <p className='text-3xl font-bold text-blue-700'>
                  {result.subscale_scores?.cognitive_anxiety || 0}/45
                </p>
                <p className='text-xs text-gray-500 mt-2'>
                  Nervous, fear, unable to relax
                </p>
              </div>
              <div className='text-center p-4 bg-purple-50 rounded-lg'>
                <p className='text-sm font-medium text-gray-600 mb-2'>Somatic Anxiety</p>
                <p className='text-3xl font-bold text-purple-700'>
                  {result.subscale_scores?.somatic_anxiety || 0}/24
                </p>
                <p className='text-xs text-gray-500 mt-2'>
                  Physical symptoms, trembling
                </p>
              </div>
              <div className='text-center p-4 bg-red-50 rounded-lg'>
                <p className='text-sm font-medium text-gray-600 mb-2'>Panic Symptoms</p>
                <p className='text-3xl font-bold text-red-700'>
                  {result.subscale_scores?.panic_severity || 0}/30
                </p>
                <p className='text-xs text-gray-500 mt-2'>
                  Heart racing, difficulty breathing
                </p>
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
            <ul className='space-y-3'>
              {result.recommendations.map((rec, idx) => (
                <li key={idx} className='flex gap-3'>
                  <Brain className='h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5' />
                  <span className='text-gray-700'>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Crisis Resources if needed */}
        {result.crisis_alert && (
          <Card className='border-red-500 bg-red-50'>
            <CardHeader>
              <CardTitle className='text-red-900'>🚨 Immediate Support Resources</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-4'>
                <div className='p-4 bg-white rounded-lg'>
                  <strong className='text-red-900 block text-lg'>988 Suicide & Crisis Lifeline</strong>
                  <p className='text-red-800'>Call or text 988 (24/7, free & confidential)</p>
                </div>
                <div className='p-4 bg-white rounded-lg'>
                  <strong className='text-red-900 block text-lg'>Crisis Text Line</strong>
                  <p className='text-red-800'>Text HOME to 741741 (24/7)</p>
                </div>
                <div className='p-4 bg-white rounded-lg'>
                  <strong className='text-red-900 block text-lg'>Anxiety & Depression Association of America</strong>
                  <p className='text-red-800'>Call 240-485-1001 or visit <a href='https://adaa.org' target='_blank' rel='noopener noreferrer' className='underline'>adaa.org</a></p>
                </div>
                <div className='p-4 bg-white rounded-lg'>
                  <strong className='text-red-900 block text-lg'>Emergency Services</strong>
                  <p className='text-red-800'>Call 911 if in immediate danger</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className='flex gap-4'>
          <Button onClick={handleReset} variant='outline' size='large'>
            Take Assessment Again
          </Button>
          <Button onClick={() => window.print()} size='large'>
            Save Results
          </Button>
        </div>
      </div>
    );
  }

  // Assessment view
  const question = BAI_QUESTIONS[currentQuestion];
  const currentResponse = responses[question.id];

  return (
    <div className='max-w-3xl mx-auto p-6 space-y-6'>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className='flex items-center gap-3'>
            <Brain className='h-8 w-8 text-purple-600' />
            <div>
              <CardTitle className='text-2xl'>Anxiety Assessment (BAI)</CardTitle>
              <CardDescription>
                Beck Anxiety Inventory • Question {currentQuestion + 1} of {BAI_QUESTIONS.length}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={progress} className='h-2' />
          <p className='text-sm text-gray-600 mt-2 text-center'>
            {Math.round(progress)}% Complete
          </p>
        </CardContent>
      </Card>

      {/* Important Note */}
      <Card className='border-blue-200 bg-blue-50'>
        <CardContent className='pt-6'>
          <p className='text-sm text-blue-900'>
            <strong>Important:</strong> This assessment measures how much each symptom has bothered
            you during the <strong>past week</strong>, including today. Rate each symptom based on
            how much it has distressed you, not how often you experienced it.
          </p>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className='border-gray-200 bg-gray-50'>
        <CardContent className='pt-6'>
          <p className='text-sm text-gray-700'>
            <strong>Disclaimer:</strong> This assessment is for informational purposes only and is
            not a substitute for professional medical advice, diagnosis, or treatment. If you are
            experiencing a mental health emergency, please call 988 or 911 immediately.
          </p>
        </CardContent>
      </Card>

      {/* Question Card */}
      <Card>
        <CardHeader>
          <div className='flex items-start justify-between'>
            <div className='flex-1'>
              <CardTitle className='text-xl mb-2'>{question.text}</CardTitle>
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  question.category === 'Panic'
                    ? 'bg-red-100 text-red-800'
                    : question.category === 'Cognitive'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-purple-100 text-purple-800'
                }`}
              >
                {question.category}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent className='space-y-4'>
          <RadioGroup
            value={currentResponse?.toString()}
            onChange={(value) => handleResponse(question.id, parseInt(value))}
          >
            {question.options.map((option) => (
              <div
                key={option.value}
                className='flex items-start space-x-3 p-4 rounded-lg hover:bg-gray-50 border transition-colors'
              >
                <RadioGroupItem value={option.value.toString()} id={`option-${option.value}`} />
                <div className='flex-1'>
                  <Label
                    htmlFor={`option-${option.value}`}
                    className='font-medium cursor-pointer text-base'
                  >
                    {option.text}
                  </Label>
                </div>
              </div>
            ))}
          </RadioGroup>

          {/* Error Message */}
          {error && (
            <Alert variant='error'>
              <AlertTriangle className='h-4 w-4' />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className='flex justify-between items-center'>
        <Button
          onClick={handlePrevious}
          disabled={currentQuestion === 0}
          variant='outline'
          size='large'
        >
          <ArrowLeft className='h-4 w-4 mr-2' />
          Previous
        </Button>

        {currentQuestion < BAI_QUESTIONS.length - 1 ? (
          <Button onClick={handleNext} disabled={!currentQuestionComplete} size='large'>
            Next
            <ArrowRight className='h-4 w-4 ml-2' />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={!allQuestionsComplete || loading}
            size='large'
            className={allQuestionsComplete ? 'bg-purple-600 hover:bg-purple-700' : ''}
          >
            {loading ? (
              <>
                <Loader2 className='h-4 w-4 mr-2 animate-spin' />
                Submitting...
              </>
            ) : (
              'Submit Assessment'
            )}
          </Button>
        )}
      </div>

      {/* Quick Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className='text-lg'>Quick Navigation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='grid grid-cols-7 gap-2'>
            {BAI_QUESTIONS.map((q, idx) => {
              const isComplete = responses[q.id] !== undefined;
              const isCurrent = idx === currentQuestion;

              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(idx)}
                  className={`w-10 h-10 rounded-lg font-medium text-sm transition-all ${
                    isCurrent
                      ? 'bg-purple-600 text-white scale-110'
                      : isComplete
                      ? 'bg-green-100 text-green-800 hover:bg-green-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  title={q.text}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
          <div className='flex items-center gap-4 mt-3 text-xs text-gray-600'>
            <div className='flex items-center gap-1'>
              <div className='w-3 h-3 bg-gray-100 rounded' />
              <span>Not started</span>
            </div>
            <div className='flex items-center gap-1'>
              <div className='w-3 h-3 bg-green-100 rounded' />
              <span>Complete</span>
            </div>
            <div className='flex items-center gap-1'>
              <div className='w-3 h-3 bg-purple-600 rounded' />
              <span>Current</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default BAIScreening;
