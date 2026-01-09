/**
 * Team Radar Chart Component
 *
 * Displays personality trait balance using radar visualization
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { PersonalityRadarData } from '../types';

interface TeamRadarChartProps {
  data: PersonalityRadarData[];
}

export const TeamRadarChart: React.FC<TeamRadarChartProps> = ({ data }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Personality Balance</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={data}>
            <PolarGrid />
            <PolarAngleAxis dataKey="trait" />
            <PolarRadiusAxis angle={90} domain={[0, 1]} />
            <Radar
              name="Current"
              dataKey="current"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.6}
            />
            <Radar
              name="Optimal"
              dataKey="optimal"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.6}
            />
            <Radar
              name="Optimized"
              dataKey="optimized"
              stroke="#f59e0b"
              fill="#f59e0b"
              fillOpacity={0.6}
            />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
