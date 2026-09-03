import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import {
  Users,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  RefreshCw,
  ChevronRight,
  BarChart3,
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface TeamRisk {
  team_id: string;
  team_name: string;
  risk_score: number;
  risk_level: string;
  member_count: number;
  burnout_risk: number;
  engagement_score: number;
  turnover_risk: number;
  trend: string;
  top_risk_factors: string[];
}

interface DashboardSummary {
  total_teams: number;
  high_risk_teams: number;
  avg_risk_score: number;
  teams_improving: number;
  teams_declining: number;
}

const TeamRiskDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [teams, setTeams] = useState<TeamRisk[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<TeamRisk | null>(null);

  useEffect(() => {
    loadTeamRiskData();
  }, []);

  const loadTeamRiskData = async () => {
    setLoading(true);
    try {
      const orgId = user?.organization_id || 'demo-org-id';
      const response = await api.get(`/teams/risk-dashboard?organization_id=${orgId}`);
      if (response.data) {
        setSummary(response.data.summary || null);
        setTeams(response.data.teams || []);
      }
    } catch (error) {
      console.error('Error loading team risk data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRiskBarColor = (score: number) => {
    if (score >= 0.75) return 'bg-red-600';
    if (score >= 0.5) return 'bg-orange-500';
    if (score >= 0.25) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'improving') return <TrendingDown className="h-4 w-4 text-green-600" />;
    if (trend === 'declining') return <TrendingUp className="h-4 w-4 text-red-600" />;
    return <Activity className="h-4 w-4 text-gray-500" />;
  };

  const getHeatmapColor = (score: number): string => {
    if (score >= 0.8) return 'bg-red-600 text-white';
    if (score >= 0.6) return 'bg-orange-500 text-white';
    if (score >= 0.4) return 'bg-yellow-400 text-gray-900';
    if (score >= 0.2) return 'bg-green-300 text-gray-900';
    return 'bg-green-500 text-white';
  };

  if (loading && !summary) {
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
          <Users className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Team Risk Dashboard</h1>
            <p className="text-sm text-gray-500">Team-level risk indicators and performance heatmap</p>
          </div>
        </div>
        <Button onClick={loadTeamRiskData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="heatmap">Risk Heatmap</TabsTrigger>
          <TabsTrigger value="details">Team Details</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Teams</CardTitle>
                <Users className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{summary?.total_teams || 0}</div>
                <p className="text-xs text-gray-500">Being monitored</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">High Risk Teams</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{summary?.high_risk_teams || 0}</div>
                <p className="text-xs text-gray-500">Need intervention</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Risk Score</CardTitle>
                <Shield className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {((summary?.avg_risk_score || 0) * 100).toFixed(0)}%
                </div>
                <p className="text-xs text-gray-500">Organization average</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Trend</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{summary?.teams_improving || 0}</div>
                <p className="text-xs text-gray-500">
                  improving / {summary?.teams_declining || 0} declining
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Team Risk Rankings */}
          <Card>
            <CardHeader>
              <CardTitle>Team Risk Rankings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {teams
                  .sort((a, b) => b.risk_score - a.risk_score)
                  .map((team) => (
                    <div
                      key={team.team_id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                      onClick={() => {
                        setSelectedTeam(team);
                        setActiveTab('details');
                      }}
                    >
                      <div className="flex items-center space-x-4 flex-1">
                        <div className="flex-1">
                          <h4 className="font-semibold">{team.team_name}</h4>
                          <p className="text-sm text-gray-500">{team.member_count} members</p>
                        </div>
                        <div className="w-48">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm text-gray-500">Risk</span>
                            <span className="text-sm font-medium">
                              {(team.risk_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all ${getRiskBarColor(team.risk_score)}`}
                              style={{ width: `${team.risk_score * 100}%` }}
                            />
                          </div>
                        </div>
                        <Badge className={getRiskColor(team.risk_level)}>{team.risk_level}</Badge>
                        {getTrendIcon(team.trend)}
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-4" />
                    </div>
                  ))}
              </div>

              {teams.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium">No team data available</p>
                  <p className="text-sm">Team risk data will appear once assessments are completed</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Heatmap Tab */}
        <TabsContent value="heatmap" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Risk Heatmap</CardTitle>
            </CardHeader>
            <CardContent>
              {teams.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th className="text-left p-3 font-medium text-gray-600">Team</th>
                        <th className="text-center p-3 font-medium text-gray-600">Overall Risk</th>
                        <th className="text-center p-3 font-medium text-gray-600">Burnout</th>
                        <th className="text-center p-3 font-medium text-gray-600">Engagement</th>
                        <th className="text-center p-3 font-medium text-gray-600">Turnover</th>
                        <th className="text-center p-3 font-medium text-gray-600">Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      {teams.map((team) => (
                        <tr key={team.team_id} className="border-t">
                          <td className="p-3 font-medium">{team.team_name}</td>
                          <td className="p-3">
                            <div className={`text-center rounded-lg p-2 ${getHeatmapColor(team.risk_score)}`}>
                              {(team.risk_score * 100).toFixed(0)}%
                            </div>
                          </td>
                          <td className="p-3">
                            <div className={`text-center rounded-lg p-2 ${getHeatmapColor(team.burnout_risk)}`}>
                              {(team.burnout_risk * 100).toFixed(0)}%
                            </div>
                          </td>
                          <td className="p-3">
                            <div className={`text-center rounded-lg p-2 ${getHeatmapColor(1 - team.engagement_score)}`}>
                              {(team.engagement_score * 100).toFixed(0)}%
                            </div>
                          </td>
                          <td className="p-3">
                            <div className={`text-center rounded-lg p-2 ${getHeatmapColor(team.turnover_risk)}`}>
                              {(team.turnover_risk * 100).toFixed(0)}%
                            </div>
                          </td>
                          <td className="p-3 text-center">
                            {getTrendIcon(team.trend)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  <div className="flex items-center justify-center space-x-2 mt-6 text-sm text-gray-500">
                    <span>Low Risk</span>
                    <div className="flex space-x-1">
                      <div className="w-8 h-4 bg-green-500 rounded" />
                      <div className="w-8 h-4 bg-green-300 rounded" />
                      <div className="w-8 h-4 bg-yellow-400 rounded" />
                      <div className="w-8 h-4 bg-orange-500 rounded" />
                      <div className="w-8 h-4 bg-red-600 rounded" />
                    </div>
                    <span>High Risk</span>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No data available for heatmap visualization</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-6">
          {selectedTeam ? (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{selectedTeam.team_name}</CardTitle>
                    <Badge className={getRiskColor(selectedTeam.risk_level)}>
                      {selectedTeam.risk_level} risk
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="text-center">
                      <p className="text-sm text-gray-500 mb-1">Overall Risk</p>
                      <p className="text-3xl font-bold">{(selectedTeam.risk_score * 100).toFixed(0)}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500 mb-1">Burnout Risk</p>
                      <p className="text-3xl font-bold">{(selectedTeam.burnout_risk * 100).toFixed(0)}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500 mb-1">Engagement</p>
                      <p className="text-3xl font-bold">{(selectedTeam.engagement_score * 100).toFixed(0)}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500 mb-1">Turnover Risk</p>
                      <p className="text-3xl font-bold">{(selectedTeam.turnover_risk * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {selectedTeam.top_risk_factors.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Top Risk Factors</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {selectedTeam.top_risk_factors.map((factor, idx) => (
                        <div key={idx} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                          <AlertTriangle className="h-4 w-4 text-orange-600 flex-shrink-0" />
                          <span>{factor}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="p-12 text-center text-gray-500">
                <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium">Select a team to view details</p>
                <p className="text-sm">Click on a team in the Overview or Heatmap tab</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TeamRiskDashboard;
