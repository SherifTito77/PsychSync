/**
 * Analysis History Hook
 *
 * Manages analysis history and selection
 */

import { useState } from 'react';
import { AnalysisResult } from '../types';
import { MOCK_ANALYSIS_HISTORY } from '../constants/mockData';

export const useAnalysisHistory = () => {
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisResult[]>(MOCK_ANALYSIS_HISTORY);
  const [selectedAnalysis, setSelectedAnalysis] = useState<AnalysisResult | null>(null);

  const selectAnalysis = (analysisId: string) => {
    const analysis = analysisHistory.find(a => a.analysis_id === analysisId);
    if (analysis) {
      setSelectedAnalysis(analysis);
    }
  };

  const addAnalysis = (analysis: AnalysisResult) => {
    setAnalysisHistory(prev => [analysis, ...prev]);
  };

  return {
    analysisHistory,
    selectedAnalysis,
    setSelectedAnalysis,
    selectAnalysis,
    addAnalysis,
  };
};
