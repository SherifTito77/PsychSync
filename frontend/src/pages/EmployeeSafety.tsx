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
  Users,
  FileText,
  BookOpen,
  Plus,
  Search,
  Filter,
  Download,
  Eye
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '@/services/api';

interface SafetyIncident {
  id: string;
  incident_type: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  date_reported: string;
  reporter_id: string;
  affected_user_id?: string;
  location?: string;
}

interface WellnessAssessment {
  id: string;
  user_id: string;
  overall_wellness_score: number;
  alert_level: string;
  risk_factors: string[];
  assessment_date: string;
  metrics: {
    stress_level?: number;
    burnout_risk?: number;
    work_life_balance?: number;
    mental_health_score?: number;
  };
}

interface SafetyMetrics {
  total_incidents: number;
  incident_rate: number;
  severity_distribution: Record<string, number>;
  resolution_time_avg: number;
  compliance_rate: number;
  training_completion_rate: number;
}

interface WellnessMetrics {
  total_assessments: number;
  average_wellness_score: number;
  high_risk_percentage: number;
  trend_direction: string;
  key_risk_factors: string[];
}

const EmployeeSafety: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [incidents, setIncidents] = useState<SafetyIncident[]>([]);
  const [wellnessAssessments, setWellnessAssessments] = useState<WellnessAssessment[]>([]);
  const [safetyMetrics, setSafetyMetrics] = useState<SafetyMetrics | null>(null);
  const [wellnessMetrics, setWellnessMetrics] = useState<WellnessMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [showIncidentForm, setShowIncidentForm] = useState(false);
  const [showWellnessForm, setShowWellnessForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Form states
  const [incidentForm, setIncidentForm] = useState({
    incident_type: '',
    severity: '',
    title: '',
    description: '',
    location: '',
    date_occurred: '',
    affected_user_id: ''
  });

  const [wellnessForm, setWellnessForm] = useState({
    stress_level: '',
    burnout_risk: '',
    work_life_balance: '',
    mental_health_score: '',
    sleep_quality: '',
    job_satisfaction: '',
    engagement_level: '',
    work_hours_per_week: ''
  });

  useEffect(() => {
    loadSafetyData();
  }, [activeTab]);

  const loadSafetyData = async () => {
    setLoading(true);
    try {
      const [incidentsResponse, metricsResponse, wellnessResponse] = await Promise.all([
        api.get('/safety/incidents?limit=50'),
        api.get('/safety/incidents/dashboard'),
        api.get('/safety/wellness/dashboard')
      ]);

      setIncidents(incidentsResponse.data.incidents || []);
      setSafetyMetrics(metricsResponse.data.statistics || null);
      setWellnessMetrics(wellnessResponse.data);

    } catch (error) {
      console.error('Error loading safety data:', error);
      toast.error('Failed to load safety data');
    } finally {
      setLoading(false);
    }
  };

  const handleReportIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/safety/incidents', incidentForm);

      toast.success('Incident reported successfully');
      setShowIncidentForm(false);
      setIncidentForm({
        incident_type: '',
        severity: '',
        title: '',
        description: '',
        location: '',
        date_occurred: '',
        affected_user_id: ''
      });
      loadSafetyData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to report incident');
    }
  };

  const handleWellnessAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/safety/wellness/assessments', {
        ...wellnessForm,
        user_id: 'current-user-id', // Would get from auth context
        assessment_type: 'self_reported'
      });

      toast.success('Wellness assessment completed');
      setShowWellnessForm(false);
      setWellnessForm({
        stress_level: '',
        burnout_risk: '',
        work_life_balance: '',
        mental_health_score: '',
        sleep_quality: '',
        job_satisfaction: '',
        engagement_level: '',
        work_hours_per_week: ''
      });
      loadSafetyData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to complete assessment');
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

  const getAlertLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'elevated': return 'bg-yellow-100 text-yellow-800';
      case 'normal': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredIncidents = incidents.filter(incident =>
    incident.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    incident.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Employee Safety & Wellness</h1>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={() => setShowIncidentForm(true)}
            className="flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Report Incident</span>
          </Button>
          <Button
            onClick={() => setShowWellnessForm(true)}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Wellness Check</span>
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="incidents">Incidents</TabsTrigger>
          <TabsTrigger value="wellness">Wellness</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Incidents</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{safetyMetrics?.total_incidents || 0}</div>
                <p className="text-xs text-gray-500">
                  {safetyMetrics?.incident_rate?.toFixed(1) || '0.0'} per 100 employees/month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Wellness Score</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{wellnessMetrics?.average_wellness_score?.toFixed(1) || '0.0'}</div>
                <p className="text-xs text-gray-500">
                  {wellnessMetrics?.trend_direction || 'Unknown'} trend
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Compliance Rate</CardTitle>
                <FileText className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{safetyMetrics?.compliance_rate?.toFixed(1) || '0.0'}%</div>
                <p className="text-xs text-gray-500">Reporting compliance</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">High Risk Employees</CardTitle>
                <Users className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{wellnessMetrics?.high_risk_percentage?.toFixed(1) || '0.0'}%</div>
                <p className="text-xs text-gray-500">Require attention</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Incidents</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(filteredIncidents || []).slice(0, 5).map((incident) => (
                    <div key={incident.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium">{incident.title}</div>
                        <div className="text-sm text-gray-500">{incident.date_reported}</div>
                      </div>
                      <div className="flex space-x-2">
                        <Badge className={getSeverityColor(incident.severity)}>
                          {incident.severity}
                        </Badge>
                        <Badge variant="outline">{incident.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Wellness Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(wellnessMetrics?.key_risk_factors || []).slice(0, 5).map((factor, index) => (
                    <Alert key={index}>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>{factor}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="incidents" className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search incidents..."
                  className="pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <Button variant="outline" className="flex items-center space-x-2">
                <Filter className="h-4 w-4" />
                <span>Filter</span>
              </Button>
            </div>
            <Button variant="outline" className="flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Export</span>
            </Button>
          </div>

          <div className="space-y-4">
            {filteredIncidents.map((incident) => (
              <Card key={incident.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold">{incident.title}</h3>
                        <Badge className={getSeverityColor(incident.severity)}>
                          {incident.severity}
                        </Badge>
                        <Badge variant="outline">{incident.status}</Badge>
                      </div>
                      <p className="text-gray-600 mb-3">{incident.description}</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>Reported: {new Date(incident.date_reported).toLocaleDateString()}</span>
                        {incident.location && <span>Location: {incident.location}</span>}
                        <span>Type: {incident.incident_type.replace('_', ' ')}</span>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="wellness" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {(wellnessMetrics?.key_risk_factors || []).slice(0, 6).map((factor, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">{factor}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Risk Level</span>
                      <span className="font-medium">High</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-red-600 h-2 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Wellness Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center text-gray-500">
                Wellness trend chart would be displayed here
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Incident Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  Incident trend chart would be displayed here
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Severity Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(safetyMetrics?.severity_distribution || {}).map(([severity, count]) => {
                    const numCount = count as number;
                    return (
                      <div key={severity} className="flex items-center justify-between">
                        <span className="capitalize">{severity}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                severity === 'critical' ? 'bg-red-600' :
                                severity === 'high' ? 'bg-orange-600' :
                                severity === 'medium' ? 'bg-yellow-600' :
                                'bg-green-600'
                              }`}
                              style={{
                                width: `${(numCount / (safetyMetrics?.total_incidents || 1)) * 100}%`
                              }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium w-8">{numCount}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BookOpen className="h-5 w-5" />
                  <span>Safety Policies</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Access organizational safety policies and procedures</p>
                <Button variant="outline" className="w-full">View Policies</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileText className="h-5 w-5" />
                  <span>Emergency Contacts</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Quick access to emergency contacts and procedures</p>
                <Button variant="outline" className="w-full">View Contacts</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="h-5 w-5" />
                  <span>Training Materials</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">Safety training resources and certification materials</p>
                <Button variant="outline" className="w-full">View Training</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Incident Report Modal */}
      {showIncidentForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Report Safety Incident</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleReportIncident} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Incident Type</label>
                    <select
                      value={incidentForm.incident_type}
                      onChange={(e) => setIncidentForm({...incidentForm, incident_type: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select type</option>
                      <option value="physical_injury">Physical Injury</option>
                      <option value="workplace_hazard">Workplace Hazard</option>
                      <option value="equipment_malfunction">Equipment Malfunction</option>
                      <option value="security_breach">Security Breach</option>
                      <option value="medical_emergency">Medical Emergency</option>
                      <option value="psychological_incident">Psychological Incident</option>
                      <option value="bullying_harassment">Bullying/Harassment</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Severity</label>
                    <select
                      value={incidentForm.severity}
                      onChange={(e) => setIncidentForm({...incidentForm, severity: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select severity</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Title</label>
                  <input
                    type="text"
                    value={incidentForm.title}
                    onChange={(e) => setIncidentForm({...incidentForm, title: e.target.value})}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={incidentForm.description}
                    onChange={(e) => setIncidentForm({...incidentForm, description: e.target.value})}
                    rows={4}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Location</label>
                    <input
                      type="text"
                      value={incidentForm.location}
                      onChange={(e) => setIncidentForm({...incidentForm, location: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Date/Time Occurred</label>
                    <input
                      type="datetime-local"
                      value={incidentForm.date_occurred}
                      onChange={(e) => setIncidentForm({...incidentForm, date_occurred: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowIncidentForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Report Incident</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Wellness Assessment Modal */}
      {showWellnessForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Wellness Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleWellnessAssessment} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Stress Level (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={wellnessForm.stress_level}
                      onChange={(e) => setWellnessForm({...wellnessForm, stress_level: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Burnout Risk (0-1)</label>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.1"
                      value={wellnessForm.burnout_risk}
                      onChange={(e) => setWellnessForm({...wellnessForm, burnout_risk: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Work-Life Balance (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={wellnessForm.work_life_balance}
                      onChange={(e) => setWellnessForm({...wellnessForm, work_life_balance: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Mental Health Score (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={wellnessForm.mental_health_score}
                      onChange={(e) => setWellnessForm({...wellnessForm, mental_health_score: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Sleep Quality (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={wellnessForm.sleep_quality}
                      onChange={(e) => setWellnessForm({...wellnessForm, sleep_quality: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Job Satisfaction (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={wellnessForm.job_satisfaction}
                      onChange={(e) => setWellnessForm({...wellnessForm, job_satisfaction: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Engagement Level (1-10)</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={wellnessForm.engagement_level}
                      onChange={(e) => setWellnessForm({...wellnessForm, engagement_level: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Weekly Work Hours</label>
                    <input
                      type="number"
                      min="0"
                      value={wellnessForm.work_hours_per_week}
                      onChange={(e) => setWellnessForm({...wellnessForm, work_hours_per_week: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowWellnessForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Complete Assessment</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default EmployeeSafety;
