import React from 'react';
interface AlertProps {
  children: React.ReactNode;
  variant?: 'info' | 'success' | 'warning' | 'error';
  className?: string;
}
export const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'info',
  className = ''
}) => {
  const baseClasses = 'p-4 rounded-lg border flex items-start';
  const variantClasses = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800'
  };
  const icons = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '❌'
  };
  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      <span className="mr-3 text-xl">{icons[variant]}</span>
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
};
export const AlertDescription: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => {
  return <div className={className}>{children}</div>;
};
export default Alert;