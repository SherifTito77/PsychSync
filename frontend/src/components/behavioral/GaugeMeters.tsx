/**
 * Gauge Meters Component
 * Displays circular gauge charts for metrics and risk scores
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface GaugeMeterProps {
  value: number; // 0-100
  max: number;
  label: string;
  unit?: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
  showThresholds?: boolean;
  thresholds?: {
    warning: number;
    danger: number;
  };
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
  };
}

export const GaugeMeter: React.FC<GaugeMeterProps> = ({
  value,
  max = 100,
  label,
  unit = '%',
  color,
  size = 'md',
  showThresholds = true,
  thresholds = { warning: 50, danger: 75 },
  trend
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  const radius = size === 'sm' ? 40 : size === 'lg' ? 70 : 55;
  const strokeWidth = size === 'sm' ? 8 : size === 'lg' ? 12 : 10;
  const circumference = 2 * Math.PI * (radius - strokeWidth / 2);
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Determine color based on value and thresholds
  const getColor = () => {
    if (color) return color;
    if (percentage >= thresholds.danger) return '#ef4444'; // red
    if (percentage >= thresholds.warning) return '#f59e0b'; // orange
    return '#22c55e'; // green
  };

  const getStatus = () => {
    if (percentage >= thresholds.danger) return { label: 'Critical', variant: 'destructive' as const };
    if (percentage >= thresholds.warning) return { label: 'Warning', variant: 'outline' as const };
    return { label: 'Good', variant: 'secondary' as const };
  };

  const sizeClasses = {
    sm: { container: 'w-32 h-32', text: 'text-lg' },
    md: { container: 'w-48 h-48', text: 'text-2xl' },
    lg: { container: 'w-64 h-64', text: 'text-4xl' }
  };

  const status = getStatus();
  const gaugeColor = getColor();

  return (
    <div className="flex flex-col items-center space-y-3">
      <div className={`relative ${sizeClasses[size].container}`}>
        <svg className="transform -rotate-90" width={radius * 2} height={radius * 2}>
          {/* Background circle */}
          <circle
            cx={radius}
            cy={radius}
            r={radius - strokeWidth / 2}
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
            fill="none"
          />

          {/* Progress circle */}
          <circle
            cx={radius}
            cy={radius}
            r={radius - strokeWidth / 2}
            stroke={gaugeColor}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-in-out"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`${sizeClasses[size].text} font-bold text-gray-900`}>
            {value.toFixed(0)}
          </span>
          {unit && <span className="text-xs text-gray-600">{unit}</span>}
          {trend && (
            <div className={`text-xs font-medium flex items-center ${
              trend.direction === 'up' ? 'text-green-600' : trend.direction === 'down' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {trend.direction === 'up' && '↑'}
              {trend.direction === 'down' && '↓'}
              {trend.direction === 'stable' && '→'}
              {Math.abs(trend.value)}%
            </div>
          )}
        </div>
      </div>

      <div className="text-center">
        <div className="text-sm font-medium text-gray-700">{label}</div>
        {showThresholds && (
          <Badge variant={status.variant} className="mt-1">
            {status.label}
          </Badge>
        )}
      </div>
    </div>
  );
};

interface MultiGaugeProps {
  gauges: Array<{
    value: number;
    max: number;
    label: string;
    unit?: string;
    color?: string;
    thresholds?: { warning: number; danger: number };
  }>;
  title?: string;
  layout?: 'horizontal' | 'grid';
}

export const MultiGaugeDisplay: React.FC<MultiGaugeProps> = ({
  gauges,
  title,
  layout = 'grid'
}) => {
  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <CardContent>
        <div className={layout === 'horizontal' ? 'flex justify-around' : 'grid grid-cols-2 md:grid-cols-4 gap-6'}>
          {gauges.map((gauge, idx) => (
            <GaugeMeter
              key={idx}
              {...gauge}
              size="md"
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

interface WellnessRadarProps {
  data: {
    metric: string;
    value: number;
    max: number;
  }[];
  title?: string;
}

export const WellnessRadarGauge: React.FC<WellnessRadarProps> = ({ data, title }) => {
  const maxRadius = 100;
  const center = maxRadius;
  const numPoints = data.length;
  const angleStep = (2 * Math.PI) / numPoints;

  const calculatePoint = (index: number, value: number) => {
    const angle = angleStep * index - Math.PI / 2;
    const radius = (value / data[index].max) * (maxRadius - 20);
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle)
    };
  };

  const polygonPoints = data.map((d, i) => {
    const point = calculatePoint(i, d.value);
    return `${point.x},${point.y}`;
  }).join(' ');

  const backgroundPoints = data.map((d, i) => {
    const point = calculatePoint(i, d.max);
    return `${point.x},${point.y}`;
  }).join(' ');

  const labelPoints = data.map((d, i) => {
    const angle = angleStep * i - Math.PI / 2;
    const radius = maxRadius - 5;
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
      label: d.metric
    };
  });

  return (
    <Card>
      {title && (
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
      )}
      <CardContent>
        <div className="flex justify-center">
          <svg width={maxRadius * 2} height={maxRadius * 2} viewBox={`0 0 ${maxRadius * 2} ${maxRadius * 2}`}>
            {/* Background polygon */}
            <polygon
              points={backgroundPoints}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="2"
            />

            {/* Concentric circles for reference */}
            {[25, 50, 75, 100].map(radius => (
              <circle
                key={radius}
                cx={center}
                cy={center}
                r={(radius / 100) * (maxRadius - 20)}
                fill="none"
                stroke="#f3f4f6"
                strokeWidth="1"
              />
            ))}

            {/* Data polygon */}
            <polygon
              points={polygonPoints}
              fill="rgba(59, 130, 246, 0.2)"
              stroke="#3b82f6"
              strokeWidth="2"
            />

            {/* Data points */}
            {data.map((d, i) => {
              const point = calculatePoint(i, d.value);
              return (
                <circle
                  key={i}
                  cx={point.x}
                  cy={point.y}
                  r="4"
                  fill="#3b82f6"
                />
              );
            })}

            {/* Labels */}
            {labelPoints.map((point, i) => (
              <text
                key={i}
                x={point.x}
                y={point.y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-xs fill-gray-700 font-medium"
              >
                {point.label}
              </text>
            ))}
          </svg>
        </div>

        {/* Legend */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-2">
          {data.map((d, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{d.metric}</span>
              <Badge variant="outline">{d.value}/{d.max}</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
