import React, { Suspense } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";

// Use simplified assessment pages to avoid loading issues
import MBTIAssessmentPageSimple from "../assessments/types/MBTIAssessmentPageSimple";
import BigFiveAssessmentPage from "../assessments/types/BigFiveAssessmentPage";
import EnneagramAssessmentPage from "../assessments/types/EnneagramAssessmentPage";
import StrengthsFinderPage from "../assessments/types/StrengthsFinderPage";
import PredictiveIndexPage from "../assessments/types/PredictiveIndexPage";
import DISCAssessmentPage from "../assessments/types/DISCAssessmentPage";
import SocialStylesPage from "../assessments/types/SocialStylesPage";

const AssessmentStartPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Route to specific assessment components
  if (id === 'mbti') {
    return <MBTIAssessmentPageSimple />;
  }

  if (id === 'big_five') {
    return <BigFiveAssessmentPage />;
  }

  if (id === 'enneagram') {
    return <EnneagramAssessmentPage />;
  }

  if (id === 'strengthsfinder') {
    return <StrengthsFinderPage />;
  }

  if (id === 'predictive_index') {
    return <PredictiveIndexPage />;
  }

  if (id === 'disc') {
    return <DISCAssessmentPage />;
  }

  if (id === 'social-styles') {
    return <SocialStylesPage />;
  }

  // For other assessments, show the generic placeholder
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4 capitalize">
        Start {id} Assessment
      </h1>
      <p className="text-gray-600 mb-6">
        This page will load the assessment questions for <strong>{id}</strong>.
        You can integrate your backend API here to dynamically fetch the
        assessment data.
      </p>
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <p className="text-yellow-800 text-sm">
          <strong>Note:</strong> For assessments other than MBTI, you'll need to implement the specific assessment component.
        </p>
      </div>
      <Button variant="default" onClick={() => navigate(`/assessments/${id}/results`)}>
        Go to Results
      </Button>
    </div>
  );
};

export default AssessmentStartPage;
