/**
 * Health Dashboard Component
 *
 * Displays personal health metrics, risk indicators, and interventions
 *
 * Features:
 * - Real-time health risk display
 * - Cardiovascular risk gauge
 * - Stress level indicator
 * - Active interventions list
 * - Biometric data visualization
 * - Wellness recommendations
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
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
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
  ExternalLink
} from 'lucide-react';

// Types
interface HealthRiskData {
  stress_level: 'normal' | 'elevated' | 'high' | 'critical';
  burnout_stage: string;
  cardiovascular_risk_score: number;
  mental_health_risk: number;
  work_life_imbalance: number;
  sleep_disruption_score: number;
  social_isolation_score: number;
  urgent_intervention_needed: boolean;
  recommend_medical_evaluation: boolean;
  recommend_immediate_break: boolean;
  recommend_workload_reduction: boolean;
  primary_risk_factors: string[];
  warning_signs: string[];
  protective_factors: string[];
  recommended_actions: string[];
  data_sources: string[];
  confidence_level: number;
}

interface Intervention {
  intervention_type: string;
  urgency: string;
  title: string;
  message: string;
  actions_required: string[];
  resources: Array<{
    title: string;
    url: string;
    type: string;
  }>;
  follow_up_required: boolean;
  follow_up_days: number;
}

interface BiometricData {
  resting_heart_rate?: number;
  heart_rate_variability?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  sleep_hours?: number;
  sleep_quality_score?: number;
  steps_count?: number;
}

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

const getUrgencyIcon = (urgency: string) => {
  switch (urgency) {
    case 'critical': return <AlertTriangle className="h-5 w-5 text-red-600" />;
    case 'high': return <Activity className="h-5 w-5 text-orange-600" />;
    case 'medium': return <Clock className="h-5 w-5 text-yellow-600" />;
    default: return <CheckCircle className="h-5 w-5 text-blue-600" />;
  }
};

export const HealthDashboard: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthRiskData | null>(null);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  // Fetch health analysis
  const analyzeHealth = async () => {
    setAnalyzing(true);
    try {
      const response = await fetch('/api/v1/health-monitoring/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          time_window_days: 30,
          include_biometric: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setHealthData(data);
      }
    } catch (error) {
      console.error('Failed to analyze health:', error);
    } finally {
      setAnalyzing(false);
      setLoading(false);
    }
  };

  // Fetch interventions
  const fetchInterventions = async () => {
    try {
      const response = await fetch('/api/v1/health-monitoring/interventions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          health_risks: healthData,
          work_patterns: {},
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setInterventions(data);
      }
    } catch (error) {
      console.error('Failed to fetch interventions:', error);
    }
  };

  useEffect(() => {
    analyzeHealth();
  }, []);

  useEffect(() => {
    if (healthData && healthData.urgent_intervention_needed) {
      fetchInterventions();
    }
  }, [healthData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-muted-foreground">
          Analyzing your health data...
        </div>
      </div>
    );
  }

  if (!healthData) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Unable to Load Health Data</AlertTitle>
        <AlertDescription>
          Please ensure you have connected your email and/or wearable devices.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Your Health Dashboard</h2>
          <p className="text-muted-foreground">
            Last analyzed: {new Date().toLocaleDateString()}
          </p>
        </div>
        <Button
          onClick={analyzeHealth}
          disabled={analyzing}
          className="bg-green-600 hover:bg-green-700"
        >
          <Activity className="mr-2 h-4 w-4" />
          {analyzing ? 'Analyzing...' : 'Refresh Analysis'}
        </Button>
      </div>

      {/* Critical Alert */}
      {healthData.urgent_intervention_needed && (
        <Alert className="border-red-500 bg-red-50 dark:bg-red-950">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-900 dark:text-red-100">
            ⚠️ Immediate Attention Required
          </AlertTitle>
          <AlertDescription className="text-red-800 dark:text-red-200">
            {healthData.recommend_medical_evaluation
              ? 'Medical evaluation is recommended. Please review the interventions below.'
              : 'Your stress levels are critically high. Please take immediate action.'}
          </AlertDescription>
        </Alert>
      )}

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

      {/* Active Interventions */}
      {interventions.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-bold">Active Interventions</h3>
          {interventions.map((intervention, index) => (
            <Card key={index} className="border-l-4 border-l-orange-500">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getUrgencyIcon(intervention.urgency)}
                    <div>
                      <CardTitle className="text-lg">{intervention.title}</CardTitle>
                      <Badge variant="outline" className="mt-1">
                        {intervention.urgency.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  {intervention.message}
                </p>

                {/* Actions Required */}
                {intervention.actions_required.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold mb-2">Actions Required:</h4>
                    <ol className="list-decimal list-inside space-y-1 text-sm">
                      {intervention.actions_required.map((action, i) => (
                        <li key={i}>{action}</li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Resources */}
                {intervention.resources.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Resources:</h4>
                    <div className="flex flex-wrap gap-2">
                      {intervention.resources.map((resource, i) => (
                        <Button
                          key={i}
                          variant="outline"
                          size="sm"
                          asChild
                          className="text-xs"
                        >
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center"
                          >
                            {resource.type === 'crisis' && <Phone className="mr-1 h-3 w-3" />}
                            {resource.title}
                            <ExternalLink className="ml-1 h-3 w-3" />
                          </a>
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Follow-up Info */}
                {intervention.follow_up_required && (
                  <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
                    <Calendar className="inline mr-1 h-3 w-3" />
                    Follow-up in {intervention.follow_up_days} day(s)
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Recommendations */}
      {healthData.recommended_actions && healthData.recommended_actions.length > 0 && (
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

      {/* Sleep Display */}
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
    </div>
  );
};

export default HealthDashboard;
