// File: src/pages/assessments/types/EnneagramAssessmentPage.tsx
import React from "react";
import { useNavigate } from "react-router-dom";
import Button from "@/components/common/Button";
const EnneagramAssessmentPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">Enneagram Assessment</h1>
      <p className="text-gray-600 mb-6">
        Discover your Enneagram type and understand your motivations and growth paths.
      </p>
      <Button onClick={() => navigate("/assessments/enneagram/start")}>
        Start Enneagram Assessment
      </Button>
    </div>
  );
};
export default EnneagramAssessmentPage;
