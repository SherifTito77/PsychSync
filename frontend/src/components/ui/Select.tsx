import React, { useId } from 'react';
interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, ''> {
  label?: string;
  error?: string;
  helperText?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  onValueChange?: (value: string) => void;
  children?: React.ReactNode;
}
export const Select: React.FC<SelectProps> = ({
  label,
  error,
  helperText,
  placeholder,
  options,
  onValueChange,
  children,
  className = '',
  id: providedId,
  ...props
}) => {
  // Generate unique ID for label-select association
  const generatedId = useId();
  const selectId = providedId || generatedId;

  const baseClasses = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';
  const errorClasses = error ? 'border-red-500 focus:ring-red-500' : '';
  const disabledClasses = props.disabled ? 'bg-gray-100 cursor-not-allowed' : '';
  const selectClasses = `${baseClasses} ${errorClasses} ${disabledClasses} ${className}`;

  return (
    <div className="space-y-2">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {children ? (
        <div className={selectClasses}>
          {React.Children.map(children, child => {
            if (React.isValidElement(child) && child.type === 'select') {
              return React.cloneElement(child, {
                ...child.props,
                id: child.props.id || selectId,
                'aria-invalid': error ? 'true' : 'false',
                'aria-describedby': error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined,
                onChange: (e: React.ChangeEvent<HTMLSelectElement>) => {
                  child.props.onChange?.(e);
                  onValueChange?.(e.target.value);
                }
              });
            }
            return child;
          })}
        </div>
      ) : (
        <select
          id={selectId}
          className={selectClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined}
          onChange={(e) => {
            props.onChange?.(e);
            onValueChange?.(e.target.value);
          }}
          {...props}
        >
          <option value="">{placeholder || 'Select an option'}</option>
          {options?.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}
      {error && (
        <p
          id={`${selectId}-error`}
          className="text-sm text-red-600"
          role="alert"
        >
          {error}
        </p>
      )}
      {helperText && !error && (
        <p
          id={`${selectId}-helper`}
          className="text-sm text-gray-500"
        >
          {helperText}
        </p>
      )}
    </div>
  );
};
// Additional exports for compatibility with shadcn/ui style
export const SelectContent: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = 'bg-white border border-gray-200 rounded-md shadow-lg'
}) => {
  return <div className={className}>{children}</div>;
};
export const SelectItem: React.FC<{
  children: React.ReactNode;
  value: string;
  className?: string
}> = ({ children, className = 'px-3 py-2 cursor-pointer hover:bg-gray-100' }) => {
  return <div className={className}>{children}</div>;
};
export const SelectTrigger: React.FC<{
  children: React.ReactNode;
  className?: string
}> = ({ children, className = 'px-3 py-2 border border-gray-300 rounded-md bg-white' }) => {
  return <div className={className}>{children}</div>;
};
export const SelectValue: React.FC<{
  placeholder?: string;
  className?: string;
}> = ({ placeholder, className = '' }) => {
  return <span className={className}>{placeholder || 'Select an option'}</span>;
};
export default Select;
