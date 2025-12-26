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
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
} from 'recharts';
import {
  FlaskConical,
  Beaker,
  TestTube,
  TrendingUp,
  TrendingDown,
  Trophy,
  Target,
  Zap,
  Users,
  Activity,
  BarChart3,
  PieChartIcon,
  Star,
  Award,
  Crown,
  Rocket,
  Mic,
  Video,
  Brain,
  Settings,
  Play,
  Pause,
  Square,
  Eye,
  Download,
  Upload,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Clock,
  User,
  Filter,
  Calendar,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Volume2,
  Signal,
  Gauge,
  Sparkles,
  Gift,
  Medal,
  Flag,
  FlagTriangleRight,
} from 'lucide-react';

interface Experiment {
  experiment_id: string;
  name: string;
  description: string;
  status: string;
  test_type: string;
  start_date: string;
  duration_days: number;
  participants: number;
  variants: {
    control: { users: number, conversion_rate: number };
    treatment: { users: number, conversion_rate: number };
  };
  statistical_significance: boolean;
  winner?: string;
  business_impact: number;
}

interface GamificationProfile {
  current_level: number;
  total_points: number;
  current_streak: number;
  longest_streak: number;
  achievements: Array<{
    id: string;
    name: string;
    description: string;
    badge: string;
    points: number;
    earned_date: string;
  }>;
  badges: Array<{
    name: string;
    badge: string;
    earned_date: string;
  }>;
  leaderboard_rank: number;
  engagement_score: number;
}

interface VoiceAnalysisResult {
  analysis_id: string;
  audio_duration: number;
  sentiment_score: {
    positive: number;
    negative: number;
    neutral: number;
  };
  emotions: {
    joy: number;
    sadness: number;
    anger: number;
    fear: number;
    surprise: number;
    disgust: number;
  };
  speech_metrics: {
    words_per_minute: number;
    pause_duration: number;
    speech_clarity: number;
    volume_consistency: number;
  };
  confidence_score: number;
  engagement_level: number;
  stress_indicators: string[];
  recommendations: string[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const ExperimentalFeaturesLab: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedExperiment, setSelectedExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(false);

  // Mock data
  const [experiments, setExperiments] = useState<Experiment[]>([
    {
      experiment_id: 'exp_001',
      name: 'AI Assessment Algorithm Test',
      description: 'Testing new personality analysis algorithm vs. current version',
      status: 'running',
      test_type: 'algorithm_change',
      start_date: '2024-01-15',
      duration_days: 21,
      participants: 2450,
      variants: {
        control: { users: 1225, conversion_rate: 0.058 },
        treatment: { users: 1225, conversion_rate: 0.067 }
      },
      statistical_significance: false,
      business_impact: 15.5
    },
    {
      experiment_id: 'exp_002',
      name: 'Gamification Impact Study',
      description: 'Measuring engagement impact of new achievement system',
      status: 'completed',
      test_type: 'ui_variation',
      start_date: '2024-01-01',
      duration_days: 14,
      participants: 1820,
      variants: {
        control: { users: 910, conversion_rate: 0.042 },
        treatment: { users: 910, conversion_rate: 0.068 }
      },
      statistical_significance: true,
      winner: 'treatment',
      business_impact: 61.9
    },
    {
      experiment_id: 'exp_003',
      name: 'Voice Response Analysis',
      description: 'Testing voice sentiment analysis accuracy',
      status: 'draft',
      test_type: 'content_variation',
      start_date: '2024-02-01',
      duration_days: 30,
      participants: 0,
      variants: {
        control: { users: 0, conversion_rate: 0 },
        treatment: { users: 0, conversion_rate: 0 }
      },
      statistical_significance: false,
      business_impact: 0
    }
  ]);

  const [gamificationProfile, setGamificationProfile] = useState<GamificationProfile>({
    current_level: 12,
    total_points: 8750,
    current_streak: 5,
    longest_streak: 23,
    achievements: [
      {
        id: 'first_assessment',
        name: 'Assessment Pioneer',
        description: 'Complete your first psychological assessment',
        badge: '🎯',
        points: 100,
        earned_date: '2024-01-15'
      },
      {
        id: 'week_streak',
        name: 'Week Warrior',
        description: 'Maintain a 7-day activity streak',
        badge: '🔥',
        points: 500,
        earned_date: '2024-02-01'
      },
      {
        id: 'team_leader',
        name: 'Team Leader',
        description: 'Lead a team to top performance',
        badge: '👑',
        points: 750,
        earned_date: '2024-01-28'
      },
      {
        id: 'innovation_explorer',
        name: 'Innovation Explorer',
        description: 'Try experimental features and provide feedback',
        badge: '🚀',
        points: 300,
        earned_date: '2024-01-20'
      }
    ],
    badges: [
      {
        name: 'Level 10 - Experienced User',
        badge: '⭐',
        earned_date: '2024-01-30'
      },
      {
        name: 'Achievement Hunter',
        badge: '🏆',
        earned_date: '2024-02-01'
      }
    ],
    leaderboard_rank: 42,
    engagement_score: 0.78
  });

  const [voiceAnalysisResults, setVoiceAnalysisResults] = useState<VoiceAnalysisResult[]>([
    {
      analysis_id: 'voice_001',
      audio_duration: 45.2,
      sentiment_score: {
        positive: 0.65,
        negative: 0.15,
        neutral: 0.20
      },
      emotions: {
        joy: 0.35,
        sadness: 0.08,
        anger: 0.05,
        fear: 0.12,
        surprise: 0.18,
        disgust: 0.02
      },
      speech_metrics: {
        words_per_minute: 145.5,
        pause_duration: 0.8,
        speech_clarity: 0.82,
        volume_consistency: 0.75
      },
      confidence_score: 0.78,
      engagement_level: 0.72,
      stress_indicators: ['slightly_elevated_pitch', 'increased_speech_rate'],
      recommendations: [
        'Consider stress management techniques to improve vocal clarity',
        'Try to speak with more enthusiasm and variation in tone'
      ]
    }
  ]);

  const experimentMetrics = {
    total: experiments.length,
    running: experiments.filter(e => e.status === 'running').length,
    completed: experiments.filter(e => e.status === 'completed').length,
    draft: experiments.filter(e => e.status === 'draft').length
  };

  const experimentPerformanceData = experiments.map(exp => ({
    name: exp.name,
    control: exp.variants.control.conversion_rate * 100,
    treatment: exp.variants.treatment.conversion_rate * 100,
    participants: exp.participants,
    impact: exp.business_impact
  }));

  const emotionData = Object.entries(voiceAnalysisResults[0]?.emotions || {}).map(([emotion, score]) => ({
    name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
    value: score * 100,
    fill: COLORS[Object.keys(voiceAnalysisResults[0]?.emotions || {}).indexOf(emotion) % COLORS.length]
  }));

  const leaderboardData = [
    { rank: 1, name: 'Alex Chen', points: 15420, level: 25, badge: '👑' },
    { rank: 2, name: 'Sarah Johnson', points: 14200, level: 23, badge: '🏆' },
    { rank: 3, name: 'Mike Davis', points: 13800, level: 22, badge: '⭐' },
    { rank: 4, name: 'Emma Wilson', points: 12100, level: 20, badge: '🎯' },
    { rank: 5, name: 'You', points: 8750, level: 12, badge: '🔥' }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'completed': return 'bg-blue-500';
      case 'draft': return 'bg-gray-500';
      case 'paused': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  const getExperimentTypeIcon = (type: string) => {
    switch (type) {
      case 'algorithm_change': return <Brain className="h-4 w-4" />;
      case 'ui_variation': return <Eye className="h-4 w-4" />;
      case 'content_variation': return <MessageSquare className="h-4 w-4" />;
      case 'pricing_test': return <DollarSign className="h-4 w-4" />;
      default: return <Beaker className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <FlaskConical className="h-8 w-8 text-purple-500" />
            Experimental Features Lab
          </h1>
          <p className="text-muted-foreground">
            Innovation playground for A/B testing, gamification, and cutting-edge features
          </p>
        </div>
        <div className="flex gap-4">
          <Button variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            Lab Settings
          </Button>
          <Button className="gap-2">
            <Rocket className="h-4 w-4" />
            Start New Experiment
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="gap-2">
            <Activity className="h-4 w-4" />
            Lab Overview
          </TabsTrigger>
          <TabsTrigger value="ab-testing" className="gap-2">
            <TestTube className="h-4 w-4" />
            A/B Testing
          </TabsTrigger>
          <TabsTrigger value="gamification" className="gap-2">
            <Trophy className="h-4 w-4" />
            Gamification
          </TabsTrigger>
          <TabsTrigger value="voice-analysis" className="gap-2">
            <Mic className="h-4 w-4" />
            Voice Analysis
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Lab Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Experiments</CardTitle>
                <Beaker className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{experimentMetrics.running}</div>
                <p className="text-xs text-muted-foreground">
                  Currently running tests
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Lab Participants</CardTitle>
                <Users className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {experiments.reduce((acc, exp) => acc + exp.participants, 0).toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground">
                  Total experiment participants
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Business Impact</CardTitle>
                <TrendingUp className="h-4 w-4 text-purple-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">
                  {experiments.filter(e => e.business_impact > 0)
                    .reduce((acc, exp) => acc + exp.business_impact, 0) /
                    experiments.filter(e => e.business_impact > 0).length || 0}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Average performance lift
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Feature Adoption</CardTitle>
                <Sparkles className="h-4 w-4 text-orange-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">83%</div>
                <p className="text-xs text-muted-foreground">
                  Experimental features opt-in rate
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Experiment Results */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Experiment Performance</CardTitle>
              <CardDescription>
                Conversion rate comparison across recent experiments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={experimentPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="control" fill="#8884d8" name="Control Group %" />
                  <Bar dataKey="treatment" fill="#82ca9d" name="Treatment Group %" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Lab Status Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Experiment Status Overview</CardTitle>
                <CardDescription>
                  Current state of all laboratory experiments
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(experimentMetrics).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`} />
                        <span className="capitalize font-medium">{status}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">{count}</span>
                        <span className="text-sm text-muted-foreground">
                          ({((count / experimentMetrics.total) * 100).toFixed(0)}%)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  Common experimental feature actions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <Button variant="outline" className="h-20 flex flex-col gap-2">
                    <TestTube className="h-6 w-6" />
                    <span className="text-sm">Create Experiment</span>
                  </Button>
                  <Button variant="outline" className="h-20 flex flex-col gap-2">
                    <Trophy className="h-6 w-6" />
                    <span className="text-sm">View Achievements</span>
                  </Button>
                  <Button variant="outline" className="h-20 flex flex-col gap-2">
                    <Mic className="h-6 w-6" />
                    <span className="text-sm">Voice Test</span>
                  </Button>
                  <Button variant="outline" className="h-20 flex flex-col gap-2">
                    <BarChart3 className="h-6 w-6" />
                    <span className="text-sm">Analytics</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ab-testing" className="space-y-6">
          {/* Experiment Management */}
          <Card>
            <CardHeader>
              <CardTitle>Experiment Management</CardTitle>
              <CardDescription>
                Design, launch, and monitor A/B testing experiments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Experiment</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Participants</TableHead>
                    <TableHead>Performance</TableHead>
                    <TableHead>Business Impact</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {experiments.map((experiment) => (
                    <TableRow key={experiment.experiment_id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{experiment.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {experiment.description}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getExperimentTypeIcon(experiment.test_type)}
                          <span className="capitalize">{experiment.test_type.replace('_', ' ')}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(experiment.status)}>
                          <span className="capitalize">{experiment.status}</span>
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-center">
                          <div className="font-medium">{experiment.participants.toLocaleString()}</div>
                          <div className="text-xs text-muted-foreground">
                            Day {Math.floor((Date.now() - new Date(experiment.start_date).getTime()) / (1000 * 60 * 60 * 24))} / {experiment.duration_days}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="text-sm">
                            Control: {(experiment.variants.control.conversion_rate * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm">
                            Treatment: {(experiment.variants.treatment.conversion_rate * 100).toFixed(1)}%
                          </div>
                          {experiment.statistical_significance && (
                            <Badge variant="secondary" className="text-xs">
                              Statistically Significant
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className={`font-bold ${experiment.business_impact > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {experiment.business_impact > 0 ? '+' : ''}{experiment.business_impact.toFixed(1)}%
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setSelectedExperiment(experiment)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {experiment.status === 'draft' && (
                            <Button variant="outline" size="sm">
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          {experiment.status === 'running' && (
                            <Button variant="outline" size="sm">
                              <Pause className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Experiment Detail Dialog */}
          {selectedExperiment && (
            <Dialog open={!!selectedExperiment} onOpenChange={() => setSelectedExperiment(null)}>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>{selectedExperiment.name}</DialogTitle>
                  <DialogDescription>
                    Detailed experiment results and analysis
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-6">
                  {/* Performance Chart */}
                  <div>
                    <h4 className="font-semibold mb-4">Performance Comparison</h4>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={[
                        {
                          name: 'Control Group',
                          conversion: selectedExperiment.variants.control.conversion_rate * 100,
                          users: selectedExperiment.variants.control.users
                        },
                        {
                          name: 'Treatment Group',
                          conversion: selectedExperiment.variants.treatment.conversion_rate * 100,
                          users: selectedExperiment.variants.treatment.users
                        }
                      ]}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="conversion" fill="#8884d8" name="Conversion Rate %" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {selectedExperiment.participants.toLocaleString()}
                      </div>
                      <div className="text-sm text-muted-foreground">Total Participants</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {selectedExperiment.statistical_significance ? 'Yes' : 'No'}
                      </div>
                      <div className="text-sm text-muted-foreground">Statistically Significant</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {selectedExperiment.winner ? 'Yes' : 'No'}
                      </div>
                      <div className="text-sm text-muted-foreground">Clear Winner</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {selectedExperiment.business_impact.toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Business Impact</div>
                    </div>
                  </div>

                  {selectedExperiment.winner && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-2">🎉 Winner: {selectedExperiment.winner.toUpperCase()}</h4>
                      <p className="text-green-700">
                        The {selectedExperiment.winner} variant showed significantly better performance and is recommended for implementation.
                      </p>
                    </div>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          )}
        </TabsContent>

        <TabsContent value="gamification" className="space-y-6">
          {/* User Profile Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Crown className="h-5 w-5 text-yellow-500" />
                  Your Gamification Profile
                </CardTitle>
                <CardDescription>
                  Track your progress and achievements
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Level and Points */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">{gamificationProfile.current_level}</div>
                    <div className="text-sm text-muted-foreground">Current Level</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{gamificationProfile.total_points.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground">Total Points</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-600">{gamificationProfile.current_streak}</div>
                    <div className="text-sm text-muted-foreground">Day Streak</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">#{gamificationProfile.leaderboard_rank}</div>
                    <div className="text-sm text-muted-foreground">Leaderboard Rank</div>
                  </div>
                </div>

                {/* Engagement Score */}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Engagement Score</span>
                    <span className="text-sm text-muted-foreground">
                      {(gamificationProfile.engagement_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={gamificationProfile.engagement_score * 100} className="h-2" />
                </div>

                {/* Recent Achievements */}
                <div className="space-y-3">
                  <h4 className="font-semibold">Recent Achievements</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {gamificationProfile.achievements.map((achievement, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                        <div className="text-2xl">{achievement.badge}</div>
                        <div className="flex-1">
                          <div className="font-medium">{achievement.name}</div>
                          <div className="text-sm text-muted-foreground">{achievement.description}</div>
                          <div className="text-xs text-blue-600">+{achievement.points} points</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Badges Collection */}
                <div className="space-y-3">
                  <h4 className="font-semibold">Badge Collection</h4>
                  <div className="flex flex-wrap gap-3">
                    {gamificationProfile.badges.map((badge, index) => (
                      <div key={index} className="text-center p-3 border rounded-lg">
                        <div className="text-3xl mb-1">{badge.badge}</div>
                        <div className="text-xs font-medium">{badge.name}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Leaderboard */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  Leaderboard
                </CardTitle>
                <CardDescription>
                  Top performers this week
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {leaderboardData.map((player, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between p-3 rounded-lg ${
                        player.name === 'You' ? 'bg-blue-50 border border-blue-200' : 'border'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                          index === 0 ? 'bg-yellow-500' :
                          index === 1 ? 'bg-gray-400' :
                          index === 2 ? 'bg-orange-600' :
                          'bg-gray-300'
                        }`}>
                          {player.rank}
                        </div>
                        <div className="text-2xl">{player.badge}</div>
                        <div>
                          <div className="font-medium">{player.name}</div>
                          <div className="text-sm text-muted-foreground">Level {player.level}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{player.points.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">points</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Challenges and Goals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Target className="h-5 w-5 text-red-500" />
                Active Challenges
              </CardTitle>
              <CardDescription>
                Complete challenges to earn points and achievements
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full" />
                    <span className="font-medium">Daily Assessment</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Complete one assessment today</p>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Progress</span>
                      <span>1/1</span>
                    </div>
                    <Progress value={100} className="h-2" />
                  </div>
                  <div className="text-xs text-blue-600">+50 points • closes in 8h</div>
                </div>

                <div className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                    <span className="font-medium">Week Warrior</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Maintain 7-day streak</p>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Progress</span>
                      <span>5/7 days</span>
                    </div>
                    <Progress value={71} className="h-2" />
                  </div>
                  <div className="text-xs text-blue-600">+500 points • 2 days left</div>
                </div>

                <div className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-purple-500 rounded-full" />
                    <span className="font-medium">Experiment Explorer</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Try 3 experimental features</p>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>Progress</span>
                      <span>1/3</span>
                    </div>
                    <Progress value={33} className="h-2" />
                  </div>
                  <div className="text-xs text-blue-600">+300 points • 5 days left</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="voice-analysis" className="space-y-6">
          {/* Voice Analysis Interface */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Mic className="h-5 w-5 text-red-500" />
                  Voice Response Analysis
                </CardTitle>
                <CardDescription>
                  Record and analyze voice responses for emotional insights
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Recording Controls */}
                <div className="flex justify-center">
                  <div className="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center space-y-4">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                      <Mic className="h-8 w-8 text-red-500" />
                    </div>
                    <div>
                      <h4 className="font-semibold">Record Voice Response</h4>
                      <p className="text-sm text-muted-foreground">
                        Click to start recording up to 2 minutes
                      </p>
                    </div>
                    <div className="flex gap-3 justify-center">
                      <Button className="gap-2">
                        <Mic className="h-4 w-4" />
                        Start Recording
                      </Button>
                      <Button variant="outline" className="gap-2">
                        <Upload className="h-4 w-4" />
                        Upload Audio
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Analysis Options */}
                <div className="space-y-3">
                  <h4 className="font-semibold">Analysis Options</h4>
                  <div className="grid grid-cols-2 gap-2">
                    <label className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" defaultChecked />
                      <span className="text-sm">Sentiment Analysis</span>
                    </label>
                    <label className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" defaultChecked />
                      <span className="text-sm">Emotion Detection</span>
                    </label>
                    <label className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" defaultChecked />
                      <span className="text-sm">Speech Patterns</span>
                    </label>
                    <label className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" />
                      <span className="text-sm">Stress Detection</span>
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Analysis Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <BarChart3 className="h-5 w-5 text-blue-500" />
                  Recent Analysis Results
                </CardTitle>
                <CardDescription>
                  Latest voice analysis insights and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {voiceAnalysisResults.map((result, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-4">
                    <div className="flex justify-between items-center">
                      <h4 className="font-semibold">Analysis #{index + 1}</h4>
                      <Badge variant="outline">
                        {result.audio_duration.toFixed(1)}s duration
                      </Badge>
                    </div>

                    {/* Sentiment Score */}
                    <div className="space-y-2">
                      <h5 className="font-medium">Sentiment Analysis</h5>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div className="text-center p-2 bg-green-50 rounded">
                          <div className="text-green-600 font-bold">
                            {(result.sentiment_score.positive * 100).toFixed(0)}%
                          </div>
                          <div className="text-green-700">Positive</div>
                        </div>
                        <div className="text-center p-2 bg-gray-50 rounded">
                          <div className="text-gray-600 font-bold">
                            {(result.sentiment_score.neutral * 100).toFixed(0)}%
                          </div>
                          <div className="text-gray-700">Neutral</div>
                        </div>
                        <div className="text-center p-2 bg-red-50 rounded">
                          <div className="text-red-600 font-bold">
                            {(result.sentiment_score.negative * 100).toFixed(0)}%
                          </div>
                          <div className="text-red-700">Negative</div>
                        </div>
                      </div>
                    </div>

                    {/* Emotional Profile */}
                    <div className="space-y-2">
                      <h5 className="font-medium">Emotional Profile</h5>
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie
                            data={emotionData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {emotionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="space-y-1">
                        <span className="text-muted-foreground">Confidence Score</span>
                        <div className="flex items-center gap-2">
                          <Progress value={result.confidence_score * 100} className="flex-1 h-2" />
                          <span className="font-medium">
                            {(result.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <span className="text-muted-foreground">Engagement Level</span>
                        <div className="flex items-center gap-2">
                          <Progress value={result.engagement_level * 100} className="flex-1 h-2" />
                          <span className="font-medium">
                            {(result.engagement_level * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Recommendations */}
                    <div className="space-y-2">
                      <h5 className="font-medium">Recommendations</h5>
                      <div className="space-y-1">
                        {result.recommendations.map((rec, idx) => (
                          <div key={idx} className="text-sm p-2 bg-blue-50 rounded flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />
                            {rec}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Voice Analytics Dashboard */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Gauge className="h-5 w-5 text-purple-500" />
                Voice Analytics Dashboard
              </CardTitle>
              <CardDescription>
                Platform-wide voice analysis statistics and trends
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">12,580</div>
                  <div className="text-sm text-muted-foreground">Total Analyses</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">76%</div>
                  <div className="text-sm text-muted-foreground">Avg. Confidence</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">2.3s</div>
                  <div className="text-sm text-muted-foreground">Avg. Duration</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">84%</div>
                  <div className="text-sm text-muted-foreground">User Satisfaction</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExperimentalFeaturesLab;