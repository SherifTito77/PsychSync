/**
 * Team Analytics Dashboard Component
 * Displays aggregate team email analytics and member performance
 */

import React, { useState, useEffect } from 'react';
import {
  UsersIcon,
  ChartBarIcon,
  TrophyIcon,
  ClockIcon,
  FaceSmileIcon,
  ArrowTrendingUpIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';

interface TeamMember {
  id: string;
  name: string;
  email: string;
  productivity_score: number;
  total_emails: number;
  emails_this_period: number;
  avg_response_time: number;
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
  };
  stress_level: string;
  categories: {
    security: number;
    financial: number;
    professional: number;
    social: number;
  };
}

interface TeamMetrics {
  total_emails: number;
  emails_this_period: number;
  daily_average_per_member: number;
  category_breakdown: Record<string, number>;
  average_response_time_minutes: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  stress_distribution: Record<string, number>;
  average_productivity_score: number;
  top_performers: Array<{
    name: string;
    score: number;
  }>;
}

interface TeamData {
  team_id: number;
  team_name: string;
  period_days: number;
  team_size: number;
  team_metrics: TeamMetrics;
  member_analytics: TeamMember[];
  insights: string[];
}

const TeamDashboard: React.FC = () => {
  console.log('🔍 TeamDashboard component rendering!');
  const [teams, setTeams] = useState<TeamData[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<TeamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'overview' | 'members' | 'comparison'>('overview');

  useEffect(() => {
    fetchTeamData();
  }, []);

  const fetchTeamData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      // TODO: Replace with actual API endpoint
      // const response = await fetch('/api/v1/team-analytics/my-teams', {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      // const data = await response.json();
      // setTeams(data.user_teams);

      // Mock data
      const mockTeam: TeamData = {
        team_id: 1,
        team_name: 'Engineering Team',
        period_days: 30,
        team_size: 5,
        team_metrics: {
          total_emails: 6250,
          emails_this_period: 435,
          daily_average_per_member: 38.5,
          category_breakdown: {
            security: 175,
            financial: 100,
            professional: 85,
            social: 50,
            promotional: 25,
          },
          average_response_time_minutes: 42.3,
          sentiment_distribution: {
            positive: 65,
            neutral: 25,
            negative: 10,
          },
          stress_distribution: {
            low: 3,
            moderate: 2,
            high: 0,
          },
          average_productivity_score: 76.8,
          top_performers: [
            { name: 'Jane Smith', score: 92 },
            { name: 'John Doe', score: 85 },
            { name: 'Bob Johnson', score: 78 },
          ],
        },
        member_analytics: [
          {
            id: '1',
            name: 'Jane Smith',
            email: 'jane@example.com',
            productivity_score: 92,
            total_emails: 1450,
            emails_this_period: 102,
            avg_response_time: 28,
            sentiment: { positive: 75, neutral: 20, negative: 5 },
            stress_level: 'low',
            categories: { security: 45, financial: 30, professional: 20, social: 7 },
          },
          {
            id: '2',
            name: 'John Doe',
            email: 'john@example.com',
            productivity_score: 85,
            total_emails: 1250,
            emails_this_period: 87,
            avg_response_time: 35,
            sentiment: { positive: 65, neutral: 25, negative: 10 },
            stress_level: 'low',
            categories: { security: 35, financial: 25, professional: 18, social: 9 },
          },
          {
            id: '3',
            name: 'Bob Johnson',
            email: 'bob@example.com',
            productivity_score: 78,
            total_emails: 1100,
            emails_this_period: 76,
            avg_response_time: 42,
            sentiment: { positive: 60, neutral: 30, negative: 10 },
            stress_level: 'moderate',
            categories: { security: 40, financial: 20, professional: 15, social: 10 },
          },
          {
            id: '4',
            name: 'Alice Brown',
            email: 'alice@example.com',
            productivity_score: 72,
            total_emails: 1350,
            emails_this_period: 95,
            avg_response_time: 55,
            sentiment: { positive: 55, neutral: 35, negative: 10 },
            stress_level: 'moderate',
            categories: { security: 30, financial: 15, professional: 20, social: 15 },
          },
          {
            id: '5',
            name: 'Charlie Wilson',
            email: 'charlie@example.com',
            productivity_score: 57,
            total_emails: 1100,
            emails_this_period: 75,
            avg_response_time: 52,
            sentiment: { positive: 50, neutral: 30, negative: 20 },
            stress_level: 'moderate',
            categories: { security: 25, financial: 10, professional: 12, social: 9 },
          },
        ],
        insights: [
          'Team productivity is good - room for improvement',
          '2 team members show moderate stress levels',
          'Team maintains highly positive communication tone',
          'Average response time is under 1 hour - good efficiency',
        ],
      };

      setTeams([mockTeam]);
      setSelectedTeam(mockTeam);
    } catch (error) {
      console.error('Failed to fetch team data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getProductivityColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getStressColor = (level: string): string => {
    switch (level) {
      case 'low':
        return 'text-green-600';
      case 'moderate':
        return 'text-yellow-600';
      case 'high':
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!selectedTeam) {
    return (
      <div className="p-6 text-center text-gray-500">
        No team data available
      </div>
    );
  }

  const metrics = selectedTeam.team_metrics;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center">
          <UsersIcon className="w-7 h-7 mr-2 text-blue-500" />
          {selectedTeam.team_name}
        </h2>
        <p className="text-gray-600">
          Team analytics for the last {selectedTeam.period_days} days • {selectedTeam.team_size}{' '}
          members
        </p>
      </div>

      {/* View Toggle */}
      <div className="mb-6 flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setView('overview')}
          className={`px-4 py-2 font-medium ${
            view === 'overview'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setView('members')}
          className={`px-4 py-2 font-medium ${
            view === 'members'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Members
        </button>
        <button
          onClick={() => setView('comparison')}
          className={`px-4 py-2 font-medium ${
            view === 'comparison'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Comparison
        </button>
      </div>

      {view === 'overview' && (
        <>
          {/* Top Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Avg Productivity</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.average_productivity_score}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">out of 100</p>
                </div>
                <div className="p-3 bg-green-100 rounded-lg">
                  <TrophyIcon className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Emails This Period</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.emails_this_period}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">last 30 days</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-lg">
                  <ChartBarIcon className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Avg Response Time</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {metrics.average_response_time_minutes.toFixed(1)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">minutes</p>
                </div>
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <ClockIcon className="w-6 h-6 text-yellow-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">Sentiment</p>
                  <p className="text-3xl font-bold text-green-600">
                    {metrics.sentiment_distribution.positive}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">positive</p>
                </div>
                <div className="p-3 bg-green-100 rounded-lg">
                  <FaceSmileIcon className="w-6 h-6 text-green-600" />
                </div>
              </div>
            </div>
          </div>

          {/* Top Performers */}
          <div className="bg-white rounded-lg shadow p-6 mb-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrophyIcon className="w-5 h-5 mr-2 text-yellow-500" />
              Top Performers
            </h3>
            <div className="space-y-3">
              {metrics.top_performers.map((performer, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                        idx === 0
                          ? 'bg-yellow-100 text-yellow-700'
                          : idx === 1
                          ? 'bg-gray-200 text-gray-700'
                          : 'bg-orange-100 text-orange-700'
                      }`}
                    >
                      {idx + 1}
                    </div>
                    <span className="font-medium text-gray-900">{performer.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-bold text-gray-900">
                      {performer.score}
                    </span>
                    <span className="text-sm text-gray-500 ml-1">/ 100</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="bg-white rounded-lg shadow p-6 mb-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Categories</h3>
            <div className="space-y-3">
              {Object.entries(metrics.category_breakdown).map(([category, count]) => {
                const total = Object.values(metrics.category_breakdown).reduce((a, b) => a + b, 0);
                const percentage = ((count / total) * 100).toFixed(1);
                const colors = {
                  security: 'bg-red-500',
                  financial: 'bg-green-500',
                  professional: 'bg-blue-500',
                  social: 'bg-purple-500',
                  promotional: 'bg-yellow-500',
                  other: 'bg-gray-500',
                };
                return (
                  <div key={category}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="capitalize text-gray-700">{category}</span>
                      <span className="text-gray-500">
                        {count} ({percentage}%)
                      </span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${colors[category as keyof typeof colors] || 'bg-gray-500'}`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Insights */}
          <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h3 className="text-lg font-semibold text-blue-900 mb-3 flex items-center">
              <ArrowTrendingUpIcon className="w-5 h-5 mr-2" />
              Team Insights
            </h3>
            <ul className="space-y-2">
              {selectedTeam.insights.map((insight, idx) => (
                <li key={idx} className="flex items-start text-sm text-blue-800">
                  <span className="mr-2">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {view === 'members' && (
        <>
          {/* Members Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Member
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Productivity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Emails (Period)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Response Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sentiment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stress
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {selectedTeam.member_analytics.map((member) => (
                  <tr key={member.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{member.name}</div>
                        <div className="text-sm text-gray-500">{member.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getProductivityColor(
                          member.productivity_score
                        )}`}
                      >
                        {member.productivity_score}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {member.emails_this_period}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {member.avg_response_time} min
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2 text-sm">
                        <span className="text-green-600">{member.sentiment.positive}%</span>
                        <span className="text-gray-400">|</span>
                        <span className="text-gray-600">{member.sentiment.neutral}%</span>
                        <span className="text-gray-400">|</span>
                        <span className="text-red-600">{member.sentiment.negative}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium capitalize ${getStressColor(
                        member.stress_level
                      )}`}>
                        {member.stress_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {view === 'comparison' && (
        <>
          {/* Member Comparison Chart */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Productivity Comparison
            </h3>
            <div className="space-y-4">
              {selectedTeam.member_analytics
                .sort((a, b) => b.productivity_score - a.productivity_score)
                .map((member) => (
                  <div key={member.id}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">{member.name}</span>
                      <span className="text-sm text-gray-500">
                        {member.productivity_score}/100
                      </span>
                    </div>
                    <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          member.productivity_score >= 80
                            ? 'bg-green-500'
                            : member.productivity_score >= 60
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${member.productivity_score}%` }}
                      />
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Stats Comparison */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Response Time Leaders
              </h3>
              <div className="space-y-3">
                {selectedTeam.member_analytics
                  .sort((a, b) => a.avg_response_time - b.avg_response_time)
                  .slice(0, 3)
                  .map((member, idx) => (
                    <div key={member.id} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500">#{idx + 1}</span>
                        <span className="text-sm font-medium text-gray-900">{member.name}</span>
                      </div>
                      <span className="text-sm text-gray-600">
                        {member.avg_response_time} min
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Highest Email Volume
              </h3>
              <div className="space-y-3">
                {selectedTeam.member_analytics
                  .sort((a, b) => b.total_emails - a.total_emails)
                  .slice(0, 3)
                  .map((member, idx) => (
                    <div key={member.id} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500">#{idx + 1}</span>
                        <span className="text-sm font-medium text-gray-900">{member.name}</span>
                      </div>
                      <span className="text-sm text-gray-600">
                        {member.total_emails.toLocaleString()}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TeamDashboard;
