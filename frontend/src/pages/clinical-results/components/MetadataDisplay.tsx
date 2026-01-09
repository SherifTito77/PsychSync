/**
 * Assessment Metadata Display Component
 *
 * Displays assessment details like completion time, provider notification status, etc.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { AssessmentMetadata } from '../types';

interface MetadataDisplayProps {
  metadata: AssessmentMetadata | null;
}

export const MetadataDisplay: React.FC<MetadataDisplayProps> = ({ metadata }) => {
  if (!metadata) return null;

  return (
    <Card className="mb-8 bg-blue-50 border-blue-200">
      <CardHeader>
        <CardTitle className="text-blue-900">Assessment Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {metadata.responseData && (
            <div>
              <h4 className="font-semibold text-blue-900 mb-2">Completion Information</h4>
              <div className="space-y-1 text-gray-700">
                {metadata.responseData.duration && (
                  <p>• Time to complete: {metadata.responseData.duration}</p>
                )}
                {metadata.responseData.questions_answered && (
                  <p>• Questions answered: {metadata.responseData.questions_answered}</p>
                )}
                {metadata.responseData.skipped_questions !== undefined && (
                  <p>• Questions skipped: {metadata.responseData.skipped_questions}</p>
                )}
              </div>
            </div>
          )}

          <div>
            <h4 className="font-semibold text-blue-900 mb-2">Status & Follow-up</h4>
            <div className="space-y-1 text-gray-700">
              {metadata.providerNotified !== undefined && (
                <p>• Provider notified: {metadata.providerNotified ? 'Yes' : 'No'}</p>
              )}
              {metadata.nextAssessmentDate && (
                <p>• Next assessment: {new Date(metadata.nextAssessmentDate).toLocaleDateString()}</p>
              )}
            </div>
          </div>

          {metadata.notes && (
            <div className="md:col-span-2">
              <h4 className="font-semibold text-blue-900 mb-2">Notes</h4>
              <p className="text-gray-700 italic">{metadata.notes}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
