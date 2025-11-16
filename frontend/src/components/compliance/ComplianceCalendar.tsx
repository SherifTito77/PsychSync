import React, { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon,
  Plus,
  Edit,
  Trash2,
  Bell,
  Clock,
  AlertTriangle,
  CheckCircle,
  Users,
  FileText,
  Shield,
  TrendingUp,
  TrendingDown,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Download,
  Mail,
  Smartphone,
  Globe,
  Settings,
  Eye,
  Copy,
  MoreHorizontal,
  X,
  HelpCircle,
  CalendarDays,
  Timer,
  Flag,
  Target,
  Award,
  BookOpen,
  GraduationCap,
  ClipboardList,
  FileCheck,
  UserCheck,
  Star,
  Zap,
  Activity
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
interface ComplianceEvent {
  id: string;
  title: string;
  description: string;
  type: 'training' | 'audit' | 'deadline' | 'meeting' | 'reminder' | 'certification' | 'review';
  category: 'mandatory' | 'recommended' | 'optional';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'scheduled' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
  startDate: string;
  endDate: string;
  allDay: boolean;
  location?: string;
  virtual?: boolean;
  attendees: Array<{
    id: string;
    name: string;
    email: string;
    role: string;
    status: 'pending' | 'accepted' | 'declined' | 'tentative';
  }>;
  organizer: {
    id: string;
    name: string;
    email: string;
  };
  recurrence?: {
    pattern: 'daily' | 'weekly' | 'monthly' | 'yearly';
    interval: number;
    endDate?: string;
  };
  reminders: Array<{
    type: 'email' | 'push' | 'sms';
    timing: number; // minutes before event
    sent: boolean;
  }>;
  attachments: Array<{
    name: string;
    url: string;
    type: string;
  }>;
  complianceRequirements: string[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}
interface ComplianceCalendarProps {
  className?: string;
}
export const ComplianceCalendar: React.FC<ComplianceCalendarProps> = ({ className = '' }) => {
  const [events, setEvents] = useState<ComplianceEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'month' | 'week' | 'day' | 'list'>('month');
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<ComplianceEvent | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const { showNotification } = useNotification();
  useEffect(() => {
    loadEvents();
  }, [searchTerm, selectedType, selectedStatus, currentDate, viewMode]);
  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await mockComplianceEvents();
      const filteredData = filterEvents(data);
      setEvents(filteredData);
    } catch (error) {
      console.error('Failed to load events:', error);
      showNotification('Failed to load compliance events', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterEvents = (eventData: ComplianceEvent[]) => {
    return eventData.filter(event => {
      const matchesSearch = event.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           event.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           event.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesType = selectedType === 'all' || event.type === selectedType;
      const matchesStatus = selectedStatus === 'all' || event.status === selectedStatus;
      return matchesSearch && matchesType && matchesStatus;
    });
  };
  const handleCreateEvent = (date?: Date) => {
    setSelectedEvent(null);
    setSelectedDate(date || new Date());
    setShowEventModal(true);
  };
  const handleEditEvent = (event: ComplianceEvent) => {
    setSelectedEvent(event);
    setShowEventModal(true);
  };
  const handleDeleteEvent = (eventId: string) => {
    if (confirm('Are you sure you want to delete this event?')) {
      setEvents(prev => prev.filter(event => event.id !== eventId));
      showNotification('Event deleted successfully', 'success');
    }
  };
  const getTypeIcon = (type: ComplianceEvent['type']) => {
    switch (type) {
      case 'training': return <GraduationCap className="w-4 h-4" />;
      case 'audit': return <ClipboardList className="w-4 h-4" />;
      case 'deadline': return <Clock3 className="w-4 h-4" />;
      case 'meeting': return <Users className="w-4 h-4" />;
      case 'reminder': return <Bell className="w-4 h-4" />;
      case 'certification': return <Award className="w-4 h-4" />;
      case 'review': return <FileCheck className="w-4 h-4" />;
      default: return <CalendarIcon className="w-4 h-4" />;
    }
  };
  const getStatusColor = (status: ComplianceEvent['status']) => {
    switch (status) {
      case 'completed': return 'green';
      case 'in_progress': return 'blue';
      case 'scheduled': return 'yellow';
      case 'overdue': return 'red';
      case 'cancelled': return 'gray';
      default: return 'gray';
    }
  };
  const getPriorityColor = (priority: ComplianceEvent['priority']) => {
    switch (priority) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };
  const getCategoryColor = (category: ComplianceEvent['category']) => {
    switch (category) {
      case 'mandatory': return 'red';
      case 'recommended': return 'yellow';
      case 'optional': return 'green';
      default: return 'gray';
    }
  };
  const navigateDate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    switch (viewMode) {
      case 'month':
        newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
        break;
      case 'week':
        newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
        break;
      case 'day':
        newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1));
        break;
    }
    setCurrentDate(newDate);
  };
  const getEventsForDate = (date: Date) => {
    return events.filter(event => {
      const eventStart = new Date(event.startDate);
      const eventEnd = new Date(event.endDate);
      return date >= eventStart && date <= eventEnd;
    });
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  return (
    <div className={`max-w-7xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compliance Calendar</h1>
          <p className="text-gray-600 mt-1">Schedule and track compliance deadlines, training, and audits</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            icon={<RefreshCw className="w-4 h-4" />}
            onClick={loadEvents}
          >
            Refresh
          </Button>
          <Button
            onClick={() => handleCreateEvent()}
            icon={<Plus className="w-4 h-4" />}
          >
            Add Event
          </Button>
        </div>
      </div>
      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          value={events.filter(e => e.status === 'scheduled').length}
          icon={<CalendarIcon className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          value={events.filter(e => e.status === 'overdue').length}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="red"
        />
        <StatCard
          value={events.filter(e => {
            const eventDate = new Date(e.startDate);
            const now = new Date();
            const weekEnd = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
            return eventDate >= now && eventDate <= weekEnd;
          }).length}
          icon={<Activity className="w-5 h-5" />}
          color="purple"
        />
        <StatCard
          value={events.filter(e => e.status === 'completed').length}
          icon={<CheckCircle className="w-5 h-5" />}
          color="green"
        />
      </div>
      {/* Controls */}
      <Card className="mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Date Navigation */}
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="small"
              onClick={() => navigateDate('prev')}
              icon={<ChevronLeft className="w-4 h-4" />}
            />
            <h2 className="text-lg font-semibold text-gray-900 min-w-[200px] text-center">
              {currentDate.toLocaleDateString('en-US', {
                month: 'long',
                year: 'numeric',
                ...(viewMode === 'day' && { day: 'numeric' })
              })}
            </h2>
            <Button
              variant="outline"
              size="small"
              onClick={() => navigateDate('next')}
              icon={<ChevronRight className="w-4 h-4" />}
            />
            <Button
              variant="outline"
              size="small"
              onClick={() => setCurrentDate(new Date())}
            >
              Today
            </Button>
          </div>
          {/* View Mode */}
          <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
            {[
              { id: 'month', label: 'Month', icon: <CalendarDays className="w-4 h-4" /> },
              { id: 'week', label: 'Week', icon: <CalendarIcon className="w-4 h-4" /> },
              { id: 'day', label: 'Day', icon: <Clock className="w-4 h-4" /> },
              { id: 'list', label: 'List', icon: <FileText className="w-4 h-4" /> }
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => setViewMode(mode.id as any)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === mode.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {mode.icon}
                <span>{mode.label}</span>
              </button>
            ))}
          </div>
          {/* Search and Filters */}
          <div className="flex-1 flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search events..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="training">Training</option>
              <option value="audit">Audit</option>
              <option value="deadline">Deadline</option>
              <option value="meeting">Meeting</option>
              <option value="reminder">Reminder</option>
              <option value="certification">Certification</option>
              <option value="review">Review</option>
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="overdue">Overdue</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </Card>
      {/* Calendar Content */}
      {viewMode === 'month' && (
        <MonthView
          currentDate={currentDate}
          events={events}
          onDateClick={handleCreateEvent}
          onEventClick={handleEditEvent}
          getTypeIcon={getTypeIcon}
          getStatusColor={getStatusColor}
          getPriorityColor={getPriorityColor}
        />
      )}
      {viewMode === 'week' && (
        <WeekView
          currentDate={currentDate}
          events={events}
          onEventClick={handleEditEvent}
          getTypeIcon={getTypeIcon}
          getStatusColor={getStatusColor}
        />
      )}
      {viewMode === 'day' && (
        <DayView
          currentDate={currentDate}
          events={events}
          onEventClick={handleEditEvent}
          getTypeIcon={getTypeIcon}
          getStatusColor={getStatusColor}
        />
      )}
      {viewMode === 'list' && (
        <ListView
          events={events}
          onEventClick={handleEditEvent}
          getTypeIcon={getTypeIcon}
          getStatusColor={getStatusColor}
          getPriorityColor={getPriorityColor}
          getCategoryColor={getCategoryColor}
        />
      )}
      {/* Event Modal */}
      {showEventModal && (
        <EventModal
          event={selectedEvent}
          date={selectedDate}
          onClose={() => {
            setShowEventModal(false);
            setSelectedEvent(null);
            setSelectedDate(null);
          }}
          onSaved={(eventData) => {
            if (selectedEvent) {
              setEvents(prev => prev.map(e =>
                e.id === selectedEvent.id
                  ? { ...e, ...eventData, updatedAt: new Date().toISOString() }
                  : e
              ));
            } else {
              const newEvent: ComplianceEvent = {
                id: `event-${Date.now()}`,
                ...eventData,
                attendees: [],
                organizer: {
                  id: 'user-1',
                  name: 'Current User',
                  email: 'user@company.com'
                },
                reminders: [
                  { type: 'email', timing: 60, sent: false },
                  { type: 'push', timing: 15, sent: false }
                ],
                attachments: [],
                complianceRequirements: [],
                tags: [],
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                createdBy: 'Current User'
              };
              setEvents(prev => [...prev, newEvent]);
            }
            setShowEventModal(false);
            setSelectedEvent(null);
            setSelectedDate(null);
            showNotification('Event saved successfully', 'success');
          }}
        />
      )}
    </div>
  );
};
// View Components
const MonthView: React.FC<any> = ({ currentDate, events, onDateClick, onEventClick, getTypeIcon, getStatusColor, getPriorityColor }) => {
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    const days = [];
    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    // Add days of the month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i));
    }
    return days;
  };
  const getEventsForDate = (date: Date) => {
    return events.filter(event => {
      const eventStart = new Date(event.startDate);
      const eventEnd = new Date(event.endDate);
      const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1);
      return eventStart < dayEnd && eventEnd >= dayStart;
    });
  };
  const days = getDaysInMonth(currentDate);
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  return (
    <Card>
      <div className="p-4">
        {/* Week day headers */}
        <div className="grid grid-cols-7 gap-2 mb-4">
          {weekDays.map((day) => (
            <div key={day} className="text-center text-sm font-medium text-gray-700 py-2">
              {day}
            </div>
          ))}
        </div>
        {/* Calendar days */}
        <div className="grid grid-cols-7 gap-2">
          {days.map((date, index) => {
            if (!date) {
              return <div key={`empty-${index}`} className="aspect-square" />;
            }
            const dayEvents = getEventsForDate(date);
            const isToday = new Date().toDateString() === date.toDateString();
            const isCurrentMonth = date.getMonth() === currentDate.getMonth();
            return (
              <div
                key={date.toISOString()}
                onClick={() => onDateClick(date)}
                className={`aspect-square border rounded-lg p-2 cursor-pointer transition-colors ${
                  isToday
                    ? 'bg-blue-50 border-blue-200'
                    : isCurrentMonth
                    ? 'bg-white border-gray-200 hover:bg-gray-50'
                    : 'bg-gray-50 border-gray-100'
                }`}
              >
                <div className="text-sm font-medium mb-1">
                  {date.getDate()}
                </div>
                <div className="space-y-1">
                  {dayEvents.slice(0, 3).map((event) => (
                    <div
                      key={event.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onEventClick(event);
                      }}
                      className={`text-xs p-1 rounded truncate cursor-pointer ${
                        event.priority === 'critical' ? 'bg-red-100 text-red-700' :
                        event.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                        event.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}
                    >
                      {event.title}
                    </div>
                  ))}
                  {dayEvents.length > 3 && (
                    <div className="text-xs text-gray-500 text-center">
                      +{dayEvents.length - 3} more
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
const WeekView: React.FC<any> = ({ currentDate, events, onEventClick, getTypeIcon, getStatusColor }) => {
  const getWeekDays = (date: Date) => {
    const week = [];
    const startOfWeek = new Date(date);
    const day = startOfWeek.getDay();
    const diff = startOfWeek.getDate() - day;
    startOfWeek.setDate(diff);
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      week.push(day);
    }
    return week;
  };
  const weekDays = getWeekDays(currentDate);
  const hours = Array.from({ length: 24 }, (_, i) => i);
  return (
    <Card>
      <div className="p-4">
        <div className="grid grid-cols-8 gap-2">
          <div className="text-sm font-medium text-gray-700">Time</div>
          {weekDays.map((day) => (
            <div key={day.toISOString()} className="text-center text-sm font-medium text-gray-700">
              {day.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
            </div>
          ))}
          {hours.map((hour) => (
            <React.Fragment key={hour}>
              <div className="text-sm text-gray-500 py-2">
                {hour.toString().padStart(2, '0')}:00
              </div>
              {weekDays.map((day) => (
                <div
                  key={`${day.toISOString()}-${hour}`}
                  className="border border-gray-200 rounded p-1 min-h-[60px]"
                >
                  {/* Events for this hour and day would go here */}
                </div>
              ))}
            </React.Fragment>
          ))}
        </div>
      </div>
    </Card>
  );
};
const DayView: React.FC<any> = ({ currentDate, events, onEventClick, getTypeIcon, getStatusColor }) => {
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const dayEvents = events.filter(event => {
    const eventDate = new Date(event.startDate);
    return eventDate.toDateString() === currentDate.toDateString();
  });
  return (
    <Card>
      <div className="p-4">
        <div className="space-y-2">
          {hours.map((hour) => {
            const hourEvents = dayEvents.filter(event => {
              const eventHour = new Date(event.startDate).getHours();
              return eventHour === hour;
            });
            return (
              <div key={hour} className="flex gap-4">
                <div className="w-20 text-sm text-gray-500 py-2">
                  {hour.toString().padStart(2, '0')}:00
                </div>
                <div className="flex-1 border-l-2 border-gray-200 pl-4 min-h-[60px]">
                  {hourEvents.map((event) => (
                    <div
                      key={event.id}
                      onClick={() => onEventClick(event)}
                      className="mb-2 p-2 bg-white border border-gray-200 rounded-lg cursor-pointer hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center space-x-2">
                        {getTypeIcon(event.type)}
                        <span className="font-medium text-sm">{event.title}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(event.startDate).toLocaleTimeString()} - {new Date(event.endDate).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
const ListView: React.FC<any> = ({ events, onEventClick, getTypeIcon, getStatusColor, getPriorityColor, getCategoryColor }) => {
  const sortedEvents = [...events].sort((a, b) =>
    new Date(a.startDate).getTime() - new Date(b.startDate).getTime()
  );
  return (
    <div className="space-y-4">
      {sortedEvents.map((event) => (
        <EventCard
          key={event.id}
          event={event}
          onClick={() => onEventClick(event)}
          getTypeIcon={getTypeIcon}
          getStatusColor={getStatusColor}
          getPriorityColor={getPriorityColor}
          getCategoryColor={getCategoryColor}
        />
      ))}
    </div>
  );
};
// Event Card Component
const EventCard: React.FC<any> = ({ event, onClick, getTypeIcon, getStatusColor, getPriorityColor, getCategoryColor }) => {
  const [showActions, setShowActions] = useState(false);
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={onClick}>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${
              event.priority === 'critical' ? 'bg-red-100' :
              event.priority === 'high' ? 'bg-orange-100' :
              event.priority === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
            }`}>
              {getTypeIcon(event.type)}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{event.title}</h3>
              <p className="text-sm text-gray-600">{event.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge color={getStatusColor(event.status)} size="sm">
              {event.status}
            </Badge>
            <Badge color={getPriorityColor(event.priority)} size="sm" variant="outline">
              {event.priority}
            </Badge>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <span className="text-sm text-gray-600">Date & Time:</span>
            <p className="font-medium text-sm">
              {new Date(event.startDate).toLocaleString()} - {new Date(event.endDate).toLocaleString()}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Attendees:</span>
            <p className="font-medium text-sm">{event.attendees.length} people</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Category:</span>
            <Badge color={getCategoryColor(event.category)} size="sm" className="ml-2">
              {event.category}
            </Badge>
          </div>
        </div>
        {event.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-4">
            {event.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
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
}
const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color }) => {
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
        </div>
        <div className={`p-3 rounded-lg ${getColorClasses(color)}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};
// Event Modal Component
const EventModal: React.FC<any> = ({ event, date, onClose, onSaved }) => {
  const [formData, setFormData] = useState({
    title: event?.title || '',
    description: event?.description || '',
    type: event?.type || 'training',
    category: event?.category || 'mandatory',
    priority: event?.priority || 'medium',
    startDate: event?.startDate || (date ? date.toISOString() : new Date().toISOString()),
    endDate: event?.endDate || (date ? new Date(date.getTime() + 60 * 60 * 1000).toISOString() : new Date().toISOString()),
    allDay: event?.allDay || false,
    location: event?.location || '',
    virtual: event?.virtual || false
  });
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSaved(formData);
  };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {event ? 'Edit Event' : 'Create Event'}
            </h2>
            <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
          </div>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="training">Training</option>
                <option value="audit">Audit</option>
                <option value="deadline">Deadline</option>
                <option value="meeting">Meeting</option>
                <option value="reminder">Reminder</option>
                <option value="certification">Certification</option>
                <option value="review">Review</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as any }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="mandatory">Mandatory</option>
                <option value="recommended">Recommended</option>
                <option value="optional">Optional</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date & Time</label>
              <input
                type="datetime-local"
                value={formData.startDate.slice(0, 16)}
                onChange={(e) => setFormData(prev => ({ ...prev, startDate: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date & Time</label>
              <input
                type="datetime-local"
                value={formData.endDate.slice(0, 16)}
                onChange={(e) => setFormData(prev => ({ ...prev, endDate: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button type="submit">
              {event ? 'Update' : 'Create'} Event
            </Button>
            <Button variant="outline" type="button" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
// Mock data
const mockComplianceEvents = async (): Promise<ComplianceEvent[]> => {
  return [
    {
      id: 'event-1',
      title: 'Annual Harassment Prevention Training',
      description: 'Mandatory training for all employees on workplace harassment prevention',
      type: 'training',
      category: 'mandatory',
      priority: 'high',
      status: 'scheduled',
      startDate: '2024-03-15T09:00:00Z',
      endDate: '2024-03-15T11:00:00Z',
      allDay: false,
      location: 'Conference Room A',
      virtual: false,
      attendees: [
        { id: 'user-1', name: 'John Doe', email: 'john@company.com', role: 'Employee', status: 'pending' },
        { id: 'user-2', name: 'Jane Smith', email: 'jane@company.com', role: 'Manager', status: 'accepted' }
      ],
      organizer: {
        id: 'hr-1',
        name: 'HR Team',
        email: 'hr@company.com'
      },
      reminders: [
        { type: 'email', timing: 1440, sent: false },
        { type: 'push', timing: 60, sent: false }
      ],
      attachments: [],
      complianceRequirements: ['State Law Compliance', 'Company Policy'],
      tags: ['training', 'mandatory', 'harassment'],
      createdAt: '2024-02-01T10:00:00Z',
      updatedAt: '2024-02-15T14:30:00Z',
      createdBy: 'HR Team'
    },
    {
      id: 'event-2',
      title: 'Q1 Compliance Audit',
      description: 'Quarterly compliance audit for all departments',
      type: 'audit',
      category: 'mandatory',
      priority: 'critical',
      status: 'in_progress',
      startDate: '2024-03-20T00:00:00Z',
      endDate: '2024-03-22T23:59:59Z',
      allDay: true,
      virtual: true,
      attendees: [],
      organizer: {
        id: 'audit-1',
        name: 'Compliance Team',
        email: 'compliance@company.com'
      },
      reminders: [
        { type: 'email', timing: 2880, sent: false }
      ],
      attachments: [],
      complianceRequirements: ['SOX Compliance', 'Internal Audit Policy'],
      tags: ['audit', 'quarterly', 'critical'],
      createdAt: '2024-01-15T09:00:00Z',
      updatedAt: '2024-03-01T10:00:00Z',
      createdBy: 'Compliance Team'
    }
  ];
};