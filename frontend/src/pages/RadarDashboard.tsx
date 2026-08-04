import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import api from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import {
  Radar,
  Shield,
  AlertTriangle,
  Activity,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  XCircle,
  Eye,
  RefreshCw,
  Zap,
  Target,
  Flame,
  Snowflake,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { ConcentricZoneVisualization } from '@/components/radar/ConcentricZoneVisualization';
import { ZoneMetrics } from '@/components/radar/ZoneMetrics';
import { HotspotList } from '@/components/radar/HotspotList';
import { ZoneHistoryChart } from '@/components/radar/ZoneHistoryChart';

// Types
interface ZoneClassification {
  zone: string;
  zone_label: string;
  overall_risk_score: number;
  confidence: number;
  risk_components: Array<{ component: string; risk: number; weight: number }>;
  recommendation: string;
}

interface ConcentricZones {
  inner_zone: { name: string; risk_score: number; indicator_count: number; zone: string };
  middle_zone: { name: string; risk_score: number; health_score: number; zone: string };
  outer_zone: { name: string; risk_score: number; safety_score: number | null; zone: string };
}

interface Hotspot {
  type: string;
  severity: number;
  description: string;
  priority: string;
}

interface RadarData {
  organization_id: string;
  team_id: string | null;
  analysis_date: string;
  period_days: number;
  toxicity_analysis: any;
  early_warnings: any;
  behavioral_patterns: any;
  psychological_safety: any;
  zone_classification: ZoneClassification;
  concentric_zones: ConcentricZones;
  active_interventions: any;
  trends: any;
  hotspots: Hotspot[];
}

const RadarDashboard: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Data state
  const [radarData, setRadarData] = useState<RadarData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    loadRadarData();
  }, [selectedPeriod]);

  const loadRadarData = async () => {
    setLoading(true);
    try {
      const orgId = user?.organization_id || 'demo-org-id';

      const response = await api.post('/radar/view', {
        organization_id: orgId,
        period_days: selectedPeriod,
      });

      if (response.data) {
        setRadarData(response.data);
      }
    } catch (error: any) {
      console.error('Error loading radar data:', error);
      toast.error(error.response?.data?.detail || 'Failed to load radar data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadRadarData();
    setRefreshing(false);
    toast.success('Radar data refreshed');
  };

  const getZoneColor = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return 'bg-red-100 text-red-800 border-red-200';
      case 'yellow': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'green': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getZoneIcon = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return <Flame className="h-5 w-5 text-red-600" />;
      case 'yellow': return <Zap className="h-5 w-5 text-yellow-600" />;
      case 'green': return <Snowflake className="h-5 w-5 text-green-600" />;
      default: return <Shield className="h-5 w-5 text-gray-600" />;
    }
  };

  const getRiskPercentage = (score: number) => {
    return (score * 100).toFixed(1);
  };

  if (loading && !radarData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const zoneClass = radarData?.zone_classification;
  const concentricZones = radarData?.concentric_zones;
  const hotspots = radarData?.hotspots || [];

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Radar className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">PsychSync Radar</h1>
            <p className="text-sm text-gray-500">360° organizational health monitoring system</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Zone Classification Banner */}
      {zoneClass && (
        <Alert className={`border-2 ${getZoneColor(zoneClass.zone).split(' ')[2]}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getZoneIcon(zoneClass.zone)}
              <div>
                <AlertDescription className="text-lg font-semibold">
                  {zoneClass.zone_label} Zone - Risk Score: {getRiskPercentage(zoneClass.overall_risk_score)}%
                </AlertDescription>
                <p className="text-sm text-gray-600 mt-1">{zoneClass.recommendation}</p>
              </div>
            </div>
            <Badge className={getZoneColor(zoneClass.zone)} size="lg">
              Confidence: {getRiskPercentage(zoneClass.confidence)}%
            </Badge>
          </div>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="zones">Concentric Zones</TabsTrigger>
          <TabsTrigger value="hotspots">Hotspots</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="analysis">Deep Analysis</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Current Zone</CardTitle>
                {getZoneIcon(zoneClass?.zone || 'green')}
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold capitalize">{zoneClass?.zone_label || 'Unknown'}</div>
                <p className="text-xs text-gray-500">
                  Risk: {getRiskPercentage(zoneClass?.overall_risk_score || 0)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Toxicity Patterns</CardTitle>
                <AlertTriangle className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {radarData?.toxicity_analysis?.patterns_detected?.length || 0}
                </div>
                <p className="text-xs text-gray-500">Detected patterns</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Psych Safety</CardTitle>
                <Users className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {radarData?.psychological_safety?.overall_safety_score
                    ? (radarData.psychological_safety.overall_safety_score * 100).toFixed(0)
                    : 'N/A'}%
                </div>
                <p className="text-xs text-gray-500">Safety score</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Interventions</CardTitle>
                <CheckCircle className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {radarData?.active_interventions?.active_count || 0}
                </div>
                <p className="text-xs text-gray-500">In progress</p>
              </CardContent>
            </Card>
          </div>

          {/* Risk Components Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Risk Component Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {zoneClass?.risk_components.map((component, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium capitalize">
                        {component.component.replace(/_/g, ' ')}
                      </span>
                      <span className="text-sm text-gray-600">
                        {getRiskPercentage(component.risk)}% (weight: {(component.weight * 100).toFixed(0)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all ${
                          component.risk >= 0.6 ? 'bg-red-600' :
                          component.risk >= 0.3 ? 'bg-yellow-600' :
                          'bg-green-600'
                        }`}
                        style={{ width: `${component.risk * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Behavioral Health */}
          <Card>
            <CardHeader>
              <CardTitle>Behavioral Health Indicators</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-500 mb-2">Behavioral Health Score</p>
                  <div className="text-2xl font-bold">
                    {getRiskPercentage(radarData?.behavioral_patterns?.behavioral_health_score || 1.0)}%
                  </div>
                  <Badge
                    className={
                      (radarData?.behavioral_patterns?.behavioral_health_score || 1.0) >= 0.7
                        ? 'bg-green-100 text-green-800'
                        : (radarData?.behavioral_patterns?.behavioral_health_score || 1.0) >= 0.4
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }
                  >
                    {radarData?.behavioral_patterns?.trend_direction === 'decreasing' ? 'Improving' :
                     radarData?.behavioral_patterns?.trend_direction === 'increasing' ? 'Declining' : 'Stable'}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-2">Pattern Diversity</p>
                  <div className="text-2xl font-bold">
                    {getRiskPercentage(radarData?.behavioral_patterns?.pattern_diversity || 0)}%
                  </div>
                  <p className="text-xs text-gray-500">
                    {radarData?.behavioral_patterns?.total_patterns || 0} patterns detected
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-2">Pattern Frequency</p>
                  <div className="text-2xl font-bold">
                    {radarData?.behavioral_patterns?.pattern_frequency || 0}/day
                  </div>
                  <p className="text-xs text-gray-500">
                    {radarData?.behavioral_patterns?.most_common_patterns?.[0]?.type || 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Early Warnings */}
          <Card>
            <CardHeader>
              <CardTitle>Early Warning Indicators</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <p className="text-sm text-gray-500 mb-2">Warning Level</p>
                  <Badge
                    className={
                      radarData?.early_warnings?.warning_level === 'high'
                        ? 'bg-red-100 text-red-800'
                        : radarData?.early_warnings?.warning_level === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : radarData?.early_warnings?.warning_level === 'low'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-green-100 text-green-800'
                    }
                    size="lg"
                  >
                    {radarData?.early_warnings?.warning_level?.toUpperCase() || 'NONE'}
                  </Badge>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500 mb-2">High-Risk Patterns</p>
                  <div className="text-2xl font-bold">
                    {radarData?.early_warnings?.high_risk_patterns_count || 0}
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-500 mb-2">Critical Patterns</p>
                  <div className="text-2xl font-bold text-red-600">
                    {radarData?.early_warnings?.critical_patterns_count || 0}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Concentric Zones Tab */}
        <TabsContent value="zones" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Concentric Zone Visualization</CardTitle>
              <p className="text-sm text-gray-500">
                Visual representation of organizational health across three zones
              </p>
            </CardHeader>
            <CardContent>
              {concentricZones && (
                <ConcentricZoneVisualization zones={concentricZones} />
              )}
            </CardContent>
          </Card>

          {concentricZones && (
            <ZoneMetrics zones={concentricZones} />
          )}
        </TabsContent>

        {/* Hotspots Tab */}
        <TabsContent value="hotspots" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Identified Hotspots</CardTitle>
              <p className="text-sm text-gray-500">
                Priority areas requiring attention
              </p>
            </CardHeader>
            <CardContent>
              <HotspotList hotspots={hotspots} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Zone History</CardTitle>
              <p className="text-sm text-gray-500">
                Historical zone classifications over time
              </p>
            </CardHeader>
            <CardContent>
              <ZoneHistoryChart organizationId={user?.organization_id || 'demo-org-id'} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Deep Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Toxicity Analysis Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">Detected Patterns</p>
                  <div className="space-y-2">
                    {radarData?.toxicity_analysis?.patterns_detected?.slice(0, 5).map((pattern: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium capitalize">{pattern.type?.replace(/_/g, ' ')}</p>
                          <p className="text-sm text-gray-500">Frequency: {pattern.frequency}</p>
                        </div>
                        <Badge
                          className={
                            pattern.severity_score >= 0.7 ? 'bg-red-100 text-red-800' :
                            pattern.severity_score >= 0.4 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }
                        >
                          {(pattern.severity_score * 100).toFixed(0)}% severity
                        </Badge>
                      </div>
                    )) || <p className="text-gray-500">No patterns detected</p>}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium mb-2">Recommendations</p>
                  <div className="space-y-2">
                    {radarData?.toxicity_analysis?.recommendations?.slice(0, 3).map((rec: any, idx: number) => (
                      <Alert key={idx}>
                        <Target className="h-4 w-4" />
                        <AlertDescription>
                          <p className="font-medium">{rec.title}</p>
                          <p className="text-sm text-gray-600">{rec.description}</p>
                          <p className="text-xs text-gray-500 mt-2">Timeline: {rec.timeline}</p>
                        </AlertDescription>
                      </Alert>
                    )) || <p className="text-gray-500">No recommendations available</p>}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RadarDashboard;
