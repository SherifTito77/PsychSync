/**
 * Voice & Video Analysis - Main Orchestrator
 *
 * AI-powered voice and video analysis for behavioral insights
 *
 * SPLIT from 1,120 lines → ~200 lines (82% reduction)
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Mic, Video, Brain, BarChart3 } from 'lucide-react';

import { RecordingConfig } from './types';
import { DEFAULT_RECORDING_CONFIG, COLORS } from './constants/mockData';
import { useVoiceRecording } from './hooks/useVoiceRecording';
import { useAnalysisHistory } from './hooks/useAnalysisHistory';
import {
  getSentimentIcon,
  getRiskColor,
  formatTime,
  prepareEmotionTimeline,
  prepareSentimentTimeline,
  prepareEmotionDistribution,
} from './utils/displayHelpers.tsx';

const VoiceVideoAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('recording');
  const [recordingConfig, setRecordingConfig] = useState<RecordingConfig>(DEFAULT_RECORDING_CONFIG);

  // Custom hooks
  const {
    isRecording,
    recordingTime,
    isProcessing,
    videoRef,
    startRecording,
    stopRecording,
  } = useVoiceRecording(recordingConfig);

  const {
    analysisHistory,
    selectedAnalysis,
    setSelectedAnalysis,
    selectAnalysis,
  } = useAnalysisHistory();

  // Prepare chart data
  const emotionTimelineData = selectedAnalysis
    ? prepareEmotionTimeline(selectedAnalysis.facial_analysis)
    : [];

  const sentimentTimelineData = selectedAnalysis
    ? prepareSentimentTimeline(selectedAnalysis.voice_sentiment)
    : [];

  const emotionChartData = selectedAnalysis
    ? prepareEmotionDistribution(selectedAnalysis.facial_analysis, COLORS)
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Voice & Video Analysis</h1>
            <p className="text-sm text-gray-500">AI-powered behavioral insights from voice and video</p>
          </div>
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="recording">Recording</TabsTrigger>
          <TabsTrigger value="results">Analysis Results</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Recording Tab */}
        <TabsContent value="recording" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Video className="h-5 w-5" />
                Record Video for Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-black rounded-lg aspect-video flex items-center justify-center">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  className="w-full h-full rounded-lg"
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="text-2xl font-mono">
                  {formatTime(recordingTime)}
                </div>
                <div className="flex gap-2">
                  {!isRecording ? (
                    <Button
                      onClick={startRecording}
                      className="flex items-center gap-2"
                      disabled={isProcessing}
                    >
                      <Mic className="h-4 w-4" />
                      Start Recording
                    </Button>
                  ) : (
                    <Button
                      onClick={stopRecording}
                      variant="danger"
                      className="flex items-center gap-2"
                    >
                      Stop Recording
                    </Button>
                  )}
                </div>
              </div>

              {isProcessing && (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Processing video with AI...</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recording Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Max Duration (seconds)</label>
                  <input
                    type="number"
                    value={recordingConfig.maxDuration}
                    onChange={(e) => setRecordingConfig({
                      ...recordingConfig,
                      maxDuration: parseInt(e.target.value)
                    })}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Quality</label>
                  <select
                    value={recordingConfig.quality}
                    onChange={(e) => setRecordingConfig({
                      ...recordingConfig,
                      quality: e.target.value
                    })}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {!selectedAnalysis ? (
            <Card>
              <CardContent className="p-12 text-center text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select an analysis from history to view results</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Overview */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {(selectedAnalysis.overall_confidence * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-gray-500">Confidence</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {(selectedAnalysis.engagement_score * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-gray-500">Engagement</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {(selectedAnalysis.authenticity_score * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-gray-500">Authenticity</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${getRiskColor(selectedAnalysis.risk_assessment.risk_level)}`}>
                        {selectedAnalysis.risk_assessment.risk_level.toUpperCase()}
                      </div>
                      <p className="text-sm text-gray-500">Risk Level</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Transcription */}
              <Card>
                <CardHeader>
                  <CardTitle>Transcription</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 mb-2">
                    {getSentimentIcon(selectedAnalysis.overall_sentiment)}
                    <Badge className="capitalize">{selectedAnalysis.overall_sentiment}</Badge>
                    <span className="text-sm text-gray-500">
                      {selectedAnalysis.transcription.language} • {(selectedAnalysis.transcription.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <p className="text-gray-700 leading-relaxed">
                    {selectedAnalysis.transcription.text}
                  </p>
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {selectedAnalysis.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-blue-500 mt-1">•</span>
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {analysisHistory.map((analysis) => (
            <Card
              key={analysis.analysis_id}
              className={`cursor-pointer transition-colors ${
                selectedAnalysis?.analysis_id === analysis.analysis_id
                  ? 'ring-2 ring-blue-500'
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => selectAnalysis(analysis.analysis_id)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">Analysis {analysis.analysis_id}</h3>
                      <Badge className={getRiskColor(analysis.risk_assessment.risk_level)}>
                        {analysis.risk_assessment.risk_level}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>Duration: {formatTime(analysis.duration)}</span>
                      <span className="flex items-center gap-1">
                        {getSentimentIcon(analysis.overall_sentiment)}
                        <span className="capitalize">{analysis.overall_sentiment}</span>
                      </span>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default VoiceVideoAnalysis;
