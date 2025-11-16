import React, { useState, useEffect } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Users,
  TrendingUp,
  Activity,
  RefreshCw,
  Download,
  Calendar
} from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
import { ComplianceScore, ComplianceCheck } from '../../types/compliance';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Card } from '../common/card';
import { Badge } from '../common/Badge';
interface ComplianceDashboardProps {
  className?: string;
}
export const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({ className = '' }) => {
  const [complianceData, setComplianceData] = useState<ComplianceScore | null>(null);
  const [lastCheck, setLastCheck] = useState<ComplianceCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningCheck, setRunningCheck] = useState(false);
  const { showNotification } = useNotification();
  useEffect(() => {
    loadComplianceData();
  }, []);
  const loadComplianceData = async () => {
    try {
      setLoading(true);
      const [score, check] = await Promise.all([
        complianceService.getComplianceScore(),
        complianceService.getComplianceAnalytics().catch(() => null)
      ]);
      setComplianceData(score);
      setLastCheck(check);
    } catch (error) {
      console.error('Failed to load compliance data:', error);
      showNotification('Failed to load compliance data', 'error');
    } finally {
      setLoading(false);
    }
  };
  const runComplianceCheck = async () => {
    try {
      setRunningCheck(true);
      const result = await complianceService.runComplianceCheck('full');
      showNotification('Compliance check completed successfully', 'success');
      await loadComplianceData();
    } catch (error) {
      console.error('Failed to run compliance check:', error);
      showNotification('Failed to run compliance check', 'error');
    } finally {
      setRunningCheck(false);
    }
  };
  const downloadReport = async () => {
    try {
      const response = await fetch('/api/v1/reports/compliance/monthly', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      showNotification('Failed to download report', 'error');
    }
  };
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-yellow-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };
  const getStatusColor = (status: string) => {
    const colors = {
      excellent: 'green',
      good: 'blue',
      needs_improvement: 'yellow',
      critical: 'red'
    };
    return colors[status as keyof typeof colors] || 'gray';
  };
  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor and manage organizational compliance</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={downloadReport}
            icon={<Download className="w-4 h-4" />}
          >
            Download Report
          </Button>
          <Button
            onClick={runComplianceCheck}
            disabled={runningCheck}
            icon={runningCheck ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />}
          >
            {runningCheck ? 'Running Check...' : 'Run Compliance Check'}
          </Button>
        </div>
      </div>
      {/* Overall Score Card */}
      <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white overflow-hidden">
        <div className="relative">
          <div className="flex items-center justify-between">
            <div className="z-10">
              <p className="text-indigo-100 text-sm font-medium">Overall Compliance Score</p>
              <div className="flex items-baseline mt-2">
                <span className="text-6xl font-bold">{complianceData?.overall || 0}</span>
                <span className="text-3xl font-semibold ml-2">/ 100</span>
              </div>
              <div className="mt-4 flex items-center gap-3">
                <Badge color={getStatusColor(complianceData?.status || 'critical')} variant="solid">
                  {complianceData?.status?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
                </Badge>
                <span className="text-sm text-indigo-100">
                  Last updated: {complianceData?.last_updated ?
                    new Date(complianceData.last_updated).toLocaleDateString() :
                    'Never'
                  }
                </span>
              </div>
            </div>
            <Shield className="w-32 h-32 opacity-20" />
          </div>
        </div>
      </Card>
      {/* Category Scores Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ComplianceCategoryCard
          score={complianceData?.categories.labor_law || 0}
          icon={<Users className="w-6 h-6" />}
          link="/compliance/labor-law"
          color="blue"
        />
        <ComplianceCategoryCard
          score={complianceData?.categories.data_privacy || 0}
          icon={<Shield className="w-6 h-6" />}
          link="/compliance/privacy"
          color="green"
        />
        <ComplianceCategoryCard
          score={complianceData?.categories.workplace_safety || 0}
          icon={<AlertTriangle className="w-6 h-6" />}
          link="/compliance/safety"
          color="yellow"
        />
        <ComplianceCategoryCard
          score={complianceData?.categories.training || 0}
          icon={<FileText className="w-6 h-6" />}
          link="/compliance/training"
          color="purple"
        />
      </div>
      {/* Priority Actions */}
      {lastCheck?.priority_actions && lastCheck.priority_actions.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Priority Actions</h2>
            <Badge color="red" variant="outline">
              {lastCheck.priority_actions.length} Required
            </Badge>
          </div>
          <div className="space-y-3">
            {lastCheck.priority_actions.slice(0, 5).map((action, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Badge color={action.priority === 'critical' ? 'red' : 'orange'} size="sm">
                      {action.priority.toUpperCase()}
                    </Badge>
                    <span className="text-sm font-medium text-gray-900">{action.action}</span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{action.category}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Deadline</p>
                  <p className="text-sm font-medium">{action.deadline}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
      {/* Quick Actions & Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <QuickActionCard
              description="Manage mandatory training assignments"
              icon={<FileText className="w-8 h-8" />}
              link="/compliance/training"
              color="blue"
            />
            <QuickActionCard
              description="Review employee feedback submissions"
              icon={<Activity className="w-8 h-8" />}
              link="/compliance/feedback"
              color="green"
            />
            <QuickActionCard
              description="View employee rights information"
              icon={<Shield className="w-8 h-8" />}
              link="/compliance/rights"
              color="purple"
            />
            <QuickActionCard
              description="Review system activity logs"
              icon={<Clock className="w-8 h-8" />}
              link="/compliance/audit"
              color="gray"
            />
          </div>
        </Card>
        <Card>
          <h2 className="text-xl font-semibold mb-4">Compliance Trends</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Current Score</span>
              <span className={`font-semibold ${getScoreColor(complianceData?.overall || 0)}`}>
                {complianceData?.overall || 0}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Status</span>
              <Badge color={getStatusColor(complianceData?.status || 'critical')} size="sm">
                {complianceData?.status?.replace('_', ' ') || 'Unknown'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Check</span>
              <span className="text-sm">
                {lastCheck?.check_date ?
                  new Date(lastCheck.check_date).toLocaleDateString() :
                  'Not run'
                }
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  (complianceData?.overall || 0) >= 90 ? 'bg-green-500' :
                  (complianceData?.overall || 0) >= 75 ? 'bg-yellow-500' :
                  (complianceData?.overall || 0) >= 60 ? 'bg-orange-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${complianceData?.overall || 0}%` }}
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
// Compliance Category Card Component
interface ComplianceCategoryCardProps {
  title: string;
  score: number;
  icon: React.ReactNode;
  link: string;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red' | 'orange' | 'gray';
}
const ComplianceCategoryCard: React.FC<ComplianceCategoryCardProps> = ({
  title,
  score,
  icon,
  link,
  color
}) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-600 hover:bg-blue-600',
      green: 'bg-green-500 text-green-600 hover:bg-green-600',
      yellow: 'bg-yellow-500 text-yellow-600 hover:bg-yellow-600',
      purple: 'bg-purple-500 text-purple-600 hover:bg-purple-600',
      red: 'bg-red-500 text-red-600 hover:bg-red-600',
      orange: 'bg-orange-500 text-orange-600 hover:bg-orange-600',
      gray: 'bg-gray-500 text-gray-600 hover:bg-gray-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <a
      href={link}
      className="block group"
    >
      <Card className="h-full transition-all duration-200 hover:shadow-lg group-hover:scale-105">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-3 rounded-lg bg-opacity-10 ${getColorClasses(color)}`}>
            {icon}
          </div>
          <span className={`text-2xl font-bold ${
            score >= 90 ? 'text-green-600' :
            score >= 75 ? 'text-yellow-600' :
            score >= 60 ? 'text-orange-600' :
            'text-red-600'
          }`}>
            {score}%
          </span>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600">
          {title}
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {score >= 90 ? 'Excellent' :
           score >= 75 ? 'Good' :
           score >= 60 ? 'Needs Improvement' :
           'Critical'}
        </p>
        <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              score >= 90 ? 'bg-green-500' :
              score >= 75 ? 'bg-yellow-500' :
              score >= 60 ? 'bg-orange-500' :
              'bg-red-500'
            }`}
            style={{ width: `${score}%` }}
          />
        </div>
      </Card>
    </a>
  );
};
// Quick Action Card Component
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  link: string;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red' | 'orange' | 'gray';
}
const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  description,
  icon,
  link,
  color
}) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'text-blue-600 hover:bg-blue-50',
      green: 'text-green-600 hover:bg-green-50',
      yellow: 'text-yellow-600 hover:bg-yellow-50',
      purple: 'text-purple-600 hover:bg-purple-50',
      red: 'text-red-600 hover:bg-red-50',
      orange: 'text-orange-600 hover:bg-orange-50',
      gray: 'text-gray-600 hover:bg-gray-50'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <a
      href={link}
      className={`block p-4 rounded-lg border transition-all duration-200 ${getColorClasses(color)}`}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          {icon}
        </div>
        <div>
          <h3 className="font-semibold">{title}</h3>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </a>
  );
};