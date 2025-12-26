import React from 'react';
import { Card, CardContent } from '@/components/ui/Card';
import { Progress } from '@/components/ui/progress';

interface WellbeingScoreProps {
  score: number;
  maxScore: number;
  category: 'overall' | 'mental' | 'physical' | 'social';
  showDetails?: boolean;
  size?: 'sm' | 'md' | 'lg';
  trend?: 'up' | 'down' | 'stable';
  previousScore?: number;
}

const WellbeingScore: React.FC<WellbeingScoreProps> = ({
  score,
  maxScore,
  category,
  showDetails = false,
  size = 'md',
  trend,
  previousScore,
}) => {
  const percentage = (score / maxScore) * 100;

  const getCategoryConfig = () => {
    switch (category) {
      case 'overall':
        return {
          title: 'Overall Wellbeing',
          color: 'purple',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 2.008 0 .3.009.485.15.69.627.997.377 1.375.239 1.992-.411.692-.24.99-.702.246-.233.998-.246.998-.239.998-.398 1.003-.398 1.003-.398 1.003-.398.004 1.004-.403 1.004-.403.398-.999.403-1.003.403-1.004-.003-.997-.004-1.004zM12.538 10.017c.208.26.628.1.966-.12.474-.21.987-.201 1.506-.177.397-.18.735.08.631.08.474.255.711.08.474-.256.711-.08a.728.728 0 00-.339-.089c-.458-.112-.945-.237-1.26-.58-.312-.345-.561-.479-.393-.415-.12-.371-.243-.514-.353-.143-.144-.244-.37-.514-.833-.37-1.631-.194-2.417.049-1.667.255-3.258.105-4.787.251-.573.104-.73.233-.207.129-.526-.21-.734.241-.208.051-.474.087-.806.04-.332.107-.741.162-1.15-.084-.408-.159-.733-.083-.331-.075-.62.037-.896.12-.282.084-.64.162-1.006.03-.374-.097-.789-.202-1.184.059-.393.019-.767.058-1.135.058-.367 0-.74-.036-1.135-.058z" />
            </svg>
          ),
        };
      case 'mental':
        return {
          title: 'Mental Health',
          color: 'blue',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1v1a1 1 0 11-2 0V3a1 1 0 011-1zm3.707 2.293a1 1 0 00-1.414 1.414l-.093.09a1 1 0 01-1.332 0L8 6.586l-1.293-1.293a1 1 0 011.414-1.414l3.586 3.586a1 1 0 001.414-1.414l.093.09a1 1 0 001.332 0l.907.907a1 1 0 001.414-1.414L8 8.586l-1.293 1.293a1 1 0 01-1.414 0l-3.586-3.586a1 1 0 00-1.414 1.414l-.093.09a1 1 0 00-.024.034zM14 7a1 1 0 01-.445.893L12.557 8.891a1 1 0 01-1.332 0l-2.545 2.545a1 1 0 011.414 0l2.545-2.545a1 1 0 001.414 1.414l.093.09a1 1 0 00.024.034z" clipRule="evenodd" />
            </svg>
          ),
        };
      case 'physical':
        return {
          title: 'Physical Health',
          color: 'green',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 9.343l1.414-1.414a4 4 0 015.656 0L16.828 4.828a4 4 0 01-5.656 0L5.172 4.828a4 4 0 010-5.656zm1.414 1.414L10 11.828l8.172-8.172a2 2 0 00-2.828 0L8.828 6.586a2 2 0 01-2.828 0l-2-2a2 2 0 00-2.828 0l-2 2a2 2 0 001.414 1.414l4 4a2 2 0 001.414-1.414l-2-2z" clipRule="evenodd" />
            </svg>
          ),
        };
      case 'social':
        return {
          title: 'Social Connection',
          color: 'yellow',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0 4 4 0 008 0zM12 2a1 1 0 100 2 1 1 0 012 0z" />
            </svg>
          ),
        };
      default:
        return {
          title: 'Wellbeing',
          color: 'gray',
          icon: (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
            </svg>
          ),
        };
    }
  };

  const config = getCategoryConfig();
  const getColorClass = () => {
    const colorMap: Record<string, string> = {
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      orange: 'bg-orange-500',
      red: 'bg-red-500',
      blue: 'bg-blue-500',
      purple: 'bg-purple-500',
      gray: 'bg-gray-500',
    };
    return colorMap[config.color] || colorMap.gray;
  };

  const getScoreColor = () => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getTrendIcon = () => {
    if (!trend) return null;

    if (trend === 'up') {
      return (
        <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      );
    } else if (trend === 'down') {
      return (
        <svg className="h-4 w-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L9 14.586V3a1 1 0 10-2 0v11.586l2.293 2.293a1 1 0 011.414 1.414l4-4a1 1 0 001.414-1.414L11 14.586V3a1 1 0 10-2 0v11.586l2.293-2.293z" clipRule="evenodd" />
        </svg>
      );
    } else {
      return null;
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          score: 'text-2xl',
          icon: 'w-8 h-8',
          card: 'p-3',
        };
      case 'lg':
        return {
          score: 'text-4xl',
          icon: 'w-12 h-12',
          card: 'p-6',
        };
      default:
        return {
          score: 'text-3xl',
          icon: 'w-10 h-10',
          card: 'p-4',
        };
    }
  };

  const sizeClasses = getSizeClasses();

  const getScoreLabel = () => {
    if (percentage >= 90) return 'Excellent';
    if (percentage >= 80) return 'Very Good';
    if (percentage >= 70) return 'Good';
    if (percentage >= 60) return 'Fair';
    if (percentage >= 40) return 'Needs Attention';
    return 'Requires Support';
  };

  return (
    <Card className={`border-gray-200 ${size === 'lg' ? 'col-span-2' : ''}`}>
      <CardContent className={sizeClasses.card}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`${sizeClasses.icon} ${getColorClass()} bg-opacity-10 p-2 rounded-full`}>
              {config.icon}
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{config.title}</h3>
              {showDetails && (
                <p className="text-sm text-gray-500">
                  Score: {score}/{maxScore}
                </p>
              )}
            </div>
          </div>

          {trend && getTrendIcon()}
        </div>

        <div className="space-y-3">
          {/* Score Display */}
          <div className="flex items-baseline">
            <span className={`${sizeClasses.score} font-bold ${getScoreColor()}`}>
              {Math.round(percentage)}%
            </span>
            {showDetails && (
              <span className="text-sm text-gray-500 ml-2">
                ({score}/{maxScore})
              </span>
            )}
          </div>

          {/* Progress Bar */}
          <Progress
            value={percentage}
            className={`h-2 ${getColorClass()}`}
          />

          {/* Score Label */}
          <div className="flex justify-between items-center">
            <span className={`text-sm font-medium ${getScoreColor()}`}>
              {getScoreLabel()}
            </span>
            {showDetails && previousScore && (
              <div className="flex items-center space-x-1 text-sm text-gray-500">
                {getTrendIcon()}
                <span>
                  {previousScore} → {score}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Additional Details */}
        {showDetails && (
          <div className="pt-3 border-t border-gray-100">
            <div className="text-sm text-gray-600">
              <p>
                <strong>Last assessment:</strong> {new Date().toLocaleDateString()}
              </p>
              <p>
                <strong>Category score:</strong> {score}/{maxScore} points
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WellbeingScore;