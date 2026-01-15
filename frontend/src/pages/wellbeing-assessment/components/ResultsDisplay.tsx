/**
 * Wellbeing Results Display Component
 *
 * Displays overall wellbeing score and category breakdown.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CategoryScore } from '../types';

interface ResultsDisplayProps {
  overallPercentage: number;
  categoryScores: CategoryScore[];
  onRetake: () => void;
  onDashboard: () => void;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  overallPercentage,
  categoryScores,
  onRetake,
  onDashboard,
}) => {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'low':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case 'high':
        return 'High Wellbeing';
      case 'medium':
        return 'Moderate Wellbeing';
      case 'low':
        return 'Low Wellbeing';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Overall Score */}
      <Card className="bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200">
        <CardHeader>
          <CardTitle className="text-center">Your Overall Wellbeing</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center">
            <div className="text-6xl font-bold text-purple-600 mb-4">
              {overallPercentage}%
            </div>
            <div className="text-lg text-gray-700 mb-4">
              {getLevelLabel(
                overallPercentage >= 70 ? 'high' : overallPercentage >= 40 ? 'medium' : 'low'
              )}
            </div>
            <p className="text-sm text-gray-600 max-w-2xl mx-auto">
              This assessment measures your wellbeing across 7 dimensions: Physical,
              Emotional, Social, Work, Purpose, Financial, and Self-Care.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Category Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Category Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {categoryScores.map((category) => (
              <div key={category.category} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-900">{category.category}</h3>
                  <span
                    className={`px-2 py-1 text-xs rounded ${getLevelColor(category.level)}`}
                  >
                    {getLevelLabel(category.level)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${category.percentage}%` }}
                  />
                </div>
                <div className="text-sm text-gray-600">
                  {category.score} / {category.maxScore} points ({category.percentage}%)
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-center gap-4">
        <Button onClick={onRetake} variant="outline">
          Retake Assessment
        </Button>
        <Button onClick={onDashboard}>
          View Dashboard
        </Button>
      </div>
    </div>
  );
};
