// Burnout Prediction Dashboard - Combines HRIS attendance data with assessment stress scores
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHRISData } from '@/hooks/useHRISData';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface EmployeeBurnoutRisk {
  id: string;
  name: string;
  department: string;
  position: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  riskScore: number;
  factors: {
    attendanceScore: number; // from HRIS
    stressScore: number; // from assessments
    leaveFrequency: number; // from HRIS
    workloadScore: number; // from assessments
  };
  recommendations: string[];
  lastAssessmentDate: string;
}

const BurnoutPredictionDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { employees, departments } = useHRISData();
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [showDetails, setShowDetails] = useState(false);

  // Mock burnout risk data (in production, this comes from the ML model API)
  const burnoutData: EmployeeBurnoutRisk[] = employees.map(emp => {
    // Simulate risk factors based on HRIS data
    const attendanceScore = 70 + Math.random() * 30; // Higher is better
    const stressScore = 30 + Math.random() * 60; // Higher is worse
    const leaveFrequency = Math.random() * 10; // Days taken in last month
    const workloadScore = 40 + Math.random() * 50; // Higher is worse

    // Calculate overall risk score (0-100, higher is worse)
    const riskScore = (
      (100 - attendanceScore) * 0.25 +
      stressScore * 0.35 +
      leaveFrequency * 0.2 +
      workloadScore * 0.2
    );

    let riskLevel: 'low' | 'medium' | 'high' | 'critical';
    if (riskScore < 30) riskLevel = 'low';
    else if (riskScore < 50) riskLevel = 'medium';
    else if (riskScore < 70) riskLevel = 'high';
    else riskLevel = 'critical';

    const recommendations: string[] = [];
    if (stressScore > 60) recommendations.push('High stress levels detected - consider stress management program');
    if (attendanceScore < 80) recommendations.push('Attendance pattern suggests possible disengagement');
    if (leaveFrequency > 5) recommendations.push('Frequent leave may indicate burnout - check in with employee');
    if (workloadScore > 70) recommendations.push('Workload concerns identified - review current assignments');

    if (recommendations.length === 0) {
      recommendations.push('Employee appears well-balanced - continue current support');
    }

    return {
      id: emp.id,
      name: emp.name,
      department: emp.department,
      position: emp.position,
      riskLevel,
      riskScore,
      factors: {
        attendanceScore,
        stressScore,
        leaveFrequency,
        workloadScore,
      },
      recommendations,
      lastAssessmentDate: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    };
  });

  const filteredData = selectedDepartment === 'All'
    ? burnoutData
    : burnoutData.filter(d => d.department === selectedDepartment);

  const riskCounts = {
    critical: burnoutData.filter(d => d.riskLevel === 'critical').length,
    high: burnoutData.filter(d => d.riskLevel === 'high').length,
    medium: burnoutData.filter(d => d.riskLevel === 'medium').length,
    low: burnoutData.filter(d => d.riskLevel === 'low').length,
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiskBarColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Burnout Prediction Dashboard</h1>
          <p className="text-gray-600 mt-1">
            AI-powered burnout risk analysis using HRIS data + assessment scores
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate('/dashboard')}
        >
          ← Back to Dashboard
        </Button>
      </div>

      {/* Risk Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-red-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600 font-medium">Critical Risk</p>
                <p className="text-3xl font-bold text-red-700 mt-1">{riskCounts.critical}</p>
                <p className="text-xs text-red-600 mt-1">Immediate action needed</p>
              </div>
              <div className="text-4xl">🚨</div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600 font-medium">High Risk</p>
                <p className="text-3xl font-bold text-orange-700 mt-1">{riskCounts.high}</p>
                <p className="text-xs text-orange-600 mt-1">Monitor closely</p>
              </div>
              <div className="text-4xl">⚠️</div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-yellow-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-600 font-medium">Medium Risk</p>
                <p className="text-3xl font-bold text-yellow-700 mt-1">{riskCounts.medium}</p>
                <p className="text-xs text-yellow-600 mt-1">Preventive measures</p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Low Risk</p>
                <p className="text-3xl font-bold text-green-700 mt-1">{riskCounts.low}</p>
                <p className="text-xs text-green-600 mt-1">Maintain support</p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Department:</label>
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? 'Hide' : 'Show'} Details
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Employee Risk List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">
          Employee Burnout Risk Analysis
          {selectedDepartment !== 'All' && ` (${selectedDepartment})`}
        </h2>

        {filteredData
          .sort((a, b) => b.riskScore - a.riskScore)
          .map((employee) => (
            <Card key={employee.id} className={`border-l-4 ${
              employee.riskLevel === 'critical' ? 'border-l-red-500' :
              employee.riskLevel === 'high' ? 'border-l-orange-500' :
              employee.riskLevel === 'medium' ? 'border-l-yellow-500' : 'border-l-green-500'
            }`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-4">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl ${
                      employee.riskLevel === 'critical' ? 'bg-red-500' :
                      employee.riskLevel === 'high' ? 'bg-orange-500' :
                      employee.riskLevel === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                    }`}>
                      {employee.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-semibold text-gray-900">{employee.name}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(employee.riskLevel)}`}>
                          {employee.riskLevel.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        {employee.position} • {employee.department}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-gray-900">
                      {employee.riskScore.toFixed(0)}
                    </div>
                    <p className="text-xs text-gray-600">Risk Score</p>
                  </div>
                </div>

                {/* Risk Factors */}
                <div className="mb-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">Risk Factors</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Attendance</span>
                        <span>{employee.factors.attendanceScore.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${employee.factors.attendanceScore}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Stress Level</span>
                        <span>{employee.factors.stressScore.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${employee.factors.stressScore > 60 ? 'bg-red-500' : 'bg-yellow-500'}`}
                          style={{ width: `${employee.factors.stressScore}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Leave Frequency</span>
                        <span>{employee.factors.leaveFrequency.toFixed(1)} days</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${employee.factors.leaveFrequency > 5 ? 'bg-red-500' : 'bg-green-500'}`}
                          style={{ width: `${Math.min(employee.factors.leaveFrequency * 10, 100)}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Workload</span>
                        <span>{employee.factors.workloadScore.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${employee.factors.workloadScore > 70 ? 'bg-red-500' : 'bg-yellow-500'}`}
                          style={{ width: `${employee.factors.workloadScore}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="mb-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">AI Recommendations</div>
                  <ul className="space-y-1">
                    {employee.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-indigo-600 mr-2">→</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>

                {showDetails && (
                  <div className="bg-gray-50 rounded-lg p-4 text-sm">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-gray-600">Last Assessment:</span>
                        <span className="ml-2 font-medium">{employee.lastAssessmentDate}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Risk Trend:</span>
                        <span className="ml-2 font-medium text-green-600">↓ Improving</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex space-x-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/assessments?employee=${employee.id}`)}
                  >
                    View Full Assessment
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/reports?employee=${employee.id}`)}
                  >
                    Generate Report
                  </Button>
                  {employee.riskLevel === 'critical' || employee.riskLevel === 'high' ? (
                    <Button
                      size="sm"
                      className="bg-red-600 hover:bg-red-700"
                    >
                      Schedule Check-in
                    </Button>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ))}
      </div>

      {/* Summary Insights */}
      <Card className="bg-indigo-50">
        <CardHeader>
          <CardTitle className="text-indigo-900">🤖 AI-Generated Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-indigo-900">
            <div className="flex items-start">
              <span className="font-bold mr-2">1.</span>
              <span>
                <strong>{riskCounts.critical + riskCounts.high}</strong> employees require immediate attention.
                {riskCounts.critical > 0 && ` ${riskCounts.critical} are at critical risk - schedule 1:1 meetings this week.`}
              </span>
            </div>
            <div className="flex items-start">
              <span className="font-bold mr-2">2.</span>
              <span>
                Department with highest risk: <strong>{
                  departments.reduce((acc, dept) => {
                    const deptRisks = burnoutData.filter(d => d.department === dept && (d.riskLevel === 'high' || d.riskLevel === 'critical'));
                    return deptRisks.length > acc.count ? { name: dept, count: deptRisks.length } : acc;
                  }, { name: 'N/A', count: 0 }).name
                }</strong>
              </span>
            </div>
            <div className="flex items-start">
              <span className="font-bold mr-2">3.</span>
              <span>
                Primary risk factors across organization: <strong>High stress levels</strong> and <strong>workload concerns</strong>
              </span>
            </div>
            <div className="flex items-start">
              <span className="font-bold mr-2">4.</span>
              <span>
                Recommended action: Implement organization-wide stress management program and review workload distribution
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BurnoutPredictionDashboard;
