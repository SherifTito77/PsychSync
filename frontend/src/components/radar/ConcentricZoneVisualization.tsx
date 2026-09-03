import React from 'react';
import { Flame, Zap, Snowflake, Shield } from 'lucide-react';

interface ConcentricZoneData {
  inner_zone: { name: string; risk_score: number; indicator_count: number; zone: string };
  middle_zone: { name: string; risk_score: number; health_score: number; zone: string };
  outer_zone: { name: string; risk_score: number; safety_score: number | null; zone: string };
}

interface ConcentricZoneVisualizationProps {
  zones: ConcentricZoneData;
}

export const ConcentricZoneVisualization: React.FC<ConcentricZoneVisualizationProps> = ({ zones }) => {
  const getZoneColor = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return { bg: 'rgba(239, 68, 68, 0.3)', border: '#ef4444', fill: '#ef4444' };
      case 'yellow': return { bg: 'rgba(245, 158, 11, 0.3)', border: '#f59e0b', fill: '#f59e0b' };
      case 'green': return { bg: 'rgba(34, 197, 94, 0.3)', border: '#22c55e', fill: '#22c55e' };
      default: return { bg: 'rgba(156, 163, 175, 0.3)', border: '#9ca3af', fill: '#9ca3af' };
    }
  };

  const getZoneIcon = (zone: string) => {
    switch (zone.toLowerCase()) {
      case 'red': return <Flame className="h-4 w-4" />;
      case 'yellow': return <Zap className="h-4 w-4" />;
      case 'green': return <Snowflake className="h-4 w-4" />;
      default: return <Shield className="h-4 w-4" />;
    }
  };

  const innerColor = getZoneColor(zones.inner_zone.zone);
  const middleColor = getZoneColor(zones.middle_zone.zone);
  const outerColor = getZoneColor(zones.outer_zone.zone);

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <svg viewBox="0 0 400 400" className="w-full h-auto">
        {/* Outer Zone - Organizational Health */}
        <circle
          cx="200"
          cy="200"
          r="190"
          fill={outerColor.bg}
          stroke={outerColor.border}
          strokeWidth="3"
          className="transition-all duration-500"
        />

        {/* Middle Zone - Team Dynamics */}
        <circle
          cx="200"
          cy="200"
          r="130"
          fill={middleColor.bg}
          stroke={middleColor.border}
          strokeWidth="3"
          className="transition-all duration-500"
        />

        {/* Inner Zone - Individual Behaviors */}
        <circle
          cx="200"
          cy="200"
          r="70"
          fill={innerColor.bg}
          stroke={innerColor.border}
          strokeWidth="3"
          className="transition-all duration-500"
        />

        {/* Labels */}
        <text x="200" y="30" textAnchor="middle" className="fill-gray-700 text-sm font-medium">
          {zones.outer_zone.name}
        </text>
        <text x="200" y="50" textAnchor="middle" className="fill-gray-600 text-xs">
          Risk: {((zones.outer_zone.risk_score) * 100).toFixed(0)}%
        </text>

        <text x="200" y="100" textAnchor="middle" className="fill-gray-700 text-sm font-medium">
          {zones.middle_zone.name}
        </text>
        <text x="200" y="120" textAnchor="middle" className="fill-gray-600 text-xs">
          Risk: {((zones.middle_zone.risk_score) * 100).toFixed(0)}%
        </text>

        <text x="200" y="200" textAnchor="middle" dominantBaseline="middle" className="fill-gray-700 text-sm font-medium">
          {zones.inner_zone.name}
        </text>

        {/* Zone Icons */}
        <foreignObject x="170" y="150" width="60" height="60">
          <div className="flex items-center justify-center h-full">
            {getZoneIcon(zones.inner_zone.zone)}
          </div>
        </foreignObject>
      </svg>

      {/* Legend */}
      <div className="absolute -right-4 top-0 space-y-2 bg-white p-4 rounded-lg shadow-lg">
        <h4 className="text-sm font-semibold mb-2">Zone Legend</h4>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span className="text-xs">Healthy (0-30%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
          <span className="text-xs">Caution (30-60%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-red-500"></div>
          <span className="text-xs">Critical (60-100%)</span>
        </div>
      </div>
    </div>
  );
};
