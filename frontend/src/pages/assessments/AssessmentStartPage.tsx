import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
const AssessmentStartPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
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
      <Button variant="default" onClick={() => navigate(`/assessments/${id}/results`)}>
        Submit and View Results
      </Button>
    </div>
  );
};
export default AssessmentStartPage;
