// frontend/src/components/common/LoadingSpinner.tsx
import React from 'react';
interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'blue' | 'white' | 'gray' | 'indigo' | 'black';
  className?: string;
}
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  color = 'indigo',
  className = '' 
}) => {
  const sizeClasses = {
    small: 'h-4 w-4 border-2',
    medium: 'h-8 w-8 border-3',
    large: 'h-12 w-12 border-4',
  };
  const colorClasses = {
    blue: 'border-gray-200 border-t-blue-600',
    white: 'border-gray-400 border-t-white',
    gray: 'border-gray-300 border-t-gray-600',
    indigo: 'border-gray-200 border-t-indigo-600',
    black: 'border-gray-300 border-t-black', // added black
  };
  return (
    <div
      className={`${sizeClasses[size]} ${colorClasses[color]} animate-spin rounded-full ${className}`}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};
export { LoadingSpinner };
export default LoadingSpinner;
