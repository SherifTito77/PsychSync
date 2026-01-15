// Analytics & AI Overview Page
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const AnalyticsOverview: React.FC = () => {
  const navigate = useNavigate();

  const analyticsCategories = [
    {
      title: 'AI-Powered Tools',
      icon: '🤖',
      description: 'Advanced artificial intelligence for insights and optimization',
      items: [
        {
          name: 'Team Optimizer',
          path: '/team-optimizer',
          icon: '⚡',
          description: 'AI-driven team composition and dynamics optimization',
          features: ['Personality matching', 'Role optimization', 'Team balance analysis']
        },
        {
          name: 'Predictive Analytics',
          path: '/predictive-analytics',
          icon: '🔮',
          description: 'Machine learning predictions for behavior and outcomes',
          features: ['Churn prediction', 'Performance forecasting', 'Risk assessment']
        }
      ]
    },
    {
      title: 'Research & Validation',
      icon: '🔬',
      description: 'Evidence-based metrics and scientific validation',
      items: [
        {
          name: 'Reliability & Validity',
          path: '/reliability-validity',
          icon: '🔬',
          description: 'Psychometric validation and research metrics',
          features: ['Cronbach\'s alpha', 'Construct validity', 'Test-retest reliability']
        }
      ]
    },
    {
      title: 'Analytics Dashboards',
      icon: '📊',
      description: 'Comprehensive data visualization and reporting',
      items: [
        {
          name: 'General Analytics',
          path: '/analytics/dashboard',
          icon: '📈',
          description: 'Personal performance metrics and assessment history',
          features: ['Assessment history', 'Score tracking', 'Performance trends']
        }
      ]
    }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics & AI</h1>
        <p className="text-gray-600">
          Powerful artificial intelligence tools and analytics dashboards for data-driven insights
        </p>
      </div>

      {/* Features Grid */}
      {analyticsCategories.map((category, idx) => (
        <div key={idx} className="mb-10">
          <div className="flex items-center mb-6">
            <span className="text-3xl mr-3">{category.icon}</span>
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">{category.title}</h2>
              <p className="text-sm text-gray-600">{category.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {category.items.map((item, itemIdx) => (
              <Card
                key={itemIdx}
                className="hover:shadow-xl transition-all cursor-pointer border-2 hover:border-blue-300"
                onClick={() => navigate(item.path)}
              >
                <CardHeader>
                  <CardTitle className="flex items-center space-x-3">
                    <span className="text-3xl">{item.icon}</span>
                    <div>
                      <div className="text-xl">{item.name}</div>
                      <div className="text-sm font-normal text-gray-500 mt-1">{item.description}</div>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 mb-4">
                    {item.features.map((feature, fIdx) => (
                      <li key={fIdx} className="flex items-center text-sm text-gray-600">
                        <svg className="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button variant="outline" className="w-full">
                    Explore Tool
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}

      {/* AI Capabilities Info Card */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span className="text-2xl">🧠</span>
            <span className="text-purple-800">AI-Powered Insights</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 mb-4">
            Our analytics platform leverages cutting-edge machine learning algorithms to provide actionable insights:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg">
              <h4 className="font-semibold text-purple-800 mb-2">🎯 Prediction Accuracy</h4>
              <p className="text-sm text-gray-600">Up to 94% accuracy in behavioral predictions using validated models</p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <h4 className="font-semibold text-purple-800 mb-2">⚡ Real-Time Processing</h4>
              <p className="text-sm text-gray-600">Instant AI analysis as team members complete assessments</p>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <h4 className="font-semibold text-purple-800 mb-2">🔒 Privacy-First</h4>
              <p className="text-sm text-gray-600">All AI processing anonymizes data and protects individual privacy</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsOverview;
