/**
 * File Path: frontend/src/components/scoring_dashboard.tsx
 * Assessment Scoring Dashboard Component
 * Displays assessment scores, analytics, and insights
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Download, RefreshCw, TrendingUp, TrendingDown, Activity } from 'lucide-react';
// =================================================================
// TYPES
// =================================================================
interface AssessmentScore {
  id: string;
  assessment_name: string;
  completed_at: string;
  overall_score: number;
  category_scores: {
    [key: string]: number;
  };
  percentile: number;
  confidence_score: number;
}
interface TrendData {
  date: string;
  score: number;
  category: string;
}
interface PersonalityProfile {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}
interface DashboardProps {
  userId?: string;
  teamId?: string;
}
// =================================================================
// MAIN COMPONENT
// =================================================================
const ScoringDashboard: React.FC<DashboardProps> = ({ userId, teamId }) => {
  const [scores, setScores] = useState<AssessmentScore[]>([]);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [personalityProfile, setPersonalityProfile] = useState<PersonalityProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('month');
  const [activeTab, setActiveTab] = useState<'overview' | 'trends' | 'personality'>('overview');
  // =================================================================
  // DATA FETCHING
  // =================================================================
  useEffect(() => {
    fetchDashboardData();
  }, [userId, teamId, selectedPeriod]);
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
      // Fetch assessment scores
      const scoresResponse = await fetch(
        `/api/v1/assessments/scores?period=${selectedPeriod}`,
        { headers }
      );
      const scoresData = await scoresResponse.json();
      setScores(scoresData);
      // Fetch trend data
      const trendsResponse = await fetch(
        `/api/v1/assessments/trends?period=${selectedPeriod}`,
        { headers }
      );
      const trendsData = await trendsResponse.json();
      setTrendData(trendsData);
      // Fetch personality profile
      const profileResponse = await fetch(
        `/api/v1/assessments/personality-profile`,
        { headers }
      );
      const profileData = await profileResponse.json();
      setPersonalityProfile(profileData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };
  // =================================================================
  // UTILITY FUNCTIONS
  // =================================================================
  const getScoreTrend = (currentScore: number, previousScore: number) => {
    const diff = currentScore - previousScore;
    if (diff > 0) return { direction: 'up', value: diff };
    if (diff < 0) return { direction: 'down', value: Math.abs(diff) };
    return { direction: 'stable', value: 0 };
  };
  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };
  const getScoreBgColor = (score: number): string => {
    if (score >= 90) return 'bg-green-100';
    if (score >= 75) return 'bg-blue-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };
  const downloadReport = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/assessments/report/download', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `assessment_report_${new Date().toISOString()}.pdf`;
      a.click();
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };
  // =================================================================
  // RENDER COMPONENTS
  // =================================================================
  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {scores.slice(0, 3).map((score) => (
          <div
            key={score.id}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                {score.assessment_name}
              </h3>
              <Activity className="w-5 h-5 text-gray-400" />
            </div>
            <div className="flex items-end justify-between">
              <div>
                <div className={`text-4xl font-bold ${getScoreColor(score.overall_score)}`}>
                  {score.overall_score.toFixed(1)}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {score.percentile}th percentile
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center text-green-600">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  <span className="text-sm font-medium">+5.2%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">vs last month</div>
              </div>
            </div>
            {/* Progress Bar */}
            <div className="mt-4">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getScoreBgColor(score.overall_score)} transition-all duration-500`}
                  style={{ width: `${score.overall_score}%` }}
                />
              </div>
            </div>
            {/* Confidence Indicator */}
            <div className="mt-3 flex items-center text-xs text-gray-600">
              <div className="flex-1">
                <span className="font-medium">Confidence: </span>
                <span>{(score.confidence_score * 100).toFixed(0)}%</span>
              </div>
              <div className="text-gray-400">
                {new Date(score.completed_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        ))}
      </div>
      {/* Category Scores Bar Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Category Performance
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={Object.entries(scores[0]?.category_scores || {}).map(([key, value]) => ({
            category: key,
            score: value,
          }))}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="score" fill="#3b82f6" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {/* Recent Assessments Table */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Recent Assessments
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  Assessment
                </th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">
                  Date
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                  Score
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                  Percentile
                </th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-600">
                  Trend
                </th>
              </tr>
            </thead>
            <tbody>
              {scores.map((score) => (
                <tr key={score.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-800">
                    {score.assessment_name}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {new Date(score.completed_at).toLocaleDateString()}
                  </td>
                  <td className={`py-3 px-4 text-sm text-right font-semibold ${getScoreColor(score.overall_score)}`}>
                    {score.overall_score.toFixed(1)}
                  </td>
                  <td className="py-3 px-4 text-sm text-right text-gray-600">
                    {score.percentile}th
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center text-green-600 text-sm">
                      <TrendingUp className="w-4 h-4" />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
  const renderTrendsTab = () => (
    <div className="space-y-6">
      {/* Score Trends Line Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Score Trends Over Time
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {/* Growth Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="font-semibold text-gray-800 mb-3">Strengths</h4>
          <ul className="space-y-2">
            <li className="flex items-start">
              <TrendingUp className="w-5 h-5 text-green-600 mr-2 mt-0.5" />
              <div>
                <div className="font-medium text-gray-800">Problem Solving</div>
                <div className="text-sm text-gray-600">Improved by 12% this month</div>
              </div>
            </li>
            <li className="flex items-start">
              <TrendingUp className="w-5 h-5 text-green-600 mr-2 mt-0.5" />
              <div>
                <div className="font-medium text-gray-800">Leadership</div>
                <div className="text-sm text-gray-600">Consistently high scores</div>
              </div>
            </li>
          </ul>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="font-semibold text-gray-800 mb-3">Areas for Growth</h4>
          <ul className="space-y-2">
            <li className="flex items-start">
              <TrendingDown className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
              <div>
                <div className="font-medium text-gray-800">Time Management</div>
                <div className="text-sm text-gray-600">Focus area for next month</div>
              </div>
            </li>
            <li className="flex items-start">
              <TrendingDown className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
              <div>
                <div className="font-medium text-gray-800">Stress Management</div>
                <div className="text-sm text-gray-600">Consider training resources</div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
  const renderPersonalityTab = () => {
    if (!personalityProfile) return null;
    const radarData = Object.entries(personalityProfile).map(([key, value]) => ({
      trait: key.charAt(0).toUpperCase() + key.slice(1),
      value: value,
    }));
    return (
      <div className="space-y-6">
        {/* Personality Radar Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Personality Profile (Big Five)
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="trait" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar
                name="Your Profile"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        {/* Trait Descriptions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(personalityProfile).map(([trait, score]) => (
            <div key={trait} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-800 capitalize">
                  {trait}
                </h4>
                <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                  {score.toFixed(0)}
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full ${getScoreBgColor(score)}`}
                  style={{ width: `${score}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {getTraitDescription(trait, score)}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  };
  const getTraitDescription = (trait: string, score: number): string => {
    const descriptions: { [key: string]: { high: string; low: string } } = {
      openness: {
        high: 'You enjoy new experiences and creative thinking.',
        low: 'You prefer familiar routines and practical approaches.',
      },
      conscientiousness: {
        high: 'You are organized, reliable, and detail-oriented.',
        low: 'You are flexible and spontaneous in your approach.',
      },
      extraversion: {
        high: 'You are outgoing and energized by social interaction.',
        low: 'You prefer quieter settings and smaller groups.',
      },
      agreeableness: {
        high: 'You are cooperative and value harmony in relationships.',
        low: 'You are direct and prioritize objectivity over harmony.',
      },
      neuroticism: {
        high: 'You experience emotions intensely and may stress easily.',
        low: 'You are calm and emotionally stable under pressure.',
      },
    };
    return score >= 50 ? descriptions[trait]?.high : descriptions[trait]?.low;
  };
  // =================================================================
  // MAIN RENDER
  // =================================================================
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assessment Dashboard</h1>
          <p className="text-gray-600 mt-1">Track your progress and insights</p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Period Selector */}
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="year">Last Year</option>
          </select>
          {/* Refresh Button */}
          <button
            onClick={fetchDashboardData}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          {/* Download Report Button */}
          <button
            onClick={downloadReport}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="w-4 h-4 mr-2" />
            Download Report
          </button>
        </div>
      </div>
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <div className="flex space-x-8">
          {['overview', 'trends', 'personality'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>
      {/* Tab Content */}
      {activeTab === 'overview' && renderOverviewTab()}
      {activeTab === 'trends' && renderTrendsTab()}
      {activeTab === 'personality' && renderPersonalityTab()}
    </div>
  );
};
export default ScoringDashboard;
