import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import WellnessQuestionSelector, { WellnessDomain as ImportedWellnessDomain, WellnessQuestion } from '@/data/wellnessQuestionBank';
import EnhancedWellnessAI, { AdvancedWellnessAnalysis, WellnessResponse } from '@/services/enhancedWellnessAI';

// Use local interfaces to avoid conflicts
interface WellnessDomain {
  id: string;
  name: string;
  icon: string;
  description: string;
  weight: number;
  color: string;
  questions: WellnessQuestion[];
}

interface WellnessAssessmentData {
  assessment_type: string;
  domains: WellnessDomain[];
  total_questions: number;
  estimated_time: string;
  description: string;
}

interface WellnessResults {
  success: boolean;
  wellness_result: {
    overall_score: number;
    wellness_level: string;
    domain_scores: Record<string, {
      score: number;
      level: string;
      weight: number;
    }>;
    domain_insights: Record<string, {
      score: number;
      level: string;
      strengths: string[];
      areas_for_improvement: string[];
      description: string;
    }>;
    recommendations: Array<{
      type: string;
      title: string;
      description: string;
      priority: string;
    }>;
    trend_analysis: {
      trend: string;
      trajectory: string;
      message: string;
    };
    ai_insights: {
      strengths_analysis: {
        domains: string[];
        message: string;
      };
      improvement_opportunities: {
        domains: string[];
        message: string;
      };
      holistic_insights: {
        balance_score: number;
        recommendation: string;
      };
      confidence_level: number;
      generated_at: string;
    };
    completed_at: string;
    next_recommended_assessment: string;
  };
}

/**
 * Enhanced Wellness Assessment with Randomized Question Selection
 * Uses comprehensive question bank with 10+ questions per domain
 */
const generateEnhancedWellnessAssessment = (): WellnessDomain[] => {
  const domains = ['physical', 'mental', 'emotional', 'social'];
  const selectedQuestions = WellnessQuestionSelector.selectRandomQuestions(
    domains,
    10, // 10 questions per domain = 40 total questions
    undefined, // Mix all difficulty levels
    undefined // Include all categories
  );

  const domainMetadata = WellnessQuestionSelector.getDomainMetadata();

  return domains.map(domainId => ({
    ...domainMetadata[domainId],
    questions: selectedQuestions[domainId] || []
  }));
};

// Demo wellness results for development/testing
const generateDemoWellnessResults = (): WellnessResults => {
  const overallScore = (Math.floor(Math.random() * 30) + 60) / 100; // 0.60-0.90 range
  const wellnessLevel = overallScore >= 0.85 ? 'Excellent' : overallScore >= 0.70 ? 'Good' : overallScore >= 0.55 ? 'Fair' : 'Poor';

  return {
    success: true,
    wellness_result: {
      overall_score: overallScore,
      wellness_level: wellnessLevel,
      domain_scores: {
        physical: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          weight: 0.25
        },
        mental: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          weight: 0.25
        },
        emotional: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          weight: 0.25
        },
        social: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          weight: 0.25
        }
      },
      domain_insights: {
        physical: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          strengths: ['Regular exercise routine', 'Good sleep patterns'],
          areas_for_improvement: ['Increase daily movement', 'Balance nutrition'],
          description: 'Your physical wellness shows room for improvement in daily activity levels.'
        },
        mental: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          strengths: ['Good stress management techniques', 'Mindfulness practice'],
          areas_for_improvement: ['Regular mental breaks', 'Cognitive challenges'],
          description: 'Your mental wellness benefits from consistent practice.'
        },
        emotional: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          strengths: ['Emotional awareness', 'Healthy expression'],
          areas_for_improvement: ['Emotional regulation techniques', 'Support network'],
          description: 'Your emotional intelligence is developing well.'
        },
        social: {
          score: (Math.floor(Math.random() * 30) + 60) / 100,
          level: ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][Math.floor(Math.random() * 5)],
          strengths: ['Quality relationships', 'Community involvement'],
          areas_for_improvement: ['Expand social circle', 'Deepen connections'],
          description: 'Your social connections provide good support.'
        }
      },
      recommendations: [
        {
          type: 'physical',
          title: 'Increase Physical Activity',
          description: 'Aim for 30 minutes of moderate exercise 5 days a week to improve energy and mood.',
          priority: 'high'
        },
        {
          type: 'mental',
          title: 'Practice Mindfulness',
          description: 'Take 10 minutes daily for meditation or deep breathing exercises to reduce stress.',
          priority: 'medium'
        },
        {
          type: 'emotional',
          title: 'Journal for Emotional Health',
          description: 'Write down your thoughts and feelings regularly to process emotions effectively.',
          priority: 'low'
        }
      ],
      trend_analysis: {
        trend: 'improving',
        trajectory: 'positive',
        message: 'Your wellness metrics show positive movement over time. Keep up the good work!'
      },
      ai_insights: {
        strengths_analysis: {
          domains: ['physical', 'social'],
          message: 'You demonstrate strong physical health habits and maintain supportive social connections.'
        },
        improvement_opportunities: {
          domains: ['mental', 'emotional'],
          message: 'Focus on developing mental resilience and emotional regulation techniques.'
        },
        holistic_insights: {
          balance_score: 0.75,
          recommendation: 'Maintain current strengths while addressing improvement areas for optimal wellness balance.'
        },
        confidence_level: 0.85,
        generated_at: new Date().toISOString()
      },
      completed_at: new Date().toISOString(),
      next_recommended_assessment: '3 months'
    }
  };
};

const WellnessAssessmentForm: React.FC = () => {
  const [assessmentData, setAssessmentData] = useState<WellnessAssessmentData | null>(null);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [currentDomainIndex, setCurrentDomainIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<WellnessResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeAssessment();
  }, []);

  const initializeAssessment = () => {
    try {
      console.log('Initializing Enhanced Wellness Assessment with randomized questions');

      // Generate enhanced assessment with randomized questions
      const enhancedQuestions = generateEnhancedWellnessAssessment();
      const totalQuestions = enhancedQuestions.reduce((sum, domain) => sum + domain.questions.length, 0);

      setAssessmentData({
        assessment_type: 'enhanced_wellness',
        domains: enhancedQuestions,
        total_questions: totalQuestions,
        estimated_time: `${Math.ceil(totalQuestions / 4)}-${Math.ceil(totalQuestions / 3)} minutes`, // ~15 seconds per question
        description: 'Comprehensive AI-enhanced wellness assessment with randomized questions across physical, mental, emotional, and social domains'
      });

      console.log(`Enhanced assessment initialized with ${totalQuestions} questions across ${enhancedQuestions.length} domains`);
    } catch (err) {
      console.error('Error initializing wellness assessment:', err);
      setError('Failed to initialize assessment');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResponseChange = (questionId: string, value: number) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const getCurrentQuestion = () => {
    if (!assessmentData) return null;
    const currentDomain = assessmentData.domains[currentDomainIndex];
    return currentDomain.questions[currentQuestionIndex];
  };

  const getCurrentDomain = () => {
    if (!assessmentData) return null;
    return assessmentData.domains[currentDomainIndex];
  };

  const getTotalProgress = () => {
    if (!assessmentData) return 0;
    const totalQuestions = assessmentData.total_questions;
    const answeredQuestions = Object.keys(responses).length;
    return (answeredQuestions / totalQuestions) * 100;
  };

  const getDomainProgress = () => {
    if (!assessmentData) return 0;
    const currentDomain = assessmentData.domains[currentDomainIndex];
    const domainQuestions = currentDomain.questions;
    const answeredInDomain = domainQuestions.filter(q => q.id in responses).length;
    return (answeredInDomain / domainQuestions.length) * 100;
  };

  const handleNext = () => {
    if (!assessmentData) return;

    const currentDomain = assessmentData.domains[currentDomainIndex];
    if (currentQuestionIndex < currentDomain.questions.length - 1) {
      // Next question in current domain
      setCurrentQuestionIndex(prev => prev + 1);
    } else if (currentDomainIndex < assessmentData.domains.length - 1) {
      // Next domain
      setCurrentDomainIndex(prev => prev + 1);
      setCurrentQuestionIndex(0);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      // Previous question in current domain
      setCurrentQuestionIndex(prev => prev - 1);
    } else if (currentDomainIndex > 0) {
      // Previous domain
      setCurrentDomainIndex(prev => prev - 1);
      setCurrentQuestionIndex(assessmentData!.domains[currentDomainIndex - 1].questions.length - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      console.log('Processing wellness assessment with Enhanced AI engine...');

      // Convert responses to WellnessResponse format for AI processing
      const wellnessResponses: WellnessResponse[] = Object.entries(responses).map(([questionId, value]) => {
        // Extract domain from question ID
        const domain = questionId.split('_')[0];
        const category = assessmentData?.domains
          .find(d => d.questions.find(q => q.id === questionId))
          ?.questions.find(q => q.id === questionId)?.category || 'behavioral';

        return {
          questionId,
          value: value as number,
          domain,
          category,
          timestamp: new Date()
        };
      });

      // Initialize Enhanced AI Engine
      const aiEngine = new EnhancedWellnessAI(wellnessResponses);

      // Process with AI
      const aiAnalysis: AdvancedWellnessAnalysis = aiEngine.analyzeResponses(wellnessResponses);

      // Convert AI analysis to expected result format
      const enhancedResults = convertAIToWellnessResults(aiAnalysis);

      console.log('Enhanced wellness analysis completed:', {
        overallScore: Math.round(aiAnalysis.overallScore * 100),
        domainCount: Object.keys(aiAnalysis.domainScores).length,
        recommendations: aiAnalysis.recommendations.length,
        patterns: aiAnalysis.patterns.length,
        confidence: Math.round(aiAnalysis.aiConfidence * 100)
      });

      setResults(enhancedResults);

    } catch (err) {
      console.error('Error processing wellness assessment:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Convert Enhanced AI Analysis to Wellness Results format
   */
  const convertAIToWellnessResults = (aiAnalysis: AdvancedWellnessAnalysis): WellnessResults => {
    return {
      success: true,
      wellness_result: {
        overall_score: aiAnalysis.overallScore,
        wellness_level: aiAnalysis.wellnessLevel,
        domain_scores: Object.entries(aiAnalysis.domainScores).reduce((acc, [domain, score]) => {
          acc[domain] = {
            score: (score as any).score,
            level: (score as any).level,
            weight: 1.0
          };
          return acc;
        }, {} as Record<string, any>),
        domain_insights: Object.entries(aiAnalysis.domainScores).reduce((acc, [domain, score]) => {
          acc[domain] = {
            score: (score as any).score,
            level: (score as any).level,
            strengths: aiAnalysis.strengths
              .filter(s => s.domains.includes(domain))
              .map(s => s.strength),
            areas_for_improvement: aiAnalysis.risks
              .filter(r => r.domains.includes(domain))
              .map(r => r.risk),
            description: `${domain} wellness is ${score.level.toLowerCase()} with ${score.trend === 'improving' ? 'positive' : score.trend === 'declining' ? 'negative' : 'stable'} trends.`
          };
          return acc;
        }, {} as Record<string, any>),
        recommendations: aiAnalysis.recommendations.slice(0, 6).map(rec => ({
          type: rec.category,
          title: rec.title,
          description: rec.description,
          priority: rec.priority
        })),
        trend_analysis: {
          trend: 'stable',
          trajectory: 'positive',
          message: 'Enhanced AI analysis reveals opportunities for growth across multiple wellness dimensions.'
        },
        ai_insights: {
          strengths_analysis: {
            domains: aiAnalysis.strengths.flatMap(s => s.domains),
            message: `Your strengths in ${aiAnalysis.strengths.map(s => s.domains.join(', ')).join(' and ')} provide solid foundation for overall wellness.`
          },
          improvement_opportunities: {
            domains: aiAnalysis.risks.flatMap(r => r.domains),
            message: `Focus on ${aiAnalysis.risks.map(r => r.domains.join(', ')).join(' and ')} for comprehensive wellness improvement.`
          },
          holistic_insights: {
            balance_score: aiAnalysis.overallScore,
            recommendation: 'Maintain balanced approach while addressing key improvement areas identified by AI analysis.'
          },
          confidence_level: aiAnalysis.aiConfidence,
          generated_at: aiAnalysis.analysisTimestamp.toISOString()
        },
        completed_at: new Date().toISOString(),
        next_recommended_assessment: '3 months'
      }
    };
  };

  const getWellnessLevelColor = (level: string) => {
    switch (level) {
      case 'excellent': return 'text-green-600 bg-green-50';
      case 'good': return 'text-blue-600 bg-blue-50';
      case 'moderate': return 'text-yellow-600 bg-yellow-50';
      case 'needs_improvement': return 'text-orange-600 bg-orange-50';
      case 'poor': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading wellness assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6">
            <h3 className="text-red-800 font-semibold mb-2">Error</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={initializeAssessment} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (results) {
    return (
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Wellness Assessment Complete!</h2>
          <p className="text-gray-600">Here are your comprehensive wellness results</p>
        </div>

        {/* Overall Score */}
        <Card>
          <CardHeader>
            <CardTitle className="text-center">Overall Wellness Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-6xl font-bold text-blue-600 mb-2">
                {Math.round(results.wellness_result.overall_score * 100)}%
              </div>
              <div className={`inline-block px-4 py-2 rounded-full text-sm font-medium ${getWellnessLevelColor(results.wellness_result.wellness_level)}`}>
                {results.wellness_result.wellness_level.replace('_', ' ').toUpperCase()}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Domain Scores */}
        <Card>
          <CardHeader>
            <CardTitle>Domain Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(results.wellness_result.domain_scores).map(([domain, data]) => (
                <div key={domain} className="p-4 border rounded-lg">
                  <h4 className="font-semibold capitalize mb-2">{domain}</h4>
                  <div className="text-2xl font-bold mb-2">{Math.round(data.score * 100)}%</div>
                  <div className={`inline-block px-2 py-1 rounded text-xs font-medium ${getWellnessLevelColor(data.level)}`}>
                    {data.level.replace('_', ' ').toUpperCase()}
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${data.score * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Insights */}
        <Card>
          <CardHeader>
            <CardTitle>AI-Powered Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-3">Your Strengths</h4>
                <div className="space-y-2">
                  {results.wellness_result.ai_insights.strengths_analysis.domains.map((domain) => (
                    <div key={domain} className="flex items-center space-x-2">
                      <span className="text-green-600">✓</span>
                      <span className="capitalize">{domain}</span>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {results.wellness_result.ai_insights.strengths_analysis.message}
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-3">Improvement Opportunities</h4>
                <div className="space-y-2">
                  {results.wellness_result.ai_insights.improvement_opportunities.domains.map((domain) => (
                    <div key={domain} className="flex items-center space-x-2">
                      <span className="text-orange-600">→</span>
                      <span className="capitalize">{domain}</span>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {results.wellness_result.ai_insights.improvement_opportunities.message}
                </p>
              </div>
            </div>
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold mb-2">Balance Analysis</h4>
              <div className="flex items-center justify-between">
                <span>Life Balance Score:</span>
                <span className="font-bold">{Math.round(results.wellness_result.ai_insights.holistic_insights.balance_score * 100)}%</span>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {results.wellness_result.ai_insights.holistic_insights.recommendation}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Wellness Factors Analysis */}
        <Card>
          <CardHeader>
            <CardTitle>Key Wellness Factors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(results.wellness_result.domain_scores).map(([domain, data]) => {
                const domainInfo = {
                  physical: { icon: '💪', color: 'text-green-600' },
                  mental: { icon: '🧠', color: 'text-blue-600' },
                  emotional: { icon: '❤️', color: 'text-pink-600' },
                  social: { icon: '👥', color: 'text-purple-600' }
                }[domain] || { icon: '📊', color: 'text-gray-600' };

                return (
                  <div key={domain} className="p-4 border rounded-lg">
                    <div className="flex items-center space-x-3 mb-3">
                      <span className="text-2xl">{domainInfo.icon}</span>
                      <div className="flex-1">
                        <h4 className="font-semibold capitalize">{domain} Wellness</h4>
                        <div className={`text-lg font-bold ${domainInfo.color}`}>
                          {Math.round(data.score * 100)}%
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm">
                        <span className="font-medium">Status:</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs ${getWellnessLevelColor(data.level)}`}>
                          {data.level.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <div className="text-sm">
                        <span className="font-medium">Key Factors:</span>
                        <div className="mt-1 text-xs text-gray-600">
                          {domain === 'physical' && 'Exercise frequency, sleep quality, nutrition habits'}
                          {domain === 'mental' && 'Stress management, cognitive clarity, mental focus'}
                          {domain === 'emotional' && 'Emotional regulation, self-awareness, resilience'}
                          {domain === 'social' && 'Relationship quality, social support, communication'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Wellness Score Details */}
        <Card>
          <CardHeader>
            <CardTitle>Wellness Score Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {Object.keys(results.wellness_result.domain_scores).length}
                  </div>
                  <div className="text-sm text-gray-600">Domains Assessed</div>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {Math.round(results.wellness_result.ai_insights.confidence_level * 100)}%
                  </div>
                  <div className="text-sm text-gray-600">AI Confidence</div>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.round(results.wellness_result.ai_insights.holistic_insights.balance_score * 100)}%
                  </div>
                  <div className="text-sm text-gray-600">Life Balance</div>
                </div>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">
                  <strong>Analysis Date:</strong> {new Date(results.wellness_result.ai_insights.generated_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle>Personalized Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            {results.wellness_result.recommendations.length > 0 ? (
              <div className="space-y-4">
                {results.wellness_result.recommendations.map((rec, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${getPriorityColor(rec.priority)}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold">{rec.title}</h4>
                        <p className="text-sm mt-1">{rec.description}</p>
                        <div className="mt-2 text-xs text-gray-500">
                          Category: {rec.type} • Priority: {rec.priority}
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded font-medium ${getPriorityColor(rec.priority)}`}>
                        {rec.priority.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">🎯</div>
                <h3 className="text-lg font-semibold mb-2">Recommendations Being Generated</h3>
                <p className="text-gray-600 mb-4">
                  Your personalized wellness recommendations are being calculated based on your assessment results.
                </p>
                <div className="inline-block p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-sm text-blue-700">Processing AI insights...</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action Plan */}
        <Card>
          <CardHeader>
            <CardTitle>Your Wellness Action Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="font-semibold text-red-800 mb-2">🚨 Immediate Actions</h4>
                <p className="text-sm text-red-700 mb-3">Start this week for urgent wellness needs</p>
                <ul className="text-xs text-red-600 space-y-1">
                  <li>• Focus on lowest scoring domains</li>
                  <li>• Address any critical risks identified</li>
                  <li>• Establish foundational habits</li>
                </ul>
              </div>
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h4 className="font-semibold text-yellow-800 mb-2">📈 Short-Term Goals</h4>
                <p className="text-sm text-yellow-700 mb-3">Build momentum over next 4-6 weeks</p>
                <ul className="text-xs text-yellow-600 space-y-1">
                  <li>• Implement 1-2 key recommendations</li>
                  <li>• Track progress weekly</li>
                  <li>• Adjust strategies as needed</li>
                </ul>
              </div>
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-2">🎯 Long-Term Vision</h4>
                <p className="text-sm text-green-700 mb-3">Sustainable wellness over 3-6 months</p>
                <ul className="text-xs text-green-600 space-y-1">
                  <li>• Maintain positive changes</li>
                  <li>• Expand wellness practices</li>
                  <li>• Share success with others</li>
                </ul>
              </div>
            </div>
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">
                <strong>📊 Pro Tip:</strong> Set calendar reminders for your wellness activities and track your progress weekly. Small consistent actions lead to significant long-term results!
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps & Resources */}
        <div className="text-center space-y-4">
          <div className="flex justify-center space-x-4">
            <Button variant="primary" onClick={() => window.location.reload()}>
              Take Another Assessment
            </Button>
            <Button variant="outline" onClick={() => window.location.href = '/mental-health-wellness'}>
              Explore Wellness Resources
            </Button>
            <Button variant="secondary" onClick={() => window.location.href = '/wellness-plans'}>
              Create Wellness Plan
            </Button>
          </div>
          <div className="text-sm text-gray-600">
            <p>Next recommended assessment: {results.wellness_result.next_recommended_assessment}</p>
            <p className="mt-2">
              <strong>Remember:</strong> Wellness is a journey, not a destination. Be patient and compassionate with yourself as you work toward your wellbeing goals.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = getCurrentQuestion();
  const currentDomain = getCurrentDomain();

  if (!currentQuestion || !currentDomain) {
    return <div className="text-center p-6">No question available</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-medium text-gray-700">{Math.round(getTotalProgress())}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${getTotalProgress()}%` }}
          ></div>
        </div>
      </div>

      {/* Domain Progress */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <span className="text-2xl">{currentDomain.icon}</span>
          <div>
            <h3 className="text-xl font-semibold capitalize">{currentDomain.name}</h3>
            <p className="text-sm text-gray-600">{currentDomain.description}</p>
          </div>
          <div className="ml-auto">
            <span className="text-sm font-medium text-gray-700">
              Question {currentQuestionIndex + 1} of {currentDomain.questions.length}
            </span>
          </div>
        </div>
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-medium text-gray-700">Domain Progress</span>
          <span className="text-xs font-medium text-gray-700">{Math.round(getDomainProgress())}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-green-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getDomainProgress()}%` }}
          ></div>
        </div>
      </div>

      {/* Question Card */}
      <Card className="mb-8">
        <CardContent className="p-8">
          <h4 className="text-lg font-medium text-gray-900 mb-6">
            {currentQuestion.text}
          </h4>
          <div className="space-y-3">
            {currentQuestion.options.map((option, index) => {
              const isSelected = responses[currentQuestion.id] === option.value;
              return (
                <label
                  key={option.value}
                  className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="radio"
                    name={currentQuestion.id}
                    value={option.value}
                    checked={isSelected}
                    onChange={(e) => handleResponseChange(currentQuestion.id, parseInt(e.target.value))}
                    className="mr-3 w-5 h-5 text-blue-600 focus:ring-blue-500 focus:ring-offset-2"
                  />
                  <div className="flex-1 flex items-center justify-between">
                    <span className="text-gray-900 font-medium">{option.text}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      isSelected
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {option.value}/5
                    </span>
                  </div>
                </label>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentDomainIndex === 0 && currentQuestionIndex === 0}
        >
          Previous
        </Button>

        {currentDomainIndex === assessmentData.domains.length - 1 &&
         currentQuestionIndex === currentDomain.questions.length - 1 ? (
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || Object.keys(responses).length < assessmentData.total_questions}
            className="bg-green-600 hover:bg-green-700"
          >
            {isSubmitting ? 'Submitting...' : 'Complete Assessment'}
          </Button>
        ) : (
          <Button
            onClick={handleNext}
            disabled={!responses[currentQuestion.id]}
          >
            Next
          </Button>
        )}
      </div>
    </div>
  );
};

export default WellnessAssessmentForm;
