// Test component to verify WellnessAssessmentForm works in isolation
import React, { useState, useEffect } from 'react';
import WellnessAssessmentForm from './WellnessAssessmentForm';

const TestWellnessForm: React.FC = () => {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Wellness Assessment Test</h1>
      <p className="mb-4">Testing the WellnessAssessmentForm component:</p>
      <div className="border-2 border-gray-300 rounded-lg p-4 bg-white">
        <WellnessAssessmentForm />
      </div>
    </div>
  );
};

export default TestWellnessForm;