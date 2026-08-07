/**
 * Integrated Predictive Analytics Dashboard
 *
 * Comprehensive dashboard that integrates all PsychSync analytics capabilities:
 * Growth trajectories, intervention effectiveness, longitudinal analysis, and organizational insights.
 */

import React, { useState, useEffect, useMemo } from 'react';
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
import Progress from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Treemap,
  ReferenceLine,
  ReferenceArea,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Target,
  Users,
  Brain,
  Activity,
  BarChart3,
  PieChart as PieChartIcon,
  Zap,
  Shield,
  Settings,
  Download,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  Rocket,
  Award,
  Star,
  Filter,
  RefreshCw,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

// Types
interface OrganizationalMetrics {
  overallScore: number;
  growthRate: number;
  engagementLevel: number;
  performanceIndex: number;
  innovationCapacity: number;
  retentionRate: number;
  diversityIndex: number;
  collaborationScore: number;
}

interface PredictiveInsight {
  id: string;
  category: 'growth' | 'performance' | 'retention' | 'intervention' | 'risk';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  confidence: number;
  timeHorizon: string;
  impact: number;
  recommendations: string[];
  metrics: string[];
}

interface InterventionEffectiveness {
  id: string;
  name: string;
  effectivenessScore: number;
  roi: number;
  participantCount: number;
  completionRate: number;
  skillGained: string;
  impactArea: string;
  status: 'active' | 'completed' | 'planned';
}

interface GrowthTrajectory {
  userId: string;
  userName: string;
  competency: string;
  currentLevel: number;
  predictedLevel: number;
  growthVelocity: number;
  timeToMastery: number;
  potentialScore: number;
  milestones: {
    achieved: number;
    total: number;
  };
}

interface OrganizationalRisk {
  category: 'turnover' | 'performance' | 'skill_gap' | 'compliance' | 'financial';
  level: 'critical' | 'high' | 'medium' | 'low';
  probability: number;
  impact: number;
  description: string;
  mitigation: string;
  affectedCount: number;
}

interface PredictiveAnalyticsDashboardProps {
  organizationId?: string;
  timeRange?: string;
  refreshInterval?: number;
  onExportData?: (format: string) => void;
}

const PredictiveAnalyticsDashboard: React.FC<PredictiveAnalyticsDashboardProps> = ({
  organizationId,
  timeRange = '12m',
  refreshInterval = 300000, // 5 minutes
  onExportData,
}) => {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [timeRangeFilter, setTimeRangeFilter] = useState(timeRange);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Mock data - in production this would come from APIs
  const organizationalMetrics: OrganizationalMetrics = {
    overallScore: 0.82,
    growthRate: 0.15,
    engagementLevel: 0.78,
    performanceIndex: 0.85,
    innovationCapacity: 0.71,
    retentionRate: 0.88,
    diversityIndex: 0.73,
    collaborationScore: 0.79,
  };

  const predictiveInsights: PredictiveInsight[] = [
    {
      id: '1',
      category: 'growth',
      priority: 'high',
      title: 'High-Potential Employee Flight Risk',
      description: '3 top performers showing declining engagement patterns, 78% probability of departure within 6 months',
      confidence: 0.85,
      timeHorizon: '6 months',
      impact: 0.9,
      recommendations: [
        'Implement retention bonus program',
        'Schedule career development discussions',
        'Review compensation packages',
      ],
      metrics: ['Engagement Score', 'Performance Trend', 'Salary Benchmark'],
    },
    {
      id: '2',
      category: 'performance',
      priority: 'medium',
      title: 'Leadership Pipeline Gap Identified',
      description: 'Current succession planning shows 42% gap in senior leadership positions within 2 years',
      confidence: 0.78,
      timeHorizon: '24 months',
      impact: 0.7,
      recommendations: [
        'Accelerate high-potential development programs',
        'Implement mentorship initiatives',
        'Consider external hiring for critical roles',
      ],
      metrics: ['Leadership Competency', 'Readiness Assessment', 'Position Criticality'],
    },
    {
      id: '3',
      category: 'intervention',
      priority: 'critical',
      title: 'Leadership Development Program Impact',
      description: 'Upcoming leadership intervention projected to improve team performance by 23% with 95% confidence',
      confidence: 0.92,
      timeHorizon: '3 months',
      impact: 0.8,
      recommendations: [
        'Ensure participant selection alignment',
        'Prepare implementation resources',
        'Establish success metrics',
      ],
      metrics: ['Leadership Assessment', 'Team Performance', '360 Feedback'],
    },
    {
      id: '4',
      category: 'risk',
      priority: 'high',
      title: 'Skill Gap in Digital Transformation',
      description: 'Critical digital skills gap identified in 67% of leadership roles, affecting organizational agility',
      confidence: 0.88,
      timeHorizon: '12 months',
      impact: 0.85,
      recommendations: [
        'Launch digital literacy programs',
        'Partner with external training providers',
        'Incentivize skill acquisition',
      ],
      metrics: ['Digital Skills Assessment', 'Role Requirements', 'Training Completion'],
    },
  ];

  const interventionEffectiveness: InterventionEffectiveness[] = [
    {
      id: '1',
      name: 'Leadership Excellence Program',
      effectivenessScore: 0.87,
      roi: 3.2,
      participantCount: 45,
      completionRate: 0.91,
      skillGained: 'Strategic Thinking',
      impactArea: 'Leadership',
      status: 'active',
    },
    {
      id: '2',
      name: 'Technical Skills Upskilling',
      effectivenessScore: 0.82,
      roi: 2.8,
      participantCount: 128,
      completionRate: 0.87,
      skillGained: 'Cloud Computing',
      impactArea: 'Technical',
      status: 'completed',
    },
    {
      id: '3',
      name: 'Communication Mastery',
      effectivenessScore: 0.75,
      roi: 2.1,
      participantCount: 67,
      completionRate: 0.83,
      skillGained: 'Executive Presence',
      impactArea: 'Soft Skills',
      status: 'active',
    },
  ];

  const growthTrajectories: GrowthTrajectory[] = [
    {
      userId: '1',
      userName: 'Sarah Johnson',
      competency: 'Leadership',
      currentLevel: 3.2,
      predictedLevel: 4.1,
      growthVelocity: 0.08,
      timeToMastery: 540,
      potentialScore: 0.91,
      milestones: { achieved: 4, total: 6 },
    },
    {
      userId: '2',
      userName: 'Michael Chen',
      competency: 'Technical Innovation',
      currentLevel: 2.8,
      predictedLevel: 3.9,
      growthVelocity: 0.12,
      timeToMastery: 420,
      potentialScore: 0.88,
      milestones: { achieved: 3, total: 5 },
    },
    {
      userId: '3',
      userName: 'Emily Rodriguez',
      competency: 'Strategic Planning',
      currentLevel: 3.5,
      predictedLevel: 4.3,
      growthVelocity: 0.06,
      timeToMastery: 680,
      potentialScore: 0.85,
      milestones: { achieved: 5, total: 7 },
    },
    {
      userId: '4',
      userName: 'David Kim',
      competency: 'Team Management',
      currentLevel: 2.9,
      predictedLevel: 3.7,
      growthVelocity: 0.09,
      timeToMastery: 480,
      potentialScore: 0.82,
      milestones: { achieved: 2, total: 5 },
    },
  ];

  const organizationalRisks: OrganizationalRisk[] = [
    {
      category: 'turnover',
      level: 'critical',
      probability: 0.78,
      impact: 0.85,
      description: 'High-performing employee turnover risk in key technical roles',
      mitigation: 'Implement targeted retention strategies and career pathing',
      affectedCount: 23,
    },
    {
      category: 'skill_gap',
      level: 'high',
      probability: 0.65,
      impact: 0.7,
      description: 'Emerging technology skills gap across senior management',
      mitigation: 'Accelerated digital transformation training programs',
      affectedCount: 45,
    },
    {
      category: 'performance',
      level: 'medium',
      probability: 0.42,
      impact: 0.6,
      description: 'Performance plateau in mid-level management roles',
      mitigation: 'Advanced leadership development interventions',
      affectedCount: 34,
    },
  ];

  // Data preparation for charts
  const metricsRadarData = useMemo(() => [
    { metric: 'Growth', value: organizationalMetrics.growthRate * 100, fullMark: 100 },
    { metric: 'Engagement', value: organizationalMetrics.engagementLevel * 100, fullMark: 100 },
    { metric: 'Performance', value: organizationalMetrics.performanceIndex * 100, fullMark: 100 },
    { metric: 'Innovation', value: organizationalMetrics.innovationCapacity * 100, fullMark: 100 },
    { metric: 'Retention', value: organizationalMetrics.retentionRate * 100, fullMark: 100 },
    { metric: 'Diversity', value: organizationalMetrics.diversityIndex * 100, fullMark: 100 },
    { metric: 'Collaboration', value: organizationalMetrics.collaborationScore * 100, fullMark: 100 },
  ], [organizationalMetrics]);

  const interventionROIData = useMemo(() => interventionEffectiveness.map(intervention => ({
    name: intervention.name.length > 20 ? intervention.name.substring(0, 20) + '...' : intervention.name,
    roi: intervention.roi,
    effectiveness: intervention.effectivenessScore * 100,
    participants: intervention.participantCount,
  })), [interventionEffectiveness]);

  const growthTrajectoryData = useMemo(() => growthTrajectories.map(trajectory => ({
    name: trajectory.userName.split(' ')[0],
    current: trajectory.currentLevel,
    predicted: trajectory.predictedLevel,
    potential: trajectory.potentialScore * 100,
    velocity: trajectory.growthVelocity * 100,
  })), [growthTrajectories]);

  const riskDistributionData = useMemo(() => [
    { category: 'Critical', value: organizationalRisks.filter(r => r.level === 'critical').length, color: 'var(--color-error)' },
    { category: 'High', value: organizationalRisks.filter(r => r.level === 'high').length, color: 'var(--color-clinical-moderate)' },
    { category: 'Medium', value: organizationalRisks.filter(r => r.level === 'medium').length, color: 'var(--color-warning)' },
    { category: 'Low', value: organizationalRisks.filter(r => r.level === 'low').length, color: 'var(--color-success)' },
  ], [organizationalRisks]);

  const insightsByCategory = useMemo(() => Object.entries(
    predictiveInsights.reduce((acc, insight) => {
      acc[insight.category] = (acc[insight.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([category, count]) => ({
    category: category.charAt(0).toUpperCase() + category.slice(1),
    count,
  })), [predictiveInsights]);

  // Helper functions
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getImpactColor = (impact: number) => {
    if (impact >= 0.8) return 'text-red-600';
    if (impact >= 0.6) return 'text-orange-600';
    if (impact >= 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  const handleRefresh = () => {
    setIsLoading(true);
    // Simulate data refresh
    setTimeout(() => {
      setLastRefresh(new Date());
      setIsLoading(false);
    }, 1000);
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(organizationalMetrics.overallScore * 100).toFixed(1)}%</div>
            <Progress value={organizationalMetrics.overallScore * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Growth Rate</CardTitle>
            <Rocket className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">+{(organizationalMetrics.growthRate * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">vs. last quarter</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Insights</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{predictiveInsights.length}</div>
            <div className="flex gap-1 mt-2">
              <Badge variant="secondary" className="text-xs">
                {predictiveInsights.filter(i => i.priority === 'critical').length} Critical
              </Badge>
              <Badge variant="outline" className="text-xs">
                {predictiveInsights.filter(i => i.priority === 'high').length} High
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Level</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">Medium</div>
            <p className="text-xs text-muted-foreground">
              {organizationalRisks.filter(r => r.level === 'critical' || r.level === 'high').length} high-priority risks
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Predictive Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5" />
            Predictive Insights
          </CardTitle>
          <CardDescription>
            AI-powered insights and recommendations based on advanced analytics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {predictiveInsights.map((insight) => (
              <div key={insight.id} className="p-4 border rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">{insight.title}</h3>
                      <Badge className={getPriorityColor(insight.priority)}>
                        {insight.priority}
                      </Badge>
                      <Badge variant="outline">{insight.category}</Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{insight.description}</p>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-sm text-gray-600">Confidence</div>
                    <div className="font-bold">{formatConfidence(insight.confidence)}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Time Horizon: </span>
                    <span className="font-medium">{insight.timeHorizon}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Impact: </span>
                    <span className={`font-medium ${getImpactColor(insight.impact)}`}>
                      {(insight.impact * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Metrics: </span>
                    <span className="font-medium">{insight.metrics.length}</span>
                  </div>
                  <div className="flex justify-end">
                    <Button variant="outline" size="sm">
                      View Details
                      <ChevronRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Radar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Organizational Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={metricsRadarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="Current Performance"
                  dataKey="value"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(props: any) => `${props.category} ${(props.percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderGrowthTab = () => (
    <div className="space-y-6">
      {/* Growth Trajectories */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Growth Trajectories
          </CardTitle>
          <CardDescription>
            Individual growth predictions and potential assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={growthTrajectoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="current" stroke="#3b82f6" strokeWidth={2} name="Current Level" />
              <Line type="monotone" dataKey="predicted" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" name="Predicted Level" />
              <Line type="monotone" dataKey="potential" stroke="#f59e0b" strokeWidth={2} name="Potential Score" />
            </LineChart>
          </ResponsiveContainer>

          {/* Growth Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {growthTrajectories.length}
              </div>
              <p className="text-sm text-gray-600">High Potential Employees</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {(growthTrajectories.reduce((sum, t) => sum + t.potentialScore, 0) / growthTrajectories.length * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Average Potential Score</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {(growthTrajectories.reduce((sum, t) => sum + t.growthVelocity, 0) / growthTrajectories.length * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Average Growth Velocity</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.floor(growthTrajectories.reduce((sum, t) => sum + t.timeToMastery, 0) / growthTrajectories.length / 30)}
              </div>
              <p className="text-sm text-gray-600">Months to Mastery</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Milestone Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Milestone Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {growthTrajectories.map((trajectory) => (
              <div key={trajectory.userId} className="p-4 border rounded-lg">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold">{trajectory.userName}</h3>
                    <p className="text-sm text-gray-600">{trajectory.competency}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">Potential</div>
                    <div className="font-bold">{(trajectory.potentialScore * 100).toFixed(0)}%</div>
                  </div>
                </div>

                <div className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Milestone Progress</span>
                    <span>{trajectory.milestones.achieved}/{trajectory.milestones.total}</span>
                  </div>
                  <Progress
                    value={(trajectory.milestones.achieved / trajectory.milestones.total) * 100}
                    className="h-2"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Current: </span>
                    <span className="font-medium">{trajectory.currentLevel.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Predicted: </span>
                    <span className="font-medium">{trajectory.predictedLevel.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Time to Mastery: </span>
                    <span className="font-medium">{Math.floor(trajectory.timeToMastery / 30)} months</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderInterventionsTab = () => (
    <div className="space-y-6">
      {/* Intervention Effectiveness */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Intervention Effectiveness Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={interventionROIData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} />
              <Tooltip />
              <Legend />
              <Bar dataKey="roi" fill="#10b981" name="ROI (x)" />
              <Bar dataKey="effectiveness" fill="#3b82f6" name="Effectiveness (%)" />
            </BarChart>
          </ResponsiveContainer>

          {/* Intervention Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {interventionEffectiveness.length}
              </div>
              <p className="text-sm text-gray-600">Active Programs</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {(interventionEffectiveness.reduce((sum, i) => sum + i.effectivenessScore, 0) / interventionEffectiveness.length * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Avg. Effectiveness</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {(interventionEffectiveness.reduce((sum, i) => sum + i.roi, 0) / interventionEffectiveness.length).toFixed(1)}x
              </div>
              <p className="text-sm text-gray-600">Avg. ROI</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {interventionEffectiveness.reduce((sum, i) => sum + i.participantCount, 0).toLocaleString()}
              </div>
              <p className="text-sm text-gray-600">Total Participants</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Program Details */}
      <Card>
        <CardHeader>
          <CardTitle>Program Details & Impact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {interventionEffectiveness.map((intervention) => (
              <div key={intervention.id} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold">{intervention.name}</h3>
                    <Badge variant={intervention.status === 'active' ? 'default' : 'secondary'}>
                      {intervention.status}
                    </Badge>
                    <Badge variant="outline">{intervention.impactArea}</Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-right">
                      <div className="text-gray-600">ROI</div>
                      <div className="font-bold text-green-600">{intervention.roi}x</div>
                    </div>
                    <div className="text-right">
                      <div className="text-gray-600">Effectiveness</div>
                      <div className="font-bold">{(intervention.effectivenessScore * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Participants: </span>
                    <span className="font-medium">{intervention.participantCount}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Completion: </span>
                    <span className="font-medium">{(intervention.completionRate * 100).toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Primary Skill: </span>
                    <span className="font-medium">{intervention.skillGained}</span>
                  </div>
                </div>

                {/* Progress bars */}
                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Effectiveness</span>
                      <span>{(intervention.effectivenessScore * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={intervention.effectivenessScore * 100} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span>Completion Rate</span>
                      <span>{(intervention.completionRate * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={intervention.completionRate * 100} className="h-2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderRisksTab = () => (
    <div className="space-y-6">
      {/* Risk Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Organizational Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {organizationalRisks.filter(r => r.level === 'critical').length}
              </div>
              <p className="text-sm text-gray-600">Critical Risks</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {organizationalRisks.filter(r => r.level === 'high').length}
              </div>
              <p className="text-sm text-gray-600">High Priority</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {(organizationalRisks.reduce((sum, r) => sum + r.probability, 0) / organizationalRisks.length * 100).toFixed(1)}%
              </div>
              <p className="text-sm text-gray-600">Avg. Probability</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {organizationalRisks.reduce((sum, r) => sum + r.affectedCount, 0).toLocaleString()}
              </div>
              <p className="text-sm text-gray-600">People Affected</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Details */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Analysis & Mitigation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {organizationalRisks.map((risk, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold capitalize">{risk.category.replace('_', ' ')} Risk</h3>
                      <Badge className={getPriorityColor(risk.level)}>
                        {risk.level}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{risk.description}</p>
                    <p className="text-sm text-gray-500">
                      <span className="font-medium">Mitigation: </span>
                      {risk.mitigation}
                    </p>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-sm text-gray-600">Probability</div>
                    <div className="font-bold text-orange-600">{(risk.probability * 100).toFixed(0)}%</div>
                    <div className="text-sm text-gray-600 mt-1">Impact</div>
                    <div className="font-bold">{(risk.impact * 100).toFixed(0)}%</div>
                    <div className="text-sm text-gray-600 mt-1">Affected</div>
                    <div className="font-bold">{risk.affectedCount}</div>
                  </div>
                </div>

                {/* Risk probability and impact visualization */}
                <div className="mt-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span>Probability</span>
                        <span>{(risk.probability * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={risk.probability * 100} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span>Impact</span>
                        <span>{(risk.impact * 100).toFixed(0)}%</span>
                      </div>
                      <Progress value={risk.impact * 100} className="h-2" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Risk Recommendations */}
      <Alert>
        <CheckCircle className="h-4 w-4" />
        <AlertTitle>Risk Mitigation Recommendations</AlertTitle>
        <AlertDescription>
          <ul className="mt-2 space-y-1">
            <li className="text-sm">• Prioritize critical risks with immediate action plans</li>
            <li className="text-sm">• Implement monitoring for high-probability risks</li>
            <li className="text-sm">• Develop contingency plans for business continuity</li>
            <li className="text-sm">• Review and update risk assessments quarterly</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Predictive Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive organizational intelligence with AI-powered insights
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Time Range:</label>
            <select
              value={timeRangeFilter}
              onChange={(e) => setTimeRangeFilter(e.target.value)}
              className="px-3 py-1 border rounded-md text-sm"
            >
              <option value="3m">3 Months</option>
              <option value="6m">6 Months</option>
              <option value="12m">12 Months</option>
              <option value="24m">24 Months</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            Last refreshed: {lastRefresh.toLocaleTimeString()}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          <Button variant="outline" size="sm" onClick={() => onExportData?.('pdf')}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Predictive Accuracy</p>
                <p className="text-2xl font-bold">87.3%</p>
              </div>
              <Brain className="h-8 w-8 text-blue-600" />
            </div>
            <p className="text-xs text-blue-600 mt-2">↑ 3.2% from last month</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-green-50 to-green-100 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Active Interventions</p>
                <p className="text-2xl font-bold">{interventionEffectiveness.length}</p>
              </div>
              <Shield className="h-8 w-8 text-green-600" />
            </div>
            <p className="text-xs text-green-600 mt-2">85% average effectiveness</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">High-Potential Talent</p>
                <p className="text-2xl font-bold">{growthTrajectories.length}</p>
              </div>
              <Users className="h-8 w-8 text-purple-600" />
            </div>
            <p className="text-xs text-purple-600 mt-2">88% average potential score</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-orange-50 to-orange-100 border-orange-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Risk Level</p>
                <p className="text-2xl font-bold">Medium</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-600" />
            </div>
            <p className="text-xs text-orange-600 mt-2">{organizationalRisks.length} total risks identified</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="growth">Growth</TabsTrigger>
          <TabsTrigger value="interventions">Interventions</TabsTrigger>
          <TabsTrigger value="risks">Risks</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {renderOverviewTab()}
        </TabsContent>

        <TabsContent value="growth" className="space-y-4">
          {renderGrowthTab()}
        </TabsContent>

        <TabsContent value="interventions" className="space-y-4">
          {renderInterventionsTab()}
        </TabsContent>

        <TabsContent value="risks" className="space-y-4">
          {renderRisksTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default React.memo(PredictiveAnalyticsDashboard);
