// // src/types/components.ts - Fixed component type definitions
// src/types/components.ts - Component Type Definitions
export interface MenuItem {
  name: string;
  path: string;
  icon: string;
}
export interface HeaderProps {
  onMenuToggle: () => void;
}
export interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  children: React.ReactNode;
}
const variantClasses = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
  secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  default: 'bg-white text-black border border-gray-300 hover:bg-gray-100 focus:ring-gray-400',
  outline: 'bg-transparent border border-gray-500 text-gray-700 hover:bg-gray-50 focus:ring-gray-400',
};
export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'blue' | 'white' | 'gray'| 'black';
}
