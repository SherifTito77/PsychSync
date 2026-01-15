/**
 * Clinical Results Page
 *
 * Main orchestrator component for clinical assessment results display.
 * This page has been split from a monolithic 1,928-line component into
 * manageable, focused sub-components and utilities.
 *
 * Architecture:
 * - Custom hooks manage data fetching and actions
 * - Utility functions handle business logic (severity, recommendations, resources)
 * - Sub-components handle specific UI sections
 * - This file coordinates everything together
 *
 * Before: 1,928 lines in one file
 * After:  <100 lines in this file + focused sub-components
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle } from '@/components/ui/alert';

// Custom hooks
import { useClinicalResults } from './hooks/useClinicalResults';
import { useClinicalActions } from './hooks/useClinicalActions';

// Sub-components
import { ResultsHeader } from './components/ResultsHeader';
import { SeverityBanner } from './components/SeverityBanner';
import { ScoreDisplay } from './components/ScoreDisplay';
import { RecommendationsList } from './components/RecommendationsList';
import { ResourcesGrid } from './components/ResourcesGrid';
import { MetadataDisplay } from './components/MetadataDisplay';

// Tool-specific educational content components
// These contain the large educational sections for each assessment type
import { PCL5Education } from './components/tool-education/PCL5Education';
import { DASS21Education } from './components/tool-education/DASS21Education';
import { AUDITEducation } from './components/tool-education/AUDITEducation';
import { PHQ9Education } from './components/tool-education/PHQ9Education';
import { GAD7Education } from './components/tool-education/GAD7Education';
import { StressEducation } from './components/tool-education/StressEducation';
import { WellbeingEducation } from './components/tool-education/WellbeingEducation';

/**
 * Loading state component
 */
const ResultsLoading = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading your results...</p>
    </div>
  </div>
);

/**
 * Error state component
 */
const ResultsError = ({ error }: { error: string | null }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <p className="text-red-600 mb-4">{error || 'Failed to load results'}</p>
      <Button onClick={() => window.location.reload()}>Try Again</Button>
    </div>
  </div>
);

/**
 * No results component
 */
const NoResults = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <p className="text-gray-600 mb-4">Results not found</p>
      <Button onClick={() => window.location.href = '/clinical-assessments'}>
        Back to Assessments
      </Button>
    </div>
  </div>
);

/**
 * Main Clinical Results Component
 */
const ClinicalResults: React.FC = () => {
  const { tool } = useParams<{ tool: string }>();

  // Data fetching hook
  const { result, metadata, loading, error } = useClinicalResults(tool);

  // Action handlers hook
  const { saving, handleSave, handleShareWithProvider, handleRetakeAssessment, handleBackToAssessments } =
    useClinicalActions();

  // Loading state
  if (loading) {
    return <ResultsLoading />;
  }

  // Error state
  if (error) {
    return <ResultsError error={error} />;
  }

  // No results state
  if (!result) {
    return <NoResults />;
  }

  const { score, severity, crisisAlert, recommendations, resources } = result;

  /**
   * Render tool-specific educational content
   */
  const renderToolEducation = () => {
    switch (tool) {
      case 'pcl5':
        return <PCL5Education score={score} severity={severity} />;
      case 'dass21':
        return <DASS21Education score={score} severity={severity} />;
      case 'audit':
        return <AUDITEducation score={score} severity={severity} />;
      case 'phq9':
        return <PHQ9Education score={score} severity={severity} />;
      case 'gad7':
        return <GAD7Education score={score} severity={severity} />;
      case 'stress':
        return <StressEducation score={score} severity={severity} />;
      case 'wellbeing':
        return <WellbeingEducation score={score} severity={severity} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with back button and metadata */}
        <ResultsHeader tool={tool} metadata={metadata} onBack={handleBackToAssessments} />

        {/* Crisis alert banner */}
        <SeverityBanner crisisAlert={crisisAlert} />

        {/* Assessment metadata */}
        <MetadataDisplay metadata={metadata} />

        {/* Main score display */}
        <ScoreDisplay result={result} />

        {/* Tool-specific educational content */}
        {renderToolEducation()}

        {/* Recommendations */}
        <RecommendationsList recommendations={recommendations} />

        {/* Resources */}
        <ResourcesGrid resources={resources} />

        {/* Action buttons */}
        <div className="flex flex-wrap gap-4 justify-center">
          <Button onClick={() => handleShareWithProvider(result)} variant="outline">
            Share with Provider
          </Button>
          <Button onClick={() => handleSave(result, tool)} disabled={saving}>
            {saving ? 'Saving...' : 'Save Results'}
          </Button>
          <Button onClick={() => handleRetakeAssessment(tool)} variant="outline">
            Retake Assessment
          </Button>
          <Button onClick={handleBackToAssessments}>
            Take Another Assessment
          </Button>
        </div>

        {/* Disclaimer */}
        <Alert variant="info" className="mt-8">
          <AlertTitle>Important Disclaimer</AlertTitle>
          <p className="mt-2 text-sm">
            This screening tool is not a diagnostic instrument. It's designed to help you identify
            symptoms that may be associated with certain mental health conditions. Please discuss
            your results with a qualified healthcare provider for proper diagnosis and treatment planning.
          </p>
        </Alert>
      </div>
    </div>
  );
};

export default ClinicalResults;
