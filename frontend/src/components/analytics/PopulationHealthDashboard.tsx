/**
 * Population Health Dashboard
 *
 * Executive dashboard for clinicians and administrators to monitor
 * population health metrics, high-risk users, treatment outcomes, and trends.
 *
 * Features:
 * - Overview metrics cards
 * - High-risk user identification
 * - Treatment outcome visualization
 * - Time series trend charts
 * - Assessment type comparison
 * - Real-time data refresh
 *
 * Access: Clinicians and Administrators only
 */

import React, { useState, useEffect, useRef, memo, useMemo, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

// TODO(human): Implement performance optimization through component memoization
// The dashboard has several child components that re-render unnecessarily when parent state changes.
// Your task is to:
// 1. Extract MetricCard, HighRiskUsersList, TreatmentOutcomesChart, and TimeSeriesChart into separate memoized components
// 2. Use useMemo() for expensive calculations (like risk distribution calculations)
// 3. Use useCallback() for event handlers to prevent child re-renders
// 4. Consider using React.memo() for components that only depend on their props
//
// Performance goal: Reduce unnecessary re-renders by 60-80% when filters change
import {
  Users,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  RefreshCw,
  Download,
  Filter,
  Brain,
  HeartPulse,
} from 'lucide-react';
import api from '@/services/api';

// =============================================================================
// Types
// =============================================================================

interface PopulationMetrics {
  total_users: number;
  active_assessments: number;
  average_scores: Record<string, number>;
  risk_distribution: {
    critical: number;
    high: number;
    moderate: number;
    low: number;
  };
  crisis_count: number;
  high_risk_count: number;
  moderate_risk_count: number;
  low_risk_count: number;
}

interface HighRiskUser {
  user_id: string;
  risk_level: string;
  prediction_type: string;
  current_score: number;
  trend: string;
  last_assessment: string;
  factors: {
    crisis_alert: boolean;
    risk_flags: string[];
  };
}

interface TreatmentOutcome {
  outcome_type: string;
  count: number;
  percentage: number;
  avg_score_change: number | null;
}

interface TimeSeriesData {
  period: string;
  avg_score: number;
  assessment_count: number;
  high_risk_count: number;
  crisis_count: number;
}

interface SummaryStatistics {
  population_metrics: PopulationMetrics;
  high_risk_users: {
    count: number;
    users: HighRiskUser[];
  };
  treatment_outcomes: TreatmentOutcome[];
  trend_direction: string;
  crisis_rate: number;
  high_risk_rate: number;
}

// =============================================================================
// Memoized Components
// =============================================================================

const MetricCard = memo(function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  trendUp,
  color = "blue",
}: {
  title: string;
  value: string | number;
  icon: any;
  description: string;
  trend?: string;
  trendUp?: boolean;
  color?: string;
}) {
  const colorClasses = {
    blue: "bg-blue-50 border-blue-200",
    green: "bg-green-50 border-green-200",
    red: "bg-red-50 border-red-200",
    yellow: "bg-yellow-50 border-yellow-200",
    purple: "bg-purple-50 border-purple-200",
  };

  const iconColors = {
    blue: "text-blue-600",
    green: "text-green-600",
    red: "text-red-600",
    yellow: "text-yellow-600",
    purple: "text-purple-600",
  };

  return (
    <Card className={`${colorClasses[color as keyof typeof colorClasses]} border-2`}>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
            <h3 className="text-3xl font-bold text-gray-900">{value}</h3>
            <p className="text-sm text-gray-600 mt-2">{description}</p>
            {trend && (
              <div className={`flex items-center mt-2 text-sm ${trendUp ? 'text-red-600' : 'text-green-600'}`}>
                {trendUp ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
                {trend}
              </div>
            )}
          </div>
          <Icon className={`h-12 w-12 ${iconColors[color as keyof typeof iconColors]}`} />
        </div>
      </CardContent>
    </Card>
  );
});

const HighRiskUsersList = memo(function HighRiskUsersList({ users }: { users: HighRiskUser[] }) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'worsening':
        return <TrendingUp className="h-4 w-4 text-red-600" />;
      case 'improving':
        return <TrendingDown className="h-4 w-4 text-green-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-3">
      {users.map((user) => (
        <Card key={user.user_id} className="hover:shadow-md transition-shadow">
          <CardContent className="pt-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getRiskColor(user.risk_level)}`}>
                    {user.risk_level.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-500">{user.prediction_type}</span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Current Score: </span>
                    <span className="font-semibold">{user.current_score.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {getTrendIcon(user.trend)}
                    <span className="text-gray-600 capitalize">{user.trend}</span>
                  </div>
                  <div className="text-gray-500 text-xs">
                    Last: {new Date(user.last_assessment).toLocaleDateString()}
                  </div>
                </div>
                {user.factors.risk_flags && user.factors.risk_flags.length > 0 && (
                  <div className="mt-2">
                    <span className="text-xs font-semibold text-gray-700">Risk Flags: </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {user.factors.risk_flags.slice(0, 3).map((flag, idx) => (
                        <span key={idx} className="text-xs bg-orange-50 text-orange-700 px-2 py-0.5 rounded">
                          {flag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <Button size="sm" variant="outline">
                View Details
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
});
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Current Score: </span>
                    <span className="font-semibold">{user.current_score.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {getTrendIcon(user.trend)}
                    <span className="text-gray-600 capitalize">{user.trend}</span>
                  </div>
                  <div className="text-gray-500 text-xs">
                    Last: {new Date(user.last_assessment).toLocaleDateString()}
                  </div>
                </div>
                {user.factors.risk_flags && user.factors.risk_flags.length > 0 && (
                  <div className="mt-2">
                    <span className="text-xs font-semibold text-gray-700">Risk Flags: </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {user.factors.risk_flags.slice(0, 3).map((flag, idx) => (
                        <span key={idx} className="text-xs bg-orange-50 text-orange-700 px-2 py-0.5 rounded">
                          {flag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <Button size="sm" variant="outline">
                View Details
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function TreatmentOutcomesChart({ outcomes }: { outcomes: TreatmentOutcome[] }) {
  const maxCount = Math.max(...outcomes.map((o) => o.count));

  const getOutcomeColor = (type: string) => {
    switch (type) {
      case 'full_response':
        return 'bg-green-500';
      case 'partial_response':
        return 'bg-blue-500';
      case 'non_response':
        return 'bg-yellow-500';
      case 'deterioration':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getOutcomeLabel = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="space-y-4">
      {outcomes.map((outcome) => (
        <div key={outcome.outcome_type} className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">
              {getOutcomeLabel(outcome.outcome_type)}
            </span>
            <span className="text-sm text-gray-600">
              {outcome.count} users ({outcome.percentage.toFixed(1)}%)
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
              className={`h-full ${getOutcomeColor(outcome.outcome_type)} transition-all duration-500`}
              style={{ width: `${(outcome.count / maxCount) * 100}%` }}
            />
          </div>
          {outcome.avg_score_change !== null && (
            <div className="text-xs text-gray-500 text-right">
              Avg change: {outcome.avg_score_change > 0 ? '+' : ''}{outcome.avg_score_change.toFixed(1)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function TimeSeriesChart({ data }: { data: TimeSeriesData[] }) {
  const maxScore = Math.max(...data.map((d) => d.avg_score));
  const maxCount = Math.max(...data.map((d) => d.assessment_count));

  return (
    <div className="space-y-4">
      {data.map((point, idx) => (
        <div key={idx} className="space-y-2">
          <div className="text-xs text-gray-600 font-medium">{point.period}</div>

          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-600">Avg Score</span>
              <span className="font-semibold">{point.avg_score.toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${(point.avg_score / maxScore) * 100}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-600">Assessments: </span>
              <span className="font-semibold">{point.assessment_count}</span>
            </div>
            <div>
              <span className="text-gray-600">High Risk: </span>
              <span className="font-semibold text-orange-600">{point.high_risk_count}</span>
            </div>
            <div className="col-span-2">
              <span className="text-gray-600">Crisis: </span>
              <span className="font-semibold text-red-600">{point.crisis_count}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// Main Dashboard Component
// =============================================================================

export default function PopulationHealthDashboard() {
  const [summary, setSummary] = useState<SummaryStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daysBack, setDaysBack] = useState(30);
  const [refreshing, setRefreshing] = useState(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    fetchSummary();

    return () => {
      isMountedRef.current = false;
    };
  }, [daysBack]);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/api/v1/population-health/summary?days_back=${daysBack}`);
      if (isMountedRef.current) {
        setSummary(response.data);
      }
    } catch (err: any) {
      console.error('Error fetching summary:', err);
      if (isMountedRef.current) {
        setError(
          err.response?.data?.detail || 'Failed to load population health data'
        );
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchSummary();
  };

  const handleExport = () => {
    // Export functionality placeholder
    console.log('Exporting data...');
  };

  // Loading state
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <RefreshCw className="h-12 w-12 mx-auto mb-4 text-blue-600 animate-spin" />
            <p className="text-lg text-gray-600">Loading population health data...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error || !summary) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error || 'Unable to load population health data'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const metrics = summary.population_metrics;
  const highRiskUsers = summary.high_risk_users.users;
  const treatmentOutcomes = summary.treatment_outcomes;
  const trend = summary.trend_direction;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Population Health Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Monitor clinical outcomes across all users
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDaysBack(daysBack === 30 ? 90 : 30)}
          >
            <Filter className="h-4 w-4 mr-2" />
            {daysBack} Days
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alert for concerning trends */}
      {(summary.crisis_rate > 5 || trend === 'worsening') && (
        <Alert className="border-red-500 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-900">
            {trend === 'worsening' && (
              <strong>⚠️ Worsening trend detected - population scores are increasing over time. </strong>
            )}
            {summary.crisis_rate > 5 && (
              <strong>
                {trend === 'worsening' ? ' | ' : '⚠️ '}
                High crisis rate ({summary.crisis_rate.toFixed(1)}%) requires attention.
              </strong>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Overview Metrics */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Total Users"
            value={metrics.total_users}
            icon={Users}
            description="Unique users with assessments"
            color="blue"
          />
          <MetricCard
            title="Active Assessments"
            value={metrics.active_assessments}
            icon={Activity}
            description={`In last ${daysBack} days`}
            color="purple"
          />
          <MetricCard
            title="Crisis Alerts"
            value={metrics.crisis_count}
            icon={AlertTriangle}
            description={`${summary.crisis_rate.toFixed(1)}% of assessments`}
            color="red"
          />
          <MetricCard
            title="High-Risk Users"
            value={metrics.high_risk_count}
            icon={HeartPulse}
            description={`${summary.high_risk_rate.toFixed(1)}% of users`}
            trend={trend === 'worsening' ? 'Worsening' : trend === 'improving' ? 'Improving' : 'Stable'}
            trendUp={trend === 'worsening'}
            color={trend === 'worsening' ? 'red' : trend === 'improving' ? 'green' : 'yellow'}
          />
        </div>
      </Card>

      {/* Risk Distribution Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Level Distribution</CardTitle>
          <CardDescription>User distribution across risk categories</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { label: 'Critical', count: metrics.risk_distribution.critical, color: 'bg-red-500' },
              { label: 'High', count: metrics.risk_distribution.high, color: 'bg-orange-500' },
              { label: 'Moderate', count: metrics.risk_distribution.moderate, color: 'bg-yellow-500' },
              { label: 'Low', count: metrics.risk_distribution.low, color: 'bg-green-500' },
            ].map((level) => {
              const percentage = metrics.active_assessments > 0
                ? (level.count / metrics.active_assessments) * 100
                : 0;

              return (
                <div key={level.label} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{level.label}</span>
                    <span className="text-gray-600">
                      {level.count} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${level.color}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* High-Risk Users */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              High-Risk Users Requiring Attention
            </CardTitle>
            <CardDescription>
              {summary.high_risk_users.count} users identified
            </CardDescription>
          </CardHeader>
          <CardContent>
            {highRiskUsers.length > 0 ? (
              <HighRiskUsersList users={highRiskUsers} />
            ) : (
              <div className="text-center py-8 text-gray-500">
                <HeartPulse className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>No high-risk users identified</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Treatment Outcomes */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-600" />
              Treatment Outcomes
            </CardTitle>
            <CardDescription>
                Population response to treatment
            </CardDescription>
          </CardHeader>
          <CardContent>
            {treatmentOutcomes.length > 0 ? (
              <TreatmentOutcomesChart outcomes={treatmentOutcomes} />
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>Insufficient data for outcome analysis</p>
                <p className="text-sm mt-1">Requires users with 4+ assessments</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <Card className="bg-gray-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <p>Data refreshed: {new Date().toLocaleString()}</p>
              <p className="mt-1">Lookback period: Last {daysBack} days</p>
            </div>
            <div className="text-right">
              <p className="font-semibold">Population Health Analytics</p>
              <p className="text-xs">For clinical monitoring and quality improvement</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
