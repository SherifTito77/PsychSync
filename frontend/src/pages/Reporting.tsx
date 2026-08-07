import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText,
  Download,
  Calendar,
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  Filter,
  Search,
  Plus,
  Settings,
  BarChart3,
  PieChart,
  FileSpreadsheet,
  FileJson,
  Mail,
  Webhook,
  Eye,
  Trash2,
  Edit,
  Play
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Report {
  id: string;
  title: string;
  description: string;
  report_type: string;
  status: string;
  file_format: string;
  file_name?: string;
  file_size?: number;
  record_count?: number;
  download_count: number;
  created_at: string;
  generation_started?: string;
  generation_completed?: string;
  expires_at?: string;
  is_public: boolean;
  template_id?: string;
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  report_type: string;
  category?: string;
  tags: string[];
  is_public: boolean;
  usage_count: number;
  created_at: string;
}

interface ReportSchedule {
  id: string;
  name: string;
  description: string;
  frequency: string;
  next_run?: string;
  last_run?: string;
  template_id: string;
  delivery_method: string;
  default_format: string;
  is_active: boolean;
  success_count: number;
  failure_count: number;
}

interface ReportAnalytics {
  period: {
    start_date: string;
    end_date: string;
  };
  generation_stats: {
    total_reports: number;
    completed_reports: number;
    failed_reports: number;
    success_rate: number;
  };
  format_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
  performance: {
    avg_generation_time_seconds: number;
  };
  popular_templates: Array<{
    name: string;
    usage_count: number;
  }>;
}

const Reporting: React.FC = () => {
  const [activeTab, setActiveTab] = useState('reports');
  const [reports, setReports] = useState<Report[]>([]);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [schedules, setSchedules] = useState<ReportSchedule[]>([]);
  const [analytics, setAnalytics] = useState<ReportAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Modal states
  const [showReportForm, setShowReportForm] = useState(false);
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);

  // Form states
  const [reportForm, setReportForm] = useState({
    title: '',
    description: '',
    report_type: 'custom',
    template_id: '',
    export_format: 'pdf',
    data_range_start: '',
    data_range_end: '',
    team_id: '',
    is_public: false,
    retention_days: 90
  });

  const [templateForm, setTemplateForm] = useState({
    name: '',
    description: '',
    report_type: 'custom',
    category: '',
    tags: '',
    is_public: false
  });

  const [scheduleForm, setScheduleForm] = useState({
    name: '',
    description: '',
    template_id: '',
    frequency: 'weekly',
    delivery_method: 'download',
    delivery_config: '',
    end_date: '',
    default_format: 'pdf'
  });

  useEffect(() => {
    loadReportingData();
  }, [activeTab]);

  const loadReportingData = async () => {
    setLoading(true);
    try {
      const [reportsResponse, templatesResponse, schedulesResponse, analyticsResponse] = await Promise.all([
        fetch('/api/v1/reports/list?limit=100'),
        fetch('/api/v1/reports/templates'),
        fetch('/api/v1/reports/schedules'),
        fetch('/api/v1/reports/analytics?days=30')
      ]);

      const reportsData = await reportsResponse.json();
      const templatesData = await templatesResponse.json();
      const schedulesData = await schedulesResponse.json();
      const analyticsData = await analyticsResponse.json();

      setReports(reportsData.reports || []);
      setTemplates(templatesData || []);
      setSchedules(schedulesData || []);
      setAnalytics(analyticsData);

    } catch (error) {
      console.error('Error loading reporting data:', error);
      toast.error('Failed to load reporting data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...reportForm,
          template_id: reportForm.template_id || undefined,
          data_range_start: reportForm.data_range_start ? new Date(reportForm.data_range_start) : undefined,
          data_range_end: reportForm.data_range_end ? new Date(reportForm.data_range_end) : undefined,
          team_id: reportForm.team_id || undefined
        })
      });

      if (response.ok) {
        toast.success('Report generation started successfully');
        setShowReportForm(false);
        setReportForm({
          title: '',
          description: '',
          report_type: 'custom',
          template_id: '',
          export_format: 'pdf',
          data_range_start: '',
          data_range_end: '',
          team_id: '',
          is_public: false,
          retention_days: 90
        });
        loadReportingData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to generate report');
      }
    } catch (error) {
      toast.error('Error generating report');
    }
  };

  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/reports/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...templateForm,
          tags: templateForm.tags.split(',').map(tag => tag.trim()).filter(Boolean)
        })
      });

      if (response.ok) {
        toast.success('Template created successfully');
        setShowTemplateForm(false);
        setTemplateForm({
          name: '',
          description: '',
          report_type: 'custom',
          category: '',
          tags: '',
          is_public: false
        });
        loadReportingData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create template');
      }
    } catch (error) {
      toast.error('Error creating template');
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/reports/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...scheduleForm,
          end_date: scheduleForm.end_date ? new Date(scheduleForm.end_date) : undefined,
          delivery_config: scheduleForm.delivery_method === 'email'
            ? { recipients: [] }
            : scheduleForm.delivery_method === 'webhook'
            ? { url: '' }
            : {}
        })
      });

      if (response.ok) {
        toast.success('Schedule created successfully');
        setShowScheduleForm(false);
        setScheduleForm({
          name: '',
          description: '',
          template_id: '',
          frequency: 'weekly',
          delivery_method: 'download',
          delivery_config: '',
          end_date: '',
          default_format: 'pdf'
        });
        loadReportingData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create schedule');
      }
    } catch (error) {
      toast.error('Error creating schedule');
    }
  };

  const handleDownloadReport = async (reportId: string) => {
    try {
      const response = await fetch(`/api/v1/reports/${reportId}/download`);
      if (response.ok) {
        const data = await response.json();
        // In a real implementation, this would trigger a file download
        toast.success('Report download started');
        window.open(data.download_url, '_blank');
      } else {
        toast.error('Failed to download report');
      }
    } catch (error) {
      toast.error('Error downloading report');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'generating': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'scheduled': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format.toLowerCase()) {
      case 'pdf': return <FileText className="h-4 w-4" />;
      case 'excel': return <FileSpreadsheet className="h-4 w-4" />;
      case 'csv': return <FileSpreadsheet className="h-4 w-4" />;
      case 'json': return <FileJson className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getDeliveryIcon = (method: string) => {
    switch (method.toLowerCase()) {
      case 'email': return <Mail className="h-4 w-4" />;
      case 'webhook': return <Webhook className="h-4 w-4" />;
      case 'download': return <Download className="h-4 w-4" />;
      default: return <Download className="h-4 w-4" />;
    }
  };

  const filteredReports = reports.filter(report =>
    report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.description.toLowerCase().includes(searchTerm.toLowerCase())
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
          <BarChart3 className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Advanced Reporting</h1>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={() => setShowReportForm(true)}
            className="flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Generate Report</span>
          </Button>
          <Button
            onClick={() => setShowScheduleForm(true)}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <Calendar className="h-4 w-4" />
            <span>Schedule Report</span>
          </Button>
        </div>
      </div>

      {/* Analytics Overview */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
              <FileText className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.generation_stats.total_reports}</div>
              <p className="text-xs text-gray-500">
                {analytics.generation_stats.success_rate.toFixed(1)}% success rate
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Generation Time</CardTitle>
              <Clock className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {analytics.performance.avg_generation_time_seconds.toFixed(1)}s
              </div>
              <p className="text-xs text-gray-500">Per report</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Schedules</CardTitle>
              <Calendar className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{schedules.filter(s => s.is_active).length}</div>
              <p className="text-xs text-gray-500">Automated reports</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Available Templates</CardTitle>
              <Settings className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{templates.length}</div>
              <p className="text-xs text-gray-500">Report templates</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="schedules">Schedules</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="reports" className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search reports..."
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
            <Button
              onClick={() => setShowTemplateForm(true)}
              variant="outline"
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>New Template</span>
            </Button>
          </div>

          <div className="space-y-4">
            {filteredReports.map((report) => (
              <Card key={report.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold">{report.title}</h3>
                        <Badge className={getStatusColor(report.status)}>
                          {report.status}
                        </Badge>
                        <div className="flex items-center space-x-1">
                          {getFormatIcon(report.file_format)}
                          <span className="text-sm text-gray-500">{report.file_format.toUpperCase()}</span>
                        </div>
                      </div>
                      <p className="text-gray-600 mb-3">{report.description}</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
                        <span>Downloads: {report.download_count}</span>
                        {report.record_count && <span>Records: {report.record_count}</span>}
                        {report.file_size && <span>Size: {(report.file_size / 1024).toFixed(1)} KB</span>}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      {report.status === 'completed' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadReport(report.id)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Report Templates</h2>
            <Button
              onClick={() => setShowTemplateForm(true)}
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Create Template</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <Card key={template.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <div className="flex space-x-2">
                      {template.is_public && (
                        <Badge variant="secondary">Public</Badge>
                      )}
                      <Badge variant="outline">{template.report_type}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">{template.description}</p>
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>Used {template.usage_count} times</span>
                    <span>{new Date(template.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="mt-4 flex space-x-2">
                    <Button variant="outline" size="sm" className="flex-1">
                      Use Template
                    </Button>
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="schedules" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Report Schedules</h2>
            <Button
              onClick={() => setShowScheduleForm(true)}
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>New Schedule</span>
            </Button>
          </div>

          <div className="space-y-4">
            {schedules.map((schedule) => (
              <Card key={schedule.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold">{schedule.name}</h3>
                        <Badge variant={schedule.is_active ? "default" : "secondary"}>
                          {schedule.is_active ? "Active" : "Inactive"}
                        </Badge>
                        <Badge variant="outline">{schedule.frequency}</Badge>
                      </div>
                      <p className="text-gray-600 mb-3">{schedule.description}</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
                        <div className="flex items-center space-x-2">
                          {getDeliveryIcon(schedule.delivery_method)}
                          <span>{schedule.delivery_method}</span>
                        </div>
                        <div>
                          <span className="font-medium">Success Rate:</span> {schedule.success_count + schedule.failure_count > 0
                            ? ((schedule.success_count / (schedule.success_count + schedule.failure_count)) * 100).toFixed(1)
                            : 0}%
                        </div>
                        {schedule.next_run && (
                          <div>
                            <span className="font-medium">Next Run:</span> {new Date(schedule.next_run).toLocaleDateString()}
                          </div>
                        )}
                        {schedule.last_run && (
                          <div>
                            <span className="font-medium">Last Run:</span> {new Date(schedule.last_run).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          {analytics && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Format Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(analytics.format_distribution).map(([format, count]) => {
                        const numCount = count as number;
                        return (
                          <div key={format} className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              {getFormatIcon(format)}
                              <span className="capitalize">{format}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{
                                    width: `${(numCount / analytics.generation_stats.total_reports) * 100}%`
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

                <Card>
                  <CardHeader>
                    <CardTitle>Popular Templates</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {analytics.popular_templates.map((template, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span>{template.name}</span>
                          <Badge variant="outline">{template.usage_count} uses</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Generation Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {analytics.generation_stats.completed_reports}
                      </div>
                      <p className="text-sm text-gray-500">Completed</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {analytics.generation_stats.failed_reports}
                      </div>
                      <p className="text-sm text-gray-500">Failed</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {analytics.generation_stats.success_rate.toFixed(1)}%
                      </div>
                      <p className="text-sm text-gray-500">Success Rate</p>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {analytics.performance.avg_generation_time_seconds.toFixed(1)}s
                      </div>
                      <p className="text-sm text-gray-500">Avg Time</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Reporting Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Report Defaults</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Default Export Format</label>
                      <select className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="pdf">PDF</option>
                        <option value="excel">Excel</option>
                        <option value="csv">CSV</option>
                        <option value="json">JSON</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Default Retention Days</label>
                      <input
                        type="number"
                        defaultValue="90"
                        className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-4">System Administration</h3>
                  <div className="space-y-3">
                    <Button variant="outline" className="w-full">
                      <Play className="h-4 w-4 mr-2" />
                      Execute Scheduled Reports
                    </Button>
                    <Button variant="outline" className="w-full">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Cleanup Expired Reports
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Report Generation Modal */}
      {showReportForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Generate New Report</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleGenerateReport} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Report Type</label>
                    <select
                      value={reportForm.report_type}
                      onChange={(e) => setReportForm({...reportForm, report_type: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="custom">Custom</option>
                      <option value="assessment_summary">Assessment Summary</option>
                      <option value="team_performance">Team Performance</option>
                      <option value="user_progress">User Progress</option>
                      <option value="organization_analytics">Organization Analytics</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Export Format</label>
                    <select
                      value={reportForm.export_format}
                      onChange={(e) => setReportForm({...reportForm, export_format: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pdf">PDF</option>
                      <option value="excel">Excel</option>
                      <option value="csv">CSV</option>
                      <option value="json">JSON</option>
                      <option value="powerpoint">PowerPoint</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Title</label>
                  <input
                    type="text"
                    value={reportForm.title}
                    onChange={(e) => setReportForm({...reportForm, title: e.target.value})}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={reportForm.description}
                    onChange={(e) => setReportForm({...reportForm, description: e.target.value})}
                    rows={4}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Data Range Start</label>
                    <input
                      type="date"
                      value={reportForm.data_range_start}
                      onChange={(e) => setReportForm({...reportForm, data_range_start: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Data Range End</label>
                    <input
                      type="date"
                      value={reportForm.data_range_end}
                      onChange={(e) => setReportForm({...reportForm, data_range_end: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Retention Days</label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={reportForm.retention_days}
                      onChange={(e) => setReportForm({...reportForm, retention_days: parseInt(e.target.value)})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="is_public"
                      checked={reportForm.is_public}
                      onChange={(e) => setReportForm({...reportForm, is_public: e.target.checked})}
                      className="rounded"
                    />
                    <label htmlFor="is_public" className="text-sm font-medium">
                      Make Public
                    </label>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowReportForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Generate Report</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Template Creation Modal */}
      {showTemplateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Create Report Template</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateTemplate} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Template Name</label>
                    <input
                      type="text"
                      value={templateForm.name}
                      onChange={(e) => setTemplateForm({...templateForm, name: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Report Type</label>
                    <select
                      value={templateForm.report_type}
                      onChange={(e) => setTemplateForm({...templateForm, report_type: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="custom">Custom</option>
                      <option value="assessment_summary">Assessment Summary</option>
                      <option value="team_performance">Team Performance</option>
                      <option value="user_progress">User Progress</option>
                      <option value="organization_analytics">Organization Analytics</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={templateForm.description}
                    onChange={(e) => setTemplateForm({...templateForm, description: e.target.value})}
                    rows={4}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Category</label>
                    <input
                      type="text"
                      value={templateForm.category}
                      onChange={(e) => setTemplateForm({...templateForm, category: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Analytics, Compliance, HR"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Tags (comma-separated)</label>
                    <input
                      type="text"
                      value={templateForm.tags}
                      onChange={(e) => setTemplateForm({...templateForm, tags: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., monthly, team, performance"
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="template_is_public"
                    checked={templateForm.is_public}
                    onChange={(e) => setTemplateForm({...templateForm, is_public: e.target.checked})}
                    className="rounded"
                  />
                  <label htmlFor="template_is_public" className="text-sm font-medium">
                    Make Template Public
                  </label>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowTemplateForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Create Template</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Schedule Creation Modal */}
      {showScheduleForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Create Report Schedule</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateSchedule} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Schedule Name</label>
                    <input
                      type="text"
                      value={scheduleForm.name}
                      onChange={(e) => setScheduleForm({...scheduleForm, name: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Frequency</label>
                    <select
                      value={scheduleForm.frequency}
                      onChange={(e) => setScheduleForm({...scheduleForm, frequency: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="quarterly">Quarterly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Description</label>
                  <textarea
                    value={scheduleForm.description}
                    onChange={(e) => setScheduleForm({...scheduleForm, description: e.target.value})}
                    rows={4}
                    className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Template</label>
                    <select
                      value={scheduleForm.template_id}
                      onChange={(e) => setScheduleForm({...scheduleForm, template_id: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select template</option>
                      {templates.map(template => (
                        <option key={template.id} value={template.id}>
                          {template.name} ({template.report_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Delivery Method</label>
                    <select
                      value={scheduleForm.delivery_method}
                      onChange={(e) => setScheduleForm({...scheduleForm, delivery_method: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="download">Download</option>
                      <option value="email">Email</option>
                      <option value="webhook">Webhook</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">End Date (Optional)</label>
                    <input
                      type="date"
                      value={scheduleForm.end_date}
                      onChange={(e) => setScheduleForm({...scheduleForm, end_date: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Default Format</label>
                    <select
                      value={scheduleForm.default_format}
                      onChange={(e) => setScheduleForm({...scheduleForm, default_format: e.target.value})}
                      className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="pdf">PDF</option>
                      <option value="excel">Excel</option>
                      <option value="csv">CSV</option>
                      <option value="json">JSON</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowScheduleForm(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">Create Schedule</Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Reporting;
