import React from 'react';

interface LabelProps {
  children: React.ReactNode;
  htmlFor?: string;
  className?: string;
}

const Label = React.memo<LabelProps>(({ children, htmlFor, className = '' }) => {
  return (
    <label
      htmlFor={htmlFor}
      className={`text-sm font-medium text-gray-700 mb-1 block ${className}`}
    >
      {children}
    </label>
  );
});

Label.displayName = 'Label';

export { Label };
export default Label;
