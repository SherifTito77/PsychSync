/**
 * Comparison Tab Component
 *
 * Displays before/after team composition comparison
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { GitBranch } from 'lucide-react';
import { TeamRequirement, SkillCoverageData } from '../types';

interface ComparisonTabProps {
  requirements: TeamRequirement;
  skillCoverageData: SkillCoverageData[];
}

export const ComparisonTab: React.FC<ComparisonTabProps> = ({
  requirements,
  skillCoverageData,
}) => {
  return (
    <div className="space-y-6">
      {/* Comparison Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Team Composition Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">+15%</div>
              <p className="text-sm text-blue-700">Performance Improvement</p>
              <div className="text-xs text-blue-600 mt-1">Compared to baseline</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">+22%</div>
              <p className="text-sm text-green-700">Skill Coverage</p>
              <div className="text-xs text-green-600 mt-1">Better requirements match</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">+18%</div>
              <p className="text-sm text-purple-700">Diversity Score</p>
              <div className="text-xs text-purple-600 mt-1">More inclusive composition</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Before vs After Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={Object.keys(requirements.skillWeights).map((skill) => ({
                  skill,
                  before: 65,
                  after: skillCoverageData.find((s) => s.skill === skill)?.coverage || 0,
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="skill" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="before" fill="#94a3b8" name="Before" />
                <Bar dataKey="after" fill="#10b981" name="After" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Trend Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={[
                  { month: 'Initial', initial: 65, after3: 75, after6: 85 },
                  { month: 'Optimized', initial: 65, after3: 82, after6: 95 },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[60, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="initial" stroke="#94a3b8" strokeWidth={2} name="Initial" />
                <Line
                  type="monotone"
                  dataKey="after3"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="After 3 Months"
                />
                <Line
                  type="monotone"
                  dataKey="after6"
                  stroke="#10b981"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="After 6 Months"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
