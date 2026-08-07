/**
 * LSAS (Liebowitz Social Anxiety Scale) Screening Component
 *
 * 24-item assessment for social anxiety disorder
 * Each item rates both FEAR (0-3) and AVOIDANCE (0-3)
 *
 * Reliability: α = 0.95
 * Clinical utility: High - gold standard for social anxiety assessment
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

interface LSASItemResponse {
  fear: number;
  avoidance: number;
}

interface LSASResponse {
  [key: string]: LSASItemResponse;
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
    total_fear: number;
    total_avoidance: number;
    performance_anxiety: number;
    social_interaction_anxiety: number;
  };
}

const LSAS_QUESTIONS = [
  // Performance/Speaking Situations (Items 1, 5-7, 9, 11, 13, 17, 19, 22-24)
  { id: 'item_1', text: 'Telephoning in public', category: 'Performance' },
  { id: 'item_5', text: 'Participating in small groups', category: 'Performance' },
  { id: 'item_6', text: 'Eating in public places', category: 'Performance' },
  { id: 'item_7', text: 'Drinking with others', category: 'Performance' },
  { id: 'item_9', text: 'Talking to people in authority', category: 'Performance' },
  { id: 'item_11', text: 'Acting, performing, or giving a talk', category: 'Performance' },
  { id: 'item_13', text: 'Going to a party', category: 'Performance' },
  { id: 'item_17', text: 'Returning goods to a store', category: 'Performance' },
  { id: 'item_19', text: 'Giving a report to a group', category: 'Performance' },
  { id: 'item_22', text: 'Trying to pick up someone', category: 'Performance' },
  { id: 'item_23', text: 'Resisting a high pressure salesperson', category: 'Performance' },
  { id: 'item_24', text: 'Giving a speech', category: 'Performance' },

  // Social Interaction Situations (Items 2-4, 8, 10, 12, 14-16, 18, 20-21)
  { id: 'item_2', text: 'Using a public bathroom', category: 'Social Interaction' },
  { id: 'item_3', text: 'Entering a room when others are already seated', category: 'Social Interaction' },
  { id: 'item_4', text: 'Being the center of attention', category: 'Social Interaction' },
  { id: 'item_8', text: 'Expressing disagreement or disapproval', category: 'Social Interaction' },
  { id: 'item_10', text: 'Giving written or oral feedback', category: 'Social Interaction' },
  { id: 'item_12', text: 'Looking at people you do not know very well in the eyes', category: 'Social Interaction' },
  { id: 'item_14', text: 'Meeting strangers', category: 'Social Interaction' },
  { id: 'item_15', text: 'Urinating in a public bathroom', category: 'Social Interaction' },
  { id: 'item_16', text: 'Being interviewed', category: 'Social Interaction' },
  { id: 'item_18', text: 'Calling someone you do not know very well', category: 'Social Interaction' },
  { id: 'item_20', text: 'Hosting a party', category: 'Social Interaction' },
  { id: 'item_21', text: 'Interacting with authority figures', category: 'Social Interaction' },
];

const FEAR_OPTIONS = [
  { value: 0, label: 'None', description: 'No fear' },
  { value: 1, label: 'Mild', description: 'Some fear' },
  { value: 2, label: 'Moderate', description: 'Moderate fear' },
  { value: 3, label: 'Severe', description: 'Severe fear' },
];

const AVOIDANCE_OPTIONS = [
  { value: 0, label: 'Never', description: 'Never avoid (0%)' },
  { value: 1, label: 'Occasionally', description: 'Sometimes avoid (33%)' },
  { value: 2, label: 'Often', description: 'Often avoid (67%)' },
  { value: 3, label: 'Usually', description: 'Usually avoid (100%)' },
];

function LSASScreening() {
  const [responses, setResponses] = useState<LSASResponse>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const progress = (Object.keys(responses).length / LSAS_QUESTIONS.length) * 100;

  const currentQuestionComplete =
    responses[LSAS_QUESTIONS[currentQuestion]?.id]?.fear !== undefined &&
    responses[LSAS_QUESTIONS[currentQuestion]?.id]?.avoidance !== undefined;

  const allQuestionsComplete = LSAS_QUESTIONS.every(
    (q) => responses[q.id]?.fear !== undefined && responses[q.id]?.avoidance !== undefined
  );

  const handleResponse = (questionId: string, field: 'fear' | 'avoidance', value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        [field]: value,
      },
    }));
    setError(null);
  };

  const handleNext = () => {
    if (currentQuestion < LSAS_QUESTIONS.length - 1) {
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
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'lsas',
        responses: responses
      }
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
        <Card className={`border-2 ${
          result.crisis_alert ? 'border-red-500 bg-red-50' : 'border-green-500 bg-green-50'
        }`}>
          <CardHeader>
            <div className='flex items-center gap-3'>
              {result.crisis_alert ? (
                <AlertTriangle className='h-8 w-8 text-red-600' />
              ) : (
                <CheckCircle className='h-8 w-8 text-green-600' />
              )}
              <div>
                <CardTitle className='text-2xl'>
                  {result.crisis_alert ? 'Crisis Alert' : 'Assessment Complete'}
                </CardTitle>
                <CardDescription className='text-base'>
                  Liebowitz Social Anxiety Scale (LSAS)
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className='space-y-4'>
              <div className='text-center py-4'>
                <p className='text-sm text-gray-600 mb-2'>Total Score (0-144)</p>
                <p className='text-5xl font-bold text-gray-900'>{result.total_score}</p>
              </div>

              <div className='grid grid-cols-2 gap-4 text-center'>
                <div className='bg-white p-4 rounded-lg shadow'>
                  <p className='text-sm text-gray-600'>Severity</p>
                  <p className='text-xl font-semibold capitalize'>{result.severity_level.replace('_', ' ')}</p>
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
                    <strong>Crisis Alert:</strong> Your responses indicate severe social anxiety with significant avoidance.
                    Please contact a mental health professional as soon as possible.
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
                        <li key={idx} className='capitalize'>{flag.replace(/_/g, ' ')}</li>
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
            <CardTitle>Detailed Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className='grid grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <p className='text-sm font-medium text-gray-600'>Fear Subscale</p>
                <p className='text-3xl font-bold'>{result.subscale_scores?.total_fear || 0}/72</p>
              </div>
              <div className='space-y-2'>
                <p className='text-sm font-medium text-gray-600'>Avoidance Subscale</p>
                <p className='text-3xl font-bold'>{result.subscale_scores?.total_avoidance || 0}/72</p>
              </div>
              <div className='space-y-2'>
                <p className='text-sm font-medium text-gray-600'>Performance Anxiety</p>
                <p className='text-3xl font-bold'>{result.subscale_scores?.performance_anxiety || 0}/72</p>
              </div>
              <div className='space-y-2'>
                <p className='text-sm font-medium text-gray-600'>Social Interaction Anxiety</p>
                <p className='text-3xl font-bold'>{result.subscale_scores?.social_interaction_anxiety || 0}/72</p>
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
              <CardTitle className='text-red-900'>Immediate Support Resources</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='space-y-3'>
                <div>
                  <strong className='text-red-900'>988 Suicide & Crisis Lifeline</strong>
                  <p className='text-red-800'>Call or text 988 (24/7)</p>
                </div>
                <div>
                  <strong className='text-red-900'>Crisis Text Line</strong>
                  <p className='text-red-800'>Text HOME to 741741</p>
                </div>
                <div>
                  <strong className='text-red-900'>Emergency Services</strong>
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
  const question = LSAS_QUESTIONS[currentQuestion];
  const currentResponse = responses[question.id] || { fear: undefined, avoidance: undefined };

  return (
    <div className='max-w-3xl mx-auto p-6 space-y-6'>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className='flex items-center gap-3'>
            <Brain className='h-8 w-8 text-blue-600' />
            <div>
              <CardTitle className='text-2xl'>Social Anxiety Assessment</CardTitle>
              <CardDescription>
                Liebowitz Social Anxiety Scale (LSAS) • Question {currentQuestion + 1} of {LSAS_QUESTIONS.length}
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

      {/* Question Card */}
      <Card>
        <CardHeader>
          <div className='flex items-start justify-between'>
            <div className='flex-1'>
              <CardTitle className='text-xl mb-2'>
                {question.text}
              </CardTitle>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                question.category === 'Performance' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
              }`}>
                {question.category}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent className='space-y-8'>
          {/* Fear Rating */}
          <div className='space-y-4'>
            <div>
              <Label className='text-base font-semibold'>Fear Level</Label>
              <p className='text-sm text-gray-600'>How much fear would you experience in this situation?</p>
            </div>
            <RadioGroup
              value={currentResponse.fear?.toString()}
              onChange={(value) => handleResponse(question.id, 'fear', parseInt(value))}
            >
              {FEAR_OPTIONS.map((option) => (
                <div key={option.value} className='flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 border'>
                  <RadioGroupItem value={option.value.toString()} id={`fear-${option.value}`} />
                  <div className='flex-1'>
                    <Label htmlFor={`fear-${option.value}`} className='font-medium cursor-pointer'>
                      {option.label}
                    </Label>
                    <p className='text-sm text-gray-600'>{option.description}</p>
                  </div>
                </div>
              ))}
            </RadioGroup>
          </div>

          {/* Avoidance Rating */}
          <div className='space-y-4'>
            <div>
              <Label className='text-base font-semibold'>Avoidance Level</Label>
              <p className='text-sm text-gray-600'>How often do you avoid this situation?</p>
            </div>
            <RadioGroup
              value={currentResponse.avoidance?.toString()}
              onChange={(value) => handleResponse(question.id, 'avoidance', parseInt(value))}
            >
              {AVOIDANCE_OPTIONS.map((option) => (
                <div key={option.value} className='flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 border'>
                  <RadioGroupItem value={option.value.toString()} id={`avoid-${option.value}`} />
                  <div className='flex-1'>
                    <Label htmlFor={`avoid-${option.value}`} className='font-medium cursor-pointer'>
                      {option.label}
                    </Label>
                    <p className='text-sm text-gray-600'>{option.description}</p>
                  </div>
                </div>
              ))}
            </RadioGroup>
          </div>

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

        {currentQuestion < LSAS_QUESTIONS.length - 1 ? (
          <Button
            onClick={handleNext}
            disabled={!currentQuestionComplete}
            size='large'
          >
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
          <div className='grid grid-cols-6 gap-2'>
            {LSAS_QUESTIONS.map((q, idx) => {
              const isComplete = responses[q.id]?.fear !== undefined && responses[q.id]?.avoidance !== undefined;
              const isCurrent = idx === currentQuestion;

              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentQuestion(idx)}
                  className={`w-10 h-10 rounded-lg font-medium text-sm transition-all ${
                    isCurrent
                      ? 'bg-blue-600 text-white scale-110'
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
export default LSASScreening;
