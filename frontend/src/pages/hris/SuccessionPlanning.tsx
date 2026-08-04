// SuccessionPlanning.tsx - Leadership Pipeline and Readiness Analysis
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ZAxis
} from 'recharts';

interface SuccessionCandidate {
  employee_id: string;
  employee_name: string;
  current_role: string;
  department: string;
  potential_role: string;
  readiness_score: number;
  performance_rating: number;
  years_in_role: number;
  leadership_score: number;
  risk_of_leaving: 'Low' | 'Medium' | 'High';
  timeline: 'Ready Now' | '1-2 Years' | '2-3 Years' | '3+ Years';
}

interface KeyPosition {
  position_id: string;
  position_title: string;
  department: string;
  incumbent: string;
  risk_level: 'Critical' | 'High' | 'Medium' | 'Low';
  successors: number;
  ready_now: number;
}

const COLORS04 = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6'];

const mockCandidates: SuccessionCandidate[] = [
  { employee_id: 'EMP002', employee_name: 'John Dickens', current_role: 'Senior Developer', department: 'IT', potential_role: 'Engineering Manager', readiness_score: 85, performance_rating: 4.8, years_in_role: 3, leadership_score: 78, risk_of_leaving: 'Low', timeline: '1-2 Years' },
  { employee_id: 'EMP003', employee_name: 'Jane Doe', current_role: 'Sales Manager', department: 'Sales', potential_role: 'Sales Director', readiness_score: 92, performance_rating: 4.7, years_in_role: 4, leadership_score: 88, risk_of_leaving: 'Medium', timeline: 'Ready Now' },
  { employee_id: 'EMP004', employee_name: 'Bob Smith', current_role: 'HR Manager', department: 'HR', potential_role: 'HR Director', readiness_score: 78, performance_rating: 4.5, years_in_role: 5, leadership_score: 82, risk_of_leaving: 'Low', timeline: '1-2 Years' },
  { employee_id: 'EMP006', employee_name: 'David Chen', current_role: 'Developer', department: 'IT', potential_role: 'Tech Lead', readiness_score: 72, performance_rating: 4.3, years_in_role: 2, leadership_score: 65, risk_of_leaving: 'Medium', timeline: '2-3 Years' },
  { employee_id: 'EMP007', employee_name: 'Sarah Johnson', current_role: 'Marketing Lead', department: 'Sales', potential_role: 'VP Marketing', readiness_score: 88, performance_rating: 4.6, years_in_role: 3, leadership_score: 85, risk_of_leaving: 'Low', timeline: 'Ready Now' }
];

const mockKeyPositions: KeyPosition[] = [
  { position_id: 'POS001', position_title: 'Engineering Manager', department: 'IT', incumbent: 'Current Manager', risk_level: 'Critical', successors: 3, ready_now: 1 },
  { position_id: 'POS002', position_title: 'Sales Director', department: 'Sales', incumbent: 'Current Director', risk_level: 'High', successors: 2, ready_now: 1 },
  { position_id: 'POS003', position_title: 'HR Director', department: 'HR', incumbent: 'Current Director', risk_level: 'Medium', successors: 2, ready_now: 0 },
  { position_id: 'POS004', position_title: 'VP Marketing', department: 'Sales', incumbent: 'Current VP', risk_level: 'High', successors: 1, ready_now: 1 },
  { position_id: 'POS005', position_title: 'Tech Lead', department: 'IT', incumbent: 'Current Lead', risk_level: 'Critical', successors: 4, ready_now: 0 }
];

const pipelineHealthData = [
  { level: 'Executive', ready: 2, gap: 3 },
  { level: 'Director', ready: 4, gap: 2 },
  { level: 'Manager', ready: 8, gap: 1 },
  { level: 'Team Lead', ready: 12, gap: 0 }
];

export const SuccessionPlanning: React.FC = () => {
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [selectedTimeline, setSelectedTimeline] = useState<string>('All');

  const filteredCandidates = useMemo(() => {
    return mockCandidates.filter(candidate => {
      if (selectedDepartment !== 'All' && candidate.department !== selectedDepartment) return false;
      if (selectedTimeline !== 'All' && candidate.timeline !== selectedTimeline) return false;
      return true;
    });
  }, [selectedDepartment, selectedTimeline]);

  const analytics = useMemo(() => {
    const readyNow = filteredCandidates.filter(c => c.timeline === 'Ready Now').length;
    const totalCandidates = filteredCandidates.length;
    const avgReadiness = filteredCandidates.reduce((sum, c) => sum + c.readiness_score, 0) / filteredCandidates.length;
    const highPotential = filteredCandidates.filter(c => c.readiness_score >= 85).length;

    const readinessDistribution = filteredCandidates.reduce((acc, candidate) => {
      acc[candidate.timeline] = (acc[candidate.timeline] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const riskDistribution = filteredCandidates.reduce((acc, candidate) => {
      acc[candidate.risk_of_leaving] = (acc[candidate.risk_of_leaving] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      readyNow,
      totalCandidates,
      avgReadiness: avgReadiness.toFixed(1),
      highPotential,
      readinessDistribution,
      riskDistribution
    };
  }, [filteredCandidates]);

  const readinessChartData = Object.entries(analytics.readinessDistribution).map(([name, value]) => ({ name, value }));
  const riskChartData = Object.entries(analytics.riskDistribution).map(([name, value]) => ({ name, value }));

  const scatterData = filteredCandidates.map(candidate => ({
    x: candidate.years_in_role,
    y: candidate.readiness_score,
    z: candidate.performance_rating * 20,
    name: candidate.employee_name
  }));

  const departments = [...new Set(mockCandidates.map(c => c.department))];
  const timelines = ['All', 'Ready Now', '1-2 Years', '2-3 Years', '3+ Years'];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          🎯 Succession Planning
        </h1>
        <p className="text-gray-600 mt-1">
          Identify future leaders, build leadership pipeline, and ensure organizational continuity
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
              <label className="block text-sm font-medium mb-2">Timeline</label>
              <select
                className="border rounded-lg px-4 py-2"
                value={selectedTimeline}
                onChange={(e) => setSelectedTimeline(e.target.value)}
              >
                {timelines.map(timeline => (
                  <option key={timeline} value={timeline}>{timeline}</option>
                ))}
              </select>
            </div>
            <Button
              onClick={() => {
                setSelectedDepartment('All');
                setSelectedTimeline('All');
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
        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700">{analytics.readyNow}</div>
                <div className="text-sm text-green-600">Ready Now</div>
              </div>
              <span className="text-4xl">✅</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{analytics.totalCandidates}</div>
                <div className="text-sm text-blue-600">Total Candidates</div>
              </div>
              <span className="text-4xl">👥</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700">{analytics.avgReadiness}%</div>
                <div className="text-sm text-purple-600">Avg Readiness</div>
              </div>
              <span className="text-4xl">📊</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-yellow-700">{analytics.highPotential}</div>
                <div className="text-sm text-yellow-600">High Potential</div>
              </div>
              <span className="text-4xl">⭐</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Pipeline Health */}
        <Card>
          <CardHeader>
            <CardTitle>📊 Leadership Pipeline Health</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={pipelineHealthData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="level" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="ready" name="Ready" fill="#10b981" />
                <Bar dataKey="gap" name="Gap" fill="#f43f5e" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Readiness Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>🕐 Readiness Timeline Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={readinessChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {readinessChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS04[index % COLORS04.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Risk Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>⚠️ Risk of Losing Candidates</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={riskChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Performance vs Readiness Scatter */}
        <Card>
          <CardHeader>
            <CardTitle>🎯 Performance vs Readiness (Size = Rating)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid />
                <XAxis type="number" dataKey="x" name="Years in Role" label={{ value: 'Years in Role', position: 'insideBottom', offset: -5 }} />
                <YAxis type="number" dataKey="y" name="Readiness Score" label={{ value: 'Readiness', angle: -90, position: 'insideLeft' }} />
                <ZAxis type="number" dataKey="z" range={[50, 200]} name="Performance" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value, name) => {
                  if (name === 'z') return [value / 20, 'Rating'];
                  return [value, name];
                }} />
                <Scatter name="Candidates" data={scatterData} fill="#6366f1" />
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Key Positions */}
      <Card className="mb-8 border-2 border-orange-200">
        <CardHeader>
          <CardTitle className="text-orange-700">🔑 Key Positions & Succession Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mockKeyPositions.map(position => (
              <div key={position.position_id} className={`p-4 rounded-lg border-2 ${
                position.risk_level === 'Critical' ? 'bg-red-50 border-red-300' :
                position.risk_level === 'High' ? 'bg-orange-50 border-orange-300' :
                position.risk_level === 'Medium' ? 'bg-yellow-50 border-yellow-300' :
                'bg-green-50 border-green-300'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <div className="font-semibold text-lg">{position.position_title}</div>
                    <div className="text-sm text-gray-600">{position.department} • Incumbent: {position.incumbent}</div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-bold ${
                      position.risk_level === 'Critical' ? 'text-red-600' :
                      position.risk_level === 'High' ? 'text-orange-600' :
                      'text-yellow-600'
                    }`}>
                      {position.risk_level} Risk
                    </div>
                    <div className="text-xs text-gray-600">{position.successors} successors</div>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full ${position.ready_now > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {position.ready_now} Ready Now
                    </span>
                    <span className="text-gray-600">
                      {position.successors - position.ready_now} in development
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top Candidates */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>🏆 Top Succession Candidates</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredCandidates
              .sort((a, b) => b.readiness_score - a.readiness_score)
              .slice(0, 5)
              .map((candidate, index) => (
                <div key={candidate.employee_id} className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="text-2xl">🥇</div>
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                      {candidate.employee_name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="font-semibold">{candidate.employee_name}</div>
                      <div className="text-sm text-gray-600">{candidate.current_role} → {candidate.potential_role}</div>
                      <div className="text-xs text-gray-500">{candidate.department}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-6">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">{candidate.readiness_score}%</div>
                      <div className="text-xs text-gray-600">Readiness</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-purple-600">{candidate.performance_rating}</div>
                      <div className="text-xs text-gray-600">Performance</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-sm font-bold px-3 py-1 rounded-full ${
                        candidate.timeline === 'Ready Now' ? 'bg-green-100 text-green-800' :
                        candidate.timeline === '1-2 Years' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {candidate.timeline}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className={`text-sm font-bold ${
                        candidate.risk_of_leaving === 'Low' ? 'text-green-600' :
                        candidate.risk_of_leaving === 'Medium' ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {candidate.risk_of_leaving} Risk
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50">
        <CardHeader>
          <CardTitle>💡 Succession Planning Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <div className="font-semibold text-red-700 mb-2">🚨 Critical Actions</div>
              <ul className="text-sm space-y-1 text-gray-600">
                <li>• 3 key positions have "Critical" risk with no ready successors</li>
                <li>• Accelerate development programs for high-potential candidates</li>
                <li>• Consider external recruitment for Engineering Manager and Tech Lead roles</li>
              </ul>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="font-semibold text-green-700 mb-2">✅ Strengths</div>
              <ul className="text-sm space-y-1 text-gray-600">
                <li>• 2 candidates ready now for promotion (Jane Doe, Sarah Johnson)</li>
                <li>• Strong pipeline at Manager level (8 ready candidates)</li>
                <li>• Low turnover risk among top succession candidates</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SuccessionPlanning;
