/**
 * Team Composition Optimizer Component
 *
 * Advanced interface for optimizing team composition based on personality traits,
 skills diversity, and performance predictors. Uses AI-powered recommendations.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useAnalytics } from '@/services/analytics/tracker';
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  BarChart,
  Bar,
  Treemap,
  HeatmapGrid,
  Cell,
} from 'recharts';
import {
  Users,
  Brain,
  Target,
  Shield,
  Activity,
  BarChart3,
  Zap,
  Settings,
  Play,
  RefreshCw,
  Download,
  Upload,
  UserPlus,
  UserX,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Info,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
  Star,
  Award,
  Trophy,
  GitBranch,
  Lightbulb,
  Filter,
  Search,
} from 'lucide-react';

// Types
interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  department: string;
  skills: string[];
  skillLevels: Record<string, number>;
  personalityTraits: Record<string, number>;
  performanceScore: number;
  collaborationScore: number;
  innovationScore: number;
  leadershipPotential: number;
  adaptabilityScore: number;
  yearsOfExperience: number;
  avatar?: string;
  availability: boolean;
}

interface TeamRequirement {
  teamSize: number;
  requiredSkills: string[];
  skillWeights: Record<string, number>;
  personalityBalance: Record<string, [number, number]>;
  objectives: string[];
  experienceDistribution: Record<string, number>;
  budget: number;
  deadline: string;
  projectType: string;
}

interface OptimizationResult {
  recommendedMembers: string[];
  teamScore: number;
  performancePrediction: number;
  skillCoverage: Record<string, number>;
  personalityBalance: Record<string, number>;
  compatibilityScore: number;
  diversityMetrics: Record<string, number>;
  riskFactors: string[];
  recommendations: string[];
  improvementOpportunities: string[];
}

interface TeamCompositionOptimizerProps {
  currentTeamId?: string;
  projectId?: string;
  onOptimizationComplete?: (result: OptimizationResult) => void;
}

const TeamCompositionOptimizer: React.FC<TeamCompositionOptimizerProps> = ({
  currentTeamId,
  projectId,
  onOptimizationComplete,
}) => {
  const { trackFeatureUsed } = useAnalytics();

  const [selectedTab, setSelectedTab] = useState('setup');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [currentTeam, setCurrentTeam] = useState<TeamMember[]>([]);
  const [availableCandidates, setAvailableCandidates] = useState<TeamMember[]>([]);
  const [requirements, setRequirements] = useState<TeamRequirement>({
    teamSize: 5,
    requiredSkills: ['Leadership', 'Communication', 'Technical'],
    skillWeights: { 'Leadership': 0.3, 'Communication': 0.2, 'Technical': 0.25 },
    personalityBalance: {
      'Openness': [0.4, 0.8],
      'Conscientiousness': [0.5, 0.9],
      'Extraversion': [0.3, 0.7],
      'Agreeableness': [0.4, 0.8],
      'Neuroticism': [0.1, 0.4]
    },
    objectives: ['Performance', 'Collaboration', 'Innovation'],
    experienceDistribution: { 'Junior': 1, 'Mid': 3, 'Senior': 1 },
    budget: 500000,
    deadline: '2024-06-30',
    projectType: 'Digital Transformation'
  });

  // Mock data generation
  useEffect(() => {
    // Generate mock current team members
    const mockTeam: TeamMember[] = [
      {
        id: '1',
        name: 'Sarah Johnson',
        email: 'sarah.johnson@company.com',
        role: 'Team Lead',
        department: 'Engineering',
        skills: ['Leadership', 'Communication', 'Technical'],
        skillLevels: { 'Leadership': 0.85, 'Communication': 0.9, 'Technical': 0.8 },
        personalityTraits: {
          'Openness': 0.75,
          'Conscientiousness': 0.85,
          'Extraversion': 0.7,
          'Agreeableness': 0.8,
          'Neuroticism': 0.25
        },
        performanceScore: 0.88,
        collaborationScore: 0.92,
        innovationScore: 0.78,
        leadershipPotential: 0.9,
        adaptabilityScore: 0.85,
        yearsOfExperience: 8,
        availability: true,
      },
      {
        id: '2',
        name: 'Michael Chen',
        email: 'michael.chen@company.com',
        role: 'Senior Developer',
        department: 'Engineering',
        skills: ['Technical', 'Problem Solving', 'Analytics'],
        skillLevels: { 'Technical': 0.9, 'Problem Solving': 0.85, 'Analytics': 0.8 },
        personalityTraits: {
          'Openness': 0.8,
          'Conscientiousness': 0.75,
          'Extraversion': 0.4,
          'Agreeableness': 0.7,
          'Neuroticism': 0.3
        },
        performanceScore: 0.85,
        collaborationScore: 0.75,
        innovationScore: 0.9,
        leadershipPotential: 0.65,
        adaptabilityScore: 0.88,
        yearsOfExperience: 6,
        availability: true,
      },
    ];

    // Generate mock available candidates
    const mockCandidates: TeamMember[] = [
      {
        id: '3',
        name: 'Emily Rodriguez',
        email: 'emily.rodriguez@company.com',
        role: 'UX Designer',
        department: 'Design',
        skills: ['Design', 'User Research', 'Communication'],
        skillLevels: { 'Design': 0.85, 'User Research': 0.8, 'Communication': 0.75 },
        personalityTraits: {
          'Openness': 0.9,
          'Conscientiousness': 0.7,
          'Extraversion': 0.6,
          'Agreeableness': 0.85,
          'Neuroticism': 0.2
        },
        performanceScore: 0.82,
        collaborationScore: 0.9,
        innovationScore: 0.95,
        leadershipPotential: 0.7,
        adaptabilityScore: 0.92,
        yearsOfExperience: 5,
        availability: true,
      },
      {
        id: '4',
        name: 'David Kim',
        email: 'david.kim@company.com',
        role: 'Data Analyst',
        department: 'Analytics',
        skills: ['Analytics', 'Statistics', 'Communication'],
        skillLevels: { 'Analytics': 0.88, 'Statistics': 0.9, 'Communication': 0.7 },
        personalityTraits: {
          'Openness': 0.6,
          'Conscientiousness': 0.9,
          'Extraversion': 0.3,
          'Agreeableness': 0.8,
          'Neuroticism': 0.15
        },
        performanceScore: 0.87,
        collaborationScore: 0.8,
        innovationScore: 0.65,
        leadershipPotential: 0.6,
        adaptabilityScore: 0.85,
        yearsOfExperience: 4,
        availability: true,
      },
      {
        id: '5',
        name: 'Lisa Wang',
        email: 'lisa.wang@company.com',
        role: 'Project Manager',
        department: 'Operations',
        skills: ['Leadership', 'Planning', 'Communication'],
        skillLevels: { 'Leadership': 0.8, 'Planning': 0.85, 'Communication': 0.88 },
        personalityTraits: {
          'Openness': 0.7,
          'Conscientiousness': 0.95,
          'Extraversion': 0.8,
          'Agreeableness': 0.9,
          'Neuroticism': 0.1
        },
        performanceScore: 0.9,
        collaborationScore: 0.95,
        innovationScore: 0.7,
        leadershipPotential: 0.85,
        adaptabilityScore: 0.88,
        yearsOfExperience: 7,
        availability: true,
      },
      {
        id: '6',
        name: 'James Wilson',
        email: 'james.wilson@company.com',
        role: 'DevOps Engineer',
        department: 'Engineering',
        skills: ['Technical', 'Infrastructure', 'Automation'],
        skillLevels: { 'Technical': 0.85, 'Infrastructure': 0.9, 'Automation': 0.8 },
        personalityTraits: {
          'Openness': 0.65,
          'Conscientiousness': 0.85,
          'Extraversion': 0.5,
          'Agreeableness': 0.6,
          'Neuroticism': 0.2
        },
        performanceScore: 0.83,
        collaborationScore: 0.7,
        innovationScore: 0.75,
        leadershipPotential: 0.55,
        adaptabilityScore: 0.9,
        yearsOfExperience: 5,
        availability: true,
      },
      {
        id: '7',
        name: 'Maria Garcia',
        email: 'maria.garcia@company.com',
        role: 'Business Analyst',
        department: 'Business',
        skills: ['Analysis', 'Requirements', 'Communication'],
        skillLevels: { 'Analysis': 0.88, 'Requirements': 0.82, 'Communication': 0.9 },
        personalityTraits: {
          'Openness': 0.75,
          'Conscientiousness': 0.8,
          'Extraversion': 0.7,
          'Agreeableness': 0.85,
          'Neuroticism': 0.25
        },
        performanceScore: 0.86,
        collaborationScore: 0.92,
        innovationScore: 0.7,
        leadershipPotential: 0.75,
        adaptabilityScore: 0.88,
        yearsOfExperience: 6,
        availability: true,
      },
    ];

    setCurrentTeam(mockTeam);
    setAvailableCandidates(mockCandidates);
  }, []);

  // Handle optimization
  const handleOptimize = async () => {
    setIsOptimizing(true);

    // ✅ NEW: Track team optimizer usage
    trackFeatureUsed('team_optimizer_used', {
      feature_category: 'team_analytics',
      team_size: currentTeam.length,
      usage_context: 'team_composition_optimization',
    });

    // Simulate optimization process
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock optimization result
    const mockResult: OptimizationResult = {
      recommendedMembers: ['3', '5', '7', '6', '4'], // Selected candidate IDs
      teamScore: 0.87,
      performancePrediction: 0.85,
      skillCoverage: {
        'Leadership': 0.85,
        'Communication': 0.88,
        'Technical': 0.82,
        'Analytics': 0.88
      },
      personalityBalance: {
        'Openness': 0.7,
        'Conscientiousness': 0.82,
        'Extraversion': 0.6,
        'Agreeableness': 0.83,
        'Neuroticism': 0.18
      },
      compatibilityScore: 0.82,
      diversityMetrics: {
        'skillDiversity': 0.85,
        'experienceDiversity': 0.78,
        'departmentalDiversity': 0.7
      },
      riskFactors: [
        'Low diversity in technical skills',
        'Potential communication bottlenecks',
        'Limited leadership experience'
      ],
      recommendations: [
        'Add more technical diversity through training',
        'Implement cross-functional collaboration initiatives',
        'Provide leadership development opportunities'
      ],
      improvementOpportunities: [
        'Enhance innovation capabilities through diverse thinking',
        'Balance team composition for better collaboration',
        'Invest in skill development for emerging technologies'
      ]
    };

    setOptimizationResult(mockResult);
    setIsOptimizing(false);
    onOptimizationComplete?.(mockResult);
  };

  // Get recommended team members
  const recommendedTeam = useMemo(() => {
    if (!optimizationResult) return [];
    return [...currentTeam, ...availableCandidates.filter(c =>
      optimizationResult.recommendedMembers.includes(c.id)
    )].slice(0, requirements.teamSize);
  }, [optimizationResult, currentTeam, availableCandidates, requirements.teamSize]);

  // Prepare data for charts
  const personalityRadarData = useMemo(() => {
    const traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism'];
    return traits.map(trait => ({
      trait,
      current: currentTeam.length > 0
        ? currentTeam.reduce((sum, member) => sum + member.personalityTraits[trait], 0) / currentTeam.length
        : 0.5,
      optimal: requirements.personalityBalance[trait]
        ? (requirements.personalityBalance[trait][0] + requirements.personalityBalance[trait][1]) / 2
        : 0.5,
      optimized: optimizationResult
        ? optimizationResult.personalityBalance[trait]
        : 0.5,
    }));
  }, [currentTeam, requirements, optimizationResult]);

  const skillCoverageData = useMemo(() => {
    const skills = Object.keys(requirements.skillWeights);
    return skills.map(skill => ({
      skill,
      coverage: optimizationResult?.skillCoverage[skill] || 0,
      weight: requirements.skillWeights[skill] || 0,
    }));
  }, [optimizationResult, requirements.skillWeights]);

  const compatibilityHeatmapData = useMemo(() => {
    if (recommendedTeam.length === 0) return [];

    return recommendedTeam.map((member1, i) => {
      const row: any = { name: member1.name, id: member1.id };
      recommendedTeam.forEach((member2, j) => {
        const compatibility = Math.random() * 0.3 + 0.7; // Mock compatibility score
        row[`member${j}`] = Number((compatibility * 100).toFixed(1));
      });
      return row;
    });
  }, [recommendedTeam]);

  const diversityMetricsData = [
    { metric: 'Skill Diversity', current: 85, target: 90, improvement: 5 },
    { metric: 'Experience Diversity', current: 78, target: 85, improvement: 7 },
    { metric: 'Departmental Diversity', current: 70, target: 80, improvement: 10 },
    { metric: 'Cognitive Diversity', current: 88, target: 85, improvement: -3 },
    { metric: 'Age Diversity', current: 65, target: 75, improvement: 10 },
  ];

  const performancePredictionData = [
    { phase: 'Current', score: 0.78 },
    { phase: 'Optimized', score: optimizationResult?.performancePrediction || 0.85 },
    { phase: '6-Month Target', score: 0.92 },
  ];

  // Helper functions
  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-blue-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 0.9) return 'bg-green-100';
    if (score >= 0.7) return 'bg-blue-100';
    if (score >= 0.5) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const handleMemberSelection = (memberId: string, selected: boolean) => {
    if (selected) {
      setSelectedMembers([...selectedMembers, memberId]);
    } else {
      setSelectedMembers(selectedMembers.filter(id => id !== memberId));
    }
  };

  // Render different tabs
  const renderSetupTab = () => (
    <div className="space-y-6">
      {/* Requirements Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Team Requirements
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-4">Basic Requirements</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Team Size</label>
                  <input
                    type="number"
                    value={requirements.teamSize}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      teamSize: parseInt(e.target.value)
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                    min="1"
                    max="20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Project Type</label>
                  <select
                    value={requirements.projectType}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      projectType: e.target.value
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="Digital Transformation">Digital Transformation</option>
                    <option value="Product Development">Product Development</option>
                    <option value="Process Improvement">Process Improvement</option>
                    <option value="Research & Development">Research & Development</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Deadline</label>
                  <input
                    type="date"
                    value={requirements.deadline}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      deadline: e.target.value
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Budget ($)</label>
                  <input
                    type="number"
                    value={requirements.budget}
                    onChange={(e) => setRequirements({
                      ...requirements,
                      budget: parseInt(e.target.value)
                    })}
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    step="10000"
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Required Skills</h3>

              <div className="space-y-4">
                {requirements.requiredSkills.map((skill, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <span className="text-sm">{skill}</span>
                    <input
                      type="range"
                      value={requirements.skillWeights[skill] * 100}
                      onChange={(e) => setRequirements({
                        ...requirements,
                        skillWeights: {
                          ...requirements.skillWeights,
                          [skill]: parseInt(e.target.value) / 100
                        }
                      })}
                      className="flex-1"
                      min="0"
                      max="100"
                    />
                    <span className="text-sm text-gray-600 w-12">
                      {(requirements.skillWeights[skill] * 100).toFixed(0)}%
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newSkills = requirements.requiredSkills.filter(s => s !== skill);
                        setRequirements({
                          ...requirements,
                          requiredSkills: newSkills
                        });
                      }}
                    >
                      <UserX className="h-3 w-3" />
                    </Button>
                  </div>
                ))}

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setRequirements({
                      ...requirements,
                      requiredSkills: [...requirements.requiredSkills, 'New Skill']
                    });
                  }}
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Add Skill
                </Button>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Optimization Objectives</h3>

              <div className="space-y-2">
                {['Performance', 'Collaboration', 'Innovation', 'Leadership', 'Stability', 'Diversity'].map((objective) => (
                  <label key={objective} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={requirements.objectives.includes(objective)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setRequirements({
                            ...requirements,
                            objectives: [...requirements.objectives, objective]
                          });
                        } else {
                          setRequirements({
                            ...requirements,
                            objectives: requirements.objectives.filter(o => o !== objective)
                          });
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm">{objective}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-6">
            <div className="flex justify-end gap-4">
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Import Requirements
              </Button>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Export Configuration
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Team Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Current Team Analysis
          </CardTitle>
          <CardDescription>
            Current team composition with performance and skill metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3">Team Members</h4>
              <div className="space-y-3">
                {currentTeam.map((member) => (
                  <div key={member.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                        <Users className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <div className="font-medium">{member.name}</div>
                        <div className="text-sm text-gray-600">
                          {member.role} • {member.department}
                        </div>
                        <div className="flex gap-1 mt-1">
                          {member.skills.slice(0, 2).map((skill) => (
                            <Badge key={skill} variant="secondary" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm text-gray-600">Performance</div>
                      <div className={`font-bold ${getScoreColor(member.performanceScore)}`}>
                        {(member.performanceScore * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-gray-600">Collaboration</div>
                      <div className={`font-bold ${getScoreColor(member.collaborationScore)}`}>
                        {(member.collaborationScore * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Current State Metrics</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {currentTeam.length}
                  </div>
                  <p className="text-sm text-blue-700">Team Size</p>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {(currentTeam.reduce((sum, m) => sum + m.performanceScore, 0) / currentTeam.length * 100).toFixed(1)}%
                  </div>
                  <p className="text-sm text-green-700">Avg Performance</p>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {currentTeam.reduce((sum, m) => sum + m.skills.length, 0) / currentTeam.length}
                  </div>
                  <p className="text-sm text-purple-700">Avg Skills</p>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {(currentTeam.reduce((sum, m) => sum + m.yearsOfExperience, 0) / currentTeam.length).toFixed(1)}
                  </div>
                  <p className="text-sm text-orange-700">Avg Experience</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Candidates */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Available Candidates
          </CardTitle>
          <CardDescription>
            {availableCandidates.length} candidates available for team composition
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {availableCandidates.map((candidate) => (
              <div key={candidate.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                   onClick={() => handleMemberSelection(candidate.id, !selectedMembers.includes(candidate.id))}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <Users className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{candidate.name}</h3>
                      {selectedMembers.includes(candidate.id) && (
                        <Badge variant="default">Selected</Badge>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">
                      {candidate.role} • {candidate.department}
                    </div>
                    <div className="flex gap-1 mt-1">
                      {candidate.skills.slice(0, 2).map((skill) => (
                        <Badge key={skill} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="text-right ml-4">
                    <div className="text-sm text-gray-600">Leadership</div>
                    <div className={`font-bold ${getScoreColor(candidate.leadershipPotential)}`}>
                      {(candidate.leadershipPotential * 100).toFixed(0)}%
                    </div>
                    <div className="text-sm text-gray-600 mt-1">Innovation</div>
                    <div className={`font-bold ${getScoreColor(candidate.innovationScore)}`}>
                      {(candidate.innovationScore * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Optimization Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Optimization Controls</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Selected: {selectedMembers.length} / {requirements.teamSize} members
            </div>
            <Button
              onClick={handleOptimize}
              disabled={isOptimizing || selectedMembers.length !== requirements.teamSize}
              className="flex items-center gap-2"
            >
              <Brain className="h-4 w-4" />
              {isOptimizing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  Optimize Team Composition
                </>
              )}
            </Button>
          </div>

          {isOptimizing && (
            <div className="mt-4">
              <Progress value={50} className="mb-2" />
              <p className="text-sm text-gray-600 text-center">Analyzing team dynamics and compatibility...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const renderResultsTab = () => (
    <div className="space-y-6">
      {!optimizationResult ? (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>No Optimization Results</AlertTitle>
          <AlertDescription>
            Please run the optimization first to see results and recommendations.
          </AlertDescription>
        </Alert>
      ) : (
        <>
          {/* Optimization Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                Optimization Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {(optimizationResult.teamScore * 100).toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600">Team Score</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {(optimizationResult.performancePrediction * 100).toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600">Predicted Performance</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">
                    {(optimizationResult.compatibilityScore * 100).toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600">Compatibility Score</p>
                </div>
              </div>

              {/* Recommended Team */}
              <div className="mt-6">
                <h3 className="font-semibold mb-3">Recommended Team</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {recommendedTeam.map((member) => (
                    <div key={member.id} className="p-4 border rounded-lg">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <h4 className="font-medium">{member.name}</h4>
                          <p className="text-sm text-gray-600">{member.role}</p>
                          <div className="flex gap-1 mt-1">
                            {member.skills.slice(0, 2).map((skill) => (
                              <Badge key={skill} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <span className="text-gray-600">Performance</span>
                          <div className={`font-bold ${getScoreColor(member.performanceScore)}`}>
                            {(member.performanceScore * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Leadership</span>
                          <div className={`font-bold ${getScoreColor(member.leadershipPotential)}`}>
                            {(member.leadershipPotential * 100).toFixed(0)}%
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Adaptability</span>
                          <div className={`font-bold ${getScoreColor(member.adaptabilityScore)}`}>
                            {(member.adaptabilityScore * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Skill Coverage Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Skill Coverage Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={skillCoverageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="skill" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="coverage" fill="#3b82f6" name="Coverage (%)" />
                  <Bar dataKey="weight" fill="#10b981" name="Weight" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Personality Balance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Personality Balance</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={personalityRadarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="trait" />
                    <PolarRadiusAxis angle={90} domain={[0, 1]} />
                    <Radar
                      name="Current"
                      dataKey="current"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="Optimal"
                      dataKey="optimal"
                      stroke="#10b981"
                      fill="#10b981"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="Optimized"
                      dataKey="optimized"
                      stroke="#f59e0b"
                      fill="#f59e0b"
                      fillOpacity={0.6}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Prediction</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performancePredictionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="phase" />
                    <YAxis domain={[0.7, 1.0]} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Diversity Metrics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Diversity Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={diversityMetricsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="current" fill="#3b82f6" name="Current" />
                  <Bar dataKey="target" fill="#10b981" name="Target" />
                  <Bar dataKey="improvement" fill="#f59e0b" name="Improvement" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Compatibility Matrix */}
          <Card>
            <CardHeader>
              <CardTitle>Team Compatibility Matrix</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <HeatmapGrid
                  data={compatibilityHeatmapData}
                  xKey="name"
                  yKey="name"
                  colors={[
                    '#ef4444', // < 60
                    '#f59e0b', // 60-70
                    '#10b981', // 70-80
                    '#22c55e', // 80-90
                    '#10b981', // > 90
                  ]}
                />
                <Tooltip />
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                Recommendations & Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 text-green-600">Recommendations</h4>
                  <ul className="space-y-2">
                    {optimizationResult.recommendations.map((rec, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold mb-3 text-orange-600">Risk Factors</h4>
                  <ul className="space-y-2">
                    {optimizationResult.riskFactors.map((risk, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{risk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-semibold mb-2 text-blue-800">Improvement Opportunities</h4>
                <ul className="space-y-1">
                  {optimizationResult.improvementOpportunities.map((opportunity, index) => (
                    <li key={index} className="text-sm text-blue-700">
                      • {opportunity}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Export Options */}
          <Card>
            <CardHeader>
              <CardTitle>Export Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export PDF Report
                </Button>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export Excel Data
                </Button>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Save Configuration
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );

  const renderComparisonTab = () => (
    <div className="space-y-6">
      {/* Comparison Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Team Composition Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">+15%</div>
                <p className="text-sm text-blue-700">Performance Improvement</p>
                <div className="text-xs text-blue-600 mt-1">Compared to baseline</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">+22%</div>
                <p className="text-sm text-green-700">Skill Coverage</p>
                <div className="text-xs text-green-600 mt-1">Better requirements match</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">+18%</div>
                <p className="text-sm text-purple-700">Diversity Score</p>
                <div className="text-xs text-purple-600 mt-1">More inclusive composition</div>
              </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Before vs After Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.keys(requirements.skillWeights).map(skill => ({
                skill,
                before: 65,
                after: skillCoverageData.find(s => s.skill === skill)?.coverage || 0
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="skill" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="before" fill="#94a3b8" name="Before" />
                <Bar dataKey="after" fill="#10b981" name="After" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Trend Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={[
                { month: 'Initial', initial: 65, after3: 75, after6: 85 },
                { month: 'Optimized', initial: 65, after3: 82, after6: 95 }
              ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[60, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="initial" stroke="#94a3b8" strokeWidth={2} name="Initial" />
                <Line type="monotone" dataKey="after3" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" name="After 3 Months" />
                <Line type="monotone" dataKey="after6" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" name="After 6 Months" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Team Composition Optimizer</h1>
          <p className="text-muted-foreground">
            AI-powered team optimization for maximum performance and collaboration
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Brain className="h-3 w-3" />
            AI-Powered
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            {optimizationResult ? 'Optimized' : 'Ready'}
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-4">
          {renderSetupTab()}
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {renderResultsTab()}
        </TabsContent>

        <TabsContent value="comparison" className="space-y-4">
          {renderComparisonTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TeamCompositionOptimizer;
