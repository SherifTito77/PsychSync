/**
 * De-Identification Tools Component
 *
 * Comprehensive interface for data anonymization, de-identification, and privacy compliance.
 * Supports multiple anonymization methods, risk assessment, and audit trail generation.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  Shield,
  EyeOff,
  Database,
  CheckCircle,
  AlertTriangle,
  Clock,
  Settings,
  Download,
  Upload,
  FileText,
  Users,
  Lock,
  Unlock,
  Activity,
  BarChart3,
  PieChart as PieChartIcon,
  Zap,
  Target,
  Scale,
  FileSearch,
  History,
} from 'lucide-react';

// Types
interface AnonymizationMethod {
  id: string;
  name: string;
  type: string;
  description: string;
  privacyRiskScore: number;
  dataUtilityScore: number;
  kAnonymityLevel?: number;
  lDiversityLevel?: number;
  tClosenessThreshold?: number;
  standards: string[];
}

interface QuasiIdentifier {
  name: string;
  type: string;
  generalizationHierarchy: string[];
  weight: number;
  isSensitive: boolean;
  selected: boolean;
}

interface AnonymizationJob {
  id: string;
  jobName: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  algorithm: AnonymizationMethod;
  inputRecords: number;
  outputRecords: number;
  privacyMetrics: {
    kAnonymityLevel: number;
    lDiversityLevel: number;
    tClosenessValue: number;
    reIdentificationRisk: number;
    uniquenessRisk: number;
  };
  dataUtilityScore: number;
  processingTime: number;
  createdAt: string;
  completedAt?: string;
}

interface DataSample {
  id: string;
  [key: string]: any;
}

interface PrivacyRiskAssessment {
  overallRisk: 'very_low' | 'low' | 'moderate' | 'high' | 'very_high';
  riskScore: number;
  riskFactors: string[];
  recommendations: string[];
  complianceScore: number;
}

interface DeIdentificationToolsProps {
  datasetName?: string;
  datasetSize?: number;
  availableAlgorithms?: AnonymizationMethod[];
  onAnonymizationComplete?: (jobId: string, results: any) => void;
}

const DeIdentificationTools: React.FC<DeIdentificationToolsProps> = ({
  datasetName,
  datasetSize = 1000,
  availableAlgorithms,
  onAnonymizationComplete,
}) => {
  const [selectedTab, setSelectedTab] = useState('setup');
  const [selectedMethod, setSelectedMethod] = useState<string>('');
  const [quasiIdentifiers, setQuasiIdentifiers] = useState<QuasiIdentifier[]>([
    { name: 'age', type: 'demographic', generalizationHierarchy: ['exact', '5-year_range', 'decade', 'adult/child'], weight: 1.0, isSensitive: false, selected: true },
    { name: 'zip_code', type: 'demographic', generalizationHierarchy: ['exact', 'first_3_digits', 'county', 'state'], weight: 1.2, isSensitive: false, selected: true },
    { name: 'job_title', type: 'organizational', generalizationHierarchy: ['exact', 'level', 'category', 'department'], weight: 0.8, isSensitive: false, selected: false },
    { name: 'salary', type: 'organizational', generalizationHierarchy: ['exact', '5k_range', '10k_range', 'quartile'], weight: 1.5, isSensitive: true, selected: true },
    { name: 'performance_score', type: 'behavioral', generalizationHierarchy: ['exact', 'decile', 'quartile', 'pass/fail'], weight: 1.0, isSensitive: false, selected: false },
  ]);
  const [sensitiveAttributes, setSensitiveAttributes] = useState<string[]>(['medical_conditions', 'assessment_results']);
  const [kThreshold, setKThreshold] = useState(5);
  const [lThreshold, setLThreshold] = useState(3);
  const [tThreshold, setTThreshold] = useState(0.2);
  const [currentJob, setCurrentJob] = useState<AnonymizationJob | null>(null);
  const [recentJobs, setRecentJobs] = useState<AnonymizationJob[]>([]);
  const [sampleData, setSampleData] = useState<DataSample[]>([]);

  // Mock algorithms data
  const mockAlgorithms: AnonymizationMethod[] = [
    {
      id: 'k_anonymity',
      name: 'K-Anonymity',
      type: 'generalization',
      description: 'Ensures each record is indistinguishable from at least k-1 other records',
      privacyRiskScore: 0.25,
      dataUtilityScore: 0.85,
      kAnonymityLevel: 5,
      standards: ['GDPR', 'HIPAA', 'CCPA'],
    },
    {
      id: 'l_diversity',
      name: 'L-Diversity',
      type: 'generalization',
      description: 'Ensures each equivalence class has at least l distinct sensitive values',
      privacyRiskScore: 0.20,
      dataUtilityScore: 0.80,
      kAnonymityLevel: 5,
      lDiversityLevel: 3,
      standards: ['GDPR', 'HIPAA'],
    },
    {
      id: 't_closeness',
      name: 'T-Closeness',
      type: 'generalization',
      description: 'Ensures distribution of sensitive values in each class close to overall distribution',
      privacyRiskScore: 0.15,
      dataUtilityScore: 0.75,
      kAnonymityLevel: 5,
      tClosenessThreshold: 0.2,
      standards: ['GDPR', 'HIPAA'],
    },
    {
      id: 'differential_privacy',
      name: 'Differential Privacy',
      type: 'perturbation',
      description: 'Adds calibrated noise to provide mathematical privacy guarantees',
      privacyRiskScore: 0.05,
      dataUtilityScore: 0.90,
      standards: ['GDPR', 'CCPA'],
    },
    {
      id: 'synthetic_data',
      name: 'Synthetic Data Generation',
      type: 'synthetic_data',
      description: 'Generates artificial data with similar statistical properties',
      privacyRiskScore: 0.02,
      dataUtilityScore: 0.70,
      standards: ['GDPR', 'HIPAA', 'CCPA'],
    },
  ];

  const algorithms = availableAlgorithms || mockAlgorithms;

  // Calculate privacy risk assessment
  const riskAssessment: PrivacyRiskAssessment = useMemo(() => {
    const selectedQI = quasiIdentifiers.filter(qi => qi.selected);
    const avgWeight = selectedQI.reduce((sum, qi) => sum + qi.weight, 0) / Math.max(selectedQI.length, 1);
    const sensitiveCount = selectedQI.filter(qi => qi.isSensitive).length;

    let riskScore = avgWeight * 0.3 + (sensitiveCount / selectedQI.length) * 0.7;
    riskScore = Math.min(1, Math.max(0, riskScore));

    let riskLevel: 'very_low' | 'low' | 'moderate' | 'high' | 'very_high';
    if (riskScore < 0.2) riskLevel = 'very_low';
    else if (riskScore < 0.4) riskLevel = 'low';
    else if (riskScore < 0.6) riskLevel = 'moderate';
    else if (riskScore < 0.8) riskLevel = 'high';
    else riskLevel = 'very_high';

    const riskFactors = [];
    if (sensitiveCount > 2) riskFactors.push('Multiple sensitive attributes selected');
    if (avgWeight > 1.2) riskFactors.push('High-weight quasi-identifiers');
    if (selectedQI.length > 5) riskFactors.push('Many quasi-identifiers selected');
    if (sensitiveCount > 0) riskFactors.push('Sensitive attributes included');

    const recommendations = [];
    if (riskScore > 0.6) recommendations.push('Consider using differential privacy for maximum protection');
    if (sensitiveCount > 0) recommendations.push('Apply additional suppression for sensitive values');
    if (selectedQI.length > 4) recommendations.push('Review necessity of all selected quasi-identifiers');
    if (riskScore < 0.3) recommendations.push('Current configuration provides good balance of privacy and utility');

    return {
      overallRisk: riskLevel,
      riskScore,
      riskFactors,
      recommendations,
      complianceScore: 1 - riskScore,
    };
  }, [quasiIdentifiers]);

  // Generate mock sample data
  useEffect(() => {
    const sample = Array.from({ length: 100 }, (_, i) => ({
      id: `sample_${i}`,
      age: Math.floor(Math.random() * 50) + 25,
      zip_code: `${Math.floor(Math.random() * 90000) + 10000}`,
      job_title: ['Manager', 'Developer', 'Analyst', 'Director', 'Specialist'][Math.floor(Math.random() * 5)],
      salary: Math.floor(Math.random() * 100000) + 40000,
      performance_score: Math.floor(Math.random() * 50) + 50,
      medical_conditions: ['None', 'Hypertension', 'Diabetes', 'Asthma'][Math.floor(Math.random() * 4)],
      assessment_results: Math.floor(Math.random() * 100),
    }));
    setSampleData(sample);
  }, []);

  const selectedAlgorithm = algorithms.find(alg => alg.id === selectedMethod);

  const handleStartAnonymization = () => {
    if (!selectedMethod) return;

    const newJob: AnonymizationJob = {
      id: `job_${Date.now()}`,
      jobName: `Anonymization - ${new Date().toLocaleDateString()}`,
      status: 'running',
      progress: 0,
      algorithm: selectedAlgorithm,
      inputRecords: datasetSize,
      outputRecords: Math.floor(datasetSize * 0.95), // Mock 5% data loss
      privacyMetrics: {
        kAnonymityLevel: kThreshold,
        lDiversityLevel: lThreshold,
        tClosenessValue: tThreshold,
        reIdentificationRisk: 0.15,
        uniquenessRisk: 0.25,
      },
      dataUtilityScore: 0.8,
      processingTime: 0,
      createdAt: new Date().toISOString(),
    };

    setCurrentJob(newJob);
    setRecentJobs([newJob, ...recentJobs.slice(0, 9)]);

    // Simulate processing
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setCurrentJob(prev => prev ? { ...prev, progress } : null);

      if (progress >= 100) {
        clearInterval(interval);
        setCurrentJob(prev => prev ? {
          ...prev,
          status: 'completed',
          progress: 100,
          completedAt: new Date().toISOString(),
          processingTime: 180, // 3 minutes
        } : null);

        onAnonymizationComplete?.(newJob.id, { success: true });
      }
    }, 500);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'very_low': return 'text-green-600';
      case 'low': return 'text-green-500';
      case 'moderate': return 'text-yellow-600';
      case 'high': return 'text-orange-600';
      case 'very_high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Prepare chart data
  const algorithmComparisonData = algorithms.map(alg => ({
    name: alg.name,
    privacy: alg.privacyRiskScore * 100,
    utility: alg.dataUtilityScore * 100,
    type: alg.type,
  }));

  const riskDistributionData = [
    { name: 'Very Low', value: recentJobs.filter(j => j.privacyMetrics.reIdentificationRisk < 0.1).length, color: '#10b981' },
    { name: 'Low', value: recentJobs.filter(j => j.privacyMetrics.reIdentificationRisk >= 0.1 && j.privacyMetrics.reIdentificationRisk < 0.3).length, color: '#22c55e' },
    { name: 'Moderate', value: recentJobs.filter(j => j.privacyMetrics.reIdentificationRisk >= 0.3 && j.privacyMetrics.reIdentificationRisk < 0.5).length, color: '#f59e0b' },
    { name: 'High', value: recentJobs.filter(j => j.privacyMetrics.reIdentificationRisk >= 0.5 && j.privacyMetrics.reIdentificationRisk < 0.7).length, color: '#f97316' },
    { name: 'Very High', value: recentJobs.filter(j => j.privacyMetrics.reIdentificationRisk >= 0.7).length, color: '#ef4444' },
  ];

  const utilityVsPrivacyData = recentJobs.map(job => ({
    jobName: job.jobName.split(' ')[1],
    utility: job.dataUtilityScore * 100,
    privacy: (1 - job.privacyMetrics.reIdentificationRisk) * 100,
  }));

  const renderSetupTab = () => (
    <div className="space-y-6">
      {/* Risk Assessment */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Scale className="h-5 w-5" />
            Privacy Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Overall Risk Level</span>
                <Badge className={getRiskColor(riskAssessment.overallRisk)}>
                  {riskAssessment.overallRisk.replace('_', ' ')}
                </Badge>
              </div>
              <Progress value={riskAssessment.riskScore * 100} className="mb-4" />

              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Compliance Score</span>
                <span className="text-sm">{(riskAssessment.complianceScore * 100).toFixed(1)}%</span>
              </div>
              <Progress value={riskAssessment.complianceScore * 100} className="mb-4" />
            </div>

            <div>
              <h4 className="font-semibold mb-2">Risk Factors</h4>
              <ul className="space-y-1 text-sm">
                {riskAssessment.riskFactors.map((factor, index) => (
                  <li key={index} className="flex items-center gap-2">
                    <AlertTriangle className="h-3 w-3 text-yellow-500" />
                    {factor}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {riskAssessment.recommendations.length > 0 && (
            <Alert className="mt-4">
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Recommendations</AlertTitle>
              <AlertDescription>
                <ul className="mt-2 space-y-1">
                  {riskAssessment.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm">• {rec}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Algorithm Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Anonymization Method
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {algorithms.map((algorithm) => (
              <div
                key={algorithm.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedMethod === algorithm.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedMethod(algorithm.id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{algorithm.name}</h3>
                  <Badge variant="outline">{algorithm.type}</Badge>
                </div>
                <p className="text-sm text-gray-600 mb-3">{algorithm.description}</p>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Privacy Protection:</span>
                    <span className={algorithm.privacyRiskScore < 0.3 ? 'text-green-600' : 'text-yellow-600'}>
                      {((1 - algorithm.privacyRiskScore) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>Data Utility:</span>
                    <span className={algorithm.dataUtilityScore > 0.7 ? 'text-green-600' : 'text-yellow-600'}>
                      {(algorithm.dataUtilityScore * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-1">
                  {algorithm.standards.slice(0, 2).map((standard, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {standard}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quasi-Identifiers Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <EyeOff className="h-5 w-5" />
            Quasi-Identifiers Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {quasiIdentifiers.map((qi, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={qi.selected}
                    onChange={(e) => {
                      const updated = [...quasiIdentifiers];
                      updated[index].selected = e.target.checked;
                      setQuasiIdentifiers(updated);
                    }}
                    className="rounded"
                  />
                  <div>
                    <div className="font-medium">{qi.name}</div>
                    <div className="text-sm text-gray-600">
                      Type: {qi.type} • Weight: {qi.weight}
                      {qi.isSensitive && <span className="text-red-600 ml-2">• Sensitive</span>}
                    </div>
                  </div>
                </div>

                <div className="text-sm text-gray-600">
                  {qi.generalizationHierarchy.length} levels
                </div>
              </div>
            ))}
          </div>

          {/* Parameter Configuration */}
          {selectedMethod && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold mb-3">Algorithm Parameters</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">K-Anonymity Threshold</label>
                  <input
                    type="number"
                    value={kThreshold}
                    onChange={(e) => setKThreshold(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                    min="2"
                    max="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">L-Diversity Threshold</label>
                  <input
                    type="number"
                    value={lThreshold}
                    onChange={(e) => setLThreshold(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                    min="1"
                    max="10"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">T-Closeness Threshold</label>
                  <input
                    type="number"
                    value={tThreshold}
                    onChange={(e) => setTThreshold(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    max="1"
                    step="0.01"
                  />
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex justify-end gap-4">
        <Button variant="outline">
          <Upload className="h-4 w-4 mr-2" />
          Upload Dataset
        </Button>
        <Button
          onClick={handleStartAnonymization}
          disabled={!selectedMethod || currentJob?.status === 'running'}
        >
          <Shield className="h-4 w-4 mr-2" />
          Start Anonymization
        </Button>
      </div>
    </div>
  );

  const renderMonitoringTab = () => (
    <div className="space-y-6">
      {/* Current Job Status */}
      {currentJob && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Current Job: {currentJob.jobName}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Progress</span>
                  <span className="text-sm">{currentJob.progress}%</span>
                </div>
                <Progress value={currentJob.progress} />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Status: </span>
                  <Badge className={getStatusColor(currentJob.status)}>
                    {currentJob.status}
                  </Badge>
                </div>
                <div>
                  <span className="text-gray-600">Algorithm: </span>
                  {currentJob.algorithm.name}
                </div>
                <div>
                  <span className="text-gray-600">Records: </span>
                  {currentJob.inputRecords} → {currentJob.outputRecords}
                </div>
                <div>
                  <span className="text-gray-600">Duration: </span>
                  {Math.floor(currentJob.processingTime / 60)}m {currentJob.processingTime % 60}s
                </div>
              </div>

              {currentJob.status === 'completed' && (
                <div className="mt-4 p-3 bg-green-50 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">K-Anonymity: </span>
                      <span className="font-medium">{currentJob.privacyMetrics.kAnonymityLevel}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Data Utility: </span>
                      <span className="font-medium">{(currentJob.dataUtilityScore * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Risk Score: </span>
                      <span className="font-medium">{(currentJob.privacyMetrics.reIdentificationRisk * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Jobs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Recent Anonymization Jobs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentJobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="font-medium">{job.jobName}</div>
                  <div className="text-sm text-gray-600">
                    {job.algorithm.name} • {new Date(job.createdAt).toLocaleDateString()}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right text-sm">
                    <div>Utility: {(job.dataUtilityScore * 100).toFixed(0)}%</div>
                    <div>Risk: {(job.privacyMetrics.reIdentificationRisk * 100).toFixed(0)}%</div>
                  </div>

                  <Badge className={getStatusColor(job.status)}>
                    {job.status}
                  </Badge>

                  {job.status === 'completed' && (
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      {/* Algorithm Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Algorithm Performance Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={algorithmComparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="privacy" fill="#10b981" name="Privacy Score" />
              <Bar dataKey="utility" fill="#3b82f6" name="Utility Score" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Risk Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5" />
              Risk Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={riskDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Utility vs Privacy Trade-off
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={utilityVsPrivacyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="jobName" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="utility" stroke="#3b82f6" name="Utility" />
                <Line type="monotone" dataKey="privacy" stroke="#10b981" name="Privacy" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Dataset Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Dataset Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{datasetSize.toLocaleString()}</div>
              <p className="text-sm text-gray-600">Total Records</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{quasiIdentifiers.filter(qi => qi.selected).length}</div>
              <p className="text-sm text-gray-600">Quasi-Identifiers</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{sensitiveAttributes.length}</div>
              <p className="text-sm text-gray-600">Sensitive Attributes</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{recentJobs.length}</div>
              <p className="text-sm text-gray-600">Total Jobs</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data De-Identification Tools</h1>
          <p className="text-muted-foreground">
            {datasetName ? `Dataset: ${datasetName}` : 'Advanced privacy-preserving data anonymization'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Shield className="h-3 w-3" />
            {algorithms.length} Algorithms
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {recentJobs.length} Jobs
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-4">
          {renderSetupTab()}
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          {renderMonitoringTab()}
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          {renderAnalyticsTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DeIdentificationTools;
