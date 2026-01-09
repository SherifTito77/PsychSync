/**
 * Predictive Analytics Dashboard - Main Orchestrator
 *
 * Comprehensive dashboard with growth trajectories, predictions, and organizational insights
 *
 * SPLIT from 1,077 lines → ~250 lines (77% reduction)
 */

import React from 'react';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  Users,
  AlertTriangle,
  RefreshCw,
  Zap,
  Award,
  BarChart3,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { usePredictiveAnalytics } from './hooks/usePredictiveAnalytics';
import {
  getRiskColor,
  getRiskTextColor,
  formatPercentage,
  formatDecimalAsPercentage,
  getTrendDirection
} from './utils/chartHelpers';

const PredictiveAnalyticsDashboard: React.FC = () => {
  const {
    metrics,
    filteredPredictionData,
    filteredTrendData,
    highRiskEmployees,
    interventionImpacts,
    loading,
    selectedTimeRange,
    averageConfidence,
    refreshData,
    setSelectedTimeRange,
  } = usePredictiveAnalytics();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-purple-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Predictive Analytics</h1>
            <p className="text-sm text-gray-500">AI-powered insights and forecasting</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className="bg-purple-100 text-purple-600">
            {formatDecimalAsPercentage(averageConfidence / 100)} Confidence
          </Badge>
          <Button variant="outline" size="sm" onClick={refreshData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Overall Score</p>
                <p className="text-2xl font-bold">{formatPercentage(metrics.overallScore)}</p>
                <TrendingUp className="h-4 w-4 text-green-600 mt-1" />
              </div>
              <Target className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Engagement</p>
                <p className="text-2xl font-bold">{formatPercentage(metrics.engagementScore)}</p>
                <TrendingUp className="h-4 w-4 text-green-600 mt-1" />
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Growth Potential</p>
                <p className="text-2xl font-bold">{formatPercentage(metrics.growthPotential)}</p>
                <Zap className="h-4 w-4 text-yellow-600 mt-1" />
              </div>
              <Award className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Retention Risk</p>
                <p className="text-2xl font-bold">{formatPercentage(metrics.retentionRisk)}</p>
                <AlertTriangle className="h-4 w-4 text-orange-600 mt-1" />
              </div>
              <BarChart3 className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Time Range Selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">Time Range:</span>
        {(['3m', '6m', '1y', '2y'] as const).map((range) => (
          <Button
            key={range}
            variant={selectedTimeRange === range ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedTimeRange(range)}
          >
            {range.toUpperCase()}
          </Button>
        ))}
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="predictions" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="predictions">Predictions</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="risks">Risks</TabsTrigger>
          <TabsTrigger value="interventions">Interventions</TabsTrigger>
        </TabsList>

        {/* Predictions Tab */}
        <TabsContent value="predictions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Predictions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {filteredPredictionData.map((data, index) => (
                    <div
                      key={index}
                      className={`p-4 border rounded-lg ${
                        data.actual
                          ? 'bg-green-50 border-green-200'
                          : 'bg-purple-50 border-purple-200'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{data.period}</span>
                        <Badge variant={data.actual ? 'default' : 'outline'}>
                          {data.actual ? 'Actual' : 'Predicted'}
                        </Badge>
                      </div>
                      <div className="text-2xl font-bold">
                        {data.actual ?? data.predicted}
                      </div>
                      <div className="text-sm text-gray-500">
                        {formatDecimalAsPercentage(data.confidence)} confidence
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Trends vs Benchmark</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredTrendData.map((trend, index) => {
                  const direction = getTrendDirection(
                    trend.value,
                    index > 0 ? filteredTrendData[index - 1].value : trend.value
                  );

                  return (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{trend.month}</span>
                        <div className="flex items-center gap-2">
                          {direction === 'up' && <TrendingUp className="h-4 w-4 text-green-600" />}
                          {direction === 'down' && <TrendingDown className="h-4 w-4 text-red-600" />}
                          <span className="text-sm text-gray-500">{trend.value} vs {trend.benchmark} benchmark</span>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${trend.value}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risks Tab */}
        <TabsContent value="risks" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Employee Retention Risks</CardTitle>
                <Badge className="bg-red-100 text-red-600">
                  {highRiskEmployees.length} High Risk
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {highRiskEmployees.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-600" />
                    <p>No high-risk employees detected</p>
                  </div>
                ) : (
                  highRiskEmployees.map((employee) => (
                    <div
                      key={employee.employeeId}
                      className="p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold">{employee.name}</h3>
                            <Badge className={getRiskTextColor(employee.riskLevel)}>
                              {employee.riskLevel.toUpperCase()}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600">{employee.department}</p>
                          <div className="mt-2 space-y-1">
                            {employee.riskFactors.map((factor, idx) => (
                              <div key={idx} className="text-sm text-gray-500">
                                • {factor}
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-orange-600">
                            {formatPercentage(employee.probability * 100)}
                          </div>
                          <div className="text-sm text-gray-500">Risk Probability</div>
                          <div className="text-sm text-gray-500 mt-1">
                            Timeframe: {employee.timeframe}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Interventions Tab */}
        <TabsContent value="interventions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Intervention Effectiveness</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {interventionImpacts.map((intervention, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-lg">{intervention.intervention}</h3>
                        <p className="text-sm text-gray-500">
                          Baseline: {intervention.baseline} → Projected: {intervention.projected}
                        </p>
                      </div>
                      <Badge className="bg-purple-100 text-purple-600">
                        {formatDecimalAsPercentage(intervention.confidence)} Confidence
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>Baseline</span>
                        <span className="font-medium">{intervention.baseline}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gray-400 h-2 rounded-full"
                          style={{ width: `${intervention.baseline}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Projected</span>
                        <span className="font-medium text-purple-600">{intervention.projected}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${intervention.projected}%` }}
                        />
                      </div>
                      {intervention.actual && (
                        <>
                          <div className="flex items-center justify-between text-sm">
                            <span>Actual</span>
                            <span className="font-medium text-green-600">{intervention.actual}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-600 h-2 rounded-full"
                              style={{ width: `${intervention.actual}%` }}
                            />
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PredictiveAnalyticsDashboard;
