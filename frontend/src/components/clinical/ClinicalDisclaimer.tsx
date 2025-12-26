import React from 'react';
import { Alert } from '@/components/ui/Alert';

interface ClinicalDisclaimerProps {
  variant?: 'info' | 'warning';
  compact?: boolean;
}

const ClinicalDisclaimer: React.FC<ClinicalDisclaimerProps> = ({
  variant = 'info',
  compact = false,
}) => {
  if (compact) {
    return (
      <Alert variant="info" className="text-xs">
        <p>
          <strong>Disclaimer:</strong> This screening tool is not a diagnostic instrument.
          Please discuss results with a qualified healthcare provider.
        </p>
      </Alert>
    );
  }

  return (
    <Alert variant="info" className="mt-8">
      <Alert.Heading>Important Medical Disclaimer</Alert.Heading>
      <div className="mt-4 space-y-3">
        <p>
          <strong>This screening tool is NOT a diagnostic instrument.</strong> It's designed to help
          identify potential symptoms that may be associated with certain mental health conditions.
        </p>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">What this tool CAN do:</h4>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li>Help you identify symptoms that may need attention</li>
            <li>Track changes in your mental health over time</li>
            <li>Provide information about mental health resources</li>
            <li>Facilitate conversations with healthcare providers</li>
          </ul>
        </div>

        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <h4 className="font-semibold mb-2">What this tool CANNOT do:</h4>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            <li>Diagnose mental health conditions</li>
            <li>Replace professional medical evaluation</li>
            <li>Provide treatment recommendations</li>
            <li>Address crisis situations (call emergency services instead)</li>
          </ul>
        </div>

        <div className="mt-4">
          <h4 className="font-semibold mb-2">When to seek immediate help:</h4>
          <p className="text-sm text-gray-700">
            Call emergency services (911) or go to the nearest emergency room if you:
          </p>
          <ul className="list-disc list-inside text-sm text-red-700 font-medium mt-2 space-y-1">
            <li>Have thoughts of harming yourself or others</li>
            <li>Are experiencing severe symptoms that interfere with daily functioning</li>
            <li>Are in immediate danger or need urgent medical attention</li>
          </ul>
        </div>

        <div className="mt-6 pt-6 border-t">
          <p className="text-sm text-gray-600 italic">
            <strong>Professional Guidance:</strong> Please discuss your screening results with a qualified
            healthcare provider, such as your primary care physician, psychiatrist, psychologist, or
            licensed therapist. They can provide proper diagnosis, treatment planning, and ongoing care.
          </p>
        </div>

        <div className="mt-4 text-xs text-gray-500">
          <p>
            <strong>Confidentiality Notice:</strong> Your responses are confidential and protected under
            HIPAA privacy regulations. They may be shared with authorized healthcare providers
            involved in your care for treatment purposes.
          </p>
        </div>
      </div>
    </Alert>
  );
};

export default ClinicalDisclaimer;