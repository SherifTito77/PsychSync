// WorkforceDemographics.tsx - Workforce Demographics Analytics
import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, PieChart, Pie, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

interface Employee {
  id: string;
  name: string;
  position: string;
  department: string;
  location: string;
  status: string;
  age?: number;
  gender?: string;
  education?: string;
  yearsOfService?: number;
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6'];

// Mock employee demographics data
const mockEmployees: Employee[] = [
  { id: 'EMP001', name: 'Admin User', position: 'Administrator', department: 'Administration', location: 'Headquarters', status: 'Active', age: 45, gender: 'Female', education: 'Masters', yearsOfService: 8 },
  { id: 'EMP002', name: 'John Dickens', position: 'Software Engineer', department: 'IT', location: 'Headquarters', status: 'Active', age: 32, gender: 'Male', education: 'Bachelors', yearsOfService: 3 },
  { id: 'EMP003', name: 'Jane Doe', position: 'Sales Manager', department: 'Sales', location: 'Headquarters', status: 'Active', age: 38, gender: 'Female', education: 'MBA', yearsOfService: 5 },
  { id: 'EMP004', name: 'Bob Smith', position: 'HR Manager', department: 'HR', location: 'Headquarters', status: 'Active', age: 42, gender: 'Male', education: 'Masters', yearsOfService: 7 },
  { id: 'EMP005', name: 'Alice Williams', position: 'Accountant', department: 'Finance', location: 'Branch Office', status: 'Active', age: 29, gender: 'Female', education: 'Bachelors', yearsOfService: 2 },
  { id: 'EMP006', name: 'David Chen', position: 'Developer', department: 'IT', location: 'Headquarters', status: 'Active', age: 27, gender: 'Male', education: 'Masters', yearsOfService: 4 },
  { id: 'EMP007', name: 'Sarah Johnson', position: 'Marketing Lead', department: 'Sales', location: 'Branch Office', status: 'Active', age: 35, gender: 'Female', education: 'MBA', yearsOfService: 6 },
  { id: 'EMP008', name: 'Michael Brown', position: 'Analyst', department: 'Finance', location: 'Headquarters', status: 'Active', age: 31, gender: 'Male', education: 'Bachelors', yearsOfService: 3 },
  { id: 'EMP009', name: 'Emily Davis', position: 'Recruiter', department: 'HR', location: 'Branch Office', status: 'Active', age: 28, gender: 'Female', education: 'Masters', yearsOfService: 2 },
  { id: 'EMP010', name: 'Robert Wilson', position: 'SysAdmin', department: 'IT', location: 'Headquarters', status: 'Active', age: 40, gender: 'Male', education: 'Bachelors', yearsOfService: 10 }
];

export const WorkforceDemographics: React.FC = () => {
  const [selectedDepartment, setSelectedDepartment] = useState<string>('All');
  const [selectedLocation, setSelectedLocation] = useState<string>('All');

  // Filter employees
  const filteredEmployees = useMemo(() => {
    return mockEmployees.filter(emp => {
      if (selectedDepartment !== 'All' && emp.department !== selectedDepartment) return false;
      if (selectedLocation !== 'All' && emp.location !== selectedLocation) return false;
      return true;
    });
  }, [selectedDepartment, selectedLocation]);

  // Calculate demographics
  const demographics = useMemo(() => {
    const genderDistribution = filteredEmployees.reduce((acc, emp) => {
      const gender = emp.gender || 'Unknown';
      acc[gender] = (acc[gender] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const educationDistribution = filteredEmployees.reduce((acc, emp) => {
      const edu = emp.education || 'Unknown';
      acc[edu] = (acc[edu] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const ageGroups = filteredEmployees.reduce((acc, emp) => {
      const age = emp.age || 0;
      if (age < 30) acc['20-29'] = (acc['20-29'] || 0) + 1;
      else if (age < 40) acc['30-39'] = (acc['30-39'] || 0) + 1;
      else if (age < 50) acc['40-49'] = (acc['40-49'] || 0) + 1;
      else acc['50+'] = (acc['50+'] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const tenureGroups = filteredEmployees.reduce((acc, emp) => {
      const years = emp.yearsOfService || 0;
      if (years < 2) acc['<2 years'] = (acc['<2 years'] || 0) + 1;
      else if (years < 5) acc['2-5 years'] = (acc['2-5 years'] || 0) + 1;
      else if (years < 10) acc['5-10 years'] = (acc['5-10 years'] || 0) + 1;
      else acc['10+ years'] = (acc['10+ years'] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const avgAge = filteredEmployees.reduce((sum, emp) => sum + (emp.age || 0), 0) / filteredEmployees.length;
    const avgTenure = filteredEmployees.reduce((sum, emp) => sum + (emp.yearsOfService || 0), 0) / filteredEmployees.length;

    return {
      totalEmployees: filteredEmployees.length,
      avgAge: avgAge.toFixed(1),
      avgTenure: avgTenure.toFixed(1),
      genderDistribution,
      educationDistribution,
      ageGroups,
      tenureGroups,
      genderDiversity: Object.keys(genderDistribution).length,
      educationDiversity: Object.keys(educationDistribution).length
    };
  }, [filteredEmployees]);

  // Prepare chart data
  const genderChartData = Object.entries(demographics.genderDistribution).map(([name, value]) => ({ name, value }));
  const educationChartData = Object.entries(demographics.educationDistribution).map(([name, value]) => ({ name, value }));
  const ageChartData = Object.entries(demographics.ageGroups).map(([name, value]) => ({ name, value }));
  const tenureChartData = Object.entries(demographics.tenureGroups).map(([name, value]) => ({ name, value }));

  const departments = [...new Set(mockEmployees.map(e => e.department))];
  const locations = [...new Set(mockEmployees.map(e => e.location))];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          👥 Workforce Demographics
        </h1>
        <p className="text-gray-600 mt-1">
          Comprehensive analysis of your workforce composition, diversity, and distribution
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
            <Button
              onClick={() => {
                setSelectedDepartment('All');
                setSelectedLocation('All');
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
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700">{demographics.totalEmployees}</div>
                <div className="text-sm text-blue-600">Total Employees</div>
              </div>
              <span className="text-4xl">👥</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700">{demographics.avgAge}</div>
                <div className="text-sm text-purple-600">Average Age</div>
              </div>
              <span className="text-4xl">🎂</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700">{demographics.avgTenure} yrs</div>
                <div className="text-sm text-green-600">Avg Tenure</div>
              </div>
              <span className="text-4xl">⏱️</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-700">{demographics.genderDiversity}</div>
                <div className="text-sm text-orange-600">Gender Categories</div>
              </div>
              <span className="text-4xl">🌈</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Gender Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>⚧️ Gender Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={genderChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {genderChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Age Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>🎂 Age Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ageChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Education Level */}
        <Card>
          <CardHeader>
            <CardTitle>🎓 Education Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={educationChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Tenure Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>⏱️ Years of Service Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={tenureChartData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="value" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Employee Table */}
      <Card>
        <CardHeader>
          <CardTitle>👥 Employee Demographics Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Name</th>
                  <th className="text-left p-3">Department</th>
                  <th className="text-left p-3">Location</th>
                  <th className="text-left p-3">Age</th>
                  <th className="text-left p-3">Gender</th>
                  <th className="text-left p-3">Education</th>
                  <th className="text-left p-3">Tenure</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map(emp => (
                  <tr key={emp.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{emp.name}</td>
                    <td className="p-3">{emp.department}</td>
                    <td className="p-3">{emp.location}</td>
                    <td className="p-3">{emp.age || 'N/A'}</td>
                    <td className="p-3">{emp.gender || 'N/A'}</td>
                    <td className="p-3">{emp.education || 'N/A'}</td>
                    <td className="p-3">{emp.yearsOfService ? `${emp.yearsOfService} years` : 'N/A'}</td>
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

export default WorkforceDemographics;
