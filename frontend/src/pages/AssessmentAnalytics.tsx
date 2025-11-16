// frontend/src/pages/AssessmentAnalytics.tsx
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  analyticsService,
 type AssessmentAnalytics,
} from '../services/analyticsService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);
const AssessmentAnalytics: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const [analytics, setAnalytics] = useState<AssessmentAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    loadAnalytics();
  }, [assessmentId]);
  const loadAnalytics = async () => {
    if (!assessmentId) return;
    setIsLoading(true);
    setError('');
    try {
      const data = await analyticsService.getAssessmentAnalytics(
        parseInt(assessmentId)
      );
      setAnalytics(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }
  if (error || !analytics) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <p className="text-sm text-red-800">{error || 'Analytics not available'}</p>
        <Link
          to={`/assessments/${assessmentId}`}
          className="mt-2 text-sm text-red-600 hover:text-red-500"
        >
          ← Back to assessment
        </Link>
      </div>
    );
  }
  // Prepare chart data
  const scoreDistributionData = {
    labels: analytics.score_distribution.map((item) => item.range),
    datasets: [
      {
        label: 'Number of Responses',
        data: analytics.score_distribution.map((item) => item.count),
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)',
          'rgba(249, 115, 22, 0.8)',
          'rgba(234, 179, 8, 0.8)',
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
        ],
      },
    ],
  };
  const completionData = {
    labels: ['Completed', 'Pending'],
    datasets: [
      {
        data: [
          analytics.total_responses,
          analytics.total_assignments - analytics.total_responses,
        ],
        backgroundColor: ['rgba(34, 197, 94, 0.8)', 'rgba(156, 163, 175, 0.8)'],
      },
    ],
  };
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          to={`/assessments/${assessmentId}`}
          className="text-sm text-gray-500 hover:text-gray-700 flex items-center mb-2"
        >
          <svg
            className="w-4 h-4 mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to assessment
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          Analytics: {analytics.assessment_title}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Detailed performance metrics and insights
        </p>
      </div>
      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Responses
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {analytics.total_responses}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Average Score
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {analytics.average_score
                      ? `${analytics.average_score.toFixed(1)}%`
                      : 'N/A'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Average Time
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {analytics.average_time
                      ? `${Math.floor(analytics.average_time / 60)}m`
                      : 'N/A'}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Completion Rate
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {analytics.completion_rate.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Distribution */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Score Distribution
          </h3>
          <Bar
            data={scoreDistributionData}
            options={{
              responsive: true,
              plugins: {
                legend: {
                  display: false,
                },
                title: {
                  display: false,
                },
              },
              scales: {
                y: {
                  beginAtZero: true,
                  ticks: {
                    stepSize: 1,
                  },
                },
              },
            }}
          />
        </div>
        {/* Completion Status */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Completion Status
          </h3>
          <div className="flex justify-center">
            <div style={{ maxWidth: '300px', maxHeight: '300px' }}>
              <Doughnut
                data={completionData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    },
                  },
                }}
              />
            </div>
          </div>
        </div>
      </div>
      {/* Recent Responses */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Recent Responses
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Response ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Submitted
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analytics.recent_responses.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-4 text-center text-sm text-gray-500">
                    No responses yet
                  </td>
                </tr>
              ) : (
                analytics.recent_responses.map((response) => (
                  <tr key={response.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      #{response.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {response.submitted_at
                        ? new Date(response.submitted_at).toLocaleString()
                        : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {response.score ? `${response.score.toFixed(1)}%` : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default AssessmentAnalytics;
