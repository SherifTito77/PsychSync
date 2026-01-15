import React, { createContext, useContext, useState, ReactNode, HTMLAttributes } from 'react';

interface CheckboxContextType {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled: boolean;
}

const CheckboxContext = createContext<CheckboxContextType | undefined>(undefined);

interface CheckboxProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onChange'> {
  checked: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  children?: ReactNode;
  className?: string;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  checked,
  onCheckedChange,
  disabled = false,
  children,
  className = '',
  ...props
}) => {
  const [internalChecked, setInternalChecked] = useState(checked);

  const handleChange = (newValue: boolean) => {
    if (!disabled) {
      setInternalChecked(newValue);
      onCheckedChange?.(newValue);
    }
  };

  return (
    <CheckboxContext.Provider value={{ checked: internalChecked, onChange: handleChange, disabled }}>
      <div className={`flex items-center space-x-2 ${className}`} {...props}>
        {children}
      </div>
    </CheckboxContext.Provider>
  );
};

interface CheckboxIndicatorProps {
  className?: string;
}

export const CheckboxIndicator: React.FC<CheckboxIndicatorProps> = ({ className = '' }) => {
  const context = useContext(CheckboxContext);

  if (!context) {
    throw new Error('CheckboxIndicator must be used within a Checkbox');
  }

  const { checked, disabled, onChange } = context;

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`
        relative flex h-4 w-4 shrink-0 cursor-pointer items-center justify-center rounded-sm border border-primary transition-colors
        ${checked ? 'bg-primary text-primary-foreground' : 'bg-background'}
        ${disabled ? 'cursor-not-allowed opacity-50' : 'hover:bg-accent hover:text-accent-foreground'}
        ${className}
      `}
    >
      {checked && (
        <svg
          className="h-3 w-3 text-current"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </button>
  );
};

export default Checkbox;
