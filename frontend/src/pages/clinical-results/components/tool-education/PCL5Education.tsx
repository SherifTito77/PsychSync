/**
 * PCL-5 Educational Content Component
 *
 * Displays detailed educational information about PCL-5 (PTSD) assessment results.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SeverityInfo } from '../../types';

interface PCL5EducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const PCL5Education: React.FC<PCL5EducationProps> = ({ score, severity }) => {
  return (
    <Card className="mb-8 bg-blue-50 border-blue-200">
      <CardHeader>
        <CardTitle className="text-blue-900">Understanding Your PCL-5 Results</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 text-gray-700">
          <div>
            <h4 className="font-semibold text-blue-900 mb-2">What Your Score Means:</h4>
            <p className="text-sm leading-relaxed">
              The PCL-5 assesses PTSD symptoms across four clusters: Intrusion (re-experiencing),
              Avoidance, Negative alterations in cognitions and mood, and Alterations in arousal
              and reactivity. Your score reflects the frequency and severity of these symptoms
              over the past month.
            </p>
          </div>

          {severity?.label?.includes('Severe') && (
            <div className="mt-4 p-4 bg-red-100 rounded-lg border border-red-300">
              <h4 className="font-semibold text-red-900 mb-2">For Severe Symptoms:</h4>
              <p className="text-sm text-red-800 leading-relaxed">
                Your symptoms indicate a high level of distress that requires immediate professional
                attention. This level of severity is very treatable, but delaying care can make
                recovery more difficult. Please contact a mental health professional today -
                effective treatment can provide rapid relief from severe symptoms.
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
