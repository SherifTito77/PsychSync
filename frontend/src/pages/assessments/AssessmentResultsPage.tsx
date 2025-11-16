import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import  Button  from "../../components/common/Button";
const AssessmentResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4 capitalize">{id} Results</h1>
      <p className="text-gray-600 mb-6">
        This page shows the result summary for your <strong>{id}</strong>{" "}
        assessment. You’ll later connect this to the backend’s assessment results API.
      </p>
      <Button variant="outline" onClick={() => navigate("/assessments")}>
        Back to Assessments
      </Button>
    </div>
  );
};
export default AssessmentResultsPage;
