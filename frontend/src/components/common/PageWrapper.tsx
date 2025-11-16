// frontend/src/components/common/PageWrapper.tsx
import React from 'react';
interface PageWrapperProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}
const PageWrapper: React.FC<PageWrapperProps> = ({
  children,
  className = '',
  maxWidth = 'xl'
}) => {
  const getMaxWidthClass = () => {
    switch (maxWidth) {
      case 'sm': return 'max-w-2xl';
      case 'md': return 'max-w-4xl';
      case 'lg': return 'max-w-6xl';
      case 'xl': return 'max-w-7xl';
      case 'full': return 'max-w-full';
      default: return 'max-w-7xl';
    }
  };
  return (
    <div className={`content-wrapper ${getMaxWidthClass()} ${className}`}>
      {children}
    </div>
  );
};
export default PageWrapper;