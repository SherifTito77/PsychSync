import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Users,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Download,
  Filter,
  Calendar,
  RefreshCw
} from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
interface AnalyticsDashboardProps {
  className?: string;
}
interface AnalyticsData {
  overview: {
    totalComplianceScore: number;
    previousScore: number;
    trend: 'up' | 'down' | 'stable';
    totalEmployees: number;
    completedTraining: number;
    pendingFeedback: number;
    criticalIssues: number;
  };
  complianceTrends: Array<{
    date: string;
    score: number;
    category: string;
  }>;
  trainingAnalytics: {
    completionRate: number;
    averageTime: number;
    byType: Record<string, {
      total: number;
      completed: number;
      completionRate: number;
    }>;
    overdue: number;
  };
  feedbackAnalytics: {
    total: number;
    byType: Record<string, number>;
    bySeverity: Record<string, number>;
    resolved: number;
    avgResolutionTime: number;
  };
  riskAssessment: Array<{
    category: string;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    score: number;
    recommendations: string[];
  }>;
}
export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ className = '' }) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('30d');
  const [refreshing, setRefreshing] = useState(false);
  const { showNotification } = useNotification();
  useEffect(() => {
    loadAnalytics();
  }, [dateRange]);
  const loadAnalytics = async () => {
    try {
      setLoading(true);
      // This would be a real API call
      const data = await mockAnalyticsData();
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      showNotification('Failed to load analytics data', 'error');
    } finally {
      setLoading(false);
    }
  };
  const refreshData = async () => {
    setRefreshing(true);
    await loadAnalytics();
    setRefreshing(false);
  };
  const exportReport = async () => {
    try {
      const response = await fetch('/api/v1/reports/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ dateRange })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Analytics report exported successfully', 'success');
      }
    } catch (error) {
      showNotification('Failed to export report', 'error');
    }
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  if (!analytics) {
    return (
      <Card>
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Unable to load analytics data</p>
          <Button onClick={loadAnalytics} className="mt-4">Try Again</Button>
        </div>
      </Card>
    );
  }
  const scoreImprovement = analytics.overview.totalComplianceScore - analytics.overview.previousScore;
  const improvementPercentage = analytics.overview.previousScore > 0
    ? ((scoreImprovement / analytics.overview.previousScore) * 100).toFixed(1)
    : '0';
  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Compliance metrics and performance insights</p>
        </div>
        <div className="flex gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <Button
            variant="outline"
            onClick={refreshData}
            disabled={refreshing}
            icon={refreshing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>
          <Button
            onClick={exportReport}
            icon={<Download className="w-4 h-4" />}
          >
            Export Report
          </Button>
        </div>
      </div>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <MetricCard
          value={analytics.overview.totalComplianceScore}
          unit="%"
          trend={analytics.overview.trend}
          change={parseFloat(improvementPercentage)}
          icon={<BarChart3 className="w-6 h-6" />}
          color="blue"
        />
        <MetricCard
          value={analytics.overview.totalEmployees}
          icon={<Users className="w-6 h-6" />}
          color="green"
        />
        <MetricCard
          value={analytics.overview.completedTraining}
          icon={<FileText className="w-6 h-6" />}
          color="purple"
        />
        <MetricCard
          value={analytics.overview.pendingFeedback}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="orange"
        />
        <MetricCard
          value={analytics.overview.criticalIssues}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
        />
      </div>
      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Trends Chart */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Compliance Trends</h3>
          <div className="h-64">
            <TrendChart data={analytics.complianceTrends} />
          </div>
        </Card>
        {/* Training Distribution */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Training by Type</h3>
          <div className="h-64">
            <PieChartComponent data={analytics.trainingAnalytics.byType} />
          </div>
        </Card>
      </div>
      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Training Analytics */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Training Analytics</h3>
            <Badge color={analytics.trainingAnalytics.completionRate >= 80 ? 'green' : 'yellow'}>
              {analytics.trainingAnalytics.completionRate.toFixed(1)}%
            </Badge>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Completion Rate</span>
              <span className="font-semibold">{analytics.trainingAnalytics.completionRate.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Avg. Completion Time</span>
              <span className="font-semibold">{analytics.trainingAnalytics.averageTime.toFixed(0)} min</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Overdue Assignments</span>
              <span className={`font-semibold ${analytics.trainingAnalytics.overdue > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {analytics.trainingAnalytics.overdue}
              </span>
            </div>
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">By Training Type</h4>
              <div className="space-y-2">
                {Object.entries(analytics.trainingAnalytics.byType).map(([type, data]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{type.replace('_', ' ')}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            data.completionRate >= 80 ? 'bg-green-500' :
                            data.completionRate >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${data.completionRate}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">{data.completionRate.toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
        {/* Feedback Analytics */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Feedback Analytics</h3>
            <Activity className="w-5 h-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Total Feedback</span>
              <span className="font-semibold">{analytics.feedbackAnalytics.total}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Resolved</span>
              <span className="font-semibold text-green-600">{analytics.feedbackAnalytics.resolved}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Avg. Resolution Time</span>
              <span className="font-semibold">{analytics.feedbackAnalytics.avgResolutionTime.toFixed(1)} days</span>
            </div>
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">By Type</h4>
              <div className="space-y-2">
                {Object.entries(analytics.feedbackAnalytics.byType).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{type.replace('_', ' ')}</span>
                    <span className="text-sm font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">By Severity</h4>
              <div className="space-y-2">
                {Object.entries(analytics.feedbackAnalytics.bySeverity).map(([severity, count]) => (
                  <div key={severity} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{severity}</span>
                    <Badge
                      color={severity === 'critical' ? 'red' : severity === 'high' ? 'orange' : 'yellow'}
                      size="sm"
                    >
                      {count}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
        {/* Risk Assessment */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Risk Assessment</h3>
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
          </div>
          <div className="space-y-4">
            {analytics.riskAssessment.map((risk, index) => (
              <div key={index} className="border-l-4 pl-4 py-2" style={{
                borderLeftColor: risk.riskLevel === 'critical' ? '#ef4444' :
                                 risk.riskLevel === 'high' ? '#f97316' :
                                 risk.riskLevel === 'medium' ? '#eab308' : '#22c55e'
              }}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{risk.category}</h4>
                  <Badge
                    color={risk.riskLevel === 'critical' ? 'red' : risk.riskLevel === 'high' ? 'orange' : risk.riskLevel === 'medium' ? 'yellow' : 'green'}
                    size="sm"
                  >
                    {risk.riskLevel}
                  </Badge>
                </div>
                <div className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Risk Score</span>
                    <span className="font-medium">{risk.score}/100</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        risk.score >= 80 ? 'bg-red-500' :
                        risk.score >= 60 ? 'bg-orange-500' :
                        risk.score >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${risk.score}%` }}
                    />
                  </div>
                </div>
                {risk.recommendations.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-900 mb-1">Recommendations:</p>
                    <ul className="text-xs text-gray-600 space-y-1">
                      {risk.recommendations.slice(0, 2).map((rec, idx) => (
                        <li key={idx} className="flex items-start">
                          <span className="mr-1">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
// Helper Components
interface MetricCardProps {
  title: string;
  value: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  change?: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'orange';
}
const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  change,
  icon,
  color
}) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600',
      green: 'bg-green-100 text-green-600',
      yellow: 'bg-yellow-100 text-yellow-600',
      red: 'bg-red-100 text-red-600',
      purple: 'bg-purple-100 text-purple-600',
      orange: 'bg-orange-100 text-orange-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline mt-1">
            <p className="text-2xl font-bold text-gray-900">
              {value.toLocaleString()}
              {unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
            </p>
          </div>
          {trend && change !== undefined && (
            <div className="flex items-center mt-2 text-sm">
              {trend === 'up' ? (
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              ) : trend === 'down' ? (
                <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
              ) : (
                <div className="w-4 h-4 bg-gray-300 rounded-full mr-1" />
              )}
              <span className={trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'}>
                {trend !== 'stable' && `${Math.abs(change)}%`}
                {trend !== 'stable' && (trend === 'up' ? ' increase' : ' decrease')}
                {trend === 'stable' && 'No change'}
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${getColorClasses(color)}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};
// Mock Chart Components (in real implementation, use a charting library like Chart.js or Recharts)
const TrendChart: React.FC<{ data: any[] }> = ({ data }) => {
  return (
    <div className="h-full flex items-center justify-center text-gray-500">
      <div className="text-center">
        <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Trend Chart</p>
        <p className="text-xs opacity-75">Chart data: {data.length} points</p>
      </div>
    </div>
  );
};
const PieChartComponent: React.FC<{ data: Record<string, any> }> = ({ data }) => {
  return (
    <div className="h-full flex items-center justify-center text-gray-500">
      <div className="text-center">
        <PieChartIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Distribution Chart</p>
        <p className="text-xs opacity-75">Categories: {Object.keys(data).length}</p>
      </div>
    </div>
  );
};
// Mock analytics data generator
const mockAnalyticsData = async (): Promise<AnalyticsData> => {
  return {
    overview: {
      totalComplianceScore: 87,
      previousScore: 83,
      trend: 'up',
      totalEmployees: 1247,
      completedTraining: 1103,
      pendingFeedback: 23,
      criticalIssues: 2
    },
    complianceTrends: [],
    trainingAnalytics: {
      completionRate: 88.5,
      averageTime: 45,
      byType: {
        harassment_prevention: { total: 1247, completed: 1103, completionRate: 88.5 },
        data_privacy: { total: 1247, completed: 1180, completionRate: 94.6 },
        workplace_safety: { total: 1247, completed: 1090, completionRate: 87.4 }
      },
      overdue: 47
    },
    feedbackAnalytics: {
      total: 156,
      byType: {
        harassment: 45,
        discrimination: 23,
        safety: 67,
        toxic_culture: 21
      },
      bySeverity: {
        low: 67,
        medium: 54,
        high: 28,
        critical: 7
      },
      resolved: 142,
      avgResolutionTime: 3.2
    },
    riskAssessment: [
      {
        category: 'Data Privacy',
        riskLevel: 'medium',
        score: 65,
        recommendations: [
          'Update privacy policy',
          'Complete GDPR training for all staff'
        ]
      },
      {
        category: 'Workplace Safety',
        riskLevel: 'low',
        score: 92,
        recommendations: [
          'Schedule quarterly safety drills'
        ]
      },
      {
        category: 'Training Compliance',
        riskLevel: 'high',
        score: 78,
        recommendations: [
          'Send overdue training reminders',
          'Schedule mandatory make-up sessions'
        ]
      }
    ]
  };
};