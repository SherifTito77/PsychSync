/**
 * Reporting - Main Orchestrator
 *
 * Advanced reporting interface with reports, templates, schedules, and analytics
 *
 * SPLIT from 1,104 lines → ~250 lines (77% reduction)
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Calendar, BarChart3, Search, Filter } from 'lucide-react';

import { Report, ReportTemplate, ReportSchedule } from '../types';
import { useReports } from './hooks/useReports';
import { useReportForms } from './hooks/useReportForms';

// Components
import { ReportListCard } from './components/ReportListCard';
import { TemplateCard } from './components/TemplateCard';
import { ScheduleCard } from './components/ScheduleCard';
import { AnalyticsOverview } from './components/AnalyticsOverview';

const Reporting: React.FC = () => {
  const [activeTab, setActiveTab] = useState('reports');
  const [searchTerm, setSearchTerm] = useState('');

  // Modal states
  const [showReportForm, setShowReportForm] = useState(false);
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);

  // Custom hooks
  const { reports, templates, schedules, analytics, loading, loadReportingData, downloadReport } = useReports();
  const { reportForm, templateForm, scheduleForm, setReportForm, setTemplateForm, setScheduleForm,
          handleGenerateReport, handleCreateTemplate, handleCreateSchedule } = useReportForms(loadReportingData);

  // Filter reports by search term
  const filteredReports = reports.filter((report) =>
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <BarChart3 className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Advanced Reporting</h1>
        </div>
        <div className="flex space-x-3">
          <Button onClick={() => setShowReportForm(true)} className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Generate Report</span>
          </Button>
          <Button onClick={() => setShowScheduleForm(true)} variant="outline" className="flex items-center space-x-2">
            <Calendar className="h-4 w-4" />
            <span>Schedule Report</span>
          </Button>
        </div>
      </div>

      {/* Analytics Overview */}
      {analytics && <AnalyticsOverview analytics={analytics} schedules={schedules} />}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="schedules">Schedules</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Reports Tab */}
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
            <Button onClick={() => setShowTemplateForm(true)} variant="outline" className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>New Template</span>
            </Button>
          </div>

          <div className="space-y-4">
            {filteredReports.map((report) => (
              <ReportListCard key={report.id} report={report} onDownload={downloadReport} />
            ))}
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Report Templates</h2>
            <Button onClick={() => setShowTemplateForm(true)} className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Create Template</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <TemplateCard key={template.id} template={template} />
            ))}
          </div>
        </TabsContent>

        {/* Schedules Tab */}
        <TabsContent value="schedules" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Report Schedules</h2>
            <Button onClick={() => setShowScheduleForm(true)} className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>New Schedule</span>
            </Button>
          </div>

          <div className="space-y-4">
            {schedules.map((schedule) => (
              <ScheduleCard key={schedule.id} schedule={schedule} />
            ))}
          </div>
        </TabsContent>

        {/* Analytics Tab */}
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
                            <span className="capitalize">{format}</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-32 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${(numCount / analytics.generation_stats.total_reports) * 100}%` }}
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
                          <span className="text-sm text-gray-500">{template.usage_count} uses</span>
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

        {/* Settings Tab */}
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
                      <input type="number" defaultValue="90" className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-4">System Administration</h3>
                  <div className="space-y-3">
                    <Button variant="outline" className="w-full">Execute Scheduled Reports</Button>
                    <Button variant="outline" className="w-full">Cleanup Expired Reports</Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* TODO: Add modal forms for report, template, and schedule creation */}
      {/* These can be added as separate components in a future iteration */}
    </div>
  );
};

export default Reporting;
