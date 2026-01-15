/**
 * Enhanced Health Dashboard Component
 *
 * Displays personal health metrics, risk indicators, and interventions
 * with real-time monitoring and improved service integration.
 *
 * Features:
 * - Real-time health risk display
 * - Cardiovascular risk gauge
 * - Stress level indicator
 * - Active interventions list
 * - Biometric data visualization
 * - Wellness recommendations
 * - Real-time alerts integration
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
import Progress from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Heart,
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  Moon,
  Zap,
  Shield,
  Calendar,
  Phone,
  ExternalLink,
  RefreshCw,
  Upload,
} from 'lucide-react';
import HealthMonitoringService from '@/services/healthMonitoringService';
import InterventionService from '@/services/interventionService';
import { HealthAlertContainer } from './HealthAlertBanner';
import { useRealTimeHealthMonitoring } from '@/hooks/useRealTimeHealthMonitoring';
import type {
  HealthRiskData,
  Intervention,
  BiometricData,
} from '@/types/healthMonitoring';

export const EnhancedHealthDashboard: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthRiskData | null>(null);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Real-time monitoring
  const {
    isConnected,
    latestUpdate,
    alerts,
    acknowledgeAlert,
    clearAlerts,
  } = useRealTimeHealthMonitoring({
    enabled: true,
    onHealthAlert: (alert) => {
      console.log('Health alert received:', alert);
    },
    onHealthUpdate: (update) => {
      console.log('Health update received:', update);
    },
  });

  // Fetch health analysis
  const analyzeHealth = async (timeWindowDays: number = 30) => {
    setAnalyzing(true);
    try {
      const data = await HealthMonitoringService.analyzeHealthRisks({
        time_window_days: timeWindowDays,
        include_biometric: false,
      });
      setHealthData(data);

      // Auto-create interventions if urgent
      if (data.urgent_intervention_needed) {
        await fetchInterventions(data);
      }
    } catch (error) {
      console.error('Failed to analyze health:', error);
    } finally {
      setAnalyzing(false);
      setLoading(false);
    }
  };

  // Fetch interventions
  const fetchInterventions = async (healthRisks?: HealthRiskData) => {
    try {
      const risks = healthRisks || healthData;
      if (!risks) return;

      const interventionList = await InterventionService.createInterventionPlan({
        health_risks: risks,
        work_patterns: {},
      });
      setInterventions(interventionList);
    } catch (error) {
      console.error('Failed to fetch interventions:', error);
    }
  };

  // Initial load
  useEffect(() => {
    analyzeHealth();
  }, []);

  // Update health data when real-time updates arrive
  useEffect(() => {
    if (latestUpdate?.stress_level) {
      setHealthData(prev => prev ? {
        ...prev,
        stress_level: latestUpdate.stress_level!,
      } : null);
    }
  }, [latestUpdate]);

  // Utility functions
  const getStressColor = (level: string) => {
    switch (level) {
      case 'normal': return 'bg-green-500';
      case 'elevated': return 'bg-yellow-500';
      case 'high': return 'bg-orange-500';
      case 'critical': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 0.8) return 'text-red-600';
    if (score >= 0.6) return 'text-orange-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse bg-gray-200 h-32 w-full rounded"></div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="animate-pulse bg-gray-200 h-32 rounded"></div>
          <div className="animate-pulse bg-gray-200 h-32 rounded"></div>
          <div className="animate-pulse bg-gray-200 h-32 rounded"></div>
          <div className="animate-pulse bg-gray-200 h-32 rounded"></div>
        </div>
      </div>
    );
  }

  if (!healthData) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <AlertTriangle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Unable to Load Health Data</h3>
            <p className="text-muted-foreground mb-4">
              Please ensure you have connected your email and/or wearable devices.
            </p>
            <Button onClick={() => analyzeHealth()}>Try Again</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-3xl font-bold">Your Health Dashboard</h2>
            {isConnected && (
              <Badge variant="outline" className="text-xs">
                <Activity className="mr-1 h-3 w-3" />
                Live
              </Badge>
            )}
          </div>
          <p className="text-muted-foreground">
            Last analyzed: {new Date(healthData.analysis_date).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => analyzeHealth(7)}
            disabled={analyzing}
            variant="outline"
            size="sm"
          >
            <Clock className="mr-2 h-4 w-4" />
            Quick Check
          </Button>
          <Button
            onClick={() => analyzeHealth(30)}
            disabled={analyzing}
            className="bg-green-600 hover:bg-green-700"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Analyzing...' : 'Refresh Analysis'}
          </Button>
        </div>
      </div>

      {/* Critical Alert */}
      {healthData.urgent_intervention_needed && (
        <Card className="border-red-500 bg-red-50 dark:bg-red-950">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <div className="flex-1">
                <h3 className="text-red-900 dark:text-red-100 font-semibold">
                  ⚠️ Immediate Attention Required
                </h3>
                <p className="text-red-800 dark:text-red-200 text-sm">
                  {healthData.recommend_medical_evaluation
                    ? 'Medical evaluation is recommended. Please review the interventions below.'
                    : 'Your stress levels are critically high. Please take immediate action.'}
                </p>
              </div>
              <Button
                variant="outline"
                className="text-red-600 border-red-300"
                onClick={() => setActiveTab('interventions')}
              >
                View Interventions
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Real-time Alerts */}
      {alerts.length > 0 && (
        <Card className="border-blue-500">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center">
              <Activity className="mr-2 h-5 w-5" />
              Recent Alerts ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="flex items-start gap-2 p-2 rounded bg-muted">
                  <AlertTriangle className={`h-4 w-4 mt-0.5 ${
                    alert.severity === 'critical' ? 'text-red-600' :
                    alert.severity === 'high' ? 'text-orange-600' :
                    'text-yellow-600'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    Acknowledge
                  </Button>
                </div>
              ))}
            </div>
            {alerts.length > 3 && (
              <Button variant="link" className="mt-2" onClick={clearAlerts}>
                Clear all alerts
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="details">Risk Details</TabsTrigger>
          <TabsTrigger value="interventions">
            Interventions
            {interventions.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {interventions.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="biometric">Biometric Data</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          {/* Main Risk Scores */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Stress Level */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Stress Level</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <Badge
                    className={`${getStressColor(healthData.stress_level)} text-white`}
                  >
                    {healthData.stress_level.toUpperCase()}
                  </Badge>
                  <Heart className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>

            {/* Cardiovascular Risk */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Cardiovascular Risk</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-2xl font-bold">
                    <span className={getRiskColor(healthData.cardiovascular_risk_score)}>
                      {(healthData.cardiovascular_risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={healthData.cardiovascular_risk_score * 100} />
                </div>
              </CardContent>
            </Card>

            {/* Mental Health Risk */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Mental Health Risk</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-2xl font-bold">
                    <span className={getRiskColor(healthData.mental_health_risk)}>
                      {(healthData.mental_health_risk * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={healthData.mental_health_risk * 100} />
                </div>
              </CardContent>
            </Card>

            {/* Work-Life Balance */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Work-Life Balance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-2xl font-bold">
                    <span className={getRiskColor(1 - healthData.work_life_imbalance)}>
                      {((1 - healthData.work_life_imbalance) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={(1 - healthData.work_life_imbalance) * 100} />
                  <p className="text-xs text-muted-foreground">
                    {healthData.work_life_imbalance > 0.6 ? 'Needs attention' : 'Good balance'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          {healthData.recommended_actions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommended Actions</CardTitle>
                <CardDescription>
                  Personalized recommendations based on your health data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {healthData.recommended_actions.map((action, index) => (
                    <li key={index} className="flex items-start">
                      <Zap className="mr-2 h-4 w-4 text-blue-500 mt-1 flex-shrink-0" />
                      <span className="text-sm">{action}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Risk Details Tab */}
        <TabsContent value="details" className="space-y-4">
          {/* Risk Factors */}
          {healthData.primary_risk_factors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Risk Factors Detected</CardTitle>
                <CardDescription>
                  Based on analysis of {healthData.data_sources.length} data sources
                  (Confidence: {(healthData.confidence_level * 100).toFixed(0)}%)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {healthData.primary_risk_factors.map((factor, index) => (
                    <li key={index} className="flex items-start">
                      <AlertTriangle className="mr-2 h-4 w-4 text-orange-500 mt-1 flex-shrink-0" />
                      <span className="text-sm">{factor}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Warning Signs */}
          {healthData.warning_signs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Warning Signs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 md:grid-cols-2">
                  {healthData.warning_signs.map((sign, index) => (
                    <div key={index} className="flex items-center text-sm">
                      <TrendingUp className="mr-2 h-4 w-4 text-yellow-500" />
                      {sign}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Protective Factors */}
          {healthData.protective_factors.length > 0 && (
            <Card className="border-green-500">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="mr-2 h-5 w-5 text-green-600" />
                  Protective Factors
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {healthData.protective_factors.map((factor, index) => (
                    <li key={index} className="flex items-center text-sm">
                      <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Sleep Quality */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Moon className="mr-2 h-5 w-5 text-indigo-500" />
                Sleep Quality
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Sleep Disruption Score</span>
                  <span className={`text-lg font-bold ${getRiskColor(healthData.sleep_disruption_score)}`}>
                    {(healthData.sleep_disruption_score * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress value={healthData.sleep_disruption_score * 100} />
                {healthData.sleep_disruption_score > 0.6 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    💡 Consider the sleep hygiene program in your interventions
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Interventions Tab */}
        <TabsContent value="interventions" className="space-y-4">
          {interventions.length > 0 ? (
            <HealthAlertContainer
              interventions={interventions}
              onDismiss={(interventionId) => {
                setInterventions(prev => prev.filter(i => i.intervention_id !== interventionId));
              }}
            />
          ) : (
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Interventions</h3>
                  <p className="text-muted-foreground">
                    Your health metrics are within normal ranges. Continue maintaining your healthy habits!
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Biometric Data Tab */}
        <TabsContent value="biometric" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="mr-2 h-5 w-5" />
                Submit Biometric Data
              </CardTitle>
              <CardDescription>
                Upload data from your wearable device or enter manually
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Biometric data submission form will be available soon.
                This will include support for Apple Health, Google Fit, and other wearable platforms.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedHealthDashboard;
