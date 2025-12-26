import React, { useId } from 'react';
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}
export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className = '',
  id: providedId,
  ...props
}) => {
  // Generate unique ID for label-input association
  const generatedId = useId();
  const inputId = providedId || generatedId;

  const baseClasses = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';
  const errorClasses = error ? 'border-red-500 focus:ring-red-500' : '';
  const disabledClasses = props.disabled ? 'bg-gray-100 cursor-not-allowed' : '';
  const inputClasses = `${baseClasses} ${errorClasses} ${disabledClasses} ${className}`;

  return (
    <div className="space-y-2">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        id={inputId}
        className={inputClasses}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        {...props}
      />
      {error && (
        <p
          id={`${inputId}-error`}
          className="text-sm text-red-600"
          role="alert"
        >
          {error}
        </p>
      )}
      {helperText && !error && (
        <p
          id={`${inputId}-helper`}
          className="text-sm text-gray-500"
        >
          {helperText}
        </p>
      )}
    </div>
  );
};
export default Input;