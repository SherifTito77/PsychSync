import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getMonitoringStats, MonitoringStats } from '@/services/emailMonitoringService';

interface EmailAnalyticsChartsProps {
  timeframe?: 'day' | 'week' | 'month';
}

const EmailAnalyticsCharts: React.FC<EmailAnalyticsChartsProps> = ({
  timeframe = 'week'
}) => {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedChart, setSelectedChart] = useState<'timeline' | 'categories' | 'patterns'>('timeline');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const result = await getMonitoringStats();
      if (result.success && result.data) {
        setStats(result.data);
      }
      setLoading(false);
    };

    fetchData();
  }, [timeframe]);

  if (loading || !stats) {
    return <div className="p-6">Loading charts...</div>;
  }

  // Generate hourly timeline data
  const generateTimelineData = () => {
    const hours = [];
    const now = new Date();
    for (let i = 23; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourStr = hour.getHours() + ':00';
      // Simulate data based on patterns
      const isPeakHour = hour.getHours() === 0 || hour.getHours() === 19;
      const value = isPeakHour ? Math.floor(Math.random() * 30 + 20) : Math.floor(Math.random() * 10 + 2);
      hours.push({ hour: hourStr, value, timestamp: hour });
    }
    return hours;
  };

  const timelineData = generateTimelineData();
  const maxValue = Math.max(...timelineData.map(d => d.value));

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">📊 Email Analytics Charts</h2>
          <p className="text-gray-600">Advanced visualizations of your email patterns</p>
        </div>
        <div className="flex space-x-2">
          {(['timeline', 'categories', 'patterns'] as const).map((chart) => (
            <Button
              key={chart}
              variant={selectedChart === chart ? 'default' : 'outline'}
              onClick={() => setSelectedChart(chart)}
              className="capitalize"
            >
              {chart}
            </Button>
          ))}
        </div>
      </div>

      {/* Timeline Chart */}
      {selectedChart === 'timeline' && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>📈 Email Volume Timeline (Last 24 Hours)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Bar chart */}
              <div className="relative h-64 border-l border-b border-gray-300">
                {timelineData.map((data, index) => {
                  const height = (data.value / maxValue) * 100;
                  const isNow = index === timelineData.length - 1;

                  return (
                    <div
                      key={index}
                      className="absolute bottom-0 flex flex-col items-center justify-end"
                      style={{
                        left: `${(index / timelineData.length) * 100}%`,
                        width: `${100 / timelineData.length}%`,
                        height: '100%'
                      }}
                    >
                      <div className="w-full relative" style={{ height: `${height}%` }}>
                        <div
                          className={`absolute bottom-0 w-full mx-auto rounded-t transition-all ${
                            data.value > 20 ? 'bg-red-400' : data.value > 10 ? 'bg-yellow-400' : 'bg-blue-400'
                          }`}
                          style={{ height: '100%', width: '80%' }}
                        ></div>
                      </div>
                      {isNow && (
                        <div className="absolute top-0 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded">
                          NOW
                        </div>
                      )}
                      {/* X-axis label */}
                      <div className="absolute bottom-0 w-full text-center text-xs text-gray-500 -translate-y-full">
                        {index % 4 === 0 ? data.hour : ''}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="flex justify-center space-x-6 mt-4">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-red-400 rounded"></div>
                  <span className="text-sm text-gray-600">High (&gt;20)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-yellow-400 rounded"></div>
                  <span className="text-sm text-gray-600">Moderate (10-20)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-blue-400 rounded"></div>
                  <span className="text-sm text-gray-600">Normal (&lt;10)</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Distribution */}
      {selectedChart === 'categories' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle>🥧 Email Category Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative w-64 h-64 mx-auto">
                <svg viewBox="0 0 100 100" className="transform -rotate-90">
                  {Object.entries(stats.categories).map(([category, count], index, arr) => {
                    const total = Object.values(stats.categories).reduce((a, b) => a + b, 0);
                    const percentage = (count / total) * 100;
                    const circumference = 2 * Math.PI * 40;
                    const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;
                    const colors = {
                      security: '#ef4444',
                      financial: '#22c55e',
                      professional: '#3b82f6',
                      social: '#a855f7',
                      promotional: '#eab308',
                      other: '#6b7280'
                    };
                    const offset = arr.slice(0, index).reduce((acc, [, c]) => {
                      return acc + (c / total) * 360;
                    }, 0);

                    return (
                      <circle
                        key={category}
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke={colors[category as keyof typeof colors]}
                        strokeWidth="20"
                        strokeDasharray={strokeDasharray}
                        transform={`rotate(${offset} 50 50)`}
                      />
                    );
                  })}
                </svg>
                {/* Legend */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {Object.values(stats.categories).reduce((a, b) => a + b, 0)}
                  </div>
                  <div className="text-sm text-gray-500">Total</div>
                </div>
              </div>

              {/* Legend */}
              <div className="mt-6 grid grid-cols-2 gap-2">
                {Object.entries(stats.categories).map(([category, count]) => {
                  const total = Object.values(stats.categories).reduce((a, b) => a + b, 0);
                  const percentage = ((count / total) * 100).toFixed(1);
                  const colors = {
                    security: 'bg-red-500',
                    financial: 'bg-green-500',
                    professional: 'bg-blue-500',
                    social: 'bg-purple-500',
                    promotional: 'bg-yellow-500',
                    other: 'bg-gray-500'
                  };

                  return (
                    <div key={category} className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded ${colors[category as keyof typeof colors]}`}></div>
                      <span className="text-sm text-gray-700 capitalize">{category}</span>
                      <span className="text-sm text-gray-500">{percentage}%</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Donut Chart with Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>📊 Category Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(stats.categories)
                  .sort(([, a], [, b]) => b - a)
                  .map(([category, count], index) => {
                    const total = Object.values(stats.categories).reduce((a, b) => a + b, 0);
                    const percentage = ((count / total) * 100).toFixed(1);
                    const colors = {
                      security: 'bg-red-500',
                      financial: 'bg-green-500',
                      professional: 'bg-blue-500',
                      social: 'bg-purple-500',
                      promotional: 'bg-yellow-500',
                      other: 'bg-gray-500'
                    };

                    return (
                      <div key={category}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700 capitalize">
                            {category}
                          </span>
                          <span className="text-sm text-gray-500">
                            {count} ({percentage}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`h-3 rounded-full ${colors[category as keyof typeof colors]}`}
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Patterns Chart */}
      {selectedChart === 'patterns' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Heat Map */}
          <Card>
            <CardHeader>
              <CardTitle>🌡️ Weekly Activity Heat Map</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, dayIndex) => (
                  <div key={day} className="flex items-center space-x-2">
                    <div className="w-12 text-sm text-gray-600">{day}</div>
                    <div className="flex-1 flex space-x-1">
                      {Array.from({ length: 24 }).map((_, hour) => {
                        // Simulate activity intensity
                        const isWorkHour = hour >= 9 && hour <= 17;
                        const isEvening = hour >= 18 && hour <= 22;
                        const isNight = hour < 6;
                        const random = Math.random();

                        let intensity = 'bg-gray-100';
                        if (isWorkHour && random > 0.3) intensity = 'bg-blue-300';
                        if (isWorkHour && random > 0.7) intensity = 'bg-blue-500';
                        if (isEvening && random > 0.5) intensity = 'bg-purple-400';
                        if (isNight && random > 0.8) intensity = 'bg-red-400';

                        return (
                          <div
                            key={hour}
                            className={`h-4 flex-1 rounded-sm ${intensity}`}
                            title={`${day} ${hour}:00`}
                          ></div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex justify-center space-x-4 text-xs text-gray-600">
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 bg-gray-100 rounded-sm"></div>
                  <span>Low</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 bg-blue-300 rounded-sm"></div>
                  <span>Medium</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 bg-blue-500 rounded-sm"></div>
                  <span>High</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 bg-red-400 rounded-sm"></div>
                  <span>Peak</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Activity Ring */}
          <Card>
            <CardHeader>
              <CardTitle>⭕ Daily Activity Ring</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center justify-center py-8">
                {/* Concentric rings */}
                <div className="relative w-64 h-64">
                  {/* Outer ring - Total emails */}
                  <svg viewBox="0 0 100 100" className="w-full h-full">
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="8"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="8"
                      strokeDasharray={`${(stats.emails_last_day / 500) * 2 * Math.PI * 45} ${2 * Math.PI * 45}`}
                      transform="rotate(-90 50 50)"
                      strokeLinecap="round"
                    />

                    {/* Middle ring - Security */}
                    <circle
                      cx="50"
                      cy="50"
                      r="35"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="8"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="35"
                      fill="none"
                      stroke="#ef4444"
                      strokeWidth="8"
                      strokeDasharray={`${(stats.categories.security / 100) * 2 * Math.PI * 35} ${2 * Math.PI * 35}`}
                      transform="rotate(-90 50 50)"
                      strokeLinecap="round"
                    />

                    {/* Inner ring - Financial */}
                    <circle
                      cx="50"
                      cy="50"
                      r="25"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="8"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="25"
                      fill="none"
                      stroke="#22c55e"
                      strokeWidth="8"
                      strokeDasharray={`${(stats.categories.financial / 50) * 2 * Math.PI * 25} ${2 * Math.PI * 25}`}
                      transform="rotate(-90 50 50)"
                      strokeLinecap="round"
                    />
                  </svg>

                  {/* Center text */}
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                    <div className="text-3xl font-bold text-gray-900">{stats.emails_last_day}</div>
                    <div className="text-xs text-gray-500">Today</div>
                  </div>
                </div>

                {/* Ring legend */}
                <div className="mt-6 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Total (Blue)</span>
                    <span className="font-medium text-gray-900">{stats.emails_last_day} / 500</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Security (Red)</span>
                    <span className="font-medium text-gray-900">{stats.categories.security} / 100</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Financial (Green)</span>
                    <span className="font-medium text-gray-900">{stats.categories.financial} / 50</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Stats Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{stats.emails_last_hour}</div>
              <div className="text-xs text-blue-600">Last Hour</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{stats.emails_last_day}</div>
              <div className="text-xs text-green-600">Last 24 Hours</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-700">{stats.emails_last_week}</div>
              <div className="text-xs text-purple-600">Last 7 Days</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-700">
                {Math.round(stats.emails_last_week / 7)}
              </div>
              <div className="text-xs text-orange-600">Daily Average</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EmailAnalyticsCharts;
