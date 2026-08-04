// HRIS Analytics Dashboard - Comprehensive workforce analytics
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHRISData } from '@/hooks/useHRISData';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface AssessmentCompletion {
  department: string;
  totalEmployees: number;
  completedAssessments: number;
  completionRate: number;
  averageScore: number;
}

const HRISAnalyticsDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { employees, departments, totalEmployees, getEmployeesByDepartment, loading } = useHRISData();
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');

  // Mock assessment completion data (in production, this comes from the API)
  const assessmentCompletionData: AssessmentCompletion[] = departments.map(dept => {
    const deptEmployees = getEmployeesByDepartment(dept);
    const completedCount = Math.floor(deptEmployees.length * 0.7); // Mock 70% completion
    return {
      department: dept,
      totalEmployees: deptEmployees.length,
      completedAssessments: completedCount,
      completionRate: (completedCount / deptEmployees.length) * 100,
      averageScore: 75 + Math.random() * 20, // Mock scores between 75-95
    };
  });

  const filteredData = selectedDepartment === 'All'
    ? assessmentCompletionData
    : assessmentCompletionData.filter(d => d.department === selectedDepartment);

  const overallCompletionRate = assessmentCompletionData.reduce((acc, curr) =>
    acc + (curr.completedAssessments / curr.totalEmployees) * curr.totalEmployees, 0) / totalEmployees;

  // Department breakdown metrics
  const departmentMetrics = departments.map(dept => {
    const deptEmployees = getEmployeesByDepartment(dept);
    return {
      name: dept,
      count: deptEmployees.length,
      percentage: (deptEmployees.length / employees.length) * 100,
    };
  }).sort((a, b) => b.count - a.count);

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">HRIS Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Comprehensive workforce and assessment analytics</p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate('/hris-connector')}
        >
          ← Back to HRIS Connector
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Employees</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{loading ? '...' : totalEmployees}</p>
              </div>
              <div className="text-4xl">👥</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Departments</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{loading ? '...' : departments.length}</p>
              </div>
              <div className="text-4xl">🏢</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Assessment Completion</p>
                <p className="text-3xl font-bold text-green-600 mt-1">
                  {loading ? '...' : `${overallCompletionRate.toFixed(0)}%`}
                </p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Performance Score</p>
                <p className="text-3xl font-bold text-purple-600 mt-1">
                  {loading ? '...' : '85.2'}
                </p>
              </div>
              <div className="text-4xl">⭐</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Department Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Department Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {departmentMetrics.map((metric) => (
              <div key={metric.name}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{metric.name}</span>
                  <span className="text-sm text-gray-600">
                    {metric.count} employees ({metric.percentage.toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-indigo-600 h-3 rounded-full transition-all"
                    style={{ width: `${metric.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Assessment Completion by Department */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Assessment Completion by Department</CardTitle>
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="All">All Departments</option>
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredData.map((data) => (
              <div key={data.department} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{data.department}</h3>
                    <p className="text-sm text-gray-600">
                      {data.completedAssessments} of {data.totalEmployees} employees completed
                    </p>
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${
                      data.completionRate >= 80 ? 'text-green-600' :
                      data.completionRate >= 60 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {data.completionRate.toFixed(0)}%
                    </div>
                    <p className="text-xs text-gray-600">completion rate</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Completion Progress</div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          data.completionRate >= 80 ? 'bg-green-500' :
                          data.completionRate >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${data.completionRate}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Average Score</div>
                    <div className="flex items-center">
                      <div className="text-lg font-semibold text-gray-900">
                        {data.averageScore.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-600 ml-2">/ 100</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Employee Directory with Assessment Links */}
      <Card>
        <CardHeader>
          <CardTitle>Employee Assessment Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {employees.map((employee) => {
              const hasCompletedAssessment = Math.random() > 0.3; // Mock completion status
              return (
                <div
                  key={employee.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-indigo-300 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                      {employee.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{employee.name}</div>
                      <div className="text-sm text-gray-600">
                        {employee.position} • {employee.department}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className={`text-sm font-medium ${
                        hasCompletedAssessment ? 'text-green-600' : 'text-yellow-600'
                      }`}>
                        {hasCompletedAssessment ? '✓ Assessment Complete' : '⏳ Pending'}
                      </div>
                      {hasCompletedAssessment && (
                        <div className="text-xs text-gray-600">Score: {(75 + Math.random() * 20).toFixed(1)}</div>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/assessments?employee=${employee.id}`)}
                    >
                      {hasCompletedAssessment ? 'View Results' : 'Start Assessment'}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              className="h-auto py-4"
              onClick={() => navigate('/team-optimizer')}
            >
              <div className="text-center">
                <div className="text-2xl mb-1">🎯</div>
                <div>Optimize Teams</div>
                <div className="text-xs opacity-75 mt-1">Create balanced teams from HRIS data</div>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4"
              onClick={() => navigate('/assessments')}
            >
              <div className="text-center">
                <div className="text-2xl mb-1">📝</div>
                <div>Run Assessments</div>
                <div className="text-xs opacity-75 mt-1">Start assessments for employees</div>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4"
              onClick={() => navigate('/reports')}
            >
              <div className="text-center">
                <div className="text-2xl mb-1">📈</div>
                <div>View Reports</div>
                <div className="text-xs opacity-75 mt-1">Generate detailed analytics reports</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HRISAnalyticsDashboard;
