/**
 * Report Forms Hook
 *
 * Manages form state and submission for reports, templates, and schedules
 */

import { useState } from 'react';
import { toast } from 'react-hot-toast';
import { ReportFormState, TemplateFormState, ScheduleFormState } from '../types';

const INITIAL_REPORT_FORM: ReportFormState = {
  title: '',
  description: '',
  report_type: 'custom',
  template_id: '',
  export_format: 'pdf',
  data_range_start: '',
  data_range_end: '',
  team_id: '',
  is_public: false,
  retention_days: 90,
};

const INITIAL_TEMPLATE_FORM: TemplateFormState = {
  name: '',
  description: '',
  report_type: 'custom',
  category: '',
  tags: '',
  is_public: false,
};

const INITIAL_SCHEDULE_FORM: ScheduleFormState = {
  name: '',
  description: '',
  template_id: '',
  frequency: 'weekly',
  delivery_method: 'download',
  delivery_config: '',
  end_date: '',
  default_format: 'pdf',
};

export const useReportForms = (onSuccess?: () => void) => {
  const [reportForm, setReportForm] = useState<ReportFormState>(INITIAL_REPORT_FORM);
  const [templateForm, setTemplateForm] = useState<TemplateFormState>(INITIAL_TEMPLATE_FORM);
  const [scheduleForm, setScheduleForm] = useState<ScheduleFormState>(INITIAL_SCHEDULE_FORM);

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
          team_id: reportForm.team_id || undefined,
        }),
      });

      if (response.ok) {
        toast.success('Report generation started successfully');
        setReportForm(INITIAL_REPORT_FORM);
        onSuccess?.();
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
          tags: templateForm.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
        }),
      });

      if (response.ok) {
        toast.success('Template created successfully');
        setTemplateForm(INITIAL_TEMPLATE_FORM);
        onSuccess?.();
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
          delivery_config:
            scheduleForm.delivery_method === 'email'
              ? { recipients: [] }
              : scheduleForm.delivery_method === 'webhook'
              ? { url: '' }
              : {},
        }),
      });

      if (response.ok) {
        toast.success('Schedule created successfully');
        setScheduleForm(INITIAL_SCHEDULE_FORM);
        onSuccess?.();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create schedule');
      }
    } catch (error) {
      toast.error('Error creating schedule');
    }
  };

  return {
    reportForm,
    setReportForm,
    templateForm,
    setTemplateForm,
    scheduleForm,
    setScheduleForm,
    handleGenerateReport,
    handleCreateTemplate,
    handleCreateSchedule,
  };
};
