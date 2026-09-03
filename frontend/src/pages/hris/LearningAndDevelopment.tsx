// LearningAndDevelopment.tsx - Training Effectiveness and Skill Development
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area, TreemapChart, Treemap,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

interface TrainingProgram {
  program_id: string;
  program_name: string;
  category: string;
  participants: number;
  completion_rate: number;
  avg_satisfaction: number;
  total_cost: number;
  skills_developed: string[];
}

interface EmployeeSkill {
  employee_id: string;
  employee_name: string;
  department: string;
  skills: Array<{ skill: string; level: number; last_updated: string }>;
  certifications: Array<{ name: string; date: string; status: string }>;
  training_hours_ytd: number;
}

const COLORS03 = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6'];

const mockTrainingPrograms: TrainingProgram[] = [
  { program_id: 'TRG001', program_name: 'Leadership Excellence', category: 'Leadership', participants: 24, completion_rate: 92, avg_satisfaction: 4.5, total_cost: 45000, skills_developed: ['Strategic Thinking', 'Team Management', 'Decision Making'] },
  { program_id: 'TRG002', program_name: 'Technical Skills Bootcamp', category: 'Technical', participants: 45, completion_rate: 88, avg_satisfaction: 4.7, total_cost: 35000, skills_developed: ['Programming', 'Cloud Computing', 'DevOps'] },
  { program_id: 'TRG003', program_name: 'Communication Mastery', category: 'Soft Skills', participants: 60, completion_rate: 95, avg_satisfaction: 4.6, total_cost: 28000, skills_developed: ['Public Speaking', 'Writing', 'Presentation'] },
  { program_id: 'TRG004', program_name: 'Data Analytics Fundamentals', category: 'Technical', participants: 38, completion_rate: 85, avg_satisfaction: 4.4, total_cost: 32000, skills_developed: ['SQL', 'Data Visualization', 'Statistics'] },
  { program_id: 'TRG005', program_name: 'Project Management Professional', category: 'Leadership', participants: 30, completion_rate: 90, avg_satisfaction: 4.5, total_cost: 40000, skills_developed: ['Agile', 'Scrum', 'Risk Management'] }
];

const mockEmployeeSkills: EmployeeSkill[] = [
  { employee_id: 'EMP001', employee_name: 'Admin User', department: 'Administration', skills: [{ skill: 'Leadership', level: 85, last_updated: '2024-01-15' }, { skill: 'Communication', level: 90, last_updated: '2024-01-15' }], certifications: [{ name: 'PMP', date: '2023-06-15', status: 'Active' }], training_hours_ytd: 45 },
  { employee_id: 'EMP002', employee_name: 'John Dickens', department: 'IT', skills: [{ skill: 'Programming', level: 95, last_updated: '2024-01-20' }, { skill: 'Cloud Computing', level: 88, last_updated: '2024-01-20' }], certifications: [{ name: 'AWS Solutions Architect', date: '2023-11-10', status: 'Active' }], training_hours_ytd: 72 },
  { employee_id: 'EMP003', employee_name: 'Jane Doe', department: 'Sales', skills: [{ skill: 'Negotiation', level: 92, last_updated: '2024-01-18' }, { skill: 'Communication', level: 88, last_updated: '2024-01-18' }], certifications: [{ name: 'Sales Certification', date: '2023-08-22', status: 'Active' }], training_hours_ytd: 38 },
  { employee_id: 'EMP004', employee_name: 'Bob Smith', department: 'HR', skills: [{ skill: 'Recruitment', level: 90, last_updated: '2024-01-12' }, { skill: 'Employee Relations', level: 85, last_updated: '2024-01-12' }], certifications: [{ name: 'SHRM-CP', date: '2023-05-18', status: 'Active' }], training_hours_ytd: 52 }
];

const trainingTrendData = [
  { month: 'Aug', hours: 320, programs: 12 },
  { month: 'Sep', hours: 380, programs: 15 },
  { month: 'Oct', hours: 420, programs: 18 },
  { month: 'Nov', hours: 450, programs: 20 },
  { month: 'Dec', hours: 390, programs: 16 },
  { month: 'Jan', hours: 480, programs: 22 }
];

export const LearningAndDevelopment: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const filteredPrograms = useMemo(() => {
    return mockTrainingPrograms.filter(program => {
      if (selectedCategory !== 'All' && program.category !== selectedCategory) return false;
      return true;
    });
  }, [selectedCategory]);

  const analytics = useMemo(() => {
    const totalPrograms = filteredPrograms.length;
    const totalParticipants = filteredPrograms.reduce((sum, p) => sum + p.participants, 0);
    const avgCompletion = filteredPrograms.reduce((sum, p) => sum + p.completion_rate, 0) / filteredPrograms.length;
    const avgSatisfaction = filteredPrograms.reduce((sum, p) => sum + p.avg_satisfaction, 0) / filteredPrograms.length;
    const totalCost = filteredPrograms.reduce((sum, p) => sum + p.total_cost, 0);
    const costPerParticipant = totalParticipants > 0 ? totalCost / totalParticipants : 0;

    const categoryData = filteredPrograms.reduce((acc, program) => {
      if (!acc[program.category]) {
        acc[program.category] = { participants: 0, cost: 0, count: 0 };
      }
      acc[program.category].participants += program.participants;
      acc[program.category].cost += program.total_cost;
      acc[program.category].count += 1;
      return acc;
    }, {} as Record<string, { participants: number; cost: number; count: number }>);

    const categoryStats = Object.entries(categoryData).map(([category, data]) => ({
      category,
      participants: data.participants,
      avgCost: Math.round(data.cost / data.participants)
    }));

    return {
      totalPrograms,
      totalParticipants,
      avgCompletion: avgCompletion.toFixed(1),
      avgSatisfaction: avgSatisfaction.toFixed(2),
      totalCost,
      costPerParticipant: Math.round(costPerParticipant),
      categoryStats
    };
  }, [filteredPrograms]);

  const skillGapData = [
    { skill: 'Leadership', current: 72, required: 85, gap: 13 },
    { skill: 'Technical', current: 68, required: 90, gap: 22 },
    { skill: 'Communication', current: 82, required: 85, gap: 3 },
    { skill: 'Data Analysis', current: 58, required: 80, gap: 22 },
    { skill: 'Project Management', current: 75, required: 85, gap: 10 }
  ];

  const categories = ['All', ...new Set(mockTrainingPrograms.map(p => p.category))];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          📚 Learning & Development
        </h1>
        <p className="text-gray-600 mt-1">
          Track training effectiveness, skill development, and learning progress across the organization
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Category</label>
              <select
                className="border rounded-lg px-4 py-2"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <Button onClick={() => setSelectedCategory('All')} className="mt-6">
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{analytics.totalPrograms}</div>
                <div className="text-sm text-blue-600">Active Programs</div>
              </div>
              <span className="text-4xl">📚</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700">{analytics.totalParticipants}</div>
                <div className="text-sm text-green-600">Total Participants</div>
              </div>
              <span className="text-4xl">👥</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700">{analytics.avgCompletion}%</div>
                <div className="text-sm text-purple-600">Completion Rate</div>
              </div>
              <span className="text-4xl">✅</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-700">{analytics.avgSatisfaction}</div>
                <div className="text-sm text-orange-600">Avg Satisfaction</div>
              </div>
              <span className="text-4xl">⭐</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Training Trend */}
        <Card>
          <CardHeader>
            <CardTitle>📈 Training Hours Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={trainingTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="hours" name="Training Hours" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Skill Gaps */}
        <Card>
          <CardHeader>
            <CardTitle>🎯 Skill Gap Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={skillGapData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="skill" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="current" name="Current Level" fill="#6366f1" fillOpacity={0.7} />
                <Bar dataKey="required" name="Required Level" fill="#ec4899" fillOpacity={0.7} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>📊 Training by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.categoryStats} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="category" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="participants" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Cost by Category */}
        <Card>
          <CardHeader>
            <CardTitle>💰 Cost per Participant by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics.categoryStats}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, avgCost }) => `${category}: $${avgCost}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="avgCost"
                >
                  {analytics.categoryStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS03[index % COLORS03.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value}`} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Training Programs Table */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>📋 Training Programs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Program</th>
                  <th className="text-left p-3">Category</th>
                  <th className="text-right p-3">Participants</th>
                  <th className="text-right p-3">Completion</th>
                  <th className="text-right p-3">Satisfaction</th>
                  <th className="text-right p-3">Total Cost</th>
                  <th className="text-left p-3">Skills Developed</th>
                </tr>
              </thead>
              <tbody>
                {filteredPrograms.map(program => (
                  <tr key={program.program_id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <div className="font-medium">{program.program_name}</div>
                    </td>
                    <td className="p-3">{program.category}</td>
                    <td className="p-3 text-right">{program.participants}</td>
                    <td className="p-3 text-right">
                      <span className={`px-2 py-1 rounded text-sm ${
                        program.completion_rate >= 90 ? 'bg-green-100 text-green-800' :
                        program.completion_rate >= 80 ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {program.completion_rate}%
                      </span>
                    </td>
                    <td className="p-3 text-right">{program.avg_satisfaction.toFixed(1)}</td>
                    <td className="p-3 text-right">${program.total_cost.toLocaleString()}</td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {program.skills_developed.slice(0, 3).map((skill, i) => (
                          <span key={i} className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">{skill}</span>
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

      {/* Top Learners */}
      <Card>
        <CardHeader>
          <CardTitle>🏆 Top Learners (Training Hours YTD)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {mockEmployeeSkills
              .sort((a, b) => b.training_hours_ytd - a.training_hours_ytd)
              .slice(0, 5)
              .map((emp, index) => (
                <div key={emp.employee_id} className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="text-2xl">🥇</div>
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                      {emp.employee_name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="font-semibold">{emp.employee_name}</div>
                      <div className="text-sm text-gray-600">{emp.department}</div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {emp.skills.slice(0, 2).map((s, i) => (
                          <span key={i} className="text-xs bg-white px-2 py-1 rounded border">{s.skill} ({s.level}%)</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-indigo-600">{emp.training_hours_ytd} hrs</div>
                    <div className="text-xs text-gray-600">{emp.certifications.length} Certifications</div>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LearningAndDevelopment;
