/**
 * Voice & Video Analysis Mock Data
 *
 * Simulated analysis results for development/testing
 */

import { AnalysisResult } from '../types';

export const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const DEFAULT_RECORDING_CONFIG = {
  maxDuration: 300,
  quality: 'high',
  format: 'mp4',
  includeAudio: true,
  autoTranscription: true,
};

export const MOCK_ANALYSIS_RESULT: AnalysisResult = {
  analysis_id: 'analysis_001',
  user_id: 'user_001',
  video_path: '/videos/analysis_001.mp4',
  duration: 45.2,
  transcription: {
    text: 'I believe that my leadership style focuses on empowering team members through clear communication and setting achievable goals. I find that when people understand the vision and their role in achieving it, they become more motivated and engaged.',
    language: 'en-US',
    confidence: 0.94,
    word_timestamps: [
      [0, 0.5, 'I'],
      [0.5, 1.2, 'believe'],
      [1.2, 1.8, 'that']
    ],
    processing_time: 2.3,
  },
  facial_analysis: [
    {
      timestamp: 0,
      primary_emotion: 'happy',
      emotion_confidence: 0.85,
      attention_score: 0.92,
      eye_contact: true,
      engagement_indicators: ['maintains_eye_contact', 'high_attention'],
    },
    {
      timestamp: 15,
      primary_emotion: 'engaged',
      emotion_confidence: 0.78,
      attention_score: 0.88,
      eye_contact: true,
      engagement_indicators: ['clear_expressions', 'focused'],
    },
    {
      timestamp: 30,
      primary_emotion: 'neutral',
      emotion_confidence: 0.72,
      attention_score: 0.85,
      eye_contact: true,
      engagement_indicators: ['steady_gaze', 'composed'],
    },
  ],
  voice_sentiment: [
    {
      timestamp: 0,
      sentiment: 'positive',
      sentiment_confidence: 0.87,
      confidence_score: 0.91,
      speech_rate: 145,
      clarity_score: 0.89,
      stress_indicators: [],
    },
    {
      timestamp: 20,
      sentiment: 'positive',
      sentiment_confidence: 0.82,
      confidence_score: 0.88,
      speech_rate: 152,
      clarity_score: 0.91,
      stress_indicators: [],
    },
  ],
  overall_sentiment: 'positive',
  overall_confidence: 0.86,
  engagement_score: 0.89,
  authenticity_score: 0.79,
  recommendations: [
    'Excellent eye contact and engagement throughout',
    'Consider varying pace slightly for better emphasis',
    'Strong vocal confidence and clarity detected',
  ],
  insights: [
    'High engagement level detected throughout the response',
    'Strong vocal confidence and clarity detected',
    'Emotional consistency shows authentic communication',
  ],
  risk_assessment: {
    risk_level: 'low',
    risk_factors: [],
  },
};

export const MOCK_ANALYSIS_HISTORY: AnalysisResult[] = [MOCK_ANALYSIS_RESULT];
