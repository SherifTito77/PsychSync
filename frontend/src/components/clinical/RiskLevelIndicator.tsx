import React from 'react';

interface RiskLevelIndicatorProps {
  level: 'low' | 'moderate' | 'high' | 'critical';
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const RiskLevelIndicator: React.FC<RiskLevelIndicatorProps> = ({
  level,
  showLabel = true,
  size = 'md',
}) => {
  const getRiskConfig = () => {
    switch (level) {
      case 'low':
        return {
          color: 'bg-green-500',
          textColor: 'text-green-800',
          bgColor: 'bg-green-100',
          label: 'Low Risk',
          description: 'Minimal risk factors detected',
        };
      case 'moderate':
        return {
          color: 'bg-yellow-500',
          textColor: 'text-yellow-800',
          bgColor: 'bg-yellow-100',
          label: 'Moderate Risk',
          description: 'Some risk factors present',
        };
      case 'high':
        return {
          color: 'bg-orange-500',
          textColor: 'text-orange-800',
          bgColor: 'bg-orange-100',
          label: 'High Risk',
          description: 'Significant risk factors detected',
        };
      case 'critical':
        return {
          color: 'bg-red-500',
          textColor: 'text-red-800',
          bgColor: 'bg-red-100',
          label: 'Critical Risk',
          description: 'Immediate attention required',
        };
      default:
        return {
          color: 'bg-gray-500',
          textColor: 'text-gray-800',
          bgColor: 'bg-gray-100',
          label: 'Unknown Risk',
          description: 'Risk level not assessed',
        };
    }
  };

  const config = getRiskConfig();
  const sizeClasses = {
    sm: 'h-2 w-2',
    md: 'h-3 w-3',
    lg: 'h-4 w-4',
  };

  return (
    <div className="flex items-center space-x-2">
      {/* Risk Indicator Dot */}
      <div className={`rounded-full ${config.color} ${sizeClasses[size]}`} />

      {/* Risk Label */}
      {showLabel && (
        <div>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
            {config.label}
          </span>
          <p className="text-xs text-gray-500 mt-1">{config.description}</p>
        </div>
      )}
    </div>
  );
};

export default RiskLevelIndicator;