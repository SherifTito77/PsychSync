/**
 * BDI-II (Beck Depression Inventory-II) Screening Component
 *
 * 21-item assessment for depression severity
 * Each item rated 0-3 based on symptom severity over past 2 weeks
 *
 * Reliability: α = 0.91
 * Test-retest: r = 0.93
 * Clinical utility: High - gold standard for depression assessment
 *
 * CRITICAL: Item 9 assesses suicidal thoughts - requires immediate attention if score ≥ 2
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

interface BDI2Response {
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
    cognitive: number;
    affective: number;
    somatic: number;
  };
}

const BDI2_QUESTIONS = [
  {
    id: '1',
    text: 'Sadness',
    options: [
      { value: 0, text: 'I do not feel sad' },
      { value: 1, text: 'I feel sad much of the time' },
      { value: 2, text: 'I am sad all the time' },
      { value: 3, text: 'I am so sad or unhappy that I can\'t stand it' },
    ],
    category: 'Affective',
  },
  {
    id: '2',
    text: 'Pessimism',
    options: [
      { value: 0, text: 'I am not discouraged about my future' },
      { value: 1, text: 'I feel more discouraged about my future than I used to be' },
      { value: 2, text: 'I do not expect things to work out for me' },
      { value: 3, text: 'I feel my future is hopeless and will only get worse' },
    ],
    category: 'Cognitive',
  },
  {
    id: '3',
    text: 'Past Failure',
    options: [
      { value: 0, text: 'I do not feel like a failure' },
      { value: 1, text: 'I have failed more than I should have' },
      { value: 2, text: 'As I look back, I see a lot of failures' },
      { value: 3, text: 'I feel I am a total failure as a person' },
    ],
    category: 'Cognitive',
  },
  {
    id: '4',
    text: 'Loss of Pleasure',
    options: [
      { value: 0, text: 'I get as much pleasure as I ever did from things I enjoy' },
      { value: 1, text: 'I don\'t enjoy things as much as I used to' },
      { value: 2, text: 'I get very little pleasure from things I used to enjoy' },
      { value: 3, text: 'I can\'t get any pleasure from things I used to enjoy' },
    ],
    category: 'Affective',
  },
  {
    id: '5',
    text: 'Guilty Feelings',
    options: [
      { value: 0, text: 'I don\'t feel particularly guilty' },
      { value: 1, text: 'I feel guilty a good part of the time' },
      { value: 2, text: 'I feel quite guilty most of the time' },
      { value: 3, text: 'I feel guilty all of the time' },
    ],
    category: 'Cognitive',
  },
  {
    id: '6',
    text: 'Punishment Feelings',
    options: [
      { value: 0, text: 'I don\'t feel I am being punished' },
      { value: 1, text: 'I feel I may be punished' },
      { value: 2, text: 'I expect to be punished' },
      { value: 3, text: 'I feel I am being punished' },
    ],
    category: 'Cognitive',
  },
  {
    id: '7',
    text: 'Self-Dislike',
    options: [
      { value: 0, text: 'I feel the same about myself as ever' },
      { value: 1, text: 'I have lost confidence in myself' },
      { value: 2, text: 'I am disappointed in myself' },
      { value: 3, text: 'I dislike myself' },
    ],
    category: 'Cognitive',
  },
  {
    id: '8',
    text: 'Self-Criticalness',
    options: [
      { value: 0, text: 'I don\'t criticize or blame myself more than usual' },
      { value: 1, text: 'I am more critical of myself than I used to be' },
      { value: 2, text: 'I criticize myself for all of my faults' },
      { value: 3, text: 'I blame myself for everything bad that happens' },
    ],
    category: 'Cognitive',
  },
  {
    id: '9',
    text: 'Suicidal Thoughts or Wishes',
    options: [
      { value: 0, text: 'I don\'t have any thoughts of killing myself' },
      { value: 1, text: 'I have thoughts of killing myself, but I would not carry them out' },
      { value: 2, text: 'I would like to kill myself' },
      { value: 3, text: 'I would kill myself if I had the chance' },
    ],
    category: 'CRITICAL',
    isCritical: true,
  },
  {
    id: '10',
    text: 'Crying',
    options: [
      { value: 0, text: 'I don\'t cry any more than I used to' },
      { value: 1, text: 'I cry more than I used to' },
      { value: 2, text: 'I cry over every little thing' },
      { value: 3, text: 'I feel like crying, but I can\'t' },
    ],
    category: 'Affective',
  },
  {
    id: '11',
    text: 'Agitation',
    options: [
      { value: 0, text: 'I am no more restless or wound up than usual' },
      { value: 1, text: 'I feel more restless or wound up than usual' },
      { value: 2, text: 'I am so restless or agitated, it\'s hard to stay still' },
      { value: 3, text: 'I am so restless or agitated that I have to keep moving or doing something' },
    ],
    category: 'Somatic',
  },
  {
    id: '12',
    text: 'Loss of Interest',
    options: [
      { value: 0, text: 'I have not lost interest in other people or activities' },
      { value: 1, text: 'I am less interested in other people or things than before' },
      { value: 2, text: 'I have lost most of my interest in other people or things' },
      { value: 3, text: 'It\'s hard to get interested in anything' },
    ],
    category: 'Affective',
  },
  {
    id: '13',
    text: 'Indecisiveness',
    options: [
      { value: 0, text: 'I make decisions about as well as ever' },
      { value: 1, text: 'I put off making decisions more than I used to' },
      { value: 2, text: 'I have greater difficulty making decisions than before' },
      { value: 3, text: 'I can\'t make any decisions at all anymore' },
    ],
    category: 'Cognitive',
  },
  {
    id: '14',
    text: 'Worthlessness',
    options: [
      { value: 0, text: 'I do not feel I am worthless' },
      { value: 1, text: 'I don\'t consider myself as worthwhile and useful as I used to' },
      { value: 2, text: 'I feel I am not very worthwhile' },
      { value: 3, text: 'I feel utterly worthless' },
    ],
    category: 'Cognitive',
  },
  {
    id: '15',
    text: 'Loss of Energy',
    options: [
      { value: 0, text: 'I have as much energy as ever' },
      { value: 1, text: 'I have less energy than I used to have' },
      { value: 2, text: 'I don\'t have enough energy to do very much' },
      { value: 3, text: 'I don\'t have enough energy to do anything' },
    ],
    category: 'Somatic',
  },
  {
    id: '16',
    text: 'Changes in Sleeping Pattern',
    options: [
      { value: 0, text: 'I have not experienced any change in my sleeping' },
      { value: 1, text: 'I sleep somewhat more or less than usual' },
      { value: 2, text: 'I sleep a lot more or a lot less than usual' },
      { value: 3, text: 'I sleep most of the day or can\'t sleep at all' },
    ],
    category: 'Somatic',
  },
  {
    id: '17',
    text: 'Irritability',
    options: [
      { value: 0, text: 'I am not more irritable than usual' },
      { value: 1, text: 'I am more irritable than usual' },
      { value: 2, text: 'I am much more irritable than usual' },
      { value: 3, text: 'I am irritable all the time' },
    ],
    category: 'Somatic',
  },
  {
    id: '18',
    text: 'Changes in Appetite',
    options: [
      { value: 0, text: 'I have not experienced any change in my appetite' },
      { value: 1, text: 'My appetite is somewhat less or greater than usual' },
      { value: 2, text: 'My appetite is much less or much greater than usual' },
      { value: 3, text: 'I have no appetite at all or can\'t stop eating' },
    ],
    category: 'Somatic',
  },
  {
    id: '19',
    text: 'Concentration Difficulty',
    options: [
      { value: 0, text: 'I can concentrate as well as ever' },
      { value: 1, text: 'I can\'t concentrate as well as usual' },
      { value: 2, text: 'It\'s hard to keep my mind on anything for very long' },
      { value: 3, text: 'I find I can\'t concentrate on anything' },
    ],
    category: 'Cognitive',
  },
  {
    id: '20',
    text: 'Tiredness or Fatigue',
    options: [
      { value: 0, text: 'I am no more tired or fatigued than usual' },
      { value: 1, text: 'I get more tired or fatigued more easily than usual' },
      { value: 2, text: 'I am too tired or fatigued to do a lot of the things I used to do' },
      { value: 3, text: 'I am too tired or fatigued to do most of the things I used to do' },
    ],
    category: 'Somatic',
  },
  {
    id: '21',
    text: 'Loss of Interest in Sex',
    options: [
      { value: 0, text: 'I have not noticed any recent change in my interest in sex' },
      { value: 1, text: 'I am less interested in sex than I used to be' },
      { value: 2, text: 'I am much less interested in sex now' },
      { value: 3, text: 'I have lost interest in sex completely' },
    ],
    category: 'Somatic',
  },
];

function BDI2Screening() {
  const [responses, setResponses] = useState<BDI2Response>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const progress = (Object.keys(responses).length / BDI2_QUESTIONS.length) * 100;

  const currentQuestionComplete = responses[BDI2_QUESTIONS[currentQuestion]?.id] !== undefined;

  const allQuestionsComplete = BDI2_QUESTIONS.every((q) => responses[q.id] !== undefined);

  const handleResponse = (questionId: string, value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }));
    setError(null);
  };

  const handleNext = () => {
    if (currentQuestion < BDI2_QUESTIONS.length - 1) {
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
      const response = await api.post('/clinical/BDI2/submit', responses);
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
                  Beck Depression Inventory-II (BDI-II)
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
                    <strong>⚠️ Crisis Alert:</strong> Your responses indicate severe depression
                    with possible suicidal ideation. <strong>Please seek immediate help from a
                    mental health professional or crisis service.</strong>
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
            <CardTitle>Symptom Dimension Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='grid grid-cols-3 gap-4'>
              <div className='text-center p-4 bg-blue-50 rounded-lg'>
                <p className='text-sm font-medium text-gray-600 mb-2'>Cognitive Symptoms</p>
                <p className='text-3xl font-bold text-blue-700'>
                  {result.subscale_scores?.cognitive || 0}/30
                </p>
                <p className='text-xs text-gray-500 mt-2'>
                  Negative thoughts, guilt, worthlessness
                </p>
              </div>
              <div className='text-center p-4 bg-purple-50 rounded-lg'>
                <p className='text-sm font-medium text-gray-600 mb-2'>Affective Symptoms</p>
                <p className='text-3xl font-bold text-purple-700'>
                  {result.subscale_scores?.affective || 0}/21
                </p>
                <p className='text-xs text-gray-500 mt-2'>
                  Sadness, loss of pleasure, crying
                </p>
              </div>
              <div className='text-center p-4 bg-green-50 rounded-lg'>
                <p className='text-sm font-medium text-gray-600 mb-2'>Somatic Symptoms</p>
                <p className='text-3xl font-bold text-green-700'>
                  {result.subscale_scores?.somatic || 0}/12
                </p>
                <p className='text-xs text-gray-500 mt-2'>
                  Sleep, appetite, energy changes
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
                  <strong className='text-red-900 block text-lg'>Emergency Services</strong>
                  <p className='text-red-800'>Call 911 if in immediate danger</p>
                </div>
                <div className='p-4 bg-white rounded-lg'>
                  <strong className='text-red-900 block text-lg'>International Association for Suicide Prevention</strong>
                  <p className='text-red-800'>Visit <a href='https://www.iasp.info/resources/Crisis_Centres/' target='_blank' rel='noopener noreferrer' className='underline'>iasp.info</a> for international crisis centers</p>
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
  const question = BDI2_QUESTIONS[currentQuestion];
  const currentResponse = responses[question.id];

  return (
    <div className='max-w-3xl mx-auto p-6 space-y-6'>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className='flex items-center gap-3'>
            <Brain className='h-8 w-8 text-blue-600' />
            <div>
              <CardTitle className='text-2xl'>Depression Assessment (BDI-II)</CardTitle>
              <CardDescription>
                Beck Depression Inventory-II • Question {currentQuestion + 1} of{' '}
                {BDI2_QUESTIONS.length}
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

      {/* Disclaimer */}
      <Card className='border-blue-200 bg-blue-50'>
        <CardContent className='pt-6'>
          <p className='text-sm text-blue-900'>
            <strong>Disclaimer:</strong> This assessment is for informational purposes only and is
            not a substitute for professional medical advice, diagnosis, or treatment. If you are
            experiencing a mental health emergency, please call 988 or 911 immediately.
          </p>
        </CardContent>
      </Card>

      {/* Question Card */}
      <Card className={question.isCritical ? 'border-red-300 bg-red-50' : ''}>
        <CardHeader>
          <div className='flex items-start justify-between'>
            <div className='flex-1'>
              <div className='flex items-center gap-3 mb-2'>
                <CardTitle className='text-xl'>{question.text}</CardTitle>
                {question.isCritical && (
                  <span className='px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-bold'>
                    CRITICAL
                  </span>
                )}
              </div>
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  question.category === 'CRITICAL'
                    ? 'bg-red-100 text-red-800'
                    : question.category === 'Cognitive'
                    ? 'bg-blue-100 text-blue-800'
                    : question.category === 'Affective'
                    ? 'bg-purple-100 text-purple-800'
                    : 'bg-green-100 text-green-800'
                }`}
              >
                {question.category}
              </span>
              {question.isCritical && (
                <p className='text-sm text-red-700 mt-2'>
                  <strong>Important:</strong> This question assesses suicidal thoughts. Your honest
                  response helps us provide appropriate support.
                </p>
              )}
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

        {currentQuestion < BDI2_QUESTIONS.length - 1 ? (
          <Button onClick={handleNext} disabled={!currentQuestionComplete} size='large'>
            Next
            <ArrowRight className='h-4 w-4 ml-2' />
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            disabled={!allQuestionsComplete || loading}
            size='large'
            className={allQuestionsComplete ? 'bg-blue-600 hover:bg-blue-700' : ''}
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
            {BDI2_QUESTIONS.map((q, idx) => {
              const isComplete = responses[q.id] !== undefined;
              const isCurrent = idx === currentQuestion;
              const isCritical = q.isCritical;

              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(idx)}
                  className={`w-10 h-10 rounded-lg font-medium text-sm transition-all ${
                    isCurrent
                      ? 'bg-blue-600 text-white scale-110'
                      : isCritical
                      ? isComplete
                        ? 'bg-red-100 text-red-800 hover:bg-red-200 border-2 border-red-300'
                        : 'bg-red-50 text-red-600 hover:bg-red-100 border-2 border-red-200'
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
              <div className='w-3 h-3 bg-red-100 border-2 border-red-300 rounded' />
              <span>Critical item</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default BDI2Screening;
