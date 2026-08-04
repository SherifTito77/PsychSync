/**
 * Goal Setting & Tracking Component
 * Allows users to set wellness goals and track progress
 */

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Target,
  Trophy,
  Plus,
  Calendar,
  TrendingUp,
  CheckCircle,
  Flame,
  Star,
  Heart
} from 'lucide-react';

interface Goal {
  id: string;
  title: string;
  description: string;
  category: 'wellness' | 'mental-health' | 'performance' | 'habits';
  targetValue: number;
  currentValue: number;
  unit: string;
  deadline: string;
  streak: number;
  status: 'on-track' | 'behind' | 'completed' | 'not-started';
}

interface GoalTrackingProps {
  goals: Goal[];
  onUpdateGoal?: (goalId: string, progress: number) => Promise<void>;
  onCreateGoal?: (goal: Omit<Goal, 'id' | 'currentValue' | 'streak' | 'status'>) => Promise<void>;
}

export const GoalTracking: React.FC<GoalTrackingProps> = ({
  goals,
  onUpdateGoal,
  onCreateGoal
}) => {
  const [showCreateForm, setShowCreateForm] = useState(false);

  const getStatusColor = (status: Goal['status']) => {
    switch (status) {
      case 'on-track': return 'bg-green-100 text-green-800 border-green-300';
      case 'behind': return 'bg-red-100 text-red-800 border-red-300';
      case 'completed': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusIcon = (status: Goal['status']) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'on-track': return <TrendingUp className="h-4 w-4" />;
      default: return <Target className="h-4 w-4" />;
    }
  };

  const getProgressColor = (goal: Goal) => {
    const progress = (goal.currentValue / goal.targetValue) * 100;

    if (progress >= 100) return 'bg-green-500';
    if (progress >= 75) return 'bg-blue-500';
    if (progress >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const calculateDaysRemaining = (deadline: string) => {
    const deadlineDate = new Date(deadline);
    const today = new Date();
    const diffTime = deadlineDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const categoryIcons = {
    'wellness': <Heart className="h-4 w-4" />,
    'mental-health': <Star className="h-4 w-4" />,
    'performance': <TrendingUp className="h-4 w-4" />,
    'habits': <Flame className="h-4 w-4" />
  };

  const overallProgress = goals.length > 0
    ? goals.reduce((sum, goal) => sum + (goal.currentValue / goal.targetValue), 0) / goals.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Overall Progress Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-600" />
              Goal Tracking
            </CardTitle>
            <Button
              onClick={() => setShowCreateForm(!showCreateForm)}
              size="sm"
              variant="outline"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Goal
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Overall Progress</span>
                <span className="text-sm text-gray-600">
                  {Math.round(overallProgress * 100)}% complete
                </span>
              </div>
              <Progress value={overallProgress * 100} className="h-3" />
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {goals.filter(g => g.status === 'completed').length}
                </div>
                <div className="text-xs text-gray-600">Completed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {goals.filter(g => g.status === 'on-track').length}
                </div>
                <div className="text-xs text-gray-600">On Track</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-600">
                  {goals.filter(g => g.streak >= 7).length}
                </div>
                <div className="text-xs text-gray-600">7+ Day Streaks</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Goals List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map((goal) => {
          const progress = (goal.currentValue / goal.targetValue) * 100;
          const daysRemaining = calculateDaysRemaining(goal.deadline);

          return (
            <Card key={goal.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {categoryIcons[goal.category]}
                        <h4 className="font-semibold">{goal.title}</h4>
                      </div>
                      <p className="text-sm text-gray-600">{goal.description}</p>
                    </div>
                    <Badge className={getStatusColor(goal.status)} variant="outline">
                      <div className="flex items-center gap-1">
                        {getStatusIcon(goal.status)}
                        {goal.status.replace('-', ' ').toUpperCase()}
                      </div>
                    </Badge>
                  </div>

                  {/* Progress */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600">Progress</span>
                      <span className="text-sm font-medium">
                        {goal.currentValue} / {goal.targetValue} {goal.unit}
                        ({progress.toFixed(0)}%)
                      </span>
                    </div>
                    <Progress
                      value={Math.min(progress, 100)}
                      className="h-2"
                    />
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Calendar className="h-4 w-4" />
                      <span className={daysRemaining < 0 ? 'text-red-600' : ''}>
                        {daysRemaining < 0
                          ? `${Math.abs(daysRemaining)} days overdue`
                          : `${daysRemaining} days remaining`
                        }
                      </span>
                    </div>
                    {goal.streak > 0 && (
                      <div className="flex items-center gap-1 text-orange-600">
                        <Flame className="h-4 w-4" />
                        <span className="font-medium">{goal.streak} day streak</span>
                      </div>
                    )}
                  </div>

                  {/* Quick Action */}
                  {goal.status !== 'completed' && onUpdateGoal && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full"
                      onClick={() => {
                        const newProgress = Math.min(goal.currentValue + (goal.targetValue * 0.1), goal.targetValue);
                        onUpdateGoal(goal.id, newProgress);
                      }}
                    >
                      Log Progress (+{Math.round(goal.targetValue * 0.1)} {goal.unit})
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Achievement Banner */}
      {goals.some(g => g.streak >= 30) && (
        <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-300">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <Trophy className="h-12 w-12 text-yellow-600" />
              <div className="flex-1">
                <h3 className="text-xl font-bold text-yellow-900 mb-1">
                  🎉 Incredible Achievement!
                </h3>
                <p className="text-yellow-800">
                  You've maintained a 30+ day streak on your goals. Consistency is key to lasting change!
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
