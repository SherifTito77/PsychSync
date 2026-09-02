// Multi-Framework Personality Synthesis Page
// Advanced AI-powered synthesis across multiple personality frameworks
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Brain,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Target,
  Users,
  TrendingUp,
  Zap,
  Puzzle,
  Activity,
  Lightbulb,
  Shield,
  GitCompare,
  BarChart3,
  RefreshCw,
  Download
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

interface FrameworkData {
  name: string;
  type: string;
  result: string;
  confidence: number;
  completed: boolean;
}

interface SynthesisResult {
  unified_traits: Record<string, number>;
  confidence: number;
  contradictions: Array<{
    trait: string;
    frameworks: string[];
    description: string;
    resolved_value: number;
  }>;
  insights: Array<{
    title: string;
    description: string;
    impact: 'positive' | 'neutral' | 'concern';
    confidence: number;
  }>;
  recommendations: Array<{
    role: string;
    fit_score: number;
    description: string;
  }>;
  team_compatibility: {
    overall_score: number;
    strengths: string[];
    potential_conflicts: string[];
  };
}

const MultiFrameworkSynthesis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [synthesizing, setSynthesizing] = useState(false);
  const [frameworks, setFrameworks] = useState<FrameworkData[]>([]);
  const [synthesisResult, setSynthesisResult] = useState<SynthesisResult | null>(null);
  const [selectedUser, setSelectedUser] = useState<string>('self');
  const { user } = useAuth();

  useEffect(() => {
    loadFrameworks();
  }, [selectedUser]);

  const loadFrameworks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const userId = selectedUser === 'self' ? user?.id : selectedUser;
      if (!userId) return;

      const res = await fetch(`/api/v1/personality/user-assessments/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to fetch assessments');
      const data = await res.json();

      // All known frameworks; mark completed ones from API data
      const completedSet = new Set<string>(data.frameworks_completed ?? []);
      const allFrameworks = [
        { name: 'Big Five (OCEAN)', type: 'big_five' },
        { name: 'MBTI', type: 'mbti' },
        { name: 'Enneagram', type: 'enneagram' },
        { name: 'DISC', type: 'disct' },
        { name: 'Predictive Index', type: 'predictive_index' },
        { name: 'CliftonStrengths', type: 'clifton_strengths' },
        { name: 'Social Styles', type: 'social_styles' },
        { name: 'Belbin Team Roles', type: 'belbin' },
        { name: 'Holland Code (RIASEC)', type: 'holland' },
      ];

      const mapped: FrameworkData[] = allFrameworks.map(fw => {
        const match = (data.assessments ?? []).find(
          (a: any) => a.framework_code === fw.type && a.status === 'completed'
        );
        const resultStr = match?.processed_results
          ? JSON.stringify(match.processed_results).slice(0, 80) + '…'
          : 'Not completed';
        return {
          name: fw.name,
          type: fw.type,
          result: resultStr,
          confidence: match ? (match.data_quality?.score ?? 0.8) : 0,
          completed: completedSet.has(fw.type),
        };
      });
      setFrameworks(mapped);
    } catch (error) {
      toast.error('Failed to load framework data');
    } finally {
      setLoading(false);
    }
  };

  const runSynthesis = async () => {
    setSynthesizing(true);
    try {
      const token = localStorage.getItem('auth_token');
      const userId = selectedUser === 'self' ? user?.id : selectedUser;
      if (!userId) throw new Error('No user ID');

      const res = await fetch(`/api/v1/personality/synthesis/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Synthesis request failed');
      const data = await res.json();

      setSynthesisResult({
        unified_traits: data.unified_traits ?? {},
        confidence: data.confidence ?? 0,
        contradictions: data.contradictions ?? [],
        insights: data.insights ?? [],
        recommendations: data.recommendations ?? [],
        team_compatibility: data.team_compatibility ?? { overall_score: 0, strengths: [], potential_conflicts: [] },
      });
      toast.success('Synthesis completed successfully!');
    } catch (error) {
      toast.error('Failed to synthesize frameworks');
      console.error(error);
    } finally {
      setSynthesizing(false);
    }
  };

  const _deprecatedRunSynthesisOld = async () => {
    // kept only for reference; unreachable
    const mockSynthesis: SynthesisResult = {
      unified_traits: {
        openness: 0.78,
        conscientiousness: 0.82,
        extraversion: 0.52,
        agreeableness: 0.72,
        neuroticism: 0.35,
        analytical_thinking: 0.91,
        strategic_orientation: 0.88,
        independence: 0.76,
        adaptability: 0.65,
        leadership_potential: 0.71,
      },
      confidence: 0.87,
      contradictions: [
        {
            trait: 'Extraversion',
            frameworks: ['MBTI (Introverted)', 'Big Five (45 - Moderate)', 'DISC (C - Reserved)'],
            description: 'MBTI suggests introversion, Big Five shows moderate extraversion. Using weighted average favoring Big Five (more reliable).',
            resolved_value: 0.52
          },
          {
            trait: 'Decision Making Style',
            frameworks: ['MBTI (Thinking - Logical)', 'Enneagram (Type 5 - Analytical)', 'DISC (C - Cautious)'],
            description: 'All frameworks align on analytical decision-making approach',
            resolved_value: 0.85
          }
        ],
        insights: [
          {
            title: 'Strong Analytical Foundation',
            description: 'Consistently high analytical scores across Big Five (Openness: 78), MBTI (INTJ), and DISC (Conscientious) indicate a robust analytical thinking style suited for complex problem-solving.',
            impact: 'positive',
            confidence: 0.91
          },
          {
            title: 'Moderate Extraversion Context',
            description: 'While MBTI indicates introversion, behavioral data suggests context-dependent extraversion - likely introverted in personal life but professionally extraverted when needed.',
            impact: 'neutral',
            confidence: 0.73
          },
          {
            title: 'High Strategic Capability',
            description: 'Exceptional strategic thinking across multiple frameworks suggests natural fit for long-term planning, vision setting, and architectural roles.',
            impact: 'positive',
            confidence: 0.88
          },
          {
            title: 'Potential Collaboration Gap',
            description: 'Lower teamwork collaboration scores (0.68) combined with high independence (0.76) may indicate preference for autonomous work over collaborative environments.',
            impact: 'concern',
            confidence: 0.65
          }
        ],
        recommendations: [
          {
            role: 'Technical Architect',
            fit_score: 94,
            description: 'Ideal match: High analytical thinking (91%), strategic orientation (88%), and conscientiousness (82%) align perfectly with architectural responsibilities requiring deep technical analysis and long-term planning.'
          },
          {
            role: 'Data Scientist',
            fit_score: 91,
            description: 'Excellent fit: Strong analytical foundation (91%), learning orientation (92%), and strategic thinking (88%) support advanced data analysis and model development.'
          },
          {
            role: 'Product Strategy Lead',
            fit_score: 87,
            description: 'Strong match: Strategic capability (88%) combined with openness (78%) and conscientiousness (82%) creates ideal profile for product strategy and vision.'
          },
          {
            role: 'Research Scientist',
            fit_score: 89,
            description: 'Very strong fit: Exceptional learning orientation (92%) and analytical thinking (91%) with high independence (76%) suited for autonomous research work.'
          },
          {
            role: 'Engineering Manager',
            fit_score: 72,
            description: 'Moderate fit: Leadership potential (71%) is good, but lower teamwork collaboration (68%) and extraversion (52%) may present challenges in people management roles.'
          }
        ],
        team_compatibility: {
          overall_score: 78,
          strengths: [
            'Brings exceptional analytical depth to team discussions',
            'Excels at strategic planning and long-term visioning',
            'High conscientiousness ensures reliable delivery',
            'Strong learning orientation benefits team knowledge sharing',
            'Natural fit for technical leadership roles'
          ],
          potential_conflicts: [
            'May clash with highly emotional/feeling-oriented personalities',
            'Preference for independence could create friction in collaborative teams',
            'High standards (Conscientiousness: 82%) may cause frustration with slower-paced team members',
            'Reserved communication style might be misinterpreted as disengagement'
          ]
        }
      };

      setSynthesisResult(mockSynthesis);
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return 'bg-green-100 text-green-800 border-green-200';
      case 'concern': return 'bg-red-100 text-red-800 border-red-200';
      case 'neutral': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getFitScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
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
          <div className="h-8 w-8 text-purple-600 flex items-center justify-center bg-purple-100 rounded-lg">
            <Puzzle className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Multi-Framework Synthesis</h1>
            <p className="text-sm text-gray-500">AI-powered synthesis across personality frameworks for unified insights</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={runSynthesis}
            disabled={synthesizing}
            className="flex items-center space-x-2"
          >
            <Sparkles className="h-4 w-4" />
            <span>{synthesizing ? 'Synthesizing...' : 'Run Synthesis'}</span>
          </Button>
        </div>
      </div>

      {/* Frameworks Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {frameworks.map((fw) => (
          <Card key={fw.type} className={fw.completed ? 'border-green-200' : 'border-gray-200'}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{fw.name}</CardTitle>
                {fw.completed ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                )}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-gray-600 mb-2">{fw.result}</p>
              <div className="flex items-center justify-between text-xs">
                <span>Confidence:</span>
                <span className="font-semibold">{(fw.confidence * 100).toFixed(0)}%</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!synthesisResult ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Brain className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold mb-2">Run Multi-Framework Synthesis</h3>
            <p className="text-gray-600 mb-6">
              Synthesize data across all completed personality frameworks to generate unified insights,
              detect contradictions, and provide personalized recommendations.
            </p>
            <Button onClick={runSynthesis} disabled={synthesizing}>
              {synthesizing ? 'Synthesizing...' : 'Start Synthesis'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="traits">Unified Traits</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
            <TabsTrigger value="recommendations">Roles</TabsTrigger>
            <TabsTrigger value="team">Team</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Synthesis Confidence */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Sparkles className="h-5 w-5 text-purple-600" />
                    <span>Synthesis Results</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Overall Confidence</p>
                      <div className="text-3xl font-bold text-purple-600">
                        {(synthesisResult.confidence * 100).toFixed(1)}%
                      </div>
                      <p className="text-xs text-gray-500 mt-1">High confidence synthesis</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Frameworks Analyzed</p>
                      <div className="text-3xl font-bold">{frameworks.filter(f => f.completed).length}</div>
                      <p className="text-xs text-gray-500 mt-1">Completed assessments</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Contradictions Detected</CardTitle>
                  <GitCompare className="h-4 w-4 text-orange-600 mt-1" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{synthesisResult.contradictions.length}</div>
                  <p className="text-xs text-gray-500 mt-1">Automatically resolved</p>
                </CardContent>
              </Card>
            </div>

            {/* Top Insights */}
            <Card>
              <CardHeader>
                <CardTitle>Key Synthesis Insights</CardTitle>
                <CardDescription>Most important findings from cross-framework analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {synthesisResult.insights.slice(0, 3).map((insight, index) => (
                    <Alert key={index} className={getImpactColor(insight.impact)}>
                      {insight.impact === 'positive' && <CheckCircle className="h-4 w-4" />}
                      {insight.impact === 'concern' && <AlertTriangle className="h-4 w-4" />}
                      {insight.impact === 'neutral' && <Activity className="h-4 w-4" />}
                      <AlertTitle className="flex items-center justify-between">
                        <span>{insight.title}</span>
                        <span className="text-xs font-normal">Confidence: {(insight.confidence * 100).toFixed(0)}%</span>
                      </AlertTitle>
                      <AlertDescription className="mt-2">
                        {insight.description}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Unified Traits Tab */}
          <TabsContent value="traits" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-blue-600" />
                  <span>Unified Personality Profile</span>
                </CardTitle>
                <CardDescription>Synthesized traits across all frameworks (0-1 scale)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(synthesisResult.unified_traits).map(([trait, value]) => (
                    <div key={trait} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium capitalize">{trait.replace(/_/g, ' ')}</span>
                        <span className="text-sm font-semibold">{(value * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${value * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Contradictions */}
            {synthesisResult.contradictions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <GitCompare className="h-5 w-5 text-orange-600" />
                    <span>Contradiction Resolution</span>
                  </CardTitle>
                  <CardDescription>Framework disagreements and how they were resolved</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {synthesisResult.contradictions.map((contradiction, index) => (
                      <div key={index} className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                        <h4 className="font-semibold mb-2 capitalize">{contradiction.trait}</h4>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {contradiction.frameworks.map((fw, i) => (
                            <Badge key={i} variant="outline">{fw}</Badge>
                          ))}
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{contradiction.description}</p>
                        <div className="text-xs text-gray-600">
                          Resolved Value: <span className="font-semibold">{(contradiction.resolved_value * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>All Synthesis Insights</CardTitle>
                <CardDescription>Detailed analysis across personality frameworks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {synthesisResult.insights.map((insight, index) => (
                    <Card key={index} className={`border-l-4 ${
                      insight.impact === 'positive' ? 'border-l-green-600' :
                      insight.impact === 'concern' ? 'border-l-red-600' :
                      'border-l-gray-400'
                    }`}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold">{insight.title}</h4>
                          <div className="flex items-center space-x-2">
                            <Badge className={getImpactColor(insight.impact)}>{insight.impact}</Badge>
                            <span className="text-xs text-gray-500">{(insight.confidence * 100).toFixed(0)}% confidence</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600">{insight.description}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Recommendations Tab */}
          <TabsContent value="recommendations" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Lightbulb className="h-5 w-5 text-yellow-600" />
                  <span>Role Fit Recommendations</span>
                </CardTitle>
                <CardDescription>Personalized career and role recommendations based on synthesis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {synthesisResult.recommendations
                    .sort((a, b) => b.fit_score - a.fit_score)
                    .map((rec, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <Badge variant="outline" className="text-xs">
                              #{index + 1} Match
                            </Badge>
                            <h4 className="font-semibold">{rec.role}</h4>
                          </div>
                          <p className="text-sm text-gray-600">{rec.description}</p>
                        </div>
                        <div className="text-right">
                          <div className={`text-2xl font-bold ${getFitScoreColor(rec.fit_score)}`}>
                            {rec.fit_score}%
                          </div>
                          <p className="text-xs text-gray-500">Fit Score</p>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Team Tab */}
          <TabsContent value="team" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-green-600" />
                    <span>Team Strengths</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {synthesisResult.team_compatibility.strengths.map((strength, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-green-800">{strength}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    <span>Potential Conflicts</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {synthesisResult.team_compatibility.potential_conflicts.map((conflict, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-orange-800">{conflict}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Overall Team Compatibility</CardTitle>
                <CardDescription>Aggregate score indicating how well this profile typically fits in teams</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-5xl font-bold text-blue-600 mb-2">
                    {synthesisResult.team_compatibility.overall_score}/100
                  </div>
                  <p className="text-sm text-gray-600">Team Compatibility Score</p>
                  <Badge className="mt-3" variant="outline">
                    {synthesisResult.team_compatibility.overall_score >= 80 ? 'Excellent' :
                     synthesisResult.team_compatibility.overall_score >= 60 ? 'Good' :
                     synthesisResult.team_compatibility.overall_score >= 40 ? 'Moderate' : 'Needs Attention'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Export */}
      <Card>
        <CardHeader>
          <CardTitle>Export Synthesis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-3">
            <Button variant="outline" className="flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Export PDF Report</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Share Results</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MultiFrameworkSynthesis;
