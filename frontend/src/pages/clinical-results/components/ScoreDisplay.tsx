/**
 * Score Display Component
 *
 * Displays the main assessment score with severity indicator.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { AssessmentResult } from '../types';
import { getSeverityColorClass } from '../utils/severityCalculator';

interface ScoreDisplayProps {
  result: AssessmentResult;
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({ result }) => {
  const { score, severity } = result;
  const colorClass = severity ? getSeverityColorClass(result.severity_level) : 'bg-gray-500';

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle>Your Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-center">
          <div className="text-6xl font-bold text-gray-900 mb-4">{score}</div>
          <div
            className={`inline-block px-4 py-2 rounded-full text-white font-medium mb-4 ${colorClass}`}
          >
            {severity?.label}
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            {severity?.description}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
