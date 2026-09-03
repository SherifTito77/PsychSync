/**
 * Manager Health Dashboard Component
 *
 * Displays anonymized team health analytics for managers and HR.
 * Privacy-focused with aggregate metrics only - no individual identifiers.
 *
 * Features:
 * - Team stress distribution (anonymized)
 * - Cardiovascular risk trends
 * - Weekly stress trend analysis
 * - High-risk member counts (no identities)
 * - Active intervention tracking
 * - Organizational risk factors
 * - Team action recommendations
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Progress from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Users,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Shield,
  Activity,
  Heart,
  Calendar,
  Building,
  Target,
  CheckCircle,
} from 'lucide-react';
import ManagerDashboardService from '@/services/managerDashboardService';
import type { ManagerDashboardData, StressDistribution } from '@/types/healthMonitoring';
import { useDebouncedCallback } from '@/hooks/usePerformanceOptimizations';

export const ManagerDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<ManagerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<number>(30);

  // Track the most recent request ID to ignore stale responses
  // NO AbortController - let all requests complete naturally
  const requestIdRef = useRef<number>(0);

  // Fetch dashboard data with proper race condition protection
  const fetchDashboardData = useCallback(async () => {
    // Generate a unique request ID for this fetch
    const currentRequestId = ++requestIdRef.current;

    console.log('[ManagerDashboard] Fetch called, request ID:', currentRequestId);

    console.log('[ManagerDashboard] Starting fetch...');
    setLoading(true);
    setError(null);

    try {
      const data = selectedTeam === 'all'
        ? await ManagerDashboardService.getOrganizationOverview(timeRange)
        : await ManagerDashboardService.getTeamOverview(selectedTeam, timeRange);

      // Only update state if this is still the most recent request
      if (currentRequestId !== requestIdRef.current) {
        console.log('[ManagerDashboard] Ignoring stale response from request', currentRequestId, ', latest is', requestIdRef.current);
        return;
      }

      console.log('[ManagerDashboard] Setting dashboard data:', data);
      setDashboardData(data);
    } catch (err: any) {
      // Only show error if this is still the most recent request
      if (currentRequestId === requestIdRef.current) {
        console.error('Failed to fetch dashboard data:', err);
        if (err.response) {
          console.error('Error response:', {
            status: err.response.status,
            data: err.response.data,
            headers: err.response.headers
          });
        } else if (err.request) {
          console.error('No response received:', err.request);
        } else {
          console.error('Error message:', err.message);
        }
        setError(`Unable to load team health data: ${err.response?.data?.message || err.message || 'Please check your permissions'}`);
      } else {
        console.log('[ManagerDashboard] Ignoring error from stale request', currentRequestId);
      }
    } finally {
      // Only clear loading state if this is still the most recent request
      if (currentRequestId === requestIdRef.current) {
        console.log('[ManagerDashboard] Request', currentRequestId, 'completed, clearing loading state');
        setLoading(false);
      }
    }
  }, [selectedTeam, timeRange]);

  // Initial data load with race condition protection
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Debounced refresh handler (500ms debounce)
  const handleRefresh = useDebouncedCallback(() => {
    fetchDashboardData();
  }, 500, []);

  // Utility functions
  const getStressColor = (level: string): string => {
    switch (level) {
      case 'normal': return 'bg-green-500';
      case 'elevated': return 'bg-yellow-500';
      case 'high': return 'bg-orange-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStressLevel = (score: number): string => {
    if (score < 1.5) return 'normal';
    if (score < 2.5) return 'elevated';
    if (score < 3.5) return 'high';
    return 'critical';
  };

  const getRiskPercentage = (distribution: StressDistribution, level: string): number => {
    const total = Object.values(distribution).reduce((sum, count) => sum + (count as number), 0);
    if (total === 0) return 0;
    return ((distribution as any)[level] / total) * 100;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-muted-foreground">
          Loading team health analytics...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="error">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Access Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!dashboardData) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Team Health Dashboard</h2>
          <p className="text-muted-foreground">
            {dashboardData.team_name} • Last analyzed: {new Date(dashboardData.analysis_date).toLocaleDateString()}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Button onClick={handleRefresh} variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Privacy Notice */}
      <Alert className="border-blue-500 bg-blue-50 dark:bg-blue-950">
        <Shield className="h-4 w-4 text-blue-600" />
        <AlertTitle className="text-blue-900 dark:text-blue-100">
          Privacy-First Analytics
        </AlertTitle>
        <AlertDescription className="text-blue-800 dark:text-blue-200">
          This dashboard displays aggregate, anonymized metrics only. No individual employee data is visible.
        </AlertDescription>
      </Alert>

      {/* Critical Alerts */}
      {(dashboardData.high_risk_members_count > 0 || dashboardData.critical_interventions_active > 0) && (
        <Alert className="border-red-500 bg-red-50 dark:bg-red-950">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-900 dark:text-red-100">
            Attention Required
          </AlertTitle>
          <AlertDescription className="text-red-800 dark:text-red-200">
            {dashboardData.critical_interventions_active > 0 && (
              <span>{dashboardData.critical_interventions_active} critical intervention(s) currently active.{' '}
              </span>
            )}
            {dashboardData.high_risk_members_count > 0 && (
              <span>{dashboardData.high_risk_members_count} team member(s) at elevated health risk.</span>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Key Metrics Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Team Size */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Team Size</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">
                {dashboardData.members_analyzed}/{dashboardData.total_team_members}
              </div>
              <Users className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Members analyzed
            </p>
          </CardContent>
        </Card>

        {/* Average Stress Level */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg Stress Level</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">
                {dashboardData.average_stress_level.toFixed(1)}/4.0
              </div>
              <Progress
                value={(dashboardData.average_stress_level / 4) * 100}
                className="h-2"
              />
              <Badge
                className={`${getStressColor(getStressLevel(dashboardData.average_stress_level))} text-white`}
              >
                {getStressLevel(dashboardData.average_stress_level).toUpperCase()}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* High Risk Members */}
        <Card className={dashboardData.high_risk_members_count > 0 ? 'border-red-500' : ''}>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">High Risk Members</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-red-600">
                {dashboardData.high_risk_members_count}
              </div>
              <AlertTriangle className="h-5 w-5 text-red-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Require attention
            </p>
          </CardContent>
        </Card>

        {/* Active Interventions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active Interventions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">
                {dashboardData.critical_interventions_active}
              </div>
              <Target className="h-5 w-5 text-orange-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Critical interventions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Stress Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Stress Level Distribution</CardTitle>
          <CardDescription>
            Anonymized breakdown of team stress levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(['normal', 'elevated', 'high', 'critical'] as const).map((level) => {
              const count = dashboardData.stress_distribution[level];
              const percentage = getRiskPercentage(dashboardData.stress_distribution, level);

              return (
                <div key={level} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize font-medium">{level}</span>
                    <span className="text-muted-foreground">{count} members ({percentage.toFixed(0)}%)</span>
                  </div>
                  <Progress value={percentage} className={`h-2 ${getStressColor(level)}`} />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Cardiovascular Risk Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Heart className="mr-2 h-5 w-5 text-red-500" />
            Cardiovascular Risk Distribution
          </CardTitle>
          <CardDescription>
            Aggregate cardiovascular health metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {(['low', 'medium', 'high'] as const).map((level) => {
              const count = dashboardData.cardiovascular_risk_distribution[level];
              const total = Object.values(dashboardData.cardiovascular_risk_distribution).reduce((sum, c) => sum + (c as number), 0);
              const percentage = total > 0 ? (count / total) * 100 : 0;

              return (
                <Card key={level} className={`text-center ${
                  level === 'high' ? 'border-red-500 bg-red-50 dark:bg-red-950' :
                  level === 'medium' ? 'border-yellow-500' :
                  'border-green-500'
                }`}>
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold mb-1">{count}</div>
                    <div className="text-sm text-muted-foreground capitalize">{level} risk</div>
                    <div className="text-xs text-muted-foreground mt-1">{percentage.toFixed(0)}%</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Weekly Stress Trend */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <TrendingUp className="mr-2 h-5 w-5 text-blue-500" />
            Weekly Stress Trend
          </CardTitle>
          <CardDescription>
            Stress level changes over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {dashboardData.weekly_stress_trend.map((week, index) => {
              const prevWeek = dashboardData.weekly_stress_trend[index - 1];
              const trend = prevWeek ? week.avg_stress - prevWeek.avg_stress : 0;

              return (
                <div key={week.week} className="flex items-center justify-between p-3 rounded-lg border">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{week.week}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-lg font-bold">{week.avg_stress.toFixed(1)}</div>
                      <div className="text-xs text-muted-foreground">Avg stress</div>
                    </div>
                    {trend !== 0 && (
                      <div className={`flex items-center gap-1 ${trend > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {trend > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                        <span className="text-sm font-medium">{Math.abs(trend).toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Organizational Risk Factors */}
      {dashboardData.organizational_risk_factors.length > 0 && (
        <Card className="border-orange-500">
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="mr-2 h-5 w-5 text-orange-600" />
              Organizational Risk Factors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {dashboardData.organizational_risk_factors.map((factor, index) => (
                <li key={index} className="flex items-start">
                  <AlertTriangle className="mr-2 h-4 w-4 text-orange-500 mt-1 flex-shrink-0" />
                  <span className="text-sm">{factor}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Recommended Team Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="mr-2 h-5 w-5 text-blue-600" />
            Recommended Team Actions
          </CardTitle>
          <CardDescription>
            Data-driven recommendations to improve team wellness
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {dashboardData.recommended_team_actions.map((action, index) => (
              <li key={index} className="flex items-start">
                <CheckCircle className="mr-2 h-4 w-4 text-green-500 mt-1 flex-shrink-0" />
                <span className="text-sm">{action}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default ManagerDashboard;
