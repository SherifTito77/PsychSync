import React, { useState, useEffect } from 'react';
import {
  ClipboardCheck,
  AlertTriangle,
  CheckCircle,
  Clock,
  Shield,
  FileText,
  Download,
  Calendar,
  Filter,
  Search,
  TrendingUp,
  RefreshCw,
ChevronDown,
} from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
import { Button } from '../common/Button';
import { Card } from '../common/card';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
interface ComplianceChecklistProps {
  className?: string;
}
interface ComplianceResult {
  organization_id: string;
  check_date: string;
  check_type: string;
  compliance_score: number;
  compliance_status: string;
  categories: Record<string, {
    compliance_score: number;
    checks: Array<{
      check: string;
      status: string;
      severity: string;
      violations?: any[];
    }>;
    violations: any[];
    recommendations: string[];
  }>;
  priority_actions: Array<{
    priority: string;
    category: string;
    action: string;
    deadline: string;
  }>;
  next_check_date: string;
}
export const ComplianceChecklist: React.FC<ComplianceChecklistProps> = ({ className = '' }) => {
  const [checkResults, setCheckResults] = useState<ComplianceResult | null>(null);
  const [running, setRunning] = useState(false);
  const [checkType, setCheckType] = useState('full');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const { showNotification } = useNotification();
  useEffect(() => {
    loadLatestResults();
  }, []);
  const loadLatestResults = async () => {
    try {
      setLoading(true);
      const data = await complianceService.getComplianceAnalytics().catch(() => null);
      if (data) {
        setCheckResults(data);
      }
    } catch (error) {
      console.error('Failed to load latest results:', error);
    } finally {
      setLoading(false);
    }
  };
  const runComplianceCheck = async () => {
    try {
      setRunning(true);
      const result = await complianceService.runComplianceCheck(checkType);
      setCheckResults(result);
      showNotification(`Compliance check completed. Score: ${result.compliance_score}/100`, 'success');
    } catch (error) {
      showNotification('Failed to run compliance check', 'error');
    } finally {
      setRunning(false);
    }
  };
  const exportReport = async () => {
    try {
      const response = await fetch('/api/v1/reports/compliance/checklist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ checkType })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-checklist-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Report exported successfully', 'success');
      }
    } catch (error) {
      showNotification('Failed to export report', 'error');
    }
  };
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
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
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compliance Checklist</h1>
          <p className="text-gray-600 mt-1">
            Automated compliance verification and remediation guidance
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={exportReport}
            icon={<Download className="w-4 h-4" />}
          >
            Export Report
          </Button>
          <Button
            onClick={runComplianceCheck}
            disabled={running}
            icon={running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ClipboardCheck className="w-4 h-4" />}
          >
            {running ? 'Running Check...' : 'Run Compliance Check'}
          </Button>
        </div>
      </div>
      {/* Check Type Selection */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Check Type</h3>
          {checkResults && (
            <div className="text-sm text-gray-600">
              Last run: {new Date(checkResults.check_date).toLocaleDateString()}
            </div>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { value: 'full', label: 'Full Compliance', desc: 'Complete compliance review' },
            { value: 'labor', label: 'Labor Law', desc: 'Wage, hour, and employment laws' },
            { value: 'privacy', label: 'Data Privacy', desc: 'GDPR, CCPA compliance' },
            { value: 'safety', label: 'Workplace Safety', desc: 'OSHA and safety regulations' }
          ].map((type) => (
            <button
              key={type.value}
              onClick={() => setCheckType(type.value)}
              className={`p-4 rounded-lg border text-left transition-all ${
                checkType === type.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-medium">{type.label}</div>
              <div className="text-sm text-gray-600">{type.desc}</div>
            </button>
          ))}
        </div>
      </Card>
      {/* Compliance Score Overview */}
      {checkResults && (
        <>
          <Card className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">Compliance Score</h2>
                <div className="flex items-baseline">
                  <span className="text-5xl font-bold">{checkResults.compliance_score}</span>
                  <span className="text-2xl font-semibold ml-2">/ 100</span>
                </div>
                <div className="mt-3">
                  <Badge color={getStatusColor(checkResults.compliance_status)} variant="solid">
                    {checkResults.compliance_status.replace('_', ' ').toUpperCase()}
                  </Badge>
                </div>
              </div>
              <ClipboardCheck className="w-24 h-24 opacity-20" />
            </div>
          </Card>
          {/* Priority Actions */}
          {checkResults.priority_actions.length > 0 && (
            <Card>
              <div className="flex items-center mb-4">
                <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                <h3 className="text-lg font-semibold">Priority Actions</h3>
                <Badge color="red" className="ml-2">
                  {checkResults.priority_actions.length} Required
                </Badge>
              </div>
              <div className="space-y-3">
                {checkResults.priority_actions.map((action, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-l-4 ${
                      action.priority === 'critical'
                        ? 'bg-red-50 border-red-500'
                        : action.priority === 'high'
                        ? 'bg-orange-50 border-orange-500'
                        : 'bg-yellow-50 border-yellow-500'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge
                            color={action.priority === 'critical' ? 'red' : action.priority === 'high' ? 'orange' : 'yellow'}
                            size="sm"
                          >
                            {action.priority.toUpperCase()}
                          </Badge>
                          <span className="text-sm text-gray-600">{action.category}</span>
                        </div>
                        <p className="font-medium text-gray-900">{action.action}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Deadline</p>
                        <p className="text-sm font-medium">{action.deadline}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
          {/* Category Breakdown */}
          <div className="space-y-6">
            <h3 className="text-xl font-semibold">Category Breakdown</h3>
            {Object.entries(checkResults.categories).map(([categoryKey, category]) => (
              <Card key={categoryKey}>
                <div
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => toggleCategory(categoryKey)}
                >
                  <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-lg ${
                      category.compliance_score >= 90 ? 'bg-green-100 text-green-600' :
                      category.compliance_score >= 75 ? 'bg-blue-100 text-blue-600' :
                      category.compliance_score >= 60 ? 'bg-yellow-100 text-yellow-600' :
                      'bg-red-100 text-red-600'
                    }`}>
                      {getCategoryIcon(categoryKey)}
                    </div>
                    <div>
                      <h4 className="text-lg font-semibold">{getCategoryTitle(categoryKey)}</h4>
                      <p className="text-sm text-gray-600">{getCategoryDescription(categoryKey)}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getScoreColor(category.compliance_score)}`}>
                        {category.compliance_score}%
                      </p>
                      <p className="text-sm text-gray-600">
                        {category.compliance_score >= 90 ? 'Excellent' :
                         category.compliance_score >= 75 ? 'Good' :
                         category.compliance_score >= 60 ? 'Needs Improvement' :
                         'Critical'}
                      </p>
                    </div>
                    <ChevronDown
                      className={`w-5 h-5 text-gray-400 transform transition-transform ${
                        expandedCategories.has(categoryKey) ? 'rotate-180' : ''
                      }`}
                    />
                  </div>
                </div>
                {expandedCategories.has(categoryKey) && (
                  <div className="mt-6 pt-6 border-t">
                    {/* Checks List */}
                    <div className="space-y-3 mb-6">
                      <h5 className="font-medium text-gray-900">Checks Performed</h5>
                      {category.checks.map((check, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <CheckStatusIcon status={check.status} />
                            <span className="text-sm font-medium">{check.check}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {check.severity !== 'none' && (
                              <Badge
                                color={check.severity === 'critical' ? 'red' : check.severity === 'high' ? 'orange' : 'yellow'}
                                size="sm"
                              >
                                {check.severity}
                              </Badge>
                            )}
                            <CheckStatusBadge status={check.status} />
                          </div>
                        </div>
                      ))}
                    </div>
                    {/* Violations */}
                    {category.violations.length > 0 && (
                      <div className="mb-6">
                        <h5 className="font-medium text-red-900 mb-3">Violations Found</h5>
                        <div className="space-y-2">
                          {category.violations.map((violation, index) => (
                            <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                              <div className="flex items-start space-x-2">
                                <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5" />
                                <div>
                                  <p className="text-sm font-medium text-red-900">{violation.check}</p>
                                  {violation.violations && (
                                    <ul className="text-xs text-red-700 mt-1 list-disc list-inside">
                                      {violation.violations.map((v: any, i: number) => (
                                        <li key={i}>{v}</li>
                                      ))}
                                    </ul>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {/* Recommendations */}
                    {category.recommendations.length > 0 && (
                      <div>
                        <h5 className="font-medium text-blue-900 mb-3">Recommendations</h5>
                        <ul className="space-y-2">
                          {category.recommendations.map((recommendation, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <CheckCircle className="w-4 h-4 text-blue-600 mt-0.5" />
                              <span className="text-sm text-blue-900">{recommendation}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            ))}
          </div>
          {/* Next Check Date */}
          <Card>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-blue-600" />
                <div>
                  <h3 className="font-semibold">Next Scheduled Check</h3>
                  <p className="text-sm text-gray-600">
                    Automated compliance checks run monthly
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-blue-600">
                  {new Date(checkResults.next_check_date).toLocaleDateString()}
                </p>
                <p className="text-sm text-gray-600">
                  {Math.ceil((new Date(checkResults.next_check_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} days
                </p>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};
// Helper Components
const getCategoryIcon = (categoryKey: string) => {
  const icons: Record<string, React.ReactNode> = {
    labor_law: <FileText className="w-5 h-5" />,
    data_privacy: <Shield className="w-5 h-5" />,
    workplace_safety: <AlertTriangle className="w-5 h-5" />,
    training: <TrendingUp className="w-5 h-5" />,
    documentation: <ClipboardCheck className="w-5 h-5" />
  };
  return icons[categoryKey] || <ClipboardCheck className="w-5 h-5" />;
};
const getCategoryTitle = (categoryKey: string): string => {
  const titles: Record<string, string> = {
    labor_law: 'Labor Law Compliance',
    data_privacy: 'Data Privacy & Security',
    workplace_safety: 'Workplace Safety',
    training: 'Training Compliance',
    documentation: 'Documentation Requirements'
  };
  return titles[categoryKey] || categoryKey.replace('_', ' ').title();
};
const getCategoryDescription = (categoryKey: string): string => {
  const descriptions: Record<string, string> = {
    labor_law: 'Minimum wage, overtime, classification, and employment law compliance',
    data_privacy: 'Data protection, privacy policies, and regulatory compliance',
    workplace_safety: 'OSHA regulations, safety protocols, and incident reporting',
    training: 'Mandatory training completion and certification tracking',
    documentation: 'Required policies, posters, and compliance documentation'
  };
  return descriptions[categoryKey] || 'Compliance requirements and verification';
};
const CheckStatusIcon: React.FC<{ status: string }> = ({ status }) => {
  switch (status) {
    case 'pass':
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    case 'fail':
      return <AlertTriangle className="w-5 h-5 text-red-600" />;
    case 'warning':
      return <Clock className="w-5 h-5 text-yellow-600" />;
    default:
      return <Clock className="w-5 h-5 text-gray-400" />;
  }
};
const CheckStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusConfig = {
    pass: { color: 'green', label: 'Pass' },
    fail: { color: 'red', label: 'Fail' },
    warning: { color: 'yellow', label: 'Warning' }
  };
  const config = statusConfig[status as keyof typeof statusConfig] || {
    color: 'gray',
    label: status
  };
  return <Badge color={config.color} size="sm">{config.label}</Badge>;
};