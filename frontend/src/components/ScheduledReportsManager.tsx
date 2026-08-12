/**
 * Scheduled Reports Management Component
 * Configure and manage automated weekly/monthly email reports
 */

import React, { useState, useEffect } from 'react';
import {
  CalendarDaysIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  PlayIcon,
  PauseIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

interface ScheduledReport {
  id: string;
  name: string;
  frequency: 'weekly' | 'monthly';
  recipients: string[];
  next_run: string;
  last_run: string | null;
  status: 'active' | 'paused';
  include_charts: boolean;
  format: 'pdf' | 'html';
}

const ScheduledReportsManager: React.FC = () => {
  console.log('🎉🎉🎉 SCHEDULED REPORTS MANAGER MOUNTED! 🎉🎉🎉');
  console.log('Current URL:', window.location.pathname);
  console.log('Timestamp:', new Date().toISOString());

  const [reports, setReports] = useState<ScheduledReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newReport, setNewReport] = useState({
    name: '',
    frequency: 'weekly' as 'weekly' | 'monthly',
    recipients: '',
    format: 'pdf' as 'pdf' | 'html',
  });

  useEffect(() => {
    fetchScheduledReports();
  }, []);

  const fetchScheduledReports = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/v1/scheduled-reports', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch');
      const data = await response.json();
      setReports(data.reports ?? []);
    } catch (error) {
      console.error('Failed to fetch scheduled reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReport = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('/api/v1/scheduled-reports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...newReport,
          recipients: newReport.recipients.split(',').map(r => r.trim()),
        }),
      });
      if (!response.ok) throw new Error('Failed to create');
      const created: ScheduledReport = await response.json();
      setReports([...reports, created]);
      setShowCreateModal(false);
      setNewReport({ name: '', frequency: 'weekly', recipients: '', format: 'pdf' });
    } catch (error) {
      console.error('Failed to create report:', error);
    }
  };

  const handleToggleStatus = async (reportId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/scheduled-reports/${reportId}/toggle`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to toggle');
      const data = await response.json();
      setReports(reports.map(r => r.id === reportId ? { ...r, status: data.status } : r));
    } catch (error) {
      console.error('Failed to toggle report:', error);
    }
  };

  const handleDeleteReport = async (reportId: string) => {
    if (!confirm('Are you sure you want to delete this scheduled report?')) return;
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/scheduled-reports/${reportId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to delete');
      setReports(reports.filter(r => r.id !== reportId));
    } catch (error) {
      console.error('Failed to delete report:', error);
    }
  };

  const handleSendNow = async (reportId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/scheduled-reports/${reportId}/send-now`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to send');
      const data = await response.json();
      alert(data.message ?? 'Report queued for delivery!');
      // Refresh to show updated last_run
      fetchScheduledReports();
    } catch (error) {
      alert('Failed to send report');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">📅 Scheduled Reports</h2>
        <p className="text-gray-600">
          Automate weekly and monthly email reports delivered to your inbox
        </p>
      </div>

      {/* Create Report Button */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          New Scheduled Report
        </button>
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        {reports.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No scheduled reports</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating a new scheduled report
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Create Report
              </button>
            </div>
          </div>
        ) : (
          reports.map((report) => (
            <div
              key={report.id}
              className="bg-white rounded-lg shadow border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div
                    className={`p-3 rounded-lg ${
                      report.status === 'active' ? 'bg-green-100' : 'bg-gray-100'
                    }`}
                  >
                    <CalendarDaysIcon
                      className={`w-6 h-6 ${
                        report.status === 'active' ? 'text-green-600' : 'text-gray-400'
                      }`}
                    />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-gray-900">{report.name}</h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          report.status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {report.status === 'active' ? 'Active' : 'Paused'}
                      </span>
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        {report.frequency}
                      </span>
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Recipients:</span>
                        <span className="ml-2 text-gray-900">
                          {report.recipients.join(', ')}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Format:</span>
                        <span className="ml-2 text-gray-900 uppercase">{report.format}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Next Run:</span>
                        <span className="ml-2 text-gray-900">
                          {new Date(report.next_run).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Last Run:</span>
                        <span className="ml-2 text-gray-900">
                          {report.last_run
                            ? new Date(report.last_run).toLocaleString()
                            : 'Never'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => handleSendNow(report.id)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
                    title="Send Now"
                  >
                    <EnvelopeIcon className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => handleToggleStatus(report.id)}
                    className={`p-2 rounded-md ${
                      report.status === 'active'
                        ? 'text-yellow-600 hover:bg-yellow-50'
                        : 'text-green-600 hover:bg-green-50'
                    }`}
                    title={report.status === 'active' ? 'Pause' : 'Resume'}
                  >
                    {report.status === 'active' ? (
                      <PauseIcon className="w-5 h-5" />
                    ) : (
                      <PlayIcon className="w-5 h-5" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDeleteReport(report.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                    title="Delete"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Report Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Create Scheduled Report</h3>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Report Name
                </label>
                <input
                  type="text"
                  value={newReport.name}
                  onChange={(e) => setNewReport({ ...newReport, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="My Weekly Report"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Frequency
                </label>
                <select
                  value={newReport.frequency}
                  onChange={(e) =>
                    setNewReport({
                      ...newReport,
                      frequency: e.target.value as 'weekly' | 'monthly',
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Recipients (comma-separated)
                </label>
                <input
                  type="text"
                  value={newReport.recipients}
                  onChange={(e) =>
                    setNewReport({ ...newReport, recipients: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="email1@example.com, email2@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Format
                </label>
                <select
                  value={newReport.format}
                  onChange={(e) =>
                    setNewReport({
                      ...newReport,
                      format: e.target.value as 'pdf' | 'html',
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="pdf">PDF</option>
                  <option value="html">HTML</option>
                </select>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 hover:text-gray-900"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateReport}
                disabled={!newReport.name || !newReport.recipients}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex">
          <DocumentTextIcon className="h-5 w-5 text-blue-400 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              About Scheduled Reports
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <p className="mb-1">• <strong>Weekly reports</strong> are sent every Monday at 9 AM</p>
              <p className="mb-1">• <strong>Monthly reports</strong> are sent on the 1st of each month</p>
              <p>• Reports include email statistics, category breakdowns, and behavioral insights</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScheduledReportsManager;
