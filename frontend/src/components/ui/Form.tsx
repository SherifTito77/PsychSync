import React from 'react';

interface FormProps {
  children: React.ReactNode;
  onSubmit?: (e: React.FormEvent) => void;
  className?: string;
}

export const Form: React.FC<FormProps> = ({ children, onSubmit, className = '' }) => {
  return (
    <form
      className={`space-y-6 ${className}`}
      onSubmit={onSubmit}
    >
      {children}
    </form>
  );
};

// Mock the required form components for compatibility
export const FormControl: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = ''
}) => {
  return <div className={className}>{children}</div>;
};

export const FormDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = 'text-sm text-gray-600'
}) => {
  return <p className={className}>{children}</p>;
};

// Proper type definitions for form field
interface FieldState {
  invalid?: boolean;
  isTouched?: boolean;
  isDirty?: boolean;
  error?: { type?: string; message?: string } | undefined;
}

interface ControllerFieldState {
  invalid: boolean;
  isTouched: boolean;
  isDirty: boolean;
  error?: { type?: string; message?: string } | undefined;
}

interface FieldValues {
  [key: string]: unknown;
}

interface ControllerFieldStateWithValue extends ControllerFieldState {
  field: FieldValues;
}

interface FormFieldProps<TFieldValues extends FieldValues = FieldValues> {
  control?: unknown; // Control from react-hook-form, mocked for now
  name: string;
  render: (props: {
    field: {
      name: string;
      value: unknown;
      onChange: (...event: unknown[]) => void;
      onBlur: () => void;
      ref: React.Ref<unknown>;
    };
    fieldState: FieldState;
  }) => React.ReactNode;
}

export const FormField = <TFieldValues extends FieldValues = FieldValues>({
  name,
  render
}: FormFieldProps<TFieldValues>): React.ReactElement => {
  // Mock implementation for compatibility with react-hook-form
  const field = {
    name,
    value: undefined as unknown,
    onChange: () => {},
    onBlur: () => {},
    ref: () => {}
  };
  const fieldState: FieldState = { error: undefined };
  return <>{render({ field, fieldState })}</>;
};
export const FormItem: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = 'space-y-2'
}) => {
  return <div className={className}>{children}</div>;
};
export const FormLabel: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = 'block text-sm font-medium text-gray-700'
}) => {
  return <label className={className}>{children}</label>;
};
export const FormMessage: React.FC<{ children?: React.ReactNode; className?: string }> = ({
  children,
  className = 'text-sm text-red-600'
}) => {
  return children ? <p className={className}>{children}</p> : null;
};
