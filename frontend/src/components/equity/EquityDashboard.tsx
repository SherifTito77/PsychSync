/**
 * Employee Equity & Transparency Dashboard
 *
 * Provides employees with visibility into organizational equity metrics,
 * pay equity, promotion rates, and demographic representation.
 * Promotes transparency and accountability.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Scale,
  Users,
  TrendingUp,
  DollarSign,
  Award,
  CheckCircle,
  AlertTriangle,
  Info,
  BarChart3,
  PieChart,
  Target,
  Shield,
  Eye,
  FileText,
  Download,
  Calendar
} from 'lucide-react';
import api from '@/services/api';

interface EquityReport {
  organization_id: string;
  analysis_date: string;
  overall_risk_score: number;
  pay_equity: {
    severity: string;
    disparity_detected: boolean;
    affected_groups: string[];
  };
  promotion_equity: {
    severity: string;
    disparity_detected: boolean;
    affected_groups: string[];
  };
  hiring_equity: {
    severity: string;
    disparity_detected: boolean;
    affected_groups: string[];
  };
  open_complaints: number;
  complaint_severity_breakdown: Record<string, number>;
  compliance_score: number;
  recommendations: string[];
}

interface DemographicData {
  total_employees: number;
  demographics: {
    gender?: Record<string, number>;
    race?: Record<string, number>;
    age_range?: Record<string, number>;
    veteran_status?: Record<string, number>;
  };
}

function EquityDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [equityReport, setEquityReport] = useState<EquityReport | null>(null);
  const [demographics, setDemographics] = useState<DemographicData | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load equity report and demographics
      const [reportRes, demoRes] = await Promise.all([
        api.get('/discrimination-analysis/compliance/report').catch(() => null),
        api.get('/discrimination-analysis/demographics').catch(() => null)
      ]);

      if (reportRes) setEquityReport(reportRes.data);
      if (demoRes) setDemographics(demoRes.data);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load equity data');
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
            <span>Loading equity dashboard...</span>
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
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600 mb-4">
            This dashboard requires HR/Admin access to view comprehensive equity metrics.
          </p>
          <Button onClick={loadData} variant="outline">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'severe': return 'bg-red-400';
      case 'significant': return 'bg-orange-500';
      case 'moderate': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-green-500';
    }
  };

  const getSeverityIcon = (severity: string) => {
    if (severity === 'none' || severity === 'low') {
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    }
    return <AlertTriangle className="h-5 w-5 text-orange-600" />;
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Scale className="h-8 w-8 text-blue-600" />
            Equity & Transparency Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            Promoting fairness, equality, and transparency in the workplace
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Eye className="h-5 w-5 text-green-600" />
          <span className="text-sm text-gray-600">Transparency Mode</span>
        </div>
      </div>

      {/* Key Metrics */}
      {equityReport && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Compliance Score */}
          <Card className={equityReport.compliance_score >= 80 ? 'bg-gradient-to-br from-green-50 to-green-100' : 'bg-gradient-to-br from-orange-50 to-orange-100'}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Compliance Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {equityReport.compliance_score}%
              </div>
              <p className="text-xs text-gray-600 mt-1">
                {equityReport.compliance_score >= 80 ? 'Excellent' : equityReport.compliance_score >= 60 ? 'Good' : 'Needs Improvement'}
              </p>
            </CardContent>
          </Card>

          {/* Pay Equity */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Pay Equity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {getSeverityIcon(equityReport.pay_equity.severity)}
                <span className={`text-lg font-semibold ${equityReport.pay_equity.disparity_detected ? 'text-orange-600' : 'text-green-600'}`}>
                  {equityReport.pay_equity.severity === 'none' ? 'Fair' : equityReport.pay_equity.severity}
                </span>
              </div>
              {equityReport.pay_equity.disparity_detected && (
                <Badge className={`${getSeverityColor(equityReport.pay_equity.severity)} text-white mt-2`}>
                  Disparity Detected
                </Badge>
              )}
            </CardContent>
          </Card>

          {/* Promotion Equity */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Award className="h-4 w-4" />
                Promotion Equity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {getSeverityIcon(equityReport.promotion_equity.severity)}
                <span className={`text-lg font-semibold ${equityReport.promotion_equity.disparity_detected ? 'text-orange-600' : 'text-green-600'}`}>
                  {equityReport.promotion_equity.severity === 'none' ? 'Fair' : equityReport.promotion_equity.severity}
                </span>
              </div>
              {equityReport.promotion_equity.disparity_detected && (
                <Badge className={`${getSeverityColor(equityReport.promotion_equity.severity)} text-white mt-2`}>
                  Disparity Detected
                </Badge>
              )}
            </CardContent>
          </Card>

          {/* Open Complaints */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Open Complaints
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {equityReport.open_complaints}
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Under investigation
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="pay-equity">Pay Equity</TabsTrigger>
          <TabsTrigger value="promotions">Promotions</TabsTrigger>
          <TabsTrigger value="recommendations">Actions</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Equity Analysis Summary</CardTitle>
              <CardDescription>
                Comprehensive analysis of workplace fairness across pay, promotions, and hiring
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {equityReport && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Pay Equity Analysis</span>
                          {equityReport.pay_equity.disparity_detected ? (
                            <AlertTriangle className="h-5 w-5 text-orange-600" />
                          ) : (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                        </div>
                        <Badge className={`${getSeverityColor(equityReport.pay_equity.severity)} text-white`}>
                          {equityReport.pay_equity.severity}
                        </Badge>
                        {equityReport.pay_equity.affected_groups.length > 0 && (
                          <p className="text-xs text-gray-600 mt-2">
                            Affected: {equityReport.pay_equity.affected_groups.join(', ')}
                          </p>
                        )}
                      </div>

                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Promotion Equity</span>
                          {equityReport.promotion_equity.disparity_detected ? (
                            <AlertTriangle className="h-5 w-5 text-orange-600" />
                          ) : (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                        </div>
                        <Badge className={`${getSeverityColor(equityReport.promotion_equity.severity)} text-white`}>
                          {equityReport.promotion_equity.severity}
                        </Badge>
                        {equityReport.promotion_equity.affected_groups.length > 0 && (
                          <p className="text-xs text-gray-600 mt-2">
                            Affected: {equityReport.promotion_equity.affected_groups.join(', ')}
                          </p>
                        )}
                      </div>

                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Hiring Equity</span>
                          {equityReport.hiring_equity.disparity_detected ? (
                            <AlertTriangle className="h-5 w-5 text-orange-600" />
                          ) : (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                        </div>
                        <Badge className={`${getSeverityColor(equityReport.hiring_equity.severity)} text-white`}>
                          {equityReport.hiring_equity.severity}
                        </Badge>
                        {equityReport.hiring_equity.affected_groups.length > 0 && (
                          <p className="text-xs text-gray-600 mt-2">
                            Affected: {equityReport.hiring_equity.affected_groups.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>

                    {equityReport.open_complaints > 0 && (
                      <Alert variant="error">
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          There are currently {equityReport.open_complaints} open discrimination complaints under investigation.
                        </AlertDescription>
                      </Alert>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Demographics Tab */}
        <TabsContent value="demographics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Organizational Demographics
              </CardTitle>
              <CardDescription>
                Aggregated demographic data for transparency and accountability
              </CardDescription>
            </CardHeader>
            <CardContent>
              {demographics ? (
                <div className="space-y-6">
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold">Total Employees</h4>
                      <Badge variant="outline" className="text-lg px-3 py-1">
                        {demographics.total_employees}
                      </Badge>
                    </div>
                  </div>

                  {demographics.demographics.gender && (
                    <div>
                      <h5 className="font-medium mb-3">Gender Distribution</h5>
                      <div className="space-y-2">
                        {Object.entries(demographics.demographics.gender).map(([gender, count]) => (
                          <div key={gender} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <span className="capitalize">{gender}</span>
                            <div className="flex items-center gap-3">
                              <div className="w-48 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full"
                                  style={{ width: `${(count / demographics.total_employees) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium w-16 text-right">
                                {count} ({Math.round((count / demographics.total_employees) * 100)}%)
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {demographics.demographics.race && (
                    <div>
                      <h5 className="font-medium mb-3">Racial/Ethnic Distribution</h5>
                      <div className="space-y-2">
                        {Object.entries(demographics.demographics.race).map(([race, count]) => (
                          <div key={race} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <span className="capitalize">{race}</span>
                            <div className="flex items-center gap-3">
                              <div className="w-48 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-green-600 h-2 rounded-full"
                                  style={{ width: `${(count / demographics.total_employees) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium w-16 text-right">
                                {count} ({Math.round((count / demographics.total_employees) * 100)}%)
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">No demographic data available</p>
                  <p className="text-sm">Demographic data collection is voluntary. Encourage employees to complete their profiles.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pay Equity Tab */}
        <TabsContent value="pay-equity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pay Equity Analysis</CardTitle>
              <CardDescription>
                Detailed analysis of compensation fairness across demographic groups
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <DollarSign className="h-12 w-12 mx-auto mb-4 text-blue-600" />
                <p className="text-lg font-medium mb-2">Detailed Pay Equity Report</p>
                <p className="text-sm text-gray-600 mb-4">
                  Comprehensive pay equity analysis requires HR/Admin access.
                </p>
                <Button variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Request Full Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Promotions Tab */}
        <TabsContent value="promotions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Promotion Equity Analysis</CardTitle>
              <CardDescription>
                Analysis of promotion rates and timing across demographic groups
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Award className="h-12 w-12 mx-auto mb-4 text-purple-600" />
                <p className="text-lg font-medium mb-2">Detailed Promotion Report</p>
                <p className="text-sm text-gray-600 mb-4">
                  Promotion equity analysis requires HR/Admin access.
                </p>
                <Button variant="outline">
                  <FileText className="h-4 w-4 mr-2" />
                  Request Full Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Recommended Actions
              </CardTitle>
              <CardDescription>
                Evidence-based recommendations to improve workplace equity
              </CardDescription>
            </CardHeader>
            <CardContent>
              {equityReport && equityReport.recommendations.length > 0 ? (
                <div className="space-y-3">
                  {equityReport.recommendations.map((recommendation, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-4 border rounded-lg hover:bg-blue-50">
                      <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <p className="text-sm">{recommendation}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50 text-green-600" />
                  <p className="text-lg font-medium mb-2">Looking Good!</p>
                  <p className="text-sm">No critical issues detected. Continue monitoring equity metrics.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Export Button */}
          <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold mb-1">Export Equity Report</h3>
                  <p className="text-sm opacity-90">Download comprehensive analysis and data</p>
                </div>
                <Button variant="secondary" size="lg">
                  <Download className="h-5 w-5 mr-2" />
                  Export Report
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default EquityDashboard;
