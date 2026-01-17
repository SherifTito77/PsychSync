import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import SelfHelpResources from '@/components/clinical/SelfHelpResources';

const ClinicalSelfHelp: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Self-Help & Coping Strategies
          </h1>
          <p className="text-lg text-gray-600">
            Evidence-based techniques to help you manage stress, anxiety, and improve your mental wellbeing.
          </p>
        </div>

        {/* Quick Access */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Quick Access</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                onClick={() => window.location.href = '/clinical/emergency'}
                variant="destructive"
                className="h-16 flex flex-col items-center justify-center"
              >
                <span className="text-2xl mb-2">🚨</span>
                <span>Emergency Support</span>
              </Button>
              <Button
                onClick={() => window.location.href = '/clinical-assessments'}
                className="h-16 flex flex-col items-center justify-center"
              >
                <span className="text-2xl mb-2">📋</span>
                <span>Mental Health Screening</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Self-Help Resources */}
        <SelfHelpResources />
      </div>
    </div>
  );
};

export default ClinicalSelfHelp;
