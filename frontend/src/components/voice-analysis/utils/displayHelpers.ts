/**
 * Display Helper Utilities
 *
 * Functions for formatting and styling analysis results
 */

import React from 'react';
import { Smile, Frown, Meh } from 'lucide-react';

/**
 * Get sentiment icon component
 */
export const getSentimentIcon = (sentiment: string): React.ReactElement => {
  switch (sentiment) {
    case 'positive':
      return <Smile className="h-4 w-4 text-green-500" />;
    case 'negative':
      return <Frown className="h-4 w-4 text-red-500" />;
    case 'neutral':
      return <Meh className="h-4 w-4 text-gray-500" />;
    default:
      return <Meh className="h-4 w-4 text-gray-500" />;
  }
};

/**
 * Get risk color classes
 */
export const getRiskColor = (level: string): string => {
  switch (level) {
    case 'low':
      return 'text-green-600 bg-green-50';
    case 'medium':
      return 'text-yellow-600 bg-yellow-50';
    case 'high':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-600 bg-gray-50';
  }
};

/**
 * Format seconds to MM:SS
 */
export const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

/**
 * Prepare emotion timeline data for charts
 */
export const prepareEmotionTimeline = (facialAnalysis: any[]) => {
  return facialAnalysis.map(point => ({
    time: point.timestamp,
    emotion: point.primary_emotion,
    confidence: point.emotion_confidence * 100,
    attention: point.attention_score * 100,
  }));
};

/**
 * Prepare sentiment timeline data for charts
 */
export const prepareSentimentTimeline = (voiceSentiment: any[]) => {
  return voiceSentiment.map(point => ({
    time: point.timestamp,
    sentiment: point.sentiment,
    confidence: point.sentiment_confidence * 100,
    clarity: point.clarity_score * 100,
  }));
};

/**
 * Prepare emotion distribution data for pie chart
 */
export const prepareEmotionDistribution = (facialAnalysis: any[], colors: string[]) => {
  const emotionDistribution = facialAnalysis.reduce((acc, point) => {
    acc[point.primary_emotion] = (acc[point.primary_emotion] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return Object.entries(emotionDistribution).map(([emotion, count]) => ({
    name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
    value: count,
    fill: colors[Object.keys(emotionDistribution).indexOf(emotion) % colors.length]
  }));
};
