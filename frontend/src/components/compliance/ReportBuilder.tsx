import React, { useState, useEffect } from 'react';
import {
  FileText,
  Plus,
  Trash2,
  Edit,
  Save,
  Download,
  Eye,
  Copy,
  Settings,
  BarChart3,
  PieChart,
  TrendingUp,
  TrendingDown,
  Calendar,
  Filter,
  Users,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  Globe,
  Mail,
  Smartphone,
  Key,
  Zap,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  GripVertical,
  X,
  HelpCircle,
  Info,
  Search,
  ChevronRight,
  ChevronLeft,
  Layout,
  Table,
  List
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: 'compliance' | 'audit' | 'analytics' | 'custom';
  isPublic: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  layout: 'single_column' | 'two_column' | 'dashboard' | 'custom';
  sections: ReportSection[];
  filters: ReportFilter[];
  schedule?: ReportSchedule;
  permissions: {
    view: string[];
    edit: string[];
    share: string[];
  };
  tags: string[];
}
interface ReportSection {
  id: string;
  type: 'chart' | 'table' | 'kpi' | 'text' | 'image' | 'list' | 'timeline';
  title: string;
  description?: string;
  dataSource: string;
  query?: string;
  config: SectionConfig;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  visibility: {
    showTitle: boolean;
    showDescription: boolean;
    showBorder: boolean;
    backgroundColor?: string;
  };
}
interface SectionConfig {
  // Chart specific
  chartType?: 'line' | 'bar' | 'pie' | 'donut' | 'area' | 'scatter' | 'heatmap';
  xAxis?: string;
  yAxis?: string;
  groupBy?: string;
  aggregation?: 'sum' | 'count' | 'average' | 'min' | 'max';
  // Table specific
  columns?: Array<{
    field: string;
    label: string;
    format?: string;
    sortable?: boolean;
  }>;
  pagination?: {
    enabled: boolean;
    pageSize: number;
  };
  // KPI specific
  kpiType?: 'single' | 'comparison' | 'trend';
  targetValue?: number;
  showTrend?: boolean;
  // Common
  colors?: string[];
  legend?: {
    show: boolean;
    position: 'top' | 'bottom' | 'left' | 'right';
  };
  grid?: {
    show: boolean;
    color?: string;
  };
}
interface ReportFilter {
  id: string;
  field: string;
  type: 'date_range' | 'select' | 'multiselect' | 'text' | 'number';
  label: string;
  defaultValue?: any;
  options?: Array<{ label: string; value: any }>;
  required?: boolean;
}
interface ReportSchedule {
  enabled: boolean;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  recipients: string[];
  format: 'pdf' | 'excel' | 'csv';
  time?: string;
  dayOfWeek?: number;
  dayOfMonth?: number;
}
interface ReportBuilderProps {
  className?: string;
}
export const ReportBuilder: React.FC<ReportBuilderProps> = ({ className = '' }) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'templates' | 'builder' | 'scheduled'>('templates');
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const { showNotification } = useNotification();
  // Builder state
  const [builderMode, setBuilderMode] = useState<'design' | 'preview' | 'data'>('design');
  const [selectedSection, setSelectedSection] = useState<ReportSection | null>(null);
  const [draggedSection, setDraggedSection] = useState<string | null>(null);
  useEffect(() => {
    loadTemplates();
  }, [searchTerm, selectedCategory]);
  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await mockReportTemplates();
      const filteredData = filterTemplates(data);
      setTemplates(filteredData);
    } catch (error) {
      console.error('Failed to load templates:', error);
      showNotification('Failed to load report templates', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterTemplates = (templateData: ReportTemplate[]) => {
    return templateData.filter(template => {
      const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           template.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  };
  const handleCreateTemplate = (templateData: Partial<ReportTemplate>) => {
    const newTemplate: ReportTemplate = {
      id: `template-${Date.now()}`,
      name: templateData.name || 'New Report Template',
      description: templateData.description || '',
      category: templateData.category || 'custom',
      isPublic: templateData.isPublic || false,
      createdBy: 'Current User',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      layout: templateData.layout || 'single_column',
      sections: [],
      filters: [],
      permissions: {
        view: ['current-user'],
        edit: ['current-user'],
        share: ['current-user']
      },
      tags: templateData.tags || []
    };
    setTemplates(prev => [newTemplate, ...prev]);
    setSelectedTemplate(newTemplate);
    setActiveTab('builder');
    setShowCreateModal(false);
    showNotification('Report template created successfully', 'success');
  };
  const handleAddSection = (type: ReportSection['type']) => {
    if (!selectedTemplate) return;
    const newSection: ReportSection = {
      id: `section-${Date.now()}`,
      type,
      title: `New ${type.charAt(0).toUpperCase() + type.slice(1)} Section`,
      dataSource: 'compliance_events',
      config: getDefaultConfig(type),
      position: {
        x: 0,
        y: selectedTemplate.sections.length * 200,
        width: type === 'kpi' ? 3 : 6,
        height: type === 'kpi' ? 2 : 4
      },
      visibility: {
        showTitle: true,
        showDescription: false,
        showBorder: true
      }
    };
    setSelectedTemplate(prev => prev ? {
      ...prev,
      sections: [...prev.sections, newSection],
      updatedAt: new Date().toISOString()
    } : null);
    setSelectedSection(newSection);
    showNotification('Section added successfully', 'success');
  };
  const handleUpdateSection = (sectionId: string, updates: Partial<ReportSection>) => {
    if (!selectedTemplate) return;
    setSelectedTemplate(prev => prev ? {
      ...prev,
      sections: prev.sections.map(section =>
        section.id === sectionId ? { ...section, ...updates } : section
      ),
      updatedAt: new Date().toISOString()
    } : null);
    if (selectedSection?.id === sectionId) {
      setSelectedSection(prev => prev ? { ...prev, ...updates } : null);
    }
  };
  const handleDeleteSection = (sectionId: string) => {
    if (!selectedTemplate) return;
    setSelectedTemplate(prev => prev ? {
      ...prev,
      sections: prev.sections.filter(section => section.id !== sectionId),
      updatedAt: new Date().toISOString()
    } : null);
    if (selectedSection?.id === sectionId) {
      setSelectedSection(null);
    }
    showNotification('Section deleted successfully', 'success');
  };
  const getDefaultConfig = (type: ReportSection['type']): SectionConfig => {
    switch (type) {
      case 'chart':
        return {
          chartType: 'bar',
          aggregation: 'count',
          legend: { show: true, position: 'bottom' },
          grid: { show: true }
        };
      case 'table':
        return {
          columns: [
            { field: 'date', label: 'Date', sortable: true },
            { field: 'type', label: 'Type', sortable: true },
            { field: 'count', label: 'Count', sortable: true }
          ],
          pagination: { enabled: true, pageSize: 10 }
        };
      case 'kpi':
        return {
          kpiType: 'single',
          showTrend: true
        };
      default:
        return {};
    }
  };
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'compliance': return 'blue';
      case 'audit': return 'purple';
      case 'analytics': return 'green';
      case 'custom': return 'gray';
      default: return 'gray';
    }
  };
  const getSectionIcon = (type: ReportSection['type']) => {
    switch (type) {
      case 'chart': return <BarChart3 className="w-4 h-4" />;
      case 'table': return <Table className="w-4 h-4" />;
      case 'kpi': return <TrendingUp className="w-4 h-4" />;
      case 'text': return <FileText className="w-4 h-4" />;
      case 'list': return <List className="w-4 h-4" />;
      default: return <Layout className="w-4 h-4" />;
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
          <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
          <p className="text-gray-600 mt-1">Create customizable compliance reports and dashboards</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setShowCreateModal(true)}
            icon={<Plus className="w-4 h-4" />}
          >
            New Template
          </Button>
          <Button
            variant="outline"
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            icon={viewMode === 'grid' ? <List className="w-4 h-4" /> : <Layout className="w-4 h-4" />}
          />
        </div>
      </div>
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'templates', label: 'Templates', count: templates.length },
            { id: 'builder', label: 'Builder', count: selectedTemplate ? 1 : null },
            { id: 'scheduled', label: 'Scheduled', count: templates.filter(t => t.schedule?.enabled).length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } ${tab.id === 'builder' && !selectedTemplate ? 'opacity-50 cursor-not-allowed' : ''}`}
              disabled={tab.id === 'builder' && !selectedTemplate}
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
      {/* Tab Content */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search report templates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Categories</option>
                  <option value="compliance">Compliance</option>
                  <option value="audit">Audit</option>
                  <option value="analytics">Analytics</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>
          </Card>
          {/* Templates Grid */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map((template) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  onSelect={() => {
                    setSelectedTemplate(template);
                    setActiveTab('builder');
                  }}
                  onPreview={() => {
                    setSelectedTemplate(template);
                    setShowPreviewModal(true);
                  }}
                  getCategoryColor={getCategoryColor}
                />
              ))}
            </div>
          ) : (
            <Card>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Template
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sections
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {templates.map((template) => (
                      <TemplateRow
                        key={template.id}
                        template={template}
                        onSelect={() => {
                          setSelectedTemplate(template);
                          setActiveTab('builder');
                        }}
                        onPreview={() => {
                          setSelectedTemplate(template);
                          setShowPreviewModal(true);
                        }}
                        getCategoryColor={getCategoryColor}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      )}
      {activeTab === 'builder' && selectedTemplate && (
        <ReportBuilderInterface
          template={selectedTemplate}
          onUpdate={(updates) => setSelectedTemplate(prev => prev ? { ...prev, ...updates } : null)}
          onAddSection={handleAddSection}
          onUpdateSection={handleUpdateSection}
          onDeleteSection={handleDeleteSection}
          selectedSection={selectedSection}
          onSelectSection={setSelectedSection}
          builderMode={builderMode}
          onBuilderModeChange={setBuilderMode}
        />
      )}
      {activeTab === 'scheduled' && (
        <ScheduledReports templates={templates} onUpdate={loadTemplates} />
      )}
      {/* Create Template Modal */}
      {showCreateModal && (
        <CreateTemplateModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateTemplate}
        />
      )}
      {/* Preview Modal */}
      {showPreviewModal && selectedTemplate && (
        <ReportPreviewModal
          template={selectedTemplate}
          onClose={() => setShowPreviewModal(false)}
        />
      )}
    </div>
  );
};
// Template Card Component
interface TemplateCardProps {
  template: ReportTemplate;
  onSelect: () => void;
  onPreview: () => void;
  getCategoryColor: (category: string) => string;
}
const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onSelect,
  onPreview,
  getCategoryColor
}) => {
  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer group">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600">
              {template.name}
            </h3>
            <p className="text-sm text-gray-600 line-clamp-2">{template.description}</p>
          </div>
          <Badge color={getCategoryColor(template.category)} size="sm">
            {template.category}
          </Badge>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Sections:</span>
            <span className="font-medium">{template.sections.length}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Layout:</span>
            <span className="font-medium">{template.layout.replace('_', ' ')}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Created:</span>
            <span className="font-medium">{new Date(template.createdAt).toLocaleDateString()}</span>
          </div>
          {template.schedule?.enabled && (
            <div className="flex items-center text-sm text-green-600">
              <Clock className="w-4 h-4 mr-2" />
              Scheduled
            </div>
          )}
        </div>
        {template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-4">
            {template.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
            {template.tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-50 text-gray-500 text-xs rounded-full">
                +{template.tags.length - 3}
              </span>
            )}
          </div>
        )}
        <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
          <Button
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onSelect();
            }}
          >
            Edit
          </Button>
          <Button
            variant="outline"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onPreview();
            }}
          >
            Preview
          </Button>
        </div>
      </div>
    </Card>
  );
};
// Template Row Component
interface TemplateRowProps {
  template: ReportTemplate;
  onSelect: () => void;
  onPreview: () => void;
  getCategoryColor: (category: string) => string;
}
const TemplateRow: React.FC<TemplateRowProps> = ({
  template,
  onSelect,
  onPreview,
  getCategoryColor
}) => {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">{template.name}</div>
          <div className="text-sm text-gray-500">{template.description}</div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <Badge color={getCategoryColor(template.category)} size="sm">
          {template.category}
        </Badge>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {template.sections.length}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {new Date(template.createdAt).toLocaleDateString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
        <Button variant="outline" size="small" onClick={onSelect}>
          Edit
        </Button>
        <Button variant="outline" size="small" onClick={onPreview}>
          Preview
        </Button>
      </td>
    </tr>
  );
};
// Report Builder Interface Component
interface ReportBuilderInterfaceProps {
  template: ReportTemplate;
  onUpdate: (updates: Partial<ReportTemplate>) => void;
  onAddSection: (type: ReportSection['type']) => void;
  onUpdateSection: (sectionId: string, updates: Partial<ReportSection>) => void;
  onDeleteSection: (sectionId: string) => void;
  selectedSection: ReportSection | null;
  onSelectSection: (section: ReportSection | null) => void;
  builderMode: 'design' | 'preview' | 'data';
  onBuilderModeChange: (mode: 'design' | 'preview' | 'data') => void;
}
const ReportBuilderInterface: React.FC<ReportBuilderInterfaceProps> = ({
  template,
  onUpdate,
  onAddSection,
  onUpdateSection,
  onDeleteSection,
  selectedSection,
  onSelectSection,
  builderMode,
  onBuilderModeChange
}) => {
  return (
    <div className="space-y-6">
      {/* Builder Toolbar */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900">{template.name}</h2>
            <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
              {[
                { id: 'design', label: 'Design', icon: <Layout className="w-4 h-4" /> },
                { id: 'data', label: 'Data', icon: <Database className="w-4 h-4" /> },
                { id: 'preview', label: 'Preview', icon: <Eye className="w-4 h-4" /> }
              ].map((mode) => (
                <button
                  key={mode.id}
                  onClick={() => onBuilderModeChange(mode.id as any)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    builderMode === mode.id
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {mode.icon}
                  <span>{mode.label}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="outline" icon={<Save className="w-4 h-4" />}>
              Save
            </Button>
            <Button variant="outline" icon={<Download className="w-4 h-4" />}>
              Export
            </Button>
          </div>
        </div>
      </Card>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Section Palette */}
        <div className="lg:col-span-1">
          <Card>
            <h3 className="font-semibold text-gray-900 mb-4">Add Section</h3>
            <div className="space-y-2">
              {[
                { type: 'chart' as const, label: 'Chart', icon: <BarChart3 className="w-4 h-4" /> },
                { type: 'table' as const, label: 'Table', icon: <Table className="w-4 h-4" /> },
                { type: 'kpi' as const, label: 'KPI', icon: <TrendingUp className="w-4 h-4" /> },
                { type: 'text' as const, label: 'Text', icon: <FileText className="w-4 h-4" /> },
                { type: 'list' as const, label: 'List', icon: <List className="w-4 h-4" /> }
              ].map((sectionType) => (
                <button
                  key={sectionType.type}
                  onClick={() => onAddSection(sectionType.type)}
                  className="w-full flex items-center space-x-3 px-3 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="text-gray-500">{sectionType.icon}</div>
                  <span className="text-sm font-medium text-gray-900">{sectionType.label}</span>
                </button>
              ))}
            </div>
          </Card>
          {/* Section Properties */}
          {selectedSection && (
            <Card className="mt-6">
              <h3 className="font-semibold text-gray-900 mb-4">Section Properties</h3>
              <SectionProperties
                section={selectedSection}
                onUpdate={(updates) => onUpdateSection(selectedSection.id, updates)}
                onDelete={() => onDeleteSection(selectedSection.id)}
              />
            </Card>
          )}
        </div>
        {/* Canvas */}
        <div className="lg:col-span-3">
          <Card className="min-h-[600px]">
            {builderMode === 'design' && (
              <ReportCanvas
                template={template}
                selectedSection={selectedSection}
                onSelectSection={onSelectSection}
                onUpdateSection={onUpdateSection}
              />
            )}
            {builderMode === 'preview' && (
              <ReportPreview template={template} />
            )}
            {builderMode === 'data' && (
              <DataSources template={template} />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
// Simplified placeholder components for the builder interface
const ReportCanvas: React.FC<any> = ({ template, selectedSection, onSelectSection, onUpdateSection }) => (
  <div className="p-6">
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
      <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">Report Canvas</h3>
      <p className="text-gray-500 mb-4">
        Drag and drop sections here to build your report layout
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {template.sections.map((section) => (
          <div
            key={section.id}
            onClick={() => onSelectSection(section)}
            className={`p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedSection?.id === section.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                {getSectionIcon(section.type)}
                <span className="font-medium text-sm">{section.title}</span>
              </div>
              <GripVertical className="w-4 h-4 text-gray-400" />
            </div>
            <p className="text-xs text-gray-500">{section.dataSource}</p>
          </div>
        ))}
      </div>
      {template.sections.length === 0 && (
        <p className="text-sm text-gray-500">Add sections from the palette to get started</p>
      )}
    </div>
  </div>
);
const SectionProperties: React.FC<any> = ({ section, onUpdate, onDelete }) => (
  <div className="space-y-4">
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
      <input
        type="text"
        value={section.title}
        onChange={(e) => onUpdate({ title: e.target.value })}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
      />
    </div>
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Data Source</label>
      <select
        value={section.dataSource}
        onChange={(e) => onUpdate({ dataSource: e.target.value })}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
      >
        <option value="compliance_events">Compliance Events</option>
        <option value="training_completion">Training Completion</option>
        <option value="feedback_data">Feedback Data</option>
        <option value="user_activity">User Activity</option>
        <option value="document_access">Document Access</option>
      </select>
    </div>
    <Button
      variant="outline"
      size="small"
      onClick={onDelete}
      className="w-full text-red-600 border-red-200 hover:bg-red-50"
    >
      Delete Section
    </Button>
  </div>
);
const ReportPreview: React.FC<any> = ({ template }) => (
  <div className="p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Report Preview</h3>
    <div className="space-y-6">
      {template.sections.map((section) => (
        <div key={section.id} className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">{section.title}</h4>
          <div className="text-sm text-gray-600">
            {section.type} section with data from {section.dataSource}
          </div>
        </div>
      ))}
    </div>
  </div>
);
const DataSources: React.FC<any> = ({ template }) => (
  <div className="p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Sources</h3>
    <div className="space-y-4">
      {template.sections.map((section) => (
        <div key={section.id} className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">{section.title}</h4>
          <p className="text-sm text-gray-600">Source: {section.dataSource}</p>
          <p className="text-xs text-gray-500 mt-1">Configure query and data mapping here</p>
        </div>
      ))}
    </div>
  </div>
);
const ScheduledReports: React.FC<any> = ({ templates, onUpdate }) => (
  <div className="space-y-6">
    <div className="text-center py-12">
      <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">Scheduled Reports</h3>
      <p className="text-gray-500">
        Configure automated report generation and delivery schedules
      </p>
    </div>
  </div>
);
// Modal Components
const CreateTemplateModal: React.FC<any> = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'custom' as const,
    layout: 'single_column' as const,
    isPublic: false,
    tags: [] as string[]
  });
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate(formData);
  };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Create Report Template</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="compliance">Compliance</option>
              <option value="audit">Audit</option>
              <option value="analytics">Analytics</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div className="flex gap-3">
            <Button type="submit">Create Template</Button>
            <Button variant="outline" type="button" onClick={onClose}>
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
const ReportPreviewModal: React.FC<any> = ({ template, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
    <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Report Preview: {template.name}</h2>
          <Button variant="outline" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
        </div>
      </div>
      <div className="p-6">
        <p className="text-gray-600">Report preview would show the fully rendered report with sample data.</p>
      </div>
    </div>
  </div>
);
// Helper functions
const getSectionIcon = (type: ReportSection['type']) => {
  switch (type) {
    case 'chart': return <BarChart3 className="w-4 h-4" />;
    case 'table': return <Table className="w-4 h-4" />;
    case 'kpi': return <TrendingUp className="w-4 h-4" />;
    case 'text': return <FileText className="w-4 h-4" />;
    case 'list': return <List className="w-4 h-4" />;
    default: return <Layout className="w-4 h-4" />;
  }
};
// Mock data
const mockReportTemplates = async (): Promise<ReportTemplate[]> => {
  return [
    {
      id: 'template-1',
      name: 'Monthly Compliance Dashboard',
      description: 'Comprehensive overview of compliance metrics and performance indicators',
      category: 'compliance',
      isPublic: true,
      createdBy: 'Compliance Team',
      createdAt: '2024-02-15T10:00:00Z',
      updatedAt: '2024-03-01T14:30:00Z',
      layout: 'dashboard',
      sections: [
        {
          id: 'section-1',
          type: 'kpi',
          title: 'Overall Compliance Score',
          dataSource: 'compliance_events',
          config: { kpiType: 'single', showTrend: true },
          position: { x: 0, y: 0, width: 3, height: 2 },
          visibility: { showTitle: true, showDescription: false, showBorder: true }
        }
      ],
      filters: [],
      schedule: {
        enabled: true,
        frequency: 'monthly',
        recipients: ['manager@company.com'],
        format: 'pdf'
      },
      permissions: {
        view: ['all'],
        edit: ['compliance-team'],
        share: ['all']
      },
      tags: ['dashboard', 'monthly', 'compliance']
    },
    {
      id: 'template-2',
      name: 'Training Completion Report',
      description: 'Detailed report on employee training completion rates and progress',
      category: 'analytics',
      isPublic: false,
      createdBy: 'HR Team',
      createdAt: '2024-01-20T09:00:00Z',
      updatedAt: '2024-02-10T16:45:00Z',
      layout: 'single_column',
      sections: [
        {
          id: 'section-2',
          type: 'chart',
          title: 'Training Completion Trends',
          dataSource: 'training_completion',
          config: { chartType: 'line', aggregation: 'count' },
          position: { x: 0, y: 0, width: 6, height: 4 },
          visibility: { showTitle: true, showDescription: false, showBorder: true }
        }
      ],
      filters: [],
      permissions: {
        view: ['hr-team', 'managers'],
        edit: ['hr-team'],
        share: ['hr-team']
      },
      tags: ['training', 'completion', 'analytics']
    }
  ];
};