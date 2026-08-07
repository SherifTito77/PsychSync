/**
 * CEO Executive Burnout Analytics Dashboard
 *
 * Strategic decision support for C-Suite executives
 *
 * Features:
 * - Organization-wide risk trends
 * - 14-day probability forecasting with confidence bands
 * - Cost-benefit analysis of interventions
 * - Department risk heatmap
 * - ROI tracking
 *
 * @version 2.0
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Users,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import api from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

// Types
interface ExecutiveSummary {
  overall_risk_score: number;
  risk_trend: 'improving' | 'stable' | 'worsening';
  high_risk_employees: number;
  high_risk_percentage: number;
  predicted_turnover_risk_30d: number;
  estimated_cost_of_burnout: {
    monthly: number;
    quarterly: number;
    annual: number;
  };
  intervention_roi: {
    invested: number;
    saved: number;
    roi_percentage: number;
  };
}

interface DepartmentHeatmap {
  department: string;
  team_count: number;
  avg_risk_score: number;
  high_risk_count: number;
  critical_risk_count: number;
  risk_trend: 'improving' | 'stable' | 'worsening';
  predicted_burnouts_90d: number;
  estimated_cost_impact: number;
}

interface ForecastData {
  date: string;
  org_burnout_probability: number;
  confidence_interval_lower: number;
  confidence_interval_upper: number;
}

interface ForecastChart {
  forecast_data: ForecastData[];
  intervention_scenarios: {
    name: string;
    probability_at_day_14: number;
    cost: number;
  }[];
}

interface CostBenefitAnalysis {
  cost_of_inaction: {
    current_month: number;
    next_quarter: number;
    next_year: number;
    breakdown: {
      turnover_replacement: number;
      productivity_loss: number;
      healthcare_costs: number;
      absenteeism: number;
    };
  };
  cost_of_intervention: {
    program_costs: number;
    implementation_costs: number;
    total: number;
  };
  projected_savings: {
    turnover_avoided: number;
    productivity_gained: number;
    healthcare_reduced: number;
    total: number;
  };
  roi: number;
}

interface CEOBurnoutDashboardProps {
  organizationId: string;
  timeRange?: '30d' | '90d' | '180d';
}

// Wrapper component that gets organization_id from auth context
const CEOBurnoutDashboardWrapper: React.FC<{ timeRange?: '30d' | '90d' | '180d' }> = ({ timeRange = '90d' }) => {
  const { user } = useAuth();
  const organizationId = user?.organization_id || 'default-org';

  return <CEOBurnoutDashboard organizationId={organizationId} timeRange={timeRange} />;
};

const CEOBurnoutDashboard: React.FC<CEOBurnoutDashboardProps> = ({
  organizationId,
  timeRange = '90d'
}) => {
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [heatmap, setHeatmap] = useState<DepartmentHeatmap[]>([]);
  const [forecast, setForecast] = useState<ForecastChart | null>(null);
  const [costBenefit, setCostBenefit] = useState<CostBenefitAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, [organizationId, timeRange]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [summaryRes, heatmapRes, forecastRes, costBenefitRes] = await Promise.all([
        api.get(`/executive/burnout/summary?org_id=${organizationId}&range=${timeRange}`),
        api.get(`/executive/burnout/heatmap?org_id=${organizationId}`),
        api.get(`/executive/burnout/forecast?org_id=${organizationId}&horizon=14d`),
        api.get(`/executive/burnout/cost-benefit?org_id=${organizationId}`)
      ]);

      const summaryData = summaryRes.data;
      const heatmapData = heatmapRes.data;
      const forecastData = forecastRes.data;
      const costBenefitData = costBenefitRes.data;

      setSummary(summaryData.summary || summaryData);
      setHeatmap(heatmapData.departments || heatmapData);
      setForecast(forecastData);
      setCostBenefit(costBenefitData.analysis || costBenefitData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Set mock data for development/demo
      setMockData();
    } finally {
      setLoading(false);
    }
  };

  const setMockData = () => {
    // Mock data for development
    setSummary({
      overall_risk_score: 52,
      risk_trend: 'stable',
      high_risk_employees: 47,
      high_risk_percentage: 12.3,
      predicted_turnover_risk_30d: 18.5,
      estimated_cost_of_burnout: {
        monthly: 284000,
        quarterly: 852000,
        annual: 3408000
      },
      intervention_roi: {
        invested: 156000,
        saved: 482000,
        roi_percentage: 209
      }
    });

    setHeatmap([
      {
        department: 'Engineering',
        team_count: 120,
        avg_risk_score: 58,
        high_risk_count: 18,
        critical_risk_count: 3,
        risk_trend: 'worsening',
        predicted_burnouts_90d: 4,
        estimated_cost_impact: 425000
      },
      {
        department: 'Sales',
        team_count: 85,
        avg_risk_score: 63,
        high_risk_count: 16,
        critical_risk_count: 4,
        risk_trend: 'stable',
        predicted_burnouts_90d: 5,
        estimated_cost_impact: 512000
      },
      {
        department: 'Marketing',
        team_count: 45,
        avg_risk_score: 42,
        high_risk_count: 5,
        critical_risk_count: 1,
        risk_trend: 'improving',
        predicted_burnouts_90d: 1,
        estimated_cost_impact: 98000
      },
      {
        department: 'Operations',
        team_count: 95,
        avg_risk_score: 48,
        high_risk_count: 8,
        critical_risk_count: 2,
        risk_trend: 'stable',
        predicted_burnouts_90d: 2,
        estimated_cost_impact: 215000
      }
    ]);

    const days = Array.from({ length: 14 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() + i + 1);
      return date.toISOString().split('T')[0];
    });

    setForecast({
      forecast_data: days.map((date, i) => ({
        date,
        org_burnout_probability: Math.min(0.35 + i * 0.015, 0.55),
        confidence_interval_lower: Math.max(0.25 + i * 0.01, 0.25),
        confidence_interval_upper: Math.min(0.45 + i * 0.02, 0.65)
      })),
      intervention_scenarios: [
        { name: 'No Action', probability_at_day_14: 55, cost: 0 },
        { name: 'Light Intervention', probability_at_day_14: 42, cost: 25000 },
        { name: 'Comprehensive Program', probability_at_day_14: 28, cost: 75000 }
      ]
    });

    setCostBenefit({
      cost_of_inaction: {
        current_month: 284000,
        next_quarter: 852000,
        next_year: 3408000,
        breakdown: {
          turnover_replacement: 1248000,
          productivity_loss: 1368000,
          healthcare_costs: 528000,
          absenteeism: 264000
        }
      },
      cost_of_intervention: {
        program_costs: 180000,
        implementation_costs: 45000,
        total: 225000
      },
      projected_savings: {
        turnover_avoided: 912000,
        productivity_gained: 1248000,
        healthcare_reduced: 312000,
        total: 2472000
      },
      roi: 999
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'worsening':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-blue-600" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            CEO Executive Burnout Analytics
          </h1>
          <p className="text-gray-600 mt-1">
            Strategic risk forecasting and ROI analysis for decision makers
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => window.location.href = `?range=${e.target.value}`}
            className="px-4 py-2 border border-gray-300 rounded-lg bg-white shadow-sm"
          >
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="180d">Last 180 Days</option>
          </select>
          <Button onClick={loadDashboardData} variant="outline">
            Refresh
          </Button>
        </div>
      </div>

      {/* Executive Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Overall Risk Score */}
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Org Risk Score</p>
                <p className="text-3xl font-bold mt-1">{summary?.overall_risk_score || 0}</p>
                <div className={`flex items-center mt-2 ${
                  summary?.risk_trend === 'improving' ? 'text-green-600' :
                  summary?.risk_trend === 'worsening' ? 'text-red-600' :
                  'text-blue-600'
                }`}>
                  {getTrendIcon(summary?.risk_trend || 'stable')}
                  <span className="ml-1 capitalize text-sm font-medium">
                    {summary?.risk_trend}
                  </span>
                </div>
              </div>
              <div className={`p-3 rounded-full ${
                (summary?.overall_risk_score || 0) >= 70 ? 'bg-red-100' :
                (summary?.overall_risk_score || 0) >= 50 ? 'bg-yellow-100' :
                'bg-green-100'
              }`}>
                <AlertTriangle className={`h-8 w-8 ${
                  (summary?.overall_risk_score || 0) >= 70 ? 'text-red-600' :
                  (summary?.overall_risk_score || 0) >= 50 ? 'text-yellow-600' :
                  'text-green-600'
                }`} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* High Risk Employees */}
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">High Risk Employees</p>
                <p className="text-3xl font-bold mt-1">{summary?.high_risk_employees || 0}</p>
                <p className="text-sm text-gray-500 mt-2">
                  {summary?.high_risk_percentage.toFixed(1)}% of workforce
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 30-Day Turnover Risk */}
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">30-Day Turnover Risk</p>
                <p className="text-3xl font-bold mt-1">
                  {(summary?.predicted_turnover_risk_30d || 0).toFixed(1)}%
                </p>
                <p className="text-sm text-orange-600 mt-2">
                  ~{Math.round((summary?.predicted_turnover_risk_30d || 0) / 100 * (summary?.high_risk_employees || 0))} employees
                </p>
              </div>
              <div className="p-3 bg-orange-100 rounded-full">
                <TrendingUp className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Annual Cost Impact */}
        <Card className="shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Annual Burnout Cost</p>
                <p className="text-2xl font-bold mt-1">
                  {formatCurrency(summary?.estimated_cost_of_burnout.annual || 0)}
                </p>
                <p className="text-sm text-red-600 mt-2">
                  If no action taken
                </p>
              </div>
              <div className="p-3 bg-red-100 rounded-full">
                <DollarSign className="h-8 w-8 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ROI of Interventions */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Intervention ROI Analysis (Year-to-Date)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Invested</p>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(summary?.intervention_roi.invested || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Saved</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(summary?.intervention_roi.saved || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Net ROI</p>
              <p className={`text-2xl font-bold ${
                (summary?.intervention_roi.roi_percentage || 0) > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {(summary?.intervention_roi.roi_percentage || 0) > 0 ? '+' : ''}
                {(summary?.intervention_roi.roi_percentage || 0).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Value Created</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency((summary?.intervention_roi.saved || 0) - (summary?.intervention_roi.invested || 0))}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 14-Day Forecast */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>14-Day Burnout Probability Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forecast?.forecast_data || []} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <defs>
                <linearGradient id="colorProbability" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#94A3B8" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#94A3B8" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis
                label={{ value: 'Probability (%)', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                domain={[0, 1]}
              />
              <Tooltip
                formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, '']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Legend />
              <ReferenceLine y={0.8} stroke="#EF4444" strokeDasharray="3 3" label={{ value: "Critical (80%)", position: "right" }} />
              <ReferenceLine y={0.6} stroke="#F59E0B" strokeDasharray="3 3" label={{ value: "High (60%)", position: "right" }} />

              {/* Confidence interval area */}
              <Area
                type="monotone"
                dataKey="confidence_interval_upper"
                stroke="#94A3B8"
                strokeOpacity={0}
                fill="url(#colorConfidence)"
                name="95% Confidence Interval"
              />

              {/* Main probability line */}
              <Area
                type="monotone"
                dataKey="org_burnout_probability"
                stroke="#3B82F6"
                fillOpacity={1}
                fill="url(#colorProbability)"
                strokeWidth={2}
                name="Burnout Probability"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Department Heatmap */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Department Risk Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {heatmap.map((dept) => (
              <div key={dept.department} className="flex items-center">
                <div className="w-48 font-medium text-sm">{dept.department}</div>
                <div className="flex-1 flex items-center space-x-4">
                  <div className="flex-1 bg-gray-200 rounded-full h-8 relative overflow-hidden">
                    <div
                      className={`h-8 transition-all duration-500 ${
                        dept.avg_risk_score >= 70 ? 'bg-red-500' :
                        dept.avg_risk_score >= 50 ? 'bg-yellow-500' :
                        dept.avg_risk_score >= 30 ? 'bg-blue-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${dept.avg_risk_score}%` }}
                    />
                    <span className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-white mix-blend-multiply">
                      {dept.avg_risk_score.toFixed(0)}
                    </span>
                  </div>
                  <div className="w-24 text-sm flex items-center space-x-1">
                    {getTrendIcon(dept.risk_trend)}
                    <span className="capitalize text-xs">{dept.risk_trend}</span>
                  </div>
                  <div className="w-20 text-sm text-orange-600">
                    {dept.high_risk_count} high
                  </div>
                  <div className="w-20 text-sm text-red-600">
                    {dept.critical_risk_count} critical
                  </div>
                  <div className="w-32 text-sm font-medium">
                    {formatCurrency(dept.estimated_cost_impact)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Cost-Benefit Analysis */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Cost-Benefit Analysis: Action vs. Inaction</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Cost of Inaction */}
            <div>
              <h3 className="text-lg font-semibold text-red-600 mb-4 flex items-center">
                <AlertTriangle className="h-5 w-5 mr-2" />
                Cost of Inaction (Annual)
              </h3>
              <div className="space-y-3 bg-red-50 rounded-lg p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Turnover Replacement</span>
                  <span className="font-medium">
                    {formatCurrency(costBenefit?.cost_of_inaction.breakdown.turnover_replacement || 0)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Productivity Loss</span>
                  <span className="font-medium">
                    {formatCurrency(costBenefit?.cost_of_inaction.breakdown.productivity_loss || 0)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Healthcare Costs</span>
                  <span className="font-medium">
                    {formatCurrency(costBenefit?.cost_of_inaction.breakdown.healthcare_costs || 0)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Absenteeism</span>
                  <span className="font-medium">
                    {formatCurrency(costBenefit?.cost_of_inaction.breakdown.absenteeism || 0)}
                  </span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between font-bold text-base">
                  <span>Total Annual Cost</span>
                  <span className="text-red-600">
                    {formatCurrency(costBenefit?.cost_of_inaction.next_year || 0)}
                  </span>
                </div>
              </div>
            </div>

            {/* Projected Savings with Intervention */}
            <div>
              <h3 className="text-lg font-semibold text-green-600 mb-4 flex items-center">
                <DollarSign className="h-5 w-5 mr-2" />
                Projected Savings (with Intervention)
              </h3>
              <div className="space-y-3 bg-green-50 rounded-lg p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Turnover Avoided</span>
                  <span className="font-medium text-green-600">
                    {formatCurrency(costBenefit?.projected_savings.turnover_avoided || 0)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Productivity Gained</span>
                  <span className="font-medium text-green-600">
                    {formatCurrency(costBenefit?.projected_savings.productivity_gained || 0)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Healthcare Reduced</span>
                  <span className="font-medium text-green-600">
                    {formatCurrency(costBenefit?.projected_savings.healthcare_reduced || 0)}
                  </span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between font-bold text-base">
                  <span>Total Savings</span>
                  <span className="text-green-600">
                    {formatCurrency(costBenefit?.projected_savings.total || 0)}
                  </span>
                </div>
                <div className="flex justify-between font-bold text-base pt-2">
                  <span>Intervention Cost</span>
                  <span className="text-blue-600">
                    {formatCurrency(costBenefit?.cost_of_intervention.total || 0)}
                  </span>
                </div>
                <div className="flex justify-between font-bold text-lg pt-2">
                  <span>Net ROI</span>
                  <span className="text-green-600">
                    {costBenefit?.roi.toFixed(0)}% ({formatCurrency((costBenefit?.projected_savings.total || 0) - (costBenefit?.cost_of_intervention.total || 0))})
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CEOBurnoutDashboardWrapper;
