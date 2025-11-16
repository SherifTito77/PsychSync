import React from 'react';
import { cn } from '../../utils/cn';
interface BadgeProps {
  children: React.ReactNode;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'orange' | 'purple' | 'gray' | 'indigo';
  variant?: 'solid' | 'outline' | 'subtle';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}
const Badge: React.FC<BadgeProps> = ({
  children,
  color = 'gray',
  variant = 'solid',
  size = 'md',
  className
}) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-full';
  const colorClasses = {
    blue: {
      solid: 'bg-blue-100 text-blue-800',
      outline: 'text-blue-700 border border-blue-300',
      subtle: 'bg-blue-50 text-blue-700'
    },
    green: {
      solid: 'bg-green-100 text-green-800',
      outline: 'text-green-700 border border-green-300',
      subtle: 'bg-green-50 text-green-700'
    },
    yellow: {
      solid: 'bg-yellow-100 text-yellow-800',
      outline: 'text-yellow-700 border border-yellow-300',
      subtle: 'bg-yellow-50 text-yellow-700'
    },
    red: {
      solid: 'bg-red-100 text-red-800',
      outline: 'text-red-700 border border-red-300',
      subtle: 'bg-red-50 text-red-700'
    },
    orange: {
      solid: 'bg-orange-100 text-orange-800',
      outline: 'text-orange-700 border border-orange-300',
      subtle: 'bg-orange-50 text-orange-700'
    },
    purple: {
      solid: 'bg-purple-100 text-purple-800',
      outline: 'text-purple-700 border border-purple-300',
      subtle: 'bg-purple-50 text-purple-700'
    },
    gray: {
      solid: 'bg-gray-100 text-gray-800',
      outline: 'text-gray-700 border border-gray-300',
      subtle: 'bg-gray-50 text-gray-700'
    },
    indigo: {
      solid: 'bg-indigo-100 text-indigo-800',
      outline: 'text-indigo-700 border border-indigo-300',
      subtle: 'bg-indigo-50 text-indigo-700'
    }
  };
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-sm'
  };
  const classes = cn(
    baseClasses,
    colorClasses[color][variant],
    sizeClasses[size],
    className
  );
  return <span className={classes}>{children}</span>;
};
export { Badge };
export default Badge;