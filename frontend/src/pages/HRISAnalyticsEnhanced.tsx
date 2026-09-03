// HRISAnalyticsEnhanced.tsx - HRIS Analytics with Advanced Features
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useHRISData } from '@/hooks/useHRISData';

interface Employee {
  id: string;
  name: string;
  position: string;
  department: string;
  location: string;
  status: string;
}

interface AssessmentData {
  employee_id: string;
  personality_type?: string;
  big_five?: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    neuroticism: number;
  };
  completed_date?: string;
}

export const HRISAnalyticsEnhanced: React.FC = () => {
  const { employees, loading, error, getEmployeesByDepartment, departments } = useHRISData();
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [compareList, setCompareList] = useState<string[]>([]);

  // Mock assessment data (in production, fetch from API)
  const assessmentData: Record<string, AssessmentData> = {
    'EMP001': {
      employee_id: 'EMP001',
      personality_type: 'INTJ-A',
      big_five: { openness: 85, conscientiousness: 90, extraversion: 45, agreeableness: 55, neuroticism: 30 },
      completed_date: '2024-01-15'
    },
    'EMP002': {
      employee_id: 'EMP002',
      personality_type: 'INTJ-T',
      big_five: { openness: 92, conscientiousness: 88, extraversion: 35, agreeableness: 48, neuroticism: 42 },
      completed_date: '2024-01-10'
    },
    'EMP003': {
      employee_id: 'EMP003',
      personality_type: 'ENFJ-A',
      big_five: { openness: 78, conscientiousness: 82, extraversion: 88, agreeableness: 90, neuroticism: 35 },
      completed_date: '2024-01-12'
    },
    'EMP004': {
      employee_id: 'EMP004',
      personality_type: 'ISFJ-A',
      big_five: { openness: 65, conscientiousness: 85, extraversion: 55, agreeableness: 92, neuroticism: 38 },
      completed_date: '2024-01-08'
    },
    'EMP005': {
      employee_id: 'EMP005',
      personality_type: 'ISTJ-A',
      big_five: { openness: 58, conscientiousness: 95, extraversion: 42, agreeableness: 78, neuroticism: 28 },
      completed_date: '2024-01-14'
    }
  };

  // Filter employees by department and search
  const filteredEmployees = useMemo(() => {
    let filtered = selectedDepartment === 'All'
      ? employees
      : getEmployeesByDepartment(selectedDepartment);

    if (searchTerm) {
      filtered = filtered.filter(emp =>
        emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.position.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  }, [employees, selectedDepartment, searchTerm, getEmployeesByDepartment]);

  // Calculate statistics
  const stats = useMemo(() => {
    const departmentCounts = departments.map(dept => ({
      name: dept,
      count: getEmployeesByDepartment(dept).length,
      percentage: (getEmployeesByDepartment(dept).length / employees.length) * 100
    }));

    const positionCounts = employees.reduce((acc, emp) => {
      acc[emp.position] = (acc[emp.position] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const locationCounts = employees.reduce((acc, emp) => {
      acc[emp.location] = (acc[emp.location] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const activeCount = employees.filter(e => e.status === 'Active').length;

    // Assessment completion rate
    const completedAssessments = employees.filter(e => assessmentData[e.id]).length;
    const completionRate = (completedAssessments / employees.length) * 100;

    return {
      totalEmployees: employees.length,
      totalDepartments: departments.length,
      totalPositions: Object.keys(positionCounts).length,
      totalLocations: Object.keys(locationCounts).length,
      activePercentage: (activeCount / employees.length) * 100,
      assessmentCompletion: completionRate,
      departmentCounts,
      positionCounts,
      locationCounts
    };
  }, [employees, departments, getEmployeesByDepartment, assessmentData]);

  const exportToCSV = () => {
    const headers = ['Employee ID', 'Name', 'Position', 'Department', 'Location', 'Status', 'Personality Type', 'Assessment Date'];
    const rows = filteredEmployees.map(emp => {
      const assessment = assessmentData[emp.id];
      return [
        emp.id,
        emp.name,
        emp.position,
        emp.department,
        emp.location,
        emp.status,
        assessment?.personality_type || 'Not completed',
        assessment?.completed_date || 'N/A'
      ];
    });

    const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'hris-analytics-export.csv';
    a.click();
  };

  const toggleCompare = (empId: string) => {
    if (compareList.includes(empId)) {
      setCompareList(compareList.filter(id => id !== empId));
    } else if (compareList.length < 3) {
      setCompareList([...compareList, empId]);
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-gray-600">Loading HRIS data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <Card className="bg-red-50">
          <CardContent className="p-6">
            <div className="text-red-800">
              <p className="font-semibold">Error loading HRIS data</p>
              <p className="text-sm">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-gray-900">📊 HRIS Analytics Dashboard</h1>
          <div className="flex gap-2">
            <Button
              variant={comparisonMode ? 'primary' : 'outline'}
              size="sm"
              onClick={() => {
                setComparisonMode(!comparisonMode);
                setCompareList([]);
              }}
            >
              {comparisonMode ? '✅ ' : ''}Compare Mode
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportToCSV}
            >
              📥 Export CSV
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              Grid View
            </Button>
            <Button
              variant={viewMode === 'list' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              List View
            </Button>
          </div>
        </div>
        <p className="text-gray-600">
          Comprehensive workforce analytics powered by HRIS + PsychSync integration
        </p>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="🔍 Search by name, position, department, or ID..."
                className="w-full border rounded-lg px-4 py-2"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            {searchTerm && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSearchTerm('')}
              >
                Clear
              </Button>
            )}
            <div className="text-sm text-gray-600">
              {filteredEmployees.length} {filteredEmployees.length === 1 ? 'result' : 'results'}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4 mb-8">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{stats.totalEmployees}</div>
                <div className="text-sm text-blue-600">Total Employees</div>
              </div>
              <span className="text-4xl">👥</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700">{stats.totalDepartments}</div>
                <div className="text-sm text-green-600">Departments</div>
              </div>
              <span className="text-4xl">🏢</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700">{stats.totalPositions}</div>
                <div className="text-sm text-purple-600">Positions</div>
              </div>
              <span className="text-4xl">💼</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-700">{stats.totalLocations}</div>
                <div className="text-sm text-orange-600">Locations</div>
              </div>
              <span className="text-4xl">📍</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-emerald-700">{stats.activePercentage.toFixed(0)}%</div>
                <div className="text-sm text-emerald-600">Active Rate</div>
              </div>
              <span className="text-4xl">✅</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-pink-50 to-pink-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-pink-700">{stats.assessmentCompletion.toFixed(0)}%</div>
                <div className="text-sm text-pink-600">Assessments</div>
              </div>
              <span className="text-4xl">🧠</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Employee Comparison */}
      {comparisonMode && compareList.length > 0 && (
        <Card className="mb-8 bg-gradient-to-r from-yellow-50 to-orange-50">
          <CardHeader>
            <CardTitle>🔄 Employee Comparison ({compareList.length}/3)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {compareList.map(empId => {
                const emp = employees.find(e => e.id === empId);
                const assessment = assessmentData[empId];
                if (!emp) return null;

                return (
                  <Card key={empId} className="bg-white">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                            {emp.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <div className="font-semibold">{emp.name}</div>
                            <div className="text-sm text-gray-600">{emp.position}</div>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleCompare(empId)}
                        >
                          ✕
                        </Button>
                      </div>

                      {assessment && (
                        <div className="space-y-3">
                          <div>
                            <div className="text-sm text-gray-600 mb-1">Personality Type</div>
                            <div className="font-semibold text-indigo-600">{assessment.personality_type}</div>
                          </div>

                          {assessment.big_five && (
                            <div>
                              <div className="text-sm text-gray-600 mb-2">Big Five Traits</div>
                              <div className="space-y-2">
                                {Object.entries(assessment.big_five).map(([trait, value]) => (
                                  <div key={trait}>
                                    <div className="flex justify-between text-xs mb-1">
                                      <span className="capitalize">{trait}</span>
                                      <span>{value}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                                      <div
                                        className="bg-indigo-600 h-1.5 rounded-full"
                                        style={{ width: `${value}%` }}
                                      ></div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {!assessment && (
                        <div className="text-sm text-gray-500 italic">
                          No assessment data available
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {compareList.length < 3 && (
              <p className="text-sm text-gray-600 mt-4 text-center">
                Click on employees below to add them to comparison (max 3)
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Department Distribution */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>🏢 Department Distribution</span>
            <span className="text-sm font-normal text-gray-500">
              Showing {selectedDepartment === 'All' ? 'all departments' : selectedDepartment}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <select
              className="border rounded-lg px-4 py-2 text-sm bg-white"
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
            >
              <option value="All">All Departments ({employees.length} employees)</option>
              {departments.map(dept => {
                const count = getEmployeesByDepartment(dept).length;
                return (
                  <option key={dept} value={dept}>
                    {dept} ({count} employees)
                  </option>
                );
              })}
            </select>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {stats.departmentCounts.map(dept => (
              <Card
                key={dept.name}
                className={`cursor-pointer transition-all ${
                  selectedDepartment === dept.name
                    ? 'ring-2 ring-indigo-500 bg-indigo-50'
                    : 'hover:shadow-md'
                }`}
                onClick={() => setSelectedDepartment(dept.name === selectedDepartment ? 'All' : dept.name)}
              >
                <CardContent className="p-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-indigo-600 mb-1">
                      {dept.count}
                    </div>
                    <div className="text-sm font-medium text-gray-700 mb-1">{dept.name}</div>
                    <div className="text-xs text-gray-500">{dept.percentage.toFixed(0)}% of workforce</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Employee Directory with Assessment Integration */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>👥 Employee Directory</span>
            <span className="text-sm font-normal text-gray-500">
              {filteredEmployees.length} {filteredEmployees.length === 1 ? 'employee' : 'employees'}
              {selectedDepartment !== 'All' && ` in ${selectedDepartment}`}
              {searchTerm && ` matching "${searchTerm}"`}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredEmployees.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-lg mb-2">No employees found</p>
              <p className="text-sm">Try adjusting your search or filter</p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredEmployees.map(emp => {
                const assessment = assessmentData[emp.id];
                const isSelected = compareList.includes(emp.id);

                return (
                  <Card
                    key={emp.id}
                    className={`hover:shadow-lg transition-all cursor-pointer ${
                      isSelected ? 'ring-2 ring-orange-500' : ''
                    }`}
                    onClick={() => {
                      if (comparisonMode) {
                        toggleCompare(emp.id);
                      } else {
                        setSelectedEmployee(emp);
                      }
                    }}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start space-x-3 mb-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                          {emp.name.split(' ').map((n: string) => n[0]).join('')}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-gray-900 truncate">{emp.name}</div>
                          <div className="text-sm text-gray-600 truncate">{emp.position}</div>
                        </div>
                        {comparisonMode && (
                          <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                            isSelected ? 'bg-orange-500 border-orange-500' : 'border-gray-300'
                          }`}>
                            {isSelected && <span className="text-white text-xs">✓</span>}
                          </div>
                        )}
                      </div>

                      <div className="space-y-1 text-sm mb-3">
                        <div className="flex items-center text-gray-600">
                          <span className="mr-2">🏢</span>
                          <span className="truncate">{emp.department}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="mr-2">📍</span>
                          <span className="truncate">{emp.location}</span>
                        </div>
                        <div className="flex items-center">
                          <span className="mr-2">🆔</span>
                          <span className="text-gray-500">{emp.id}</span>
                          <span className="ml-auto">
                            <span className={`text-xs px-2 py-1 rounded ${
                              emp.status === 'Active'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}>
                              {emp.status}
                            </span>
                          </span>
                        </div>
                      </div>

                      {assessment && (
                        <div className="pt-3 border-t">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-gray-600">🧠 Assessment</span>
                            <span className="text-xs font-semibold text-indigo-600">{assessment.personality_type}</span>
                          </div>
                          <div className="grid grid-cols-5 gap-1">
                            {assessment.big_five && Object.entries(assessment.big_five).slice(0, 5).map(([_, value]) => (
                              <div key={_} className="h-1 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-indigo-500"
                                  style={{ width: `${value}%` }}
                                ></div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {!assessment && (
                        <div className="pt-3 border-t">
                          <div className="text-xs text-gray-500 italic">
                            No assessment completed
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Employee</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Position</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Department</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Location</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Personality</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map((emp, index) => {
                    const assessment = assessmentData[emp.id];
                    return (
                      <tr
                        key={emp.id}
                        className={`border-b ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-indigo-50 cursor-pointer`}
                        onClick={() => setSelectedEmployee(emp)}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                              {emp.name.split(' ').map((n: string) => n[0]).join('')}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{emp.name}</div>
                              <div className="text-xs text-gray-500">{emp.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-700">{emp.position}</td>
                        <td className="py-3 px-4 text-gray-700">{emp.department}</td>
                        <td className="py-3 px-4 text-gray-700">{emp.location}</td>
                        <td className="py-3 px-4">
                          {assessment ? (
                            <span className="text-sm font-semibold text-indigo-600">
                              {assessment.personality_type}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400 italic">Not completed</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`text-xs px-2 py-1 rounded ${
                            emp.status === 'Active'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}>
                            {emp.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Employee Detail Modal */}
      {selectedEmployee && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Employee Details</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedEmployee(null)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Employee Info */}
                <div className="flex items-start space-x-4">
                  <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-3xl">
                    {selectedEmployee.name.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-gray-900">{selectedEmployee.name}</h3>
                    <p className="text-gray-600">{selectedEmployee.position}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                        {selectedEmployee.department}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {selectedEmployee.location}
                      </span>
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                        {selectedEmployee.status}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Assessment Data */}
                {assessmentData[selectedEmployee.id] && (
                  <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-6">
                    <h4 className="text-lg font-semibold mb-4">🧠 PsychSync Assessment Results</h4>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-600">Personality Type</div>
                        <div className="text-xl font-bold text-indigo-600">
                          {assessmentData[selectedEmployee.id].personality_type}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Completed</div>
                        <div className="text-xl font-bold text-gray-900">
                          {assessmentData[selectedEmployee.id].completed_date}
                        </div>
                      </div>
                    </div>

                    {assessmentData[selectedEmployee.id].big_five && (
                      <div>
                        <div className="text-sm font-semibold text-gray-700 mb-3">Big Five Personality Traits</div>
                        <div className="space-y-3">
                          {Object.entries(assessmentData[selectedEmployee.id].big_five!).map(([trait, value]) => (
                            <div key={trait}>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="capitalize font-medium">{trait}</span>
                                <span className="text-gray-600">{value}/100</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    value >= 80 ? 'bg-green-500' :
                                    value >= 60 ? 'bg-blue-500' :
                                    value >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${value}%` }}
                                ></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {!assessmentData[selectedEmployee.id] && (
                  <div className="bg-gray-50 rounded-lg p-6 text-center">
                    <div className="text-4xl mb-2">📋</div>
                    <p className="text-gray-600">No assessment completed yet</p>
                    <Button className="mt-4" size="sm">
                      Send Assessment Reminder
                    </Button>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1">
                    View Full Profile
                  </Button>
                  <Button variant="outline" className="flex-1">
                    View Assessment History
                  </Button>
                  <Button className="flex-1">
                    Edit Employee
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Integration Info */}
      <Card className="bg-gradient-to-r from-indigo-50 to-blue-50">
        <CardHeader>
          <CardTitle>🔗 HRIS + PsychSync Integration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-2">🧠 Assessment Data</div>
              <p className="text-gray-600 mb-2">Employee personality profiles are now integrated with HRIS data</p>
              <div className="text-xs text-indigo-600">{stats.assessmentCompletion.toFixed(0)}% completion rate</div>
            </div>
            <div className="bg-white rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-2">🔄 Compare Mode</div>
              <p className="text-gray-600 mb-2">Compare up to 3 employees side-by-side</p>
              <div className="text-xs text-indigo-600">Click "Compare Mode" to start</div>
            </div>
            <div className="bg-white rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-2">📥 Export Data</div>
              <p className="text-gray-600 mb-2">Export employee data with assessments to CSV</p>
              <div className="text-xs text-indigo-600">Click "Export CSV" button</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HRISAnalyticsEnhanced;
