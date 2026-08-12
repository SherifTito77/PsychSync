import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Progress from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  LineChart,
  Line,
  Treemap,
} from 'recharts';
import {
  Users,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Award,
  Briefcase,
  UserCheck,
  UserX,
  Building,
  DollarSign,
  Brain,
  Zap,
  Shield,
  Activity,
  BarChart3,
  PieChartIcon,
  Star,
  ArrowUp,
  ArrowDown,
  Eye,
  Calendar,
  FileText,
  Settings,
  Lightbulb,
  Heart,
  GraduationCap,
  Rocket,
  Crown,
  Flag,
  FlagTriangleRight,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

interface PipelineAnalysis {
  pipeline_level: string;
  total_positions: number;
  ready_candidates: number;
  gap_percentage: number;
  bench_strength: number;
  risk_level: string;
  development_recommendations: string[];
}

interface SuccessionCandidate {
  candidate: {
    user_id: string;
    current_role: string;
    readiness_level: string;
    readiness_score: number;
    leadership_potential: number;
    mobility_score: number;
    risk_score: number;
    promotion_timeline: number;
    retention_risk: number;
  };
  target_role: {
    role_name: string;
    level: string;
    department: string;
  };
  match_score: number;
  success_probability: number;
  gap_analysis: Record<string, number>;
}

interface SuccessionScenario {
  scenario_name: string;
  timeline_months: number;
  readiness_status: string;
  business_impact: Record<string, number>;
  financial_risk: number;
  operational_risk: number;
  required_actions: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#8DD1E1'];

const SuccessionPlanning: React.FC = () => {
  const [activeTab, setActiveTab] = useState('pipeline');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [selectedRole, setSelectedRole] = useState('all');
  const [loading, setLoading] = useState(false);
  const [timeHorizon, setTimeHorizon] = useState('24');

  // Mock data - would come from API
  const [pipelineAnalysis, setPipelineAnalysis] = useState<PipelineAnalysis[]>([
    {
      pipeline_level: 'Executive',
      total_positions: 5,
      ready_candidates: 2,
      gap_percentage: 60,
      bench_strength: 40,
      risk_level: 'HIGH',
      development_recommendations: [
        'Accelerated leadership program',
        'Executive coaching initiatives',
        'Cross-functional exposure'
      ]
    },
    {
      pipeline_level: 'Senior Management',
      total_positions: 12,
      ready_candidates: 7,
      gap_percentage: 42,
      bench_strength: 58,
      risk_level: 'MEDIUM',
      development_recommendations: [
        'Strategic thinking workshops',
        'Mentorship programs',
        'External training initiatives'
      ]
    },
    {
      pipeline_level: 'Middle Management',
      total_positions: 28,
      ready_candidates: 22,
      gap_percentage: 21,
      bench_strength: 79,
      risk_level: 'LOW',
      development_recommendations: [
        'Leadership fundamentals training',
        'Team development programs',
        'Performance management skills'
      ]
    },
    {
      pipeline_level: 'Team Lead',
      total_positions: 45,
      ready_candidates: 38,
      gap_percentage: 16,
      bench_strength: 84,
      risk_level: 'LOW',
      development_recommendations: [
        'First-time manager training',
        'Communication skills development',
        'Project management certification'
      ]
    }
  ]);

  const [successionCandidates, setSuccessionCandidates] = useState<SuccessionCandidate[]>([
    {
      candidate: {
        user_id: 'user_001',
        current_role: 'Senior Engineering Manager',
        readiness_level: 'READY_1_2_YEARS',
        readiness_score: 85,
        leadership_potential: 0.92,
        mobility_score: 0.9,
        risk_score: 15,
        promotion_timeline: 18,
        retention_risk: 20
      },
      target_role: {
        role_name: 'Director of Engineering',
        level: 'Senior Management',
        department: 'Technology'
      },
      match_score: 88,
      success_probability: 0.85,
      gap_analysis: {
        strategic_thinking: 15,
        financial_acumen: 25,
        stakeholder_management: 10
      }
    },
    {
      candidate: {
        user_id: 'user_002',
        current_role: 'Director of Product',
        readiness_level: 'READY_NOW',
        readiness_score: 95,
        leadership_potential: 0.96,
        mobility_score: 0.8,
        risk_score: 8,
        promotion_timeline: 0,
        retention_risk: 15
      },
      target_role: {
        role_name: 'VP of Product',
        level: 'Executive',
        department: 'Product'
      },
      match_score: 94,
      success_probability: 0.92,
      gap_analysis: {
        board_relations: 12,
        investor_relations: 18
      }
    },
    {
      candidate: {
        user_id: 'user_003',
        current_role: 'Senior Manager',
        readiness_level: 'READY_3_5_YEARS',
        readiness_score: 72,
        leadership_potential: 0.85,
        mobility_score: 0.95,
        risk_score: 28,
        promotion_timeline: 36,
        retention_risk: 35
      },
      target_role: {
        role_name: 'Director of Operations',
        level: 'Senior Management',
        department: 'Operations'
      },
      match_score: 76,
      success_probability: 0.68,
      gap_analysis: {
        strategic_thinking: 22,
        change_management: 18,
        financial_acumen: 30
      }
    }
  ]);

  const [scenarios, setScenarios] = useState<SuccessionScenario[]>([
    {
      scenario_name: 'CEO Transition',
      timeline_months: 12,
      readiness_status: 'AT_RISK',
      business_impact: {
        continuity_risk: 75,
        market_confidence: -15,
        team_stability: -20
      },
      financial_risk: 0.65,
      operational_risk: 0.72,
      required_actions: [
        'Accelerate successor development',
        'Implement interim leadership plan',
        'Enhance board communication'
      ]
    },
    {
      scenario_name: 'CTO Departure',
      timeline_months: 6,
      readiness_status: 'MANAGEABLE',
      business_impact: {
        continuity_risk: 35,
        innovation_velocity: -25,
        team_morale: -15
      },
      financial_risk: 0.42,
      operational_risk: 0.38,
      required_actions: [
        'Identify internal candidates',
        'Engage external search firm',
        'Knowledge transfer planning'
      ]
    }
  ]);

  useEffect(() => {
    const loadPipeline = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        const res = await fetch('/api/v1/succession/pipeline', {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (res.ok) {
          const data = await res.json();
          if (data.pipeline?.length) setPipelineAnalysis(data.pipeline);
        }
      } catch {
        // Keep mock initial state on error
      }
    };
    loadPipeline();
  }, []);

  const pipelineChartData = pipelineAnalysis.map(pipeline => ({
    name: pipeline.pipeline_level,
    total: pipeline.total_positions,
    ready: pipeline.ready_candidates,
    gap: pipeline.gap_percentage,
    bench_strength: pipeline.bench_strength
  }));

  const riskLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'text-red-600 bg-red-50';
      case 'HIGH': return 'text-orange-600 bg-orange-50';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50';
      case 'LOW': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const readinessLevelColor = (level: string) => {
    switch (level) {
      case 'READY_NOW': return 'bg-green-500';
      case 'READY_1_2_YEARS': return 'bg-blue-500';
      case 'READY_3_5_YEARS': return 'bg-yellow-500';
      case 'POTENTIAL': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const getReadinessLabel = (level: string) => {
    switch (level) {
      case 'READY_NOW': return 'Ready Now';
      case 'READY_1_2_YEARS': return 'Ready 1-2 Years';
      case 'READY_3_5_YEARS': return 'Ready 3-5 Years';
      case 'POTENTIAL': return 'Potential';
      default: return 'Not Ready';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const overallBenchStrength = pipelineAnalysis.reduce(
    (acc, pipeline) => acc + pipeline.bench_strength, 0
  ) / pipelineAnalysis.length;

  const highRiskLevels = pipelineAnalysis.filter(
    pipeline => pipeline.risk_level in ['CRITICAL', 'HIGH']
  ).length;

  const totalGapPositions = pipelineAnalysis.reduce(
    (acc, pipeline) => acc + Math.floor((pipeline.gap_percentage / 100) * pipeline.total_positions),
    0
  );

  const riskData = pipelineAnalysis.map(pipeline => ({
    name: pipeline.pipeline_level,
    gap: pipeline.gap_percentage,
    bench_strength: pipeline.bench_strength,
    risk: pipeline.risk_level === 'CRITICAL' ? 100 :
          pipeline.risk_level === 'HIGH' ? 75 :
          pipeline.risk_level === 'MEDIUM' ? 50 : 25
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Succession Planning</h1>
          <p className="text-muted-foreground">
            Strategic leadership pipeline development and risk management
          </p>
        </div>
        <div className="flex gap-4">
          <Select value={timeHorizon} onValueChange={setTimeHorizon}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="12">12 months</SelectItem>
              <SelectItem value="24">24 months</SelectItem>
              <SelectItem value="36">36 months</SelectItem>
              <SelectItem value="60">5 years</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="gap-2">
            <FileText className="h-4 w-4" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Bench Strength</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {overallBenchStrength.toFixed(0)}%
            </div>
            <Progress value={overallBenchStrength} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              Average readiness across all levels
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">High-Risk Levels</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {highRiskLevels}
            </div>
            <p className="text-xs text-muted-foreground">
              Pipeline levels requiring attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Talent Gaps</CardTitle>
            <UserX className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {totalGapPositions}
            </div>
            <p className="text-xs text-muted-foreground">
              Positions without ready successors
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ready Candidates</CardTitle>
            <UserCheck className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {pipelineAnalysis.reduce((acc, p) => acc + p.ready_candidates, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Candidates ready for promotion
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pipeline" className="gap-2">
            <Users className="h-4 w-4" />
            Leadership Pipeline
          </TabsTrigger>
          <TabsTrigger value="candidates" className="gap-2">
            <Target className="h-4 w-4" />
            Succession Candidates
          </TabsTrigger>
          <TabsTrigger value="scenarios" className="gap-2">
            <Activity className="h-4 w-4" />
            Risk Scenarios
          </TabsTrigger>
          <TabsTrigger value="development" className="gap-2">
            <GraduationCap className="h-4 w-4" />
            Development Programs
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline" className="space-y-6">
          {/* Pipeline Strength Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Pipeline Strength Analysis</CardTitle>
                <CardDescription>
                  Current bench strength across leadership levels
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={pipelineChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="bench_strength" fill="#8884d8" name="Bench Strength %" />
                    <Bar dataKey="gap" fill="#ff7c7c" name="Gap %" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Assessment by Level</CardTitle>
                <CardDescription>
                  Risk profile across leadership pipeline
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={riskData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="name" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Risk Score"
                      dataKey="risk"
                      stroke="#ff7c7c"
                      fill="#ff7c7c"
                      fillOpacity={0.6}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Pipeline Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Pipeline Analysis</CardTitle>
              <CardDescription>
                Comprehensive breakdown of leadership readiness at each level
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {pipelineAnalysis.map((pipeline, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-full">
                          <Building className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{pipeline.pipeline_level}</h3>
                          <p className="text-sm text-muted-foreground">
                            {pipeline.total_positions} total positions
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge className={riskLevelColor(pipeline.risk_level)}>
                          {pipeline.risk_level} RISK
                        </Badge>
                        <div className="text-right">
                          <div className="text-lg font-bold">
                            {pipeline.bench_strength.toFixed(0)}%
                          </div>
                          <div className="text-sm text-muted-foreground">Bench Strength</div>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Ready Candidates</span>
                          <span>{pipeline.ready_candidates} / {pipeline.total_positions}</span>
                        </div>
                        <Progress
                          value={(pipeline.ready_candidates / pipeline.total_positions) * 100}
                          className="h-2"
                        />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Gap Percentage</span>
                          <span>{pipeline.gap_percentage.toFixed(0)}%</span>
                        </div>
                        <Progress
                          value={pipeline.gap_percentage}
                          className="h-2"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="font-medium text-sm">Development Recommendations:</h4>
                      <div className="flex flex-wrap gap-2">
                        {pipeline.development_recommendations.map((rec, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {rec}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="candidates" className="space-y-6">
          {/* Succession Candidates Table */}
          <Card>
            <CardHeader>
              <CardTitle>Succession Candidate Pool</CardTitle>
              <CardDescription>
                Top candidates for key leadership positions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Candidate</TableHead>
                    <TableHead>Current Role</TableHead>
                    <TableHead>Target Role</TableHead>
                    <TableHead>Readiness</TableHead>
                    <TableHead>Match Score</TableHead>
                    <TableHead>Success Probability</TableHead>
                    <TableHead>Timeline</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {successionCandidates.map((candidate, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="p-2 bg-blue-100 rounded-full">
                            <UserCheck className="h-4 w-4 text-blue-600" />
                          </div>
                          <div>
                            <div className="font-medium">User #{candidate.candidate.user_id}</div>
                            <div className="text-sm text-muted-foreground">
                              Potential: {(candidate.candidate.leadership_potential * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{candidate.candidate.current_role}</TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{candidate.target_role.role_name}</div>
                          <div className="text-sm text-muted-foreground">{candidate.target_role.department}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${readinessLevelColor(candidate.candidate.readiness_level)}`} />
                            <span className="text-sm">
                              {getReadinessLabel(candidate.candidate.readiness_level)}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {candidate.candidate.readiness_score}% ready
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={candidate.match_score} className="w-12 h-2" />
                          <span className="text-sm font-medium">{candidate.match_score}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={candidate.success_probability * 100} className="w-12 h-2" />
                          <span className="text-sm font-medium">
                            {(candidate.success_probability * 100).toFixed(0)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {candidate.candidate.promotion_timeline === 0 ? (
                            <Badge variant="default">Ready Now</Badge>
                          ) : (
                            `${candidate.candidate.promotion_timeline} months`
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger >
                            <Button variant="outline" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle>Candidate Succession Profile</DialogTitle>
                              <DialogDescription>
                                Detailed analysis for succession planning
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-6">
                              {/* Candidate Overview */}
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="space-y-2">
                                  <div className="text-sm text-muted-foreground">Readiness Score</div>
                                  <div className="text-2xl font-bold">
                                    {candidate.candidate.readiness_score}%
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <div className="text-sm text-muted-foreground">Leadership Potential</div>
                                  <div className="text-2xl font-bold">
                                    {(candidate.candidate.leadership_potential * 100).toFixed(0)}%
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <div className="text-sm text-muted-foreground">Mobility Score</div>
                                  <div className="text-2xl font-bold">
                                    {(candidate.candidate.mobility_score * 100).toFixed(0)}%
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <div className="text-sm text-muted-foreground">Risk Score</div>
                                  <div className="text-2xl font-bold text-red-600">
                                    {candidate.candidate.risk_score}
                                  </div>
                                </div>
                              </div>

                              {/* Competency Gaps */}
                              <div className="space-y-3">
                                <h4 className="font-semibold">Competency Gap Analysis</h4>
                                <div className="space-y-2">
                                  {Object.entries(candidate.gap_analysis).map(([competency, gap]) => (
                                    <div key={competency} className="flex justify-between items-center">
                                      <span className="text-sm capitalize">
                                        {competency.replace('_', ' ')}
                                      </span>
                                      <div className="flex items-center gap-2">
                                        <Progress value={gap} className="w-16 h-2" />
                                        <span className="text-sm font-medium">-{gap}%</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {/* Development Actions */}
                              <div className="space-y-3">
                                <h4 className="font-semibold">Recommended Actions</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div className="p-3 border rounded-lg">
                                    <div className="flex items-center gap-2 mb-2">
                                      <GraduationCap className="h-4 w-4 text-blue-500" />
                                      <span className="font-medium">Development Plan</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      Customized learning program to address competency gaps
                                    </p>
                                  </div>
                                  <div className="p-3 border rounded-lg">
                                    <div className="flex items-center gap-2 mb-2">
                                      <Briefcase className="h-4 w-4 text-green-500" />
                                      <span className="font-medium">Stretch Assignment</span>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                      Cross-functional project to build critical experience
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scenarios" className="space-y-6">
          {/* Risk Scenarios */}
          <div className="space-y-6">
            {scenarios.map((scenario, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <FlagTriangleRight className="h-5 w-5" />
                    {scenario.scenario_name}
                  </CardTitle>
                  <CardDescription>
                    Risk assessment and mitigation strategies
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Scenario Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-blue-500" />
                        <span className="text-sm font-medium">Timeline</span>
                      </div>
                      <div className="text-2xl font-bold">
                        {scenario.timeline_months} months
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-orange-500" />
                        <span className="text-sm font-medium">Financial Risk</span>
                      </div>
                      <div className="text-2xl font-bold text-orange-600">
                        {(scenario.financial_risk * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Activity className="h-4 w-4 text-red-500" />
                        <span className="text-sm font-medium">Operational Risk</span>
                      </div>
                      <div className="text-2xl font-bold text-red-600">
                        {(scenario.operational_risk * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Business Impact */}
                  <div className="space-y-3">
                    <h4 className="font-semibold">Business Impact Analysis</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(scenario.business_impact).map(([impact, value]) => (
                        <div key={impact} className="p-3 border rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium capitalize">
                              {impact.replace('_', ' ')}
                            </span>
                            <div className={`flex items-center gap-1 text-sm font-bold ${
                              value > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {value > 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                              {Math.abs(value)}%
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Required Actions */}
                  <div className="space-y-3">
                    <h4 className="font-semibold">Required Actions</h4>
                    <div className="space-y-2">
                      {scenario.required_actions.map((action, idx) => (
                        <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-sm">{action}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Readiness Status */}
                  <div className="flex items-center justify-between p-4 border rounded-lg bg-gray-50">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${
                        scenario.readiness_status === 'READY' ? 'bg-green-100' :
                        scenario.readiness_status === 'MANAGEABLE' ? 'bg-yellow-100' :
                        'bg-red-100'
                      }`}>
                        <ShieldCheck className={`h-4 w-4 ${
                          scenario.readiness_status === 'READY' ? 'text-green-600' :
                          scenario.readiness_status === 'MANAGEABLE' ? 'text-yellow-600' :
                          'text-red-600'
                        }`} />
                      </div>
                      <div>
                        <div className="font-medium">Readiness Status</div>
                        <div className="text-sm text-muted-foreground">
                          Current state of succession preparedness
                        </div>
                      </div>
                    </div>
                    <Badge variant={
                      scenario.readiness_status === 'READY' ? 'default' :
                      scenario.readiness_status === 'MANAGEABLE' ? 'secondary' :
                      'error'
                    }>
                      {scenario.readiness_status.replace('_', ' ')}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="development" className="space-y-6">
          {/* Development Programs */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Accelerated Leadership Program */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Rocket className="h-5 w-5 text-red-500" />
                  Accelerated Leadership Program
                </CardTitle>
                <CardDescription>
                  Intensive development for high-risk succession gaps
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <div className="font-medium">12 months</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Participants:</span>
                    <div className="font-medium">8 candidates</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Investment:</span>
                    <div className="font-medium">$120,000</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Expected ROI:</span>
                    <div className="font-medium text-green-600">280%</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <h5 className="font-medium">Key Components:</h5>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Executive coaching (1:1)</li>
                    <li>• Strategic project assignments</li>
                    <li>• Cross-functional rotations</li>
                    <li>• Board exposure opportunities</li>
                  </ul>
                </div>
                <Button className="w-full">Launch Program</Button>
              </CardContent>
            </Card>

            {/* Emerging Leaders Program */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Sparkles className="h-5 w-5 text-blue-500" />
                  Emerging Leaders Program
                </CardTitle>
                <CardDescription>
                  Development for high-potential middle management
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <div className="font-medium">18 months</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Participants:</span>
                    <div className="font-medium">15 candidates</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Investment:</span>
                    <div className="font-medium">$85,000</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Expected ROI:</span>
                    <div className="font-medium text-green-600">195%</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <h5 className="font-medium">Key Components:</h5>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Leadership fundamentals training</li>
                    <li>• Mentorship pairing</li>
                    <li>• Team management practice</li>
                    <li>• Communication skills development</li>
                  </ul>
                </div>
                <Button className="w-full">Launch Program</Button>
              </CardContent>
            </Card>

            {/* Technical Leadership Track */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Brain className="h-5 w-5 text-purple-500" />
                  Technical Leadership Track
                </CardTitle>
                <CardDescription>
                  Specialized development for technical senior leaders
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <div className="font-medium">15 months</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Participants:</span>
                    <div className="font-medium">12 candidates</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Investment:</span>
                    <div className="font-medium">$95,000</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Expected ROI:</span>
                    <div className="font-medium text-green-600">220%</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <h5 className="font-medium">Key Components:</h5>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Advanced technical architecture</li>
                    <li>• Technology strategy development</li>
                    <li>• Innovation management</li>
                    <li>• Technical talent development</li>
                  </ul>
                </div>
                <Button className="w-full">Launch Program</Button>
              </CardContent>
            </Card>

            {/* Executive Preparation Program */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Crown className="h-5 w-5 text-yellow-500" />
                  Executive Preparation Program
                </CardTitle>
                <CardDescription>
                  Comprehensive C-suite readiness development
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Duration:</span>
                    <div className="font-medium">24 months</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Participants:</span>
                    <div className="font-medium">5 candidates</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Investment:</span>
                    <div className="font-medium">$200,000</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Expected ROI:</span>
                    <div className="font-medium text-green-600">350%</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <h5 className="font-medium">Key Components:</h5>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• Board relations training</li>
                    <li>• Investor communication skills</li>
                    <li>• Strategic decision-making</li>
                    <li>• Global business acumen</li>
                  </ul>
                </div>
                <Button className="w-full">Launch Program</Button>
              </CardContent>
            </Card>
          </div>

          {/* Development Program Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Development Program Portfolio</CardTitle>
              <CardDescription>
                Comprehensive overview of all leadership development initiatives
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">4</div>
                  <div className="text-sm text-muted-foreground">Active Programs</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">40</div>
                  <div className="text-sm text-muted-foreground">Total Participants</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">$500K</div>
                  <div className="text-sm text-muted-foreground">Total Investment</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">262%</div>
                  <div className="text-sm text-muted-foreground">Average ROI</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SuccessionPlanning;
