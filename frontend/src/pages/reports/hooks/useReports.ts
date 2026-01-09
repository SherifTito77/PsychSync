/**
 * Reports Data Hook
 *
 * Manages reports, templates, schedules, and analytics data
 */

import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Report, ReportTemplate, ReportSchedule, ReportAnalytics } from '../types';

export const useReports = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [schedules, setSchedules] = useState<ReportSchedule[]>([]);
  const [analytics, setAnalytics] = useState<ReportAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  const loadReportingData = async () => {
    setLoading(true);
    try {
      const [reportsResponse, templatesResponse, schedulesResponse, analyticsResponse] =
        await Promise.all([
          fetch('/api/v1/reports/list?limit=100'),
          fetch('/api/v1/reports/templates'),
          fetch('/api/v1/reports/schedules'),
          fetch('/api/v1/reports/analytics?days=30'),
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

  const downloadReport = async (reportId: string) => {
    try {
      const response = await fetch(`/api/v1/reports/${reportId}/download`);
      if (response.ok) {
        const data = await response.json();
        toast.success('Report download started');
        window.open(data.download_url, '_blank');
      } else {
        toast.error('Failed to download report');
      }
    } catch (error) {
      toast.error('Error downloading report');
    }
  };

  useEffect(() => {
    loadReportingData();
  }, []);

  return {
    reports,
    templates,
    schedules,
    analytics,
    loading,
    loadReportingData,
    downloadReport,
    setReports,
    setTemplates,
    setSchedules,
  };
};
