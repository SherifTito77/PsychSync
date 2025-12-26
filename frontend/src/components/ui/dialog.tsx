import React, { useEffect, useRef, useId } from 'react';
import { createPortal } from 'react-dom';

interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  dismissible?: boolean;
}

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}

interface DialogDescriptionProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
}

interface DialogHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
}

interface DialogTriggerProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const Dialog: React.FC<DialogProps> = ({
  open = false,
  onOpenChange,
  children,
  size = 'md',
  dismissible = true
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descriptionId = useId();

  // Handle escape key press
  useEffect(() => {
    if (!open) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && dismissible && onOpenChange) {
        onOpenChange(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [open, dismissible, onOpenChange]);

  // Handle focus trapping
  useEffect(() => {
    if (!open || !dialogRef.current) return;

    const dialog = dialogRef.current;
    const focusableElements = dialog.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstFocusable = focusableElements[0] as HTMLElement;
    const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement;

    // Focus first element
    firstFocusable.focus();

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          lastFocusable.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          firstFocusable.focus();
          e.preventDefault();
        }
      }
    };

    dialog.addEventListener('keydown', handleTabKey);

    // Store previous focus
    const previousFocus = document.activeElement as HTMLElement;

    return () => {
      dialog.removeEventListener('keydown', handleTabKey);
      // Restore focus when dialog closes
      if (previousFocus && typeof previousFocus.focus === 'function') {
        previousFocus.focus();
      }
    };
  }, [open]);

  // Prevent body scroll when dialog is open
  useEffect(() => {
    if (!open) return;

    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  if (!open) return null;

  // Get size classes
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-full mx-4'
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && dismissible && onOpenChange) {
      onOpenChange(false);
    }
  };

  const dialogContent = (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />

      {/* Dialog container */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          className={`relative bg-white rounded-lg shadow-xl transition-all w-full ${sizeClasses[size]} p-6`}
        >
          {/* Provide title and description IDs to children */}
          {React.Children.map(children, (child, index) => {
            if (React.isValidElement(child)) {
              if (child.type === DialogTitle) {
                return React.cloneElement(child as React.ReactElement<any>, {
                  id: titleId
                });
              }
              if (child.type === DialogDescription) {
                return React.cloneElement(child as React.ReactElement<any>, {
                  id: descriptionId
                });
              }
            }
            return child;
          })}
        </div>
      </div>
    </div>
  );

  return createPortal(dialogContent, document.body);
};

export const DialogContent: React.FC<DialogContentProps> = ({ children, className = '' }) => {
  return <div className={`dialog-content ${className}`}>{children}</div>;
};

export const DialogDescription: React.FC<DialogDescriptionProps> = ({
  children,
  className = '',
  id
}) => {
  return (
    <p id={id} className={`text-sm text-gray-600 mt-2 ${className}`}>
      {children}
    </p>
  );
};

export const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className = '' }) => {
  return <div className={`mb-4 ${className}`}>{children}</div>;
};

export const DialogTitle: React.FC<DialogTitleProps> = ({ children, className = '', id }) => {
  return (
    <h2 id={id} className={`text-lg font-semibold text-gray-900 ${className}`}>
      {children}
    </h2>
  );
};

export const DialogTrigger: React.FC<DialogTriggerProps> = ({ children, onClick, className = '' }) => {
  return (
    <div onClick={onClick} className={className} role="button" tabIndex={0}>
      {children}
    </div>
  );
};

// Dialog close button component
export const DialogClose: React.FC<{
  onClick?: () => void;
  className?: string;
}> = ({ onClick, className = '' }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 rounded-md ${className}`}
      aria-label="Close dialog"
    >
      <span className="sr-only">Close</span>
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    </button>
  );
};