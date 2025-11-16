import React from 'react';
interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}
export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  return <>{children}</>;
};
interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}
export const DialogContent: React.FC<DialogContentProps> = ({ children, className = '' }) => {
  return <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>{children}</div>;
};
interface DialogDescriptionProps {
  children: React.ReactNode;
  className?: string;
}
export const DialogDescription: React.FC<DialogDescriptionProps> = ({ children, className = '' }) => {
  return <p className={`text-sm text-gray-600 ${className}`}>{children}</p>;
};
interface DialogHeaderProps {
  children: React.ReactNode;
  className?: string;
}
export const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className = '' }) => {
  return <div className={`mb-4 ${className}`}>{children}</div>;
};
interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}
export const DialogTitle: React.FC<DialogTitleProps> = ({ children, className = '' }) => {
  return <h2 className={`text-lg font-semibold ${className}`}>{children}</h2>;
};
export const DialogTrigger: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}> = ({ children, onClick, className = '' }) => {
  return <div onClick={onClick} className={className}>{children}</div>;
};