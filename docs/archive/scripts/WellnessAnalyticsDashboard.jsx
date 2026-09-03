import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, Heart, Brain, Users, Sparkles, DollarSign, Shield,
  TrendingUp, Calendar, Target, Award, AlertCircle, CheckCircle,
  BarChart3, PieChart, LineChart, Map, Filter, Download, Share2,
  User, Clock, Star, Zap
} from 'lucide-react';

const WellnessAnalyticsDashboard = ({ assessmentData, userProgress = [] }) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('3months');
  const [selectedDomain, setSelectedDomain] = useState('all');
  const [analyticsData, setAnalyticsData] = useState(null);

  const domainConfig = {
    physical: { icon: Activity, color: '#10b981', name: 'Physical Wellness' },
    mental: { icon: Brain, color: '#3b82f6', name: 'Mental Wellness' },
    emotional: { icon: Heart, color: '#ef4444', name: 'Emotional Wellness' },
    social: { icon: Users, color: '#8b5cf6', name: 'Social Wellness' },
    spiritual: { icon: Sparkles, color: '#f59e0b', name: 'Spiritual Wellness' },
    environmental: { icon: Shield, color: '#06b6d4', name: 'Environmental Wellness' },
    financial: { icon: DollarSign, color: '#84cc16', name: 'Financial Wellness' },
    intellectual: { icon: Brain, color: '#6366f1', name: 'Intellectual Wellness' },
    digital: { icon: Target, color: '#ec4899', name: 'Digital Wellness' }
  };

  useEffect(() => {
    if (assessmentData) {
      processAnalyticsData();
    }
  }, [assessmentData, userProgress, selectedTimeRange]);

  const processAnalyticsData = () => {
    // Process assessment data and user progress
    const processed = {
      overview: calculateOverviewMetrics(),
      domainScores: calculateDomainScores(),
      trends: calculateTrends(),
      insights: generateInsights(),
      progressTracking: trackProgressOverTime(),
      recommendations: generateAnalyticsRecommendations()
    };
    setAnalyticsData(processed);
  };

  const calculateOverviewMetrics = () => {
    const latestAssessment = assessmentData?.[assessmentData.length - 1] || {};
    const domainCount = Object.keys(latestAssessment).length;
    const completedDomains = Object.values(latestAssessment).filter(score => score !== null).length;

    return {
      completionRate: domainCount > 0 ? (completedDomains / domainCount) * 100 : 0,
      overallScore: calculateOverallScore(latestAssessment),
      lastAssessmentDate: latestAssessment.timestamp || null,
      improvementRate: calculateImprovementRate(),
      streakDays: calculateStreakDays()
    };
  };

  const calculateDomainScores = () => {
    const scores = {};
    Object.entries(domainConfig).forEach(([domain, config]) => {
      const domainData = assessmentData?.filter(a => a[domain]) || [];
      const latestScore = domainData[domainData.length - 1]?.[domain] || 0;
      scores[domain] = {
        current: latestScore,
        trend: calculateDomainTrend(domain),
        status: getDomainStatus(latestScore),
        benchmark: getBenchmarkScore(domain)
      };
    });
    return scores;
  };

  const calculateTrends = () => {
    return {
      weekly: calculateWeeklyTrends(),
      monthly: calculateMonthlyTrends(),
      domainSpecific: calculateDomainTrends()
    };
  };

  const generateInsights = () => {
    const insights = [];

    // Strength insights
    const strongestDomains = getStrongestDomains();
    if (strongestDomains.length > 0) {
      insights.push({
        type: 'strength',
        title: 'Your Wellness Superpowers',
        description: `You're excelling in ${strongestDomains.map(d => domainConfig[d]?.name).join(' and ')}`,
        icon: Award,
        color: '#10b981'
      });
    }

    // Improvement opportunities
    const improvementAreas = getImprovementAreas();
    if (improvementAreas.length > 0) {
      insights.push({
        type: 'opportunity',
        title: 'Growth Opportunities',
        description: `Consider focusing on ${improvementAreas.map(d => domainConfig[d]?.name).join(' and ')}`,
        icon: TrendingUp,
        color: '#f59e0b'
      });
    }

    // Pattern insights
    const patterns = analyzePatterns();
    if (patterns.length > 0) {
      insights.push({
        type: 'pattern',
        title: 'Interesting Patterns',
        description: patterns[0],
        icon: Brain,
        color: '#3b82f6'
      });
    }

    return insights;
  };

  const trackProgressOverTime = () => {
    if (userProgress.length === 0) return [];

    return userProgress.map(progress => ({
      date: progress.date,
      score: progress.overallScore,
      domains: progress.domainScores,
      achievements: progress.achievements || [],
      challenges: progress.challenges || []
    }));
  };

  const calculateOverallScore = (assessment) => {
    if (!assessment) return 0;

    const scores = Object.values(assessment).filter(val => typeof val === 'number');
    return scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
  };

  const getDomainStatus = (score) => {
    if (score >= 80) return { label: 'Excellent', color: '#10b981' };
    if (score >= 65) return { label: 'Good', color: '#3b82f6' };
    if (score >= 50) return { label: 'Fair', color: '#f59e0b' };
    return { label: 'Needs Attention', color: '#ef4444' };
  };

  const renderOverviewSection = () => {
    if (!analyticsData) return null;

    const { overview } = analyticsData;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="h-6 w-6 text-blue-600" />
            </div>
            <span className="text-sm text-gray-500">Overall Score</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{overview.overallScore}</div>
          <div className="text-sm text-gray-600 mt-1">out of 100</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <Target className="h-6 w-6 text-green-600" />
            </div>
            <span className="text-sm text-gray-500">Completion Rate</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{Math.round(overview.completionRate)}%</div>
          <div className="text-sm text-gray-600 mt-1">assessment complete</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <span className="text-sm text-gray-500">Improvement</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{overview.improvementRate > 0 ? '+' : ''}{overview.improvementRate}%</div>
          <div className="text-sm text-gray-600 mt-1">this month</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Zap className="h-6 w-6 text-orange-600" />
            </div>
            <span className="text-sm text-gray-500">Current Streak</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{overview.streakDays}</div>
          <div className="text-sm text-gray-600 mt-1">days active</div>
        </motion.div>
      </div>
    );
  };

  const renderDomainScores = () => {
    if (!analyticsData?.domainScores) return null;

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Domain Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(analyticsData.domainScores).map(([domain, data], index) => {
            const config = domainConfig[domain];
            if (!config) return null;

            return (
              <motion.div
                key={domain}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="p-2 rounded-lg" style={{ backgroundColor: `${config.color}20` }}>
                      <config.icon className="h-5 w-5" style={{ color: config.color }} />
                    </div>
                    <span className="font-medium text-gray-900">{config.name}</span>
                  </div>
                  <span className={`text-sm font-medium px-2 py-1 rounded-full`} style={{
                    backgroundColor: `${data.status.color}20`,
                    color: data.status.color
                  }}>
                    {data.status.label}
                  </span>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Current Score</span>
                      <span className="font-medium">{data.current}/100</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all duration-500"
                        style={{
                          width: `${data.current}%`,
                          backgroundColor: config.color
                        }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">vs. Benchmark</span>
                    <span className={`font-medium ${
                      data.current >= data.benchmark ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {data.current >= data.benchmark ? '+' : ''}{data.current - data.benchmark}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    );
  };

  const renderProgressChart = () => {
    if (!analyticsData?.progressTracking || analyticsData.progressTracking.length === 0) {
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="bg-white rounded-xl shadow-sm p-6 mb-8"
        >
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No progress data available yet</p>
            <p className="text-sm text-gray-500 mt-2">Complete more assessments to see your trends</p>
          </div>
        </motion.div>
      );
    }

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="bg-white rounded-xl shadow-sm p-6 mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Progress Over Time</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedTimeRange('1month')}
              className={`px-3 py-1 text-sm rounded-lg ${
                selectedTimeRange === '1month'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              1M
            </button>
            <button
              onClick={() => setSelectedTimeRange('3months')}
              className={`px-3 py-1 text-sm rounded-lg ${
                selectedTimeRange === '3months'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              3M
            </button>
            <button
              onClick={() => setSelectedTimeRange('6months')}
              className={`px-3 py-1 text-sm rounded-lg ${
                selectedTimeRange === '6months'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              6M
            </button>
          </div>
        </div>

        <div className="h-64 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
          <LineChart className="h-12 w-12 text-gray-400" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {calculateAverageScore()}
            </div>
            <div className="text-sm text-gray-600">Average Score</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {calculateBestStreak()}
            </div>
            <div className="text-sm text-gray-600">Best Streak</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {analyticsData.progressTracking.length}
            </div>
            <div className="text-sm text-gray-600">Assessments</div>
          </div>
        </div>
      </motion.div>
    );
  };

  const renderInsights = () => {
    if (!analyticsData?.insights || analyticsData.insights.length === 0) return null;

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="space-y-4 mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-900">Personalized Insights</h3>
        {analyticsData.insights.map((insight, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.9 + index * 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
          >
            <div className="flex items-start space-x-4">
              <div className="p-2 rounded-lg" style={{ backgroundColor: `${insight.color}20` }}>
                <insight.icon className="h-6 w-6" style={{ color: insight.color }} />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-2">{insight.title}</h4>
                <p className="text-gray-600">{insight.description}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    );
  };

  const calculateAverageScore = () => {
    if (!analyticsData?.progressTracking.length) return 0;
    const scores = analyticsData.progressTracking.map(p => p.score);
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  const calculateBestStreak = () => {
    if (!analyticsData?.progressTracking.length) return 0;
    return Math.max(...analyticsData.progressTracking.map(p => p.streakDays || 0));
  };

  // Helper functions (simplified for demo)
  const calculateImprovementRate = () => 12;
  const calculateStreakDays = () => 7;
  const calculateDomainTrend = (domain) => ({ direction: 'up', change: 5 });
  const getBenchmarkScore = (domain) => 70;
  const getStrongestDomains = () => ['physical', 'social'];
  const getImprovementAreas = () => ['mental', 'emotional'];
  const analyzePatterns = () => ['Your energy peaks in the morning and dips in the afternoon'];
  const calculateWeeklyTrends = () => [];
  const calculateMonthlyTrends = () => [];

  if (!analyticsData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics dashboard...</p>
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
              <h1 className="text-2xl font-bold text-gray-900">Wellness Analytics</h1>
              <p className="text-gray-600">Track your progress and discover insights</p>
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
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Share2 className="h-4 w-4" />
                <span>Share</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {renderOverviewSection()}
        {renderDomainScores()}
        {renderProgressChart()}
        {renderInsights()}
      </div>
    </div>
  );
};

export default WellnessAnalyticsDashboard;
