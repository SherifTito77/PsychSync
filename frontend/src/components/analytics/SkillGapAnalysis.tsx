import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
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
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Treemap,
  ScatterChart,
  Scatter,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  BookOpen,
  Award,
  Users,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  GraduationCap,
  Briefcase,
  Star,
  Zap,
  Activity,
  BarChart3,
  PieChartIcon,
  LineChartIcon,
} from 'lucide-react';

interface SkillAssessment {
  skillName: string;
  category: string;
  currentLevel: number;
  requiredLevel: number;
  gapPercentage: number;
  priority: string;
  assessmentDate: string;
  confidenceScore: number;
}

interface SkillDemand {
  skillName: string;
  category: string;
  currentDemand: number;
  predictedDemand12m: number;
  predictedDemand24m: number;
  growthRate: number;
  marketTrend: string;
  industryRelevance: number;
}

interface LearningRecommendation {
  skillName: string;
  learningStyle: string;
  recommendedResources: Array<{
    name: string;
    provider: string;
    duration: number;
    cost: number;
    style: string;
  }>;
  estimatedDuration: number;
  difficultyLevel: string;
  completionProbability: number;
  expectedImprovement: number;
  costEstimate: number;
}

interface DevelopmentProgram {
  programName: string;
  targetSkills: string[];
  durationWeeks: number;
  deliveryMethod: string;
  provider: string;
  estimatedCost: number;
  expectedRoi: number;
  successRate: number;
  prerequisites: string[];
}

interface CareerTrajectory {
  currentRole: string;
  targetRole: string;
  timeToPromotion: number;
  requiredSkills: Array<{
    skill: string;
    currentLevel: number;
    requiredLevel: number;
    gap: number;
  }>;
  skillDevelopmentPlan: LearningRecommendation[];
  promotionProbability: number;
  salaryImpact: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const SkillGapAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('individual');
  const [selectedUser, setSelectedUser] = useState('current');
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState('24');

  // Mock data - would come from API
  const [skillAssessments, setSkillAssessments] = useState<SkillAssessment[]>([
    {
      skillName: 'Leadership',
      category: 'leadership',
      currentLevel: 65,
      requiredLevel: 85,
      gapPercentage: 23.5,
      priority: 'high',
      assessmentDate: '2024-01-15',
      confidenceScore: 0.85,
    },
    {
      skillName: 'AI/ML',
      category: 'technical',
      currentLevel: 45,
      requiredLevel: 75,
      gapPercentage: 40.0,
      priority: 'critical',
      assessmentDate: '2024-01-15',
      confidenceScore: 0.78,
    },
    {
      skillName: 'Communication',
      category: 'soft_skills',
      currentLevel: 78,
      requiredLevel: 85,
      gapPercentage: 8.2,
      priority: 'medium',
      assessmentDate: '2024-01-15',
      confidenceScore: 0.92,
    },
    {
      skillName: 'Cloud Computing',
      category: 'technical',
      currentLevel: 52,
      requiredLevel: 70,
      gapPercentage: 25.7,
      priority: 'high',
      assessmentDate: '2024-01-15',
      confidenceScore: 0.81,
    },
    {
      skillName: 'Strategic Thinking',
      category: 'leadership',
      currentLevel: 58,
      requiredLevel: 80,
      gapPercentage: 27.5,
      priority: 'high',
      assessmentDate: '2024-01-15',
      confidenceScore: 0.75,
    },
  ]);

  const [skillDemands, setSkillDemands] = useState<SkillDemand[]>([
    {
      skillName: 'AI/ML',
      category: 'technical',
      currentDemand: 75,
      predictedDemand12m: 90,
      predictedDemand24m: 108,
      growthRate: 0.25,
      marketTrend: 'growing',
      industryRelevance: 0.95,
    },
    {
      skillName: 'Leadership',
      category: 'leadership',
      currentDemand: 85,
      predictedDemand12m: 91,
      predictedDemand24m: 98,
      growthRate: 0.10,
      marketTrend: 'growing',
      industryRelevance: 0.88,
    },
    {
      skillName: 'Cloud Computing',
      category: 'technical',
      currentDemand: 70,
      predictedDemand24m: 87,
      predictedDemand12m: 78,
      growthRate: 0.15,
      marketTrend: 'growing',
      industryRelevance: 0.92,
    },
  ]);

  const [learningRecommendations, setLearningRecommendations] = useState<LearningRecommendation[]>([
    {
      skillName: 'AI/ML',
      learningStyle: 'visual',
      recommendedResources: [
        {
          name: 'Machine Learning Specialization',
          provider: 'Coursera',
          duration: 12,
          cost: 79,
          style: 'visual',
        },
        {
          name: 'Hands-on Deep Learning',
          provider: 'Udemy',
          duration: 8,
          cost: 89,
          style: 'kinesthetic',
        },
      ],
      estimatedDuration: 90,
      difficultyLevel: 'intermediate',
      completionProbability: 0.85,
      expectedImprovement: 65,
      costEstimate: 168,
    },
    {
      skillName: 'Leadership',
      learningStyle: 'mixed',
      recommendedResources: [
        {
          name: 'Leadership Essentials Program',
          provider: 'Internal Training',
          duration: 6,
          cost: 0,
          style: 'mixed',
        },
        {
          name: 'Executive Coaching',
          provider: 'External Coach',
          duration: 12,
          cost: 5000,
          style: 'auditory',
        },
      ],
      estimatedDuration: 60,
      difficultyLevel: 'advanced',
      completionProbability: 0.92,
      expectedImprovement: 70,
      costEstimate: 2500,
    },
  ]);

  const [careerTrajectories, setCareerTrajectories] = useState<CareerTrajectory[]>([
    {
      currentRole: 'Senior Developer',
      targetRole: 'Engineering Manager',
      timeToPromotion: 18,
      requiredSkills: [
        { skill: 'Leadership', currentLevel: 65, requiredLevel: 90, gap: 25 },
        { skill: 'Strategic Thinking', currentLevel: 58, requiredLevel: 85, gap: 27 },
        { skill: 'Team Development', currentLevel: 70, requiredLevel: 88, gap: 18 },
      ],
      skillDevelopmentPlan: learningRecommendations,
      promotionProbability: 0.75,
      salaryImpact: 35000,
    },
    {
      currentRole: 'Senior Developer',
      targetRole: 'Principal Engineer',
      timeToPromotion: 12,
      requiredSkills: [
        { skill: 'AI/ML', currentLevel: 45, requiredLevel: 85, gap: 40 },
        { skill: 'System Architecture', currentLevel: 72, requiredLevel: 95, gap: 23 },
        { skill: 'Technical Leadership', currentLevel: 68, requiredLevel: 90, gap: 22 },
      ],
      skillDevelopmentPlan: learningRecommendations,
      promotionProbability: 0.82,
      salaryImpact: 28000,
    },
  ]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getPriorityBadgeVariant = (priority: string) => {
    switch (priority) {
      case 'critical': return 'destructive';
      case 'high': return 'secondary';
      case 'medium': return 'outline';
      case 'low': return 'default';
      default: return 'outline';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const gapAnalysisData = skillAssessments.map(assessment => ({
    name: assessment.skillName,
    current: assessment.currentLevel,
    required: assessment.requiredLevel,
    gap: assessment.gapPercentage,
  }));

  const categoryDistribution = skillAssessments.reduce((acc, assessment) => {
    acc[assessment.category] = (acc[assessment.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const categoryData = Object.entries(categoryDistribution).map(([category, count]) => ({
    name: category,
    value: count,
  }));

  const radarData = skillAssessments.map(assessment => ({
    skill: assessment.skillName,
    current: assessment.currentLevel,
    required: assessment.requiredLevel,
  }));

  const demandGrowthData = skillDemands.map(demand => ({
    name: demand.skillName,
    current: demand.currentDemand,
    projected: demand.predictedDemand24m,
    growth: demand.growthRate * 100,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Skill Gap Analysis</h1>
          <p className="text-muted-foreground">
            Identify skill gaps and create personalized development plans
          </p>
        </div>
        <div className="flex gap-4">
          <Select value={selectedUser} onValueChange={setSelectedUser}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select user" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="current">Current User</SelectItem>
              <SelectItem value="team">My Team</SelectItem>
              <SelectItem value="organization">Organization</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="gap-2">
            <Activity className="h-4 w-4" />
            Generate Report
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="individual" className="gap-2">
            <Users className="h-4 w-4" />
            Individual Analysis
          </TabsTrigger>
          <TabsTrigger value="organization" className="gap-2">
            <Briefcase className="h-4 w-4" />
            Organization View
          </TabsTrigger>
          <TabsTrigger value="development" className="gap-2">
            <BookOpen className="h-4 w-4" />
            Development Plans
          </TabsTrigger>
          <TabsTrigger value="career" className="gap-2">
            <GraduationCap className="h-4 w-4" />
            Career Paths
          </TabsTrigger>
        </TabsList>

        <TabsContent value="individual" className="space-y-6">
          {/* Skills Gap Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Critical Skills Gap</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {skillAssessments.filter(s => s.priority === 'critical').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  Skills requiring immediate attention
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">High Priority Gaps</CardTitle>
                <TrendingUp className="h-4 w-4 text-orange-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {skillAssessments.filter(s => s.priority === 'high').length}
                </div>
                <p className="text-xs text-muted-foreground">
                  Skills needing development soon
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Gap Size</CardTitle>
                <BarChart3 className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {(skillAssessments.reduce((acc, s) => acc + s.gapPercentage, 0) / skillAssessments.length).toFixed(1)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Average improvement needed
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Skill Gap Comparison Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Skill Gap Analysis</CardTitle>
                <CardDescription>
                  Current vs. required skill levels
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={gapAnalysisData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="current" fill="#8884d8" name="Current Level" />
                    <Bar dataKey="required" fill="#82ca9d" name="Required Level" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Skill Radar</CardTitle>
                <CardDescription>
                  Comprehensive skill profile comparison
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="skill" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Current"
                      dataKey="current"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="Required"
                      dataKey="required"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.6}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Skills Assessment */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Skills Assessment</CardTitle>
              <CardDescription>
                Comprehensive breakdown of skill gaps with priority levels
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {skillAssessments.map((assessment, index) => (
                  <div key={index} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <h4 className="font-medium">{assessment.skillName}</h4>
                        <Badge variant={getPriorityBadgeVariant(assessment.priority)}>
                          {assessment.priority}
                        </Badge>
                        <Badge variant="outline">{assessment.category}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {assessment.gapPercentage.toFixed(1)}% gap
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Current: {assessment.currentLevel}%</span>
                        <span>Required: {assessment.requiredLevel}%</span>
                      </div>
                      <Progress
                        value={(assessment.currentLevel / assessment.requiredLevel) * 100}
                        className="h-2"
                      />
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Confidence: {(assessment.confidenceScore * 100).toFixed(0)}%</span>
                      <span>Assessed: {new Date(assessment.assessmentDate).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="organization" className="space-y-6">
          {/* Skill Demand Forecast */}
          <Card>
            <CardHeader>
              <CardTitle>Skill Demand Forecast</CardTitle>
              <CardDescription>
                Predicted skill demand growth over next {timeframe} months
              </CardDescription>
              <div className="flex items-center gap-2">
                <Label htmlFor="timeframe">Timeframe:</Label>
                <Select value={timeframe} onValueChange={setTimeframe}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="12">12 months</SelectItem>
                    <SelectItem value="24">24 months</SelectItem>
                    <SelectItem value="36">36 months</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={demandGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="current"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Current Demand"
                  />
                  <Line
                    type="monotone"
                    dataKey="projected"
                    stroke="#82ca9d"
                    strokeWidth={2}
                    name="Projected Demand"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* High-Growth Skills */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>High-Growth Skills</CardTitle>
                <CardDescription>
                  Skills with highest market growth potential
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {skillDemands
                    .filter(demand => demand.marketTrend === 'growing')
                    .sort((a, b) => b.growthRate - a.growthRate)
                    .slice(0, 5)
                    .map((demand, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-green-100 rounded-full">
                            <TrendingUp className="h-4 w-4 text-green-600" />
                          </div>
                          <div>
                            <h4 className="font-medium">{demand.skillName}</h4>
                            <p className="text-sm text-muted-foreground">{demand.category}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-green-600">
                            +{(demand.growthRate * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Relevance: {(demand.industryRelevance * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Skill Category Distribution</CardTitle>
                <CardDescription>
                  Breakdown of skill gaps by category
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="development" className="space-y-6">
          {/* Learning Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Personalized Learning Recommendations</CardTitle>
              <CardDescription>
                AI-powered learning paths based on your skill gaps and learning style
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {learningRecommendations.map((recommendation, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-full">
                          <BookOpen className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold">{recommendation.skillName}</h3>
                          <p className="text-sm text-muted-foreground">
                            {recommendation.learningStyle} learner • {recommendation.difficultyLevel}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold">{formatCurrency(recommendation.costEstimate)}</div>
                        <div className="text-sm text-muted-foreground">
                          {recommendation.estimatedDuration} days
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Target className="h-4 w-4 text-blue-500" />
                          <span className="text-sm font-medium">Expected Improvement</span>
                        </div>
                        <div className="text-2xl font-bold text-blue-600">
                          +{recommendation.expectedImprovement.toFixed(0)}%
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium">Completion Probability</span>
                        </div>
                        <div className="text-2xl font-bold text-green-600">
                          {(recommendation.completionProbability * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Zap className="h-4 w-4 text-yellow-500" />
                          <span className="text-sm font-medium">Difficulty</span>
                        </div>
                        <div className="text-lg font-semibold capitalize">
                          {recommendation.difficultyLevel}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="font-medium">Recommended Resources:</h4>
                      <div className="space-y-2">
                        {recommendation.recommendedResources.map((resource, idx) => (
                          <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div>
                              <div className="font-medium">{resource.name}</div>
                              <div className="text-sm text-muted-foreground">
                                {resource.provider} • {resource.duration} weeks • {resource.style}
                              </div>
                            </div>
                            <div className="text-sm font-medium">
                              {resource.cost === 0 ? 'Free' : formatCurrency(resource.cost)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Button className="w-full">
                      Start Learning Path
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Development Programs */}
          <Card>
            <CardHeader>
              <CardTitle>Structured Development Programs</CardTitle>
              <CardDescription>
                Comprehensive programs for accelerated skill development
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {learningRecommendations.slice(0, 3).map((rec, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold">{rec.skillName} Development Program</h4>
                      <Badge variant="outline">{rec.difficultyLevel}</Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Duration:</span>
                        <div className="font-medium">{rec.estimatedDuration} days</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Cost:</span>
                        <div className="font-medium">{formatCurrency(rec.costEstimate)}</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Success Rate:</span>
                        <div className="font-medium">{(rec.completionProbability * 100).toFixed(0)}%</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">ROI:</span>
                        <div className="font-medium text-green-600">High</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="career" className="space-y-6">
          {/* Career Trajectories */}
          <div className="space-y-6">
            {careerTrajectories.map((trajectory, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <GraduationCap className="h-5 w-5" />
                    {trajectory.currentRole} → {trajectory.targetRole}
                  </CardTitle>
                  <CardDescription>
                    Career progression path with development requirements
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Timeline and Probability */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-blue-500" />
                        <span className="text-sm font-medium">Time to Promotion</span>
                      </div>
                      <div className="text-2xl font-bold text-blue-600">
                        {trajectory.timeToPromotion} months
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-green-500" />
                        <span className="text-sm font-medium">Promotion Probability</span>
                      </div>
                      <div className="text-2xl font-bold text-green-600">
                        {(trajectory.promotionProbability * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-purple-500" />
                        <span className="text-sm font-medium">Salary Impact</span>
                      </div>
                      <div className="text-2xl font-bold text-purple-600">
                        +{formatCurrency(trajectory.salaryImpact)}
                      </div>
                    </div>
                  </div>

                  {/* Required Skills */}
                  <div className="space-y-3">
                    <h4 className="font-semibold">Required Skills Development</h4>
                    <div className="space-y-2">
                      {trajectory.requiredSkills.map((skill, idx) => (
                        <div key={idx} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="font-medium">{skill.skill}</span>
                            <span className="text-sm text-muted-foreground">
                              {skill.currentLevel}% → {skill.requiredLevel}% (+{skill.gap}%)
                            </span>
                          </div>
                          <Progress
                            value={skill.currentLevel}
                            max={skill.requiredLevel}
                            className="h-2"
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Development Plan Summary */}
                  <div className="space-y-3">
                    <h4 className="font-semibold">Development Plan Summary</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <BookOpen className="h-4 w-4 text-blue-500" />
                          <span className="font-medium">Learning Resources</span>
                        </div>
                        <div className="text-2xl font-bold">
                          {trajectory.skillDevelopmentPlan.length}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Personalized recommendations
                        </div>
                      </div>
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Award className="h-4 w-4 text-green-500" />
                          <span className="font-medium">Estimated Investment</span>
                        </div>
                        <div className="text-2xl font-bold">
                          {formatCurrency(
                            trajectory.skillDevelopmentPlan.reduce(
                              (total, plan) => total + plan.costEstimate,
                              0
                            )
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Total development cost
                        </div>
                      </div>
                    </div>
                  </div>

                  <Button className="w-full">
                    Start Career Development Plan
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SkillGapAnalysis;
