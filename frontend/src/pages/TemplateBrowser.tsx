// frontend/src/pages/TemplateBrowser.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { templateService, Template } from '../services/templateService';
import { teamService, Team } from '../services/teamService';
import LoadingSpinner from '../components/common/LoadingSpinner';
const TemplateBrowser: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [showOfficialOnly, setShowOfficialOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState<number | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const categories = [
    { value: '', label: 'All Categories' },
    { value: 'personality', label: 'Personality' },
    { value: 'cognitive', label: 'Cognitive' },
    { value: 'clinical', label: 'Clinical' },
    { value: 'behavioral', label: 'Behavioral' },
    { value: 'wellbeing', label: 'Wellbeing' },
    { value: 'custom', label: 'Custom' },
  ];
  useEffect(() => {
    loadTemplates();
    loadTeams();
  }, [selectedCategory, showOfficialOnly]);
  const loadTemplates = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await templateService.getTemplates(
        selectedCategory || undefined,
        showOfficialOnly || undefined
      );
      setTemplates(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load templates');
    } finally {
      setIsLoading(false);
    }
  };
  const loadTeams = async () => {
    try {
      const data = await teamService.getTeams(true);
      setTeams(data);
    } catch (error) {
      console.error('Failed to load teams');
    }
  };
  const handleSearch = async () => {
    if (searchQuery.length < 2) {
      loadTemplates();
      return;
    }
    setIsLoading(true);
    try {
      const data = await templateService.searchTemplates(searchQuery);
      setTemplates(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Search failed');
    } finally {
      setIsLoading(false);
    }
  };
  const handleUseTemplate = async (templateId: number) => {
    setIsCreating(templateId);
    try {
      const assessment = await templateService.createAssessmentFromTemplate(
        templateId,
        selectedTeam || undefined
      );
      navigate(`/assessments/${assessment.id}`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create assessment from template');
    } finally {
      setIsCreating(null);
    }
  };
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      personality: 'bg-purple-100 text-purple-800',
      cognitive: 'bg-blue-100 text-blue-800',
      clinical: 'bg-red-100 text-red-800',
      behavioral: 'bg-green-100 text-green-800',
      wellbeing: 'bg-yellow-100 text-yellow-800',
      custom: 'bg-gray-100 text-gray-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };
  if (isLoading && templates.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Assessment Templates</h1>
        <p className="mt-1 text-sm text-gray-500">
          Browse and use pre-built assessment templates
        </p>
      </div>
      {/* Filters and Search */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700">
              Search Templates
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                type="text"
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 min-w-0 block w-full rounded-none rounded-l-md border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Search by name or description..."
              />
              <button
                onClick={handleSearch}
                className="inline-flex items-center px-4 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 hover:bg-gray-100"
              >
                <svg
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </button>
            </div>
          </div>
          {/* Category Filter */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700">
              Category
            </label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
          {/* Official Only */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showOfficialOnly}
                onChange={(e) => setShowOfficialOnly(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-900">Official templates only</span>
            </label>
          </div>
        </div>
        {/* Team Selection */}
        {teams.length > 0 && (
          <div className="mt-4">
            <label htmlFor="team" className="block text-sm font-medium text-gray-700">
              Create assessment for team (optional)
            </label>
            <select
              id="team"
              value={selectedTeam || ''}
              onChange={(e) => setSelectedTeam(e.target.value ? parseInt(e.target.value) : null)}
              className="mt-1 block w-full md:w-1/2 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="">Personal (No team)</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}
      {/* Templates Grid */}
      {templates.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No templates found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your filters or search criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {template.name}
                      </h3>
                      {template.is_official && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                          Official
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 mb-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(
                          template.category
                        )}`}
                      >
                        {template.category}
                      </span>
                    </div>
                  </div>
                </div>
                {template.description && (
                  <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                    {template.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                  {template.author && (
                    <span className="flex items-center">
                      <svg
                        className="h-4 w-4 mr-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                        />
                      </svg>
                      {template.author}
                    </span>
                  )}
                  <span className="flex items-center">
                    <svg
                      className="h-4 w-4 mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                      />
                    </svg>
                    {template.usage_count} uses
                  </span>
                </div>
                <button
                  onClick={() => handleUseTemplate(template.id)}
                  disabled={isCreating === template.id}
                  className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center"
                >
                  {isCreating === template.id ? (
                    <>
                      <LoadingSpinner size="small" className="mr-2" />
                      Creating...
                    </>
                  ) : (
                    'Use This Template'
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default TemplateBrowser;
