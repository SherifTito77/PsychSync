// frontend/src/pages/MyResponses.tsx
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { responseService, ResponseSession } from '../services/responseService';
import LoadingSpinner from '../components/common/LoadingSpinner';
const MyResponses: React.FC = () => {
  const [responses, setResponses] = useState<ResponseSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');
  const [error, setError] = useState('');
  useEffect(() => {
    loadResponses();
  }, [filter]);
  const loadResponses = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await responseService.getMyResponses(filter || undefined);
      setResponses(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load responses');
    } finally {
      setIsLoading(false);
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  if (isLoading) {
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
        <h1 className="text-2xl font-bold text-gray-900">My Responses</h1>
        <p className="mt-1 text-sm text-gray-500">
          View and manage your assessment responses
        </p>
      </div>
      {/* Filter */}
      <div className="bg-white shadow rounded-lg p-4">
        <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700">
          Filter by Status
        </label>
        <select
          id="status-filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="mt-1 block w-full md:w-64 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        >
          <option value="">All Responses</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      {/* Error Message */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}
      {/* Responses List */}
      {responses.length === 0 ? (
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
          <h3 className="mt-2 text-sm font-medium text-gray-900">No responses</h3>
          <p className="mt-1 text-sm text-gray-500">
            You haven't completed any assessments yet.
          </p>
          <div className="mt-6">
            <Link
              to="/assessments"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              Browse Assessments
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {responses.map((response) => (
              <li key={response.id}>
                <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-indigo-600 truncate">
                          Assessment #{response.assessment_id}
                        </p>
                        <div className="ml-2 flex-shrink-0 flex">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                              response.status
                            )}`}
                          >
                            {response.status.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2 sm:flex sm:justify-between">
                        <div className="sm:flex">
                          <p className="flex items-center text-sm text-gray-500">
                            Started: {new Date(response.started_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                          <p>Progress: {response.progress_percentage.toFixed(0)}%</p>
                        </div>
                      </div>
                    </div>
                    <div className="ml-4 flex-shrink-0 flex space-x-2">
                      {response.status === 'in_progress' ? (
                        <Link
                          to={`/assessments/${response.assessment_id}/take`}
                          className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
                        >
                          Continue
                        </Link>
                      ) : (
                        <Link
                          to={`/responses/${response.id}/results`}
                          className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
                        >
                          View Results
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
export default MyResponses;