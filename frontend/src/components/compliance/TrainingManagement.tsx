import React, { useState, useEffect } from 'react';
import { FileText, Users, Clock, CheckCircle, AlertTriangle, Plus, Mail, Download, Search } from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
import { TrainingAssignment } from '../../types/compliance';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
interface TrainingManagementProps {
  className?: string;
}
export const TrainingManagement: React.FC<TrainingManagementProps> = ({ className = '' }) => {
  const [assignments, setAssignments] = useState<TrainingAssignment[]>([]);
  const [filteredAssignments, setFilteredAssignments] = useState<TrainingAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [filters, setFilters] = useState({
    status: 'all',
    training_type: 'all',
    search: ''
  });
  const { showNotification } = useNotification();
  useEffect(() => {
    loadAssignments();
  }, []);
  useEffect(() => {
    filterAssignments();
  }, [assignments, filters]);
  const loadAssignments = async () => {
    try {
      setLoading(true);
      const data = await complianceService.getTrainingAssignments();
      setAssignments(data);
    } catch (error) {
      console.error('Failed to load training assignments:', error);
      showNotification('Failed to load training assignments', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterAssignments = () => {
    let filtered = [...assignments];
    if (filters.status !== 'all') {
      filtered = filtered.filter(a => a.status === filters.status);
    }
    if (filters.training_type !== 'all') {
      filtered = filtered.filter(a => a.training_type === filters.training_type);
    }
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(a =>
        a.user_name.toLowerCase().includes(search) ||
        a.user_email.toLowerCase().includes(search) ||
        a.training_name.toLowerCase().includes(search)
      );
    }
    setFilteredAssignments(filtered);
  };
  const sendReminder = async (assignmentId: string) => {
    try {
      await complianceService.sendTrainingReminder(assignmentId);
      showNotification('Reminder sent successfully', 'success');
    } catch (error) {
      showNotification('Failed to send reminder', 'error');
    }
  };
  const exportReport = async () => {
    try {
      const response = await fetch('/api/v1/reports/training', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `training-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      showNotification('Failed to export report', 'error');
    }
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  const stats = {
    total: assignments.length,
    completed: assignments.filter(a => a.status === 'completed').length,
    inProgress: assignments.filter(a => a.status === 'in_progress').length,
    overdue: assignments.filter(a => a.status === 'overdue').length
  };
  const completionRate = ((stats.completed / stats.total) * 100).toFixed(1);
  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Training Management</h1>
          <p className="text-gray-600 mt-1">Assign and track mandatory compliance training</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={exportReport}
            icon={<Download className="w-4 h-4" />}
          >
            Export Report
          </Button>
          <Button
            onClick={() => setShowAssignModal(true)}
            icon={<Plus className="w-4 h-4" />}
          >
            Assign Training
          </Button>
        </div>
      </div>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          value={stats.total}
          icon={<FileText className="w-6 h-6" />}
          color="blue"
        />
        <StatsCard
          value={stats.completed}
          icon={<CheckCircle className="w-6 h-6" />}
          color="green"
          subtitle={`${completionRate}% completion rate`}
        />
        <StatsCard
          value={stats.inProgress}
          icon={<Clock className="w-6 h-6" />}
          color="yellow"
        />
        <StatsCard
          value={stats.overdue}
          icon={<AlertTriangle className="w-6 h-6" />}
          color="red"
          subtitle={stats.overdue > 0 ? 'Requires attention' : 'All up to date'}
        />
      </div>
      {/* Filters */}
      <Card>
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search by name, email, or training..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="overdue">Overdue</option>
            </select>
            <select
              value={filters.training_type}
              onChange={(e) => setFilters({ ...filters, training_type: e.target.value })}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Training Types</option>
              <option value="harassment_prevention">Harassment Prevention</option>
              <option value="data_privacy">Data Privacy</option>
              <option value="workplace_safety">Workplace Safety</option>
              <option value="code_of_conduct">Code of Conduct</option>
              <option value="security_awareness">Security Awareness</option>
            </select>
          </div>
        </div>
      </Card>
      {/* Assignments Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Training
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Due Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAssignments.map((assignment) => (
                <tr key={assignment.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                        <span className="text-indigo-600 font-semibold">
                          {assignment.user_name?.charAt(0) || '?'}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {assignment.user_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {assignment.user_email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{assignment.training_name}</div>
                    <div className="text-sm text-gray-500">{assignment.training_type.replace('_', ' ')}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {new Date(assignment.due_date).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-gray-500">
                      {getDaysRemaining(assignment.due_date)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={assignment.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {assignment.status === 'completed' ? (
                      <div className="flex items-center text-sm">
                        <span className="text-green-600 font-medium">
                          {assignment.completion_score || 0}%
                        </span>
                        {assignment.certificate_id && (
                          <CheckCircle className="w-4 h-4 text-green-500 ml-2" />
                        )}
                      </div>
                    ) : (
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: assignment.status === 'in_progress' ? '50%' : '0%' }}
                        />
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    {assignment.status !== 'completed' && (
                      <Button
                        variant="outline"
                        size="small"
                        onClick={() => sendReminder(assignment.id)}
                        icon={<Mail className="w-3 h-3" />}
                      >
                        Remind
                      </Button>
                    )}
                    {assignment.certificate_id && (
                      <Button
                        variant="outline"
                        size="small"
                        onClick={() => viewCertificate(assignment.certificate_id!)}
                      >
                        Certificate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredAssignments.length === 0 && (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No training assignments found</p>
            <Button
              className="mt-4"
              onClick={() => setShowAssignModal(true)}
              icon={<Plus className="w-4 h-4" />}
            >
              Assign Training
            </Button>
          </div>
        )}
      </Card>
      {/* Assign Training Modal */}
      {showAssignModal && (
        <AssignTrainingModal
          onClose={() => setShowAssignModal(false)}
          onSuccess={() => {
            setShowAssignModal(false);
            loadAssignments();
          }}
        />
      )}
    </div>
  );
};
// Helper Components
interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red';
  subtitle?: string;
}
const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color, subtitle }) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-500 text-blue-600',
      green: 'bg-green-500 text-green-600',
      yellow: 'bg-yellow-500 text-yellow-600',
      red: 'bg-red-500 text-red-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <Card>
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-opacity-10 ${getColorClasses(color)}`}>
          {icon}
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </Card>
  );
};
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusConfig = {
    assigned: { color: 'blue', label: 'Assigned' },
    in_progress: { color: 'yellow', label: 'In Progress' },
    completed: { color: 'green', label: 'Completed' },
    overdue: { color: 'red', label: 'Overdue' }
  };
  const config = statusConfig[status as keyof typeof statusConfig] || {
    color: 'gray',
    label: status
  };
  return <Badge color={config.color}>{config.label}</Badge>;
};
const getDaysRemaining = (dueDate: string): string => {
  const due = new Date(dueDate);
  const now = new Date();
  const diffTime = due.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  if (diffDays < 0) {
    return `${Math.abs(diffDays)} days overdue`;
  } else if (diffDays === 0) {
    return 'Due today';
  } else if (diffDays <= 7) {
    return `${diffDays} days left`;
  } else {
    return `${Math.ceil(diffDays / 7)} weeks left`;
  }
};
const viewCertificate = (certificateId: string) => {
  window.open(`/api/v1/compliance/training/certificate/${certificateId}`, '_blank');
};
// Assign Training Modal Component
interface AssignTrainingModalProps {
  onClose: () => void;
  onSuccess: () => void;
}
const AssignTrainingModal: React.FC<AssignTrainingModalProps> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    user_id: '',
    training_type: 'harassment_prevention',
    due_date: '',
    required_by: 'company_policy'
  });
  const [loading, setLoading] = useState(false);
  const { showNotification } = useNotification();
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await complianceService.assignTraining(formData);
      showNotification('Training assigned successfully', 'success');
      onSuccess();
    } catch (error) {
      showNotification('Failed to assign training', 'error');
    } finally {
      setLoading(false);
    }
  };
  // Calculate default due date (30 days from now)
  const defaultDueDate = new Date();
  defaultDueDate.setDate(defaultDueDate.getDate() + 30);
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <h2 className="text-xl font-semibold mb-4">Assign Training</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Employee Email
            </label>
            <input
              type="email"
              required
              value={formData.user_id}
              onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="employee@company.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Training Type
            </label>
            <select
              value={formData.training_type}
              onChange={(e) => setFormData({ ...formData, training_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="harassment_prevention">Harassment Prevention</option>
              <option value="data_privacy">Data Privacy & GDPR</option>
              <option value="workplace_safety">Workplace Safety</option>
              <option value="code_of_conduct">Code of Conduct</option>
              <option value="security_awareness">Security Awareness</option>
              <option value="diversity_inclusion">Diversity & Inclusion</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Due Date
            </label>
            <input
              type="date"
              required
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              min={new Date().toISOString().split('T')[0]}
              defaultValue={defaultDueDate.toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Required By
            </label>
            <select
              value={formData.required_by}
              onChange={(e) => setFormData({ ...formData, required_by: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="company_policy">Company Policy</option>
              <option value="regulation">Government Regulation</option>
              <option value="industry_standard">Industry Standard</option>
              <option value="client_requirement">Client Requirement</option>
            </select>
          </div>
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              loading={loading}
              className="flex-1"
            >
              Assign Training
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};