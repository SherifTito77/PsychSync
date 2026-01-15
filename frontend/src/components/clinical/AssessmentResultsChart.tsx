import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AssessmentResultsChartProps {
  score: number;
  maxScore: number;
  severity: {
    label: string;
    color: string;
    description: string;
    range: [number, number];
  };
  assessmentType: string;
  previousScore?: number;
}

const AssessmentResultsChart: React.FC<AssessmentResultsChartProps> = ({
  score,
  maxScore,
  severity,
  assessmentType,
  previousScore,
}) => {
  const getSeverityColor = (color: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'orange':
        return 'bg-orange-500';
      case 'red':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getSeverityBgColor = (color: string) => {
    switch (color) {
      case 'green':
        return 'bg-green-100 text-green-800';
      case 'yellow':
        return 'bg-yellow-100 text-yellow-800';
      case 'orange':
        return 'bg-orange-100 text-orange-800';
      case 'red':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const percentage = (score / maxScore) * 100;
  const severityStart = (severity.range[0] / maxScore) * 100;
  const severityEnd = (severity.range[1] / maxScore) * 100;

  const getImprovement = () => {
    if (previousScore === undefined) return null;
    const improvement = previousScore - score;
    if (improvement > 0) {
      return { text: `${improvement} points better`, color: 'text-green-600' };
    } else if (improvement < 0) {
      return { text: `${Math.abs(improvement)} points worse`, color: 'text-red-600' };
    } else {
      return { text: 'No change', color: 'text-gray-600' };
    }
  };

  const improvement = getImprovement();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{assessmentType} Results</span>
          {improvement && (
            <span className={`text-sm font-normal ${improvement.color}`}>
              {improvement.text}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Visual Score Display */}
        <div className="text-center mb-6">
          <div className="text-6xl font-bold text-gray-900 mb-2">{score}</div>
          <div className="text-gray-500">out of {maxScore}</div>
          <div className={`inline-block px-3 py-1 rounded-full text-white font-medium mt-3 ${getSeverityBgColor(severity.color)}`}>
            {severity.label}
          </div>
        </div>

        {/* Visual Progress Bar */}
        <div className="mb-6">
          <div className="relative">
            {/* Background bar */}
            <div className="w-full bg-gray-200 rounded-full h-8">
              {/* Severity range indicator */}
              <div
                className={`absolute h-8 ${getSeverityColor(severity.color)} opacity-30 rounded-full`}
                style={{
                  left: `${severityStart}%`,
                  width: `${severityEnd - severityStart}%`,
                }}
              />
              {/* Current score indicator */}
              <div
                className={`absolute h-8 ${getSeverityColor(severity.color)} rounded-full transition-all duration-500`}
                style={{ width: `${percentage}%` }}
              />
            </div>

            {/* Score markers */}
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>0</span>
              <span>{Math.round(maxScore * 0.25)}</span>
              <span>{Math.round(maxScore * 0.5)}</span>
              <span>{Math.round(maxScore * 0.75)}</span>
              <span>{maxScore}</span>
            </div>
          </div>
        </div>

        {/* Severity Description */}
        <div className={`p-4 rounded-lg ${getSeverityBgColor(severity.color)}`}>
          <h4 className="font-medium mb-2">What this means:</h4>
          <p className="text-sm">{severity.description}</p>
        </div>

        {/* Previous Score Comparison */}
        {previousScore !== undefined && (
          <div className="mt-4 pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Previous Score:</span>
              <span className="font-medium">{previousScore}</span>
            </div>
            <div className="flex items-center justify-between text-sm mt-1">
              <span className="text-gray-600">Current Score:</span>
              <span className="font-medium">{score}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AssessmentResultsChart;