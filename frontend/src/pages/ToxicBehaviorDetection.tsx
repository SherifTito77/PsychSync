import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  FileText,
  MessageSquare,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Download,
  Search
} from 'lucide-react';
import { toast } from 'react-hot-toast';

// Types
interface ToxicPattern {
  id: string;
  pattern_type: string;
  severity_level: string;
  confidence_score: number;
  detection_date: string;
  frequency_score: number;
  impact_score: number;
  intervention_required: boolean;
  intervention_priority: string;
  status: string;
  behavioral_indicators: string[];
  evidence_summary: string;
  risk_score: number;
}

interface ToxicityAnalysis {
  toxicity_level: string;
  risk_score: number;
  patterns_detected: any[];
  behavioral_indicators: Record<string, any>;
  risk_factors: Array<{ type: string; description: string; severity: number }>;
  recommendations: Array<{ priority: string; category: string; title: string; description: string; actions: string[]; timeline: string }>;
  data_insufficient: boolean;
  communications_analyzed: number;
}

interface DashboardSummary {
  total_patterns: number;
  critical_patterns: number;
  high_patterns: number;
  intervention_required: number;
  active_interventions: number;
  psychological_safety_score: number | null;
  psychological_safety_risk_level: string | null;
  pattern_breakdown: Record<string, number>;
}

const ToxicBehaviorDetection: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Data state
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [patterns, setPatterns] = useState<ToxicPattern[]>([]);
  const [analysis, setAnalysis] = useState<ToxicityAnalysis | null>(null);
  const [selectedPattern, setSelectedPattern] = useState<ToxicPattern | null>(null);

  // Anonymous report form
  const [showReportForm, setShowReportForm] = useState(false);
  const [reportForm, setReportForm] = useState({
    report_type: 'bullying',
    description: '',
    perpetrator_hint: ''
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const orgId = localStorage.getItem('organization_id') || 'demo-org-id';

      const response = await fetch(`/api/v1/toxicity/dashboard?organization_id=${orgId}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardSummary(data.summary);
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const orgId = localStorage.getItem('organization_id') || 'demo-org-id';

      const response = await fetch('/api/v1/toxicity/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          organization_id: orgId,
          period_days: 30
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
        toast.success(`Analysis complete: ${data.toxicity_level.toUpperCase()} toxicity level detected`);
        loadDashboardData();
        loadPatterns();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Analysis failed');
      }
    } catch (error) {
      console.error('Error running analysis:', error);
      toast.error('Failed to run analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  const loadPatterns = async () => {
    try {
      const orgId = localStorage.getItem('organization_id') || 'demo-org-id';

      const response = await fetch(`/api/v1/toxicity/patterns?organization_id=${orgId}&limit=50`);
      if (response.ok) {
        const data = await response.json();
        setPatterns(data.patterns || []);
      }
    } catch (error) {
      console.error('Error loading patterns:', error);
    }
  };

  const handleSubmitAnonymousReport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const orgId = localStorage.getItem('organization_id') || 'demo-org-id';

      const response = await fetch('/api/v1/toxicity/anonymous-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...reportForm,
          organization_id: orgId
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Report submitted! Tracking ID: ${data.tracking_id}`);
        setShowReportForm(false);
        setReportForm({ report_type: 'bullying', description: '', perpetrator_hint: '' });
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to submit report');
      }
    } catch (error) {
      toast.error('Error submitting report');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRiskLevelColor = (level: string | null) => {
    if (!level) return 'bg-gray-100 text-gray-800';
    switch (level.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading && !dashboardSummary) {
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
          <Shield className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Toxic Behavior Detection</h1>
            <p className="text-sm text-gray-500">AI-powered workplace toxicity analysis and prevention</p>
          </div>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={runAnalysis}
            disabled={analyzing}
            className="flex items-center space-x-2"
          >
            <Activity className="h-4 w-4" />
            <span>{analyzing ? 'Analyzing...' : 'Run Analysis'}</span>
          </Button>
          <Button
            onClick={() => setShowReportForm(true)}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <MessageSquare className="h-4 w-4" />
            <span>Anonymous Report</span>
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="patterns">Patterns</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="interventions">Interventions</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Patterns</CardTitle>
                <AlertTriangle className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboardSummary?.total_patterns || 0}</div>
                <p className="text-xs text-gray-500">Detected patterns (30 days)</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Critical/High</CardTitle>
                <XCircle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {(dashboardSummary?.critical_patterns || 0) + (dashboardSummary?.high_patterns || 0)}
                </div>
                <p className="text-xs text-gray-500">Require immediate attention</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Psych Safety Score</CardTitle>
                <Users className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardSummary?.psychological_safety_score?.toFixed(1) || 'N/A'}
                </div>
                <Badge className={getRiskLevelColor(dashboardSummary?.psychological_safety_risk_level || null)}>
                  {dashboardSummary?.psychological_safety_risk_level || 'Unknown'} risk
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Interventions</CardTitle>
                <CheckCircle className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboardSummary?.active_interventions || 0}</div>
                <p className="text-xs text-gray-500">Currently in progress</p>
              </CardContent>
            </Card>
          </div>

          {/* Analysis Results */}
          {analysis && (
            <Card className="border-2 border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>Latest Analysis Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Toxicity Level</p>
                    <Badge className={getSeverityColor(analysis.toxicity_level)} size="lg">
                      {analysis.toxicity_level.toUpperCase()}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Risk Score</p>
                    <p className="text-2xl font-bold">{(analysis.risk_score * 100).toFixed(1)}%</p>
                  </div>
                </div>

                {analysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Recommendations</h4>
                    <div className="space-y-2">
                      {analysis.recommendations.slice(0, 3).map((rec, index) => (
                        <Alert key={index}>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            <p className="font-medium">{rec.title}</p>
                            <p className="text-sm text-gray-600">{rec.description}</p>
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Pattern Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Pattern Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(dashboardSummary?.pattern_breakdown || {}).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="capitalize">{type.replace(/_/g, ' ')}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${(count / (dashboardSummary?.total_patterns || 1)) * 100}%`
                          }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium w-8">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Patterns Tab */}
        <TabsContent value="patterns" className="space-y-4">
          <div className="flex items-center justify-between">
            <Button onClick={loadPatterns} variant="outline">
              Refresh Patterns
            </Button>
          </div>

          <div className="space-y-4">
            {patterns.map((pattern) => (
              <Card key={pattern.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold capitalize">
                          {pattern.pattern_type.replace(/_/g, ' ')}
                        </h3>
                        <Badge className={getSeverityColor(pattern.severity_level)}>
                          {pattern.severity_level}
                        </Badge>
                        <Badge variant="outline">{pattern.status}</Badge>
                        {pattern.intervention_required && (
                          <Badge className="bg-red-100 text-red-800">Action Required</Badge>
                        )}
                      </div>

                      <p className="text-gray-600 mb-3">{pattern.evidence_summary}</p>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Confidence:</span>
                          <span className="ml-1 font-medium">{(pattern.confidence_score * 100).toFixed(0)}%</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Frequency:</span>
                          <span className="ml-1 font-medium">{pattern.frequency_score.toFixed(1)}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Impact:</span>
                          <span className="ml-1 font-medium">{pattern.impact_score.toFixed(1)}/10</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Detected:</span>
                          <span className="ml-1 font-medium">
                            {new Date(pattern.detection_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      {pattern.behavioral_indicators.length > 0 && (
                        <div className="mt-3">
                          <p className="text-sm text-gray-500 mb-1">Behavioral Indicators:</p>
                          <div className="flex flex-wrap gap-2">
                            {pattern.behavioral_indicators.slice(0, 3).map((indicator, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {indicator.replace(/_/g, ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedPattern(pattern)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {patterns.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium">No toxic patterns detected</p>
                <p className="text-sm">Run an analysis to scan for toxic behaviors</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Behavioral Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center text-gray-500">
                Behavioral trends chart would be displayed here
              </div>
            </CardContent>
          </Card>

          {analysis?.behavioral_indicators && (
            <Card>
              <CardHeader>
                <CardTitle>Behavioral Indicators</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Negative Communication Ratio</p>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-red-600 h-3 rounded-full"
                        style={{
                          width: `${(analysis.behavioral_indicators.negative_communication_ratio || 0) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-2">High Stress Ratio</p>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-orange-600 h-3 rounded-full"
                        style={{
                          width: `${(analysis.behavioral_indicators.high_stress_ratio || 0) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Conflict Indicator Ratio</p>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-yellow-600 h-3 rounded-full"
                        style={{
                          width: `${(analysis.behavioral_indicators.conflict_indicator_ratio || 0) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Interventions Tab */}
        <TabsContent value="interventions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Intervention Management</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analysis?.recommendations.map((rec, index) => (
                  <Card key={index} className="border-l-4 border-blue-600">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <Badge className={getSeverityColor(rec.priority)}>{rec.priority}</Badge>
                            <h4 className="font-semibold">{rec.title}</h4>
                          </div>
                          <p className="text-sm text-gray-600 mb-3">{rec.description}</p>
                          <div className="text-sm">
                            <p className="font-medium mb-1">Recommended Actions:</p>
                            <ul className="list-disc list-inside text-gray-600 space-y-1">
                              {rec.actions.map((action, idx) => (
                                <li key={idx}>{action}</li>
                              ))}
                            </ul>
                          </div>
                          <p className="text-xs text-gray-500 mt-2">Timeline: {rec.timeline}</p>
                        </div>
                        <Button size="sm">Create Intervention</Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {(!analysis || analysis.recommendations.length === 0) && (
                <div className="text-center text-gray-500 py-8">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No interventions required at this time</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Submit Anonymous Report</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Report toxic behavior anonymously. Your identity will not be revealed.
                </p>
                <Button
                  onClick={() => setShowReportForm(true)}
                  className="w-full"
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Submit Anonymous Report
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Check Report Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Enter tracking ID (e.g., TOXIC-XXXXXXXX)"
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Button variant="outline" className="w-full">
                    Check Status
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Export Reports</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button variant="outline" className="flex items-center justify-center space-x-2">
                  <Download className="h-4 w-4" />
                  <span>Export Patterns</span>
                </Button>
                <Button variant="outline" className="flex items-center justify-center space-x-2">
                  <Download className="h-4 w-4" />
                  <span>Export Interventions</span>
                </Button>
                <Button variant="outline" className="flex items-center justify-center space-x-2">
                  <Download className="h-4 w-4" />
                  <span>Export Trends</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Anonymous Report Modal */}
      {showReportForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Anonymous Toxic Behavior Report</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmitAnonymousReport} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Type of Toxic Behavior</label>
                  <select
                    value={reportForm.report_type}
                    onChange={(e) => setReportForm({ ...reportForm, report_type: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="bullying">Bullying</option>
                    <option value="harassment">Harassment</option>
                    <option value="verbal_abuse">Verbal Abuse</option>
                    <option value="micromanagement">Micromanagement</option>
                    <option value="exclusion">Exclusion</option>
                    <option value="gaslighting">Gaslighting</option>
                    <option value="discrimination">Discrimination</option>
                    <option value="power_abuse">Power Abuse (Gapjil)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={reportForm.description}
                    onChange={(e) => setReportForm({ ...reportForm, description: e.target.value })}
                    rows={6}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Please describe the incident or behavior pattern in detail..."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Perpetrator Hint (Optional)
                  </label>
                  <input
                    type="text"
                    value={reportForm.perpetrator_hint}
                    onChange={(e) => setReportForm({ ...reportForm, perpetrator_hint: e.target.value })}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Role, department, or any identifying information (without names)"
                  />
                </div>

                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    Your report will be submitted anonymously. A tracking ID will be provided for follow-up.
                    HR will review your report within 24-48 hours.
                  </AlertDescription>
                </Alert>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowReportForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Submit Report</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ToxicBehaviorDetection;
