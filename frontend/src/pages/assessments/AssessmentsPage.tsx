// File: frontend/src/pages/assessments/AssessmentsPage.tsx
import React from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/common/card";
import  Button  from "../../components/common/Button";
const AssessmentsPage: React.FC = () => {
  const navigate = useNavigate();
  const assessments = [
    {
      id: "mbti",
      title: "MBTI Assessment",
      description: "Myers-Briggs Type Indicator - Understand your personality preferences",
      status: "Available",
      icon: "🧭",
    },
    {
      id: "bigfive",
      title: "Big Five Personality",
      description: "Five-factor model of personality traits",
      status: "Completed",
      icon: "📊",
    },
    {
      id: "enneagram",
      title: "Enneagram",
      description: "Nine personality types and their motivations",
      status: "Available",
      icon: "⭐",
    },
    {
      id: "strengths",
      title: "StrengthsFinder",
      description: "Discover your top 5 strengths and talents",
      status: "In Progress",
      icon: "💪",
    },
    {
      id: "disc",
      title: "DISC Assessment",
      description: "Behavioral assessment for communication styles",
      status: "Available",
      icon: "🎯",
    },
    {
      id: "predictive_index",
      title: "Predictive Index",
      description: "Behavioral drives and motivations",
      status: "Available",
      icon: "🔮",
    },
  ];
  const handleAssessmentClick = (id: string, status: string) => {
    // Navigate based on assessment state
    if (status === "Completed") {
      navigate(`/assessments/${id}/results`);
    } else if (status === "In Progress") {
      navigate(`/assessments/${id}/continue`);
    } else {
      navigate(`/assessments/${id}/start`);
    }
  };
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Personality Assessments</h1>
      <p className="text-gray-600 mb-10">
        Complete assessments to build your comprehensive personality profile.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {assessments.map((assessment) => (
          <Card key={assessment.id} className="p-5 shadow-md hover:shadow-xl transition-all">
            <div className="text-4xl mb-3">{assessment.icon}</div>
            <h2 className="text-xl font-semibold mb-2">{assessment.title}</h2>
            <p className="text-sm text-gray-500 mb-4">{assessment.description}</p>
            <div className="flex justify-between items-center">
              <span
                className={`px-2 py-1 rounded text-xs ${
                  assessment.status === "Completed"
                    ? "bg-green-100 text-green-700"
                    : assessment.status === "In Progress"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-blue-100 text-blue-700"
                }`}
              >
                {assessment.status}
              </span>
              <Button
                variant="default"
                onClick={() => handleAssessmentClick(assessment.id, assessment.status)}
              >
                {assessment.status === "Completed"
                  ? "View Results"
                  : assessment.status === "In Progress"
                  ? "Continue"
                  : "Start Assessment"}
              </Button>
            </div>
          </Card>
        ))}
      </div>
      <div className="mt-10 p-4 border-t">
        <h3 className="text-lg font-semibold mb-2">💡 Complete Multiple Assessments</h3>
        <p className="text-gray-600">
          Taking multiple assessments gives you a more comprehensive and accurate personality
          profile. Our AI combines insights from different frameworks to provide better team
          optimization recommendations.
        </p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate("/about/our-approach")}
        >
          Learn More About Our Approach
        </Button>
      </div>
    </div>
  );
};
export default AssessmentsPage;
