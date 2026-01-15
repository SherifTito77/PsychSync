/**
 * Assessment Progress Bar Component
 *
 * Displays progress through the assessment questions.
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface ProgressBarProps {
  current: number;
  total: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ current, total }) => {
  const percentage = ((current + 1) / total) * 100;

  return (
    <Card className="w-full max-w-3xl mx-auto mb-6">
      <CardContent className="pt-6">
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Progress</span>
            <span>{Math.round(percentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 text-center">
            Question {current + 1} of {total}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
