import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar
} from 'recharts';
import {
  Activity, Heart, Moon, TrendingUp, Calendar,
  Filter, Download, Settings, Info, ChevronDown,
  Droplets, Flame, Brain, Battery, Target
} from 'lucide-react';

const HealthDataVisualization = ({ userId, timeRange = '7days' }) => {
  const [healthData, setHealthData] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [loading, setLoading] = useState(true);

  const metricConfig = {
    steps: {
      label: 'Steps',
      icon: Activity,
      color: '#10b981',
      unit: 'steps',
      goal: 10000,
      gradient: ['#10b981', '#34d399']
    },
    heartRate: {
      label: 'Heart Rate',
      icon: Heart,
      color: '#ef4444',
      unit: 'bpm',
      goal: 70,
      gradient: ['#ef4444', '#f87171']
    },
    sleep: {
      label: 'Sleep',
      icon: Moon,
      color: '#6366f1',
      unit: 'hours',
      goal: 8,
      gradient: ['#6366f1', '#818cf8']
    },
    calories: {
      label: 'Calories',
      icon: Flame,
      color: '#f59e0b',
      unit: 'kcal',
      goal: 2000,
      gradient: ['#f59e0b', '#fbbf24']
    },
    hydration: {
      label: 'Hydration',
      icon: Droplets,
      color: '#06b6d4',
      unit: 'ml',
      goal: 2000,
      gradient: ['#06b6d4', '#22d3ee']
    },
    recovery: {
      label: 'Recovery',
      icon: Battery,
      color: '#8b5cf6',
      unit: '%',
      goal: 80,
      gradient: ['#8b5cf6', '#a78bfa']
    },
    stress: {
      label: 'Stress',
      icon: Brain,
      color: '#ec4899',
      unit: 'score',
      goal: 30,
      gradient: ['#ec4899', '#f472b6']
    },
    activeMinutes: {
      label: 'Active Minutes',
      icon: Target,
      color: '#14b8a6',
      unit: 'minutes',
      goal: 30,
      gradient: ['#14b8a6', '#2dd4bf']
    }
  };

  useEffect(() => {
    loadHealthData();
  }, [selectedTimeRange, comparisonMode]);

  const loadHealthData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/health-data/${userId}/visualization?timeRange=${selectedTimeRange}&comparison=${comparisonMode}`
      );
      const data = await response.json();
      setHealthData(data);
    } catch (error) {
      console.error('Failed to load health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const processTimeSeriesData = (metric) => {
    if (!healthData?.timeSeries) return [];

    return healthData.timeSeries.map(point => ({
      date: new Date(point.timestamp).toLocaleDateString('en-US', { weekday: 'short' }),
      value: point[metric] || 0,
      comparison: comparisonMode ? point[`${metric}_comparison`] : null,
      timestamp: point.timestamp
    }));
  };

  const calculateWeeklyAverages = () => {
    if (!healthData?.weekly) return [];

    return healthData.weekly.map(week => ({
      week: `Week ${week.weekNumber}`,
      ...Object.keys(metricConfig).reduce((acc, metric) => {
        acc[metric] = week[metric] || 0;
        return acc;
      }, {})
    }));
  };

  const getMetricDistribution = () => {
    if (!healthData?.distribution) return [];

    return Object.entries(metricConfig).map(([key, config]) => ({
      name: config.label,
      value: healthData.distribution[key] || 0,
      color: config.color,
      goal: config.goal
    }));
  };

  const getWellnessScore = () => {
    if (!healthData?.wellnessScore) return 0;

    return Math.round(
      Object.entries(metricConfig).reduce((score, [metric, config]) => {
        const value = healthData.daily?.[metric] || 0;
        const achievement = Math.min(value / config.goal, 1);
        return score + achievement;
      }, 0) / Object.keys(metricConfig).length * 100
    );
  };

  const renderWellnessScore = () => {
    const score = getWellnessScore();
    const scoreColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
      >
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Wellness Score</h3>

          <div className="relative inline-flex items-center justify-center">
            <div className="w-32 h-32 rounded-full border-8 border-gray-200"></div>
            <div
              className="absolute w-32 h-32 rounded-full border-8 border-transparent"
              style={{
                borderRightColor: scoreColor,
                borderTopColor: scoreColor,
                transform: `rotate(${(score / 100) * 360 - 90}deg)`,
                transition: 'transform 1s ease-out'
              }}
            ></div>
            <div className="absolute text-center">
              <div className="text-3xl font-bold" style={{ color: scoreColor }}>
                {score}
              </div>
              <div className="text-sm text-gray-600">out of 100</div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div className="text-center">
              <div className="text-gray-600">Daily Average</div>
              <div className="font-semibold text-gray-900">
                {score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Needs Work'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-gray-600">Trend</div>
              <div className="font-semibold text-green-600">
                {healthData?.trend > 0 ? '+' : ''}{healthData?.trend || 0}%
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderMetricCards = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {Object.entries(metricConfig).slice(0, 8).map(([key, config], index) => {
        const value = healthData?.daily?.[key] || 0;
        const goal = config.goal;
        const progress = Math.min((value / goal) * 100, 100);
        const Icon = config.icon;

        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + index * 0.1 }}
            className="bg-white rounded-lg p-4 border border-gray-200 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setSelectedMetric(key === selectedMetric ? 'all' : key)}
          >
            <div className="flex items-center justify-between mb-3">
              <Icon className="h-4 w-4" style={{ color: config.color }} />
              <span className="text-xs text-gray-500">{progress.toFixed(0)}%</span>
            </div>

            <div className="mb-2">
              <div className="text-lg font-bold text-gray-900">
                {Math.round(value)}
                <span className="text-xs font-normal text-gray-500 ml-1">{config.unit}</span>
              </div>
              <div className="text-xs text-gray-600">{config.label}</div>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full transition-all duration-500"
                style={{
                  width: `${progress}%`,
                  backgroundColor: config.color
                }}
              />
            </div>
          </motion.div>
        );
      })}
    </div>
  );

  const renderTimeSeriesChart = () => {
    const metricsToShow = selectedMetric === 'all'
      ? Object.keys(metricConfig).slice(0, 3)
      : [selectedMetric];

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Trends Over Time</h3>
          <div className="flex items-center space-x-2">
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
              <option value="1year">Last Year</option>
            </select>
            <button
              onClick={() => setComparisonMode(!comparisonMode)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                comparisonMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Compare
            </button>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={processTimeSeriesData(metricsToShow[0])}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              stroke="#6b7280"
            />
            <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />

            {metricsToShow.map((metric, index) => {
              const config = metricConfig[metric];
              return (
                <Line
                  key={metric}
                  type="monotone"
                  dataKey="value"
                  stroke={config.color}
                  strokeWidth={2}
                  dot={{ fill: config.color, r: 4 }}
                  name={config.label}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    );
  };

  const renderWellnessWheel = () => {
    const radarData = Object.entries(metricConfig).map(([key, config]) => {
      const value = healthData?.daily?.[key] || 0;
      const percentage = Math.min((value / config.goal) * 100, 100);

      return {
        metric: config.label,
        value: percentage,
        fullMark: 100
      };
    });

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Wellness Wheel</h3>

        <ResponsiveContainer width="100%" height={350}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fontSize: 11 }}
              className="text-gray-600"
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fontSize: 10 }}
              stroke="#9ca3af"
            />
            <Radar
              name="Current"
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>

        <div className="mt-4 text-center text-sm text-gray-600">
          See how balanced your wellness is across all health metrics
        </div>
      </motion.div>
    );
  };

  const renderGoalProgress = () => {
    const goals = Object.entries(metricConfig).map(([key, config]) => {
      const current = healthData?.daily?.[key] || 0;
      const goal = config.goal;
      const progress = Math.min((current / goal) * 100, 100);

      return {
        metric: config.label,
        current: Math.round(current),
        goal: goal,
        progress: progress,
        color: config.color,
        icon: config.icon
      };
    }).sort((a, b) => b.progress - a.progress);

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="bg-white rounded-xl shadow-sm p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Daily Goal Progress</h3>

        <div className="space-y-4">
          {goals.map((goal, index) => {
            const Icon = goal.icon;

            return (
              <div key={goal.metric} className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <Icon className="h-5 w-5" style={{ color: goal.color }} />
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">{goal.metric}</span>
                    <span className="text-sm text-gray-600">
                      {goal.current} / {goal.goal}
                    </span>
                  </div>

                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${goal.progress}%`,
                        backgroundColor: goal.color
                      }}
                    />
                  </div>
                </div>

                <div className="flex-shrink-0 text-sm font-medium" style={{ color: goal.color }}>
                  {goal.progress.toFixed(0)}%
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading health data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Health Analytics</h1>
              <p className="text-gray-600">Visualize your health metrics and trends</p>
            </div>
            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <Filter className="h-4 w-4" />
                <span>Filter</span>
              </button>
              <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <Download className="h-4 w-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Left Column */}
          <div className="lg:col-span-1">
            {renderWellnessScore()}
            {renderGoalProgress()}
          </div>

          {/* Right Column */}
          <div className="lg:col-span-3 space-y-8">
            {renderMetricCards()}
            {renderTimeSeriesChart()}
            {renderWellnessWheel()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthDataVisualization;
