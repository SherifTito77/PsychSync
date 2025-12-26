import React from 'react';
import { useParams, Navigate } from 'react-router-dom';
import DASS21Assessment from './DASS21Assessment';
import PCL5Assessment from './PCL5Assessment';
import AUDITAssessment from './AUDITAssessment';
import ClinicalConsent from '../ClinicalConsent';

const AssessmentRouter: React.FC = () => {
  const { tool } = useParams<{ tool: string }>();

  // Map tool types to their respective assessment components
  const getAssessmentComponent = () => {
    switch (tool) {
      case 'dass21':
        return <DASS21Assessment />;
      case 'pcl5':
        return <PCL5Assessment />;
      case 'audit':
        return <AUDITAssessment />;
      case 'phq9':
      case 'gad7':
      case 'stress':
      case 'wellbeing':
        // For general tools, use the consent flow
        return <ClinicalConsent />;
      default:
        // Redirect to assessments page if tool is not recognized
        return <Navigate to="/clinical-assessments" replace />;
    }
  };

  return (
    <>
      {getAssessmentComponent()}
    </>
  );
};

export default AssessmentRouter;