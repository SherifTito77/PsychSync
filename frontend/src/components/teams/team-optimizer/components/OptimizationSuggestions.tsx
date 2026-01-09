/**
 * Optimization Suggestions Component
 *
 * Displays optimization recommendations, risks, and improvement opportunities
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Lightbulb, CheckCircle, AlertTriangle } from 'lucide-react';
import { OptimizationResult } from '../types';

interface OptimizationSuggestionsProps {
  result: OptimizationResult;
}

export const OptimizationSuggestions: React.FC<OptimizationSuggestionsProps> = ({ result }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          Recommendations & Insights
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold mb-3 text-green-600">Recommendations</h4>
            <ul className="space-y-2">
              {result.recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-orange-600">Risk Factors</h4>
            <ul className="space-y-2">
              {result.riskFactors.map((risk, index) => (
                <li key={index} className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-semibold mb-2 text-blue-800">Improvement Opportunities</h4>
          <ul className="space-y-1">
            {result.improvementOpportunities.map((opportunity, index) => (
              <li key={index} className="text-sm text-blue-700">
                • {opportunity}
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
