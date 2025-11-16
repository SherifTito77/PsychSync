// src/components/common/Icon.tsx
import React from 'react';
interface IconProps {
  children: React.ReactNode; // The emoji or SVG will be passed as a child
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}
const Icon: React.FC<IconProps> = ({ children, size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-5 h-5 text-lg',
    md: 'w-6 h-6 text-xl',
    lg: 'w-8 h-8 text-2xl',
    xl: 'w-10 h-10 text-3xl',
  };
  return (
    <div
      className={`inline-flex items-center justify-center flex-shrink-0 ${sizeClasses[size]} ${className}`}
      style={{
        lineHeight: 1,
        overflow: 'hidden',
        whiteSpace: 'nowrap'
      }}
    >
      {children}
    </div>
  );
};
export default Icon;