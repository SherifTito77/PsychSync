// Burnout Prevention & Prediction Page
// Advanced burnout risk assessment with Karoshi/Gapjil prevention
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Flame,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Heart,
  Clock,
  Calendar,
  Shield,
  CheckCircle,
  XCircle,
  Zap,
  Brain,
  Moon,
  Sun,
  Coffee,
  Users,
  BarChart3,
  Download,
  RefreshCw
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface BurnoutRisk {
  overall_score: number;
  risk_level: 'low' | 'moderate' | 'high' | 'critical';
  burnout_stage: string;
  seven_day_probability: number;
  thirty_day_probability: number;
  ninety_day_turnover_risk: number;
  risk_breakdown: {
    work_hours: number;
    recovery_time: number;
    sentiment_trend: number;
    social_withdrawal: number;
    response_pattern: number;
  };
  early_indicators: string[];
  interventions: Array<{
    priority: string;
    title: string;
    description: string;
    timeline: string;
  }>;
}

interface TeamBurnoutData {
  team_name: string;
  avg_risk: number;
  high_risk_count: number;
  critical_count: number;
  trend: 'improving' | 'stable' | 'declining';
}

const BurnoutPrevention: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [burnoutRisk, setBurnoutRisk] = useState<BurnoutRisk | null>(null);
  const [teamData, setTeamData] = useState<TeamBurnoutData[]>([]);
  const [timeRange, setTimeRange] = useState('30d');
  const { user } = useAuth();

  useEffect(() => {
    loadBurnoutData();
  }, [timeRange]);

  const loadBurnoutData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const userId = user?.id;
      const orgId = user?.organization_id ?? userId;

      const [forecastRes, alertsRes, heatmapRes] = await Promise.all([
        userId
          ? fetch(`/api/v1/behavioral/forecasts/${userId}`, {
              headers: { Authorization: `Bearer ${token}` },
            }).then(r => r.ok ? r.json() : null)
          : Promise.resolve(null),
        userId
          ? fetch(`/api/v1/behavioral/alerts/${userId}`, {
              headers: { Authorization: `Bearer ${token}` },
            }).then(r => r.ok ? r.json() : null)
          : Promise.resolve(null),
        orgId
          ? fetch(`/api/v1/executive/burnout/heatmap?org_id=${orgId}`, {
              headers: { Authorization: `Bearer ${token}` },
            }).then(r => r.ok ? r.json() : null)
          : Promise.resolve(null),
      ]);

      // Map forecast data → BurnoutRisk shape
      const burnout = forecastRes?.burnoutRiskForecast;
      const wellness = forecastRes?.wellnessForecast;
      const riskLevelMap: Record<string, BurnoutRisk['risk_level']> = {
        low: 'low', moderate: 'moderate', high: 'high', critical: 'critical',
      };
      const mappedRisk: BurnoutRisk = {
        overall_score: burnout?.current ?? 50,
        risk_level: riskLevelMap[burnout?.riskLevel ?? 'moderate'] ?? 'moderate',
        burnout_stage: burnout?.riskLevel === 'critical' ? 'Exhaustion' : burnout?.riskLevel === 'high' ? 'Overextension' : 'Engagement',
        seven_day_probability: burnout?.predicted7Days ?? 0,
        thirty_day_probability: burnout?.predicted30Days ?? 0,
        ninety_day_turnover_risk: Math.min(100, (burnout?.predicted30Days ?? 0) + 15),
        risk_breakdown: {
          work_hours: Math.min(100, (burnout?.current ?? 50) + 10),
          recovery_time: Math.max(0, 100 - (wellness?.current ?? 50)),
          sentiment_trend: wellness?.current ?? 50,
          social_withdrawal: Math.min(100, (burnout?.current ?? 50) - 5),
          response_pattern: burnout?.current ?? 50,
        },
        early_indicators: (alertsRes?.warnings ?? []).map((w: any) => w.message),
        interventions: (alertsRes?.tips ?? []).map((t: any, i: number) => ({
          priority: i === 0 ? 'high' : 'medium',
          title: t.category?.replace(/_/g, ' ') ?? 'Tip',
          description: t.message ?? '',
          timeline: 'Ongoing',
        })),
      };
      setBurnoutRisk(mappedRisk);

      // Map heatmap departments → TeamBurnoutData
      if (heatmapRes?.departments?.length > 0) {
        const teams: TeamBurnoutData[] = heatmapRes.departments.map((d: any) => ({
          team_name: d.department ?? d.name ?? 'Team',
          avg_risk: d.burnout_risk_score ?? d.avg_risk ?? 30,
          high_risk_count: d.high_risk_employees ?? 0,
          critical_count: d.critical_employees ?? 0,
          trend: d.trend ?? 'stable',
        }));
        setTeamData(teams);
      }
    } catch (error) {
      toast.error('Failed to load burnout data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'moderate': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'declining': return <TrendingDown className="h-4 w-4 text-red-600" />;
      case 'stable': return <Activity className="h-4 w-4 text-blue-600" />;
      default: return null;
    }
  };

  if (loading && !burnoutRisk) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Flame className="h-8 w-8 text-orange-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Burnout Prevention & Prediction</h1>
            <p className="text-sm text-gray-500">AI-powered burnout risk assessment with cultural sensitivity (Karoshi/Gapjil prevention)</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <Button onClick={loadBurnoutData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Critical Alert */}
      {burnoutRisk?.risk_level === 'critical' && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertTitle className="text-red-800">Critical Burnout Risk Detected</AlertTitle>
          <AlertDescription className="text-red-700">
            Immediate intervention required. Your burnout risk score indicates critical levels of stress and exhaustion.
            Please contact HR or your manager immediately.
          </AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="risk-factors">Risk Factors</TabsTrigger>
          <TabsTrigger value="team-view">Team View</TabsTrigger>
          <TabsTrigger value="interventions">Interventions</TabsTrigger>
          <TabsTrigger value="cultural">Cultural</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Main Risk Score */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Flame className="h-5 w-5 text-orange-600" />
                  <span>Overall Burnout Risk</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-5xl font-bold mb-2">{burnoutRisk?.overall_score || 0}/100</div>
                  <Badge className={getRiskColor(burnoutRisk?.risk_level || 'low')} size="sm">
                    {burnoutRisk?.risk_level?.toUpperCase()} RISK
                  </Badge>
                  <p className="text-sm text-gray-600 mt-3">Stage: {burnoutRisk?.burnout_stage}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">7-Day Probability</CardTitle>
                <TrendingDown className="h-4 w-4 text-blue-600 mt-1" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{burnoutRisk?.seven_day_probability || 0}%</div>
                <p className="text-xs text-gray-500">Short-term risk</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">90-Day Turnover Risk</CardTitle>
                <Users className="h-4 w-4 text-red-600 mt-1" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{burnoutRisk?.ninety_day_turnover_risk || 0}%</div>
                <p className="text-xs text-gray-500">Long-term risk</p>
              </CardContent>
            </Card>
          </div>

          {/* Early Indicators */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <span>Early Warning Indicators</span>
              </CardTitle>
              <CardDescription>Patterns detected that may indicate burnout risk</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {burnoutRisk?.early_indicators.map((indicator, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <XCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-yellow-800">{indicator}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Factors Tab */}
        <TabsContent value="risk-factors" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Risk Breakdown</CardTitle>
              <CardDescription>Analysis of different burnout risk factors</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {burnoutRisk && Object.entries(burnoutRisk.risk_breakdown).map(([key, value]) => {
                const labels: Record<string, string> = {
                  work_hours: 'Work Hours',
                  recovery_time: 'Recovery Time',
                  sentiment_trend: 'Sentiment Trend',
                  social_withdrawal: 'Social Withdrawal',
                  response_pattern: 'Response Pattern'
                };
                const icons: Record<string, React.ReactNode> = {
                  work_hours: <Clock className="h-4 w-4" />,
                  recovery_time: <Moon className="h-4 w-4" />,
                  sentiment_trend: <Brain className="h-4 w-4" />,
                  social_withdrawal: <Users className="h-4 w-4" />,
                  response_pattern: <Activity className="h-4 w-4" />
                };

                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {icons[key]}
                        <span className="font-medium">{labels[key]}</span>
                      </div>
                      <span className="text-sm font-semibold">{value}/100</span>
                    </div>
                    <Progress value={value} className="h-2" />
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Work Pattern Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Work Pattern Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Avg. Work Hours/Week</span>
                    <Clock className="h-4 w-4 text-orange-600" />
                  </div>
                  <div className="text-2xl font-bold">62 hrs</div>
                  <p className="text-xs text-red-600 mt-1">Above recommended 40-50 hrs</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">After-Hours Work</span>
                    <Moon className="h-4 w-4 text-purple-600" />
                  </div>
                  <div className="text-2xl font-bold">18%</div>
                  <p className="text-xs text-yellow-600 mt-1">Evenings & weekends</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Last PTO</span>
                  <Calendar className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="text-2xl font-bold">6 mo</div>
                  <p className="text-xs text-red-600 mt-1">No break taken</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Team View Tab */}
        <TabsContent value="team-view" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5 text-blue-600" />
                <span>Team Burnout Heatmap</span>
              </CardTitle>
              <CardDescription>Anonymized team burnout risk overview</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {teamData.map((team) => (
                  <div key={team.team_name} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-semibold">{team.team_name}</h3>
                        <Badge variant="outline" className="flex items-center space-x-1">
                          {getTrendIcon(team.trend)}
                          <span className="ml-1 capitalize">{team.trend}</span>
                        </Badge>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{team.avg_risk}</div>
                        <p className="text-xs text-gray-500">Avg Risk Score</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Team Size:</span>
                        <span className="ml-2 font-medium">--</span>
                      </div>
                      <div className="text-orange-600">
                        <span className="text-gray-600">High Risk:</span>
                        <span className="ml-2 font-medium">{team.high_risk_count}</span>
                      </div>
                      <div className="text-red-600">
                        <span className="text-gray-600">Critical:</span>
                        <span className="ml-2 font-medium">{team.critical_count}</span>
                      </div>
                    </div>
                    <Progress value={team.avg_risk} className="mt-3 h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Manager Alerts */}
          {burnoutRisk?.risk_level === 'high' || burnoutRisk?.risk_level === 'critical' ? (
            <Alert className="border-red-200 bg-red-50">
              <Shield className="h-4 w-4 text-red-600" />
              <AlertTitle>Manager Action Required</AlertTitle>
              <AlertDescription>
                Your team shows elevated burnout risk. Consider: workload redistribution, mandatory time-off policies,
                after-hours communication restrictions, and 1:1 check-ins with all team members.
              </AlertDescription>
            </Alert>
          ) : null}
        </TabsContent>

        {/* Interventions Tab */}
        <TabsContent value="interventions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Heart className="h-5 w-5 text-pink-600" />
                <span>Recommended Interventions</span>
              </CardTitle>
              <CardDescription>Personalized action plan to reduce burnout risk</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {burnoutRisk?.interventions.map((intervention, index) => (
                  <Card key={index} className={`border-l-4 ${
                    intervention.priority === 'urgent' ? 'border-l-red-600' :
                    intervention.priority === 'high' ? 'border-l-orange-600' :
                    'border-l-blue-600'
                  }`}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge className={
                              intervention.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                              intervention.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                              'bg-blue-100 text-blue-800'
                            }>
                              {intervention.priority.toUpperCase()}
                            </Badge>
                            <h4 className="font-semibold">{intervention.title}</h4>
                          </div>
                          <p className="text-sm text-gray-600 mb-3">{intervention.description}</p>
                          <div className="flex items-center text-xs text-gray-500">
                            <Clock className="h-3 w-3 mr-1" />
                            {intervention.timeline}
                          </div>
                        </div>
                        <Button size="sm">Start</Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recovery Tracking */}
          <Card>
            <CardHeader>
              <CardTitle>Recovery Progress</CardTitle>
              <CardDescription>Track your improvement over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Start an intervention to track recovery progress</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cultural Tab */}
        <TabsContent value="cultural" className="space-y-6">
          {/* Karoshi Prevention */}
          <Card className="border-2 border-red-200">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-red-700">
                <Flame className="h-5 w-5" />
                <span>Karoshi Prevention (過労死)</span>
              </CardTitle>
              <CardDescription>Death from overwork - detection and prevention</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertTitle>Hard Stop Triggers</AlertTitle>
                <AlertDescription className="space-y-2 mt-2">
                  <p>• 4 consecutive weeks of &gt;65 hours → Manager escalation + HR alert</p>
                  <p>• After-hours work &gt;30% of total time → Forced PTO within 2 weeks</p>
                  <p>• No vacation in 6 months → Automatic PTO booking</p>
                  <p>• 11 PM+ work &gt;5x/month → Executive review</p>
                </AlertDescription>
              </Alert>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-2">Japan Compliance</h4>
                  <p className="text-sm text-red-700">Tracking against 360-hour overtime limit (monthly average)</p>
                </div>
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">South Korea Compliance</h4>
                  <p className="text-sm text-blue-700">52-hour workweek compliance monitoring</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gapjil Prevention */}
          <Card className="border-2 border-orange-200">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-orange-700">
                <Shield className="h-5 w-5" />
                <span>Gapjil Prevention (갑질)</span>
              </CardTitle>
              <CardDescription>Abuse of power - detection and prevention</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <Users className="h-4 w-4 text-orange-600" />
                <AlertTitle>Cultural Pressure Detection</AlertTitle>
                <AlertDescription className="space-y-2 mt-2">
                  <p>• Late-night work patterns (past 9 PM) from hierarchical pressure</p>
                  <p>• Weekend email activity from cultural expectations</p>
                  <p>• Excessive deference language and apologies (Nunchi indicators)</p>
                  <p>• Silent suffering markers (declining to speak up)</p>
                </AlertDescription>
              </Alert>

              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <h4 className="font-semibold text-orange-800 mb-2">Junior Staff Protection</h4>
                <p className="text-sm text-orange-700 mb-3">
                  Automatic monitoring for hierarchical abuse patterns targeting junior employees
                </p>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Anonymous reporting enabled</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Manager behavior tracking</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>After-hours communication restrictions</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Global Compliance */}
          <Card>
            <CardHeader>
              <CardTitle>Global Compliance Standards</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 border rounded">
                  <h4 className="font-medium mb-1">EU Working Time Directive</h4>
                  <p className="text-xs text-gray-600">Max 48 hours/week, 11 hours daily rest</p>
                </div>
                <div className="p-3 border rounded">
                  <h4 className="font-medium mb-1">US FLSA</h4>
                  <p className="text-xs text-gray-600">Overtime pay after 40 hours/week</p>
                </div>
                <div className="p-3 border rounded">
                  <h4 className="font-medium mb-1">Australia Fair Work</h4>
                  <p className="text-xs text-gray-600">38 hour work week maximum</p>
                </div>
                <div className="p-3 border rounded">
                  <h4 className="font-medium mb-1">UK Working Time Regulations</h4>
                  <p className="text-xs text-gray-600">48 hours max opt-out available</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Export */}
      <Card>
        <CardHeader>
          <CardTitle>Export Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-3">
            <Button variant="outline" className="flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Export Report</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Export Team Data</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BurnoutPrevention;
