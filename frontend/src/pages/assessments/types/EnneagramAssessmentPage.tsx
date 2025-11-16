// frontend/src/pages/assessments/types/EnneagramAssessmentPage.tsx
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
const EnneagramAssessmentPage: React.FC = () => {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const questions = [
    "I focus on being good, right, and perfect.",
    "I often strive to be helpful and appreciated by others.",
    "I’m driven to succeed and be admired for my achievements.",
    "I want to understand myself and the world deeply.",
    "I seek uniqueness and authenticity.",
    "I focus on security, planning, and preparation.",
    "I enjoy fun, excitement, and new experiences.",
    "I take charge and seek control of situations.",
    "I value peace, harmony, and comfort.",
  ];
  const handleAnswer = (value: number) => {
    setAnswers([...answers, value]);
    if (currentQuestion + 1 < questions.length) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      alert("Assessment complete! Thank you.");
    }
  };
  return (
    <div className="max-w-2xl mx-auto py-10">
      <h1 className="text-2xl font-semibold mb-4 text-center">
        Enneagram Personality Assessment
      </h1>
      <div className="border rounded-xl p-6 shadow-sm bg-white">
        <p className="text-lg mb-6 text-center">
          {questions[currentQuestion]}
        </p>
        <div className="flex justify-center gap-4">
          {[1, 2, 3, 4, 5].map((val) => (
            <Button
              key={val}
              onClick={() => handleAnswer(val)}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            >
              {val}
            </Button>
          ))}
        </div>
        <p className="text-sm mt-6 text-center text-gray-500">
          Question {currentQuestion + 1} of {questions.length}
        </p>
      </div>
    </div>
  );
};
export default EnneagramAssessmentPage;
