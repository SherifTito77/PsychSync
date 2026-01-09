/**
 * Wellbeing Assessment Educational Content Component
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SeverityInfo } from '../../types';

interface WellbeingEducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const WellbeingEducation: React.FC<WellbeingEducationProps> = ({ score, severity }) => (
  <Card className="mb-8 bg-emerald-50 border-emerald-200">
    <CardHeader>
      <CardTitle className="text-emerald-900">Understanding Your Wellbeing Assessment Results</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-700">
        This comprehensive wellbeing assessment evaluates multiple dimensions of your mental health and life satisfaction.
        {severity && ` Your current level: ${severity.label}`}
      </p>
    </CardContent>
  </Card>
);
