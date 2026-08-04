import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import api from '@/services/api';
import { Flame, Zap, Snowflake } from 'lucide-react';

interface ZoneHistoryEntry {
  date: string;
  zone: string;
  pattern_count: number;
  critical_patterns: number;
}

interface ZoneHistoryChartProps {
  organizationId: string;
  teamId?: string;
}

export const ZoneHistoryChart: React.FC<ZoneHistoryChartProps> = ({
  organizationId,
  teamId
}) => {
  const [loading, setLoading] = useState(true);
  const [historyData, setHistoryData] = useState<ZoneHistoryEntry[]>([]);

  useEffect(() => {
    loadZoneHistory();
  }, [organizationId, teamId]);

  const loadZoneHistory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        organization_id: organizationId,
        days_back: '90',
      });

      if (teamId) {
        params.append('team_id', teamId);
      }

      const response = await api.get(`/radar/zone-history?${params.toString()}`);

      if (response.data && response.data.zone_history) {
        setHistoryData(response.data.zone_history);
      }
    } catch (error) {
      console.error('Error loading zone history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getZoneColor = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return '#ef4444';
      case 'yellow': return '#f59e0b';
      case 'green': return '#22c55e';
      default: return '#9ca3af';
    }
  };

  const getZoneIcon = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return <Flame className="h-4 w-4" />;
      case 'yellow': return <Zap className="h-4 w-4" />;
      case 'green': return <Snowflake className="h-4 w-4" />;
      default: return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (historyData.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg font-medium">No historical data available</p>
        <p className="text-sm">Zone history will appear here as data accumulates</p>
      </div>
    );
  }

  // Calculate chart dimensions
  const chartHeight = 300;
  const chartWidth = 800;
  const padding = { top: 20, right: 30, bottom: 60, left: 60 };
  const effectiveHeight = chartHeight - padding.top - padding.bottom;
  const effectiveWidth = chartWidth - padding.left - padding.right;

  // Find max patterns for scaling
  const maxPatterns = Math.max(...historyData.map(d => d.pattern_count), 1);

  // Get unique dates for x-axis
  const dates = historyData.map(d => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));

  return (
    <div className="space-y-4">
      {/* Summary Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <Flame className="h-4 w-4 text-red-600" />
            <p className="text-sm font-medium text-red-800">Red Zone Days</p>
          </div>
          <p className="text-2xl font-bold text-red-900">
            {historyData.filter(d => d.zone === 'red').length}
          </p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <Zap className="h-4 w-4 text-yellow-600" />
            <p className="text-sm font-medium text-yellow-800">Yellow Zone Days</p>
          </div>
          <p className="text-2xl font-bold text-yellow-900">
            {historyData.filter(d => d.zone === 'yellow').length}
          </p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center space-x-2 mb-1">
            <Snowflake className="h-4 w-4 text-green-600" />
            <p className="text-sm font-medium text-green-800">Green Zone Days</p>
          </div>
          <p className="text-2xl font-bold text-green-900">
            {historyData.filter(d => d.zone === 'green').length}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full h-auto"
          style={{ maxHeight: `${chartHeight}px` }}
        >
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].forEach(tick => {
            const y = padding.top + effectiveHeight * (1 - tick);
            return (
              <g key={tick}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-gray-600 text-xs"
                >
                  {Math.round(maxPatterns * tick)}
                </text>
              </g>
            );
          })}

          {/* Zone background bands */}
          <rect
            x={padding.left}
            y={padding.top + effectiveHeight * 0.6}
            width={effectiveWidth}
            height={effectiveHeight * 0.4}
            fill="rgba(239, 68, 68, 0.05)"
          />
          <rect
            x={padding.left}
            y={padding.top + effectiveHeight * 0.3}
            width={effectiveWidth}
            height={effectiveHeight * 0.3}
            fill="rgba(245, 158, 11, 0.05)"
          />
          <rect
            x={padding.left}
            y={padding.top}
            width={effectiveWidth}
            height={effectiveHeight * 0.3}
            fill="rgba(34, 197, 94, 0.05)"
          />

          {/* Data line */}
          <polyline
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            points={historyData.map((d, i) => {
              const x = padding.left + (i / (historyData.length - 1)) * effectiveWidth;
              const y = padding.top + effectiveHeight * (1 - d.pattern_count / maxPatterns);
              return `${x},${y}`;
            }).join(' ')}
          />

          {/* Data points with zone colors */}
          {historyData.map((d, i) => {
            const x = padding.left + (i / (historyData.length - 1)) * effectiveWidth;
            const y = padding.top + effectiveHeight * (1 - d.pattern_count / maxPatterns);

            return (
              <g key={i}>
                {/* Zone indicator */}
                <circle
                  cx={x}
                  cy={y}
                  r="8"
                  fill={getZoneColor(d.zone)}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => {
                    // Show tooltip or details
                    console.log('Clicked data point:', d);
                  }}
                />

                {/* Date labels (every 10th label to avoid crowding) */}
                {i % Math.ceil(historyData.length / 10) === 0 && (
                  <text
                    x={x}
                    y={chartHeight - padding.bottom + 20}
                    textAnchor="middle"
                    className="fill-gray-600 text-xs"
                  >
                    {dates[i]}
                  </text>
                )}
              </g>
            );
          })}

          {/* X-axis label */}
          <text
            x={chartWidth / 2}
            y={chartHeight - 10}
            textAnchor="middle"
            className="fill-gray-700 text-sm font-medium"
          >
            Date
          </text>

          {/* Y-axis label */}
          <text
            x={20}
            y={chartHeight / 2}
            textAnchor="middle"
            transform={`rotate(-90, 20, ${chartHeight / 2})`}
            className="fill-gray-700 text-sm font-medium"
          >
            Pattern Count
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 pt-4 border-t">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span className="text-sm">Green Zone (Healthy)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
          <span className="text-sm">Yellow Zone (Caution)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-red-500"></div>
          <span className="text-sm">Red Zone (Critical)</span>
        </div>
      </div>
    </div>
  );
};
