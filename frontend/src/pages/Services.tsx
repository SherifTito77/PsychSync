// Services & Connectors Overview Page
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const Services: React.FC = () => {
  const navigate = useNavigate();

  const serviceCategories = [
    {
      title: 'Health & Wellness',
      icon: '❤️',
      description: 'Monitor and improve your physical and mental wellbeing',
      items: [
        { name: 'Health Dashboard', path: '/health', icon: '❤️', description: 'Personal health monitoring' },
        { name: 'Team Health Analytics', path: '/team-health', icon: '📊', description: 'Manager wellness view' },
        { name: 'Mental Health', path: '/mental-health-wellness', icon: '🧘', description: 'Mental wellness resources' },
      ]
    },
    {
      title: 'Integrations',
      icon: '🔗',
      description: 'Connect with your favorite tools and platforms',
      items: [
        { name: 'Corporate Integrations', path: '/integrations/corporate', icon: '🏢', description: '30+ data sources' },
        { name: 'Email Connector', path: '/email-connector', icon: '📧', description: 'Email integration' },
        { name: 'HRIS Connector', path: '/hris-connector', icon: '🏢', description: 'HR systems' },
      ]
    },
    {
      title: 'Assessments',
      icon: '🧠',
      description: 'Discover insights about personality and behavior',
      items: [
        { name: 'Personality Assessments', path: '/personality-assessments', icon: '🧠', description: 'Personality tests' },
        { name: 'Behavioral Analysis', path: '/behavioral-analysis', icon: '📊', description: 'Behavior patterns' },
      ]
    }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Services & Connectors</h1>
        <p className="text-gray-600">
          Comprehensive suite of tools for health monitoring, integrations, and behavioral assessments
        </p>
      </div>

      {serviceCategories.map((category, idx) => (
        <div key={idx} className="mb-8">
          <div className="flex items-center mb-4">
            <span className="text-2xl mr-2">{category.icon}</span>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{category.title}</h2>
              <p className="text-sm text-gray-600">{category.description}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {category.items.map((item, itemIdx) => (
              <Card
                key={itemIdx}
                className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => navigate(item.path)}
              >
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <span className="text-2xl">{item.icon}</span>
                    <span>{item.name}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4">{item.description}</p>
                  <Button variant="outline" size="sm" className="w-full">
                    Open
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Services;
