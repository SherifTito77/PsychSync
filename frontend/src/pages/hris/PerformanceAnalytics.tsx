// PerformanceAnalytics.tsx - Performance Metrics and Trends
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

interface PerformanceRecord {
  employee_id: string;
  employee_name: string;
  department: string;
  rating: number;
  goals_completed: number;
  total_goals: number;
  review_period: string;
  strengths?: string[];
  areas_for_improvement?: string[];
}

// Mock performance data
const mockPerformanceData: PerformanceRecord[] = [
  { employee_id: 'EMP001', employee_name: 'Admin User', department: 'Administration', rating: 4.5, goals_completed: 9, total_goals: 10, review_period: 'Q4 2024', strengths: ['Leadership', 'Communication'], areas_for_improvement: ['Technical Skills'] },
  { employee_id: 'EMP002', employee_name: 'John Dickens', department: 'IT', rating: 4.8, goals_completed: 10, total_goals: 10, review_period: 'Q4 2024', strengths: ['Problem Solving', 'Innovation'], areas_for_improvement: ['Documentation'] },
  { employee_id: 'EMP003', employee_name: 'Jane Doe', department: 'Sales', rating: 4.2, goals_completed: 8, total_goals: 10, review_period: 'Q4 2024', strengths: ['Sales', 'Communication'], areas_for_improvement: ['Time Management'] },
  { employee_id: 'EMP004', employee_name: 'Bob Smith', department: 'HR', rating: 4.0, goals_completed: 7, total_goals: 10, review_period: 'Q4 2024', strengths: ['Interpersonal Skills', 'Organization'], areas_for_improvement: ['Strategic Planning'] },
  { employee_id: 'EMP005', employee_name: 'Alice Williams', department: 'Finance', rating: 4.6, goals_completed: 9, total_goals: 10, review_period: 'Q4 2024', strengths: ['Accuracy', 'Efficiency'], areas_for_improvement: ['Presentation Skills'] },
  { employee_id: 'EMP006', employee_name: 'David Chen', department: 'IT', rating: 4.3, goals_completed: 8, total_goals: 10, review_period: 'Q4 2024', strengths: ['Coding', 'Teamwork'], areas_for_improvement: ['Mentoring'] },
  { employee_id: 'EMP007', employee_name: 'Sarah Johnson', department: 'Sales', rating: 4.7, goals_completed: 10, total_goals: 10, review_period: 'Q4 2024', strengths: ['Negotiation', 'Customer Relations'], areas_for_improvement: ['Product Knowledge'] },
  { employee_id: 'EMP008', employee_name: 'Michael Brown', department: 'Finance', rating: 4.1, goals_completed: 8, total_goals: 10, review_period: 'Q4 2024', strengths: ['Analysis', 'Attention to Detail'], areas_for_improvement: ['Communication'] }
];

const performanceTrendData = [
  { quarter: 'Q1 2024', avg_rating: 4.1, goals_met: 82 },
  { quarter: 'Q2 2024', avg_rating: 4.2, goals_met: 85 },
  { quarter: 'Q3 2024', avg_rating: 4.3, goals_met: 87 },
  { quarter: 'Q4 2024', avg_rating: 4.4, goals_met: 90 }
];

export const PerformanceAnalytics: React.FC = () => {
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('Q4 2024');

  const filteredData = useMemo(() => {
    return mockPerformanceData.filter(record => {
      if (selectedDepartment !== 'All' && record.department !== selectedDepartment) return false;
      if (selectedPeriod && record.review_period !== selectedPeriod) return false;
      return true;
    });
  }, [selectedDepartment, selectedPeriod]);

  const analytics = useMemo(() => {
    const avgRating = filteredData.reduce((sum, r) => sum + r.rating, 0) / filteredData.length;
    const totalGoals = filteredData.reduce((sum, r) => sum + r.total_goals, 0);
    const completedGoals = filteredData.reduce((sum, r) => sum + r.goals_completed, 0);
    const goalCompletionRate = (completedGoals / totalGoals) * 100;

    const topPerformers = [...filteredData]
      .sort((a, b) => b.rating - a.rating)
      .slice(0, 5);

    const departmentAvg = filteredData.reduce((acc, record) => {
      if (!acc[record.department]) {
        acc[record.department] = { total: 0, count: 0 };
      }
      acc[record.department].total += record.rating;
      acc[record.department].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>);

    const deptPerformance = Object.entries(departmentAvg).map(([dept, data]) => ({
      department: dept,
      avgRating: (data.total / data.count).toFixed(2)
    }));

    const ratingDistribution = filteredData.reduce((acc, record) => {
      if (record.rating >= 4.5) acc['Excellent (4.5+)'] = (acc['Excellent (4.5+)'] || 0) + 1;
      else if (record.rating >= 4.0) acc['Good (4.0-4.4)'] = (acc['Good (4.0-4.4)'] || 0) + 1;
      else if (record.rating >= 3.5) acc['Satisfactory (3.5-3.9)'] = (acc['Satisfactory (3.5-3.9)'] || 0) + 1;
      else acc['Needs Improvement (<3.5)'] = (acc['Needs Improvement (<3.5)'] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      avgRating: avgRating.toFixed(2),
      goalCompletionRate: goalCompletionRate.toFixed(1),
      totalReviews: filteredData.length,
      topPerformers,
      deptPerformance,
      ratingDistribution
    };
  }, [filteredData]);

  const departments = [...new Set(mockPerformanceData.map(d => d.department))];
  const periods = [...new Set(mockPerformanceData.map(d => d.review_period))];

  const ratingChartData = Object.entries(analytics.ratingDistribution).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          ⭐ Performance Analytics
        </h1>
        <p className="text-gray-600 mt-1">
          Track employee performance metrics, goals, and trends across your organization
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
            <div>
              <label className="block text-sm font-medium mb-2">Review Period</label>
              <select
                className="border rounded-lg px-4 py-2"
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
              >
                {periods.map(period => (
                  <option key={period} value={period}>{period}</option>
                ))}
              </select>
            </div>
            <Button
              onClick={() => {
                setSelectedDepartment('All');
                setSelectedPeriod('Q4 2024');
              }}
              className="mt-6"
            >
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-yellow-700">{analytics.avgRating}</div>
                <div className="text-sm text-yellow-600">Avg Rating</div>
              </div>
              <span className="text-4xl">⭐</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700">{analytics.goalCompletionRate}%</div>
                <div className="text-sm text-green-600">Goals Met</div>
              </div>
              <span className="text-4xl">🎯</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{analytics.totalReviews}</div>
                <div className="text-sm text-blue-600">Reviews</div>
              </div>
              <span className="text-4xl">📝</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700">{analytics.topPerformers.length}</div>
                <div className="text-sm text-purple-600">Top Performers</div>
              </div>
              <span className="text-4xl">🏆</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Performance Trend */}
        <Card>
          <CardHeader>
            <CardTitle>📈 Performance Trend Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="quarter" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="avg_rating" name="Avg Rating" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                <Area type="monotone" dataKey="goals_met" name="Goals Met %" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Rating Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>📊 Rating Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ratingChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Department Comparison */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>🏢 Department Performance Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.deptPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" />
                <YAxis domain={[0, 5]} />
                <Tooltip />
                <Bar dataKey="avgRating" name="Avg Rating" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top Performers */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>🏆 Top Performers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {analytics.topPerformers.map((performer, index) => (
              <div key={performer.employee_id} className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="text-2xl">🥇</div>
                  <div>
                    <div className="font-semibold">{performer.employee_name}</div>
                    <div className="text-sm text-gray-600">{performer.department}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <div className="text-lg font-bold text-yellow-600">{performer.rating}</div>
                    <div className="text-xs text-gray-600">Rating</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-green-600">{performer.goals_completed}/{performer.total_goals}</div>
                    <div className="text-xs text-gray-600">Goals</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600">{((performer.goals_completed / performer.total_goals) * 100).toFixed(0)}%</div>
                    <div className="text-xs text-gray-600">Complete</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Performance Review Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Employee</th>
                  <th className="text-left p-3">Department</th>
                  <th className="text-left p-3">Rating</th>
                  <th className="text-left p-3">Goals</th>
                  <th className="text-left p-3">Completion</th>
                  <th className="text-left p-3">Strengths</th>
                  <th className="text-left p-3">Improvements</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map(record => (
                  <tr key={record.employee_id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{record.employee_name}</td>
                    <td className="p-3">{record.department}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-sm ${
                        record.rating >= 4.5 ? 'bg-green-100 text-green-800' :
                        record.rating >= 4.0 ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {record.rating.toFixed(1)}
                      </span>
                    </td>
                    <td className="p-3">{record.goals_completed}/{record.total_goals}</td>
                    <td className="p-3">{((record.goals_completed / record.total_goals) * 100).toFixed(0)}%</td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {record.strengths?.map((s, i) => (
                          <span key={i} className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">{s}</span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {record.areas_for_improvement?.map((a, i) => (
                          <span key={i} className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">{a}</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PerformanceAnalytics;
