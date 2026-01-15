// Mental Health & Wellness Page - Clinical Assessments, Wellness Monitoring, Crisis Support
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import MentalHealthScreeningForm from '@/components/clinical/MentalHealthScreeningForm';
import WellnessAssessmentForm from '@/components/clinical/WellnessAssessmentForm';
import ClinicalResources from '@/components/clinical/ClinicalResources';
import TrendAnalysis from '@/components/clinical/TrendAnalysis';
import WellnessPlanGenerator from '@/components/clinical/WellnessPlanGenerator';
import CrisisSupport from '@/components/clinical/CrisisSupport';
import { useNavigate } from 'react-router-dom';

const MentalHealthWellness: React.FC = () => {
  const navigate = useNavigate();
  const [selectedService, setSelectedService] = useState<string>('screening');
  const [showScreeningForm, setShowScreeningForm] = useState<boolean>(false);
  const [showWellnessForm, setShowWellnessForm] = useState<boolean>(false);
  const [showResources, setShowResources] = useState<boolean>(false);
  const [showTrends, setShowTrends] = useState<boolean>(false);
  const [showWellnessPlan, setShowWellnessPlan] = useState<boolean>(false);
  const [showCrisisSupport, setShowCrisisSupport] = useState<boolean>(false);

  const mentalHealthServices = [
    { id: 'screening', name: 'Mental Health Screening', description: 'Evidence-based clinical assessments', icon: '🩺' },
    { id: 'wellness', name: 'Wellness Assessment', description: 'Multi-dimensional wellness evaluation', icon: '🌿' },
    { id: 'trends', name: 'Trend Analysis', description: 'Track mental health over time', icon: '📊' },
    { id: 'plans', name: 'Wellness Plans', description: 'Personalized improvement plans', icon: '📋' },
    { id: 'crisis', name: 'Crisis Support', description: 'Immediate help and resources', icon: '🆘' },
    { id: 'resources', name: 'Clinical Resources', description: 'Therapists and support tools', icon: '📚' }
  ];

  const screeningTools = [
    { name: 'PHQ-9', description: 'Depression screening tool', validation: 'High reliability (α = 0.89)' },
    { name: 'GAD-7', description: 'Anxiety screening tool', validation: 'Excellent reliability (α = 0.92)' },
    { name: 'DASS-21', description: 'Depression, Anxiety, Stress scales', validation: 'Good reliability (α = 0.84-0.91)' },
    { name: 'PCL-5', description: 'PTSD symptom assessment', validation: 'Excellent reliability (α = 0.94)' },
    { name: 'AUDIT', description: 'Alcohol use screening', validation: 'Good reliability (α = 0.75-0.85)' }
  ];

  const wellnessDimensions = [
    { name: 'Physical', description: 'Physical health and lifestyle habits', icon: '💪' },
    { name: 'Mental', description: 'Cognitive health and mental clarity', icon: '🧠' },
    { name: 'Emotional', description: 'Emotional regulation and wellbeing', icon: '❤️' },
    { name: 'Social', description: 'Relationships and social connections', icon: '👥' },
    { name: 'Professional', description: 'Work-life balance and career satisfaction', icon: '💼' },
    { name: 'Spiritual', description: 'Purpose, meaning and values', icon: '🌟' },
    { name: 'Environmental', description: 'Living and working environment quality', icon: '🏠' }
  ];

  const emergencyResources = [
    { name: '988', description: 'Suicide & Crisis Lifeline', available: '24/7' },
    { name: '911', description: 'Emergency Services', available: '24/7' },
    { name: 'Crisis Text Line', description: 'Text HOME to 741741', available: '24/7' },
    { name: 'National Helpline', description: '1-800-662-4357', available: '24/7' }
  ];

  // Show forms when selected
  if (showScreeningForm) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto p-6">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => {
                setShowScreeningForm(false);
                setSelectedService('screening');
              }}
            >
              ← Back to Services
            </Button>
          </div>
          <MentalHealthScreeningForm />
        </div>
      </div>
    );
  }

  if (showWellnessForm) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6">
            <Button
              variant="outline"
              onClick={() => {
                setShowWellnessForm(false);
                setSelectedService('wellness');
              }}
            >
              ← Back to Services
            </Button>
          </div>
          <WellnessAssessmentForm />
        </div>
      </div>
    );
  }

  if (showTrends) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => {
              setShowTrends(false);
              setSelectedService('trends');
            }}
          >
            ← Back to Services
          </Button>
        </div>
        <TrendAnalysis />
      </div>
    );
  }

  if (showResources) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => {
              setShowResources(false);
              setSelectedService('resources');
            }}
          >
            ← Back to Services
          </Button>
        </div>
        <ClinicalResources />
      </div>
    );
  }

  if (showWellnessPlan) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => {
              setShowWellnessPlan(false);
              setSelectedService('plans');
            }}
          >
            ← Back to Services
          </Button>
        </div>
        <WellnessPlanGenerator />
      </div>
    );
  }

  if (showCrisisSupport) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => {
              setShowCrisisSupport(false);
              setSelectedService('crisis');
            }}
          >
            ← Back to Services
          </Button>
        </div>
        <CrisisSupport />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Mental Health & Wellness</h1>
        <p className="text-gray-600">
          Comprehensive mental health screening, wellness monitoring, and clinical support tools with evidence-based assessments.
        </p>
      </div>

      {/* Crisis Alert Banner */}
      <Card className="mb-8 bg-red-50 border-red-200">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-red-800">Crisis Support Available</h3>
              <p className="text-red-600">If you're in immediate crisis, please call 988 or 911</p>
            </div>
            <Button variant="outline" className="text-red-600 border-red-300 hover:bg-red-100">
              Get Help Now
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Service Selection */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Mental Health Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mentalHealthServices.map((service) => (
            <Card
              key={service.id}
              className={`cursor-pointer transition-all ${
                selectedService === service.id
                  ? 'ring-2 ring-green-500 bg-green-50'
                  : 'hover:shadow-md'
              }`}
              onClick={() => {
                setSelectedService(service.id);
                if (service.id === 'screening') {
                  // Redirect to clinical assessments page instead of showing the form
                  navigate('/clinical-assessments');
                  setShowScreeningForm(false);
                  setShowWellnessForm(false);
                  setShowTrends(false);
                  setShowResources(false);
                  setShowWellnessPlan(false);
                  setShowCrisisSupport(false);
                } else if (service.id === 'wellness') {
                  setShowWellnessForm(true);
                  setShowScreeningForm(false);
                  setShowTrends(false);
                  setShowResources(false);
                  setShowWellnessPlan(false);
                  setShowCrisisSupport(false);
                } else if (service.id === 'trends') {
                  setShowTrends(true);
                  setShowScreeningForm(false);
                  setShowWellnessForm(false);
                  setShowResources(false);
                  setShowWellnessPlan(false);
                  setShowCrisisSupport(false);
                } else if (service.id === 'resources') {
                  setShowResources(true);
                  setShowScreeningForm(false);
                  setShowWellnessForm(false);
                  setShowTrends(false);
                  setShowWellnessPlan(false);
                  setShowCrisisSupport(false);
                } else if (service.id === 'plans') {
                  setShowWellnessPlan(true);
                  setShowScreeningForm(false);
                  setShowWellnessForm(false);
                  setShowTrends(false);
                  setShowResources(false);
                  setShowCrisisSupport(false);
                } else if (service.id === 'crisis') {
                  setShowCrisisSupport(true);
                  setShowScreeningForm(false);
                  setShowWellnessForm(false);
                  setShowTrends(false);
                  setShowResources(false);
                  setShowWellnessPlan(false);
                } else {
                  setShowScreeningForm(false);
                  setShowWellnessForm(false);
                  setShowTrends(false);
                  setShowResources(false);
                  setShowWellnessPlan(false);
                  setShowCrisisSupport(false);
                }
              }}
            >
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center space-x-3">
                  <span className="text-2xl">{service.icon}</span>
                  <span>{service.name}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{service.description}</p>
                {(service.id === 'screening' || service.id === 'wellness' || service.id === 'trends' || service.id === 'resources' || service.id === 'plans' || service.id === 'crisis') && (
                  <div className="mt-3">
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (service.id === 'screening') {
                          // Redirect to clinical assessments page instead of showing the form
                          navigate('/clinical-assessments');
                          setShowScreeningForm(false);
                          setShowWellnessForm(false);
                          setShowTrends(false);
                          setShowResources(false);
                          setShowWellnessPlan(false);
                          setShowCrisisSupport(false);
                        } else if (service.id === 'wellness') {
                          setShowWellnessForm(true);
                          setShowScreeningForm(false);
                          setShowTrends(false);
                          setShowResources(false);
                          setShowWellnessPlan(false);
                          setShowCrisisSupport(false);
                        } else if (service.id === 'trends') {
                          setShowTrends(true);
                          setShowScreeningForm(false);
                          setShowWellnessForm(false);
                          setShowResources(false);
                          setShowWellnessPlan(false);
                          setShowCrisisSupport(false);
                        } else if (service.id === 'resources') {
                          setShowResources(true);
                          setShowScreeningForm(false);
                          setShowWellnessForm(false);
                          setShowTrends(false);
                          setShowWellnessPlan(false);
                          setShowCrisisSupport(false);
                        } else if (service.id === 'plans') {
                          setShowWellnessPlan(true);
                          setShowScreeningForm(false);
                          setShowWellnessForm(false);
                          setShowTrends(false);
                          setShowResources(false);
                          setShowCrisisSupport(false);
                        } else if (service.id === 'crisis') {
                          setShowCrisisSupport(true);
                          setShowScreeningForm(false);
                          setShowWellnessForm(false);
                          setShowTrends(false);
                          setShowResources(false);
                          setShowWellnessPlan(false);
                        }
                      }}
                    >
                      {service.id === 'screening' ? 'Start Screening' :
                       service.id === 'wellness' ? 'Start Assessment' :
                       service.id === 'trends' ? 'View Trends' :
                       service.id === 'resources' ? 'Browse Resources' :
                       service.id === 'plans' ? 'Create Plan' :
                       service.id === 'crisis' ? 'Get Help Now' : 'Get Started'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Clinical Screening Tools */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Clinical Screening Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {screeningTools.map((tool, index) => (
            <Card key={index} className="bg-blue-50">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg text-blue-800">{tool.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-700 mb-2">{tool.description}</p>
                <p className="text-xs text-blue-600">{tool.validation}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Wellness Dimensions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Wellness Dimensions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {wellnessDimensions.map((dimension, index) => (
            <Card key={index} className="text-center">
              <CardHeader className="pb-2">
                <span className="text-3xl">{dimension.icon}</span>
                <CardTitle className="text-lg">{dimension.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">{dimension.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Emergency Resources */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Emergency Resources</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {emergencyResources.map((resource, index) => (
            <Card key={index} className="bg-red-50">
              <CardContent className="p-4 text-center">
                <h3 className="font-semibold text-red-800">{resource.name}</h3>
                <p className="text-sm text-gray-700">{resource.description}</p>
                <p className="text-xs text-red-600">{resource.available}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <Button variant="primary" onClick={() => console.log('Start Screening')}>
          Start Screening
        </Button>
        <Button variant="secondary" onClick={() => console.log('Wellness Assessment')}>
          Wellness Assessment
        </Button>
        <Button variant="outline" onClick={() => console.log('View Trends')}>
          View Trends
        </Button>
        <Button variant="outline" onClick={() => console.log('Create Plan')}>
          Create Wellness Plan
        </Button>
      </div>

      {/* Important Disclaimer */}
      <Card className="mt-8 bg-yellow-50">
        <CardHeader>
          <CardTitle className="text-yellow-800">Important Notice</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-yellow-700">
            <strong>This platform is not a substitute for professional medical care.</strong>
            Mental health screenings are for informational purposes only. If you're experiencing
            mental health concerns, please consult with a qualified healthcare provider. In case
            of emergency, call 911 or go to the nearest emergency room.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default MentalHealthWellness;