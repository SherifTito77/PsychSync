/**
 * Actionable Recommendations Panel
 * Displays prioritized recommendations with impact scoring and quick actions
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  CheckCircle,
  XCircle,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  Target,
  Clock,
  Star,
  ArrowRight,
  Filter
} from 'lucide-react';

interface Recommendation {
  id: string;
  title: string;
  description: string;
  category: 'immediate' | 'short-term' | 'long-term';
  priority: 'critical' | 'high' | 'medium' | 'low';
  impactScore: number; // 0-100
  effortLevel: 'low' | 'medium' | 'high';
  estimatedTime: string;
  dependencies?: string[];
  actionSteps: string[];
  status: 'pending' | 'in-progress' | 'completed' | 'dismissed';
  resources?: Array<{
    title: string;
    type: 'article' | 'video' | 'tool' | 'exercise';
    url?: string;
  }>;
}

interface RecommendationsPanelProps {
  recommendations: Recommendation[];
  onUpdateStatus?: (id: string, status: Recommendation['status']) => void;
  onDismiss?: (id: string) => void;
}

export const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({
  recommendations,
  onUpdateStatus,
  onDismiss
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getPriorityConfig = (priority: Recommendation['priority']) => {
    switch (priority) {
      case 'critical':
        return {
          color: 'bg-red-100 text-red-800 border-red-300',
          icon: <AlertTriangle className="h-4 w-4" />,
          score: 100,
          label: 'Critical'
        };
      case 'high':
        return {
          color: 'bg-orange-100 text-orange-800 border-orange-300',
          icon: <TrendingUp className="h-4 w-4" />,
          score: 75,
          label: 'High'
        };
      case 'medium':
        return {
          color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          icon: <Lightbulb className="h-4 w-4" />,
          score: 50,
          label: 'Medium'
        };
      case 'low':
        return {
          color: 'bg-blue-100 text-blue-800 border-blue-300',
          icon: <Target className="h-4 w-4" />,
          score: 25,
          label: 'Low'
        };
    }
  };

  const getCategoryColor = (category: Recommendation['category']) => {
    switch (category) {
      case 'immediate': return 'bg-red-50 border-red-200';
      case 'short-term': return 'bg-yellow-50 border-yellow-200';
      case 'long-term': return 'bg-green-50 border-green-200';
    }
  };

  const getEffortColor = (effort: Recommendation['effortLevel']) => {
    switch (effort) {
      case 'low': return 'bg-green-500';
      case 'medium': return 'bg-yellow-500';
      case 'high': return 'bg-red-500';
    }
  };

  const getOverallScore = (rec: Recommendation) => {
    const priorityScore = getPriorityConfig(rec.priority).score;
    const impactScore = rec.impactScore;
    const effortMultiplier = rec.effortLevel === 'low' ? 1.2 : rec.effortLevel === 'medium' ? 1 : 0.8;
    return Math.round((priorityScore * 0.4 + impactScore * 0.6) * effortMultiplier);
  };

  const filteredRecommendations = recommendations.filter(rec => {
    if (selectedCategory !== 'all' && rec.category !== selectedCategory) return false;
    if (selectedPriority !== 'all' && rec.priority !== selectedPriority) return false;
    return true;
  }).sort((a, b) => getOverallScore(b) - getOverallScore(a));

  const categories = [
    { value: 'all', label: 'All Categories', count: recommendations.length },
    { value: 'immediate', label: 'Immediate Action', count: recommendations.filter(r => r.category === 'immediate').length },
    { value: 'short-term', label: 'Short-Term', count: recommendations.filter(r => r.category === 'short-term').length },
    { value: 'long-term', label: 'Long-Term', count: recommendations.filter(r => r.category === 'long-term').length },
  ];

  const priorities = [
    { value: 'all', label: 'All Priorities' },
    { value: 'critical', label: 'Critical' },
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' },
  ];

  const stats = {
    total: recommendations.length,
    pending: recommendations.filter(r => r.status === 'pending').length,
    inProgress: recommendations.filter(r => r.status === 'in-progress').length,
    completed: recommendations.filter(r => r.status === 'completed').length,
    avgImpact: Math.round(recommendations.reduce((sum, r) => sum + r.impactScore, 0) / recommendations.length),
  };

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-700">{stats.total}</div>
            <div className="text-xs text-blue-600">Total</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-yellow-700">{stats.pending}</div>
            <div className="text-xs text-yellow-600">Pending</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-700">{stats.inProgress}</div>
            <div className="text-xs text-purple-600">In Progress</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-700">{stats.completed}</div>
            <div className="text-xs text-green-600">Completed</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-indigo-50 to-indigo-100 border-indigo-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-indigo-700">{stats.avgImpact}</div>
            <div className="text-xs text-indigo-600">Avg Impact</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5 text-blue-600" />
              Filter Recommendations
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Category</label>
              <div className="flex flex-wrap gap-2">
                {categories.map(cat => (
                  <Badge
                    key={cat.value}
                    variant={selectedCategory === cat.value ? "default" : "outline"}
                    className="cursor-pointer hover:bg-gray-100"
                    onClick={() => setSelectedCategory(cat.value)}
                  >
                    {cat.label} ({cat.count})
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <div className="flex flex-wrap gap-2">
                {priorities.map(pri => (
                  <Badge
                    key={pri.value}
                    variant={selectedPriority === pri.value ? "default" : "outline"}
                    className="cursor-pointer hover:bg-gray-100"
                    onClick={() => setSelectedPriority(pri.value)}
                  >
                    {pri.label}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecommendations.map((rec) => {
          const priorityConfig = getPriorityConfig(rec.priority);
          const overallScore = getOverallScore(rec);
          const isExpanded = expandedId === rec.id;

          return (
            <Card
              key={rec.id}
              className={`hover:shadow-lg transition-all ${getCategoryColor(rec.category)} ${
                rec.status === 'completed' ? 'opacity-60' : ''
              }`}
            >
              <CardContent className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-gray-900">{rec.title}</h4>
                      <Badge className={priorityConfig.color} variant="outline">
                        {priorityConfig.icon}
                        {priorityConfig.label}
                      </Badge>
                      {rec.status === 'completed' && (
                        <Badge className="bg-green-100 text-green-800 border-green-300">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Completed
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-700">{rec.description}</p>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-2xl font-bold text-gray-900">{overallScore}</div>
                    <div className="text-xs text-gray-600">Score</div>
                  </div>
                </div>

                {/* Score Breakdown */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600">Priority</span>
                      <span className="text-xs font-medium">{priorityConfig.score}%</span>
                    </div>
                    <Progress value={priorityConfig.score} className="h-2" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600">Impact</span>
                      <span className="text-xs font-medium">{rec.impactScore}%</span>
                    </div>
                    <Progress value={rec.impactScore} className="h-2" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600">Effort</span>
                      <span className="text-xs font-medium capitalize">{rec.effortLevel}</span>
                    </div>
                    <div className="h-2 rounded-full bg-gray-200 overflow-hidden">
                      <div
                        className={`h-full ${getEffortColor(rec.effortLevel)}`}
                        style={{ width: rec.effortLevel === 'low' ? '33%' : rec.effortLevel === 'medium' ? '66%' : '100%' }}
                      />
                    </div>
                  </div>
                </div>

                {/* Metadata */}
                <div className="flex items-center gap-4 text-xs text-gray-600 mb-3">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {rec.estimatedTime}
                  </div>
                  <Badge variant="outline" className="text-xs capitalize">
                    {rec.category.replace('-', ' ')}
                  </Badge>
                </div>

                {/* Expandable Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t space-y-4">
                    {/* Action Steps */}
                    <div>
                      <h5 className="font-medium text-sm mb-2 flex items-center gap-2">
                        <Target className="h-4 w-4 text-blue-600" />
                        Action Steps
                      </h5>
                      <ol className="space-y-2">
                        {rec.actionSteps.map((step, idx) => (
                          <li key={idx} className="text-sm flex items-start gap-2">
                            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-medium">
                              {idx + 1}
                            </span>
                            <span className="text-gray-700">{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* Resources */}
                    {rec.resources && rec.resources.length > 0 && (
                      <div>
                        <h5 className="font-medium text-sm mb-2 flex items-center gap-2">
                          <Star className="h-4 w-4 text-yellow-600" />
                          Resources
                        </h5>
                        <div className="flex flex-wrap gap-2">
                          {rec.resources.map((resource, idx) => (
                            <Badge key={idx} variant="outline" className="capitalize">
                              {resource.type}: {resource.title}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpandedId(isExpanded ? null : rec.id)}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    {isExpanded ? 'Show Less' : 'Show Details'}
                    <ArrowRight className={`h-4 w-4 ml-2 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                  </Button>

                  <div className="flex gap-2">
                    {rec.status === 'pending' && onUpdateStatus && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onUpdateStatus(rec.id, 'in-progress')}
                          className="text-purple-600 border-purple-300 hover:bg-purple-50"
                        >
                          Start
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => onUpdateStatus(rec.id, 'completed')}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Complete
                        </Button>
                      </>
                    )}
                    {rec.status === 'in-progress' && onUpdateStatus && (
                      <Button
                        size="sm"
                        onClick={() => onUpdateStatus(rec.id, 'completed')}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Complete
                      </Button>
                    )}
                    {onDismiss && rec.status !== 'completed' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDismiss(rec.id)}
                        className="text-gray-600 hover:text-gray-700"
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}

        {filteredRecommendations.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">
                No recommendations found
              </h3>
              <p className="text-sm text-gray-600">
                Try adjusting your filters to see more recommendations
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
