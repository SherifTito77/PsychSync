/**
 * Skill Gap Analysis Component
 *
 * Displays skill coverage analysis with bar chart
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3 } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { SkillCoverageData } from '../types';

interface SkillGapAnalysisProps {
  data: SkillCoverageData[];
}

export const SkillGapAnalysis: React.FC<SkillGapAnalysisProps> = ({ data }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Skill Coverage Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="skill" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="coverage" fill="#3b82f6" name="Coverage (%)" />
            <Bar dataKey="weight" fill="#10b981" name="Weight" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
