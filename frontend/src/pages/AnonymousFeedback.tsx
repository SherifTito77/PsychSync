// Anonymous Feedback Page
// Main page component that provides access to all anonymous feedback features
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { AnonymousFeedbackForm, FeedbackStatusCheck, HRReviewDashboard } from '@/components/anonymousFeedback';
import { Shield, Info, Users, Search, BookOpen, Phone } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
const AnonymousFeedback: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('submit');
  const isHR = user?.role === 'admin' || user?.role === 'super_admin';
  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-4 flex items-center justify-center gap-3">
          <Shield className="w-10 h-10 text-green-600" />
          Anonymous Feedback System
        </h1>
        <p className="text-xl text-gray-600 mb-6">
          A safe, confidential way to report workplace concerns and provide feedback
        </p>
        {/* Privacy Guarantee */}
        <Alert className="max-w-2xl mx-auto border-green-200 bg-green-50">
          <Shield className="w-4 h-4" />
          <AlertDescription className="text-center">
            <strong>100% Anonymous:</strong> Your feedback is completely confidential.
            We do not track IP addresses, require accounts, or store any identifying information.
            Your privacy and safety are our highest priorities.
          </AlertDescription>
        </Alert>
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="submit" className="flex items-center gap-2">
            <Info className="w-4 h-4" />
            Submit Feedback
          </TabsTrigger>
          <TabsTrigger value="check" className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            Check Status
          </TabsTrigger>
          {isHR && (
            <TabsTrigger value="review" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              HR Review
            </TabsTrigger>
          )}
        </TabsList>
        {/* Submit Feedback Tab */}
        <TabsContent value="submit">
          <AnonymousFeedbackForm />
        </TabsContent>
        {/* Check Status Tab */}
        <TabsContent value="check">
          <FeedbackStatusCheck />
        </TabsContent>
        {/* HR Review Tab */}
        {isHR && (
          <TabsContent value="review">
            <HRReviewDashboard />
          </TabsContent>
        )}
      </Tabs>
      {/* Quick Links and Resources */}
      <div className="mt-12 space-y-6">
        <h2 className="text-2xl font-bold text-center mb-6">Resources & Support</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Employee Assistance Program */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Phone className="w-5 h-5" />
                Employee Assistance Program (EAP)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Confidential counseling and support services available 24/7 for all employees.
              </CardDescription>
              <div className="mt-4">
                <Button variant="outline" className="w-full">
                  Contact EAP
                </Button>
              </div>
            </CardContent>
          </Card>
          {/* HR Support */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                HR Support
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Professional HR guidance and support for workplace concerns.
              </CardDescription>
              <div className="mt-4 space-y-2">
                <Button variant="outline" className="w-full">
                  Schedule Meeting
                </Button>
                <Button variant="outline" className="w-full">
                  Email HR
                </Button>
              </div>
            </CardContent>
          </Card>
          {/* External Resources */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                External Resources
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                External organizations and hotlines for additional support and reporting.
              </CardDescription>
              <div className="mt-4">
                <Button variant="outline" className="w-full">
                  View Resources
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      {/* Reporting Guidelines */}
      <div className="mt-12">
        <Card>
          <CardHeader>
            <CardTitle>When to Use Different Reporting Options</CardTitle>
            <CardDescription>
              Choose the reporting method that best fits your situation and comfort level
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-3">
              <div className="text-center p-4 border rounded-lg">
                <Shield className="w-8 h-8 mx-auto mb-3 text-green-600" />
                <h3 className="font-semibold mb-2">Anonymous Feedback</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Best for: Fear of retaliation, toxic behavior, psychological safety concerns, uncomfortable with formal reporting
                </p>
                <Button variant="outline" onClick={() => setActiveTab('submit')}>
                  Submit Anonymously
                </Button>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <Users className="w-8 h-8 mx-auto mb-3 text-blue-600" />
                <h3 className="font-semibold mb-2">Confidential HR Report</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Best for: Need guidance, want to participate in resolution, complex situations requiring discussion
                </p>
                <Button variant="outline">
                  Contact HR
                </Button>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <Phone className="w-8 h-8 mx-auto mb-3 text-red-600" />
                <h3 className="font-semibold mb-2">External Reporting</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Best for: Legal protection required, serious violations, external intervention needed
                </p>
                <Button variant="outline">
                  External Hotlines
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Legal Protection Notice */}
      <div className="mt-8">
        <Alert className="border-blue-200 bg-blue-50">
          <Info className="w-4 h-4" />
          <AlertDescription>
            <strong>Legal Protection:</strong> Whistleblower and anti-retaliation laws protect individuals who report concerns in good faith.
            Retaliation against reporters is prohibited and may result in disciplinary action.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
};
export default AnonymousFeedback;