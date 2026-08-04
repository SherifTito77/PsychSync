// EngagementAnalytics.tsx - Employee Engagement and Satisfaction Metrics
import React, { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, AreaChart, Area, PieChart, Pie,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

interface EngagementSurvey {
  employee_id: string;
  employee_name: string;
  department: string;
  overall_score: number;
  job_satisfaction: number;
  work_life_balance: number;
  management_support: number;
  career_growth: number;
  compensation_satisfaction: number;
  team_collaboration: number;
  survey_date: string;
}

const COLORS02 = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6'];

const engagementTrendData = [
  { quarter: 'Q1 2023', overall: 3.8, participation: 85 },
  { quarter: 'Q2 2023', overall: 3.9, participation: 88 },
  { quarter: 'Q3 2023', overall: 4.0, participation: 90 },
  { quarter: 'Q4 2023', overall: 4.1, participation: 92 },
  { quarter: 'Q1 2024', overall: 4.2, participation: 94 }
];

export const EngagementAnalytics: React.FC = () => {
  const { user } = useAuth();
  const [engagementData, setEngagementData] = useState<EngagementSurvey[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');

  useEffect(() => {
    const fetchEngagementData = async () => {
      if (!user?.organization_id) return;

      try {
        setLoading(true);
        const response = await api.get(`/hris_analytics/engagement/individual-scores?organization_id=${user.organization_id}`);
        if (response.data && response.data.scores) {
          setEngagementData(response.data.scores);
        }
      } catch (error) {
        console.error('Failed to fetch engagement data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEngagementData();
  }, [user?.organization_id]);

  const filteredData = useMemo(() => {
    return engagementData.filter(survey => {
      if (selectedDepartment !== 'All' && survey.department !== selectedDepartment) return false;
      return true;
    });
  }, [selectedDepartment, engagementData]);

  const analytics = useMemo(() => {
    if (filteredData.length === 0) return {
      avgOverall: '0.00',
      avgJobSatisfaction: '0.00',
      avgWorkLife: '0.00',
      avgManagement: '0.00',
      avgCareerGrowth: '0.00',
      deptScores: [],
      engagementDistribution: {}
    };

    const avgOverall = filteredData.reduce((sum, s) => sum + s.overall_score, 0) / filteredData.length;
    const avgJobSatisfaction = filteredData.reduce((sum, s) => sum + s.job_satisfaction, 0) / filteredData.length;
    const avgWorkLife = filteredData.reduce((sum, s) => sum + s.work_life_balance, 0) / filteredData.length;
    const avgManagement = filteredData.reduce((sum, s) => sum + s.management_support, 0) / filteredData.length;
    const avgCareerGrowth = filteredData.reduce((sum, s) => sum + s.career_growth, 0) / filteredData.length;

    const deptEngagement = filteredData.reduce((acc, survey) => {
      if (!acc[survey.department]) {
        acc[survey.department] = { total: 0, count: 0 };
      }
      acc[survey.department].total += survey.overall_score;
      acc[survey.department].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>);

    const deptScores = Object.entries(deptEngagement).map(([dept, data]) => ({
      department: dept,
      score: (data.total / data.count).toFixed(2)
    }));

    const engagementDistribution = filteredData.reduce((acc, survey) => {
      if (survey.overall_score >= 4.5) acc['Highly Engaged (4.5+)'] = (acc['Highly Engaged (4.5+)'] || 0) + 1;
      else if (survey.overall_score >= 4.0) acc['Engaged (4.0-4.4)'] = (acc['Engaged (4.0-4.4)'] || 0) + 1;
      else if (survey.overall_score >= 3.5) acc['Neutral (3.5-3.9)'] = (acc['Neutral (3.5-3.9)'] || 0) + 1;
      else acc['At Risk (<3.5)'] = (acc['At Risk (<3.5)'] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      avgOverall: avgOverall.toFixed(2),
      avgJobSatisfaction: avgJobSatisfaction.toFixed(2),
      avgWorkLife: avgWorkLife.toFixed(2),
      avgManagement: avgManagement.toFixed(2),
      avgCareerGrowth: avgCareerGrowth.toFixed(2),
      deptScores,
      engagementDistribution
    };
  }, [filteredData]);

  const dimensions = ['Job Satisfaction', 'Work-Life Balance', 'Management Support', 'Career Growth', 'Compensation Satisfaction', 'Team Collaboration'];
  const avgDimensionScores = dimensions.map(dim => ({
    dimension: dim,
    score: (
      filteredData.reduce((sum, s) => {
        const key = dim.toLowerCase().replace(' ', '_').replace('-', '_');
        return sum + (s as any)[key] || 0;
      }, 0) / (filteredData.length || 1)
    ).toFixed(2)
  }));

  const radarData = dimensions.map(dim => ({
    dimension: dim,
    score: (
      filteredData.reduce((sum, s) => {
        const key = dim.toLowerCase().replace(' ', '_').replace('-', '_');
        return sum + (s as any)[key] || 0;
      }, 0) / (filteredData.length || 1)
    ).toFixed(2) as any
  }));

  const departments = [...new Set(engagementData.map(d => d.department))];
  const distributionChartData = Object.entries(analytics.engagementDistribution).map(([name, value]) => ({ name, value }));

  if (loading) {
    return <div className="p-8 text-center">Loading engagement data...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          😊 Engagement Analytics
        </h1>
        <p className="text-gray-600 mt-1">
          Monitor employee satisfaction, engagement levels, and workplace sentiment
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Department</label>
              <select
                className="border rounded-lg px-4 py-2"
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
              >
                <option value="All">All Departments</option>
                {departments.map(dept => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </div>
            <Button onClick={() => setSelectedDepartment('All')} className="mt-6">
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700">{analytics.avgOverall}</div>
                <div className="text-sm text-purple-600">Overall Score</div>
              </div>
              <span className="text-4xl">⭐</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{analytics.avgJobSatisfaction}</div>
                <div className="text-sm text-blue-600">Job Satisfaction</div>
              </div>
              <span className="text-4xl">💼</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700">{analytics.avgWorkLife}</div>
                <div className="text-sm text-green-600">Work-Life Balance</div>
              </div>
              <span className="text-4xl">⚖️</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-700">{analytics.avgCareerGrowth}</div>
                <div className="text-sm text-orange-600">Career Growth</div>
              </div>
              <span className="text-4xl">🚀</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Engagement Trend */}
        <Card>
          <CardHeader>
            <CardTitle>📈 Engagement Trend Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={engagementTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="quarter" />
                <YAxis domain={[3, 5]} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="overall" name="Overall Score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                <Area type="monotone" dataKey="participation" name="Participation %" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Engagement Radar */}
        <Card>
          <CardHeader>
            <CardTitle>🕸️ Engagement Dimensions (Org Average)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart cx="50%" cy="50%" outerRadius={100} data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="dimension" />
                <PolarRadiusAxis angle={90} domain={[0, 5]} />
                <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Department Engagement */}
        <Card>
          <CardHeader>
            <CardTitle>🏢 Engagement by Department</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.deptScores}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Bar dataKey="score" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Engagement Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>📊 Engagement Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={distributionChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {distributionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS02[index % COLORS02.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Dimension Breakdown */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>📐 Engagement Dimension Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={avgDimensionScores} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 5]} />
              <YAxis dataKey="dimension" type="category" width={150} />
              <Tooltip />
              <Bar dataKey="score" fill="#ec4899" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Individual Scores Table */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Individual Engagement Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Employee</th>
                  <th className="text-left p-3">Department</th>
                  <th className="text-center p-3">Overall</th>
                  <th className="text-center p-3">Job Satisfaction</th>
                  <th className="text-center p-3">Work-Life</th>
                  <th className="text-center p-3">Management</th>
                  <th className="text-center p-3">Career Growth</th>
                  <th className="text-center p-3">Survey Date</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map(survey => (
                  <tr key={survey.employee_id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{survey.employee_name}</td>
                    <td className="p-3">{survey.department}</td>
                    <td className="p-3 text-center">
                      <span className={`px-2 py-1 rounded text-sm ${
                        survey.overall_score >= 4.5 ? 'bg-green-100 text-green-800' :
                        survey.overall_score >= 4.0 ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {survey.overall_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="p-3 text-center">{survey.job_satisfaction.toFixed(1)}</td>
                    <td className="p-3 text-center">{survey.work_life_balance.toFixed(1)}</td>
                    <td className="p-3 text-center">{survey.management_support.toFixed(1)}</td>
                    <td className="p-3 text-center">{survey.career_growth.toFixed(1)}</td>
                    <td className="p-3 text-center">{survey.survey_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Insights Panel */}
      <Card className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50">
        <CardHeader>
          <CardTitle>💡 Engagement Insights & Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <div className="font-semibold text-green-700 mb-2">✅ Strengths</div>
              <ul className="text-sm space-y-1 text-gray-600">
                <li>• High job satisfaction across all departments</li>
                <li>• Strong management support scores</li>
                <li>• Improving engagement trend (+0.4 over 4 quarters)</li>
              </ul>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="font-semibold text-orange-700 mb-2">⚠️ Areas for Improvement</div>
              <ul className="text-sm space-y-1 text-gray-600">
                <li>• Career growth opportunities need enhancement</li>
                <li>• Work-life balance can be improved in Sales</li>
                <li>• Consider flexible work arrangements</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EngagementAnalytics;
