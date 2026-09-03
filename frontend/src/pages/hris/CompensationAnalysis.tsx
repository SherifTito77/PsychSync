// CompensationAnalysis.tsx - Pay Equity and Compensation Benchmarking
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, ScatterChart, Scatter, LineChart, Line, PieChart, Pie,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ZAxis
} from 'recharts';

interface CompensationData {
  employee_id: string;
  employee_name: string;
  department: string;
  position: string;
  salary: number;
  bonus: number;
  total_compensation: number;
  performance_rating: number;
  years_of_experience: number;
  gender?: string;
  location: string;
}

const COLORS01 = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981'];

const mockCompensationData: CompensationData[] = [
  { employee_id: 'EMP001', employee_name: 'Admin User', department: 'Administration', position: 'Administrator', salary: 95000, bonus: 15000, total_compensation: 110000, performance_rating: 4.5, years_of_experience: 8, gender: 'Female', location: 'Headquarters' },
  { employee_id: 'EMP002', employee_name: 'John Dickens', department: 'IT', position: 'Software Engineer', salary: 115000, bonus: 20000, total_compensation: 135000, performance_rating: 4.8, years_of_experience: 5, gender: 'Male', location: 'Headquarters' },
  { employee_id: 'EMP003', employee_name: 'Jane Doe', department: 'Sales', position: 'Sales Manager', salary: 105000, bonus: 35000, total_compensation: 140000, performance_rating: 4.2, years_of_experience: 6, gender: 'Female', location: 'Headquarters' },
  { employee_id: 'EMP004', employee_name: 'Bob Smith', department: 'HR', position: 'HR Manager', salary: 90000, bonus: 12000, total_compensation: 102000, performance_rating: 4.0, years_of_experience: 7, gender: 'Male', location: 'Headquarters' },
  { employee_id: 'EMP005', employee_name: 'Alice Williams', department: 'Finance', position: 'Accountant', salary: 75000, bonus: 8000, total_compensation: 83000, performance_rating: 4.6, years_of_experience: 3, gender: 'Female', location: 'Branch Office' },
  { employee_id: 'EMP006', employee_name: 'David Chen', department: 'IT', position: 'Developer', salary: 110000, bonus: 18000, total_compensation: 128000, performance_rating: 4.3, years_of_experience: 4, gender: 'Male', location: 'Headquarters' },
  { employee_id: 'EMP007', employee_name: 'Sarah Johnson', department: 'Sales', position: 'Marketing Lead', salary: 100000, bonus: 30000, total_compensation: 130000, performance_rating: 4.7, years_of_experience: 5, gender: 'Female', location: 'Branch Office' },
  { employee_id: 'EMP008', employee_name: 'Michael Brown', department: 'Finance', position: 'Analyst', salary: 80000, bonus: 10000, total_compensation: 90000, performance_rating: 4.1, years_of_experience: 3, gender: 'Male', location: 'Headquarters' }
];

const salaryBenchmarkData = [
  { position: 'Software Engineer', market_avg: 120000, our_avg: 112500 },
  { position: 'Sales Manager', market_avg: 130000, our_avg: 140000 },
  { position: 'HR Manager', market_avg: 95000, our_avg: 102000 },
  { position: 'Accountant', market_avg: 85000, our_avg: 83000 },
  { position: 'Administrator', market_avg: 100000, our_avg: 110000 }
];

export const CompensationAnalysis: React.FC = () => {
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [selectedLocation, setSelectedLocation] = useState<string>('All');

  const filteredData = useMemo(() => {
    return mockCompensationData.filter(emp => {
      if (selectedDepartment !== 'All' && emp.department !== selectedDepartment) return false;
      if (selectedLocation !== 'All' && emp.location !== selectedLocation) return false;
      return true;
    });
  }, [selectedDepartment, selectedLocation]);

  const analytics = useMemo(() => {
    const totalPayroll = filteredData.reduce((sum, emp) => sum + emp.total_compensation, 0);
    const avgSalary = filteredData.reduce((sum, emp) => sum + emp.salary, 0) / filteredData.length;
    const avgBonus = filteredData.reduce((sum, emp) => sum + emp.bonus, 0) / filteredData.length;
    const avgTotalComp = filteredData.reduce((sum, emp) => sum + emp.total_compensation, 0) / filteredData.length;

    const deptAvg = filteredData.reduce((acc, emp) => {
      if (!acc[emp.department]) {
        acc[emp.department] = { total: 0, count: 0 };
      }
      acc[emp.department].total += emp.total_compensation;
      acc[emp.department].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>);

    const deptCompensation = Object.entries(deptAvg).map(([dept, data]) => ({
      department: dept,
      avgComp: Math.round(data.total / data.count)
    }));

    const genderPayGap = filteredData.reduce((acc, emp) => {
      const gender = emp.gender || 'Unknown';
      if (!acc[gender]) {
        acc[gender] = { total: 0, count: 0 };
      }
      acc[gender].total += emp.total_compensation;
      acc[gender].count += 1;
      return acc;
    }, {} as Record<string, { total: number; count: number }>);

    const genderCompData = Object.entries(genderPayGap).map(([gender, data]) => ({
      gender,
      avgComp: Math.round(data.total / data.count)
    }));

    return {
      totalPayroll,
      avgSalary: Math.round(avgSalary),
      avgBonus: Math.round(avgBonus),
      avgTotalComp: Math.round(avgTotalComp),
      deptCompensation,
      genderCompData
    };
  }, [filteredData]);

  const scatterData = filteredData.map(emp => ({
    x: emp.years_of_experience,
    y: emp.total_compensation,
    z: emp.performance_rating * 10000,
    name: emp.employee_name
  }));

  const departments = [...new Set(mockCompensationData.map(d => d.department))];
  const locations = [...new Set(mockCompensationData.map(d => d.location))];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          💰 Compensation Analysis
        </h1>
        <p className="text-gray-600 mt-1">
          Monitor pay equity, compensation benchmarks, and total rewards across the organization
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
              <label className="block text-sm font-medium mb-2">Location</label>
              <select
                className="border rounded-lg px-4 py-2"
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
              >
                <option value="All">All Locations</option>
                {locations.map(loc => (
                  <option key={loc} value={loc}>{loc}</option>
                ))}
              </select>
            </div>
            <Button onClick={() => { setSelectedDepartment('All'); setSelectedLocation('All'); }} className="mt-6">
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
                <div className="text-2xl font-bold text-green-700">${(analytics.totalPayroll / 1000000).toFixed(1)}M</div>
                <div className="text-sm text-green-600">Total Payroll</div>
              </div>
              <span className="text-4xl">💵</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-700">${analytics.avgSalary.toLocaleString()}</div>
                <div className="text-sm text-blue-600">Avg Base Salary</div>
              </div>
              <span className="text-4xl">💼</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-purple-700">${analytics.avgBonus.toLocaleString()}</div>
                <div className="text-sm text-purple-600">Avg Bonus</div>
              </div>
              <span className="text-4xl">🎁</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-orange-700">${analytics.avgTotalComp.toLocaleString()}</div>
                <div className="text-sm text-orange-600">Avg Total Comp</div>
              </div>
              <span className="text-4xl">💰</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Salary vs Performance Scatter */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>📊 Compensation vs Experience (Bubble Size = Performance)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid />
                <XAxis type="number" dataKey="x" name="Years of Experience" label={{ value: 'Years Experience', position: 'insideBottom', offset: -5 }} />
                <YAxis type="number" dataKey="y" name="Total Compensation" label={{ value: 'Compensation $', angle: -90, position: 'insideLeft' }} />
                <ZAxis type="number" dataKey="z" range={[100, 500]} name="Performance" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value, name) => {
                  if (name === 'z') return [value / 10000, 'Performance'];
                  if (name === 'y') return [`$${(value as number).toLocaleString()}`, 'Compensation'];
                  return [value, name];
                }} />
                <Scatter name="Employees" data={scatterData} fill="#6366f1" />
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Department Compensation */}
        <Card>
          <CardHeader>
            <CardTitle>🏢 Average Compensation by Department</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.deptCompensation}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" />
                <YAxis />
                <Tooltip formatter={(value) => `$${(value as number).toLocaleString()}`} />
                <Bar dataKey="avgComp" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Gender Pay Gap */}
        <Card>
          <CardHeader>
            <CardTitle>⚖️ Compensation by Gender</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.genderCompData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="gender" />
                <YAxis />
                <Tooltip formatter={(value) => `$${(value as number).toLocaleString()}`} />
                <Bar dataKey="avgComp" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Market Benchmark */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>🎯 Salary Benchmark Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={salaryBenchmarkData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="position" />
                <YAxis />
                <Tooltip formatter={(value) => `$${(value as number).toLocaleString()}`} />
                <Legend />
                <Bar dataKey="market_avg" name="Market Average" fill="#ec4899" fillOpacity={0.7} />
                <Bar dataKey="our_avg" name="Our Average" fill="#10b981" fillOpacity={0.7} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Compensation Table */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Compensation Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Employee</th>
                  <th className="text-left p-3">Department</th>
                  <th className="text-right p-3">Base Salary</th>
                  <th className="text-right p-3">Bonus</th>
                  <th className="text-right p-3">Total Comp</th>
                  <th className="text-right p-3">Performance</th>
                  <th className="text-right p-3">Experience</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map(emp => (
                  <tr key={emp.employee_id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <div>
                        <div className="font-medium">{emp.employee_name}</div>
                        <div className="text-sm text-gray-600">{emp.position}</div>
                      </div>
                    </td>
                    <td className="p-3">{emp.department}</td>
                    <td className="p-3 text-right">${emp.salary.toLocaleString()}</td>
                    <td className="p-3 text-right">${emp.bonus.toLocaleString()}</td>
                    <td className="p-3 text-right font-semibold">${emp.total_compensation.toLocaleString()}</td>
                    <td className="p-3 text-right">{emp.performance_rating.toFixed(1)}</td>
                    <td className="p-3 text-right">{emp.years_of_experience} yrs</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Pay Equity Insights */}
      <Card className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardHeader>
          <CardTitle>⚖️ Pay Equity Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Gender Pay Gap</div>
              <div className="text-2xl font-bold text-green-600">~3%</div>
              <div className="text-xs text-gray-500 mt-1">Below industry avg of 5%</div>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Competitive Position</div>
              <div className="text-2xl font-bold text-blue-600">+5%</div>
              <div className="text-xs text-gray-500 mt-1">Above market average</div>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="text-sm text-gray-600 mb-2">Performance Correlation</div>
              <div className="text-2xl font-bold text-purple-600">Strong</div>
              <div className="text-xs text-gray-500 mt-1">Pay aligns with performance</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompensationAnalysis;
