import React, { createContext, useContext, useState, ReactNode } from 'react';

interface RadioGroupContextType {
  value: string;
  onChange: (value: string) => void;
  name: string;
}

const RadioGroupContext = createContext<RadioGroupContextType | undefined>(undefined);

interface RadioGroupProps {
  children: ReactNode;
  value: string;
  onChange: (value: string) => void;
  name?: string;
  className?: string;
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  children,
  value,
  onChange,
  name = 'radio-group',
  className = '',
}) => {
  return (
    <RadioGroupContext.Provider value={{ value, onChange, name }}>
      <div className={`space-y-2 ${className}`}>{children}</div>
    </RadioGroupContext.Provider>
  );
};

interface RadioGroupItemProps {
  value: string;
  id: string;
  disabled?: boolean;
  className?: string;
}

export const RadioGroupItem: React.FC<RadioGroupItemProps> = ({
  value,
  id,
  disabled = false,
  className = '',
}) => {
  const context = useContext(RadioGroupContext);

  if (!context) {
    throw new Error('RadioGroupItem must be used within a RadioGroup');
  }

  const { value: selectedValue, onChange, name } = context;
  const isChecked = selectedValue === value;

  return (
    <div className={`flex items-center ${className}`}>
      <input
        type="radio"
        id={id}
        name={name}
        value={value}
        checked={isChecked}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 focus:ring-2"
      />
      <label
        htmlFor={id}
        className={`ml-2 text-sm ${disabled ? 'text-gray-400 cursor-not-allowed' : 'text-gray-700 cursor-pointer'}`}
      >
        {id}
      </label>
    </div>
  );
};

export default RadioGroup;
