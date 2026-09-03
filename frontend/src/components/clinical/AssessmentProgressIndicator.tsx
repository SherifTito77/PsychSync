import React from 'react';

interface AssessmentProgressIndicatorProps {
  current: number;
  total: number;
  showPercentage?: boolean;
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const AssessmentProgressIndicator: React.FC<AssessmentProgressIndicatorProps> = ({
  current,
  total,
  showPercentage = true,
  showLabels = true,
  size = 'md',
}) => {
  const percentage = Math.round((current / total) * 100);

  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const textSizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className="w-full">
      {/* Progress Labels */}
      {showLabels && (
        <div className={`flex justify-between text-gray-600 mb-2 ${textSizeClasses[size]}`}>
          <span>Question {current} of {total}</span>
          {showPercentage && <span>{percentage}% Complete</span>}
        </div>
      )}

      {/* Progress Bar */}
      <div className={`w-full bg-gray-200 rounded-full ${sizeClasses[size]}`}>
        <div
          className="bg-blue-600 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Question Dots */}
      <div className="flex justify-between mt-3">
        {Array.from({ length: total }, (_, index) => (
          <div
            key={index}
            className={`w-2 h-2 rounded-full transition-colors duration-200 ${
              index < current ? 'bg-blue-600' : 'bg-gray-300'
            }`}
            title={`Question ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default AssessmentProgressIndicator;
