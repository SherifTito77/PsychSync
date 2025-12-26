import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface CrisisResource {
  id: string;
  name: string;
  type: 'hotline' | 'text' | 'chat' | 'emergency';
  contact: string;
  description: string;
  availability: string;
  response_time?: string;
  languages?: string[];
}

interface SafetyPlan {
  id: string;
  warning_signs: string[];
  coping_strategies: string[];
  social_supports: string[];
  professional_help: string[];
  emergency_contacts: string[];
  safe_environment: string[];
}

interface CrisisAssessment {
  severity: 'low' | 'moderate' | 'high' | 'emergency';
  risk_factors: string[];
  immediate_needs: string[];
  recommended_actions: string[];
  safety_concerns: string[];
}

const CrisisSupport: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'immediate' | 'resources' | 'plan' | 'assessment'>('immediate');
  const [assessmentResponses, setAssessmentResponses] = useState<Record<string, string>>({});
  const [assessmentResult, setAssessmentResult] = useState<CrisisAssessment | null>(null);
  const [safetyPlan, setSafetyPlan] = useState<SafetyPlan | null>(null);
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [isCallingEmergency, setIsCallingEmergency] = useState(false);
  const [showCrisisChat, setShowCrisisChat] = useState(false);

  const crisisResources: CrisisResource[] = [
    {
      id: '1',
      name: '988 Suicide & Crisis Lifeline',
      type: 'hotline',
      contact: '988',
      description: '24/7 free, confidential support for people in distress',
      availability: '24/7',
      response_time: 'Immediate',
      languages: ['English', 'Spanish']
    },
    {
      id: '2',
      name: 'Crisis Text Line',
      type: 'text',
      contact: 'Text HOME to 741741',
      description: 'Text with a trained crisis counselor',
      availability: '24/7',
      response_time: 'Average 5 minutes'
    },
    {
      id: '3',
      name: '911 Emergency Services',
      type: 'emergency',
      contact: '911',
      description: 'For immediate medical emergencies or danger',
      availability: '24/7',
      response_time: 'Immediate'
    },
    {
      id: '4',
      name: 'National Hopeline Network',
      type: 'hotline',
      contact: '1-800-442-HOPE (4673)',
      description: 'Emotional support and crisis intervention',
      availability: '24/7',
      response_time: 'Immediate'
    },
    {
      id: '5',
      name: 'The Trevor Project',
      type: 'hotline',
      contact: '1-866-488-7386',
      description: 'Crisis intervention and suicide prevention for LGBTQ youth',
      availability: '24/7',
      response_time: 'Immediate'
    },
    {
      id: '6',
      name: 'Veterans Crisis Line',
      type: 'hotline',
      contact: '988 then Press 1',
      description: 'Confidential support for veterans in crisis',
      availability: '24/7',
      response_time: 'Immediate'
    }
  ];

  const assessmentQuestions = [
    {
      id: 'suicidal_thoughts',
      question: 'Are you currently having thoughts of harming yourself?',
      type: 'yes_no_critical',
      description: 'This helps us understand your immediate safety needs'
    },
    {
      id: 'harm_plan',
      question: 'Do you have a specific plan to harm yourself?',
      type: 'yes_no_critical',
      description: 'Understanding if there are specific plans helps us provide appropriate support'
    },
    {
      id: 'anxiety_level',
      question: 'How would you rate your current anxiety or distress level? (1-10)',
      type: 'scale',
      description: '1 = Minimal distress, 10 = Extreme distress'
    },
    {
      id: 'support_system',
      question: 'Do you have someone you can talk to right now?',
      type: 'yes_no',
      description: 'Social support is important during difficult times'
    },
    {
      id: 'substances',
      question: 'Have you used alcohol or substances in the past 24 hours?',
      type: 'yes_no',
      description: 'This helps us provide the most appropriate support'
    },
    {
      id: 'sleep',
      question: 'How many hours of sleep did you get last night?',
      type: 'number',
      description: 'Sleep affects our emotional and mental wellbeing'
    },
    {
      id: 'triggers',
      question: 'What triggered this crisis feeling? (optional)',
      type: 'text',
      description: 'Understanding triggers can help with long-term planning'
    }
  ];

  useEffect(() => {
    loadSafetyPlan();
  }, []);

  const loadSafetyPlan = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('/api/v1/clinical/crisis/safety-plan', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setSafetyPlan(data.data);
        }
      }
    } catch (err) {
      console.error('Error loading safety plan:', err);
    }
  };

  const handleAssessmentResponse = (questionId: string, value: string) => {
    setAssessmentResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const submitAssessment = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Please log in to use this feature');
        return;
      }

      const response = await fetch('/api/v1/clinical/crisis/assessment', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          responses: assessmentResponses,
          timestamp: new Date().toISOString()
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAssessmentResult(data.data);
          setActiveTab('resources');
        }
      }
    } catch (err) {
      console.error('Error submitting assessment:', err);
      // Show immediate resources anyway
      setActiveTab('resources');
    }
  };

  const generateSafetyPlan = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Please log in to create a safety plan');
        return;
      }

      const response = await fetch('/api/v1/clinical/crisis/create-safety-plan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          personalize: true,
          include_local_resources: true
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSafetyPlan(data.data);
          setActiveTab('plan');
        }
      }
    } catch (err) {
      console.error('Error creating safety plan:', err);
    }
  };

  const handleEmergencyCall = (contact: string) => {
    if (contact === '911' || contact === '988') {
      setIsCallingEmergency(true);
      // Simulate emergency call
      setTimeout(() => {
        setIsCallingEmergency(false);
        alert(`Calling ${contact}... Please stay on the line.`);
      }, 2000);
    } else {
      window.open(`tel:${contact}`);
    }
  };

  const handleCrisisText = () => {
    window.open('sms:741741?body=HOME');
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'hotline': return '📞';
      case 'text': return '💬';
      case 'chat': return '💻';
      case 'emergency': return '🚨';
      default: return '🆘';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'emergency': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'moderate': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (emergencyMode) {
    return (
      <div className="min-h-screen bg-red-50 p-6">
        <div className="max-w-4xl mx-auto">
          <Card className="border-red-200">
            <CardContent className="p-8 text-center">
              <div className="text-6xl mb-4">🚨</div>
              <h1 className="text-3xl font-bold text-red-800 mb-4">Emergency Support Available</h1>
              <p className="text-red-700 mb-6">
                You are not alone. Help is available right now.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                <Button
                  onClick={() => handleEmergencyCall('988')}
                  className="bg-red-600 hover:bg-red-700 text-white p-6 text-lg"
                  disabled={isCallingEmergency}
                >
                  {isCallingEmergency ? 'Connecting...' : 'Call 988 Crisis Lifeline'}
                </Button>
                <Button
                  onClick={() => handleEmergencyCall('911')}
                  className="bg-red-600 hover:bg-red-700 text-white p-6 text-lg"
                  disabled={isCallingEmergency}
                >
                  {isCallingEmergency ? 'Connecting...' : 'Call 911 Emergency'}
                </Button>
              </div>

              <Button
                onClick={handleCrisisText}
                variant="outline"
                className="border-red-300 text-red-600 hover:bg-red-100 p-4"
              >
                Text HOME to 741741
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Crisis Support</h1>
        <p className="text-gray-600">
          Immediate help and resources when you need them most. You are not alone.
        </p>
      </div>

      {/* Emergency Alert Banner */}
      <Card className="bg-red-50 border-red-200">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-red-800 mb-1">Need Immediate Help?</h3>
              <p className="text-red-600">
                If you're in danger or having thoughts of self-harm, get help right now.
              </p>
            </div>
            <div className="space-x-3">
              <Button
                onClick={() => handleEmergencyCall('988')}
                className="bg-red-600 hover:bg-red-700"
              >
                Call 988
              </Button>
              <Button
                onClick={handleEmergencyCall('911')}
                variant="outline"
                className="text-red-600 border-red-300 hover:bg-red-100"
              >
                Call 911
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('immediate')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'immediate'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Immediate Help
          </button>
          <button
            onClick={() => setActiveTab('assessment')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'assessment'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Quick Assessment
          </button>
          <button
            onClick={() => setActiveTab('resources')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'resources'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Crisis Resources
          </button>
          <button
            onClick={() => setActiveTab('plan')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'plan'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Safety Plan
          </button>
        </nav>
      </div>

      {/* Immediate Help Tab */}
      {activeTab === 'immediate' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-red-800">Immediate Support Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {crisisResources.filter(r => r.type === 'hotline' || r.type === 'emergency').map((resource) => (
                  <div key={resource.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-start space-x-4">
                      <span className="text-3xl">{getResourceIcon(resource.type)}</span>
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg mb-1">{resource.name}</h3>
                        <p className="text-gray-600 mb-3">{resource.description}</p>
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm text-gray-500">{resource.availability}</span>
                          {resource.response_time && (
                            <span className="text-sm text-green-600">{resource.response_time}</span>
                          )}
                        </div>
                        {resource.type === 'emergency' ? (
                          <Button
                            onClick={() => handleEmergencyCall(resource.contact)}
                            className="w-full bg-red-600 hover:bg-red-700"
                            disabled={isCallingEmergency}
                          >
                            {isCallingEmergency ? 'Connecting...' : `Call ${resource.contact}`}
                          </Button>
                        ) : (
                          <Button
                            onClick={() => handleEmergencyCall(resource.contact)}
                            className="w-full"
                          >
                            {resource.contact}
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Text Support */}
          <Card>
            <CardHeader>
              <CardTitle>Text Support</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {crisisResources.filter(r => r.type === 'text').map((resource) => (
                  <div key={resource.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h3 className="font-semibold">{resource.name}</h3>
                      <p className="text-gray-600">{resource.description}</p>
                      <p className="text-sm text-gray-500">{resource.response_time}</p>
                    </div>
                    <Button onClick={handleCrisisText}>
                      {resource.contact}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Assessment Tab */}
      {activeTab === 'assessment' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Crisis Assessment</CardTitle>
              <p className="text-sm text-gray-600">
                This confidential assessment helps us provide you with the most appropriate support.
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {assessmentQuestions.map((question) => (
                  <div key={question.id} className="p-4 border rounded-lg">
                    <h3 className="font-medium mb-2">{question.question}</h3>
                    <p className="text-sm text-gray-600 mb-3">{question.description}</p>

                    {question.type === 'yes_no_critical' ? (
                      <div className="flex space-x-4">
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name={question.id}
                            value="yes"
                            onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                            className="mr-2"
                          />
                          <span className="text-red-600 font-medium">Yes</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name={question.id}
                            value="no"
                            onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                            className="mr-2"
                          />
                          <span>No</span>
                        </label>
                      </div>
                    ) : question.type === 'yes_no' ? (
                      <div className="flex space-x-4">
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name={question.id}
                            value="yes"
                            onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                            className="mr-2"
                          />
                          <span>Yes</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name={question.id}
                            value="no"
                            onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                            className="mr-2"
                          />
                          <span>No</span>
                        </label>
                      </div>
                    ) : question.type === 'scale' ? (
                      <div className="flex space-x-2">
                        {[1,2,3,4,5,6,7,8,9,10].map(num => (
                          <label key={num} className="flex items-center">
                            <input
                              type="radio"
                              name={question.id}
                              value={num.toString()}
                              onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                              className="mr-1"
                            />
                            <span>{num}</span>
                          </label>
                        ))}
                      </div>
                    ) : question.type === 'number' ? (
                      <input
                        type="number"
                        min="0"
                        max="24"
                        onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        placeholder="Enter number"
                      />
                    ) : (
                      <textarea
                        onChange={(e) => handleAssessmentResponse(question.id, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        rows={3}
                        placeholder="Optional: share what triggered this feeling..."
                      />
                    )}
                  </div>
                ))}

                <div className="flex justify-center pt-6">
                  <Button
                    onClick={submitAssessment}
                    className="px-8 py-3"
                    disabled={Object.keys(assessmentResponses).length === 0}
                  >
                    Get Assessment Results
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Assessment Results */}
          {assessmentResult && (
            <Card className={`border-2 ${getSeverityColor(assessmentResult.severity)}`}>
              <CardHeader>
                <CardTitle>Assessment Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(assessmentResult.severity)}`}>
                    Severity Level: {assessmentResult.severity.toUpperCase()}
                  </div>

                  <div>
                    <h4 className="font-semibold mb-2">Immediate Actions Recommended:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {assessmentResult.recommended_actions.map((action, index) => (
                        <li key={index} className="text-gray-700">{action}</li>
                      ))}
                    </ul>
                  </div>

                  {assessmentResult.safety_concerns.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2 text-red-600">Safety Concerns:</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {assessmentResult.safety_concerns.map((concern, index) => (
                          <li key={index} className="text-red-700">{concern}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Resources Tab */}
      {activeTab === 'resources' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {crisisResources.map((resource) => (
              <Card key={resource.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="text-center">
                    <div className="text-4xl mb-4">{getResourceIcon(resource.type)}</div>
                    <h3 className="font-semibold text-lg mb-2">{resource.name}</h3>
                    <p className="text-gray-600 mb-4">{resource.description}</p>
                    <div className="space-y-2 mb-4">
                      <div className="text-sm text-gray-500">
                        <span className="font-medium">Availability:</span> {resource.availability}
                      </div>
                      {resource.response_time && (
                        <div className="text-sm text-green-600">
                          <span className="font-medium">Response Time:</span> {resource.response_time}
                        </div>
                      )}
                      {resource.languages && (
                        <div className="text-sm text-blue-600">
                          <span className="font-medium">Languages:</span> {resource.languages.join(', ')}
                        </div>
                      )}
                    </div>
                    {resource.type === 'text' ? (
                      <Button onClick={handleCrisisText} className="w-full">
                        {resource.contact}
                      </Button>
                    ) : (
                      <Button
                        onClick={() => handleEmergencyCall(resource.contact)}
                        className="w-full"
                        disabled={isCallingEmergency}
                      >
                        {isCallingEmergency ? 'Connecting...' : resource.contact}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Local Resources */}
          <Card>
            <CardHeader>
              <CardTitle>Find Local Help</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">Emergency Departments</h4>
                  <p className="text-gray-600 mb-2">
                    Nearest hospital emergency rooms for immediate medical care
                  </p>
                  <Button variant="outline" className="w-full">
                    Find Nearest ER
                  </Button>
                </div>
                <div>
                  <h4 className="font-semibold mb-3">Mental Health Services</h4>
                  <p className="text-gray-600 mb-2">
                    Local mental health professionals and crisis centers
                  </p>
                  <Button variant="outline" className="w-full">
                    Find Local Support
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Safety Plan Tab */}
      {activeTab === 'plan' && (
        <div className="space-y-6">
          {safetyPlan ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Your Personalized Safety Plan</CardTitle>
                  <p className="text-sm text-gray-600">
                    Review this plan regularly and update it as needed.
                  </p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">⚠️</span> Warning Signs
                      </h4>
                      <ul className="space-y-2">
                        {safetyPlan.warning_signs.map((sign, index) => (
                          <li key={index} className="flex items-center">
                            <span className="w-6 h-6 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-sm mr-3">
                              !
                            </span>
                            {sign}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">🧘</span> Coping Strategies
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {safetyPlan.coping_strategies.map((strategy, index) => (
                          <div key={index} className="p-3 bg-blue-50 rounded-lg">
                            {strategy}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">👥</span> Social Support
                      </h4>
                      <div className="space-y-2">
                        {safetyPlan.social_supports.map((support, index) => (
                          <div key={index} className="flex items-center p-3 bg-green-50 rounded-lg">
                            <span className="mr-3">📞</span>
                            {support}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">🏥</span> Professional Help
                      </h4>
                      <div className="space-y-2">
                        {safetyPlan.professional_help.map((help, index) => (
                          <div key={index} className="flex items-center p-3 bg-purple-50 rounded-lg">
                            <span className="mr-3">💼</span>
                            {help}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3 flex items-center">
                        <span className="mr-2">🆘</span> Emergency Contacts
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {safetyPlan.emergency_contacts.map((contact, index) => (
                          <div key={index} className="p-3 bg-red-50 rounded-lg border border-red-200">
                            {contact}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex justify-center space-x-4">
                <Button variant="outline" onClick={generateSafetyPlan}>
                  Update Plan
                </Button>
                <Button>
                  Print or Share Plan
                </Button>
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <div className="text-6xl mb-4">🛡️</div>
                <h3 className="text-xl font-semibold mb-2">Create Your Safety Plan</h3>
                <p className="text-gray-600 mb-6">
                  A safety plan helps you prepare for difficult moments and know exactly what to do when you need help.
                </p>
                <Button onClick={generateSafetyPlan}>
                  Generate Personalized Safety Plan
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default CrisisSupport;