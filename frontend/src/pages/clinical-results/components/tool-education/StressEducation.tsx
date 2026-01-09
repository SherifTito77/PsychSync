/**
 * Stress Scale Educational Content Component
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SeverityInfo } from '../../types';

interface StressEducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const StressEducation: React.FC<StressEducationProps> = ({ score, severity }) => (
  <Card className="mb-8 bg-orange-50 border-orange-200">
    <CardHeader>
      <CardTitle className="text-orange-900">Understanding Your Perceived Stress Results</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-700">
        The Perceived Stress Scale measures your subjective experience of stress.
        {severity && ` Your current level: ${severity.label}`}
      </p>
    </CardContent>
  </Card>
);
