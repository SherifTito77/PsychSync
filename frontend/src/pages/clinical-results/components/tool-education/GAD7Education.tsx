/**
 * GAD-7 Educational Content Component
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { SeverityInfo } from '../../types';

interface GAD7EducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const GAD7Education: React.FC<GAD7EducationProps> = ({ score, severity }) => (
  <Card className="mb-8 bg-teal-50 border-teal-200">
    <CardHeader>
      <CardTitle className="text-teal-900">Understanding Your GAD-7 Results</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-700">
        The GAD-7 assesses generalized anxiety disorder symptoms.
        {severity && ` Your current level: ${severity.label}`}
      </p>
    </CardContent>
  </Card>
);
