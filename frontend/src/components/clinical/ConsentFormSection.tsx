import React from 'react';

interface ConsentFormSectionProps {
  id: string;
  title: string;
  content: string;
  required: boolean;
  checked: boolean;
  onChange: (checked: boolean) => void;
  error?: boolean;
}

const ConsentFormSection: React.FC<ConsentFormSectionProps> = ({
  id,
  title,
  content,
  required,
  checked,
  onChange,
  error = false,
}) => {
  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.checked);
  };

  return (
    <div className="border-b pb-6 last:border-b-0">
      <div className="flex items-start space-x-3">
        <input
          type="checkbox"
          id={id}
          checked={checked}
          onChange={handleCheckboxChange}
          className={`mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded ${
            error ? 'border-red-500' : ''
          }`}
        />
        <div className="flex-1">
          <label
            htmlFor={id}
            className={`block text-sm font-medium text-gray-900 mb-2 flex items-center ${
              required ? 'text-blue-900' : ''
            }`}
          >
            {title}
            {required && (
              <span className="text-red-500 ml-1">*</span>
            )}
          </label>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-700 leading-relaxed">
              {content}
            </p>
          </div>
          {error && (
            <p className="text-red-500 text-xs mt-2 flex items-center">
              <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              This section is required to proceed
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConsentFormSection;