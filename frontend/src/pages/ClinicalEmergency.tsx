import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle } from '@/components/ui/alert';

interface EmergencyResource {
  title: string;
  description: string;
  phone: string;
  available247: boolean;
  website?: string;
  type: 'hotline' | 'text' | 'website' | 'emergency';
}

const ClinicalEmergency: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [crisisAlertTriggered, setCrisisAlertTriggered] = useState(false);

  const emergencyResources: EmergencyResource[] = [
    {
      title: '988 Suicide & Crisis Lifeline',
      description: 'Free, confidential support 24/7 for people in distress',
      phone: '988',
      available247: true,
      website: 'https://988lifeline.org',
      type: 'hotline',
    },
    {
      title: 'Crisis Text Line',
      description: 'Text HOME to connect with a crisis counselor',
      phone: 'Text HOME to 741741',
      available247: true,
      website: 'https://www.crisistextline.org',
      type: 'text',
    },
    {
      title: 'National Domestic Violence Hotline',
      description: 'Support for domestic violence situations',
      phone: '1-800-799-7233',
      available247: true,
      website: 'https://www.thehotline.org',
      type: 'hotline',
    },
    {
      title: 'SAMHSA National Helpline',
      description: 'Substance abuse and mental health services',
      phone: '1-800-662-4357',
      available247: true,
      website: 'https://www.samhsa.gov',
      type: 'hotline',
    },
    {
      title: 'Emergency Services',
      description: 'For immediate life-threatening emergencies',
      phone: '911',
      available247: true,
      type: 'emergency',
    },
    {
      title: 'Veterans Crisis Line',
      description: 'Support for veterans and their families',
      phone: '1-800-273-8255',
      available247: true,
      website: 'https://www.veteranscrisisline.net',
      type: 'hotline',
    },
  ];

  const copingStrategies = [
    {
      title: 'Grounding Techniques',
      description: 'Focus on your senses to stay in the present moment',
      steps: [
        'Name 5 things you can see',
        'Name 4 things you can touch',
        'Name 3 things you can hear',
        'Name 2 things you can smell',
        'Name 1 thing you can taste',
      ],
    },
    {
      title: 'Deep Breathing',
      description: 'Slow, deep breathing can help calm your nervous system',
      steps: [
        'Breathe in slowly through your nose for 4 counts',
        'Hold your breath for 4 counts',
        'Breathe out slowly through your mouth for 4 counts',
        'Wait for 4 counts before breathing in again',
        'Repeat for 5-10 cycles',
      ],
    },
    {
      title: 'Contact Support',
      description: 'Reach out to someone you trust',
      steps: [
        'Call or text a friend or family member',
        'Contact your therapist or counselor',
        'Reach out to a support group',
        'Don\'t isolate yourself',
      ],
    },
  ];

  useEffect(() => {
    // Log that user accessed emergency page (for safety monitoring)
    const logEmergencyAccess = async () => {
      try {
        await fetch('/api/v1/clinical/emergency-access', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            accessed_at: new Date().toISOString(),
            user_agent: navigator.userAgent,
          }),
        });
      } catch (error) {
        console.error('Error logging emergency access:', error);
      }
    };

    logEmergencyAccess();
    setLoading(false);
  }, []);

  const handleCallEmergency = (phone: string) => {
    // Log emergency call
    try {
      fetch('/api/v1/clinical/emergency-call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          resource: phone,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Error logging emergency call:', error);
    }

    // Make the call
    window.open(`tel:${phone.replace(/[^\d]/g, '')}`);
  };

  const handleTriggerCrisisAlert = async () => {
    setCrisisAlertTriggered(true);

    try {
      await fetch('/api/v1/clinical/crisis-alert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          message: 'User accessed emergency resources and requested immediate support',
          severity: 'high',
          requires_immediate_follow_up: true,
        }),
      });
    } catch (error) {
      console.error('Error triggering crisis alert:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading emergency resources...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Critical Alert Banner */}
        <Alert variant="destructive" className="mb-8 border-2 border-red-500">
          <AlertTitle className="text-xl">If you are in immediate danger, call 911</AlertTitle>
          <p className="mt-2 text-lg">
            For life-threatening emergencies, call emergency services or go to the nearest emergency room.
          </p>
          <div className="mt-4">
            <Button
              variant="destructive"
              size="lg"
              onClick={() => handleCallEmergency('911')}
              className="text-lg px-8 py-3"
            >
              Call 911 Now
            </Button>
          </div>
        </Alert>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Emergency Mental Health Support
          </h1>
          <p className="text-xl text-gray-600">
            Free, confidential support is available 24/7. You are not alone.
          </p>
        </div>

        {/* Immediate Crisis Resources */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Immediate Crisis Support
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {emergencyResources.map((resource, index) => (
              <Card key={index} className="border-red-200 hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center mb-4">
                    {resource.available247 && (
                      <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">
                        24/7
                      </span>
                    )}
                    {resource.type === 'emergency' && (
                      <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded">
                        EMERGENCY
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {resource.title}
                  </h3>
                  <p className="text-gray-600 mb-4">{resource.description}</p>
                  <div className="space-y-2">
                    <Button
                      onClick={() => handleCallEmergency(resource.phone)}
                      className="w-full"
                      variant={resource.type === 'emergency' ? 'destructive' : 'default'}
                    >
                      {resource.phone.includes('Text') ? 'Text Now' : `Call ${resource.phone}`}
                    </Button>
                    {resource.website && (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => window.open(resource.website, '_blank')}
                      >
                        Visit Website
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Coping Strategies */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Immediate Coping Strategies
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {copingStrategies.map((strategy, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">{strategy.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">{strategy.description}</p>
                  <ol className="space-y-2">
                    {strategy.steps.map((step, stepIndex) => (
                      <li key={stepIndex} className="flex items-start text-sm">
                        <span className="text-blue-500 mr-2">{stepIndex + 1}.</span>
                        <span className="text-gray-700">{step}</span>
                      </li>
                    ))}
                  </ol>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Safety Plan */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Create a Safety Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Warning Signs</h3>
                <p className="text-gray-600 mb-4">
                  Identify thoughts, feelings, or situations that might signal a crisis:
                </p>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Changes in sleep or appetite</li>
                  <li>• Increased anxiety or agitation</li>
                  <li>• Withdrawing from others</li>
                  <li>• Feeling hopeless or trapped</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Support Contacts</h3>
                <p className="text-gray-600 mb-4">
                  Keep a list of people you can contact when you need help:
                </p>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Friends and family members</li>
                  <li>• Therapist or counselor</li>
                  <li>• Doctor or psychiatrist</li>
                  <li>• Support group members</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t">
              <Button
                onClick={() => navigate('/clinical/safety-plan')}
                className="w-full md:w-auto"
              >
                Create Detailed Safety Plan
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Request Professional Follow-up */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Need Professional Support?
              </h3>
              <p className="text-gray-600 mb-6">
                Let our clinical team know you need immediate follow-up support.
              </p>
              <div className="space-x-4">
                <Button
                  onClick={handleTriggerCrisisAlert}
                  disabled={crisisAlertTriggered}
                  variant="destructive"
                >
                  {crisisAlertTriggered ? 'Alert Sent - We will contact you soon' : 'Request Immediate Follow-up'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/clinical/providers')}
                >
                  Find Mental Health Provider
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Additional Resources */}
        <Alert variant="info">
          <AlertTitle>Remember: This Will Pass</AlertTitle>
          <p className="mt-2">
            Crisis situations feel overwhelming, but with support, they are temporary.
            You've taken an important step by reaching out for help. Please continue to reach out
            until you connect with someone who can help.
          </p>
        </Alert>
      </div>
    </div>
  );
};

export default ClinicalEmergency;