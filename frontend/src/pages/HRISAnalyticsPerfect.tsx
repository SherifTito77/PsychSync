// HRISAnalyticsPerfect.tsx - Enterprise-Grade HRIS Analytics Dashboard
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useHRISData } from '@/hooks/useHRISData';
import { useSearchParams } from 'react-router-dom';

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

type SortField = 'name' | 'department' | 'position' | 'location' | 'personality';
type SortOrder = 'asc' | 'desc';
type ViewMode = 'grid' | 'list';

export const HRISAnalyticsPerfect: React.FC = () => {
  const { employees, loading, error, getEmployeesByDepartment, departments } = useHRISData();
  const [searchParams, setSearchParams] = useSearchParams();

  // Read filters from URL
  const urlDept = searchParams.get('department');
  const urlSearch = searchParams.get('search');
  const urlView = searchParams.get('view');
  const urlStatus = searchParams.get('status');
  const urlLocation = searchParams.get('location');
  const urlAssessment = searchParams.get('assessment');

  // State with URL sync
  const [selectedDepartment, setSelectedDepartment] = useState<string>(urlDept || 'All');
  const [searchTerm, setSearchTerm] = useState<string>(urlSearch || '');
  const [viewMode, setViewMode] = useState<ViewMode>((urlView as ViewMode) || 'grid');
  const [statusFilter, setStatusFilter] = useState<string>(urlStatus || 'All');
  const [locationFilter, setLocationFilter] = useState<string>(urlLocation || 'All');
  const [assessmentFilter, setAssessmentFilter] = useState<string>(urlAssessment || 'All');
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [compareList, setCompareList] = useState<string[]>([]);
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [printMode, setPrintMode] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  // Mock assessment data
  const assessmentData: Record<string, AssessmentData> = {
    'EMP001': { employee_id: 'EMP001', personality_type: 'INTJ-A', big_five: { openness: 85, conscientiousness: 90, extraversion: 45, agreeableness: 55, neuroticism: 30 }, completed_date: '2024-01-15' },
    'EMP002': { employee_id: 'EMP002', personality_type: 'INTJ-T', big_five: { openness: 92, conscientiousness: 88, extraversion: 35, agreeableness: 48, neuroticism: 42 }, completed_date: '2024-01-10' },
    'EMP003': { employee_id: 'EMP003', personality_type: 'ENFJ-A', big_five: { openness: 78, conscientiousness: 82, extraversion: 88, agreeableness: 90, neuroticism: 35 }, completed_date: '2024-01-12' },
    'EMP004': { employee_id: 'EMP004', personality_type: 'ISFJ-A', big_five: { openness: 65, conscientiousness: 85, extraversion: 55, agreeableness: 92, neuroticism: 38 }, completed_date: '2024-01-08' },
    'EMP005': { employee_id: 'EMP005', personality_type: 'ISTJ-A', big_five: { openness: 58, conscientiousness: 95, extraversion: 42, agreeableness: 78, neuroticism: 28 }, completed_date: '2024-01-14' }
  };

  // Sync state to URL
  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedDepartment !== 'All') params.set('department', selectedDepartment);
    if (searchTerm) params.set('search', searchTerm);
    if (viewMode !== 'grid') params.set('view', viewMode);
    if (statusFilter !== 'All') params.set('status', statusFilter);
    if (locationFilter !== 'All') params.set('location', locationFilter);
    if (assessmentFilter !== 'All') params.set('assessment', assessmentFilter);
    setSearchParams(params);
  }, [selectedDepartment, searchTerm, viewMode, statusFilter, locationFilter, assessmentFilter, setSearchParams]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Cmd/Ctrl + F: Focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        e.preventDefault();
        document.querySelector('input[type="text"]')?.focus();
      }
      // ESC: Clear filters or close modal
      if (e.key === 'Escape') {
        if (selectedEmployee) {
          setSelectedEmployee(null);
        } else if (searchTerm || selectedDepartment !== 'All' || statusFilter !== 'All') {
          setSearchTerm('');
          setSelectedDepartment('All');
          setStatusFilter('All');
          setLocationFilter('All');
          setAssessmentFilter('All');
        }
      }
      // Cmd/Ctrl + P: Print
      if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
        e.preventDefault();
        window.print();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedEmployee, searchTerm, selectedDepartment, statusFilter]);

  // Advanced filtering
  const filteredEmployees = useMemo(() => {
    let filtered = employees;

    // Department filter
    if (selectedDepartment !== 'All') {
      filtered = filtered.filter(emp => emp.department === selectedDepartment);
    }

    // Search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(emp =>
        emp.name.toLowerCase().includes(search) ||
        emp.position.toLowerCase().includes(search) ||
        emp.department.toLowerCase().includes(search) ||
        emp.id.toLowerCase().includes(search)
      );
    }

    // Status filter
    if (statusFilter !== 'All') {
      filtered = filtered.filter(emp => emp.status === statusFilter);
    }

    // Location filter
    if (locationFilter !== 'All') {
      filtered = filtered.filter(emp => emp.location === locationFilter);
    }

    // Assessment completion filter
    if (assessmentFilter === 'Completed') {
      filtered = filtered.filter(emp => assessmentData[emp.id]);
    } else if (assessmentFilter === 'Not Completed') {
      filtered = filtered.filter(emp => !assessmentData[emp.id]);
    }

    // Sorting
    filtered = [...filtered].sort((a, b) => {
      let comparison = 0;

      if (sortField === 'personality') {
        const aType = assessmentData[a.id]?.personality_type || 'ZZZ';
        const bType = assessmentData[b.id]?.personality_type || 'ZZZ';
        comparison = aType.localeCompare(bType);
      } else {
        const aValue = a[sortField];
        const bValue = b[sortField];
        comparison = String(aValue).localeCompare(String(bValue));
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [employees, selectedDepartment, searchTerm, statusFilter, locationFilter, assessmentFilter, sortField, sortOrder, assessmentData]);

  // Statistics calculation
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
    const completedAssessments = employees.filter(e => assessmentData[e.id]).length;
    const completionRate = (completedAssessments / employees.length) * 100;

    // Personality type distribution
    const personalityCounts = Object.values(assessmentData).reduce((acc, a) => {
      if (a.personality_type) {
        acc[a.personality_type] = (acc[a.personality_type] || 0) + 1;
      }
      return acc;
    }, {} as Record<string, number>);

    return {
      totalEmployees: employees.length,
      totalDepartments: departments.length,
      totalPositions: Object.keys(positionCounts).length,
      totalLocations: Object.keys(locationCounts).length,
      activePercentage: (activeCount / employees.length) * 100,
      assessmentCompletion: completionRate,
      departmentCounts,
      positionCounts,
      locationCounts,
      personalityCounts
    };
  }, [employees, departments, getEmployeesByDepartment, assessmentData]);

  // Export functions
  const exportToCSV = useCallback(() => {
    const headers = ['Employee ID', 'Name', 'Position', 'Department', 'Location', 'Status', 'Personality Type', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Assessment Date'];
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
        assessment?.big_five?.openness || '',
        assessment?.big_five?.conscientiousness || '',
        assessment?.big_five?.extraversion || '',
        assessment?.big_five?.agreeableness || '',
        assessment?.big_five?.neuroticism || '',
        assessment?.completed_date || ''
      ];
    });

    const csv = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hris-analytics-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  }, [filteredEmployees, assessmentData]);

  const exportToPDF = useCallback(() => {
    setPrintMode(true);
    setTimeout(() => {
      window.print();
      setPrintMode(false);
    }, 100);
  }, []);

  const toggleCompare = useCallback((empId: string) => {
    if (compareList.includes(empId)) {
      setCompareList(compareList.filter(id => id !== empId));
    } else if (compareList.length < 3) {
      setCompareList([...compareList, empId]);
    }
  }, [compareList]);

  const clearAllFilters = useCallback(() => {
    setSearchTerm('');
    setSelectedDepartment('All');
    setStatusFilter('All');
    setLocationFilter('All');
    setAssessmentFilter('All');
  }, []);

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
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6">
            <div className="text-red-800">
              <p className="font-semibold text-lg">Error loading HRIS data</p>
              <p className="text-sm mt-2">{error}</p>
              <Button className="mt-4" onClick={() => window.location.reload()}>
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`p-6 max-w-7xl mx-auto ${darkMode ? 'dark' : ''}`}>
      {/* Print Styles */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white; }
          .print-break { page-break-inside: avoid; }
        }
      `}</style>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              📊 HRIS Analytics Dashboard
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-1">
              Comprehensive workforce analytics powered by HRIS + PsychSync integration
            </p>
          </div>
          <div className="flex gap-2 no-print">
            <Button
              variant={comparisonMode ? 'primary' : 'outline'}
              size="sm"
              onClick={() => {
                setComparisonMode(!comparisonMode);
                setCompareList([]);
              }}
              title="Compare up to 3 employees (C)"
            >
              🔄 Compare ({compareList.length}/3)
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportToCSV}
              title="Export to CSV (E)"
            >
              📥 CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={exportToPDF}
              title="Print or export to PDF (P)"
            >
              🖨️ PDF
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              ⊞ Grid
            </Button>
            <Button
              variant={viewMode === 'list' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              ☰ List
            </Button>
          </div>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          💡 Keyboard shortcuts: Ctrl+F (search) • Ctrl+P (print) • ESC (clear filters)
        </div>
      </div>

      {/* Advanced Filters */}
      <Card className="mb-6 no-print">
        <CardContent className="p-4">
          <div className="space-y-4">
            {/* Search */}
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="🔍 Search by name, position, department, or ID... (Ctrl+F)"
                  className="w-full border rounded-lg px-4 py-2 pr-20 dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                {searchTerm && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                    onClick={() => setSearchTerm('')}
                  >
                    ✕
                  </Button>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFilters}
                disabled={!searchTerm && selectedDepartment === 'All' && statusFilter === 'All' && locationFilter === 'All' && assessmentFilter === 'All'}
              >
                Clear All
              </Button>
            </div>

            {/* Filter Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Department Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Department</label>
                <select
                  className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  value={selectedDepartment}
                  onChange={(e) => setSelectedDepartment(e.target.value)}
                >
                  <option value="All">All Departments</option>
                  {departments.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
                <select
                  className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="All">All Statuses</option>
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>

              {/* Location Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Location</label>
                <select
                  className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                >
                  <option value="All">All Locations</option>
                  <option value="Headquarters">Headquarters</option>
                  <option value="Branch Office">Branch Office</option>
                </select>
              </div>

              {/* Assessment Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Assessment</label>
                <select
                  className="w-full border rounded-lg px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
                  value={assessmentFilter}
                  onChange={(e) => setAssessmentFilter(e.target.value)}
                >
                  <option value="All">All Employees</option>
                  <option value="Completed">Completed</option>
                  <option value="Not Completed">Not Completed</option>
                </select>
              </div>
            </div>

            {/* Results count */}
            <div className="flex items-center justify-between text-sm">
              <div className="text-gray-600 dark:text-gray-400">
                Showing <span className="font-semibold text-gray-900 dark:text-white">{filteredEmployees.length}</span> of{' '}
                <span className="font-semibold text-gray-900 dark:text-white">{employees.length}</span> employees
                {(selectedDepartment !== 'All' || statusFilter !== 'All' || locationFilter !== 'All' || assessmentFilter !== 'All' || searchTerm) && (
                  <span className="text-indigo-600"> (filtered)</span>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSortField(sortField === 'name' ? 'department' : 'name');
                  setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                }}
              >
                Sort by {sortField === 'name' ? 'Department' : 'Name'} ({sortOrder === 'asc' ? '↓' : '↑'})
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8 print-break">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900 dark:to-blue-800 print-break">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-blue-700 dark:text-blue-200">{stats.totalEmployees}</div>
                <div className="text-sm text-blue-600 dark:text-blue-300">Employees</div>
              </div>
              <span className="text-4xl">👥</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900 dark:to-green-800 print-break">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-700 dark:text-green-200">{stats.totalDepartments}</div>
                <div className="text-sm text-green-600 dark:text-green-300">Departments</div>
              </div>
              <span className="text-4xl">🏢</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900 dark:to-purple-800 print-break">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-purple-700 dark:text-purple-200">{stats.totalPositions}</div>
                <div className="text-sm text-purple-600 dark:text-purple-300">Positions</div>
              </div>
              <span className="text-4xl">💼</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900 dark:to-orange-800 print-break">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-orange-700 dark:text-orange-200">{stats.totalLocations}</div>
                <div className="text-sm text-orange-600 dark:text-orange-300">Locations</div>
              </div>
              <span className="text-4xl">📍</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900 dark:to-emerald-800 print-break">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-emerald-700 dark:text-emerald-200">{stats.activePercentage.toFixed(0)}%</div>
                <div className="text-sm text-emerald-600 dark:text-emerald-300">Active Rate</div>
              </div>
              <span className="text-4xl">✅</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-pink-50 to-pink-100 dark:from-pink-900 dark:to-pink-800 print-break">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-pink-700 dark:text-pink-200">{stats.assessmentCompletion.toFixed(0)}%</div>
                <div className="text-sm text-pink-600 dark:text-pink-300">Assessments</div>
              </div>
              <span className="text-4xl">🧠</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Employee Comparison */}
      {comparisonMode && compareList.length > 0 && (
        <Card className="mb-8 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900 dark:to-orange-900 print-break no-print">
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
                  <Card key={empId} className="bg-white dark:bg-gray-800">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                            {emp.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <div className="font-semibold dark:text-white">{emp.name}</div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">{emp.position}</div>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleCompare(emp.id)}
                        >
                          ✕
                        </Button>
                      </div>

                      {assessment && (
                        <div className="space-y-3">
                          <div>
                            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Personality Type</div>
                            <div className="font-semibold text-indigo-600 dark:text-indigo-400">{assessment.personality_type}</div>
                          </div>

                          {assessment.big_five && (
                            <div>
                              <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">Big Five Traits</div>
                              <div className="space-y-2">
                                {Object.entries(assessment.big_five).map(([trait, value]) => (
                                  <div key={trait}>
                                    <div className="flex justify-between text-xs mb-1 dark:text-gray-300">
                                      <span className="capitalize">{trait}</span>
                                      <span>{value}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
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
                        <div className="text-sm text-gray-500 dark:text-gray-400 italic">
                          No assessment data available
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {compareList.length < 3 && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-4 text-center">
                Click on employees below to add them to comparison (max 3)
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Employee Directory */}
      <Card className="mb-8 print-break">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>👥 Employee Directory</span>
            <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
              {filteredEmployees.length} {filteredEmployees.length === 1 ? 'employee' : 'employees'}
              {searchTerm && ` matching "${searchTerm}"`}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {filteredEmployees.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No employees found</p>
              <p className="text-gray-600 dark:text-gray-400 mb-4">Try adjusting your filters or search</p>
              <Button onClick={clearAllFilters}>Clear All Filters</Button>
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
                          <div className="font-semibold text-gray-900 dark:text-white truncate">{emp.name}</div>
                          <div className="text-sm text-gray-600 dark:text-gray-400 truncate">{emp.position}</div>
                        </div>
                        {comparisonMode && (
                          <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                            isSelected ? 'bg-orange-500 border-orange-500' : 'border-gray-300 dark:border-gray-600'
                          }`}>
                            {isSelected && <span className="text-white text-xs">✓</span>}
                          </div>
                        )}
                      </div>

                      <div className="space-y-1 text-sm mb-3">
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <span className="mr-2">🏢</span>
                          <span className="truncate">{emp.department}</span>
                        </div>
                        <div className="flex items-center text-gray-600 dark:text-gray-400">
                          <span className="mr-2">📍</span>
                          <span className="truncate">{emp.location}</span>
                        </div>
                        <div className="flex items-center">
                          <span className="mr-2">🆔</span>
                          <span className="text-gray-500 dark:text-gray-500">{emp.id}</span>
                          <span className="ml-auto">
                            <span className={`text-xs px-2 py-1 rounded ${
                              emp.status === 'Active'
                                ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                            }`}>
                              {emp.status}
                            </span>
                          </span>
                        </div>
                      </div>

                      {assessment && (
                        <div className="pt-3 border-t dark:border-gray-700">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-gray-600 dark:text-gray-400">🧠 Assessment</span>
                            <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">{assessment.personality_type}</span>
                          </div>
                          <div className="grid grid-cols-5 gap-1">
                            {assessment.big_five && Object.entries(assessment.big_five).slice(0, 5).map(([_, value]) => (
                              <div key={_} className="h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
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
                        <div className="pt-3 border-t dark:border-gray-700">
                          <div className="text-xs text-gray-500 dark:text-gray-500 italic">
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
                  <tr className="border-b dark:border-gray-700">
                    <th
                      className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                      onClick={() => {
                        if (sortField === 'name') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortField('name');
                          setSortOrder('asc');
                        }
                      }}
                    >
                      Employee {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th
                      className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                      onClick={() => {
                        if (sortField === 'department') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortField('department');
                          setSortOrder('asc');
                        }
                      }}
                    >
                      Department {sortField === 'department' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Position</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Location</th>
                    <th
                      className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                      onClick={() => {
                        if (sortField === 'personality') {
                          setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortField('personality');
                          setSortOrder('asc');
                        }
                      }}
                    >
                      Personality {sortField === 'personality' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map((emp, index) => {
                    const assessment = assessmentData[emp.id];
                    return (
                      <tr
                        key={emp.id}
                        className={`border-b dark:border-gray-700 ${index % 2 === 0 ? 'bg-gray-50 dark:bg-gray-800' : 'bg-white dark:bg-gray-900'} hover:bg-indigo-50 dark:hover:bg-gray-700 cursor-pointer`}
                        onClick={() => setSelectedEmployee(emp)}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                              {emp.name.split(' ').map((n: string) => n[0]).join('')}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900 dark:text-white">{emp.name}</div>
                              <div className="text-xs text-gray-500 dark:text-gray-500">{emp.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{emp.department}</td>
                        <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{emp.position}</td>
                        <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{emp.location}</td>
                        <td className="py-3 px-4">
                          {assessment ? (
                            <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
                              {assessment.personality_type}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400 dark:text-gray-500 italic">Not completed</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className={`text-xs px-2 py-1 rounded ${
                            emp.status === 'Active'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                              : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedEmployee(null)}>
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
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
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedEmployee.name}</h3>
                    <p className="text-gray-600 dark:text-gray-400">{selectedEmployee.position}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded dark:bg-indigo-900 dark:text-indigo-300">
                        {selectedEmployee.department}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded dark:bg-gray-700 dark:text-gray-300">
                        {selectedEmployee.location}
                      </span>
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded dark:bg-green-900 dark:text-green-300">
                        {selectedEmployee.status}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Assessment Data */}
                {assessmentData[selectedEmployee.id] && (
                  <div className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900 dark:to-blue-900 rounded-lg p-6">
                    <h4 className="text-lg font-semibold mb-4 dark:text-white">🧠 PsychSync Assessment Results</h4>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Personality Type</div>
                        <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                          {assessmentData[selectedEmployee.id].personality_type}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Completed</div>
                        <div className="text-xl font-bold text-gray-900 dark:text-white">
                          {assessmentData[selectedEmployee.id].completed_date}
                        </div>
                      </div>
                    </div>

                    {assessmentData[selectedEmployee.id].big_five && (
                      <div>
                        <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Big Five Personality Traits</div>
                        <div className="space-y-3">
                          {Object.entries(assessmentData[selectedEmployee.id].big_five!).map(([trait, value]) => (
                            <div key={trait}>
                              <div className="flex justify-between text-sm mb-1 dark:text-gray-300">
                                <span className="capitalize font-medium">{trait}</span>
                                <span className="text-gray-600 dark:text-gray-400">{value}/100</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
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
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
                    <div className="text-4xl mb-2">📋</div>
                    <p className="text-gray-600 dark:text-gray-400">No assessment completed yet</p>
                    <Button className="mt-4" size="sm">
                      Send Assessment Reminder
                    </Button>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 no-print">
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

      {/* Footer */}
      <Card className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900 dark:to-blue-900 no-print">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
              <div className="font-semibold text-gray-900 dark:text-white mb-2">🔗 Integration</div>
              <p className="text-gray-600 dark:text-gray-400">HRIS + PsychSync assessment data fully integrated</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
              <div className="font-semibold text-gray-900 dark:text-white mb-2">🔍 Search</div>
              <p className="text-gray-600 dark:text-gray-400">Ctrl+F to search, ESC to clear</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
              <div className="font-semibold text-gray-900 dark:text-white mb-2">⌨️ Shortcuts</div>
              <p className="text-gray-600 dark:text-gray-400">Ctrl+P to print/export PDF</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
              <div className="font-semibold text-gray-900 dark:text-white mb-2">🔗 Share</div>
              <p className="text-gray-600 dark:text-gray-400">URL updates with filters for easy sharing</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HRISAnalyticsPerfect;
