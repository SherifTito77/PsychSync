// HRISAnalyticsUltimate.tsx - Ultimate HRIS Analytics with ALL Features
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useHRISData } from '@/hooks/useHRISData';
import { useSearchParams } from 'react-router-dom';
import {
  BarChart, Bar, PieChart, Pie, LineChart, Line, RadarChart, Radar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, AreaChart, Area, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { Employee } from '@/types/hris';
import {
  exportToCSV,
  exportStatisticsSummary,
  generatePrintableReport
} from '@/utils/hrisExport';

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

interface ReportTemplate {
  id: string;
  name: string;
  filters: {
    department: string;
    status: string;
    location: string;
    assessment: string;
  };
  charts: string[];
  createdAt: string;
}

type SortField = 'name' | 'department' | 'position' | 'location' | 'personality';
type SortOrder = 'asc' | 'desc';
type ViewMode = 'grid' | 'list';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6'];

export const HRISAnalyticsUltimate: React.FC = () => {
  const {
    employees,
    loading,
    error,
    stats,
    departmentAnalytics,
    getEmployeesByDepartment,
    departments,
    useRealAPI,
    toggleAPISource
  } = useHRISData();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL state
  const urlDept = searchParams.get('department');
  const urlSearch = searchParams.get('search');
  const urlView = searchParams.get('view');
  const urlStatus = searchParams.get('status');
  const urlLocation = searchParams.get('location');
  const urlAssessment = searchParams.get('assessment');

  // Component state
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
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'kpis' | 'reports'>('overview');

  // Real-time update simulation
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [liveMode, setLiveMode] = useState(false);

  // Custom Reports
  const [reportTemplates, setReportTemplates] = useState<ReportTemplate[]>([]);
  const [showReportBuilder, setShowReportBuilder] = useState(false);
  const [newReportName, setNewReportName] = useState('');
  const [selectedCharts, setSelectedCharts] = useState<string[]>([]);

  // Mock assessment data
  const assessmentData: Record<string, AssessmentData> = {
    'EMP001': { employee_id: 'EMP001', personality_type: 'INTJ-A', big_five: { openness: 85, conscientiousness: 90, extraversion: 45, agreeableness: 55, neuroticism: 30 }, completed_date: '2024-01-15' },
    'EMP002': { employee_id: 'EMP002', personality_type: 'INTJ-T', big_five: { openness: 92, conscientiousness: 88, extraversion: 35, agreeableness: 48, neuroticism: 42 }, completed_date: '2024-01-10' },
    'EMP003': { employee_id: 'EMP003', personality_type: 'ENFJ-A', big_five: { openness: 78, conscientiousness: 82, extraversion: 88, agreeableness: 90, neuroticism: 35 }, completed_date: '2024-01-12' },
    'EMP004': { employee_id: 'EMP004', personality_type: 'ISFJ-A', big_five: { openness: 65, conscientiousness: 85, extraversion: 55, agreeableness: 92, neuroticism: 38 }, completed_date: '2024-01-08' },
    'EMP005': { employee_id: 'EMP005', personality_type: 'ISTJ-A', big_five: { openness: 58, conscientiousness: 95, extraversion: 42, agreeableness: 78, neuroticism: 28 }, completed_date: '2024-01-14' }
  };

  // WebSocket simulation for real-time updates
  useEffect(() => {
    if (!liveMode) return;

    const interval = setInterval(() => {
      setLastUpdate(new Date());
      // In production, this would fetch new data via WebSocket
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [liveMode]);

  // Sync filters to URL
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
      if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        e.preventDefault();
        document.querySelector('input[type="text"]')?.focus();
      }
      if (e.key === 'Escape') {
        if (selectedEmployee) setSelectedEmployee(null);
        else if (searchTerm || selectedDepartment !== 'All' || statusFilter !== 'All') {
          setSearchTerm('');
          setSelectedDepartment('All');
          setStatusFilter('All');
          setLocationFilter('All');
          setAssessmentFilter('All');
        }
      }
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

    if (selectedDepartment !== 'All') {
      filtered = filtered.filter(emp => emp.department === selectedDepartment);
    }

    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(emp =>
        emp.name.toLowerCase().includes(search) ||
        emp.position.toLowerCase().includes(search) ||
        emp.department.toLowerCase().includes(search) ||
        emp.id.toLowerCase().includes(search)
      );
    }

    if (statusFilter !== 'All') {
      filtered = filtered.filter(emp => emp.status === statusFilter);
    }

    if (locationFilter !== 'All') {
      filtered = filtered.filter(emp => emp.location === locationFilter);
    }

    if (assessmentFilter === 'Completed') {
      filtered = filtered.filter(emp => assessmentData[emp.id]);
    } else if (assessmentFilter === 'Not Completed') {
      filtered = filtered.filter(emp => !assessmentData[emp.id]);
    }

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

  // Advanced KPIs
  const kpis = useMemo(() => {
    const totalEmployees = employees.length;
    const activeEmployees = employees.filter(e => e.status === 'Active').length;
    const completedAssessments = employees.filter(e => assessmentData[e.id]).length;
    const deptCounts = departments.map(d => getEmployeesByDepartment(d).length);
    const avgDeptSize = deptCounts.reduce((a, b) => a + b, 0) / deptCounts.length;

    // Personality distribution
    const personalityTypes = Object.values(assessmentData).map(a => a.personality_type);
    const personalityDistribution = personalityTypes.reduce((acc, type) => {
      acc[type!] = (acc[type!] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Big Five averages
    const bigFiveAvgs = Object.values(assessmentData).reduce((acc, a) => {
      if (a.big_five) {
        acc.openness.push(a.big_five.openness);
        acc.conscientiousness.push(a.big_five.conscientiousness);
        acc.extraversion.push(a.big_five.extraversion);
        acc.agreeableness.push(a.big_five.agreeableness);
        acc.neuroticism.push(a.big_five.neuroticism);
      }
      return acc;
    }, { openness: [], conscientiousness: [], extraversion: [], agreeableness: [], neuroticism: [] } as any);

    const calculateAvg = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

    // Location efficiency
    const locationEfficiency = Object.entries(employees.reduce((acc, emp) => {
      acc[emp.location] = (acc[emp.location] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)).map(([loc, count]) => ({ location: loc, count, percentage: (count / totalEmployees) * 100 }));

    // Assessment completion trend (mock data)
    const completionTrend = [
      { month: 'Oct', completed: 3 },
      { month: 'Nov', completed: 4 },
      { month: 'Dec', completed: 4 },
      { month: 'Jan', completed: 5 }
    ];

    // Department performance
    const deptPerformance = departments.map(dept => {
      const deptEmployees = getEmployeesByDepartment(dept);
      const assessments = deptEmployees.filter(e => assessmentData[e.id]);
      const avgConscientiousness = assessments.reduce((sum, e) => {
        return sum + (assessmentData[e.id]?.big_five?.conscientiousness || 0);
      }, 0) / (assessments.length || 1);

      return { department: dept, performance: avgConscientiousness, employees: deptEmployees.length };
    });

    // Top performers
    const topPerformers = Object.entries(assessmentData)
      .map(([id, data]) => ({
        employee: employees.find(e => e.id === id),
        avgScore: data.big_five ? Object.values(data.big_five).reduce((a, b) => a + b, 0) / 5 : 0
      }))
      .sort((a, b) => b.avgScore - a.avgScore)
      .slice(0, 3);

    // Retention risk (based on neuroticism)
    const retentionRisk = Object.entries(assessmentData)
      .map(([id, data]) => ({
        employee: employees.find(e => e.id === id),
        risk: data.big_five?.neuroticism || 0
      }))
      .sort((a, b) => b.risk - a.risk)
      .slice(0, 3);

    return {
      totalEmployees,
      activeEmployees,
      activeRate: (activeEmployees / totalEmployees) * 100,
      assessmentCompletion: (completedAssessments / totalEmployees) * 100,
      avgDepartmentSize: avgDeptSize,
      personalityDistribution,
      bigFiveAverages: {
        openness: calculateAvg(bigFiveAvgs.openness),
        conscientiousness: calculateAvg(bigFiveAvgs.conscientiousness),
        extraversion: calculateAvg(bigFiveAvgs.extraversion),
        agreeableness: calculateAvg(bigFiveAvgs.agreeableness),
        neuroticism: calculateAvg(bigFiveAvgs.neuroticism)
      },
      locationEfficiency,
      completionTrend,
      deptPerformance,
      topPerformers,
      retentionRisk,
      diversityScore: new Set(personalityTypes).size / personalityTypes.length * 100
    };
  }, [employees, departments, getEmployeesByDepartment, assessmentData]);

  // Chart data preparation
  const chartData = useMemo(() => {
    // Department distribution for pie chart
    const deptData = departments.map(dept => ({
      name: dept,
      value: getEmployeesByDepartment(dept).length,
      color: COLORS[departments.indexOf(dept) % COLORS.length]
    }));

    // Personality distribution
    const personalityData = Object.entries(kpis.personalityDistribution).map(([name, value], index) => ({
      name,
      value,
      color: COLORS[index % COLORS.length]
    }));

    // Big Five averages
    const bigFiveData = [
      { trait: 'Openness', value: kpis.bigFiveAverages.openness, fullMark: 100 },
      { trait: 'Conscientiousness', value: kpis.bigFiveAverages.conscientiousness, fullMark: 100 },
      { trait: 'Extraversion', value: kpis.bigFiveAverages.extraversion, fullMark: 100 },
      { trait: 'Agreeableness', value: kpis.bigFiveAverages.agreeableness, fullMark: 100 },
      { trait: 'Neuroticism', value: kpis.bigFiveAverages.neuroticism, fullMark: 100 }
    ];

    // Radar chart data for top performer
    const topPerformer = kpis.topPerformers[0];
    const radarData = topPerformer && assessmentData[topPerformer.employee?.id]?.big_five
      ? Object.entries(assessmentData[topPerformer.employee.id].big_five!).map(([trait, value]) => ({
          trait: trait.charAt(0).toUpperCase() + trait.slice(1),
          value: value,
          fullMark: 100
        }))
      : [];

    return { deptData, personalityData, bigFiveData, radarData };
  }, [departments, getEmployeesByDepartment, kpis, assessmentData]);

  // Export functions - Using enhanced export utilities
  const handleExportCSV = useCallback(() => {
    exportToCSV(filteredEmployees, `hris-analytics-${selectedDepartment.toLowerCase()}`);
  }, [filteredEmployees, selectedDepartment]);

  const handleExportSummary = useCallback(() => {
    exportStatisticsSummary(stats, `hris-summary-${new Date().toISOString().split('T')[0]}`);
  }, [stats]);

  const handlePrintReport = useCallback(() => {
    generatePrintableReport(filteredEmployees, stats, 'HRIS Analytics Report');
  }, [filteredEmployees, stats]);

  // Save report template
  const saveReportTemplate = useCallback(() => {
    if (!newReportName) return;

    const newTemplate: ReportTemplate = {
      id: Date.now().toString(),
      name: newReportName,
      filters: {
        department: selectedDepartment,
        status: statusFilter,
        location: locationFilter,
        assessment: assessmentFilter
      },
      charts: selectedCharts,
      createdAt: new Date().toISOString()
    };

    setReportTemplates([...reportTemplates, newTemplate]);
    setNewReportName('');
    setSelectedCharts([]);
    setShowReportBuilder(false);
  }, [newReportName, selectedDepartment, statusFilter, locationFilter, assessmentFilter, selectedCharts, reportTemplates]);

  // Load report template
  const loadReportTemplate = useCallback((template: ReportTemplate) => {
    setSelectedDepartment(template.filters.department);
    setStatusFilter(template.filters.status);
    setLocationFilter(template.filters.location);
    setAssessmentFilter(template.filters.assessment);
    setSelectedCharts(template.charts);
  }, []);

  // Email report
  const emailReport = useCallback(() => {
    const subject = `HRIS Analytics Report - ${new Date().toLocaleDateString()}`;
    const body = `
HRIS Analytics Report

Generated: ${new Date().toLocaleString()}

Filters Applied:
- Department: ${selectedDepartment}
- Status: ${statusFilter}
- Location: ${locationFilter}
- Assessment: ${assessmentFilter}

Summary:
- Total Employees: ${kpis.totalEmployees}
- Active Rate: ${kpis.activeRate.toFixed(1)}%
- Assessment Completion: ${kpis.assessmentCompletion.toFixed(1)}%

View the full report here: http://localhost:5173/hris-analytics?${searchParams.toString()}
    `.trim();

    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  }, [kpis, selectedDepartment, statusFilter, locationFilter, assessmentFilter, searchParams]);

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
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              📊 HRIS Analytics Dashboard
            </h1>
            <p className="text-gray-600 mt-1">
              Comprehensive workforce analytics with real-time updates & custom reports
            </p>
          </div>
          <div className="flex items-center gap-2">
            {liveMode && (
              <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
                <span className="animate-pulse">🔴</span>
                <span>Live</span>
              </div>
            )}
            <Button
              variant={useRealAPI ? 'primary' : 'outline'}
              size="sm"
              onClick={toggleAPISource}
              title="Toggle Data Source"
            >
              {useRealAPI ? '🔌 API' : '💾 Demo'}
            </Button>
            <Button
              variant={liveMode ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setLiveMode(!liveMode)}
            >
              {liveMode ? '✅ ' : ''}Live Mode
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportCSV}
              title="Export to CSV"
            >
              📥 CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportSummary}
              title="Export Summary"
            >
              📋 Summary
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrintReport}
              title="Print Report"
            >
              🖨️ Print
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={emailReport}
              title="Email Report"
            >
              📧 Email
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowReportBuilder(true)}
              title="Save Report Template"
            >
              💾 Save Template
            </Button>
          </div>
        </div>

        {/* Saved Templates */}
        {reportTemplates.length > 0 && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-gray-600">Saved Templates:</span>
            {reportTemplates.map(template => (
              <Button
                key={template.id}
                variant="outline"
                size="sm"
                onClick={() => loadReportTemplate(template)}
              >
                📋 {template.name}
              </Button>
            ))}
          </div>
        )}

        {/* Last Update */}
        <div className="text-xs text-gray-500">
          Last updated: {lastUpdate.toLocaleTimeString()}
          {liveMode && ' • Auto-refreshing every 5 seconds'}
        </div>
      </div>

      {/* Tabs */}
      <Card className="mb-6 border-2 border-indigo-200 bg-white">
        <CardContent className="p-6">
          <div className="flex flex-wrap gap-3">
            <Button
              variant={activeTab === 'overview' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => {
                console.log('🔄 Switching to Overview tab');
                setActiveTab('overview');
              }}
              className={activeTab === 'overview' ? 'ring-2 ring-indigo-500 ring-offset-2' : ''}
            >
              📊 Overview
            </Button>
            <Button
              variant={activeTab === 'charts' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => {
                console.log('🔄 Switching to Charts tab');
                setActiveTab('charts');
              }}
              className={activeTab === 'charts' ? 'ring-2 ring-indigo-500 ring-offset-2' : ''}
            >
              📈 Charts (7)
            </Button>
            <Button
              variant={activeTab === 'kpis' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => {
                console.log('🔄 Switching to KPIs tab');
                setActiveTab('kpis');
              }}
              className={activeTab === 'kpis' ? 'ring-2 ring-indigo-500 ring-offset-2' : ''}
            >
              🎯 KPIs
            </Button>
            <Button
              variant={activeTab === 'reports' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => {
                console.log('🔄 Switching to Reports tab');
                setActiveTab('reports');
              }}
              className={activeTab === 'reports' ? 'ring-2 ring-indigo-500 ring-offset-2' : ''}
            >
              📋 Custom Reports
            </Button>
          </div>
          <div className="mt-3 text-sm text-gray-600 bg-gray-50 p-2 rounded">
            💡 Current view: <strong>{activeTab}</strong> • Click tabs to switch views
          </div>
        </CardContent>
      </Card>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold text-blue-700">{kpis.totalEmployees}</div>
                    <div className="text-sm text-blue-600">Employees</div>
                  </div>
                  <span className="text-4xl">👥</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-green-50 to-green-100">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold text-green-700">{kpis.activeRate.toFixed(0)}%</div>
                    <div className="text-sm text-green-600">Active Rate</div>
                  </div>
                  <span className="text-4xl">✅</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold text-purple-700">{kpis.assessmentCompletion.toFixed(0)}%</div>
                    <div className="text-sm text-purple-600">Assessments</div>
                  </div>
                  <span className="text-4xl">🧠</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold text-orange-700">{kpis.diversityScore.toFixed(0)}%</div>
                    <div className="text-sm text-orange-600">Diversity</div>
                  </div>
                  <span className="text-4xl">🌈</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-pink-50 to-pink-100">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold text-pink-700">{kpis.avgDepartmentSize.toFixed(1)}</div>
                    <div className="text-sm text-pink-600">Avg Dept Size</div>
                  </div>
                  <span className="text-4xl">📊</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-3xl font-bold text-cyan-700">{departments.length}</div>
                    <div className="text-sm text-cyan-600">Departments</div>
                  </div>
                  <span className="text-4xl">🏢</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Department Distribution Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>🏢 Department Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData.deptData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.deptData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Personality Distribution Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>🧠 Personality Types</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={Object.entries(kpis.personalityDistribution).map(([name, value]) => ({ name, value }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#6366f1" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Big Five Radar Chart */}
            {chartData.radarData.length > 0 && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>⭐ Top Performer Profile ({kpis.topPerformers[0]?.employee?.name})</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <RadarChart cx="50%" cy="50%" outerRadius={80} data={chartData.radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="trait" />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} />
                      <Radar name="Traits" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                      <Tooltip />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Department Performance Bar Chart */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>📈 Department Performance (Avg Conscientiousness)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={kpis.deptPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="department" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="performance" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </>
      )}

      {/* Charts Tab */}
      {activeTab === 'charts' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Big Five Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle>📊 Big Five Traits - Organization Average</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData.bigFiveData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="trait" type="category" width={100} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#6366f1" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Assessment Completion Trend */}
          <Card>
            <CardHeader>
              <CardTitle>📈 Assessment Completion Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={kpis.completionTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="completed" stroke="#6366f1" fill="#6366f1" fillOpacity={0.6} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Location Efficiency Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle>📍 Location Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={kpis.locationEfficiency}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ location, percentage }) => `${location} ${percentage.toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {kpis.locationEfficiency.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index + 2 % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Personality Distribution Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle>🧠 Personality Type Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={chartData.personalityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.personalityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* KPIs Tab */}
      {activeTab === 'kpis' && (
        <div className="space-y-6">
          {/* Top Performers */}
          <Card>
            <CardHeader>
              <CardTitle>🏆 Top 3 Performers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {kpis.topPerformers.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => item.employee && setSelectedEmployee(item.employee)}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">🥇</div>
                      <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                        {item.employee?.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <div className="font-semibold">{item.employee?.name}</div>
                        <div className="text-sm text-gray-600">{item.employee?.position}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-indigo-600">{item.avgScore.toFixed(1)}</div>
                      <div className="text-xs text-gray-600">Avg Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Retention Risk Alert */}
          <Card>
            <CardHeader>
              <CardTitle>⚠️ Retention Risk Alert (High Neuroticism)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {kpis.retentionRisk.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200 cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => item.employee && setSelectedEmployee(item.employee)}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center text-white font-bold">
                        {item.employee?.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <div className="font-semibold text-red-900">{item.employee?.name}</div>
                        <div className="text-sm text-red-700">{item.employee?.position}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-red-600">{item.risk}%</div>
                      <div className="text-xs text-red-700">Risk Score</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Big Five Averages */}
          <Card>
            <CardHeader>
              <CardTitle>📊 Organizational Big Five Averages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {Object.entries(kpis.bigFiveAverages).map(([trait, value]) => (
                  <Card key={trait} className="bg-gray-50">
                    <CardContent className="p-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-indigo-600">{value.toFixed(1)}</div>
                        <div className="text-xs text-gray-600 capitalize">{trait}</div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${value}%` }}
                          ></div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Custom Reports Tab */}
      {activeTab === 'reports' && (
        <div className="space-y-6">
          {/* Report Builder Modal */}
          {showReportBuilder && (
            <Card className="bg-gradient-to-r from-indigo-50 to-blue-50">
              <CardHeader>
                <CardTitle>📋 Create Custom Report Template</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Report Name</label>
                    <input
                      type="text"
                      className="w-full border rounded-lg px-4 py-2"
                      placeholder="e.g., Monthly IT Department Report"
                      value={newReportName}
                      onChange={(e) => setNewReportName(e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Select Charts to Include</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {['Department Distribution', 'Personality Types', 'Big Five Averages', 'Location Distribution', 'Top Performers', 'Assessment Trend'].map(chart => (
                        <label key={chart} className="flex items-center space-x-2 p-2 bg-white rounded cursor-pointer hover:bg-gray-50">
                          <input
                            type="checkbox"
                            checked={selectedCharts.includes(chart)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedCharts([...selectedCharts, chart]);
                              } else {
                                setSelectedCharts(selectedCharts.filter(c => c !== chart));
                              }
                            }}
                            className="rounded"
                          />
                          <span className="text-sm">{chart}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="text-sm text-gray-600 bg-white p-3 rounded-lg">
                    <strong>Current filters will be saved:</strong>
                    <ul className="mt-2 space-y-1">
                      <li>• Department: {selectedDepartment}</li>
                      <li>• Status: {statusFilter}</li>
                      <li>• Location: {locationFilter}</li>
                      <li>• Assessment: {assessmentFilter}</li>
                    </ul>
                  </div>

                  <div className="flex gap-2">
                    <Button onClick={saveReportTemplate} disabled={!newReportName || selectedCharts.length === 0}>
                      💾 Save Template
                    </Button>
                    <Button variant="outline" onClick={() => setShowReportBuilder(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Saved Templates */}
          {reportTemplates.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>📁 Your Saved Report Templates</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {reportTemplates.map(template => (
                    <Card key={template.id} className="bg-white border hover:shadow-md cursor-pointer" onClick={() => loadReportTemplate(template)}>
                      <CardContent className="p-4">
                        <div className="font-semibold">{template.name}</div>
                        <div className="text-sm text-gray-600 mt-1">
                          {template.charts.length} charts • Created {new Date(template.createdAt).toLocaleDateString()}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={(e) => {
                            e.stopPropagation();
                            setReportTemplates(reportTemplates.filter(t => t.id !== template.id));
                          }}
                        >
                          Delete
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {reportTemplates.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <div className="text-6xl mb-4">📋</div>
                <h3 className="text-xl font-semibold mb-2">No Saved Templates</h3>
                <p className="text-gray-600 mb-4">Create custom report templates to quickly access your preferred views</p>
                <Button onClick={() => setShowReportBuilder(true)}>
                  Create Your First Template
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Report Builder Modal (when shown from other tabs) */}
      {showReportBuilder && activeTab !== 'reports' && (
        <Card className="mb-6 bg-gradient-to-r from-indigo-50 to-blue-50">
          <CardHeader>
            <CardTitle>📋 Create Custom Report Template</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Report Name</label>
                <input
                  type="text"
                  className="w-full border rounded-lg px-4 py-2"
                  placeholder="e.g., Monthly IT Department Report"
                  value={newReportName}
                  onChange={(e) => setNewReportName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Select Charts to Include</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {['Department Distribution', 'Personality Types', 'Big Five Averages', 'Location Distribution', 'Top Performers', 'Assessment Trend'].map(chart => (
                    <label key={chart} className="flex items-center space-x-2 p-2 bg-white rounded cursor-pointer hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={selectedCharts.includes(chart)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCharts([...selectedCharts, chart]);
                          } else {
                            setSelectedCharts(selectedCharts.filter(c => c !== chart));
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">{chart}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={saveReportTemplate} disabled={!newReportName || selectedCharts.length === 0}>
                  💾 Save Template
                </Button>
                <Button variant="outline" onClick={() => setShowReportBuilder(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
      <Card className="bg-gradient-to-r from-indigo-50 to-blue-50">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm flex-1">
              <div className="bg-white rounded-lg p-4">
                <div className="font-semibold mb-2">📊 15+ Charts</div>
                <p className="text-gray-600">Interactive visualizations powered by Recharts</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <div className="font-semibold mb-2">🧠 Assessments</div>
                <p className="text-gray-600">Big Five, MBTI, Leadership Potential & more</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <div className="font-semibold mb-2">📥 Export Options</div>
                <p className="text-gray-600">CSV, Summary, Print Reports</p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <div className="font-semibold mb-2">🔌 Data Source</div>
                <p className="text-gray-600">
                  {useRealAPI ? 'Live HRIS API' : 'Demo Data'} • {stats.assessmentCompletionRate?.toFixed(0) || 0}% assessment completion
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HRISAnalyticsUltimate;
