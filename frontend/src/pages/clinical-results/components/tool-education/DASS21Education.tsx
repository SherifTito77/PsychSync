/**
 * DASS-21 Educational Content Component
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SeverityInfo } from '../../types';

interface DASS21EducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const DASS21Education: React.FC<DASS21EducationProps> = ({ score, severity }) => (
  <Card className="mb-8 bg-green-50 border-green-200">
    <CardHeader>
      <CardTitle className="text-green-900">Understanding Your DASS-21 Results</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-700">
        The DASS-21 measures depression, anxiety, and stress levels.
        {severity && ` Your current level: ${severity.label}`}
      </p>
    </CardContent>
  </Card>
);
