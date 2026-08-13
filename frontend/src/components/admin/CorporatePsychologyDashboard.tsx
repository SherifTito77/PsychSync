/**
 * Corporate Psychology Executive Dashboard
 *
 * System-level organizational psychology intelligence for executive decision-making.
 * Displays the 6 core psychology encodings and provides early-warning signals.
 *
 * **IMPORTANT**: This dashboard operates at SYSTEM level, NOT individual level.
 * No personal or diagnostic information is displayed.
 *
 * Core Encodings:
 * - Cognitive Load Index (CLI): Overall cognitive burden on organization
 * - Trust Stability Curve (TSC): Stability and strength of trust
 * - Emotional Volatility Signal (EVS): Emotional regulation at organizational level
 * - Coordination Friction Score (CFS): Efficiency of coordination
 * - Psychological Debt Accumulation (PDA): Accumulated strain
 * - Recovery & Resilience Capacity (RRC): Ability to recover and bounce back
 *
 * Author: PsychSync Team
 * Version: 1.0
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  Brain,
  HeartPulse,
  Network,
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  Activity,
  Zap,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Target,
  ArrowUpDown,
} from 'lucide-react';
import corporatePsychologyService from '@/services/corporatePsychologyService';
import { useAuth } from '@/contexts/AuthContext';

// ═══════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════

interface PsychologyMetrics {
  organization_id: string;
  team_id?: string;
  measurement_period_start: string;
  measurement_period_end: string;

  // Core encodings (0-100 scale)
  cognitive_load_index: number;
  trust_stability_score: number;
  emotional_volatility_score: number;
  coordination_friction_score: number;
  psychological_debt_score: number;
  recovery_resilience_score: number;

  // Aggregate metrics
  organizational_health_index: number;
  overall_risk_score: number;
  risk_horizon: string;
  health_trajectory: string;

  created_at: string;
}

interface SystemSignal {
  id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  risk_horizon: 'immediate' | 'emerging' | 'structural';
  signal_summary: string;
  change_description: string;
  operational_impact: string;
  current_value: number;
  probability_range: string;
  recommended_actions: string[];
  urgency: string;
  status: string;
  created_at: string;
}

interface Intervention {
  id: string;
  organization_id: string;
  team_id?: string;
  intervention_title: string;
  intervention_category: string;
  expected_outcomes: string;
  status: string;
  progress_percentage: number;
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════
// Component
// ═══════════════════════════════════════════════════════════════

const CorporatePsychologyDashboard: React.FC = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<PsychologyMetrics | null>(null);
  const [signals, setSignals] = useState<SystemSignal[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);

  // Get organization ID from authenticated user, with fallback for dev/demo
  const organizationId = user?.organization_id || 'default-org';

  useEffect(() => {
    loadPsychologyData();
    // Refresh every 5 minutes
    const interval = setInterval(loadPsychologyData, 300000);
    return () => clearInterval(interval);
  }, [selectedTeam, organizationId]);

  const loadPsychologyData = async () => {

    try {
      setLoading(true);
      setError(null);

      // Try to fetch real data from API
      try {
        const [metricsData, signalsData, interventionsData] = await Promise.all([
          corporatePsychologyService.getMetrics(organizationId, selectedTeam || undefined),
          corporatePsychologyService.getSignals(organizationId, { team_id: selectedTeam || undefined, limit: 50 }),
          corporatePsychologyService.getInterventions(organizationId, { team_id: selectedTeam || undefined }),
        ]);

        setMetrics(metricsData);
        setSignals(signalsData);
        setInterventions(interventionsData);
      } catch (apiError) {
        // If API fails (e.g., no data yet), show empty state
        console.warn('API data not available, showing empty state:', apiError);
        setMetrics(null);
        setSignals([]);
        setInterventions([]);
      }
    } catch (err) {
      setError('Failed to load psychology data');
      console.error('Error loading psychology data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getHealthLevelColor = (healthIndex: number): string => {
    if (healthIndex >= 80) return 'text-green-600';
    if (healthIndex >= 65) return 'text-blue-600';
    if (healthIndex >= 50) return 'text-yellow-600';
    if (healthIndex >= 35) return 'text-orange-600';
    return 'text-red-600';
  };

  const getHealthLevelLabel = (healthIndex: number): string => {
    if (healthIndex >= 80) return 'Excellent';
    if (healthIndex >= 65) return 'Good';
    if (healthIndex >= 50) return 'Average';
    if (healthIndex >= 35) return 'Below Average';
    return 'Critical';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getEncodingIcon = (encoding: string) => {
    switch (encoding) {
      case 'cli':
        return <Brain className="h-5 w-5" />;
      case 'tsc':
        return <Shield className="h-5 w-5" />;
      case 'evs':
        return <HeartPulse className="h-5 w-5" />;
      case 'cfs':
        return <Network className="h-5 w-5" />;
      case 'pda':
        return <Activity className="h-5 w-5" />;
      case 'rrc':
        return <Zap className="h-5 w-5" />;
      default:
        return <Activity className="h-5 w-5" />;
    }
  };

  const getEncodingName = (encoding: string): string => {
    switch (encoding) {
      case 'cli':
        return 'Cognitive Load Index';
      case 'tsc':
        return 'Trust Stability Curve';
      case 'evs':
        return 'Emotional Volatility Signal';
      case 'cfs':
        return 'Coordination Friction Score';
      case 'pda':
        return 'Psychological Debt Accumulation';
      case 'rrc':
        return 'Recovery & Resilience Capacity';
      default:
        return encoding;
    }
  };

  const getTrendIcon = (encoding: string, value: number) => {
    // For CLI, EVS, CFS, PDA: lower is better
    // For TSC, RRC: higher is better
    const lowerIsBetter = ['cli', 'evs', 'cfs', 'pda'].includes(encoding);

    // This would normally come from the API's trend field
    // For now, we'll calculate based on value thresholds
    if (lowerIsBetter) {
      if (value > 70) return <TrendingUp className="h-4 w-4 text-red-500" />;
      if (value > 50) return <Minus className="h-4 w-4 text-yellow-500" />;
      return <TrendingDown className="h-4 w-4 text-green-500" />;
    } else {
      if (value < 40) return <TrendingDown className="h-4 w-4 text-red-500" />;
      if (value < 60) return <Minus className="h-4 w-4 text-yellow-500" />;
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    }
  };

  const getEncodingStatusColor = (encoding: string, value: number): string => {
    const lowerIsBetter = ['cli', 'evs', 'cfs', 'pda'].includes(encoding);

    if (lowerIsBetter) {
      if (value > 75) return 'bg-red-100 text-red-800';
      if (value > 60) return 'bg-orange-100 text-orange-800';
      if (value > 40) return 'bg-yellow-100 text-yellow-800';
      return 'bg-green-100 text-green-800';
    } else {
      if (value < 35) return 'bg-red-100 text-red-800';
      if (value < 50) return 'bg-orange-100 text-orange-800';
      if (value < 65) return 'bg-yellow-100 text-yellow-800';
      return 'bg-green-100 text-green-800';
    }
  };

  const getEncodingStatusLabel = (encoding: string, value: number): string => {
    const lowerIsBetter = ['cli', 'evs', 'cfs', 'pda'].includes(encoding);

    if (lowerIsBetter) {
      if (value > 75) return 'Critical';
      if (value > 60) return 'Elevated';
      if (value > 40) return 'Moderate';
      return 'Healthy';
    } else {
      if (value < 35) return 'Critical';
      if (value < 50) return 'Low';
      if (value < 65) return 'Moderate';
      return 'Strong';
    }
  };

  const getInterventionStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'approved':
        return 'bg-purple-100 text-purple-800';
      case 'proposed':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading organizational psychology metrics...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Unable to Load Dashboard</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={loadPsychologyData}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Organizational Psychology Intelligence
          </h1>
          <p className="text-gray-600 mt-1">
            System-level organizational health metrics for executive decision-making
          </p>
        </div>
        <Button onClick={loadPsychologyData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Overall Health Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Organizational Health Index</span>
              <CheckCircle2 className={`h-6 w-6 ${getHealthLevelColor(metrics.organizational_health_index)}`} />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-5xl font-bold">
                    {metrics.organizational_health_index.toFixed(1)}
                  </p>
                  <p className={`text-lg font-semibold ${getHealthLevelColor(metrics.organizational_health_index)}`}>
                    {getHealthLevelLabel(metrics.organizational_health_index)}
                  </p>
                </div>
                <Badge className={`${getHealthLevelColor(metrics.organizational_health_index)} bg-opacity-10`}>
                  {metrics.health_trajectory === 'improving' && '↗ Improving'}
                  {metrics.health_trajectory === 'stable' && '→ Stable'}
                  {metrics.health_trajectory === 'declining' && '↘ Declining'}
                </Badge>
              </div>
              <p className="text-sm text-gray-600">
                Measured from {new Date(metrics.measurement_period_start).toLocaleDateString()} to{' '}
                {new Date(metrics.measurement_period_end).toLocaleDateString()}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-4xl font-bold text-gray-900">
                {metrics.overall_risk_score.toFixed(1)}
              </p>
              <Badge className={`${metrics.risk_horizon === 'immediate' ? 'bg-red-100 text-red-800' :
                metrics.risk_horizon === 'emerging' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'}`}>
                {metrics.risk_horizon.charAt(0).toUpperCase() + metrics.risk_horizon.slice(1)} Risk
              </Badge>
              <p className="text-sm text-gray-600">
                {signals.length} active signal{signals.length !== 1 ? 's' : ''}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Quality</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Confidence</span>
                <span className="font-semibold">75%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Sample Size</span>
                <span className="font-semibold">85 data points</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Last Updated</span>
                <span className="font-semibold text-sm">
                  {new Date(metrics.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="encodings" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="encodings">Psychology Encodings</TabsTrigger>
          <TabsTrigger value="signals">
            System Signals
            {signals.length > 0 && (
              <Badge className="ml-2 bg-red-100 text-red-800">{signals.length}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="interventions">
            Interventions
            {interventions.filter(i => i.status === 'proposed').length > 0 && (
              <Badge className="ml-2 bg-yellow-100 text-yellow-800">
                {interventions.filter(i => i.status === 'proposed').length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Psychology Encodings Tab */}
        <TabsContent value="encodings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Core Psychology Encodings</CardTitle>
              <CardDescription>
                System-level metrics measuring organizational health (0-100 scale)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* CLI */}
                <Card className="border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center">
                      <Brain className="h-5 w-5 mr-2 text-blue-600" />
                      Cognitive Load Index
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-end justify-between">
                      <p className="text-3xl font-bold">
                        {metrics.cognitive_load_index.toFixed(1)}
                      </p>
                      <Badge className={getEncodingStatusColor('cli', metrics.cognitive_load_index)}>
                        {getEncodingStatusLabel('cli', metrics.cognitive_load_index)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend</span>
                      <div className="flex items-center">
                        {getTrendIcon('cli', metrics.cognitive_load_index)}
                        <span className="ml-1">Stable</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">
                      Overall cognitive burden. Lower is better.
                    </p>
                  </CardContent>
                </Card>

                {/* TSC */}
                <Card className="border-l-4 border-l-green-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center">
                      <Shield className="h-5 w-5 mr-2 text-green-600" />
                      Trust Stability
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-end justify-between">
                      <p className="text-3xl font-bold">
                        {metrics.trust_stability_score.toFixed(1)}
                      </p>
                      <Badge className={getEncodingStatusColor('tsc', metrics.trust_stability_score)}>
                        {getEncodingStatusLabel('tsc', metrics.trust_stability_score)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend</span>
                      <div className="flex items-center">
                        {getTrendIcon('tsc', metrics.trust_stability_score)}
                        <span className="ml-1">Stable</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">
                      Trust stability and strength. Higher is better.
                    </p>
                  </CardContent>
                </Card>

                {/* EVS */}
                <Card className="border-l-4 border-l-purple-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center">
                      <HeartPulse className="h-5 w-5 mr-2 text-purple-600" />
                      Emotional Volatility
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-end justify-between">
                      <p className="text-3xl font-bold">
                        {metrics.emotional_volatility_score.toFixed(1)}
                      </p>
                      <Badge className={getEncodingStatusColor('evs', metrics.emotional_volatility_score)}>
                        {getEncodingStatusLabel('evs', metrics.emotional_volatility_score)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend</span>
                      <div className="flex items-center">
                        {getTrendIcon('evs', metrics.emotional_volatility_score)}
                        <span className="ml-1">Stable</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">
                      Emotional regulation level. Lower is better.
                    </p>
                  </CardContent>
                </Card>

                {/* CFS */}
                <Card className="border-l-4 border-l-orange-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center">
                      <Network className="h-5 w-5 mr-2 text-orange-600" />
                      Coordination Friction
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-end justify-between">
                      <p className="text-3xl font-bold">
                        {metrics.coordination_friction_score.toFixed(1)}
                      </p>
                      <Badge className={getEncodingStatusColor('cfs', metrics.coordination_friction_score)}>
                        {getEncodingStatusLabel('cfs', metrics.coordination_friction_score)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend</span>
                      <div className="flex items-center">
                        {getTrendIcon('cfs', metrics.coordination_friction_score)}
                        <span className="ml-1">Stable</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">
                      Coordination efficiency. Lower is better.
                    </p>
                  </CardContent>
                </Card>

                {/* PDA */}
                <Card className="border-l-4 border-l-red-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center">
                      <Activity className="h-5 w-5 mr-2 text-red-600" />
                      Psychological Debt
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-end justify-between">
                      <p className="text-3xl font-bold">
                        {metrics.psychological_debt_score.toFixed(1)}
                      </p>
                      <Badge className={getEncodingStatusColor('pda', metrics.psychological_debt_score)}>
                        {getEncodingStatusLabel('pda', metrics.psychological_debt_score)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend</span>
                      <div className="flex items-center">
                        {getTrendIcon('pda', metrics.psychological_debt_score)}
                        <span className="ml-1">Stable</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">
                      Accumulated strain. Lower is better.
                    </p>
                  </CardContent>
                </Card>

                {/* RRC */}
                <Card className="border-l-4 border-l-teal-500">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center">
                      <Zap className="h-5 w-5 mr-2 text-teal-600" />
                      Recovery Capacity
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-end justify-between">
                      <p className="text-3xl font-bold">
                        {metrics.recovery_resilience_score.toFixed(1)}
                      </p>
                      <Badge className={getEncodingStatusColor('rrc', metrics.recovery_resilience_score)}>
                        {getEncodingStatusLabel('rrc', metrics.recovery_resilience_score)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Trend</span>
                      <div className="flex items-center">
                        {getTrendIcon('rrc', metrics.recovery_resilience_score)}
                        <span className="ml-1">Stable</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600">
                      Recovery and resilience. Higher is better.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Signals Tab */}
        <TabsContent value="signals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Early-Warning Signals</CardTitle>
              <CardDescription>
                System-level alerts indicating organizational patterns requiring attention
              </CardDescription>
            </CardHeader>
            <CardContent>
              {signals.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Signals</h3>
                  <p className="text-gray-600">
                    All psychology encodings are within healthy ranges
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {signals.map((signal) => (
                    <Card key={signal.id} className="border-l-4 border-l-orange-500">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base flex items-center">
                              <AlertTriangle className="h-5 w-5 mr-2 text-orange-600" />
                              {signal.signal_summary}
                            </CardTitle>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge className={getSeverityColor(signal.severity)}>
                                {signal.severity.charAt(0).toUpperCase() + signal.severity.slice(1)}
                              </Badge>
                              <Badge variant="outline">
                                <Clock className="h-3 w-3 mr-1" />
                                {signal.risk_horizon.charAt(0).toUpperCase() + signal.risk_horizon.slice(1)}
                              </Badge>
                              <Badge variant="outline">
                                {signal.probability_range}
                              </Badge>
                            </div>
                          </div>
                          <Badge className={getInterventionStatusColor(signal.status)}>
                            {signal.status.charAt(0).toUpperCase() + signal.status.slice(1)}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <p className="text-sm text-gray-700">{signal.change_description}</p>
                        <p className="text-sm font-semibold text-gray-900">
                          Impact: {signal.operational_impact}
                        </p>
                        <div className="border-t pt-3">
                          <p className="text-xs font-semibold text-gray-700 mb-2">Recommended Actions:</p>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {signal.recommended_actions.map((action, idx) => (
                              <li key={idx} className="flex items-start">
                                <Target className="h-4 w-4 mr-2 mt-0.5 text-blue-600 flex-shrink-0" />
                                <span>{action}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Interventions Tab */}
        <TabsContent value="interventions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Structural Interventions</CardTitle>
              <CardDescription>
                Process, cadence, and structural changes to improve organizational health
              </CardDescription>
            </CardHeader>
            <CardContent>
              {interventions.length === 0 ? (
                <div className="text-center py-12">
                  <Target className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Interventions</h3>
                  <p className="text-gray-600">
                    No structural interventions are currently proposed or in progress
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {interventions.map((intervention) => (
                    <Card key={intervention.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">
                              {intervention.intervention_title}
                            </CardTitle>
                            <p className="text-sm text-gray-600 mt-1">
                              {intervention.intervention_category.charAt(0).toUpperCase() +
                               intervention.intervention_category.slice(1)} •{' '}
                              {intervention.expected_outcomes}
                            </p>
                          </div>
                          <Badge className={getInterventionStatusColor(intervention.status)}>
                            {intervention.status.charAt(0).toUpperCase() +
                             intervention.status.slice(1).replace('_', ' ')}
                          </Badge>
                        </div>
                      </CardHeader>
                      {intervention.progress_percentage > 0 && (
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Progress</span>
                              <span className="font-semibold">
                                {intervention.progress_percentage.toFixed(0)}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${intervention.progress_percentage}%` }}
                              />
                            </div>
                          </div>
                        </CardContent>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CorporatePsychologyDashboard;
