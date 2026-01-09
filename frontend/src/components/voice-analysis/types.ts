/**
 * Voice & Video Analysis Types
 *
 * Type definitions for voice/video recording and AI analysis
 */

export interface AnalysisResult {
  analysis_id: string;
  user_id: string;
  video_path: string;
  duration: number;
  transcription: {
    text: string;
    language: string;
    confidence: number;
    word_timestamps: Array<[number, number, string]>;
    processing_time: number;
  };
  facial_analysis: Array<{
    timestamp: number;
    primary_emotion: string;
    emotion_confidence: number;
    attention_score: number;
    eye_contact: boolean;
    engagement_indicators: string[];
  }>;
  voice_sentiment: Array<{
    timestamp: number;
    sentiment: string;
    sentiment_confidence: number;
    confidence_score: number;
    speech_rate: number;
    clarity_score: number;
    stress_indicators: string[];
  }>;
  overall_sentiment: string;
  overall_confidence: number;
  engagement_score: number;
  authenticity_score: number;
  recommendations: string[];
  insights: string[];
  risk_assessment: {
    risk_level: string;
    risk_factors: string[];
  };
}

export interface RecordingConfig {
  maxDuration: number;
  quality: string;
  format: string;
  includeAudio: boolean;
  autoTranscription: boolean;
}

export interface EmotionTimelineData {
  time: number;
  emotion: string;
  confidence: number;
  attention: number;
}

export interface SentimentTimelineData {
  time: number;
  sentiment: string;
  confidence: number;
  clarity: number;
}

export interface EmotionChartData {
  name: string;
  value: number;
  fill: string;
}
