import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Alert, AlertTitle } from '@/components/ui/Alert';

// Import ClinicalAssessment component for inline rendering
import ClinicalAssessment from './ClinicalAssessment';

// CSS fix for input blocking issues
const inputFixStyle = `
  input[type="checkbox"],
  input[type="radio"] {
    pointer-events: auto !important;
    z-index: 9999 !important;
    position: relative !important;
    opacity: 1 !important;
    visibility: visible !important;
  }
`;

interface ConsentSection {
  id: string;
  title: string;
  content: string;
  required: boolean;
}

// Helper function outside component to avoid initialization issues
const getToolName = (toolType: string): string => {
  const toolNames: Record<string, string> = {
    phq9: 'PHQ-9 Depression Screening',
    gad7: 'GAD-7 Anxiety Screening',
    stress: 'Perceived Stress Scale',
    wellbeing: 'Wellbeing Assessment',
  };
  return toolNames[toolType] || 'Mental Health Assessment';
};

// Consent sections defined outside component to prevent re-renders
const getConsentSections = (tool: string): ConsentSection[] => [
  {
    id: 'understanding',
    title: 'Understanding the Assessment',
    content: `I understand that this ${getToolName(tool)} is a screening tool, not a diagnostic tool.
    It helps identify potential symptoms but cannot replace professional medical evaluation.
    The results should be discussed with a qualified healthcare provider for proper diagnosis and treatment.`,
    required: true,
  },
  {
    id: 'voluntary',
    title: 'Voluntary Participation',
    content: 'I understand that my participation is completely voluntary. I can choose not to answer any question and can stop the assessment at any time without penalty.',
    required: true,
  },
  {
    id: 'confidentiality',
    title: 'Confidentiality and Privacy',
    content: 'I understand that my responses are confidential and will be stored securely. They may be shared with authorized healthcare providers involved in my care, and will be used for treatment planning and follow-up care. All data handling follows HIPAA privacy standards.',
    required: true,
  },
  {
    id: 'emergency',
    title: 'Emergency Situations',
    content: 'I understand that if my responses indicate immediate risk of harm to myself or others, clinical staff may need to take emergency action to ensure safety, which may include contacting emergency services or designated emergency contacts.',
    required: true,
  },
  {
    id: 'data_usage',
    title: 'Data Usage and Research',
    content: 'I understand that my anonymized data may be used for research purposes to improve mental health services and screening tools. No personally identifiable information will be shared without my explicit consent.',
    required: false,
  },
  {
    id: 'follow_up',
    title: 'Follow-up and Referrals',
    content: 'I understand that based on my assessment results, I may receive recommendations for follow-up care or referrals to mental health professionals. I can choose whether to pursue these recommendations.',
    required: true,
  },
];

const ClinicalConsent: React.FC = () => {
  const navigate = useNavigate();
  const { tool } = useParams<{ tool: string }>();
  const assessmentTool = tool || 'phq9';

  // Inject CSS to fix input blocking issues
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = inputFixStyle;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);
  const [loading, setLoading] = useState(false);
  const [agreements, setAgreements] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [consentVersion, setConsentVersion] = useState('1.0');
  const [showAssessment, setShowAssessment] = useState(false);

  // State monitoring

  const consentSections = useMemo(() => getConsentSections(assessmentTool), [assessmentTool]);

  useEffect(() => {
    // Initialize all required agreements to false
    const initialAgreements: Record<string, boolean> = {};
    consentSections.forEach(section => {
      initialAgreements[section.id] = false;
    });
    setAgreements(initialAgreements);

    // Add a test button directly to DOM to bypass React completely
    const testButton = document.createElement('button');
    testButton.textContent = '⚡ PURPLE TEST BUTTON';
    testButton.id = 'direct-dom-test-button';
    testButton.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 999999; padding: 20px; background: purple; color: white; border: 5px solid yellow; font-size: 16px; cursor: pointer;';
    testButton.onclick = () => {
      console.log('🟣 DIRECT DOM BUTTON CLICKED!');
      console.log('🟣 assessmentTool:', assessmentTool);
      let targetUrl = `/clinical/assessment/${assessmentTool}/take`;
      if (assessmentTool === 'stress') {
        targetUrl = '/test-stress-assessment';
      } else if (assessmentTool === 'wellbeing') {
        targetUrl = '/test-wellbeing-assessment';
      }
      console.log('🟣 Navigating to:', targetUrl);
      console.log('🟣 Using window.location.href (NO LOGIN!)');
      window.location.href = targetUrl;
    };
    document.body.appendChild(testButton);

    return () => {
      const existingButton = document.getElementById('direct-dom-test-button');
      if (existingButton) {
        document.body.removeChild(existingButton);
      }
    };
  }, [consentSections, assessmentTool, navigate]); // Run when consentSections changes (only when tool changes)

  const handleAgreementChange = (sectionId: string, agreed: boolean) => {
    setAgreements(prev => ({
      ...prev,
      [sectionId]: agreed,
    }));

    // Clear any errors when user agrees
    if (agreed) {
      setErrors(prev => prev.filter(error => error !== sectionId));
    }
  };

  const validateConsent = (): boolean => {
    const newErrors: string[] = [];

    consentSections.forEach(section => {
      if (section.required && !agreements[section.id]) {
        newErrors.push(section.id);
      }
    });

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleProceed = async () => {
    console.log('🔵 handleProceed called!');
    console.log('🔵 assessmentTool:', assessmentTool);

    const isValid = validateConsent();
    console.log('🔵 isValid:', isValid);

    if (!isValid) {
      console.log('🔴 Validation failed, returning');
      return;
    }

    setLoading(true);
    console.log('🔵 Loading set to true');

    // Navigate directly to assessment without API call for now
    // TODO: Re-enable API call once backend proxy is fixed
    console.log('🟢 Navigating to:', `/clinical/assessment/${assessmentTool}/take`);
    navigate(`/clinical/assessment/${assessmentTool}/take`);

    setLoading(false);
    console.log('🔵 Loading set to false, navigation complete');
  };

  const handleDecline = () => {
    navigate('/clinical-assessments');
  };

  const requiredAgreed = consentSections
    .filter(section => section.required)
    .every(section => agreements[section.id]);

  // Debug logging to help diagnose the issue
  console.log('=== CONSENT FORM DEBUG ===');
  console.log('Consent Sections Length:', consentSections.length);
  console.log('Consent Sections:', consentSections);
  console.log('Required Agreed:', requiredAgreed);
  console.log('Agreements:', agreements);
  console.log('Required Sections:', consentSections.filter(s => s.required).map(s => s.id));
  console.log('=== END DEBUG ===');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/clinical-assessments')}
            className="mb-4"
          >
            ← Back to Assessments
          </Button>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Informed Consent
          </h1>
          <p className="text-lg text-gray-600">
            Please review and agree to the following terms before starting your{' '}
            <strong>{getToolName(assessmentTool)}</strong>.
          </p>
        </div>

        {/* Consent Form */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Consent for Clinical Assessment</CardTitle>
            <p className="text-sm text-gray-500">
              Consent Version: {consentVersion} | Date: {new Date().toLocaleDateString()}
            </p>
            <p className="text-sm text-blue-600 font-semibold">
              DEBUG: {consentSections.length} consent sections loaded
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {consentSections.map((section) => (
                <div key={section.id} className="border-b pb-6 last:border-b-0">
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id={section.id}
                      checked={agreements[section.id] || false}
                      onChange={(e) => {
                        console.log('onChange fired!', section.id, e.target.checked);
                        handleAgreementChange(section.id, e.target.checked);
                      }}
                      onClick={(e) => {
                        e.preventDefault();
                        const newState = !agreements[section.id];
                        console.log('onClick fired!', section.id, newState);
                        handleAgreementChange(section.id, newState);
                      }}
                      onMouseDown={(e) => {
                        console.log('onMouseDown fired!', section.id);
                      }}
                      disabled={false}
                      readOnly={false}
                      style={{
                        pointerEvents: 'auto',
                        zIndex: 9999,
                        position: 'relative',
                        opacity: 1,
                        visibility: 'visible',
                        cursor: 'pointer'
                      }}
                      className={`mt-1 h-6 w-6 text-blue-600 focus:ring-blue-500 focus:ring-2 border-gray-300 rounded z-10 ${
                        errors.includes(section.id) ? 'border-red-500' : ''
                      }`}
                    />
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => {
                        const newState = !agreements[section.id];
                        console.log('Label wrapper clicked!', section.id, newState);
                        handleAgreementChange(section.id, newState);
                      }}
                    >
                      <label
                        htmlFor={section.id}
                        className={`block text-sm font-medium text-gray-900 mb-2 ${
                          section.required ? 'flex items-center' : ''
                        }`}
                      >
                        {section.title}
                        {section.required && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                      </label>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {section.content}
                      </p>
                      {errors.includes(section.id) && (
                        <p className="text-red-500 text-xs mt-1">
                          This section is required to proceed.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Digital Signature */}
            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Digital Signature</h3>
              <p className="text-xs text-gray-500 mb-4">
                By checking the boxes above and clicking "Proceed", you are electronically signing this consent form.
              </p>
              <div className="text-xs text-gray-400">
                IP Address: {typeof window !== 'undefined' ? ' concealed for privacy' : 'Loading...'} |
                User Agent: {typeof window !== 'undefined' ? navigator.userAgent.substring(0, 50) + '...' : 'Loading...'}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-between items-center">
          <Button
            variant="outline"
            onClick={handleDecline}
            disabled={loading}
          >
            Cancel
          </Button>

          <div className="text-right">
            <p className="text-sm text-gray-500 mb-2">
              All required items must be checked to proceed
            </p>
            <p className="text-xs bg-red-100 text-red-800 p-2 mb-2">
              BUTTON DEBUG: disabled={String(!requiredAgreed || loading)} | requiredAgreed={String(requiredAgreed)} | loading={String(loading)}
            </p>

            {/* Main proceed button - using inline onClick to bypass Button component issues */}
            <button
              id="PROCEED_BUTTON"
              onMouseDown={() => console.log('🔴 MOUSE DOWN on proceed button')}
              onMouseUp={() => console.log('🟢 MOUSE UP on proceed button')}
              onClick={(e) => {
                console.log('🟢=== CLICK EVENT FIRED ===');
                e.preventDefault();
                e.stopPropagation();
                console.log('🟢 PROCEED BUTTON CLICKED!');
                console.log('🟢 assessmentTool:', assessmentTool);

                // Route to appropriate assessment
                let targetUrl = `/clinical/assessment/${assessmentTool}/take`;
                if (assessmentTool === 'stress') {
                  targetUrl = '/test-stress-assessment';
                } else if (assessmentTool === 'wellbeing') {
                  targetUrl = '/test-wellbeing-assessment';
                }

                console.log('🟢 Navigating to:', targetUrl);
                // Force browser navigation
                window.location.href = targetUrl;
              }}
              disabled={!requiredAgreed || loading}
              style={{
                padding: '16px 40px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: '3px solid red',
                borderRadius: '8px',
                fontSize: '18px',
                fontWeight: 'bold',
                cursor: (!requiredAgreed || loading) ? 'not-allowed' : 'pointer',
                opacity: (!requiredAgreed || loading) ? 0.5 : 1,
                position: 'relative',
                zIndex: 99999,
                pointerEvents: 'auto !important',
                display: 'block',
                width: '100%',
                height: '60px',
                outline: '5px solid green'
              }}
            >
              {loading ? 'Saving Consent...' : `⚡ PROCEED TO ${assessmentTool.toUpperCase()} ASSESSMENT (No Login!)`}
            </button>

            {/* Debug button kept for troubleshooting */}
            <button
              onClick={() => {
                console.log('=== ORIGINAL BUTTON DEBUG ===');
                console.log('Testing original button logic...');

                // Test validation
                const isValid = validateConsent();
                console.log('Validation result:', isValid);
                console.log('requiredAgreed value:', requiredAgreed);
                console.log('loading value:', loading);

                if (isValid) {
                  console.log('Validation passed - should navigate');
                  let targetUrl = `/clinical/assessment/${assessmentTool}/take`;
                  if (assessmentTool === 'stress') {
                    targetUrl = '/test-stress-assessment';
                  } else if (assessmentTool === 'wellbeing') {
                    targetUrl = '/test-wellbeing-assessment';
                  }
                  console.log('🟠 Navigating to:', targetUrl);
                  window.location.href = targetUrl;
                } else {
                  console.log('Validation failed');
                }
              }}
              style={{
                marginTop: '10px',
                padding: '10px 20px',
                backgroundColor: '#f59e0b',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                position: 'relative',
                zIndex: 100000,
                pointerEvents: 'auto'
              }}
            >
              🟠 ORANGE BUTTON (Also No Login Required!)
            </button>
          </div>
        </div>

        {/* Information Alert */}
        <Alert variant="info" className="mt-8">
          <AlertTitle>Questions About Consent?</AlertTitle>
          <p className="mt-2 text-sm">
            If you have questions about this consent form or the assessment process,
            please contact our clinical support team or speak with a healthcare provider.
          </p>
        </Alert>

        {/* INLINE ASSESSMENT SECTION */}
        {showAssessment && (
          <div className="mt-8 p-6 bg-gray-50 rounded-lg border">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">PHQ-9 Assessment (Inline Test)</h2>
            <p className="text-sm text-gray-600 mb-4">
              This is the assessment component rendered inline - no navigation required!
            </p>
            <div className="bg-white p-4 rounded-lg shadow">
              <ClinicalAssessment />
            </div>
            <button
              onClick={() => {
                console.log('Hiding assessment...');
                setShowAssessment(false);
              }}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Hide Assessment
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClinicalConsent;