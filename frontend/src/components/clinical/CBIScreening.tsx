/**
 * CBI - Copenhagen Burnout Inventory
 *
 * Measures burnout across three dimensions: personal, work-related, and client-related
 *
 * Reliability: α = 0.87
 * Items: 19 questions, 0-4 scale (Always to Never)
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Label from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';
import api from '@/services/api';

interface CBIResponse {
  // Personal burnout (6 items)
  p1_tired: number;
  p2_exhausted: number;
  p3_physically_exhausted: number;
  p4_emotionally_exhausted: number;
  p5_cannot_take_more: number;
  p6_worn_out: number;

  // Work-related burnout (7 items)
  w1_tired_work: number;
  w2_every_work_is_strain: number;
  w3_exhausted_morning: number;
  w4_work_every_thought: number;
  w5_work_frustrated: number;
  w6_too_little_energy: number;
  w7_burnout_work: number;

  // Client-related burnout (6 items)
  c1_tired_clients: number;
  c2_frustrated_clients: number;
  c3_more_emotional: number;
  c4_caring_burden: number;
  c5_cannot_empathize: number;
  c6_clients_suffering: number;
}

interface ScreeningResult {
  id: string;
  personal_burnout: number;
  work_burnout: number;
  client_burnout: number;
  total_burnout: number;
  severity_level: string;
  interpretation: string;
  recommendations: string[];
}

const QUESTIONS = [
  // Personal Burnout
  { id: 'p1_tired', category: 'personal', text: 'How often do you feel tired?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'p2_exhausted', category: 'personal', text: 'How often are you physically exhausted?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'p3_physically_exhausted', category: 'personal', text: 'How often are you emotionally exhausted?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'p4_emotionally_exhausted', category: 'personal', text: 'How often do you think: "I can\'t take it anymore"?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'p5_cannot_take_more', category: 'personal', text: 'How often do you feel worn out?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'p6_worn_out', category: 'personal', text: 'Do you feel that you are burned out?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  // Work-related Burnout
  { id: 'w1_tired_work', category: 'work', text: 'Do you feel burned out by your work?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'w2_every_work_is_strain', category: 'work', text: 'Does your work frustrate you?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'w3_exhausted_morning', category: 'work', text: 'Do you feel exhausted by your work?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'w4_work_every_thought', category: 'work', text: 'Do you feel worn out at the end of the workday?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'w5_work_frustrated', category: 'work', text: 'Do you have difficulty coping with your work?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'w6_too_little_energy', category: 'work', text: 'Do you feel too little energy for family/friends due to work?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'w7_burnout_work', category: 'work', text: 'Do you feel burnt out because of your work?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  // Client-related Burnout
  { id: 'c1_tired_clients', category: 'client', text: 'Do you feel burned out by your work with clients?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'c2_frustrated_clients', category: 'client', text: 'Do you find it hard to work with clients?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'c3_more_emotional', category: 'client', text: 'Does your work with clients make you feel emotionally exhausted?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'c4_caring_burden', category: 'client', text: 'Do you feel that caring for clients is a burden?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'c5_cannot_empathize', category: 'client', text: 'Do you feel you cannot empathize with clients anymore?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
  { id: 'c6_clients_suffering', category: 'client', text: 'Do you feel you don\'t care about clients anymore?', options: [
    { value: 100, label: 'Always' }, { value: 75, label: 'Often' }, { value: 50, label: 'Sometimes' }, { value: 25, label: 'Seldom' }, { value: 0, label: 'Never' }
  ]},
];

const CBIScreening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<CBIResponse>>({});
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = QUESTIONS[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / QUESTIONS.length) * 100;

  const handleResponse = (value: number) => {
    const newResponses = { ...responses, [currentQuestion.id]: value };
    setResponses(newResponses);

    if (currentQuestionIndex < QUESTIONS.length - 1) {
      setTimeout(() => setCurrentQuestionIndex(currentQuestionIndex + 1), 300);
    } else {
      handleSubmit(newResponses as CBIResponse);
    }
  };

  const handleSubmit = async (finalResponses: CBIResponse) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'cbi',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentQuestionIndex(0);
    setResponses({});
    setResult(null);
    setError(null);
  };

  if (result) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">CBI Assessment Results</CardTitle>
            <CardDescription>Copenhagen Burnout Inventory</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="text-sm text-blue-700 mb-1">Personal Burnout</div>
                <div className="text-2xl font-bold text-blue-900">{result.personal_burnout}</div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <div className="text-sm text-orange-700 mb-1">Work Burnout</div>
                <div className="text-2xl font-bold text-orange-900">{result.work_burnout}</div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="text-sm text-purple-700 mb-1">Client Burnout</div>
                <div className="text-2xl font-bold text-purple-900">{result.client_burnout}</div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-2">Overall Burnout Level</h3>
              <div className="text-3xl font-bold text-gray-900">{result.severity_level}</div>
            </div>

            {result.interpretation && <Alert><AlertDescription>{result.interpretation}</AlertDescription></Alert>}
            {result.recommendations && result.recommendations.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Recommendations:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {result.recommendations.map((rec, idx) => <li key={idx} className="text-sm">{rec}</li>)}
                </ul>
              </div>
            )}
            <Button onClick={handleReset} className="w-full">Take Assessment Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">CBI Assessment</CardTitle>
          <CardDescription>Copenhagen Burnout Inventory - 19 questions</CardDescription>
          <Progress value={progress} className="mt-4" />
          <p className="text-sm text-gray-500 mt-2">Question {currentQuestionIndex + 1} of {QUESTIONS.length} ({currentQuestion.category})</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && <Alert variant="error"><AlertDescription>{error}</AlertDescription></Alert>}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p className="text-gray-600">Analyzing your responses...</p>
            </div>
          ) : (
            <>
              <Label className="text-lg font-medium">{currentQuestion.text}</Label>
              <RadioGroup
                value={String(responses[currentQuestion.id as keyof CBIResponse] || 0)}
                onChange={(value) => handleResponse(parseInt(value))}
                className="space-y-3"
              >
                {currentQuestion.options.map((option) => (
                  <div key={option.value} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                    <RadioGroupItem value={option.value.toString()} id={`${currentQuestion.id}-${option.value}`} />
                    <Label htmlFor={`${currentQuestion.id}-${option.value}`} className="flex-1 cursor-pointer">{option.label}</Label>
                  </div>
                ))}
              </RadioGroup>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CBIScreening;
