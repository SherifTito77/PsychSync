import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Upload,
  Download,
  Search,
  Filter,
  Eye,
  Lock,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Trash2,
  Share,
  Bookmark,
  BookmarkCheck,
  MoreHorizontal,
  Plus,
  ChevronDown,
  X,
  FileCheck,
  History,
  Users,
  Archive,
  Copy
} from 'lucide-react';
import Button from '../common/Button';
import { Card } from '../common/card';
import Badge from '../common/Badge';
import LoadingSpinner from '../common/LoadingSpinner';
import { useNotification } from '../../contexts/NotificationContext';
interface Document {
  id: string;
  title: string;
  description: string;
  type: 'policy' | 'handbook' | 'training' | 'form' | 'contract' | 'audit' | 'other';
  category: string;
  tags: string[];
  version: string;
  status: 'draft' | 'review' | 'published' | 'archived';
  author: string;
  authorId: string;
  createdAt: string;
  updatedAt: string;
  expiresAt?: string;
  requiredReading: boolean;
  readingProgress: number;
  accessLevel: 'public' | 'internal' | 'restricted' | 'confidential';
  encrypted: boolean;
  fileUrl?: string;
  fileSize: number;
  fileType: string;
  downloads: number;
  views: number;
  lastViewed?: string;
  complianceRequirements: string[];
  acknowledgements: number;
  totalRequiredReaders: number;
  versions: Array<{
    version: string;
    createdAt: string;
    author: string;
    changes: string;
  }>;
}
interface DocumentManagementProps {
  className?: string;
}
export const DocumentManagement: React.FC<DocumentManagementProps> = ({ className = '' }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDocumentPreview, setShowDocumentPreview] = useState(false);
  const [sortBy, setSortBy] = useState<'title' | 'createdAt' | 'updatedAt' | 'views' | 'downloads'>('updatedAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const { showNotification } = useNotification();
  const fileInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    loadDocuments();
  }, [searchTerm, selectedType, selectedCategory, selectedStatus, sortBy, sortOrder]);
  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await mockDocumentData();
      const filteredData = filterDocuments(data);
      const sortedData = sortDocuments(filteredData);
      setDocuments(sortedData);
    } catch (error) {
      console.error('Failed to load documents:', error);
      showNotification('Failed to load documents', 'error');
    } finally {
      setLoading(false);
    }
  };
  const filterDocuments = (docs: Document[]) => {
    return docs.filter(doc => {
      const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           doc.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           doc.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesType = selectedType === 'all' || doc.type === selectedType;
      const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory;
      const matchesStatus = selectedStatus === 'all' || doc.status === selectedStatus;
      return matchesSearch && matchesType && matchesCategory && matchesStatus;
    });
  };
  const sortDocuments = (docs: Document[]) => {
    return [...docs].sort((a, b) => {
      let aValue: any = a[sortBy];
      let bValue: any = b[sortBy];
      if (sortBy === 'createdAt' || sortBy === 'updatedAt') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  };
  const handleFileUpload = async (files: FileList) => {
    try {
      const uploadPromises = Array.from(files).map(async (file) => {
        const newDoc: Partial<Document> = {
          title: file.name.replace(/\.[^/.]+$/, ''),
          description: `Uploaded file: ${file.name}`,
          type: 'other',
          category: 'Uncategorized',
          tags: [],
          version: '1.0.0',
          status: 'draft',
          author: 'Current User',
          authorId: 'user-123',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          requiredReading: false,
          readingProgress: 0,
          accessLevel: 'internal',
          encrypted: false,
          fileSize: file.size,
          fileType: file.type,
          downloads: 0,
          views: 0,
          complianceRequirements: [],
          acknowledgements: 0,
          totalRequiredReaders: 0,
          versions: []
        };
        // Simulate upload process
        await new Promise(resolve => setTimeout(resolve, 1000));
        return newDoc as Document;
      });
      const newDocuments = await Promise.all(uploadPromises);
      setDocuments(prev => [...newDocuments, ...prev]);
      showNotification(`${files.length} document(s) uploaded successfully`, 'success');
      setShowUploadModal(false);
    } catch (error) {
      console.error('Upload failed:', error);
      showNotification('Failed to upload documents', 'error');
    }
  };
  const handleDocumentAction = async (documentId: string, action: string) => {
    try {
      switch (action) {
        case 'download':
          showNotification('Document download started', 'success');
          break;
        case 'view':
          const doc = documents.find(d => d.id === documentId);
          if (doc) {
            setSelectedDocument(doc);
            setShowDocumentPreview(true);
            // Update view count
            setDocuments(prev => prev.map(d =>
              d.id === documentId
                ? { ...d, views: d.views + 1, lastViewed: new Date().toISOString() }
                : d
            ));
          }
          break;
        case 'delete':
          if (confirm('Are you sure you want to delete this document?')) {
            setDocuments(prev => prev.filter(d => d.id !== documentId));
            showNotification('Document deleted successfully', 'success');
          }
          break;
        case 'publish':
          setDocuments(prev => prev.map(d =>
            d.id === documentId
              ? { ...d, status: 'published', updatedAt: new Date().toISOString() }
              : d
          ));
          showNotification('Document published successfully', 'success');
          break;
        case 'archive':
          setDocuments(prev => prev.map(d =>
            d.id === documentId
              ? { ...d, status: 'archived', updatedAt: new Date().toISOString() }
              : d
          ));
          showNotification('Document archived successfully', 'success');
          break;
      }
    } catch (error) {
      console.error('Action failed:', error);
      showNotification('Action failed', 'error');
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'green';
      case 'draft': return 'gray';
      case 'review': return 'yellow';
      case 'archived': return 'orange';
      default: return 'gray';
    }
  };
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'policy': return <Shield className="w-4 h-4" />;
      case 'handbook': return <FileText className="w-4 h-4" />;
      case 'training': return <Users className="w-4 h-4" />;
      case 'form': return <FileCheck className="w-4 h-4" />;
      case 'contract': return <Lock className="w-4 h-4" />;
      case 'audit': return <AlertTriangle className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };
  const getAccessLevelColor = (level: string) => {
    switch (level) {
      case 'public': return 'green';
      case 'internal': return 'blue';
      case 'restricted': return 'yellow';
      case 'confidential': return 'red';
      default: return 'gray';
    }
  };
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  return (
    <div className={`max-w-7xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
          <p className="text-gray-600 mt-1">Manage compliance policies, handbooks, and training materials</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setShowUploadModal(true)}
            icon={<Upload className="w-4 h-4" />}
          >
            Upload Document
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            icon={<Filter className="w-4 h-4" />}
          >
            Filters
          </Button>
        </div>
      </div>
      {/* Search and Filters */}
      <Card className="mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents, tags, or descriptions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          {/* Quick Filters */}
          <div className="flex gap-3">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="policy">Policies</option>
              <option value="handbook">Handbooks</option>
              <option value="training">Training</option>
              <option value="form">Forms</option>
              <option value="contract">Contracts</option>
              <option value="audit">Audit</option>
              <option value="other">Other</option>
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
              <option value="review">In Review</option>
              <option value="archived">Archived</option>
            </select>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field as any);
                setSortOrder(order as any);
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="updatedAt-desc">Recently Updated</option>
              <option value="updatedAt-asc">Oldest Updated</option>
              <option value="createdAt-desc">Recently Created</option>
              <option value="createdAt-asc">Oldest Created</option>
              <option value="title-asc">Title A-Z</option>
              <option value="title-desc">Title Z-A</option>
              <option value="views-desc">Most Viewed</option>
              <option value="downloads-desc">Most Downloaded</option>
            </select>
          </div>
        </div>
        {/* Advanced Filters */}
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
                  <option value="HR">Human Resources</option>
                  <option value="Safety">Workplace Safety</option>
                  <option value="Privacy">Data Privacy</option>
                  <option value="Ethics">Code of Ethics</option>
                  <option value="Legal">Legal & Compliance</option>
                  <option value="IT">Information Technology</option>
                  <option value="Finance">Finance & Accounting</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </Card>
      {/* Document Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          value={documents.length}
          icon={<FileText className="w-5 h-5" />}
          color="blue"
        />
        <StatCard
          value={documents.filter(d => d.status === 'published').length}
          icon={<CheckCircle className="w-5 h-5" />}
          color="green"
        />
        <StatCard
          value={documents.filter(d => d.requiredReading).length}
          icon={<Bookmark className="w-5 h-5" />}
          color="yellow"
        />
        <StatCard
          value={documents.filter(d => d.encrypted).length}
          icon={<Lock className="w-5 h-5" />}
          color="red"
        />
      </div>
      {/* Documents Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {documents.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            onAction={handleDocumentAction}
            getStatusColor={getStatusColor}
            getTypeIcon={getTypeIcon}
            getAccessLevelColor={getAccessLevelColor}
            formatFileSize={formatFileSize}
          />
        ))}
      </div>
      {/* Upload Modal */}
      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onUpload={handleFileUpload}
        />
      )}
      {/* Document Preview Modal */}
      {showDocumentPreview && selectedDocument && (
        <DocumentPreviewModal
          document={selectedDocument}
          onClose={() => setShowDocumentPreview(false)}
          formatFileSize={formatFileSize}
        />
      )}
    </div>
  );
};
// Document Card Component
interface DocumentCardProps {
  document: Document;
  onAction: (id: string, action: string) => void;
  getStatusColor: (status: string) => string;
  getTypeIcon: (type: string) => React.ReactNode;
  getAccessLevelColor: (level: string) => string;
  formatFileSize: (bytes: number) => string;
}
const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onAction,
  getStatusColor,
  getTypeIcon,
  getAccessLevelColor,
  formatFileSize
}) => {
  const [showActions, setShowActions] = useState(false);
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${
              document.requiredReading ? 'bg-yellow-100' : 'bg-gray-100'
            }`}>
              {document.requiredReading ? (
                <BookmarkCheck className="w-5 h-5 text-yellow-600" />
              ) : (
                getTypeIcon(document.type)
              )}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 line-clamp-2">{document.title}</h3>
              <p className="text-sm text-gray-500 line-clamp-1">{document.category}</p>
            </div>
          </div>
          <div className="relative">
            <Button
              variant="ghost"
              size="small"
              onClick={() => setShowActions(!showActions)}
              icon={<MoreHorizontal className="w-4 h-4" />}
            />
            {showActions && (
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                <button
                  onClick={() => { onAction(document.id, 'view'); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                >
                  <Eye className="w-4 h-4" />
                  <span>View</span>
                </button>
                <button
                  onClick={() => { onAction(document.id, 'download'); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </button>
                {document.status === 'draft' && (
                  <button
                    onClick={() => { onAction(document.id, 'publish'); setShowActions(false); }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Publish</span>
                  </button>
                )}
                {document.status === 'published' && (
                  <button
                    onClick={() => { onAction(document.id, 'archive'); setShowActions(false); }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <Archive className="w-4 h-4" />
                    <span>Archive</span>
                  </button>
                )}
                <button
                  onClick={() => { onAction(document.id, 'delete'); setShowActions(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            )}
          </div>
        </div>
        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{document.description}</p>
        {/* Tags */}
        {document.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {document.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
              >
                {tag}
              </span>
            ))}
            {document.tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-50 text-gray-500 text-xs rounded-full">
                +{document.tags.length - 3}
              </span>
            )}
          </div>
        )}
        {/* Status and Access Level */}
        <div className="flex items-center justify-between mb-4">
          <Badge color={getStatusColor(document.status)} size="sm">
            {document.status.charAt(0).toUpperCase() + document.status.slice(1)}
          </Badge>
          <div className="flex items-center space-x-2">
            {document.encrypted && (
              <Lock className="w-4 h-4 text-red-500"  />
            )}
            <Badge color={getAccessLevelColor(document.accessLevel)} size="sm" variant="outline">
              {document.accessLevel}
            </Badge>
          </div>
        </div>
        {/* Reading Progress */}
        {document.requiredReading && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Reading Progress</span>
              <span className="font-medium">{document.readingProgress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  document.readingProgress >= 100 ? 'bg-green-500' :
                  document.readingProgress >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${document.readingProgress}%` }}
              />
            </div>
          </div>
        )}
        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
          <div className="flex items-center space-x-4">
            <span>v{document.version}</span>
            <span>{formatFileSize(document.fileSize)}</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Eye className="w-3 h-3" />
              <span>{document.views}</span>
            </span>
            <span className="flex items-center space-x-1">
              <Download className="w-3 h-3" />
              <span>{document.downloads}</span>
            </span>
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
// Upload Modal Component
interface UploadModalProps {
  onClose: () => void;
  onUpload: (files: FileList) => Promise<void>;
}
const UploadModal: React.FC<UploadModalProps> = ({ onClose, onUpload }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };
  const handleFiles = async (files: FileList) => {
    setUploading(true);
    try {
      await onUpload(files);
      onClose();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Upload Documents</h2>
            <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
          </div>
        </div>
        <div className="p-6">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-2">
              Drop files here or click to browse
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Supports PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, and image files
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
              className="hidden"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              loading={uploading}
            >
              Select Files
            </Button>
          </div>
          <div className="mt-6 text-sm text-gray-600">
            <h4 className="font-medium mb-2">Upload Guidelines:</h4>
            <ul className="space-y-1">
              <li>• Maximum file size: 50MB per file</li>
              <li>• Supported formats: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX</li>
              <li>• Images: JPG, PNG, GIF (max 10MB)</li>
              <li>• Sensitive documents will be encrypted automatically</li>
            </ul>
          </div>
        </div>
        <div className="p-6 border-t border-gray-200">
          <div className="flex justify-end space-x-3">
            <Button variant="outline" onClick={onClose} disabled={uploading}>
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
// Document Preview Modal Component
interface DocumentPreviewModalProps {
  document: Document;
  onClose: () => void;
  formatFileSize: (bytes: number) => string;
}
const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  document,
  onClose,
  formatFileSize
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{document.title}</h2>
              <p className="text-sm text-gray-500">{document.category} • Version {document.version}</p>
            </div>
            <Button variant="ghost" size="small" onClick={onClose} icon={<X className="w-4 h-4" />} />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Document Info */}
              <Card>
                <h3 className="font-semibold text-gray-900 mb-4">Document Information</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-600">Description:</span>
                    <p className="text-sm text-gray-900">{document.description}</p>
                  </div>
                  {document.tags.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-600">Tags:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {document.tags.map((tag, index) => (
                          <span key={index} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {document.complianceRequirements.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-600">Compliance Requirements:</span>
                      <ul className="mt-1 space-y-1">
                        {document.complianceRequirements.map((req, index) => (
                          <li key={index} className="text-sm text-gray-900 flex items-center">
                            <CheckCircle className="w-3 h-3 text-green-500 mr-2" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Card>
              {/* Version History */}
              {document.versions.length > 0 && (
                <Card>
                  <h3 className="font-semibold text-gray-900 mb-4">Version History</h3>
                  <div className="space-y-3">
                    {document.versions.map((version, index) => (
                      <div key={index} className="border-l-2 border-blue-200 pl-4 py-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{version.version}</span>
                          <span className="text-xs text-gray-500">
                            {new Date(version.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{version.author}</p>
                        <p className="text-sm text-gray-900">{version.changes}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
            {/* Sidebar */}
            <div className="space-y-6">
              {/* Quick Actions */}
              <Card>
                <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-2">
                  <Button className="w-full" icon={<Download className="w-4 h-4" />}>
                    Download
                  </Button>
                  <Button variant="outline" className="w-full" icon={<Share className="w-4 h-4" />}>
                    Share
                  </Button>
                  <Button variant="outline" className="w-full" icon={<Copy className="w-4 h-4" />}>
                    Duplicate
                  </Button>
                </div>
              </Card>
              {/* Document Stats */}
              <Card>
                <h3 className="font-semibold text-gray-900 mb-4">Statistics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">File Size:</span>
                    <span className="text-sm font-medium">{formatFileSize(document.fileSize)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Type:</span>
                    <span className="text-sm font-medium">{document.fileType}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Views:</span>
                    <span className="text-sm font-medium">{document.views}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Downloads:</span>
                    <span className="text-sm font-medium">{document.downloads}</span>
                  </div>
                  {document.requiredReading && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Acknowledgements:</span>
                        <span className="text-sm font-medium">
                          {document.acknowledgements}/{document.totalRequiredReaders}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Completion:</span>
                        <span className="text-sm font-medium">
                          {document.readingProgress.toFixed(1)}%
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </Card>
              {/* Access Info */}
              <Card>
                <h3 className="font-semibold text-gray-900 mb-4">Access Information</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Status:</span>
                    <Badge color={document.status === 'published' ? 'green' : 'gray'} size="sm">
                      {document.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Access Level:</span>
                    <Badge color="blue" size="sm" variant="outline">
                      {document.accessLevel}
                    </Badge>
                  </div>
                  {document.encrypted && (
                    <div className="flex items-center text-sm text-green-600">
                      <Lock className="w-4 h-4 mr-2" />
                      Encrypted
                    </div>
                  )}
                  <div className="pt-2 border-t border-gray-100">
                    <div className="text-xs text-gray-500">
                      <p>Created: {new Date(document.createdAt).toLocaleDateString()}</p>
                      <p>Updated: {new Date(document.updatedAt).toLocaleDateString()}</p>
                      {document.lastViewed && (
                        <p>Last viewed: {new Date(document.lastViewed).toLocaleDateString()}</p>
                      )}
                      {document.expiresAt && (
                        <p className="text-orange-600">
                          Expires: {new Date(document.expiresAt).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
// Mock data generator
const mockDocumentData = async (): Promise<Document[]> => {
  return [
    {
      id: '1',
      title: 'Employee Handbook 2024',
      description: 'Comprehensive employee handbook covering all company policies, procedures, and expectations for the 2024 fiscal year.',
      type: 'handbook',
      category: 'HR',
      tags: ['handbook', 'policies', 'onboarding'],
      version: '2.1.0',
      status: 'published',
      author: 'Sarah Johnson',
      authorId: 'user-1',
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-02-01T14:30:00Z',
      requiredReading: true,
      readingProgress: 78.5,
      accessLevel: 'internal',
      encrypted: false,
      fileSize: 2048576,
      fileType: 'application/pdf',
      downloads: 156,
      views: 342,
      lastViewed: '2024-03-10T09:15:00Z',
      complianceRequirements: ['State Labor Law Compliance', 'OSHA Requirements'],
      acknowledgements: 234,
      totalRequiredReaders: 300,
      versions: [
        { version: '2.0.0', createdAt: '2023-12-01T10:00:00Z', author: 'HR Team', changes: 'Updated remote work policy' },
        { version: '2.1.0', createdAt: '2024-02-01T14:30:00Z', author: 'Sarah Johnson', changes: 'Added new benefits section' }
      ]
    },
    {
      id: '2',
      title: 'Anti-Harassment Policy',
      description: 'Zero-tolerance policy against harassment, discrimination, and retaliation with detailed reporting procedures.',
      type: 'policy',
      category: 'HR',
      tags: ['harassment', 'discrimination', 'compliance'],
      version: '1.5.0',
      status: 'published',
      author: 'Legal Team',
      authorId: 'user-2',
      createdAt: '2024-01-10T09:00:00Z',
      updatedAt: '2024-01-25T16:20:00Z',
      requiredReading: true,
      readingProgress: 95.2,
      accessLevel: 'internal',
      encrypted: false,
      fileSize: 1048576,
      fileType: 'application/pdf',
      downloads: 89,
      views: 267,
      lastViewed: '2024-03-12T11:30:00Z',
      complianceRequirements: ['EEOC Compliance', 'State Harassment Laws'],
      acknowledgements: 298,
      totalRequiredReaders: 300,
      versions: [
        { version: '1.0.0', createdAt: '2023-06-01T10:00:00Z', author: 'Legal Team', changes: 'Initial policy creation' },
        { version: '1.5.0', createdAt: '2024-01-25T16:20:00Z', author: 'Legal Team', changes: 'Updated reporting procedures' }
      ]
    },
    {
      id: '3',
      title: 'Data Privacy and Security Policy',
      description: 'Comprehensive data protection policy covering GDPR compliance, data encryption, and security protocols.',
      type: 'policy',
      category: 'Privacy',
      tags: ['GDPR', 'data-privacy', 'security'],
      version: '3.0.0',
      status: 'published',
      author: 'IT Security Team',
      authorId: 'user-3',
      createdAt: '2024-02-01T10:00:00Z',
      updatedAt: '2024-02-01T10:00:00Z',
      requiredReading: true,
      readingProgress: 62.3,
      accessLevel: 'internal',
      encrypted: true,
      fileSize: 3145728,
      fileType: 'application/pdf',
      downloads: 67,
      views: 198,
      lastViewed: '2024-03-11T14:45:00Z',
      complianceRequirements: ['GDPR Article 30', 'CCPA Compliance', 'HIPAA'],
      acknowledgements: 187,
      totalRequiredReaders: 300,
      versions: [
        { version: '3.0.0', createdAt: '2024-02-01T10:00:00Z', author: 'IT Security Team', changes: 'Complete GDPR revision' }
      ]
    },
    {
      id: '4',
      title: 'Workplace Safety Guidelines',
      description: 'OSHA-compliant safety procedures, emergency protocols, and workplace hazard prevention guidelines.',
      type: 'policy',
      category: 'Safety',
      tags: ['OSHA', 'safety', 'emergency'],
      version: '4.2.0',
      status: 'published',
      author: 'Safety Officer',
      authorId: 'user-4',
      createdAt: '2024-01-20T08:00:00Z',
      updatedAt: '2024-03-05T11:15:00Z',
      requiredReading: true,
      readingProgress: 87.1,
      accessLevel: 'public',
      encrypted: false,
      fileSize: 2097152,
      fileType: 'application/pdf',
      downloads: 143,
      views: 412,
      lastViewed: '2024-03-12T08:30:00Z',
      complianceRequirements: ['OSHA 29 CFR 1910', 'State Safety Regulations'],
      acknowledgements: 276,
      totalRequiredReaders: 300,
      versions: [
        { version: '4.0.0', createdAt: '2023-09-01T10:00:00Z', author: 'Safety Officer', changes: 'Updated OSHA standards' },
        { version: '4.1.0', createdAt: '2024-01-20T08:00:00Z', author: 'Safety Officer', changes: 'Added COVID-19 protocols' },
        { version: '4.2.0', createdAt: '2024-03-05T11:15:00Z', author: 'Safety Officer', changes: 'Updated emergency procedures' }
      ]
    },
    {
      id: '5',
      title: 'Code of Business Conduct',
      description: 'Ethical guidelines for business operations, conflicts of interest, and professional conduct standards.',
      type: 'policy',
      category: 'Ethics',
      tags: ['ethics', 'conduct', 'compliance'],
      version: '2.3.0',
      status: 'review',
      author: 'Compliance Officer',
      authorId: 'user-5',
      createdAt: '2024-02-15T09:30:00Z',
      updatedAt: '2024-03-01T13:45:00Z',
      requiredReading: true,
      readingProgress: 45.7,
      accessLevel: 'internal',
      encrypted: false,
      fileSize: 1572864,
      fileType: 'application/pdf',
      downloads: 34,
      views: 89,
      lastViewed: '2024-03-10T16:20:00Z',
      complianceRequirements: ['Sarbanes-Oxley Act', 'SEC Regulations'],
      acknowledgements: 134,
      totalRequiredReaders: 300,
      versions: [
        { version: '2.2.0', createdAt: '2023-11-01T10:00:00Z', author: 'Compliance Officer', changes: 'Updated conflict of interest policy' },
        { version: '2.3.0', createdAt: '2024-03-01T13:45:00Z', author: 'Compliance Officer', changes: 'Added anti-corruption provisions' }
      ]
    },
    {
      id: '6',
      title: 'Remote Work Policy',
      description: 'Guidelines for remote work arrangements, home office requirements, and virtual collaboration protocols.',
      type: 'policy',
      category: 'HR',
      tags: ['remote-work', 'telecommuting', 'hybrid'],
      version: '1.8.0',
      status: 'draft',
      author: 'HR Team',
      authorId: 'user-1',
      createdAt: '2024-03-01T10:00:00Z',
      updatedAt: '2024-03-10T15:30:00Z',
      requiredReading: false,
      readingProgress: 0,
      accessLevel: 'internal',
      encrypted: false,
      fileSize: 786432,
      fileType: 'application/pdf',
      downloads: 0,
      views: 12,
      lastViewed: '2024-03-10T15:30:00Z',
      complianceRequirements: [],
      acknowledgements: 0,
      totalRequiredReaders: 150,
      versions: [
        { version: '1.8.0', createdAt: '2024-03-10T15:30:00Z', author: 'HR Team', changes: 'Updated hybrid work guidelines' }
      ]
    }
  ];
};