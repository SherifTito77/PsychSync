// src/types/components.ts - Fixed component type definitions

import { ReactNode, ButtonHTMLAttributes } from 'react';

// ===== COMPONENT PROP INTERFACES =====

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
}

export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
}

export interface HeaderProps {
  onMenuToggle: () => void;
}

export interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export interface MenuItem {
  name: string;
  path: string;
  icon: string;
}

// ===== PROVIDER PROPS =====

export interface AuthProviderProps {
  children: ReactNode;
}

export interface NotificationProviderProps {
  children: ReactNode;
}

export interface TeamProviderProps {
  children: ReactNode;
}

// import { ReactNode, ButtonHTMLAttributes } from "react";
// import { Team } from "./index";

// // ===== COMPONENT PROP INTERFACES =====

// export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
//   children: ReactNode;
//   onClick?: () => void;
//   className?: string;
//   disabled?: boolean;
//   variant?: "primary" | "secondary" | "danger";
// }

// export interface LoadingSpinnerProps {
//   size?: "small" | "medium" | "large";
//   color?: string;
// }

// export interface HeaderProps {
//   onMenuToggle: () => void;
// }

// export interface SidebarProps {
//   isOpen: boolean;
//   onToggle: () => void;
// }

// export interface MenuItem {
//   name: string;
//   path: string;
//   icon: string;
// }

// // ===== PROVIDER PROPS =====

// export interface AuthProviderProps {
//   children: ReactNode;
// }

// export interface NotificationProviderProps {
//   children: ReactNode;
// }

// export interface TeamProviderProps {
//   children: ReactNode;
// }
