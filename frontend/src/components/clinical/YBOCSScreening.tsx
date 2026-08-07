/**
 * Y-BOCS (Yale-Brown Obsessive Compulsive Scale) Screening Component
 *
 * 10-item assessment for OCD symptom severity
 * 5 obsession items + 5 compulsion items
 * 0-4 scale for each item
 *
 * Reliability: Inter-rater α = 0.98
 * Clinical utility: Gold standard for OCD severity assessment
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Progress from '@/components/ui/progress';
import { Loader2, RefreshCw, AlertTriangle, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import api from '@/services/api';

interface YBOCSResponse {
  item_1_time_obsessions: number;
  item_2_interference_obsessions: number;
  item_3_distress_obsessions: number;
  item_4_resistance_obsessions: number;
  item_5_control_obsessions: number;
  item_6_time_compulsions: number;
  item_7_interference_compulsions: number;
  item_8_distress_compulsions: number;
  item_9_resistance_compulsions: number;
  item_10_control_compulsions: number;
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
    obsessions_severity: number;
    compulsions_severity: number;
    time_consumed: number;
    interference: number;
    distress: number;
    resistance: number;
    control: number;
  };
}

const YBOCS_QUESTIONS = [
  // Obsession Items (1-5)
  {
    id: 'item_1_time_obsessions',
    section: 'Obsessions',
    text: 'Time occupied by obsessive thoughts',
    description: 'How much of your time is occupied by obsessive thoughts?',
    options: [
      { value: 0, label: 'None', description: 'Not at all' },
      { value: 1, label: 'Mild', description: 'Less than 1 hour/day or occasional intrusions' },
      { value: 2, label: 'Moderate', description: '1-3 hours/day or frequent intrusions' },
      { value: 3, label: 'Severe', description: '3-8 hours/day or very frequent intrusions' },
      { value: 4, label: 'Extreme', description: 'More than 8 hours/day or near-constant intrusions' },
    ],
  },
  {
    id: 'item_2_interference_obsessions',
    section: 'Obsessions',
    text: 'Interference due to obsessive thoughts',
    description: 'How much do your obsessive thoughts interfere with your social or work functioning?',
    options: [
      { value: 0, label: 'None', description: 'No interference' },
      { value: 1, label: 'Mild', description: 'Slight interference' },
      { value: 2, label: 'Moderate', description: 'Definite interference, but still manageable' },
      { value: 3, label: 'Severe', description: 'Substantial impairment' },
      { value: 4, label: 'Extreme', description: 'Incapacitating' },
    ],
  },
  {
    id: 'item_3_distress_obsessions',
    section: 'Obsessions',
    text: 'Distress associated with obsessive thoughts',
    description: 'How much distress do your obsessive thoughts cause you?',
    options: [
      { value: 0, label: 'None', description: 'No distress' },
      { value: 1, label: 'Mild', description: 'Not too disturbing' },
      { value: 2, label: 'Moderate', description: 'Disturbing, but still manageable' },
      { value: 3, label: 'Severe', description: 'Very disturbing' },
      { value: 4, label: 'Extreme', description: 'Near constant and disabling distress' },
    ],
  },
  {
    id: 'item_4_resistance_obsessions',
    section: 'Obsessions',
    text: 'Resistance against obsessive thoughts',
    description: 'How much do you try to resist your obsessive thoughts?',
    options: [
      { value: 0, label: 'N/A', description: 'No attempt needed (thoughts are minimal)' },
      { value: 1, label: 'Mild', description: 'Tries to resist most of the time' },
      { value: 2, label: 'Moderate', description: 'Tries to resist some of the time' },
      { value: 3, label: 'Severe', description: 'Yields to almost all obsessions without trying to control' },
      { value: 4, label: 'Extreme', description: 'Completely and uncontrollably gives in to all obsessions' },
    ],
  },
  {
    id: 'item_5_control_obsessions',
    section: 'Obsessions',
    text: 'Degree of control over obsessive thoughts',
    description: 'How much control do you have over your obsessive thoughts?',
    options: [
      { value: 0, label: 'Complete', description: 'Complete control (or minimal thoughts)' },
      { value: 1, label: 'Much', description: 'Usually able to control or dismiss them' },
      { value: 2, label: 'Moderate', description: 'Sometimes can control them' },
      { value: 3, label: 'Little', description: 'Rarely able to control them' },
      { value: 4, label: 'None', description: 'Control is completely absent' },
    ],
  },

  // Compulsion Items (6-10)
  {
    id: 'item_6_time_compulsions',
    section: 'Compulsions',
    text: 'Time spent performing compulsive behaviors',
    description: 'How much time do you spend performing compulsive behaviors?',
    options: [
      { value: 0, label: 'None', description: 'Not at all' },
      { value: 1, label: 'Mild', description: 'Less than 1 hour/day' },
      { value: 2, label: 'Moderate', description: '1-3 hours/day' },
      { value: 3, label: 'Severe', description: '3-8 hours/day' },
      { value: 4, label: 'Extreme', description: 'More than 8 hours/day' },
    ],
  },
  {
    id: 'item_7_interference_compulsions',
    section: 'Compulsions',
    text: 'Interference due to compulsive behaviors',
    description: 'How much do your compulsions interfere with your social or work functioning?',
    options: [
      { value: 0, label: 'None', description: 'No interference' },
      { value: 1, label: 'Mild', description: 'Slight interference' },
      { value: 2, label: 'Moderate', description: 'Definite interference, but still manageable' },
      { value: 3, label: 'Severe', description: 'Substantial impairment' },
      { value: 4, label: 'Extreme', description: 'Incapacitating' },
    ],
  },
  {
    id: 'item_8_distress_compulsions',
    section: 'Compulsions',
    text: 'Distress associated with compulsive behaviors',
    description: 'How much distress would you feel if you were prevented from performing your compulsions?',
    options: [
      { value: 0, label: 'None', description: 'No distress' },
      { value: 1, label: 'Mild', description: 'Only slight distress' },
      { value: 2, label: 'Moderate', description: 'Moderate distress, but still manageable' },
      { value: 3, label: 'Severe', description: 'Very distressing' },
      { value: 4, label: 'Extreme', description: 'Overwhelming and disabling distress' },
    ],
  },
  {
    id: 'item_9_resistance_compulsions',
    section: 'Compulsions',
    text: 'Resistance against compulsive behaviors',
    description: 'How much do you try to resist your compulsions?',
    options: [
      { value: 0, label: 'N/A', description: 'No attempt needed (compulsions are minimal)' },
      { value: 1, label: 'Mild', description: 'Tries to resist most of the time' },
      { value: 2, label: 'Moderate', description: 'Tries to resist some of the time' },
      { value: 3, label: 'Severe', description: 'Yields to almost all compulsions without trying to control' },
      { value: 4, label: 'Extreme', description: 'Completely and uncontrollably gives in to all compulsions' },
    ],
  },
  {
    id: 'item_10_control_compulsions',
    section: 'Compulsions',
    text: 'Degree of control over compulsive behaviors',
    description: 'How much control do you have over your compulsive behaviors?',
    options: [
      { value: 0, label: 'Complete', description: 'Complete control (or minimal compulsions)' },
      { value: 1, label: 'Much', description: 'Usually able to control or resist them' },
      { value: 2, label: 'Moderate', description: 'Sometimes can control them' },
      { value: 3, label: 'Little', description: 'Rarely able to control them' },
      { value: 4, label: 'None', description: 'Control is completely absent' },
    ],
  },
];

function YBOCSScreening() {
  const [responses, setResponses] = useState<Partial<YBOCSResponse>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const progress = (Object.keys(responses).length / YBOCS_QUESTIONS.length) * 100;
  const currentQuestionComplete = responses[YBOCS_QUESTIONS[currentQuestion]?.id] !== undefined;
  const allQuestionsComplete = YBOCS_QUESTIONS.every((q) => responses[q.id] !== undefined);

  const handleResponse = (questionId: keyof YBOCSResponse, value: number) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: value,
    }));
    setError(null);
  };

  const handleNext = () => {
    if (currentQuestion < YBOCS_QUESTIONS.length - 1) {
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
      const response = await api.post(./clinical/screening/submit., { assessment_type: (w+), responses: };
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
                  Yale-Brown Obsessive Compulsive Scale (Y-BOCS)
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center py-4">
                <p className="text-sm text-gray-600 mb-2">Total Score (0-40)</p>
                <p className="text-5xl font-bold text-gray-900">{result.total_score}</p>
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
                    <strong>Severe OCD Symptoms Detected:</strong> Your responses indicate severe OCD symptoms
                    with significant functional impairment. Immediate evaluation by an OCD specialist is
                    strongly recommended. Evidence-based treatments (ERP therapy + medication) are highly
                    effective.
                  </AlertDescription>
                </Alert>
              )}

              {/* Risk Flags */}
              {result.risk_flags && result.risk_flags.length > 0 && (
                <Alert className="border-orange-500 bg-orange-50">
                  <AlertTriangle className="h-4 w-4 text-orange-600" />
                  <AlertDescription className="text-orange-900">
                    <strong>Clinical Indicators:</strong>
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

        {/* Detailed Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Symptom Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Obsessions vs Compulsions */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2 text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-600">Obsessions</p>
                  <p className="text-3xl font-bold text-purple-700">
                    {result.subscale_scores?.obsessions_severity || 0}/20
                  </p>
                </div>
                <div className="space-y-2 text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-600">Compulsions</p>
                  <p className="text-3xl font-bold text-blue-700">
                    {result.subscale_scores?.compulsions_severity || 0}/20
                  </p>
                </div>
              </div>

              {/* Detailed Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Time Consumed</p>
                  <p className="text-xl font-bold">{result.subscale_scores?.time_consumed || 0}/8</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Interference</p>
                  <p className="text-xl font-bold">{result.subscale_scores?.interference || 0}/8</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Distress</p>
                  <p className="text-xl font-bold">{result.subscale_scores?.distress || 0}/8</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-600 mb-1">Resistance</p>
                  <p className="text-xl font-bold">{result.subscale_scores?.resistance || 0}/8</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg col-span-2">
                  <p className="text-xs text-gray-600 mb-1">Control</p>
                  <p className="text-xl font-bold">{result.subscale_scores?.control || 0}/8</p>
                </div>
              </div>

              {/* Presentation Type */}
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-900 mb-2">Presentation Pattern</p>
                {result.subscale_scores?.obsessions_severity && result.subscale_scores?.compulsions_severity && (
                  <p className="text-blue-800">
                    {result.subscale_scores.obsessions_severity > result.subscale_scores.compulsions_severity * 1.3
                      ? '💭 Obsession-dominant presentation (obsessions significantly more severe)'
                      : result.subscale_scores.compulsions_severity > result.subscale_scores.obsessions_severity * 1.3
                      ? '🔄 Compulsion-dominant presentation (compulsions significantly more severe)'
                      : '⚖️ Balanced presentation (obsessions and compulsions equally severe)'}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle>Treatment Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {result.recommendations.map((rec, idx) => (
                <li key={idx} className="flex gap-3">
                  <RefreshCw className="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Crisis Resources */}
        <Card className="border-red-500 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900">OCD Support Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <strong className="text-red-900">International OCD Foundation (IOCDF)</strong>
                <p className="text-red-800">
                  Website: iocdf.org | Find specialists and support groups near you
                </p>
              </div>
              <div>
                <strong className="text-red-900">988 Suicide & Crisis Lifeline</strong>
                <p className="text-red-800">Call or text 988 (24/7)</p>
              </div>
              <div>
                <strong className="text-red-900">Crisis Text Line</strong>
                <p className="text-red-800">Text HOME to 741741</p>
              </div>
              <div>
                <strong className="text-red-900">Emergency Services</strong>
                <p className="text-red-800">Call 911 if in immediate danger</p>
              </div>
              <div className="mt-4 p-3 bg-red-100 rounded-lg">
                <p className="text-sm text-red-900">
                  <strong>Effective Treatments Available:</strong> Exposure and Response Prevention (ERP)
                  therapy is the gold standard for OCD treatment, with 70-80% of patients experiencing significant
                  improvement. Medication (SSRIs) can also be highly effective, especially when combined with therapy.
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

  // Assessment view
  const question = YBOCS_QUESTIONS[currentQuestion];
  const isObsessionSection = question.section === 'Obsessions';

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <RefreshCw className="h-8 w-8 text-purple-600" />
            <div>
              <CardTitle className="text-2xl">OCD Severity Assessment</CardTitle>
              <CardDescription>
                Yale-Brown Obsessive Compulsive Scale (Y-BOCS) • Question {currentQuestion + 1} of {YBOCS_QUESTIONS.length}
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

      {/* Section Banner */}
      <Alert className={`border-2 ${
        isObsessionSection
          ? 'bg-purple-50 border-purple-200'
          : 'bg-blue-50 border-blue-200'
      }`}>
        <RefreshCw className={`h-4 w-4 ${isObsessionSection ? 'text-purple-600' : 'text-blue-600'}`} />
        <AlertDescription className={isObsessionSection ? 'text-purple-900' : 'text-blue-900'}>
          <strong className="capitalize">{question.section} Section:</strong> Questions {isObsessionSection ? '1-5' : '6-10'}
        </AlertDescription>
      </Alert>

      {/* Question Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">{question.text}</CardTitle>
          <CardDescription className="text-base">{question.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioGroup
            value={String(responses[question.id] || 0)}
            onChange={(value) => handleResponse(question.id as keyof YBOCSResponse, parseInt(value))}
          >
            {question.options.map((option) => (
              <div
                key={option.value}
                className="flex items-start space-x-3 p-4 rounded-lg hover:bg-gray-50 border cursor-pointer"
              >
                <RadioGroupItem value={option.value.toString()} id={`option-${option.value}`} />
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <Label htmlFor={`option-${option.value}`} className="text-lg font-semibold cursor-pointer">
                      {option.label}
                    </Label>
                  </div>
                  <p className="text-sm text-gray-600 ml-6">{option.description}</p>
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

        {currentQuestion < YBOCS_QUESTIONS.length - 1 ? (
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
            onClick={handleSubmit}
            disabled={!allQuestionsComplete || loading}
            size="sm"
            className="bg-purple-600 hover:bg-purple-700"
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
        )}
      </div>

      {/* Quick Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quick Navigation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Obsessions */}
            <div>
              <p className="text-sm font-medium text-purple-900 mb-2">Obsessions (1-5)</p>
              <div className="grid grid-cols-5 gap-2">
                {YBOCS_QUESTIONS.slice(0, 5).map((q, idx) => {
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
                          ? 'bg-purple-100 text-purple-800 hover:bg-purple-200'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Compulsions */}
            <div>
              <p className="text-sm font-medium text-blue-900 mb-2">Compulsions (6-10)</p>
              <div className="grid grid-cols-5 gap-2">
                {YBOCS_QUESTIONS.slice(5, 10).map((q, idx) => {
                  const isComplete = responses[q.id] !== undefined;
                  const isCurrent = idx + 5 === currentQuestion;

                  return (
                    <button
                      key={q.id}
                      onClick={() => setCurrentQuestion(idx + 5)}
                      className={`w-10 h-10 rounded-lg font-medium text-sm transition-all ${
                        isCurrent
                          ? 'bg-blue-600 text-white scale-110'
                          : isComplete
                          ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {idx + 6}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
export default YBOCSScreening;
