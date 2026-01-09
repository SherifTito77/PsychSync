/**
 * Results Tab Component
 *
 * Displays optimization results, charts, and recommendations
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { Trophy, Users, Download, Info } from 'lucide-react';
import { OptimizationResult, PersonalityRadarData, SkillCoverageData, TeamMember } from '../types';
import { TeamRadarChart } from './TeamRadarChart';
import { SkillGapAnalysis } from './SkillGapAnalysis';
import { OptimizationSuggestions } from './OptimizationSuggestions';
import { MemberList } from './MemberList';

interface ResultsTabProps {
  optimizationResult: OptimizationResult | null;
  personalityRadarData: PersonalityRadarData[];
  skillCoverageData: SkillCoverageData[];
  recommendedTeam: TeamMember[];
}

export const ResultsTab: React.FC<ResultsTabProps> = ({
  optimizationResult,
  personalityRadarData,
  skillCoverageData,
  recommendedTeam,
}) => {
  const diversityMetricsData = [
    { metric: 'Skill Diversity', current: 85, target: 90, improvement: 5 },
    { metric: 'Experience Diversity', current: 78, target: 85, improvement: 7 },
    { metric: 'Departmental Diversity', current: 70, target: 80, improvement: 10 },
    { metric: 'Cognitive Diversity', current: 88, target: 85, improvement: -3 },
    { metric: 'Age Diversity', current: 65, target: 75, improvement: 10 },
  ];

  const performancePredictionData = [
    { phase: 'Current', score: 0.78 },
    { phase: 'Optimized', score: optimizationResult?.performancePrediction || 0.85 },
    { phase: '6-Month Target', score: 0.92 },
  ];

  if (!optimizationResult) {
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>No Optimization Results</AlertTitle>
        <AlertDescription>
          Please run the optimization first to see results and recommendations.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Optimization Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5" />
            Optimization Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {(optimizationResult.teamScore * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Team Score</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {(optimizationResult.performancePrediction * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Predicted Performance</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {(optimizationResult.compatibilityScore * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Compatibility Score</p>
            </div>
          </div>

          {/* Recommended Team */}
          <div className="mt-6">
            <h3 className="font-semibold mb-3">Recommended Team</h3>
            <MemberList members={recommendedTeam} title="" />
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <SkillGapAnalysis data={skillCoverageData} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TeamRadarChart data={personalityRadarData} />
        <Card>
          <CardHeader>
            <CardTitle>Performance Prediction</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performancePredictionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="phase" />
                <YAxis domain={[0.7, 1.0]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Diversity Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Diversity Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={diversityMetricsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="current" fill="#3b82f6" name="Current" />
              <Bar dataKey="target" fill="#10b981" name="Target" />
              <Bar dataKey="improvement" fill="#f59e0b" name="Improvement" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <OptimizationSuggestions result={optimizationResult} />

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>Export Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export PDF Report
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Excel Data
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
