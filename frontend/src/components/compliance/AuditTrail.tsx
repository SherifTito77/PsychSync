import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Download,
  Eye,
  Calendar,
  User,
  Shield,
  AlertTriangle,
  Clock,
  FileText,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  FileSearch,
  Lock,
  Database,
  Globe,
  Mail,
  Smartphone,
  Key,
  Zap,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Plus,
  Edit,
  Trash2,
  Save,
  X
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
interface AuditEvent {
  id: string;
  timestamp: string;
  eventType: 'login' | 'logout' | 'document_access' | 'data_export' | 'settings_change' | 'user_action' | 'system_event' | 'security_alert' | 'compliance_check';
  category: 'authentication' | 'data_access' | 'system_config' | 'user_management' | 'security' | 'compliance';
  severity: 'low' | 'medium' | 'high' | 'critical';
  userId: string;
  userName: string;
  userEmail: string;
  userRole: string;
  action: string;
  description: string;
  ipAddress: string;
  userAgent: string;
  sessionId: string;
  resource: string;
  resourceId: string;
  oldValue?: any;
  newValue?: any;
  status: 'success' | 'failure' | 'warning';
  source: 'web' | 'mobile' | 'api' | 'system' | 'integration';
  location?: {
    country: string;
    city: string;
    coordinates?: [number, number];
  };
  metadata: Record<string, any>;
  relatedEvents: string[];
  investigationStatus?: 'none' | 'pending' | 'investigating' | 'resolved';
  investigationNotes?: string;
  assignedTo?: string;
  tags: string[];
}
interface Investigation {
  id: string;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'closed' | 'escalated';
  priority: 'low' | 'medium' | 'high' | 'critical';
  severity: 'low' | 'medium' | 'high' | 'critical';
  assignedTo: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  dueDate?: string;
  tags: string[];
  events: string[];
  evidence: Array<{
    type: 'document' | 'screenshot' | 'log' | 'interview' | 'other';
    description: string;
    url?: string;
    uploadedAt: string;
    uploadedBy: string;
  }>;
  timeline: Array<{
    timestamp: string;
    action: string;
    performedBy: string;
    details: string;
  }>;
  findings: Array<{
    category: string;
    description: string;
    impact: 'low' | 'medium' | 'high' | 'critical';
    evidence: string[];
  }>;
  recommendations: Array<{
    action: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    assignedTo: string;
    dueDate?: string;
    status: 'pending' | 'in_progress' | 'completed';
  }>;
  resolution?: string;
  resolvedAt?: string;
  resolvedBy?: string;
}
interface AuditTrailProps {
  className?: string;
}
export const AuditTrail: React.FC<AuditTrailProps> = ({ className = '' }) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'events' | 'investigations' | 'analytics'>('events');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEventType, setSelectedEventType] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [showInvestigationModal, setShowInvestigationModal] = useState(false);
  const [showCreateInvestigationModal, setShowCreateInvestigationModal] = useState(false);
  const { showNotification } = useNotification();
  useEffect(() => {
    loadData();
  }, [activeTab, searchTerm, selectedEventType, selectedSeverity, selectedCategory, dateRange]);
  const loadData = async () => {
    try {
      setLoading(true);
      if (activeTab === 'events') {
        const data = await mockAuditEventData();
        const filteredData = filterEvents(data);
        setEvents(filteredData);
      } else if (activeTab === 'investigations') {
        const data = await mockInvestigationData();
        setInvestigations(data);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      showNotification('Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterEvents = (eventData: AuditEvent[]) => {
    return eventData.filter(event => {
      const matchesSearch = event.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           event.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           event.userName.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = selectedEventType === 'all' || event.eventType === selectedEventType;
      const matchesSeverity = selectedSeverity === 'all' || event.severity === selectedSeverity;
      const matchesCategory = selectedCategory === 'all' || event.category === selectedCategory;
      return matchesSearch && matchesType && matchesSeverity && matchesCategory;
    });
  };
  const handleCreateInvestigation = (event: AuditEvent) => {
    setSelectedEvent(event);
    setShowCreateInvestigationModal(true);
  };
  const handleAssignInvestigation = (eventId: string, assignedTo: string) => {
    setEvents(prev => prev.map(event =>
      event.id === eventId
        ? { ...event, investigationStatus: 'investigating', assignedTo }
        : event
    ));
    showNotification('Investigation assigned successfully', 'success');
  };
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failure': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <Info className="w-4 h-4 text-gray-500" />;
    }
  };
  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'web': return <Globe className="w-4 h-4 text-blue-500" />;
      case 'mobile': return <Smartphone className="w-4 h-4 text-purple-500" />;
      case 'api': return <Zap className="w-4 h-4 text-green-500" />;
      case 'system': return <Database className="w-4 h-4 text-gray-500" />;
      case 'integration': return <Lock className="w-4 h-4 text-orange-500" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  return (
    <div className={`max-w-7xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Trail & Investigations</h1>
          <p className="text-gray-600 mt-1">Monitor system activity and manage compliance investigations</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            icon={<Filter className="w-4 h-4" />}
          >
            Filters
          </Button>
          <Button
            icon={<Download className="w-4 h-4" />}
          >
            Export Report
          </Button>
        </div>
      </div>
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'events', label: 'Audit Events', count: events.length },
            { id: 'investigations', label: 'Investigations', count: investigations.filter(i => i.status !== 'closed').length },
            { id: 'analytics', label: 'Analytics', count: null }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count !== null && (
                <Badge
                  color={activeTab === tab.id ? 'blue' : 'gray'}
                  size="sm"
                  className="ml-2"
                >
                  {tab.count}
                </Badge>
              )}
            </button>
          ))}
        </nav>
      </div>
      {/* Search and Filters */}
      <Card className="mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search audit events, users, or actions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
            {activeTab === 'events' && (
              <>
                <select
                  value={selectedEventType}
                  onChange={(e) => setSelectedEventType(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Event Types</option>
                  <option value="login">Login/Logout</option>
                  <option value="document_access">Document Access</option>
                  <option value="data_export">Data Export</option>
                  <option value="settings_change">Settings Change</option>
                  <option value="user_action">User Action</option>
                  <option value="security_alert">Security Alert</option>
                  <option value="compliance_check">Compliance Check</option>
                </select>
                <select
                  value={selectedSeverity}
                  onChange={(e) => setSelectedSeverity(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </>
            )}
          </div>
        </div>
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Categories</option>
                  <option value="authentication">Authentication</option>
                  <option value="data_access">Data Access</option>
                  <option value="system_config">System Config</option>
                  <option value="user_management">User Management</option>
                  <option value="security">Security</option>
                  <option value="compliance">Compliance</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </Card>
      {/* Tab Content */}
      {activeTab === 'events' && (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              value={events.length}
              icon={<Activity className="w-5 h-5" />}
              color="blue"
              change={12.5}
              trend="up"
            />
            <StatCard
              value={events.filter(e => e.category === 'security').length}
              icon={<Shield className="w-5 h-5" />}
              color="red"
              change={-5.2}
              trend="down"
            />
            <StatCard
              value={events.filter(e => e.eventType === 'login' && e.status === 'failure').length}
              icon={<XCircle className="w-5 h-5" />}
              color="orange"
              change={8.1}
              trend="up"
            />
            <StatCard
              value={events.filter(e => e.eventType === 'data_export').length}
              icon={<Download className="w-5 h-5" />}
              color="green"
              change={15.3}
              trend="up"
            />
          </div>
          {/* Events Table */}
          <Card>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Event Details
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Investigation
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {events.map((event) => (
                    <EventRow
                      key={event.id}
                      event={event}
                      onSelect={() => {
                        setSelectedEvent(event);
                        setShowEventModal(true);
                      }}
                      onCreateInvestigation={() => handleCreateInvestigation(event)}
                      onAssignInvestigation={handleAssignInvestigation}
                      getSeverityColor={getSeverityColor}
                      getStatusIcon={getStatusIcon}
                      getSourceIcon={getSourceIcon}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
      {activeTab === 'investigations' && (
        <div className="space-y-6">
          {/* Investigation Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              value={investigations.filter(i => i.status === 'open').length}
              icon={<FileSearch className="w-5 h-5" />}
              color="blue"
            />
            <StatCard
              value={investigations.filter(i => i.status === 'in_progress').length}
              icon={<RefreshCw className="w-5 h-5" />}
              color="yellow"
            />
            <StatCard
              value={investigations.filter(i => i.severity === 'critical').length}
              icon={<AlertTriangle className="w-5 h-5" />}
              color="red"
            />
            <StatCard
              value={investigations.filter(i => i.status === 'closed').length}
              icon={<CheckCircle className="w-5 h-5" />}
              color="green"
            />
          </div>
          {/* Investigations Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {investigations.map((investigation) => (
              <InvestigationCard
                key={investigation.id}
                investigation={investigation}
                onSelect={() => {
                  setSelectedEvent(null);
                  setShowInvestigationModal(true);
                }}
                getSeverityColor={getSeverityColor}
              />
            ))}
          </div>
        </div>
      )}
      {activeTab === 'analytics' && (
        <AnalyticsDashboard events={events} investigations={investigations} />
      )}
      {/* Event Details Modal */}
      {showEventModal && selectedEvent && (
        <EventDetailsModal
          event={selectedEvent}
          onClose={() => setShowEventModal(false)}
          onCreateInvestigation={handleCreateInvestigation}
          getSeverityColor={getSeverityColor}
          getStatusIcon={getStatusIcon}
          getSourceIcon={getSourceIcon}
        />
      )}
      {/* Investigation Details Modal */}
      {showInvestigationModal && (
        <InvestigationDetailsModal
          onClose={() => setShowInvestigationModal(false)}
          getSeverityColor={getSeverityColor}
        />
      )}
      {/* Create Investigation Modal */}
      {showCreateInvestigationModal && selectedEvent && (
        <CreateInvestigationModal
          event={selectedEvent}
          onClose={() => setShowCreateInvestigationModal(false)}
          onCreated={() => {
            setShowCreateInvestigationModal(false);
            setActiveTab('investigations');
            loadData();
          }}
        />
      )}
    </div>
  );
};
// Event Row Component
interface EventRowProps {
  event: AuditEvent;
  onSelect: () => void;
  onCreateInvestigation: () => void;
  onAssignInvestigation: (eventId: string, assignedTo: string) => void;
  getSeverityColor: (severity: string) => string;
  getStatusIcon: (status: string) => React.ReactNode;
  getSourceIcon: (source: string) => React.ReactNode;
}
const EventRow: React.FC<EventRowProps> = ({
  event,
  onSelect,
  onCreateInvestigation,
  onAssignInvestigation,
  getSeverityColor,
  getStatusIcon,
  getSourceIcon
}) => {
  const [showActions, setShowActions] = useState(false);
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-10 w-10">
            <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
              event.severity === 'critical' ? 'bg-red-100' :
              event.severity === 'high' ? 'bg-orange-100' :
              event.severity === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
            }`}>
              {getStatusIcon(event.status)}
            </div>
          </div>
          <div className="ml-4">
            <div className="text-sm font-medium text-gray-900">{event.action}</div>
            <div className="text-sm text-gray-500">{event.description}</div>
            <div className="text-xs text-gray-400 mt-1">
              {new Date(event.timestamp).toLocaleString()}
            </div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-8 w-8">
            <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="h-4 w-4 text-gray-500" />
            </div>
          </div>
          <div className="ml-3">
            <div className="text-sm font-medium text-gray-900">{event.userName}</div>
            <div className="text-xs text-gray-500">{event.userRole}</div>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center space-x-2">
          <Badge color={getSeverityColor(event.severity)} size="sm">
            {event.severity}
          </Badge>
          {getStatusIcon(event.status)}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center space-x-2">
          {getSourceIcon(event.source)}
          <span className="text-sm text-gray-500">{event.source}</span>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        {event.investigationStatus === 'none' ? (
          <Badge color="gray" size="sm">None</Badge>
        ) : (
          <Badge color="yellow" size="sm">
            {event.investigationStatus} ({event.assignedTo})
          </Badge>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="relative">
          <Button
            variant="ghost"
            size="small"
            onClick={() => setShowActions(!showActions)}
            icon={<ChevronDown className="w-4 h-4" />}
          />
          {showActions && (
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
              <button
                onClick={() => { onSelect(); setShowActions(false); }}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
              >
                <Eye className="w-4 h-4" />
                <span>View Details</span>
              </button>
              {event.investigationStatus === 'none' && (
                <button
                  onClick={() => { onCreateInvestigation(); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                >
                  <FileSearch className="w-4 h-4" />
                  <span>Create Investigation</span>
                </button>
              )}
            </div>
          )}
        </div>
      </td>
    </tr>
  );
};
// Investigation Card Component
interface InvestigationCardProps {
  investigation: Investigation;
  onSelect: () => void;
  getSeverityColor: (severity: string) => string;
}
const InvestigationCard: React.FC<InvestigationCardProps> = ({
  investigation,
  onSelect,
  getSeverityColor
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'red';
      case 'in_progress': return 'yellow';
      case 'closed': return 'green';
      case 'escalated': return 'orange';
      default: return 'gray';
    }
  };
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={onSelect}>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">{investigation.title}</h3>
            <p className="text-sm text-gray-600 line-clamp-2">{investigation.description}</p>
          </div>
          <div className="flex flex-col items-end space-y-2">
            <Badge color={getStatusColor(investigation.status)} size="sm">
              {investigation.status.replace('_', ' ')}
            </Badge>
            <Badge color={getSeverityColor(investigation.severity)} size="sm" variant="outline">
              {investigation.severity}
            </Badge>
          </div>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Assigned to:</span>
            <span className="font-medium">{investigation.assignedTo}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Events:</span>
            <span className="font-medium">{investigation.events.length}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Created:</span>
            <span className="font-medium">{new Date(investigation.createdAt).toLocaleDateString()}</span>
          </div>
          {investigation.dueDate && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Due:</span>
              <span className={`font-medium ${
                new Date(investigation.dueDate) < new Date() ? 'text-red-600' : 'text-gray-900'
              }`}>
                {new Date(investigation.dueDate).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
        {investigation.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-4">
            {investigation.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Updated {new Date(investigation.updatedAt).toLocaleDateString()}</span>
            <span>{investigation.evidence.length} evidence items</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
// Stat Card Component
interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  change?: number;
  trend?: 'up' | 'down';
}
const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, change, trend }) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600',
      green: 'bg-green-100 text-green-600',
      yellow: 'bg-yellow-100 text-yellow-600',
      red: 'bg-red-100 text-red-600',
      purple: 'bg-purple-100 text-purple-600'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
          {change !== undefined && trend && (
            <div className="flex items-center mt-2 text-sm">
              {trend === 'up' ? (
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
              )}
              <span className={trend === 'up' ? 'text-green-600' : 'text-red-600'}>
                {Math.abs(change)}%
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg ${getColorClasses(color)}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};
// Analytics Dashboard Component
interface AnalyticsDashboardProps {
  events: AuditEvent[];
  investigations: Investigation[];
}
const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ events, investigations }) => {
  const [timeRange, setTimeRange] = useState('7d');
  // Calculate analytics metrics
  const totalEvents = events.length;
  const securityEvents = events.filter(e => e.category === 'security').length;
  const failedLogins = events.filter(e => e.eventType === 'login' && e.status === 'failure').length;
  const criticalEvents = events.filter(e => e.severity === 'critical').length;
  const eventTypesCount = events.reduce((acc, event) => {
    acc[event.eventType] = (acc[event.eventType] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const severityDistribution = events.reduce((acc, event) => {
    acc[event.severity] = (acc[event.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  return (
    <div className="space-y-6">
      {/* Analytics Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Audit Analytics</h2>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>
      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          value={totalEvents}
          icon={<Activity className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          value={securityEvents}
          icon={<Shield className="w-5 h-5" />}
          color="red"
        />
        <StatCard
          value={failedLogins}
          icon={<XCircle className="w-5 h-5" />}
          color="orange"
        />
        <StatCard
          value={criticalEvents}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="red"
        />
      </div>
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Event Types Distribution */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Event Types Distribution</h3>
          <div className="h-64">
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Event Type Chart</p>
                <div className="mt-4 space-y-2">
                  {Object.entries(eventTypesCount).map(([type, count]) => (
                    <div key={type} className="flex justify-between text-sm">
                      <span className="text-gray-600">{type.replace('_', ' ')}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Card>
        {/* Severity Distribution */}
        <Card>
          <h3 className="text-lg font-semibold mb-4">Severity Distribution</h3>
          <div className="h-64">
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Severity Distribution</p>
                <div className="mt-4 space-y-2">
                  {Object.entries(severityDistribution).map(([severity, count]) => (
                    <div key={severity} className="flex justify-between text-sm">
                      <span className="text-gray-600 capitalize">{severity}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
      {/* Recent Activity Timeline */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Recent Critical Activity</h3>
        <div className="space-y-4">
          {events
            .filter(e => e.severity === 'critical' || e.severity === 'high')
            .slice(0, 10)
            .map((event) => (
              <div key={event.id} className="flex items-start space-x-3">
                <div className={`p-2 rounded-full ${
                  event.severity === 'critical' ? 'bg-red-100' : 'bg-orange-100'
                }`}>
                  {getStatusIcon(event.status)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-gray-900">{event.action}</p>
                    <span className="text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{event.description}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {event.userName} • {event.source}
                  </p>
                </div>
              </div>
            ))}
        </div>
      </Card>
    </div>
  );
};
// Placeholder modals (simplified for brevity)
const EventDetailsModal: React.FC<any> = ({ event, onClose, onCreateInvestigation, getSeverityColor, getStatusIcon, getSourceIcon }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Event Details</h2>
          <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
        </div>
      </div>
      <div className="p-6">
        <p className="text-gray-600">Event details modal would show comprehensive information about the selected audit event.</p>
        <div className="mt-4">
          <Button onClick={() => onCreateInvestigation(event)}>Create Investigation</Button>
        </div>
      </div>
    </div>
  </div>
);
const InvestigationDetailsModal: React.FC<any> = ({ onClose, getSeverityColor }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Investigation Details</h2>
          <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
        </div>
      </div>
      <div className="p-6">
        <p className="text-gray-600">Investigation details modal would show comprehensive investigation information, timeline, evidence, and findings.</p>
      </div>
    </div>
  </div>
);
const CreateInvestigationModal: React.FC<any> = ({ event, onClose, onCreated }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Create Investigation</h2>
          <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
        </div>
      </div>
      <div className="p-6">
        <p className="text-gray-600">Create investigation form for event: {event.action}</p>
        <div className="mt-4 flex gap-3">
          <Button onClick={onCreated}>Create Investigation</Button>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
        </div>
      </div>
    </div>
  </div>
);
// Mock data generators
const mockAuditEventData = async (): Promise<AuditEvent[]> => {
  return [
    {
      id: '1',
      timestamp: '2024-03-12T10:30:00Z',
      eventType: 'login',
      category: 'authentication',
      severity: 'low',
      userId: 'user-123',
      userName: 'John Doe',
      userEmail: 'john.doe@company.com',
      userRole: 'Employee',
      action: 'Successful Login',
      description: 'User logged in successfully from web application',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      sessionId: 'sess_abc123',
      resource: 'auth',
      resourceId: 'auth-001',
      status: 'success',
      source: 'web',
      location: { country: 'United States', city: 'New York' },
      metadata: { loginMethod: 'password', mfaVerified: true },
      relatedEvents: [],
      tags: ['login', 'success']
    },
    {
      id: '2',
      timestamp: '2024-03-12T10:25:00Z',
      eventType: 'login',
      category: 'authentication',
      severity: 'medium',
      userId: 'user-456',
      userName: 'Jane Smith',
      userEmail: 'jane.smith@company.com',
      userRole: 'Manager',
      action: 'Failed Login Attempt',
      description: 'User failed to login with incorrect password',
      ipAddress: '192.168.1.101',
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      sessionId: 'sess_def456',
      resource: 'auth',
      resourceId: 'auth-002',
      status: 'failure',
      source: 'web',
      location: { country: 'United States', city: 'Los Angeles' },
      metadata: { loginMethod: 'password', failureReason: 'incorrect_password', attempts: 3 },
      relatedEvents: ['3', '4'],
      tags: ['login', 'failure', 'security']
    },
    {
      id: '3',
      timestamp: '2024-03-12T09:45:00Z',
      eventType: 'document_access',
      category: 'data_access',
      severity: 'medium',
      userId: 'user-789',
      userName: 'Mike Johnson',
      userEmail: 'mike.johnson@company.com',
      userRole: 'HR',
      action: 'Accessed Confidential Document',
      description: 'User accessed employee handbook with encryption',
      ipAddress: '192.168.1.102',
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
      sessionId: 'sess_ghi789',
      resource: 'document',
      resourceId: 'doc-handbook-001',
      status: 'success',
      source: 'mobile',
      location: { country: 'United States', city: 'Chicago' },
      metadata: { documentId: 'handbook-2024', accessLevel: 'confidential', encrypted: true },
      relatedEvents: [],
      tags: ['document', 'access', 'confidential']
    },
    {
      id: '4',
      timestamp: '2024-03-12T09:30:00Z',
      eventType: 'security_alert',
      category: 'security',
      severity: 'high',
      userId: 'system-001',
      userName: 'System',
      userEmail: 'system@company.com',
      userRole: 'System',
      action: 'Suspicious Activity Detected',
      description: 'Multiple failed login attempts detected from unusual IP',
      ipAddress: '203.0.113.1',
      userAgent: 'Unknown',
      sessionId: 'sess_unknown',
      resource: 'security',
      resourceId: 'security-001',
      status: 'warning',
      source: 'system',
      location: { country: 'Unknown', city: 'Unknown' },
      metadata: { alertType: 'brute_force', sourceIP: '203.0.113.1', attempts: 10 },
      relatedEvents: ['2'],
      investigationStatus: 'investigating',
      assignedTo: 'Security Team',
      tags: ['security', 'alert', 'brute_force']
    },
    {
      id: '5',
      timestamp: '2024-03-12T08:15:00Z',
      eventType: 'data_export',
      category: 'data_access',
      severity: 'medium',
      userId: 'user-101',
      userName: 'Sarah Williams',
      userEmail: 'sarah.williams@company.com',
      userRole: 'Compliance',
      action: 'Exported Compliance Report',
      description: 'User exported monthly compliance audit report',
      ipAddress: '192.168.1.103',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      sessionId: 'sess_jkl101',
      resource: 'report',
      resourceId: 'report-compliance-2024-03',
      status: 'success',
      source: 'web',
      location: { country: 'United States', city: 'Houston' },
      metadata: { reportType: 'compliance', format: 'pdf', size: '2.5MB', records: 1500 },
      relatedEvents: [],
      tags: ['export', 'report', 'compliance']
    }
  ];
};
const mockInvestigationData = async (): Promise<Investigation[]> => {
  return [
    {
      id: 'inv-001',
      title: 'Suspicious Login Activity',
      description: 'Investigation of multiple failed login attempts from unusual IP addresses',
      status: 'in_progress',
      priority: 'high',
      severity: 'high',
      assignedTo: 'Security Team',
      createdBy: 'System',
      createdAt: '2024-03-12T09:30:00Z',
      updatedAt: '2024-03-12T10:00:00Z',
      dueDate: '2024-03-15T00:00:00Z',
      tags: ['security', 'brute_force', 'ip_anomaly'],
      events: ['2', '4'],
      evidence: [
        {
          type: 'log',
          description: 'Server logs showing failed login attempts',
          uploadedAt: '2024-03-12T09:45:00Z',
          uploadedBy: 'Security Team'
        }
      ],
      timeline: [
        {
          timestamp: '2024-03-12T09:30:00Z',
          action: 'Investigation Created',
          performedBy: 'System',
          details: 'Auto-created due to security alert'
        },
        {
          timestamp: '2024-03-12T09:45:00Z',
          action: 'Evidence Collected',
          performedBy: 'Security Team',
          details: 'Server logs and network traffic analysis'
        }
      ],
      findings: [
        {
          category: 'Security Threat',
          description: 'Brute force attack from IP 203.0.113.1',
          impact: 'high',
          evidence: ['log-evidence-001']
        }
      ],
      recommendations: [
        {
          action: 'Block suspicious IP address',
          priority: 'high',
          assignedTo: 'IT Security',
          dueDate: '2024-03-13T00:00:00Z',
          status: 'pending'
        }
      ]
    },
    {
      id: 'inv-002',
      title: 'Unauthorized Document Access',
      description: 'Review of confidential document access by HR personnel',
      status: 'open',
      priority: 'medium',
      severity: 'medium',
      assignedTo: 'HR Compliance',
      createdBy: 'System',
      createdAt: '2024-03-12T09:45:00Z',
      updatedAt: '2024-03-12T09:45:00Z',
      dueDate: '2024-03-19T00:00:00Z',
      tags: ['document', 'access', 'confidential'],
      events: ['3'],
      evidence: [],
      timeline: [
        {
          timestamp: '2024-03-12T09:45:00Z',
          action: 'Investigation Created',
          performedBy: 'System',
          details: 'Auto-created due to confidential document access'
        }
      ],
      findings: [],
      recommendations: [
        {
          action: 'Verify user authorization level',
          priority: 'medium',
          assignedTo: 'HR Compliance',
          status: 'pending'
        }
      ]
    }
  ];
};
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failure': return <XCircle className="w-4 h-4 text-red-500" />;
    case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    default: return <Info className="w-4 h-4 text-gray-500" />;
  }
};