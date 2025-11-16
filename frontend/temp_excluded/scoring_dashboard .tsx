import React, { useState, useMemo } from 'react';
import { LineChart, Line, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Activity, Target, Award, AlertCircle } from 'lucide-react';

// Sample player data with comprehensive scoring
const samplePlayers = [
  {
    id: 1,
    name: "Luka Dončić",
    team: "DAL",
    position: "PG/SG",
    currentScore: 94.2,
    previousScore: 92.8,
    trend: "up",
    categories: {
      scoring: 95,
      efficiency: 92,
      playmaking: 98,
      defense: 72,
      rebounding: 85,
      consistency: 88
    },
    weeklyScores: [
      { week: 'W1', score: 89.5, minutes: 34 },
      { week: 'W2', score: 91.2, minutes: 36 },
      { week: 'W3', score: 92.8, minutes: 35 },
      { week: 'W4', score: 94.2, minutes: 37 }
    ],
    alerts: [
      { type: 'positive', message: 'Career-high efficiency week' },
      { type: 'neutral', message: 'Minutes slightly elevated' }
    ]
  },
  {
    id: 2,
    name: "Anthony Davis",
    team: "LAL",
    position: "PF/C",
    currentScore: 91.5,
    previousScore: 93.1,
    trend: "down",
    categories: {
      scoring: 88,
      efficiency: 93,
      playmaking: 75,
      defense: 96,
      rebounding: 94,
      consistency: 82
    },
    weeklyScores: [
      { week: 'W1', score: 95.2, minutes: 35 },
      { week: 'W2', score: 93.1, minutes: 33 },
      { week: 'W3', score: 92.0, minutes: 31 },
      { week: 'W4', score: 91.5, minutes: 32 }
    ],
    alerts: [
      { type: 'warning', message: 'Decreased minutes last 3 weeks' },
      { type: 'negative', message: 'Efficiency trending down' }
    ]
  },
  {
    id: 3,
    name: "Jayson Tatum",
    team: "BOS",
    position: "SF/PF",
    currentScore: 92.8,
    previousScore: 92.5,
    trend: "stable",
    categories: {
      scoring: 93,
      efficiency: 89,
      playmaking: 84,
      defense: 87,
      rebounding: 82,
      consistency: 94
    },
    weeklyScores: [
      { week: 'W1', score: 92.1, minutes: 36 },
      { week: 'W2', score: 92.5, minutes: 35 },
      { week: 'W3', score: 92.9, minutes: 36 },
      { week: 'W4', score: 92.8, minutes: 35 }
    ],
    alerts: [
      { type: 'positive', message: 'Highly consistent performance' }
    ]
  },
  {
    id: 4,
    name: "Nikola Jokić",
    team: "DEN",
    position: "C",
    currentScore: 96.1,
    previousScore: 95.8,
    trend: "up",
    categories: {
      scoring: 91,
      efficiency: 98,
      playmaking: 97,
      defense: 78,
      rebounding: 96,
      consistency: 95
    },
    weeklyScores: [
      { week: 'W1', score: 95.0, minutes: 34 },
      { week: 'W2', score: 95.8, minutes: 35 },
      { week: 'W3', score: 96.5, minutes: 34 },
      { week: 'W4', score: 96.1, minutes: 33 }
    ],
    alerts: [
      { type: 'positive', message: 'League-leading efficiency' },
      { type: 'positive', message: 'Elite playmaking for position' }
    ]
  }
];

const ScoringDashboard = () => {
  const [selectedPlayer, setSelectedPlayer] = useState(samplePlayers[0]);
  const [viewMode, setViewMode] = useState('overview'); // overview, detailed, comparison

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'up': return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'down': return <TrendingDown className="w-5 h-5 text-red-500" />;
      default: return <Minus className="w-5 h-5 text-gray-500" />;
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 90) return 'bg-green-50 border-green-200';
    if (score >= 80) return 'bg-blue-50 border-blue-200';
    if (score >= 70) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const radarData = useMemo(() => {
    return Object.entries(selectedPlayer.categories).map(([key, value]) => ({
      category: key.charAt(0).toUpperCase() + key.slice(1),
      value: value,
      fullMark: 100
    }));
  }, [selectedPlayer]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2">Player Scoring System</h1>
              <p className="text-slate-600">Comprehensive performance analytics and trending</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('overview')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  viewMode === 'overview' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setViewMode('detailed')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  viewMode === 'detailed' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                Detailed
              </button>
            </div>
          </div>

          {/* Player Selector */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {samplePlayers.map(player => (
              <button
                key={player.id}
                onClick={() => setSelectedPlayer(player)}
                className={`p-4 rounded-lg border-2 transition ${
                  selectedPlayer.id === player.id
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="font-semibold text-slate-900">{player.name}</div>
                <div className="text-sm text-slate-600">{player.team} • {player.position}</div>
                <div className={`text-2xl font-bold mt-2 ${getScoreColor(player.currentScore)}`}>
                  {player.currentScore}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Main Content */}
        {viewMode === 'overview' && (
          <>
            {/* Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Current Score */}
              <div className={`rounded-xl shadow-sm p-6 border ${getScoreBg(selectedPlayer.currentScore)}`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="text-sm font-medium text-slate-600">Current Score</div>
                  <Award className="w-5 h-5 text-slate-400" />
                </div>
                <div className={`text-4xl font-bold ${getScoreColor(selectedPlayer.currentScore)} mb-2`}>
                  {selectedPlayer.currentScore}
                </div>
                <div className="flex items-center gap-2 text-sm">
                  {getTrendIcon(selectedPlayer.trend)}
                  <span className="text-slate-600">
                    {selectedPlayer.trend === 'up' ? '+' : selectedPlayer.trend === 'down' ? '' : '±'}
                    {Math.abs(selectedPlayer.currentScore - selectedPlayer.previousScore).toFixed(1)} from last week
                  </span>
                </div>
              </div>

              {/* Best Category */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-sm font-medium text-slate-600">Top Category</div>
                  <Target className="w-5 h-5 text-slate-400" />
                </div>
                <div className="text-2xl font-bold text-slate-900 mb-1">
                  {Object.entries(selectedPlayer.categories)
                    .sort((a, b) => b[1] - a[1])[0][0]
                    .charAt(0).toUpperCase() + 
                    Object.entries(selectedPlayer.categories)
                    .sort((a, b) => b[1] - a[1])[0][0].slice(1)}
                </div>
                <div className="text-3xl font-bold text-green-600">
                  {Object.entries(selectedPlayer.categories)
                    .sort((a, b) => b[1] - a[1])[0][1]}
                </div>
              </div>

              {/* Consistency */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-sm font-medium text-slate-600">Consistency</div>
                  <Activity className="w-5 h-5 text-slate-400" />
                </div>
                <div className="text-2xl font-bold text-slate-900 mb-1">Performance</div>
                <div className={`text-3xl font-bold ${getScoreColor(selectedPlayer.categories.consistency)}`}>
                  {selectedPlayer.categories.consistency}
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Weekly Trend */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">4-Week Trend</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={selectedPlayer.weeklyScores}>
                    <defs>
                      <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="week" stroke="#64748b" />
                    <YAxis domain={[85, 100]} stroke="#64748b" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px'
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="score" 
                      stroke="#3b82f6" 
                      strokeWidth={3}
                      fill="url(#colorScore)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Radar Chart */}
              <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Category Breakdown</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="category" stroke="#64748b" />
                    <PolarRadiusAxis domain={[0, 100]} stroke="#64748b" />
                    <Radar 
                      name={selectedPlayer.name} 
                      dataKey="value" 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.5}
                      strokeWidth={2}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '8px'
                      }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Alerts */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Performance Alerts
              </h3>
              <div className="space-y-3">
                {selectedPlayer.alerts.map((alert, idx) => (
                  <div 
                    key={idx}
                    className={`p-4 rounded-lg border-l-4 ${
                      alert.type === 'positive' 
                        ? 'bg-green-50 border-green-500' 
                        : alert.type === 'warning'
                        ? 'bg-yellow-50 border-yellow-500'
                        : alert.type === 'negative'
                        ? 'bg-red-50 border-red-500'
                        : 'bg-blue-50 border-blue-500'
                    }`}
                  >
                    <p className="text-slate-700">{alert.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {viewMode === 'detailed' && (
          <div className="space-y-6">
            {/* Category Details */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Detailed Category Scores</h3>
              <div className="space-y-4">
                {Object.entries(selectedPlayer.categories).map(([category, score]) => (
                  <div key={category}>
                    <div className="flex justify-between mb-2">
                      <span className="font-medium text-slate-700 capitalize">{category}</span>
                      <span className={`font-bold ${getScoreColor(score)}`}>{score}</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-3">
                      <div 
                        className={`h-3 rounded-full transition-all ${
                          score >= 90 ? 'bg-green-500' :
                          score >= 80 ? 'bg-blue-500' :
                          score >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Minutes Trend */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Minutes vs Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={selectedPlayer.weeklyScores}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="week" stroke="#64748b" />
                  <YAxis yAxisId="left" stroke="#64748b" />
                  <YAxis yAxisId="right" orientation="right" stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#fff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Bar yAxisId="left" dataKey="score" fill="#3b82f6" name="Score" />
                  <Bar yAxisId="right" dataKey="minutes" fill="#10b981" name="Minutes" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScoringDashboard;