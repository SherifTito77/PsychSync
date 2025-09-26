import React from 'react';
import { ButtonProps } from '../types/components';

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  className = '', 
  disabled = false, 
  variant = 'primary',
  ...props 
}) => {
  // Component implementation with proper typing
};