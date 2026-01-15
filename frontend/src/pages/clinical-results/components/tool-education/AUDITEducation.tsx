/**
 * AUDIT Educational Content Component
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { SeverityInfo } from '../../types';

interface AUDITEducationProps {
  score: number;
  severity: SeverityInfo | undefined;
}

export const AUDITEducation: React.FC<AUDITEducationProps> = ({ score, severity }) => (
  <Card className="mb-8 bg-purple-50 border-purple-200">
    <CardHeader>
      <CardTitle className="text-purple-900">Understanding Your AUDIT Results</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-700">
        The AUDIT assesses alcohol consumption patterns and drinking behaviors.
        {severity && ` Your current level: ${severity.label}`}
      </p>
    </CardContent>
  </Card>
);
