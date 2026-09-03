/**
 * MDQ - Mood Disorder Questionnaire
 *
 * Screening tool for bipolar disorder
 *
 * Sensitivity: 0.73, Specificity: 0.90
 * Items: 15 questions (13 symptoms + 2 clustering questions)
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

interface MDQResponse {
  q1_periods_high_energy: number;
  q2_irritable: number;
  q3_confident: number;
  q4_less_sleep: number;
  q5_more_talkative: number;
  q6_thoughts_racing: number;
  q7_attention_jumps: number;
  q8_energy_increase: number;
  q9_more_active: number;
  q10_more_social: number;
  q11_more_interested: number;
  q12_more_sexual: number;
  q13_risk_behaviors: number;
  q14_simultaneous: number;
  q15_impairment: number;
}

interface ScreeningResult {
  id: string;
  symptom_count: number;
  clustering_present: boolean;
  impairment_present: boolean;
  mdq_positive: boolean;
  interpretation: string;
  recommendations: string[];
}

const QUESTIONS = [
  { id: 'q1_periods_high_energy', text: 'Has there ever been a period when you felt so good or hyper that others thought you were not your normal self?' },
  { id: 'q2_irritable', text: 'Has there ever been a period when you were so irritable that you shouted at people or started fights?' },
  { id: 'q3_confident', text: 'Has there ever been a period when you felt much more self-confident than usual?' },
  { id: 'q4_less_sleep', text: 'Has there ever been a period when you got much less sleep than usual but didn\'t miss it?' },
  { id: 'q5_more_talkative', text: 'Has there ever been a period when you were much more talkative or spoke faster than usual?' },
  { id: 'q6_thoughts_racing', text: 'Has there ever been a period when thoughts raced through your head?' },
  { id: 'q7_attention_jumps', text: 'Has there ever been a period when you were so easily distracted that you had trouble concentrating?' },
  { id: 'q8_energy_increase', text: 'Has there ever been a period when you had much more energy than usual?' },
  { id: 'q9_more_active', text: 'Has there ever been a period when you were much more active or did many more things than usual?' },
  { id: 'q10_more_social', text: 'Has there ever been a period when you were much more social or outgoing than usual?' },
  { id: 'q11_more_interested', text: 'Has there ever been a period when you were much more interested in sex than usual?' },
  { id: 'q12_more_sexual', text: 'Has there ever been a period when you did things that were excessive, foolish, or risky?' },
  { id: 'q13_risk_behaviors', text: 'Has there ever been a period when spending money got you or your family into trouble?' },
  { id: 'q14_simultaneous', text: 'If you said YES to more than one, have several happened during the same period?', options: [{value: 0, label: 'No'}, {value: 1, label: 'Yes'}] },
  { id: 'q15_impairment', text: 'How much of a problem did these cause you?', options: [{value: 0, label: 'No problem'}, {value: 1, label: 'Minor'}, {value: 2, label: 'Moderate'}, {value: 3, label: 'Serious'}] },
];

const getOptions = (q: typeof QUESTIONS[0]) => {
  return q.options || [{value: 0, label: 'No'}, {value: 1, label: 'Yes'}];
};

const MDQScreening: React.FC = () => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [responses, setResponses] = useState<Partial<MDQResponse>>({});
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
      handleSubmit(newResponses as MDQResponse);
    }
  };

  const handleSubmit = async (finalResponses: MDQResponse) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/clinical/screening/submit', {
        assessment_type: 'mdq',
        responses: responses
      });
      setResult(response.data as ScreeningResult);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit screening');
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
            <CardTitle className="text-2xl">MDQ Results</CardTitle>
            <CardDescription>Mood Disorder Questionnaire</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className={`p-6 rounded-lg border-2 ${result.mdq_positive ? 'bg-red-50 border-red-300' : 'bg-green-50 border-green-300'}`}>
              <h3 className="text-lg font-semibold mb-2">Bipolar Screening</h3>
              <div className={`text-2xl font-bold ${result.mdq_positive ? 'text-red-900' : 'text-green-900'}`}>
                {result.mdq_positive ? 'MDQ Positive' : 'MDQ Negative'}
              </div>
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
            <Button onClick={handleReset} className="w-full">Take Again</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">MDQ Assessment</CardTitle>
          <CardDescription>Mood Disorder Questionnaire</CardDescription>
          <Progress value={progress} className="mt-4" />
          <p className="text-sm text-gray-500 mt-2">Question {currentQuestionIndex + 1} of {QUESTIONS.length}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && <Alert variant="error"><AlertDescription>{error}</AlertDescription></Alert>}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p>Analyzing responses...</p>
            </div>
          ) : (
            <>
              <Label className="text-lg font-medium">{currentQuestion.text}</Label>
              <RadioGroup
                value={String(responses[currentQuestion.id as keyof MDQResponse] || 0)}
                onChange={(value) => handleResponse(parseInt(value))}
                className="space-y-3"
              >
                {getOptions(currentQuestion).map((option) => (
                  <div key={option.value} className="flex items-center space-x-2 p-3 border rounded-lg hover:bg-gray-50">
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

export default MDQScreening;
