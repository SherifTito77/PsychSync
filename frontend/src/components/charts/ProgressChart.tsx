import React from 'react';

interface ProgressChartProps {
  data: Array<{
    date: string;
    overall: number;
    physical: number;
    emotional: number;
    social: number;
    work: number;
    purpose: number;
    financial: number;
    selfCare: number;
  }>;
}

export const ProgressChart: React.FC<ProgressChartProps> = ({ data }) => {
  if (data.length < 2) {
    return (
      <div className="text-center p-8 bg-gray-50 rounded-lg">
        <p className="text-gray-600">Complete at least 2 assessments to see your progress trend</p>
      </div>
    );
  }

  const maxValue = 100;
  const minValue = 0;
  const chartHeight = 200;
  const chartWidth = 100;
  const padding = 10;

  // Get date labels
  const labels = data.map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  const categories = [
    { key: 'overall', color: '#8B5CF6', label: 'Overall' },
    { key: 'physical', color: '#10B981', label: 'Physical' },
    { key: 'emotional', color: '#6366F1', label: 'Emotional' },
    { key: 'social', color: '#F59E0B', label: 'Social' }
  ];

  return (
    <div className="bg-white p-3 rounded-lg border">
      <h3 className="font-bold text-sm mb-2">📈 Your Progress Over Time</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
        {categories.map(cat => (
          <div key={cat.key} className="border rounded p-2">
            <div className="flex items-center gap-1 mb-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: cat.color }}
              />
              <span className="font-medium text-xs">{cat.label}</span>
            </div>

            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="w-full h-16"
              preserveAspectRatio="none"
            >
              {/* Grid lines */}
              {[0, 25, 50, 75, 100].map(tick => (
                <line
                  key={tick}
                  x1={padding}
                  y1={chartHeight - padding - (tick / maxValue) * (chartHeight - 2 * padding)}
                  x2={chartWidth - padding}
                  y2={chartHeight - padding - (tick / maxValue) * (chartHeight - 2 * padding)}
                  stroke="#e5e7eb"
                  strokeWidth={0.5}
                />
              ))}

              {/* Data line */}
              <polyline
                points={data.map((d, i) => {
                  const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding);
                  const value = d[cat.key as keyof typeof d] as number;
                  const y = chartHeight - padding - (value / maxValue) * (chartHeight - 2 * padding);
                  return `${x},${y}`;
                }).join(' ')}
                fill="none"
                stroke={cat.color}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Data points */}
              {data.map((d, i) => {
                const x = padding + (i / (data.length - 1)) * (chartWidth - 2 * padding);
                const value = d[cat.key as keyof typeof d] as number;
                const y = chartHeight - padding - (value / maxValue) * (chartHeight - 2 * padding);
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r={2}
                    fill={cat.color}
                  />
                );
              })}
            </svg>

            {/* X-axis labels */}
            <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
              {labels.map((label, i) => (
                <span key={i}>{label}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="text-[10px] text-gray-500 text-center">
        Showing your last {data.length} assessments
      </div>
    </div>
  );
};
