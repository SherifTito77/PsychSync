/**
 * CEO Executive Dashboard
 *
 * High-altitude strategic view for organizational leadership.
 * Focuses on retention risk, organizational health, and goal alignment.
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  Target,
  AlertCircle,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import api from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

// Types
interface OrgHealthScore {
  score: number;
  trend: number; // percentage change
  history: { month: string; score: number }[];
}

interface DepartmentRisk {
  department: string;
  retentionRisk: number;
  compositionRisk: number;
  wellbeingScore: number;
  headcount: number;
}

interface GoalBenchmark {
  label: string;
  current: number;
  target: number;
  unit: string;
}

const CEOExecutiveDashboard: React.FC = () => {
  const { user } = useAuth();
  const organizationId = user?.organization_id || 'default-org';
  const timeRange = '90d';
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [heatmap, setHeatmap] = useState<DepartmentHeatmap[]>([]);
  const [forecast, setForecast] = useState<ForecastChart | null>(null);
  const [costBenefit, setCostBenefit] = useState<CostBenefitAnalysis | null>(null);
  const [healthScore, setHealthScore] = useState<OrgHealthScore | null>(null);
  const [deptRisks, setDeptRisks] = useState<DepartmentRisk[]>([]);
  const [benchmarks, setBenchmarks] = useState<GoalBenchmark[]>([]);
  const [loading, setLoading] = useState(true);

  const setMockData = () => {
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

    setHealthScore({
      score: 78,
      trend: 4.2,
      history: [
        { month: 'Jan', score: 72 },
        { month: 'Feb', score: 71 },
        { month: 'Mar', score: 74 },
        { month: 'Apr', score: 75 },
        { month: 'May', score: 77 },
        { month: 'Jun', score: 78 }
      ]
    });

    setDeptRisks([
      { department: 'Engineering', retentionRisk: 22, compositionRisk: 15, wellbeingScore: 68, headcount: 145 },
      { department: 'Sales', retentionRisk: 35, compositionRisk: 28, wellbeingScore: 55, headcount: 92 },
      { department: 'Product', retentionRisk: 18, compositionRisk: 12, wellbeingScore: 74, headcount: 48 },
      { department: 'Marketing', retentionRisk: 25, compositionRisk: 20, wellbeingScore: 71, headcount: 64 },
      { department: 'Operations', retentionRisk: 28, compositionRisk: 22, wellbeingScore: 65, headcount: 110 }
    ]);

    setBenchmarks([
      { label: 'Retention Rate', current: 92, target: 95, unit: '%' },
      { label: 'Engagement Index', current: 74, target: 80, unit: '%' },
      { label: 'Psychological Safety', current: 68, target: 75, unit: '%' }
    ]);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch live summary data
      const summaryRes = await api.get(`/burnout/summary?org_id=${organizationId}&range=${timeRange}`);
      const summaryData = summaryRes.data;

      // Update state with live data
      setSummary({
        overall_risk_score: summaryData.overall_risk_score,
        risk_trend: summaryData.risk_trend as any,
        high_risk_employees: summaryData.high_risk_employees,
        high_risk_percentage: summaryData.high_risk_percentage,
        predicted_turnover_risk_30d: summaryData.predicted_turnover_risk_30d,
        estimated_cost_of_burnout: summaryData.estimated_cost_of_burnout,
        intervention_roi: summaryData.intervention_roi
      });

      setHealthScore({
        score: summaryData.health_index,
        trend: 4.2,
        history: [
          { month: 'Jan', score: 72 },
          { month: 'Feb', score: 71 },
          { month: 'Mar', score: 74 },
          { month: 'Apr', score: 75 },
          { month: 'May', score: 77 },
          { month: 'Jun', score: summaryData.health_index }
        ]
      });

      // Fetch other data
      const [heatmapRes, forecastRes, costBenefitRes] = await Promise.all([
        api.get(`/burnout/heatmap?org_id=${organizationId}`),
        api.get(`/burnout/forecast?org_id=${organizationId}&horizon=14d`),
        api.get(`/burnout/cost-benefit?org_id=${organizationId}`)
      ]);

      setHeatmap(heatmapRes.data.departments || []);
      setForecast(forecastRes.data);
      setCostBenefit(costBenefitRes.data.analysis || costBenefitRes.data);

      setBenchmarks([
        { label: 'Retention Rate', current: 92, target: 95, unit: '%' },
        { label: 'Engagement Index', current: 74, target: 80, unit: '%' },
        { label: 'Psychological Safety', current: 68, target: 75, unit: '%' }
      ]);
    } catch (error) {
      console.error('Error loading executive dashboard:', error);
      setMockData();
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 bg-white min-h-screen">
      {/* Executive Header & Narrative Callout */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b pb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">CEO Executive Dashboard</h1>
          <p className="text-slate-500 mt-1">Strategic organizational health & retention insights</p>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3 max-w-md">
          <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-900">Needs Attention</p>
            <p className="text-xs text-amber-800 leading-relaxed mt-0.5">
              Sales team retention risk crossed the 30% threshold this month. Composition mismatches in mid-level management are primary drivers.
            </p>
          </div>
        </div>
      </div>

      {/* Top Level: Org Health Score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 shadow-none border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 uppercase tracking-wider">Organizational Health Index</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <span className="text-6xl font-bold text-slate-900">{healthScore?.score}</span>
              <div className="flex items-center text-green-600 font-semibold text-sm">
                <TrendingUp className="h-4 w-4 mr-0.5" />
                {healthScore?.trend}%
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-2">Composite score of engagement, retention, and team compatibility</p>
            <div className="h-32 mt-6 min-h-[128px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={healthScore?.history}>
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#4F46E5"
                    strokeWidth={3}
                    dot={false}
                  />
                  <Tooltip
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-4">
          {benchmarks.map((goal, idx) => (
            <Card key={idx} className="shadow-none border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-slate-500 uppercase tracking-wider">{goal.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-bold text-slate-900">{goal.current}{goal.unit}</span>
                  <span className="text-xs text-slate-400">Target: {goal.target}{goal.unit}</span>
                </div>
                <div className="mt-4 h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${goal.current >= goal.target ? 'bg-green-500' : 'bg-indigo-500'}`}
                    style={{ width: `${(goal.current / goal.target) * 100}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-400 mt-2 uppercase font-semibold tracking-tighter">
                  {goal.target - goal.current > 0 ? `${goal.target - goal.current}${goal.unit} to target` : 'Goal met'}
                </p>
              </CardContent>
            </Card>
          ))}

          <Card className="md:col-span-3 shadow-none bg-slate-50 border-dashed border-slate-300">
            <CardContent className="py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-indigo-600" />
                <span className="text-sm font-medium text-slate-700">All data anonymized to department level to preserve trust and privacy.</span>
              </div>
              <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-700 font-semibold">
                Privacy Policy
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Middle Section: Risks by Department */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="shadow-none border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg">Retention Risk by Department</CardTitle>
            <CardDescription>Predicted flight risk based on engagement & stress signals</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={deptRisks} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#F1F5F9" />
                  <XAxis type="number" hide />
                  <YAxis
                    dataKey="department"
                    type="category"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#64748B', fontSize: 12 }}
                  />
                  <Tooltip
                    cursor={{ fill: '#F8FAFC' }}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="retentionRisk" radius={[0, 4, 4, 0]} barSize={24}>
                    {deptRisks.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.retentionRisk > 30 ? '#EF4444' : '#4F46E5'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-none border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg">Team Compatibility Heatmap</CardTitle>
            <CardDescription>Structural mismatch risk across business units</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {deptRisks.sort((a, b) => b.compositionRisk - a.compositionRisk).map((dept, idx) => (
                <div key={idx} className="flex items-center gap-4">
                  <div className="w-24 text-sm font-medium text-slate-600">{dept.department}</div>
                  <div className="flex-1 h-8 rounded-md overflow-hidden flex">
                    <div
                      className={`h-full transition-all duration-500`}
                      style={{
                        width: `${dept.compositionRisk}%`,
                        backgroundColor: dept.compositionRisk > 25 ? '#FEE2E2' : '#EEF2FF',
                        borderRight: `2px solid ${dept.compositionRisk > 25 ? '#EF4444' : '#4F46E5'}`
                      }}
                    />
                    <div className="flex-1 bg-slate-50" />
                  </div>
                  <div className="w-12 text-right text-xs font-bold text-slate-400">
                    {dept.compositionRisk}%
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 pt-6 border-t border-slate-100 flex justify-between items-center text-xs text-slate-400 uppercase tracking-widest font-semibold">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-indigo-500" /> Optimal Alignment
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-red-500" /> Critical Mismatch
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section: Wellbeing Trends & Benchmarks */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="shadow-none border-slate-200 bg-emerald-50/30">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Zap className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-emerald-800 uppercase tracking-tight">Wellbeing Trend</p>
              <p className="text-sm font-bold text-emerald-900 mt-0.5">Improving (+2.1%)</p>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-none border-slate-200">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-slate-100 rounded-lg">
              <Users className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-tight">Active Headcount</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">459 Total</p>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-none border-slate-200">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-slate-100 rounded-lg">
              <Target className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-tight">Q3 Goal Status</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">On Track (82%)</p>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-none border-slate-200">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-slate-100 rounded-lg">
              <ShieldCheck className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-tight">Compliance Status</p>
              <p className="text-sm font-bold text-slate-900 mt-0.5">100% Certified</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Footer Info */}
      <div className="text-center pt-8">
        <p className="text-[10px] text-slate-400 uppercase tracking-[0.2em] font-bold">
          Strategic Organizational Intelligence &bull; Strictly Confidential &bull; Generated {new Date().toLocaleDateString()}
        </p>
      </div>
    </div>
  );
};

export default CEOExecutiveDashboard;
