// HRISAnalytics.tsx - Production-Ready HRIS Analytics Dashboard
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

export const HRISAnalytics: React.FC = () => {
  const { employees, loading, error, getEmployeesByDepartment, departments } = useHRISData();
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Filter employees by department
  const filteredEmployees = useMemo(() => {
    if (selectedDepartment === 'All') return employees;
    return getEmployeesByDepartment(selectedDepartment);
  }, [employees, selectedDepartment, getEmployeesByDepartment]);

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

    return {
      totalEmployees: employees.length,
      totalDepartments: departments.length,
      totalPositions: Object.keys(positionCounts).length,
      totalLocations: Object.keys(locationCounts).length,
      activePercentage: (activeCount / employees.length) * 100,
      departmentCounts,
      positionCounts,
      locationCounts
    };
  }, [employees, departments, getEmployeesByDepartment]);

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
          Comprehensive workforce analytics powered by HRIS integration
        </p>
      </div>

      {/* Key Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
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
      </div>

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

      {/* Position Breakdown */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>💼 Position Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(stats.positionCounts)
              .sort(([, a], [, b]) => b - a)
              .map(([position, count]) => {
                const percentage = (count / stats.totalEmployees) * 100;
                return (
                  <div key={position} className="flex items-center justify-between border-b pb-3">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{position}</div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      <div className="text-lg font-semibold text-gray-900">{count}</div>
                      <div className="text-xs text-gray-500">{percentage.toFixed(0)}%</div>
                    </div>
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>

      {/* Location Distribution */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>📍 Location Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(stats.locationCounts).map(([location, count]) => {
              const percentage = (count / stats.totalEmployees) * 100;
              return (
                <Card key={location} className="bg-gray-50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-gray-900">{location}</div>
                        <div className="text-sm text-gray-600">
                          {count} employees • {percentage.toFixed(0)}% of workforce
                        </div>
                      </div>
                      <div className="text-3xl">{location === 'Headquarters' ? '🏢' : '🏘️'}</div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Employee Directory */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>👥 Employee Directory</span>
            <span className="text-sm font-normal text-gray-500">
              {filteredEmployees.length} {filteredEmployees.length === 1 ? 'employee' : 'employees'}
              {selectedDepartment !== 'All' && ` in ${selectedDepartment}`}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredEmployees.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No employees found for the selected criteria.</p>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredEmployees.map(emp => (
                <Card key={emp.id} className="hover:shadow-lg transition-all">
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3 mb-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
                        {emp.name.split(' ').map((n: string) => n[0]).join('')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-gray-900 truncate">{emp.name}</div>
                        <div className="text-sm text-gray-600 truncate">{emp.position}</div>
                      </div>
                    </div>
                    <div className="space-y-1 text-sm">
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
                  </CardContent>
                </Card>
              ))}
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
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map((emp, index) => (
                    <tr key={emp.id} className={`border-b ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}>
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
                        <span className={`text-xs px-2 py-1 rounded ${
                          emp.status === 'Active'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {emp.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integration Info */}
      <Card className="bg-gradient-to-r from-indigo-50 to-blue-50">
        <CardHeader>
          <CardTitle>🔗 PsychSync Integration Ready</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-2">🧠 Assessments</div>
              <p className="text-gray-600">Link employees to their personality assessments and psychological profiles</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-2">📊 Analytics</div>
              <p className="text-gray-600">Combine HRIS data with behavioral analytics for deeper insights</p>
            </div>
            <div className="bg-white rounded-lg p-4">
              <div className="font-semibold text-gray-900 mb-2">🎯 Optimization</div>
              <p className="text-gray-600">Build optimal teams based on both skills and personality compatibility</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HRISAnalytics;
