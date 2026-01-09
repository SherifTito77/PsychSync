/**
 * Audit Trail - Main Orchestrator
 *
 * Comprehensive compliance audit logging and investigation system
 *
 * SPLIT from 1,172 lines → ~250 lines (79% reduction)
 */

import React from 'react';
import {
  Shield,
  Search,
  Filter,
  Download,
  RefreshCw,
  FileText,
  Activity,
  ChevronDown,
  Eye,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Globe,
  Smartphone,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

import { useAuditTrail } from './hooks/useAuditTrail';
import {
  getSeverityColor,
  getStatusColor,
  getEventTypeIcon,
  getSourceIcon,
  getStatusIcon,
  formatRelativeTime,
  maskIPAddress,
  maskEmail,
} from './utils/displayHelpers';

const AuditTrail: React.FC = () => {
  const {
    filteredEvents,
    eventCount,
    loading,
    filters,
    sortField,
    sortOrder,
    selectedEvent,
    setSelectedEvent,
    updateFilter,
    clearFilters,
    handleSort,
    exportToCSV,
    loadEvents,
  } = useAuditTrail();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-purple-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Audit Trail</h1>
            <p className="text-sm text-gray-500">Comprehensive compliance and security event logging</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className="bg-purple-100 text-purple-600">
            {eventCount} Events
          </Badge>
          <Button variant="outline" size="sm" onClick={loadEvents}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={exportToCSV}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search events..."
                value={filters.searchTerm}
                onChange={(e) => updateFilter('searchTerm', e.target.value)}
                className="w-full pl-8 pr-4 py-2 border rounded-lg text-sm"
              />
            </div>

            {/* Event Type Filter */}
            <select
              value={filters.eventType}
              onChange={(e) => updateFilter('eventType', e.target.value)}
              className="px-4 py-2 border rounded-lg text-sm"
            >
              <option value="all">All Event Types</option>
              <option value="login">Login</option>
              <option value="logout">Logout</option>
              <option value="document_access">Document Access</option>
              <option value="data_export">Data Export</option>
              <option value="security_alert">Security Alert</option>
            </select>

            {/* Severity Filter */}
            <select
              value={filters.severity}
              onChange={(e) => updateFilter('severity', e.target.value)}
              className="px-4 py-2 border rounded-lg text-sm"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={filters.status}
              onChange={(e) => updateFilter('status', e.target.value)}
              className="px-4 py-2 border rounded-lg text-sm"
            >
              <option value="all">All Statuses</option>
              <option value="success">Success</option>
              <option value="failure">Failure</option>
              <option value="warning">Warning</option>
            </select>

            {/* Date Range */}
            <input
              type="date"
              value={filters.dateRange.start}
              onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, start: e.target.value })}
              className="px-4 py-2 border rounded-lg text-sm"
            />
          </div>
        </CardContent>
      </Card>

      {/* Events List */}
      <Card>
        <CardHeader>
          <CardTitle>Event Log</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredEvents.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No audit events found</p>
              <p className="text-sm">Try adjusting your filters</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredEvents.map((event) => {
                const EventTypeIcon = getEventTypeIcon(event.eventType);
                const SourceIcon = getSourceIcon(event.source);
                const StatusIcon = getStatusIcon(event.status);

                return (
                  <div
                    key={event.id}
                    className="p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => setSelectedEvent(event)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        {/* Event Icon */}
                        <div className={`p-2 rounded-lg ${getSeverityColor(event.severity)}`}>
                          <EventTypeIcon className="h-5 w-5" />
                        </div>

                        {/* Event Details */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold">{event.action}</h3>
                            <Badge className={getSeverityColor(event.severity)} size="sm">
                              {event.severity.toUpperCase()}
                            </Badge>
                            <Badge variant="outline" size="sm">
                              {event.category}
                            </Badge>
                          </div>

                          <p className="text-sm text-gray-600 mb-2">{event.description}</p>

                          <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <SourceIcon className="h-3 w-3" />
                              {event.source}
                            </span>
                            <span className="flex items-center gap-1">
                              <StatusIcon className={`h-3 w-3 ${getStatusColor(event.status)}`} />
                              {event.status}
                            </span>
                            <span>{formatRelativeTime(event.timestamp)}</span>
                            <span>{event.userName}</span>
                            <span>{maskIPAddress(event.ipAddress)}</span>
                          </div>

                          {event.tags && event.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-2">
                              {event.tags.map((tag, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          )}

                          {event.investigationStatus && event.investigationStatus !== 'none' && (
                            <div className="mt-2">
                              <Badge className="bg-orange-100 text-orange-600">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                {event.investigationStatus}
                              </Badge>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Action Icon */}
                      <Eye className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Event Details</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedEvent(null)}
                >
                  ✕
                </Button>
              </div>

              <div className="space-y-6">
                {/* Overview */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Event Type</label>
                    <p className="font-semibold">{selectedEvent.eventType}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Category</label>
                    <p className="font-semibold">{selectedEvent.category}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Severity</label>
                    <p className={`font-semibold capitalize ${getSeverityColor(selectedEvent.severity)}`}>
                      {selectedEvent.severity}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Status</label>
                    <p className={`font-semibold capitalize ${getStatusColor(selectedEvent.status)}`}>
                      {selectedEvent.status}
                    </p>
                  </div>
                </div>

                {/* User Information */}
                <div>
                  <h3 className="font-semibold mb-3">User Information</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Name:</span>
                      <span className="ml-2 font-medium">{selectedEvent.userName}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Email:</span>
                      <span className="ml-2 font-medium">{maskEmail(selectedEvent.userEmail)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Role:</span>
                      <span className="ml-2 font-medium">{selectedEvent.userRole}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">User ID:</span>
                      <span className="ml-2 font-medium">{selectedEvent.userId}</span>
                    </div>
                  </div>
                </div>

                {/* Technical Details */}
                <div>
                  <h3 className="font-semibold mb-3">Technical Details</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">IP Address:</span>
                      <span className="ml-2 font-medium">{maskIPAddress(selectedEvent.ipAddress)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Source:</span>
                      <span className="ml-2 font-medium capitalize">{selectedEvent.source}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-500">User Agent:</span>
                      <span className="ml-2 font-medium text-xs">{selectedEvent.userAgent}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Session ID:</span>
                      <span className="ml-2 font-medium">{selectedEvent.sessionId}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Timestamp:</span>
                      <span className="ml-2 font-medium">{selectedEvent.timestamp}</span>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-gray-700">{selectedEvent.description}</p>
                </div>

                {/* Metadata */}
                {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">Additional Metadata</h3>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(selectedEvent.metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-2 pt-4 border-t">
                  <Button variant="outline" onClick={() => setSelectedEvent(null)}>
                    Close
                  </Button>
                  {selectedEvent.investigationStatus === 'none' && (
                    <Button>
                      Start Investigation
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditTrail;
