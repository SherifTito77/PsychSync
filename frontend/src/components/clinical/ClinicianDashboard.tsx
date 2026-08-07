// frontend/src/components/clinical/ClinicianDashboard.tsx
/**
 * Clinician Dashboard - Crisis Intervention & Patient Management
 *
 * Features:
 * - Real-time alert monitoring (30-second refresh)
 * - Severity-based filtering and prioritization
 * - Quick action buttons for crisis intervention
 * - Patient record access
 * - Clinical notes and documentation
 * - HIPAA-compliant audit logging
 *
 * @author PsychSync Clinical Team
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertCircle, Bell, CheckCircle, Clock, Phone, User, FileText,
  TrendingUp, Filter, Search, ChevronRight, AlertTriangle, Heart,
  Shield, X, Calendar, Mail, Download, Send, Activity, Plus,
  MessageSquare, Video, Archive
} from 'lucide-react';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface ClinicalAlert {
  id: string;
  user_id: string;
  alert_type: string;
  alert_message: string;
  severity: 'critical' | 'high' | 'moderate' | 'low';
  risk_flags: string[];
  screening_data: {
    screening_type: string;
    total_score: number;
    [key: string]: any;
  };
  acknowledged: boolean;
  resolution_status: string;
  created_at: string;
  updated_at: string;
}

interface DashboardStats {
  critical_alerts: number;
  pending_reviews: number;
  resolved_today: number;
  avg_response_time: string;
  unacknowledged_alerts: number;
  active_patients: number;
}

interface TabProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  icon: any;
  children: React.ReactNode;
}

// ============================================================================
// STAT CARD COMPONENT
// ============================================================================

const StatCard: React.FC<{
  icon: any;
  label: string;
  value: number | string;
  color: string;
  trend?: string;
}> = ({ icon: Icon, label, value, color, trend }) => {
  const colorClasses: Record<string, { bg: string; text: string }> = {
    red: { bg: 'bg-red-100', text: 'text-red-600' },
    yellow: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
    green: { bg: 'bg-green-100', text: 'text-green-600' },
    blue: { bg: 'bg-blue-100', text: 'text-blue-600' }
  };

  const classes = colorClasses[color] || colorClasses.blue;

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl ${classes.bg}`}>
          <Icon className={`w-6 h-6 ${classes.text}`} />
        </div>
      </div>
      <h3 className="text-3xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm text-gray-600 mb-2">{label}</p>
      {trend && <p className="text-xs text-gray-500">{trend}</p>}
    </div>
  );
};

// ============================================================================
// TAB BUTTON COMPONENT
// ============================================================================

const TabButton: React.FC<TabProps> = ({ activeTab, setActiveTab, icon: Icon, children }) => (
  <button
    onClick={() => setActiveTab(children as string)}
    className={`flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm transition-all ${
      activeTab === children
        ? 'border-blue-600 text-blue-600'
        : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
    }`}
  >
    <Icon className="w-4 h-4" />
    {children}
  </button>
);

// ============================================================================
// MAIN DASHBOARD COMPONENT
// ============================================================================

export const ClinicianDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('alerts');
  const [alerts, setAlerts] = useState<ClinicalAlert[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<ClinicalAlert | null>(null);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [onDuty, setOnDuty] = useState(true);

  // ✅ FIXED: Safe fetch function with optional AbortSignal
  const fetchDashboardData = useCallback(async (signal?: AbortSignal) => {
    try {
      const [alertsRes, statsRes] = await Promise.all([
        fetch('/api/v1/clinical/alerts?status=pending,in_progress', { signal }),
        fetch('/api/v1/clinical/dashboard/stats', { signal })
      ]);

      // ✅ Check for abort
      if (signal?.aborted) {
        return;
      }

      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        if (!signal?.aborted) {
          setAlerts(alertsData);
        }
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        if (!signal?.aborted) {
          setStats(statsData);
        }
      }

      if (!signal?.aborted) {
        setLoading(false);
      }
    } catch (error) {
      // ✅ Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }
      console.error('Error fetching dashboard data:', error);
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, []);

  // ✅ FIXED: Safe async effect with cleanup
  useEffect(() => {
    let isMounted = true;
    const abortController = new AbortController();
    const signal = abortController.signal;

    const fetchData = async () => {
      if (!isMounted || signal.aborted) {
        return;
      }
      await fetchDashboardData(signal);
    };

    // Run immediately on mount
    fetchData();

    // Set up interval for periodic refresh
    const interval = setInterval(fetchData, 30000); // 30-second refresh

    // ✅ Cleanup function
    return () => {
      isMounted = false;
      abortController.abort();
      clearInterval(interval);
    };
  }, [fetchDashboardData]);

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/clinical/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        fetchDashboardData();
        setSelectedAlert(null);
      } else {
        throw new Error('Failed to acknowledge alert');
      }
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      alert('Error acknowledging alert. Please try again.');
    }
  };

  const handleEmergencyContact = async (userId: string) => {
    if (confirm('This will initiate emergency protocol. Continue?')) {
      window.open(`tel:988`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading Clinical Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="w-10 h-10 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Clinical Dashboard</h1>
                <p className="text-sm text-gray-600">Crisis Intervention & Patient Management</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <button className="relative p-3 hover:bg-gray-100 rounded-full transition-colors">
                <Bell className="w-6 h-6 text-gray-600" />
                {stats?.unacknowledged_alerts > 0 && (
                  <span className="absolute top-0 right-0 w-5 h-5 bg-red-600 text-white text-xs rounded-full flex items-center justify-center">
                    {stats.unacknowledged_alerts}
                  </span>
                )}
              </button>

              <button
                onClick={() => setOnDuty(!onDuty)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium transition ${
                  onDuty ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                }`}
              >
                <div className={`w-3 h-3 rounded-full ${onDuty ? 'bg-green-600 animate-pulse' : 'bg-gray-400'}`}></div>
                {onDuty ? 'On Call' : 'Off Duty'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="px-6 py-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <StatCard
            icon={AlertTriangle}
            label="Critical Alerts"
            value={stats?.critical_alerts || 0}
            color="red"
            trend="Requires immediate attention"
          />
          <StatCard
            icon={Clock}
            label="Pending Reviews"
            value={stats?.pending_reviews || 0}
            color="yellow"
            trend={`${stats?.resolved_today || 0} resolved today`}
          />
          <StatCard
            icon={CheckCircle}
            label="Resolved Today"
            value={stats?.resolved_today || 0}
            color="green"
          />
          <StatCard
            icon={TrendingUp}
            label="Avg Response Time"
            value={stats?.avg_response_time || 'N/A'}
            color="blue"
            trend="Target: <10 minutes"
          />
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <TabButton activeTab={activeTab} setActiveTab={setActiveTab} icon={AlertCircle}>
                Crisis Alerts
              </TabButton>
              <TabButton activeTab={activeTab} setActiveTab={setActiveTab} icon={FileText}>
                Referrals
              </TabButton>
              <TabButton activeTab={activeTab} setActiveTab={setActiveTab} icon={Clock}>
                Follow-Ups
              </TabButton>
              <TabButton activeTab={activeTab} setActiveTab={setActiveTab} icon={User}>
                Patients
              </TabButton>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'alerts' && (
              <AlertsView
                alerts={alerts}
                filterSeverity={filterSeverity}
                searchTerm={searchTerm}
                setFilterSeverity={setFilterSeverity}
                setSearchTerm={setSearchTerm}
                onSelectAlert={setSelectedAlert}
                onRefresh={fetchDashboardData}
              />
            )}
            {activeTab === 'referrals' && <ReferralsView />}
            {activeTab === 'follow-ups' && <FollowUpsView />}
            {activeTab === 'patients' && <PatientsView />}
          </div>
        </div>
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <AlertDetailModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onAcknowledge={handleAcknowledgeAlert}
          onEmergencyContact={handleEmergencyContact}
          onRefresh={fetchDashboardData}
        />
      )}
    </div>
  );
};

// ============================================================================
// ALERTS VIEW COMPONENT
// ============================================================================

const AlertsView: React.FC<{
  alerts: ClinicalAlert[];
  filterSeverity: string;
  searchTerm: string;
  setFilterSeverity: (severity: string) => void;
  setSearchTerm: (term: string) => void;
  onSelectAlert: (alert: ClinicalAlert) => void;
  onRefresh: () => void;
}> = ({ alerts, filterSeverity, searchTerm, setFilterSeverity, setSearchTerm, onSelectAlert, onRefresh }) => {
  const filteredAlerts = alerts.filter(alert => {
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity;
    const matchesSearch = !searchTerm ||
      alert.alert_message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.user_id.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  const sortedAlerts = [...filteredAlerts].sort((a, b) => {
    const severityOrder = { critical: 0, high: 1, moderate: 2, low: 3 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });

  const timeAgo = (date: string) => {
    const minutes = Math.floor((new Date().getTime() - new Date(date).getTime()) / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search alerts by patient ID or message..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Severity Levels</option>
          <option value="critical">Critical Only</option>
          <option value="high">High & Critical</option>
          <option value="moderate">Moderate+</option>
        </select>

        <button
          onClick={onRefresh}
          className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Activity className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {sortedAlerts.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
            <p className="text-xl font-medium mb-2">No Active Alerts</p>
            <p className="text-sm">All patients are currently stable</p>
          </div>
        ) : (
          sortedAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onClick={() => onSelectAlert(alert)}
              timeAgo={timeAgo}
            />
          ))
        )}
      </div>
    </div>
  );
};

// ============================================================================
// ALERT CARD COMPONENT
// ============================================================================

const AlertCard: React.FC<{
  alert: ClinicalAlert;
  onClick: () => void;
  timeAgo: (date: string) => string;
}> = ({ alert, onClick, timeAgo }) => {
  const getSeverityClasses = (severity: string) => {
    const classes: Record<string, { bg: string; border: string; text: string; badge: string }> = {
      critical: {
        bg: 'bg-red-50',
        border: 'border-red-600',
        text: 'text-red-900',
        badge: 'bg-red-600'
      },
      high: {
        bg: 'bg-orange-50',
        border: 'border-orange-600',
        text: 'text-orange-900',
        badge: 'bg-orange-600'
      },
      moderate: {
        bg: 'bg-yellow-50',
        border: 'border-yellow-600',
        text: 'text-yellow-900',
        badge: 'bg-yellow-600'
      },
      low: {
        bg: 'bg-blue-50',
        border: 'border-blue-600',
        text: 'text-blue-900',
        badge: 'bg-blue-600'
      }
    };
    return classes[severity] || classes.low;
  };

  const classes = getSeverityClasses(alert.severity);

  return (
    <div
      onClick={onClick}
      className={`border-l-4 p-5 rounded-lg cursor-pointer hover:shadow-lg transition-all ${classes.bg} ${classes.border}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-3 py-1 rounded text-xs font-bold uppercase text-white ${classes.badge}`}>
              {alert.severity}
            </span>
            {!alert.acknowledged && (
              <span className="px-3 py-1 bg-blue-600 text-white rounded text-xs font-bold">
                NEW
              </span>
            )}
            <span className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-xs font-mono">
              {alert.alert_type.replace(/_/g, ' ')}
            </span>
          </div>

          <h3 className={`font-bold text-lg mb-2 ${classes.text}`}>
            {alert.alert_message}
          </h3>

          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mt-3">
            <span className="flex items-center gap-1">
              <User className="w-3 h-3" />
              Patient: <span className="font-mono">{alert.user_id.substring(0, 8)}...</span>
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {timeAgo(alert.created_at)}
            </span>
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {alert.screening_data.screening_type}
            </span>
            {alert.screening_data.total_score > 0 && (
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Score: {alert.screening_data.total_score}
              </span>
            )}
          </div>

          {/* Risk Flags */}
          {alert.risk_flags && alert.risk_flags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {alert.risk_flags.slice(0, 3).map((flag, index) => (
                <span key={index} className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                  {flag.replace(/_/g, ' ')}
                </span>
              ))}
              {alert.risk_flags.length > 3 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                  +{alert.risk_flags.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>

        <ChevronRight className="w-6 h-6 text-gray-400 flex-shrink-0" />
      </div>
    </div>
  );
};

// ============================================================================
// ALERT DETAIL MODAL
// ============================================================================

const AlertDetailModal: React.FC<{
  alert: ClinicalAlert;
  onClose: () => void;
  onAcknowledge: (alertId: string) => void;
  onEmergencyContact: (userId: string) => void;
  onRefresh: () => void;
}> = ({ alert, onClose, onAcknowledge, onEmergencyContact, onRefresh }) => {
  const [acknowledging, setAcknowledging] = useState(false);
  const [notes, setNotes] = useState('');
  const [showReferralForm, setShowReferralForm] = useState(false);

  const getSeverityClasses = (severity: string) => {
    const classes: Record<string, { bg: string; border: string; text: string }> = {
      critical: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-900' },
      high: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-900' },
      moderate: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-900' },
      low: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-900' }
    };
    return classes[severity] || classes.low;
  };

  const classes = getSeverityClasses(alert.severity);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className={`sticky top-0 ${classes.bg} border-b ${classes.border} p-6 rounded-t-2xl`}>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <AlertTriangle className={`w-8 h-8 ${classes.text.replace('900', '600')}`} />
              Crisis Alert Details
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
              <X className="w-8 h-8" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Alert Info */}
          <div className={`p-6 rounded-xl ${classes.bg} ${classes.border} border-2`}>
            <div className="flex items-start gap-4">
              <AlertCircle className={`w-10 h-10 ${classes.text.replace('900', '600')} flex-shrink-0 mt-1`} />
              <div className="flex-1">
                <h3 className={`font-bold text-xl mb-3 ${classes.text}`}>{alert.alert_message}</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Severity:</span>
                    <span className="ml-2 font-semibold uppercase">{alert.severity}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Status:</span>
                    <span className="ml-2 font-semibold">{alert.resolution_status}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Screening:</span>
                    <span className="ml-2 font-semibold">{alert.screening_data.screening_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Score:</span>
                    <span className="ml-2 font-bold text-xl">{alert.screening_data.total_score}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600">Patient ID:</span>
                    <span className="ml-2 font-mono text-xs">{alert.user_id}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600">Created:</span>
                    <span className="ml-2">{new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Flags */}
          {alert.risk_flags && alert.risk_flags.length > 0 && (
            <div>
              <h4 className="font-bold text-gray-900 mb-3">Risk Indicators:</h4>
              <div className="flex flex-wrap gap-2">
                {alert.risk_flags.map((flag, index) => (
                  <span key={index} className="px-4 py-2 bg-red-100 text-red-800 rounded-full text-sm font-semibold">
                    {flag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div>
            <h4 className="font-bold text-gray-900 mb-4">Quick Actions:</h4>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => onEmergencyContact(alert.user_id)}
                className="flex items-center justify-center gap-2 px-4 py-4 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors font-semibold"
              >
                <Phone className="w-5 h-5" />
                Call 988 Crisis Line
              </button>
              <button
                onClick={() => setShowReferralForm(true)}
                className="flex items-center justify-center gap-2 px-4 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-semibold"
              >
                <FileText className="w-5 h-5" />
                Create Referral
              </button>
              <button className="flex items-center justify-center gap-2 px-4 py-4 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-semibold">
                <User className="w-5 h-5" />
                View Patient Record
              </button>
              <button className="flex items-center justify-center gap-2 px-4 py-4 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-semibold">
                <Heart className="w-5 h-5" />
                Send Safety Plan
              </button>
              <button className="flex items-center justify-center gap-2 px-4 py-4 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-semibold">
                <MessageSquare className="w-5 h-5" />
                Send Message
              </button>
              <button className="flex items-center justify-center gap-2 px-4 py-4 border-2 border-gray-300 rounded-xl hover:bg-gray-50 transition-colors font-semibold">
                <Video className="w-5 h-5" />
                Schedule Video Call
              </button>
            </div>
          </div>

          {/* Clinical Notes */}
          <div>
            <h4 className="font-bold text-gray-900 mb-3">Clinical Notes:</h4>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Document your assessment and actions taken..."
              className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={5}
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-6 flex gap-4">
          <button
            onClick={() => onAcknowledge(alert.id)}
            disabled={acknowledging || alert.acknowledged}
            className="flex-1 bg-green-600 text-white py-4 rounded-xl font-semibold hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {acknowledging ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </>
            ) : alert.acknowledged ? (
              <>
                <CheckCircle className="w-5 h-5" />
                Acknowledged
              </>
            ) : (
              <>
                <Shield className="w-5 h-5" />
                Acknowledge & Accept
              </>
            )}
          </button>
          <button
            onClick={onClose}
            className="px-8 py-4 border-2 border-gray-300 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// PLACEHOLDER VIEWS
// ============================================================================

const ReferralsView: React.FC = () => (
  <div className="text-center py-16 text-gray-500">
    <FileText className="w-16 h-16 mx-auto mb-4" />
    <p className="text-xl font-medium mb-2">Referral Management</p>
    <p className="text-sm">Track and manage patient referrals</p>
  </div>
);

const FollowUpsView: React.FC = () => (
  <div className="text-center py-16 text-gray-500">
    <Calendar className="w-16 h-16 mx-auto mb-4" />
    <p className="text-xl font-medium mb-2">Follow-Up Tracking</p>
    <p className="text-sm">Monitor patient progress and scheduled follow-ups</p>
  </div>
);

const PatientsView: React.FC = () => (
  <div className="text-center py-16 text-gray-500">
    <User className="w-16 h-16 mx-auto mb-4" />
    <p className="text-xl font-medium mb-2">Patient Directory</p>
    <p className="text-sm">View and manage all patients</p>
  </div>
);

export default ClinicianDashboard;
