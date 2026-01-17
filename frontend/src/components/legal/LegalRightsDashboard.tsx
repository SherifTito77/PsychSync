/**
 * Legal Rights Awareness Dashboard
 *
 * Comprehensive employee legal rights information and resources
 * Includes labor law information, violation reporting, and legal aid finder
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Scale,
  Gavel,
  BookOpen,
  AlertTriangle,
  Shield,
  Search,
  CheckCircle,
  ExternalLink,
  FileText,
  Video,
  GraduationCap,
  HelpCircle,
  TrendingUp,
  Globe,
  Phone,
  Mail,
  MapPin,
  Star,
  Clock,
  Calendar as CalendarIcon
} from 'lucide-react';
import api from '@/services/api';

interface LaborLaw {
  id: string;
  country_name: string;
  law_name: string;
  category: string;
  description: string;
  min_wage?: number;
  max_weekly_hours?: number;
  overtime_threshold?: number;
  overtime_rate?: number;
  mandatory_break_minutes?: number;
  min_vacation_days?: number;
}

interface RightsResource {
  id: string;
  title: string;
  category: string;
  resource_type: string;
  summary?: string;
  url?: string;
  thumbnail_url?: string;
  video_url?: string;
  duration_minutes?: number;
  view_count: number;
}

interface ContractViolation {
  id: string;
  violation_type: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  status: string;
  detected_at: string;
  legal_risk_score?: number;
}

interface LegalAidResource {
  id: string;
  name: string;
  resource_type: string;
  description?: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  specializations?: string[];
  free_consultation: boolean;
  rating?: number;
}

function LegalRightsDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [countryCode, setCountryCode] = useState('US');

  // Data states
  const [rightsSummary, setRightsSummary] = useState<any>(null);
  const [laborLaws, setLaborLaws] = useState<LaborLaw[]>([]);
  const [resources, setResources] = useState<RightsResource[]>([]);
  const [violations, setViolations] = useState<ContractViolation[]>([]);
  const [legalAid, setLegalAid] = useState<LegalAidResource[]>([]);

  useEffect(() => {
    loadAllData();
  }, [countryCode]);

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel
      const [
        summaryRes,
        lawsRes,
        resourcesRes,
        violationsRes,
        legalAidRes
      ] = await Promise.all([
        api.get(`/legal-rights/rights-summary?country_code=${countryCode}`),
        api.get(`/legal-rights/labor-laws?country_code=${countryCode}`),
        api.get('/legal-rights/resources?featured_only=true&limit=6'),
        api.get('/legal-rights/violations?limit=10'),
        api.get(`/legal-rights/legal-aid?country_code=${countryCode}&free_only=true`)
      ]);

      setRightsSummary(summaryRes.data);
      setLaborLaws(lawsRes.data);
      setResources(resourcesRes.data);
      setViolations(violationsRes.data);
      setLegalAid(legalAidRes.data);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load legal rights data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card>
          <CardContent className="flex items-center justify-center py-20">
            <Scale className="h-8 w-8 animate-spin text-blue-600 mr-3" />
            <span>Loading legal rights information...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Alert variant="error">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Scale className="h-8 w-8 text-blue-600" />
            Legal Rights Awareness
          </h1>
          <p className="text-gray-600 mt-2">
            Know your rights. Protect yourself. Get help when you need it.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={countryCode}
            onChange={(e) => setCountryCode(e.target.value)}
            className="border rounded-lg px-4 py-2"
          >
            <option value="US">🇺🇸 United States</option>
            <option value="UK">🇬🇧 United Kingdom</option>
            <option value="CA">🇨🇦 Canada</option>
            <option value="AU">🇦🇺 Australia</option>
            <option value="DE">🇩🇪 Germany</option>
            <option value="FR">🇫🇷 France</option>
          </select>
        </div>
      </div>

      {/* Key Protections Summary */}
      {rightsSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-blue-900 flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Max Hours/Week
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-900">
                {rightsSummary.key_protections.max_weekly_hours || 'N/A'}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-green-900 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Min Wage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-900">
                {rightsSummary.key_protections.min_wage
                  ? `$${rightsSummary.key_protections.min_wage}/hr`
                  : 'Varies'}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-purple-900 flex items-center gap-2">
                <CalendarIcon className="h-4 w-4" />
                Min Vacation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-900">
                {rightsSummary.key_protections.min_vacation_days || 'N/A'} days
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-orange-900 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Protection Level
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-900">
                {rightsSummary.protection_levels?.discrimination
                  ? `${rightsSummary.protection_levels.discrimination}/10`
                  : 'N/A'}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="know-your-rights" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
          <TabsTrigger value="know-your-rights">Know Your Rights</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="violations">Report Violation</TabsTrigger>
          <TabsTrigger value="legal-aid">Find Legal Aid</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>

        {/* Know Your Rights Tab */}
        <TabsContent value="know-your-rights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Labor Laws - {rightsSummary?.country_name}
              </CardTitle>
              <CardDescription>
                Comprehensive information about your workplace rights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {laborLaws.map((law) => (
                  <div key={law.id} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <Badge variant="outline" className="mb-2">
                          {law.category.replace('_', ' ')}
                        </Badge>
                        <h4 className="font-semibold">{law.law_name}</h4>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{law.description}</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      {law.min_wage && (
                        <div>
                          <span className="font-medium">Min Wage:</span> ${law.min_wage}/hr
                        </div>
                      )}
                      {law.max_weekly_hours && (
                        <div>
                          <span className="font-medium">Max Hours:</span> {law.max_weekly_hours}/week
                        </div>
                      )}
                      {law.overtime_threshold && (
                        <div>
                          <span className="font-medium">Overtime:</span> After {law.overtime_threshold}hrs
                        </div>
                      )}
                      {law.min_vacation_days && (
                        <div>
                          <span className="font-medium">Vacation:</span> {law.min_vacation_days} days
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Resources Tab */}
        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {resources.map((resource) => (
              <Card key={resource.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Badge variant="outline" className="mb-2">
                        {resource.category}
                      </Badge>
                      <CardTitle className="text-lg">{resource.title}</CardTitle>
                    </div>
                    {resource.resource_type === 'video' ? (
                      <Video className="h-5 w-5 text-blue-600" />
                    ) : (
                      <FileText className="h-5 w-5 text-gray-600" />
                    )}
                  </div>
                  {resource.summary && (
                    <CardDescription>{resource.summary}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      {resource.duration_minutes && (
                        <span className="mr-3">⏱️ {resource.duration_minutes} min</span>
                      )}
                      <span>👁️ {resource.view_count} views</span>
                    </div>
                    <Button size="sm" variant="outline">
                      {resource.url ? 'Open' : 'View'}
                      <ExternalLink className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {resources.length === 0 && (
            <Card>
              <CardContent className="text-center py-12">
                <GraduationCap className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">No educational resources available yet.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Report Violation Tab */}
        <TabsContent value="violations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                Report a Violation
              </CardTitle>
              <CardDescription>
                Report suspected violations of your workplace rights. Your report can be anonymous.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Button size="lg" className="bg-orange-600 hover:bg-orange-700">
                  <FileText className="h-5 w-5 mr-2" />
                  Submit Violation Report
                </Button>
                <p className="text-sm text-gray-600 mt-3">
                  All reports are confidential. You can choose to remain anonymous.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Recent Violations */}
          {violations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Violations Reported</CardTitle>
                <CardDescription>
                  Track the status of reported violations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {violations.map((violation) => (
                    <div key={violation.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <Badge className={`${getSeverityColor(violation.severity)} text-white mb-2`}>
                            {violation.severity}
                          </Badge>
                          <h4 className="font-semibold">{violation.title}</h4>
                          <p className="text-sm text-gray-600 mt-1">{violation.description}</p>
                        </div>
                        <Badge variant="outline">{violation.status}</Badge>
                      </div>
                      <div className="text-xs text-gray-500">
                        Reported: {new Date(violation.detected_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Legal Aid Tab */}
        <TabsContent value="legal-aid" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gavel className="h-5 w-5" />
                Find Legal Help
              </CardTitle>
              <CardDescription>
                Connect with lawyers, legal aid organizations, and labor boards
              </CardDescription>
            </CardHeader>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {legalAid.map((aid) => (
              <Card key={aid.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">{aid.resource_type}</Badge>
                        {aid.free_consultation && (
                          <Badge className="bg-green-600 text-white">Free Consultation</Badge>
                        )}
                        {aid.rating && (
                          <div className="flex items-center text-yellow-600">
                            <Star className="h-4 w-4 fill-current" />
                            <span className="ml-1 text-sm">{aid.rating}</span>
                          </div>
                        )}
                      </div>
                      <CardTitle className="text-lg">{aid.name}</CardTitle>
                      {aid.description && (
                        <CardDescription>{aid.description}</CardDescription>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {aid.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4 text-gray-600" />
                        <a href={`tel:${aid.phone}`} className="text-blue-600 hover:underline">
                          {aid.phone}
                        </a>
                      </div>
                    )}
                    {aid.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-gray-600" />
                        <a href={`mailto:${aid.email}`} className="text-blue-600 hover:underline">
                          {aid.email}
                        </a>
                      </div>
                    )}
                    {aid.website && (
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4 text-gray-600" />
                        <a
                          href={aid.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline flex items-center"
                        >
                          Visit website
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </div>
                    )}
                    {aid.address && (
                      <div className="flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-gray-600 mt-0.5" />
                        <span className="text-gray-600">{aid.address}</span>
                      </div>
                    )}
                  </div>
                  {aid.specializations && aid.specializations.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <div className="text-xs font-medium text-gray-600 mb-2">Specializations:</div>
                      <div className="flex flex-wrap gap-1">
                        {aid.specializations.map((spec, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {spec}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {legalAid.length === 0 && (
            <Card>
              <CardContent className="text-center py-12">
                <Search className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">No legal aid resources found for your region.</p>
                <Button className="mt-4" variant="outline">
                  Search Different Region
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Compliance Tab (Admin/HR only) */}
        <TabsContent value="compliance" className="space-y-4">
          <Card>
            <CardContent className="text-center py-12">
              <Shield className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Compliance Dashboard</h3>
              <p className="text-gray-600 mb-4">
                Admin and HR access required to view compliance reports.
              </p>
              <Button variant="outline">Request Access</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="secondary"
              className="h-full py-6 flex flex-col items-center justify-center gap-2"
            >
              <HelpCircle className="h-6 w-6" />
              <span>Take Rights Quiz</span>
            </Button>
            <Button
              variant="secondary"
              className="h-full py-6 flex flex-col items-center justify-center gap-2"
            >
              <FileText className="h-6 w-6" />
              <span>Download Rights Guide</span>
            </Button>
            <Button
              variant="secondary"
              className="h-full py-6 flex flex-col items-center justify-center gap-2"
            >
              <Phone className="h-6 w-6" />
              <span>Emergency Legal Hotline</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default LegalRightsDashboard;
