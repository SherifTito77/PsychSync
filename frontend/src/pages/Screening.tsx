// Clinical Screening Overview Page
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const Screening: React.FC = () => {
  const navigate = useNavigate();

  const screeningTools = [
    {
      title: 'Depression Screening',
      path: '/screening/phq9',
      icon: '💙',
      description: 'PHQ-9 - Evidence-based depression screening',
      validity: 'High reliability (α = 0.89)',
      color: 'blue',
      badge: null
    },
    {
      title: 'Anxiety Screening',
      path: '/screening/gad7',
      icon: '💛',
      description: 'GAD-7 - Comprehensive anxiety assessment',
      validity: 'Excellent reliability (α = 0.92)',
      color: 'yellow',
      badge: null
    },
    {
      title: 'Social Anxiety Assessment',
      path: '/screening/lsas',
      icon: '🧠',
      description: 'LSAS - Liebowitz Social Anxiety Scale (24 items)',
      validity: 'Gold standard (α = 0.95)',
      color: 'blue',
      badge: 'NEW'
    },
    {
      title: 'Eating Attitudes Assessment',
      path: '/screening/eat26',
      icon: '🍎',
      description: 'EAT-26 - Eating disorder screening (26 items)',
      validity: 'High reliability (α = 0.83)',
      color: 'green',
      badge: 'NEW'
    },
    {
      title: 'OCD Severity Assessment',
      path: '/screening/ybocs',
      icon: '🔄',
      description: 'Y-BOCS - Yale-Brown OCD Scale (10 items)',
      validity: 'Inter-rater α = 0.98',
      color: 'purple',
      badge: 'NEW'
    },
    {
      title: 'Suicide Risk Assessment',
      path: '/screening/cssrs',
      icon: '🚨',
      description: 'C-SSRS - Columbia-Suicide Severity Rating Scale',
      validity: 'High validity (AUC = 0.83)',
      color: 'red',
      badge: null
    },
    {
      title: 'Video Consultation',
      path: '/telehealth/schedule',
      icon: '📹',
      description: 'Secure HIPAA-compliant telehealth sessions',
      validity: 'Twilio Video encrypted connection',
      color: 'blue',
      badge: 'NEW'
    },
    {
      title: 'Crisis Resources',
      path: '/screening/crisis-resources',
      icon: '🆘',
      description: '24/7 crisis support and emergency resources',
      validity: 'Immediate help available',
      color: 'red',
      badge: null
    },
    {
      title: 'Clinical Assessment Portal',
      path: '/clinical-assessments',
      icon: '🏠',
      description: 'Main mental health assessment hub',
      validity: 'Comprehensive tools',
      color: 'green',
      badge: null
    },
    {
      title: 'Wellbeing Check',
      path: '/clinical/wellbeing/take',
      icon: '🌟',
      description: 'Overall wellbeing assessment',
      validity: 'Holistic approach',
      color: 'purple',
      badge: null
    },
    {
      title: 'Stress Assessment',
      path: '/clinical/stress/take',
      icon: '😰',
      description: 'Perceived stress level evaluation',
      validity: 'Validated scale',
      color: 'orange',
      badge: null
    },
    {
      title: 'Self-Help Library',
      path: '/clinical/self-help',
      icon: '📚',
      description: 'Comprehensive coping strategies',
      validity: 'Evidence-based resources',
      color: 'indigo',
      badge: null
    },
    {
      title: 'Emergency Resources',
      path: '/clinical/emergency',
      icon: '🚨',
      description: '24/7 crisis support hotline',
      validity: 'Immediate assistance',
      color: 'red',
      badge: null
    },
    {
      title: 'Clinical Dashboard',
      path: '/clinical/dashboard',
      icon: '👨‍⚕️',
      description: 'Professional tools for clinicians',
      validity: 'Advanced analytics',
      color: 'teal',
      badge: null
    }
  ];

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Crisis Alert Banner - Mobile Optimized */}
      <Card className="mb-6 sm:mb-8 bg-red-50 border-red-200">
        <CardContent className="p-3 sm:p-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex-1">
              <h3 className="text-base sm:text-lg font-semibold text-red-800">Need Immediate Help?</h3>
              <p className="text-sm sm:text-base text-red-600">If you're in crisis, please call 988 or 911</p>
            </div>
            <Button
              variant="outline"
              className="w-full sm:w-auto text-red-600 border-red-300 hover:bg-red-100 whitespace-nowrap"
              onClick={() => navigate('/screening/crisis-resources')}
            >
              Get Help Now
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Clinical Screening Tools</h1>
        <p className="text-sm sm:text-base text-gray-600">
          Evidence-based mental health assessments with validated psychometric properties
        </p>
      </div>

      {/* Screening Tools Grid - Mobile Optimized */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {screeningTools.map((tool, idx) => (
          <Card
            key={idx}
            className="hover:shadow-lg transition-shadow cursor-pointer relative"
            onClick={() => navigate(tool.path)}
          >
            {tool.badge && (
              <div className="absolute top-2 right-2 bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full z-10">
                {tool.badge}
              </div>
            )}
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center space-x-2 sm:space-x-3">
                <span className="text-2xl sm:text-3xl">{tool.icon}</span>
                <span className="text-base sm:text-lg leading-tight">{tool.title}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs sm:text-sm text-gray-700 mb-2 sm:mb-3 line-clamp-2">
                {tool.description}
              </p>
              <p className="text-xs text-gray-500 mb-3 sm:mb-4">{tool.validity}</p>
              <Button variant="outline" size="sm" className="w-full text-sm">
                Open Tool
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Important Disclaimer - Mobile Optimized */}
      <Card className="bg-yellow-50">
        <CardHeader className="pb-2">
          <CardTitle className="text-base sm:text-lg text-yellow-800">Important Notice</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm sm:text-base text-yellow-700">
            <strong>This platform is not a substitute for professional medical care.</strong>
            {' '}Mental health screenings are for informational purposes only. If you're experiencing
            mental health concerns, please consult with a qualified healthcare provider. In case
            of emergency, call 911 or go to the nearest emergency room.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Screening;
