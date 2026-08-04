// TurnoverAnalysis.tsx - Employee Turnover Patterns and Predictions
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

interface TurnoverRecord {
  employee_id: string;
  employee_name: string;
  department: string;
  position: string;
  termination_date: string;
  reason: string;
  tenure_years: number;
  performance_rating?: number;
}

interface RetentionRisk {
  employee_id: string;
  employee_name: string;
  department: string;
  risk_level: 'High' | 'Medium' | 'Low';
  risk_factors: string[];
  probability: number;
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6'];

// Mock turnover data
const mockTurnoverData: TurnoverRecord[] = [
  { employee_id: 'OLD001', employee_name: 'Former Employee 1', department: 'IT', position: 'Developer', termination_date: '2024-01-15', reason: 'Better Opportunity', tenure_years: 2, performance_rating: 4.2 },
  { employee_id: 'OLD002', employee_name: 'Former Employee 2', department: 'Sales', position: 'Sales Rep', termination_date: '2024-02-20', reason: 'Career Change', tenure_years: 1.5, performance_rating: 3.8 },
  { employee_id: 'OLD003', employee_name: 'Former Employee 3', department: 'HR', position: 'HR Specialist', termination_date: '2024-03-10', reason: 'Relocation', tenure_years: 3, performance_rating: 4.0 },
  { employee_id: 'OLD004', employee_name: 'Former Employee 4', department: 'IT', position: 'Developer', termination_date: '2024-04-05', reason: 'Work-Life Balance', tenure_years: 1, performance_rating: 3.5 },
  { employee_id: 'OLD005', employee_name: 'Former Employee 5', department: 'Finance', position: 'Analyst', termination_date: '2024-05-12', reason: 'Better Opportunity', tenure_years: 4, performance_rating: 4.5 },
  { employee_id: 'OLD006', employee_name: 'Former Employee 6', department: 'Sales', position: 'Manager', termination_date: '2024-06-18', reason: 'Retirement', tenure_years: 15, performance_rating: 4.7 }
];

const monthlyTurnoverData = [
  { month: 'Jan', voluntary: 1, involuntary: 0, total: 1 },
  { month: 'Feb', voluntary: 1, involuntary: 0, total: 1 },
  { month: 'Mar', voluntary: 0, involuntary: 1, total: 1 },
  { month: 'Apr', voluntary: 1, involuntary: 0, total: 1 },
  { month: 'May', voluntary: 1, involuntary: 0, total: 1 },
  { month: 'Jun', voluntary: 1, involuntary: 0, total: 1 }
];

const retentionRiskData: RetentionRisk[] = [
  { employee_id: 'EMP002', employee_name: 'John Dickens', department: 'IT', risk_level: 'Low', risk_factors: ['High Performance', 'Good Tenure'], probability: 15 },
  { employee_id: 'EMP003', employee_name: 'Jane Doe', department: 'Sales', risk_level: 'Medium', risk_factors: ['High Stress', 'Market Demand'], probability: 45 },
  { employee_id: 'EMP006', employee_name: 'David Chen', department: 'IT', risk_level: 'Low', risk_factors: ['Recent Promotion'], probability: 20 },
  { employee_id: 'EMP007', employee_name: 'Sarah Johnson', department: 'Sales', risk_level: 'High', risk_factors: ['High Skills', 'External Offers', 'Long Tenure'], probability: 75 }
];

export const TurnoverAnalysis: React.FC = () => {
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [selectedReason, setSelectedReason] = useState<string>('All');

  const filteredTurnover = useMemo(() => {
    return mockTurnoverData.filter(record => {
      if (selectedDepartment !== 'All' && record.department !== selectedDepartment) return false;
      if (selectedReason !== 'All' && record.reason !== selectedReason) return false;
      return true;
    });
  }, [selectedDepartment, selectedReason]);

  const turnoverAnalytics = useMemo(() => {
    const totalTurnover = filteredTurnover.length;
    const avgTenure = filteredTurnover.reduce((sum, r) => sum + r.tenure_years, 0) / filteredTurnover.length;
    const avgRating = filteredTurnover.reduce((sum, r) => sum + (r.performance_rating || 0), 0) / filteredTurnover.length;

    const reasonDistribution = filteredTurnover.reduce((acc, record) => {
      acc[record.reason] = (acc[record.reason] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const departmentTurnover = filteredTurnover.reduce((acc, record) => {
      acc[record.department] = (acc[record.department] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const turnoverByTenure = filteredTurnover.reduce((acc, record) => {
      if (record.tenure_years < 1) acc['<1 year'] = (acc['<1 year'] || 0) + 1;
      else if (record.tenure_years < 2) acc['1-2 years'] = (acc['1-2 years'] || 0) + 1;
      else if (record.tenure_years < 5) acc['2-5 years'] = (acc['2-5 years'] || 0) + 1;
      else acc['5+ years'] = (acc['5+ years'] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalTurnover,
      avgTenure: avgTenure.toFixed(1),
      avgRating: avgRating.toFixed(2),
      reasonDistribution,
      departmentTurnover,
      turnoverByTenure
    };
  }, [filteredTurnover]);

  const departments = [...new Set(mockTurnoverData.map(d => d.department))];
  const reasons = [...new Set(mockTurnoverData.map(d => d.reason))];

  const reasonChartData = Object.entries(turnoverAnalytics.reasonDistribution).map(([name, value]) => ({ name, value }));
  const deptChartData = Object.entries(turnoverAnalytics.departmentTurnover).map(([name, value]) => ({ name, value }));
  const tenureChartData = Object.entries(turnoverAnalytics.turnoverByTenure).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          📉 Turnover Analysis
        </h1>
        <p className="text-gray-600 mt-1">
          Monitor employee turnover patterns, identify risk factors, and improve retention
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
              <label className="block text-sm font-medium mb-2">Reason</label>
              <select
                className="border rounded-lg px-4 py-2"
                value={selectedReason}
                onChange={(e) => setSelectedReason(e.target.value)}
              >
                <option value="All">All Reasons</option>
                {reasons.map(reason => (
                  <option key={reason} value={reason}>{reason}</option>
                ))}
              </select>
            </div>
            <Button
              onClick={() => {
                setSelectedDepartment('All');
                setSelectedReason('All');
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
        <Card className="bg-gradient-to-br from-red-50 to-red-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-red-700">{turnoverAnalytics.totalTurnover}</div>
                <div className="text-sm text-red-600">Total Departures</div>
              </div>
              <span className="text-4xl">🚪</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{turnoverAnalytics.avgTenure} yrs</div>
                <div className="text-sm text-blue-600">Avg Tenure at Exit</div>
              </div>
              <span className="text-4xl">⏱️</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-yellow-700">{turnoverAnalytics.avgRating}</div>
                <div className="text-sm text-yellow-600">Avg Rating at Exit</div>
              </div>
              <span className="text-4xl">⭐</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-700">{retentionRiskData.length}</div>
                <div className="text-sm text-orange-600">At-Risk Employees</div>
              </div>
              <span className="text-4xl">⚠️</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Monthly Turnover Trend */}
        <Card>
          <CardHeader>
            <CardTitle>📈 Monthly Turnover Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={monthlyTurnoverData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="total" name="Total" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Reasons for Leaving */}
        <Card>
          <CardHeader>
            <CardTitle>🔍 Reasons for Leaving</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={reasonChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {reasonChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Turnover by Department */}
        <Card>
          <CardHeader>
            <CardTitle>🏢 Turnover by Department</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={deptChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#ec4899" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Turnover by Tenure */}
        <Card>
          <CardHeader>
            <CardTitle>⏱️ Turnover by Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={tenureChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Retention Risk Alert */}
      <Card className="mb-8 border-2 border-orange-200">
        <CardHeader>
          <CardTitle className="text-orange-700">⚠️ Retention Risk Alert</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {retentionRiskData.map(risk => (
              <div key={risk.employee_id} className={`p-4 rounded-lg border-2 ${
                risk.risk_level === 'High' ? 'bg-red-50 border-red-300' :
                risk.risk_level === 'Medium' ? 'bg-yellow-50 border-yellow-300' :
                'bg-green-50 border-green-300'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                      {risk.employee_name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="font-semibold">{risk.employee_name}</div>
                      <div className="text-sm text-gray-600">{risk.department}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${
                      risk.risk_level === 'High' ? 'text-red-600' :
                      risk.risk_level === 'Medium' ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {risk.risk_level} Risk
                    </div>
                    <div className="text-sm text-gray-600">{risk.probability}% probability</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {risk.risk_factors.map((factor, i) => (
                    <span key={i} className="text-xs bg-white px-2 py-1 rounded border">
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Turnover Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Employee Turnover Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Employee</th>
                  <th className="text-left p-3">Department</th>
                  <th className="text-left p-3">Position</th>
                  <th className="text-left p-3">Termination Date</th>
                  <th className="text-left p-3">Tenure</th>
                  <th className="text-left p-3">Reason</th>
                  <th className="text-left p-3">Rating</th>
                </tr>
              </thead>
              <tbody>
                {filteredTurnover.map(record => (
                  <tr key={record.employee_id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{record.employee_name}</td>
                    <td className="p-3">{record.department}</td>
                    <td className="p-3">{record.position}</td>
                    <td className="p-3">{record.termination_date}</td>
                    <td className="p-3">{record.tenure_years} years</td>
                    <td className="p-3">{record.reason}</td>
                    <td className="p-3">{record.performance_rating ? record.performance_rating.toFixed(1) : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Insights Panel */}
      <Card className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardHeader>
          <CardTitle>💡 Turnover Insights & Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">📊</span>
              <div>
                <div className="font-semibold">Top Reason: Better Opportunities</div>
                <div className="text-sm text-gray-600">Consider reviewing compensation packages and career growth paths.</div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <div className="font-semibold">Critical Tenure: First 2 Years</div>
                <div className="text-sm text-gray-600">Focus on onboarding and early-career support to reduce early turnover.</div>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <span className="text-2xl">🎯</span>
              <div>
                <div className="font-semibold">High-Performing Retention</div>
                <div className="text-sm text-gray-600">Employees with ratings 4.5+ stay longer. Invest in performance development.</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TurnoverAnalysis;
