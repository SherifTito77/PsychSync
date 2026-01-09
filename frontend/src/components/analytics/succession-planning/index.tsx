/**
 * Succession Planning - Main Orchestrator
 *
 * HR succession planning with candidate analysis and pipeline visualization
 *
 * SPLIT from 1,135 lines → ~250 lines (78% reduction)
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Users,
  TrendingUp,
  AlertTriangle,
  Award,
  BarChart3,
  Target,
  Shield,
  Sparkles,
} from 'lucide-react';

import { useSuccessionPlanning } from './hooks/useSuccessionPlanning';
import { getReadinessColor, getRiskColor, getReadinessLabel, getGapColor } from './utils/displayHelpers';

const SuccessionPlanning: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    pipelineAnalysis,
    successionCandidates,
    scenarios,
  } = useSuccessionPlanning();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <BarChart3 className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Succession Planning</h1>
            <p className="text-sm text-gray-500">Identify and develop future leaders</p>
          </div>
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="pipeline">Pipeline Overview</TabsTrigger>
          <TabsTrigger value="candidates">Candidates</TabsTrigger>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
        </TabsList>

        {/* Pipeline Overview Tab */}
        <TabsContent value="pipeline" className="space-y-6">
          {pipelineAnalysis.map((level) => (
            <Card key={level.pipeline_level}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{level.pipeline_level}</CardTitle>
                  <Badge className={getRiskColor(level.risk_level)}>
                    {level.risk_level} Risk
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold">{level.total_positions}</div>
                      <p className="text-sm text-gray-500">Positions</p>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{level.ready_candidates}</div>
                      <p className="text-sm text-gray-500">Ready</p>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${getGapColor(level.gap_percentage)}`}>
                        {level.gap_percentage}%
                      </div>
                      <p className="text-sm text-gray-500">Gap</p>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-blue-600">{level.bench_strength}%</div>
                      <p className="text-sm text-gray-500">Bench Strength</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Ready Candidates</span>
                      <span className="text-sm text-gray-500">
                        {level.ready_candidates} / {level.total_positions}
                      </span>
                    </div>
                    <Progress value={(level.ready_candidates / level.total_positions) * 100} />
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">Development Recommendations</h4>
                    <ul className="space-y-1">
                      {level.development_recommendations.map((rec, i) => (
                        <li key={i} className="text-sm flex items-start gap-2">
                          <Target className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Candidates Tab */}
        <TabsContent value="candidates" className="space-y-4">
          {successionCandidates.map((item, index) => (
            <Card key={index}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-semibold">
                        {item.candidate.user_id}
                      </h3>
                      <Badge className={getReadinessColor(item.candidate.readiness_level)}>
                        {getReadinessLabel(item.candidate.readiness_level)}
                      </Badge>
                      <Badge variant="outline">{item.target_role.level}</Badge>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Current Role</span>
                        <p className="font-medium">{item.candidate.current_role}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Target Role</span>
                        <p className="font-medium">{item.target_role.role_name}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Match Score</span>
                        <p className="font-bold text-blue-600">{item.match_score}%</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Success Probability</span>
                        <p className="font-bold text-green-600">
                          {(item.success_probability * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>

                    <div className="mt-4">
                      <h4 className="text-sm font-medium mb-2">Skill Gaps</h4>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(item.gap_analysis).map(([skill, gap]) => (
                          <Badge key={skill} variant="outline" className="text-xs">
                            {skill}: {gap}%
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="ml-4 flex flex-col items-end gap-2">
                    <Award className="h-8 w-8 text-yellow-500" />
                    <Button variant="outline" size="sm">View Details</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Scenarios Tab */}
        <TabsContent value="scenarios" className="space-y-4">
          {scenarios.map((scenario, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    {scenario.scenario_name}
                  </CardTitle>
                  <Badge className={getRiskColor(scenario.readiness_status === 'AT_RISK' ? 'HIGH' : 'LOW')}>
                    {scenario.readiness_status.replace('_', ' ')}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold">{scenario.timeline_months}</div>
                      <p className="text-sm text-gray-500">Months Timeline</p>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${getGapColor(scenario.financial_risk * 100)}`}>
                        {(scenario.financial_risk * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-gray-500">Financial Risk</p>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold ${getGapColor(scenario.operational_risk * 100)}`}>
                        {(scenario.operational_risk * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-gray-500">Operational Risk</p>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">Business Impact</h4>
                    <div className="space-y-2">
                      {Object.entries(scenario.business_impact).map(([key, value]) => (
                        <div key={key} className="flex items-center justify-between text-sm">
                          <span className="capitalize">{key.replace(/_/g, ' ')}</span>
                          <span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {value > 0 ? '+' : ''}{value}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">Required Actions</h4>
                    <ul className="space-y-1">
                      {scenario.required_actions.map((action, i) => (
                        <li key={i} className="text-sm flex items-start gap-2">
                          <Shield className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SuccessionPlanning;
