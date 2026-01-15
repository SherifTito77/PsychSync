/**
 * Results Header Component
 *
 * Displays the assessment header with title, back button, and metadata.
 */

import React from 'react';
import { Button } from '@/components/ui/button';

interface ResultsHeaderProps {
  tool: string | undefined;
  metadata: {
    completedAt: string;
    assessmentId?: string;
  } | null;
  onBack: () => void;
}

export const ResultsHeader: React.FC<ResultsHeaderProps> = ({ tool, metadata, onBack }) => {
  return (
    <div className="mb-8">
      <Button
        variant="ghost"
        onClick={onBack}
        className="mb-4"
      >
        ← Back to Assessments
      </Button>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Assessment Results
      </h1>
      <div className="flex items-center justify-between">
        <p className="text-lg text-gray-600">
          {tool?.toUpperCase()} - Completed on{' '}
          {metadata?.completedAt
            ? new Date(metadata.completedAt).toLocaleDateString()
            : new Date().toLocaleDateString()
          }
        </p>
        {metadata?.assessmentId && (
          <p className="text-sm text-gray-500">
            ID: {metadata.assessmentId}
          </p>
        )}
      </div>
    </div>
  );
};
