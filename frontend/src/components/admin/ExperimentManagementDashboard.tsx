// frontend/src/components/admin/ExperimentManagementDashboard.tsx
/**
 * Experiment Management Dashboard
 *
 * Admin dashboard for managing A/B testing experiments and viewing results.
 * Provides experiment status, statistical significance, and variant performance.
 */
import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';

// ========================================================================
// Types
// ========================================================================

interface Experiment {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'running' | 'paused' | 'completed';
  start_date: string;
  end_date: string | null;
  config: {
    hypothesis?: string;
    variants?: string[];
    traffic_split?: Record<string, number>;
    target_metrics?: string[];
  };
  created_at: string;
  updated_at: string;
}

interface ExperimentVariant {
  id: string;
  experiment_id: string;
  name: string;
  traffic_split: number;
  is_control: boolean;
}

interface ExperimentResults {
  experiment_id: string;
  total_participants: number;
  total_conversions: number;
  overall_conversion_rate: number;
  variants: {
    name: string;
    participants: number;
    conversions: number;
    conversion_rate: number;
    is_control: boolean;
    is_winner: boolean;
    is_significant: boolean;
    confidence_interval?: [number, number];
    uplift?: number;
  }[];
  statistical_test: {
    test_type: string;
    p_value: number;
    is_significant: boolean;
    confidence_level: number;
  };
}

interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  status: string;
  theme: string;
  priority: string;
  rice_score: number | null;
  vote_count: number;
  created_at: string;
}

// ========================================================================
// Components
// ========================================================================

export const ExperimentManagementDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'experiments' | 'results' | 'feature-requests'>('experiments');
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [featureRequests, setFeatureRequests] = useState<FeatureRequest[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);
  const [results, setResults] = useState<ExperimentResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExperiments();
    loadFeatureRequests();
  }, []);

  const loadExperiments = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/ab/experiments');
      setExperiments((response.data as any).experiments || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadFeatureRequests = async () => {
    try {
      const response = await apiClient.get('/feature-requests');
      setFeatureRequests((response.data as any).requests || []);
    } catch (err) {
      console.error('Failed to load feature requests:', err);
    }
  };

  const loadResults = async (experimentId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/ab/experiments/${experimentId}/results`);
      setResults(response.data as ExperimentResults);
      setSelectedExperiment(experimentId);
    } catch (err) {
      console.error('Failed to load results:', err);
    }
  };

  const updateExperimentStatus = async (experimentId: string, status: string) => {
    try {
      await apiClient.put(`/api/v1/ab/experiments/${experimentId}`, { status });
      await loadExperiments();
    } catch (err) {
      console.error('Failed to update experiment:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-50';
      case 'completed': return 'text-blue-600 bg-blue-50';
      case 'paused': return 'text-yellow-600 bg-yellow-50';
      case 'draft': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getRiceColor = (score: number | null) => {
    if (!score) return 'text-gray-500';
    if (score >= 1.0) return 'text-green-600 font-bold';
    if (score >= 0.5) return 'text-blue-600 font-semibold';
    return 'text-yellow-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Product Operations Dashboard</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage A/B tests and feature requests
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'experiments', label: 'A/B Experiments', count: experiments.length },
            { key: 'results', label: 'Experiment Results', count: 0 },
            { key: 'feature-requests', label: 'Feature Requests', count: featureRequests.length }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`${
                activeTab === tab.key
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'experiments' && (
        <ExperimentsList
          experiments={experiments}
          onSelectExperiment={loadResults}
          onUpdateStatus={updateExperimentStatus}
          getStatusColor={getStatusColor}
        />
      )}

      {activeTab === 'results' && (
        <ExperimentResultsView
          experiments={experiments}
          selectedExperiment={selectedExperiment}
          results={results}
          onSelectExperiment={loadResults}
          getStatusColor={getStatusColor}
        />
      )}

      {activeTab === 'feature-requests' && (
        <FeatureRequestsList
          featureRequests={featureRequests}
          getRiceColor={getRiceColor}
          onRefresh={loadFeatureRequests}
        />
      )}
    </div>
  );
};

// ========================================================================
// Sub-Components
// ========================================================================

interface ExperimentsListProps {
  experiments: Experiment[];
  onSelectExperiment: (id: string) => void;
  onUpdateStatus: (id: string, status: string) => void;
  getStatusColor: (status: string) => string;
}

const ExperimentsList: React.FC<ExperimentsListProps> = ({
  experiments,
  onSelectExperiment,
  onUpdateStatus,
  getStatusColor
}) => {
  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <ul className="divide-y divide-gray-200">
        {experiments.map((experiment) => (
          <li key={experiment.id} className="p-6 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {experiment.name}
                  </h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(experiment.status)}`}>
                    {experiment.status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{experiment.description}</p>
                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                  <span>Started: {new Date(experiment.start_date).toLocaleDateString()}</span>
                  {experiment.end_date && (
                    <span>Ends: {new Date(experiment.end_date).toLocaleDateString()}</span>
                  )}
                  {experiment.config.hypothesis && (
                    <span className="text-indigo-600">
                      Hypothesis: {experiment.config.hypothesis}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => onSelectExperiment(experiment.id)}
                  className="px-3 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-900 transition-colors"
                >
                  View Results
                </button>
                {experiment.status === 'running' && (
                  <button
                    onClick={() => onUpdateStatus(experiment.id, 'paused')}
                    className="px-3 py-2 text-sm font-medium text-yellow-600 hover:text-yellow-900 transition-colors"
                  >
                    Pause
                  </button>
                )}
                {experiment.status === 'paused' && (
                  <button
                    onClick={() => onUpdateStatus(experiment.id, 'running')}
                    className="px-3 py-2 text-sm font-medium text-green-600 hover:text-green-900 transition-colors"
                  >
                    Resume
                  </button>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
      {experiments.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No experiments found. Create your first A/B test!</p>
        </div>
      )}
    </div>
  );
};

interface ExperimentResultsViewProps {
  experiments: Experiment[];
  selectedExperiment: string | null;
  results: ExperimentResults | null;
  onSelectExperiment: (id: string) => void;
  getStatusColor: (status: string) => string;
}

const ExperimentResultsView: React.FC<ExperimentResultsViewProps> = ({
  experiments,
  selectedExperiment,
  results,
  onSelectExperiment,
  getStatusColor
}) => {
  const runningExperiments = experiments.filter(e => e.status === 'running' || e.status === 'completed');

  return (
    <div className="space-y-6">
      {/* Experiment Selector */}
      <div className="bg-white shadow rounded-lg p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Experiment
        </label>
        <select
          value={selectedExperiment || ''}
          onChange={(e) => e.target.value && onSelectExperiment(e.target.value)}
          className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md border"
        >
          <option value="">Choose an experiment...</option>
          {runningExperiments.map((exp) => (
            <option key={exp.id} value={exp.id}>
              {exp.name} ({exp.status})
            </option>
          ))}
        </select>
      </div>

      {/* Results Display */}
      {results && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Experiment Results</h3>
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="bg-indigo-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Participants</p>
                <p className="text-2xl font-bold text-indigo-600 mt-1">
                  {results.total_participants.toLocaleString()}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Conversions</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {results.total_conversions.toLocaleString()}
                </p>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {(results.overall_conversion_rate * 100).toFixed(2)}%
                </p>
              </div>
            </div>
          </div>

          {/* Statistical Significance */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">
                  Statistical Test: {results.statistical_test.test_type}
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  P-value: {results.statistical_test.p_value.toFixed(4)}
                </p>
              </div>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                results.statistical_test.is_significant
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {results.statistical_test.is_significant ? 'Significant' : 'Not Significant'}
              </span>
            </div>
          </div>

          {/* Variant Performance */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Variant Performance</h4>
            <div className="space-y-3">
              {results.variants.map((variant) => (
                <div key={variant.name} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        variant.is_control ? 'bg-gray-400' : 'bg-indigo-600'
                      }`} />
                      <span className="font-medium text-gray-900">
                        {variant.name}
                        {variant.is_control && ' (Control)'}
                      </span>
                      {variant.is_winner && (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          Winner
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-gray-900">
                        {(variant.conversion_rate * 100).toFixed(2)}%
                      </p>
                      {variant.uplift !== undefined && variant.uplift !== 0 && (
                        <p className={`text-sm font-medium ${
                          variant.uplift > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {variant.uplift > 0 ? '+' : ''}{variant.uplift.toFixed(2)}% uplift
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">Participants:</span> {variant.participants.toLocaleString()}
                    </div>
                    <div>
                      <span className="font-medium">Conversions:</span> {variant.conversions.toLocaleString()}
                    </div>
                  </div>
                  {variant.confidence_interval && (
                    <div className="mt-2 text-xs text-gray-500">
                      95% CI: [{(variant.confidence_interval[0] * 100).toFixed(2)}%, {(variant.confidence_interval[1] * 100).toFixed(2)}%]
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {!results && selectedExperiment && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="text-gray-500 mt-4">Loading results...</p>
        </div>
      )}

      {!results && !selectedExperiment && (
        <div className="text-center py-12">
          <p className="text-gray-500">Select an experiment to view results</p>
        </div>
      )}
    </div>
  );
};

interface FeatureRequestsListProps {
  featureRequests: FeatureRequest[];
  getRiceColor: (score: number | null) => string;
  onRefresh: () => void;
}

const FeatureRequestsList: React.FC<FeatureRequestsListProps> = ({
  featureRequests,
  getRiceColor,
  onRefresh
}) => {
  const [sortBy, setSortBy] = useState<'rice' | 'votes' | 'date'>('rice');

  const sortedRequests = [...featureRequests].sort((a, b) => {
    switch (sortBy) {
      case 'rice':
        return (b.rice_score || 0) - (a.rice_score || 0);
      case 'votes':
        return b.vote_count - a.vote_count;
      case 'date':
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      default:
        return 0;
    }
  });

  return (
    <div className="space-y-4">
      {/* Sort Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-700">Sort by:</span>
          {[
            { key: 'rice', label: 'RICE Score' },
            { key: 'votes', label: 'Votes' },
            { key: 'date', label: 'Date' }
          ].map((sort) => (
            <button
              key={sort.key}
              onClick={() => setSortBy(sort.key as any)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                sortBy === sort.key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {sort.label}
            </button>
          ))}
        </div>
        <button
          onClick={onRefresh}
          className="px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-900"
        >
          Refresh
        </button>
      </div>

      {/* Feature Requests List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {sortedRequests.map((request) => (
            <li key={request.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {request.title}
                    </h3>
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                      {request.priority}
                    </span>
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {request.theme}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{request.description}</p>
                  <div className="mt-3 flex items-center space-x-6 text-sm">
                    <div className="flex items-center space-x-1">
                      <span className="text-gray-600">RICE Score:</span>
                      <span className={`text-lg ${getRiceColor(request.rice_score)}`}>
                        {request.rice_score?.toFixed(2) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-gray-600">Votes:</span>
                      <span className="font-semibold text-indigo-600">
                        {request.vote_count}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {featureRequests.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No feature requests found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExperimentManagementDashboard;
