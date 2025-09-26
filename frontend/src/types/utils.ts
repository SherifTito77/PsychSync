// ===== ENUMS =====

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  MEMBER = 'member'
}

export enum TeamStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived'
}

export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

// ===== UTILITY TYPES =====

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export type FormErrors<T> = {
  [K in keyof T]?: string;
};

// Generic form state
export interface FormState<T> {
  data: T;
  errors: FormErrors<T>;
  isSubmitting: boolean;
  isValid: boolean;
}
